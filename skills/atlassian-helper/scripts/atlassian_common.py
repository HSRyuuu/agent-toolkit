#!/usr/bin/env python3
"""Shared Atlassian (Jira + Confluence) helper utilities."""

from __future__ import annotations

import base64
import html
import json
import mimetypes
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_CONFIG_DIR = Path("~/.config/atlassian-helper").expanduser()
LEGACY_CONFIG_DIR = Path("~/.config/jira-helper").expanduser()
CONFIG_FILE = "config.json"
MEMORY_FILE = "MEMORY.md"
DEFAULT_LIMIT = 20
MAX_LIMIT = 100  # Jira Cloud /search/jql caps maxResults at 100
MAX_RETRY_AFTER_SECONDS = 60
TRANSIENT_RETRY_SLEEP_SECONDS = 2
UPLOAD_MAX_BYTES = 100 * 1024 * 1024  # Confluence Cloud per-file default; Jira is lower
UPLOAD_MAX_TIME_SECONDS = 300

SEARCH_PATH = "/rest/api/3/search/jql"
COUNT_PATH = "/rest/api/3/search/approximate-count"
MYSELF_PATH = "/rest/api/3/myself"
CQL_SEARCH_PATH = "/wiki/rest/api/search"
CONTENT_PATH = "/wiki/rest/api/content"  # v1: only API with attachment upload
PAGES_PATH = "/wiki/api/v2/pages"
SPACES_PATH = "/wiki/api/v2/spaces"

DEFAULT_FIELDS = [
    "summary",
    "status",
    "assignee",
    "reporter",
    "priority",
    "issuetype",
    "duedate",
    "updated",
    "created",
    "project",
    "labels",
    "resolution",
]


class AtlassianHelperError(RuntimeError):
    pass


def config_dir() -> Path:
    override = os.environ.get("ATLASSIAN_HELPER_CONFIG_DIR") or os.environ.get(
        "JIRA_HELPER_CONFIG_DIR"
    )
    if override:
        return Path(override).expanduser()
    # keep working for installs created before the jira-helper -> atlassian-helper rename
    if not DEFAULT_CONFIG_DIR.exists() and LEGACY_CONFIG_DIR.exists():
        return LEGACY_CONFIG_DIR
    return DEFAULT_CONFIG_DIR


def config_path() -> Path:
    return config_dir() / CONFIG_FILE


def memory_path() -> Path:
    return config_dir() / MEMORY_FILE


def read_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise AtlassianHelperError(f"Missing config file: {path}")
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise AtlassianHelperError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise AtlassianHelperError(f"Expected a JSON object in {path}")
    return data


def write_json_secure(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, stat.S_IRWXU)
    except OSError:
        pass
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.chmod(temp_name, stat.S_IRUSR | stat.S_IWUSR)
    os.replace(temp_name, path)


def ensure_memory_file() -> Path:
    path = memory_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            "# atlassian-helper memory\n\n"
            "## 프로젝트/스페이스 별칭\n\n"
            "## 팀/사람\n\n"
            "## 자주 쓰는 JQL\n\n"
            "## 자주 쓰는 CQL\n\n"
            "## 선호\n",
            encoding="utf-8",
        )
    try:
        os.chmod(path.parent, stat.S_IRWXU)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return path


def load_config(*, required: bool = True) -> dict[str, Any]:
    return read_json(config_path(), required=required)


def save_config(data: dict[str, Any]) -> None:
    write_json_secure(config_path(), data)


ISSUE_KEY_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*-\d+$")
PROJECT_KEY_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
NUMERIC_ID_PATTERN = re.compile(r"^\d+$")
SPACE_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_~][A-Za-z0-9_~.-]*$")


def validate_issue_key(value: str) -> str:
    key = str(value or "").strip()
    if not ISSUE_KEY_PATTERN.fullmatch(key):
        raise AtlassianHelperError(f"이슈 키 형식이 아닙니다: {value} (예: ABC-123)")
    return key


def validate_project_key(value: str) -> str:
    key = str(value or "").strip()
    if not PROJECT_KEY_PATTERN.fullmatch(key):
        raise AtlassianHelperError(f"프로젝트 키 형식이 아닙니다: {value} (예: ABC)")
    return key


def validate_id(value: str, label: str = "ID") -> str:
    text = str(value or "").strip()
    if not NUMERIC_ID_PATTERN.fullmatch(text):
        raise AtlassianHelperError(f"{label} 형식이 아닙니다: {value} (숫자만 가능)")
    return text


def validate_space_key(value: str) -> str:
    key = str(value or "").strip()
    if not SPACE_KEY_PATTERN.fullmatch(key):
        raise AtlassianHelperError(f"스페이스 키 형식이 아닙니다: {value} (예: DEV)")
    return key


def normalize_site(value: str) -> str:
    """Accept 'your-org.atlassian.net' or a full URL; return 'https://<host>'."""
    raw = (value or "").strip()
    if not raw:
        raise AtlassianHelperError("Atlassian site가 비어 있습니다. 예: your-org.atlassian.net")
    raw = re.sub(r"^https?://", "", raw, flags=re.I).split("/", 1)[0].strip().lower()
    if not raw or "." not in raw:
        raise AtlassianHelperError(f"Atlassian site를 해석할 수 없습니다: {value}")
    return f"https://{raw}"


def load_profile(name: str | None = None) -> tuple[str, dict[str, Any]]:
    config = load_config()
    profile_name = name or config.get("default_profile") or "default"
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise AtlassianHelperError(f"Profile not found in config.json ({profile_name})")
    profile = profiles[profile_name]
    if not isinstance(profile, dict):
        raise AtlassianHelperError(f"Profile must be an object: {profile_name}")
    for key in ("site", "email", "api_token"):
        if not profile.get(key):
            raise AtlassianHelperError(f"Profile '{profile_name}' has no {key}")
    return profile_name, profile


def update_profile(profile_name: str, updates: dict[str, Any]) -> None:
    config = load_config()
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise AtlassianHelperError(f"Profile not found in config.json ({profile_name})")
    profiles[profile_name].update(updates)
    save_config(config)


def mask_secret(value: str) -> str:
    if not value:
        return "***"
    return f"***(len={len(value)})"


def basic_auth_header(profile: dict[str, Any]) -> str:
    raw = f"{profile['email']}:{profile['api_token']}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def sanitize_sensitive(text: str, profile: dict[str, Any] | None = None) -> str:
    sanitized = text
    if profile:
        token = str(profile.get("api_token") or "")
        if token:
            sanitized = sanitized.replace(token, mask_secret(token))
        try:
            sanitized = sanitized.replace(basic_auth_header(profile), "Basic ***")
        except KeyError:
            pass
    sanitized = re.sub(r"(Authorization:\s*Basic\s+)\S+", r"\1***", sanitized, flags=re.I)
    return sanitized


def curl_config_quote(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def run_curl(
    *,
    url: str,
    http_method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    form: list[str] | None = None,
    max_time: int = 60,
) -> tuple[int, str, str]:
    method = http_method.upper()
    headers = headers or {}

    with tempfile.TemporaryDirectory(prefix="atlassian-helper-") as temp_dir:
        header_path = Path(temp_dir) / "headers.txt"
        body_path = Path(temp_dir) / "body.json"
        config_lines = [f'url = "{curl_config_quote(url)}"', f'request = "{method}"']
        for name, value in headers.items():
            config_lines.append(f'header = "{curl_config_quote(name)}: {curl_config_quote(value)}"')
        if payload is not None and method != "GET":
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            config_lines.append('header = "Content-Type: application/json"')
            config_lines.append(f'data = "{curl_config_quote(body)}"')
        for part in form or []:
            config_lines.append(f'form = "{curl_config_quote(part)}"')

        command = [
            "curl",
            "--silent",
            "--show-error",
            "--location",
            "--connect-timeout",
            "10",
            "--max-time",
            str(max_time),
            "--dump-header",
            str(header_path),
            "--output",
            str(body_path),
            "--write-out",
            "%{http_code}",
            "--config",
            "-",
        ]
        result = subprocess.run(
            command,
            input="\n".join(config_lines) + "\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        headers_text = header_path.read_text(encoding="utf-8", errors="replace")
        body_text = body_path.read_text(encoding="utf-8", errors="replace")

    if result.returncode != 0:
        raise AtlassianHelperError(result.stderr.strip() or "curl failed")
    try:
        status_code = int(result.stdout.strip()[-3:])
    except ValueError as exc:
        raise AtlassianHelperError(f"Could not parse curl HTTP status: {result.stdout}") from exc
    return status_code, headers_text, body_text


def parse_json_body(body: str, label: str) -> Any:
    if not body.strip():
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise AtlassianHelperError(
            f"Atlassian API {label} returned non-JSON body: {body[:500]}"
        ) from exc


def retry_after_seconds(headers: str) -> int | None:
    match = re.search(r"(?im)^retry-after:\s*(\d+)", headers)
    return int(match.group(1)) if match else None


def api_request(
    profile: dict[str, Any],
    path: str,
    *,
    http_method: str = "GET",
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    retries: int = 1,
    form: list[str] | None = None,
    max_time: int = 60,
) -> Any:
    base = normalize_site(str(profile.get("site")))
    url = f"{base}{path}"
    if query:
        params = urllib.parse.urlencode(
            {key: value for key, value in query.items() if value is not None}
        )
        if params:
            url = f"{url}?{params}"
    headers = {
        "Accept": "application/json",
        "Authorization": basic_auth_header(profile),
    }
    if form:
        # Atlassian rejects multipart uploads without this XSRF opt-out header.
        headers["X-Atlassian-Token"] = "no-check"

    attempts_left = retries
    transient_left = retries
    while True:
        try:
            status, response_headers, body = run_curl(
                url=url,
                http_method=http_method,
                headers=headers,
                payload=payload,
                form=form,
                max_time=max_time,
            )
        except AtlassianHelperError:
            # network failure / curl error: retry once before giving up
            if transient_left > 0:
                transient_left -= 1
                time.sleep(TRANSIENT_RETRY_SLEEP_SECONDS)
                continue
            raise
        if status == 429:
            wait_seconds = retry_after_seconds(response_headers)
            if wait_seconds is None:
                wait_seconds = TRANSIENT_RETRY_SLEEP_SECONDS
            if attempts_left > 0 and wait_seconds <= MAX_RETRY_AFTER_SECONDS:
                attempts_left -= 1
                time.sleep(wait_seconds)
                continue
            raise AtlassianHelperError("Atlassian API rate limited: retry later")
        if status >= 500 and transient_left > 0:
            transient_left -= 1
            time.sleep(TRANSIENT_RETRY_SLEEP_SECONDS)
            continue
        break

    data = parse_json_body(body, path)
    if status >= 400:
        if status in (401, 403):
            hint = " (인증/권한 실패: email/API token 또는 쓰기 권한을 확인하세요. setup-guide 참조)"
        elif status == 404:
            hint = " (경로 또는 대상이 없거나 볼 권한이 없습니다)"
        else:
            hint = ""
        detail = json.dumps(data, ensure_ascii=False) if data else body[:500]
        raise AtlassianHelperError(
            sanitize_sensitive(f"Atlassian API {path} HTTP {status}{hint}: {detail}", profile)
        )
    return data


def prepare_upload(path_value: str, name: str | None = None) -> tuple[Path, str]:
    """Validate a local file for upload and resolve the attachment filename."""
    path = Path(path_value).expanduser()
    if not path.exists():
        raise AtlassianHelperError(f"파일을 찾을 수 없습니다: {path}")
    if not path.is_file():
        raise AtlassianHelperError(f"파일이 아닙니다: {path}")
    size = path.stat().st_size
    if size == 0:
        raise AtlassianHelperError(f"빈 파일은 업로드하지 않습니다: {path}")
    if size > UPLOAD_MAX_BYTES:
        limit_mb = UPLOAD_MAX_BYTES // (1024 * 1024)
        raise AtlassianHelperError(f"파일이 너무 큽니다 ({size} bytes, 상한 {limit_mb}MB): {path}")
    filename = (name or path.name).strip()
    if not filename or filename in (".", "..") or "/" in filename or "\\" in filename:
        raise AtlassianHelperError(f"첨부 파일명이 올바르지 않습니다: {filename!r}")
    return path, filename


def file_form(path: Path, filename: str, field: str = "file") -> list[str]:
    """Build the curl --form spec for a single file part."""
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return [f'{field}=@"{path.resolve()}";filename="{filename}";type={content_type}']


def human_size(value: Any) -> str:
    try:
        size = float(value)
    except (TypeError, ValueError):
        return "-"
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return "-"


def site_url(profile: dict[str, Any]) -> str:
    return normalize_site(str(profile.get("site")))


def print_response(response: Any) -> int:
    print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def truncate_text(text: str, limit: int = 240) -> str:
    normalized = re.sub(r"\s+", " ", str(text)).strip()
    if len(normalized) <= limit:
        return normalized
    if limit <= 3:
        return "." * limit
    return normalized[: limit - 3] + "..."


def resolve_tz(tz_name: str | None):
    if not tz_name:
        return datetime.now().astimezone().tzinfo
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise AtlassianHelperError(
            f"알 수 없는 타임존입니다: {tz_name} (예: Asia/Seoul, UTC)"
        ) from exc


def format_timestamp(value: Any, tz_name: str | None = None) -> str:
    if not value:
        return "-"
    text = str(value)
    try:
        # Jira uses e.g. 2026-07-14T10:03:21.000+0900 (no colon in offset)
        normalized = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", text.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(resolve_tz(tz_name)).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return text


def due_label(value: Any, tz_name: str | None = None) -> str:
    """Format a duedate (YYYY-MM-DD) with a D-day marker."""
    if not value:
        return "-"
    text = str(value)
    try:
        due = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return text
    today = datetime.now(resolve_tz(tz_name)).date()
    delta = (due - today).days
    if delta > 0:
        marker = f"D-{delta}"
    elif delta == 0:
        marker = "D-DAY"
    else:
        marker = f"OVERDUE {-delta}d"
    return f"{text}({marker})"


# --- Ownership guard ------------------------------------------------------


def my_account_id(profile: dict[str, Any]) -> str:
    """Current user's accountId (cached in the profile by auth-test)."""
    cached = str(profile.get("account_id") or "").strip()
    if cached:
        return cached
    response = api_request(profile, MYSELF_PATH)
    account_id = str(response.get("accountId") or "") if isinstance(response, dict) else ""
    if not account_id:
        raise AtlassianHelperError(
            "내 accountId를 확인할 수 없습니다. atlassian_setup.py auth-test를 먼저 실행하세요."
        )
    profile["account_id"] = account_id  # in-memory cache for this run
    return account_id


def assert_owner(
    profile: dict[str, Any],
    owner_id: Any,
    owner_name: Any,
    target: str,
) -> None:
    """Block modify/delete unless the current user authored the target.

    Fails closed: an unknown author is treated as "not mine".
    """
    owner = str(owner_id or "").strip()
    if not owner:
        raise AtlassianHelperError(
            f"{target}의 작성자를 확인할 수 없어 수정/삭제를 중단합니다."
        )
    me = my_account_id(profile)
    if owner != me:
        raise AtlassianHelperError(
            f"{target}의 작성자가 본인이 아닙니다 (작성자: {owner_name or owner}). "
            "수정/삭제는 본인이 작성한 항목에만 허용됩니다."
        )


def confirm_destructive(yes: bool, target: str) -> None:
    if not yes:
        raise AtlassianHelperError(f"{target} 삭제는 --yes 를 붙여야 실행됩니다.")


def read_body(text: str | None, path: str | None, *, label: str = "본문") -> str:
    """Body from --body or --body-file (exactly one; '-' reads stdin)."""
    if (text is None) == (path is None):
        raise AtlassianHelperError(f"{label}은 --body 또는 --body-file 중 하나만 지정하세요.")
    if path is not None:
        if path == "-":
            return sys.stdin.read()
        file_path = Path(path).expanduser()
        if not file_path.exists():
            raise AtlassianHelperError(f"파일을 찾을 수 없습니다: {path}")
        return file_path.read_text(encoding="utf-8")
    return text or ""


# --- JQL / CQL helpers ----------------------------------------------------

JQL_RELATIVE_PATTERN = re.compile(r"^-?\d+[mhdw]$")  # -7d, 4h, 30m, 2w
JQL_FUNCTION_PATTERN = re.compile(r"^\w+\(.*\)$")  # startOfWeek(), endOfDay("-1")


def jql_quote(value: str) -> str:
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


# CQL uses the same quoting rules as JQL.
cql_quote = jql_quote


def jql_time_value(value: str) -> str:
    """Relative offsets and JQL functions stay raw; anything else gets quoted."""
    text = str(value).strip()
    if JQL_RELATIVE_PATTERN.fullmatch(text) or JQL_FUNCTION_PATTERN.fullmatch(text):
        return text
    return jql_quote(text)


def jql_in_clause(field: str, values: list[str]) -> str:
    if len(values) == 1:
        return f"{field} = {jql_quote(values[0])}"
    joined = ", ".join(jql_quote(value) for value in values)
    return f"{field} IN ({joined})"


def combine_jql(clauses: list[str], order_by: str | None = None) -> str:
    query = " AND ".join(clause for clause in clauses if clause)
    if order_by:
        query = f"{query} ORDER BY {order_by}" if query else f"ORDER BY {order_by}"
    return query


# --- ADF (Atlassian Document Format) -------------------------------------


def adf_to_text(node: Any, depth: int = 0) -> str:
    """Flatten an ADF document to plain text (paragraphs joined by newlines)."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(adf_to_text(child, depth) for child in node)
    if not isinstance(node, dict):
        return ""
    node_type = node.get("type")
    content = node.get("content")
    if node_type == "text":
        return str(node.get("text") or "")
    if node_type in ("mention", "emoji", "status", "date"):
        attrs = node.get("attrs")
        if isinstance(attrs, dict):
            return str(attrs.get("text") or attrs.get("shortName") or attrs.get("timestamp") or "")
        return ""
    if node_type == "hardBreak":
        return "\n"
    if node_type == "inlineCard":
        attrs = node.get("attrs")
        return str(attrs.get("url") or "") if isinstance(attrs, dict) else ""
    inner = adf_to_text(content, depth + 1) if content is not None else ""
    if node_type in ("paragraph", "heading", "blockquote", "codeBlock", "rule"):
        return inner + "\n"
    if node_type == "listItem":
        return "- " + inner
    if node_type == "tableRow":
        return "| " + inner + "\n"
    if node_type in ("bulletList", "orderedList", "table"):
        return inner
    if node_type == "tableCell" or node_type == "tableHeader":
        return inner.rstrip("\n") + " | "
    return inner


def adf_summary(node: Any, limit: int = 800) -> str:
    text = adf_to_text(node)
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line.strip())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


_TABLE_SEP_RE = re.compile(r"^:?-{1,}:?$")


def _split_pipe_row(line: str) -> list[str]:
    body = line.strip().strip("|")
    return [cell.replace("\x00", "|").strip() for cell in body.replace(r"\|", "\x00").split("|")]


def _take_pipe_table(lines: list[str], start: int) -> tuple[list[list[str]], bool, int]:
    """Read a markdown pipe table at `lines[start]`.

    Returns (rows, has_header, next_index). `rows` is empty when the lines are
    not a table. A table needs a `|---|---|` separator right after the first
    row; without it the caller keeps its plain-text handling.
    """
    if start + 1 >= len(lines) or not lines[start].strip().startswith("|"):
        return [], False, start
    separator = lines[start + 1].strip()
    if not separator.startswith("|"):
        return [], False, start
    cells = _split_pipe_row(separator)
    if not cells or not all(_TABLE_SEP_RE.match(cell) for cell in cells):
        return [], False, start
    header = _split_pipe_row(lines[start])
    width = len(header)
    rows = [header]
    index = start + 2
    while index < len(lines) and lines[index].strip().startswith("|"):
        row = _split_pipe_row(lines[index])
        rows.append((row + [""] * width)[:width])
        index += 1
    return rows, True, index


# `code`, **bold**, [label](url) — the inline forms worth carrying over. Italic
# is left alone: `*x*` collides with bullets and `_x_` with identifiers.
# The double-backtick span comes first: it is how markdown escapes a literal
# backtick, and letting the single-backtick branch see it shreds the run.
_INLINE_RE = re.compile(
    r"``\s?(?P<code2>.+?)\s?``"
    r"|`(?P<code>[^`\n]+)`"
    r"|\*\*(?P<bold>[^*\n]+)\*\*"
    r"|\[(?P<label>[^\]\n]+)\]\((?P<href>[^)\s]+)\)"
)
_FENCE_RE = re.compile(r"^(?:```|~~~)\s*([A-Za-z0-9_+#-]*)\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET_RE = re.compile(r"^[-*]\s+(.*)$")
_NUMBER_RE = re.compile(r"^\d+[.)]\s+(.*)$")


def _is_web_link(href: str) -> bool:
    return href.startswith(("http://", "https://", "mailto:"))


def _adf_inline(text: str) -> list[dict[str, Any]]:
    """Split one line into ADF text nodes, applying code/strong/link marks."""
    nodes: list[dict[str, Any]] = []
    pos = 0
    for match in _INLINE_RE.finditer(text):
        if match.start() > pos:
            nodes.append({"type": "text", "text": text[pos : match.start()]})
        code = match.group("code2") or match.group("code")
        bold, label, href = match.group("bold", "label", "href")
        if code is not None:
            nodes.append({"type": "text", "text": code, "marks": [{"type": "code"}]})
        elif bold is not None:
            # Bold wraps whatever is inside it, so recurse. ADF rejects a code
            # mark combined with any other formatting mark, so code wins there
            # and the strong is dropped rather than sent as an invalid pair.
            for inner in _adf_inline(bold):
                marks = inner.get("marks") or []
                if not any(mark["type"] == "code" for mark in marks):
                    inner["marks"] = marks + [{"type": "strong"}]
                nodes.append(inner)
        else:
            # Labels carry their own formatting, so recurse there too. Anchors
            # and relative paths mean nothing outside the source doc, so those
            # keep the label and drop the target.
            inner_nodes = _adf_inline(label)
            if _is_web_link(href):
                for inner in inner_nodes:
                    inner["marks"] = (inner.get("marks") or []) + [
                        {"type": "link", "attrs": {"href": href}}
                    ]
            nodes.extend(inner_nodes)
        pos = match.end()
    if pos < len(text):
        nodes.append({"type": "text", "text": text[pos:]})
    return [node for node in nodes if node.get("text")]


def _storage_inline(text: str) -> str:
    """Split one line into storage XHTML, applying code/strong/link markup."""
    out: list[str] = []
    pos = 0
    for match in _INLINE_RE.finditer(text):
        if match.start() > pos:
            out.append(html.escape(text[pos : match.start()]))
        code = match.group("code2") or match.group("code")
        bold, label, href = match.group("bold", "label", "href")
        if code is not None:
            out.append(f"<code>{html.escape(code)}</code>")
        elif bold is not None:
            out.append(f"<strong>{_storage_inline(bold)}</strong>")
        elif _is_web_link(href):
            out.append(f'<a href="{html.escape(href, quote=True)}">{_storage_inline(label)}</a>')
        else:
            out.append(_storage_inline(label))
        pos = match.end()
    if pos < len(text):
        out.append(html.escape(text[pos:]))
    return "".join(out)


def _parse_blocks(text: str) -> list[tuple[str, Any]]:
    """Markdown-ish plain text -> neutral block list shared by both writers.

    Blank line ends a block. Recognized: ATX headings (`#`..`######`), fenced
    code blocks, blockquotes, bullet and numbered lists, and pipe tables.
    Anything else becomes a paragraph, with its lines joined by line breaks.
    """
    lines = [raw.rstrip() for raw in str(text).splitlines()]
    blocks: list[tuple[str, Any]] = []
    paragraph: list[str] = []
    items: list[str] = []
    ordered = False

    def flush() -> None:
        nonlocal ordered
        if items:
            blocks.append(("list", (ordered, list(items))))
            items.clear()
            ordered = False
        if paragraph:
            blocks.append(("para", list(paragraph)))
            paragraph.clear()

    index = 0
    total = len(lines)
    while index < total:
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush()
            index += 1
            continue

        fence = _FENCE_RE.match(stripped)
        if fence:
            flush()
            language = fence.group(1)
            index += 1
            body: list[str] = []
            while index < total and not _FENCE_RE.match(lines[index].strip()):
                body.append(lines[index])
                index += 1
            index += 1  # closing fence, or past the end when it was never closed
            blocks.append(("code", (language, "\n".join(body))))
            continue

        rows, has_header, next_index = _take_pipe_table(lines, index)
        if rows:
            flush()
            blocks.append(("table", (rows, has_header)))
            index = next_index
            continue

        heading = _HEADING_RE.match(stripped)
        if heading:
            flush()
            blocks.append(("heading", (len(heading.group(1)), heading.group(2).strip())))
            index += 1
            continue

        if stripped == ">" or stripped.startswith("> "):
            flush()
            quote: list[str] = []
            while index < total and (
                lines[index].strip() == ">" or lines[index].strip().startswith("> ")
            ):
                quote.append(lines[index].strip()[1:].lstrip())
                index += 1
            blocks.append(("quote", quote))
            continue

        bullet = _BULLET_RE.match(stripped)
        number = _NUMBER_RE.match(stripped)
        if bullet or number:
            wants_ordered = number is not None
            if paragraph or (items and ordered != wants_ordered):
                flush()
            ordered = wants_ordered
            items.append((number or bullet).group(1).strip())
            index += 1
            continue

        if items:
            flush()
        paragraph.append(line)
        index += 1

    flush()
    return blocks


def _adf_table(rows: list[list[str]], has_header: bool) -> dict[str, Any]:
    content = []
    for row_index, row in enumerate(rows):
        cell_type = "tableHeader" if has_header and row_index == 0 else "tableCell"
        content.append(
            {
                "type": "tableRow",
                "content": [
                    {"type": cell_type, "attrs": {}, "content": [_adf_paragraph([cell] if cell else [])]}
                    for cell in row
                ],
            }
        )
    return {
        "type": "table",
        "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
        "content": content,
    }


def _storage_table(rows: list[list[str]], has_header: bool) -> str:
    body = []
    for row_index, row in enumerate(rows):
        tag = "th" if has_header and row_index == 0 else "td"
        cells = "".join(f"<{tag}><p>{_storage_inline(cell)}</p></{tag}>" for cell in row)
        body.append(f"<tr>{cells}</tr>")
    return f"<table><tbody>{''.join(body)}</tbody></table>"


def _adf_paragraph(lines: list[str]) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        if index:
            content.append({"type": "hardBreak"})
        content.extend(_adf_inline(line))
    return {"type": "paragraph", "content": content} if content else {"type": "paragraph"}


def _adf_list(ordered: bool, items: list[str]) -> dict[str, Any]:
    return {
        "type": "orderedList" if ordered else "bulletList",
        "content": [{"type": "listItem", "content": [_adf_paragraph([item])]} for item in items],
    }


def text_to_adf(text: str) -> dict[str, Any]:
    """Markdown-ish plain text -> ADF doc.

    Supported: headings, paragraphs, bullet/numbered lists, blockquotes, fenced
    code blocks, pipe tables, and inline `code` / **bold** / [label](url).
    See `references/markdown-mapping.md` for what is deliberately not supported.
    """
    blocks: list[dict[str, Any]] = []
    for kind, value in _parse_blocks(text):
        if kind == "heading":
            level, content = value
            blocks.append(
                {"type": "heading", "attrs": {"level": level}, "content": _adf_inline(content)}
            )
        elif kind == "para":
            blocks.append(_adf_paragraph(value))
        elif kind == "list":
            blocks.append(_adf_list(*value))
        elif kind == "quote":
            blocks.append({"type": "blockquote", "content": [_adf_paragraph(value)]})
        elif kind == "code":
            language, body = value
            node: dict[str, Any] = {"type": "codeBlock", "attrs": {}}
            if language:
                node["attrs"] = {"language": language}
            if body:
                node["content"] = [{"type": "text", "text": body}]
            blocks.append(node)
        elif kind == "table":
            blocks.append(_adf_table(*value))

    if not blocks:
        blocks = [{"type": "paragraph"}]
    return {"type": "doc", "version": 1, "content": blocks}


# --- Confluence storage format -------------------------------------------


def storage_to_text(value: Any, limit: int | None = None) -> str:
    """Flatten Confluence storage XHTML to readable plain text."""
    text = str(value or "")
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", text)
    # Unwrap code-macro bodies first; otherwise tag stripping eats them whole.
    text = re.sub(r"(?s)<!\[CDATA\[(.*?)\]\]>", lambda match: match.group(1), text)
    text = re.sub(r"(?i)<li[^>]*>", "\n- ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|h[1-6]|li|tr|table|ul|ol)>", "\n", text)
    text = re.sub(r"(?i)</t[dh]>", " | ", text)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    text = html.unescape(text)
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line.strip())
    if limit is not None and len(cleaned) > limit:
        return cleaned[: limit - 3] + "..."
    return cleaned


def _storage_code(language: str, body: str) -> str:
    """Confluence code macro. CDATA cannot nest, so split any literal `]]>`."""
    safe = body.replace("]]>", "]]]]><![CDATA[>")
    parameter = (
        f'<ac:parameter ac:name="language">{html.escape(language)}</ac:parameter>' if language else ""
    )
    return (
        '<ac:structured-macro ac:name="code" ac:schema-version="1">'
        f"{parameter}<ac:plain-text-body><![CDATA[{safe}]]></ac:plain-text-body>"
        "</ac:structured-macro>"
    )


def text_to_storage(text: str) -> str:
    """Markdown-ish plain text -> Confluence storage XHTML.

    Same input grammar as `text_to_adf`; see `references/markdown-mapping.md`.
    """
    blocks: list[str] = []
    for kind, value in _parse_blocks(text):
        if kind == "heading":
            level, content = value
            tag = min(level + 1, 6)  # the page title is h1
            blocks.append(f"<h{tag}>{_storage_inline(content)}</h{tag}>")
        elif kind == "para":
            blocks.append("<p>" + "<br />".join(_storage_inline(line) for line in value) + "</p>")
        elif kind == "list":
            ordered, items = value
            tag = "ol" if ordered else "ul"
            entries = "".join(f"<li><p>{_storage_inline(item)}</p></li>" for item in items)
            blocks.append(f"<{tag}>{entries}</{tag}>")
        elif kind == "quote":
            body = "<br />".join(_storage_inline(line) for line in value)
            blocks.append(f"<blockquote><p>{body}</p></blockquote>")
        elif kind == "code":
            blocks.append(_storage_code(*value))
        elif kind == "table":
            blocks.append(_storage_table(*value))

    return "".join(blocks) or "<p />"


# --- Issue formatting -----------------------------------------------------


def _field(issue: dict[str, Any], name: str) -> Any:
    fields = issue.get("fields")
    return fields.get(name) if isinstance(fields, dict) else None


def _named(value: Any, key: str = "name") -> str:
    if isinstance(value, dict):
        return str(value.get(key) or value.get("displayName") or "-")
    return "-"


def issue_status(issue: dict[str, Any]) -> str:
    return _named(_field(issue, "status"))


def issue_assignee(issue: dict[str, Any]) -> str:
    value = _field(issue, "assignee")
    if isinstance(value, dict):
        return str(value.get("displayName") or "-")
    return "(미배정)"


def format_issue(issue: dict[str, Any], *, tz_name: str | None = None) -> str:
    key = str(issue.get("key") or "-")
    issue_type = _named(_field(issue, "issuetype"))
    priority = _named(_field(issue, "priority"))
    status = issue_status(issue)
    summary = truncate_text(str(_field(issue, "summary") or "-"), 160)
    due = due_label(_field(issue, "duedate"), tz_name)
    updated = format_timestamp(_field(issue, "updated"), tz_name)
    labels = _field(issue, "labels")
    label_text = ",".join(labels) if isinstance(labels, list) and labels else "-"
    lines = [
        f"{key}  [{status}]  {issue_type}/{priority}  due={due}",
        f"  {summary}",
        f"  assignee={issue_assignee(issue)} updated={updated} labels={label_text}",
    ]
    return "\n".join(lines)


def format_issues(issues: list[Any], *, tz_name: str | None = None) -> str:
    blocks = [
        format_issue(issue, tz_name=tz_name) for issue in issues if isinstance(issue, dict)
    ]
    return "\n\n".join(blocks)


def response_issues(response: Any) -> list[dict[str, Any]]:
    if not isinstance(response, dict):
        return []
    issues = response.get("issues")
    if not isinstance(issues, list):
        return []
    return [issue for issue in issues if isinstance(issue, dict)]


def response_next_page(response: Any) -> str | None:
    if not isinstance(response, dict):
        return None
    token = response.get("nextPageToken")
    return str(token) if token else None


def add_profile_arg(parser: Any) -> None:
    parser.add_argument("--profile", help="config.json profile name")


def run_main(parser_builder: Any) -> int:
    parser = parser_builder()
    args = parser.parse_args()
    try:
        return args.func(args)
    except AtlassianHelperError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nerror: 입력이 취소되었습니다.", file=sys.stderr)
        return 1
