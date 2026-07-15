#!/usr/bin/env python3
"""Shared Jira helper utilities."""

from __future__ import annotations

import base64
import json
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


DEFAULT_CONFIG_DIR = Path("~/.config/jira-helper").expanduser()
CONFIG_FILE = "config.json"
MEMORY_FILE = "MEMORY.md"
DEFAULT_LIMIT = 20
MAX_LIMIT = 100  # Jira Cloud /search/jql caps maxResults at 100
MAX_RETRY_AFTER_SECONDS = 60
TRANSIENT_RETRY_SLEEP_SECONDS = 2

SEARCH_PATH = "/rest/api/3/search/jql"
COUNT_PATH = "/rest/api/3/search/approximate-count"

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


class JiraHelperError(RuntimeError):
    pass


def config_dir() -> Path:
    override = os.environ.get("JIRA_HELPER_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    return DEFAULT_CONFIG_DIR


def config_path() -> Path:
    return config_dir() / CONFIG_FILE


def memory_path() -> Path:
    return config_dir() / MEMORY_FILE


def read_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise JiraHelperError(f"Missing config file: {path}")
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise JiraHelperError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise JiraHelperError(f"Expected a JSON object in {path}")
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
            "# jira-helper memory\n\n"
            "## 프로젝트 별칭\n\n"
            "## 팀/사람\n\n"
            "## 자주 쓰는 JQL\n\n"
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


def validate_issue_key(value: str) -> str:
    key = str(value or "").strip()
    if not ISSUE_KEY_PATTERN.fullmatch(key):
        raise JiraHelperError(f"이슈 키 형식이 아닙니다: {value} (예: ABC-123)")
    return key


def validate_project_key(value: str) -> str:
    key = str(value or "").strip()
    if not PROJECT_KEY_PATTERN.fullmatch(key):
        raise JiraHelperError(f"프로젝트 키 형식이 아닙니다: {value} (예: ABC)")
    return key


def normalize_site(value: str) -> str:
    """Accept 'your-org.atlassian.net' or a full URL; return 'https://<host>'."""
    raw = (value or "").strip()
    if not raw:
        raise JiraHelperError("Jira site가 비어 있습니다. 예: your-org.atlassian.net")
    raw = re.sub(r"^https?://", "", raw, flags=re.I).split("/", 1)[0].strip().lower()
    if not raw or "." not in raw:
        raise JiraHelperError(f"Jira site를 해석할 수 없습니다: {value}")
    return f"https://{raw}"


def load_profile(name: str | None = None) -> tuple[str, dict[str, Any]]:
    config = load_config()
    profile_name = name or config.get("default_profile") or "default"
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise JiraHelperError(f"Profile not found in config.json ({profile_name})")
    profile = profiles[profile_name]
    if not isinstance(profile, dict):
        raise JiraHelperError(f"Profile must be an object: {profile_name}")
    for key in ("site", "email", "api_token"):
        if not profile.get(key):
            raise JiraHelperError(f"Profile '{profile_name}' has no {key}")
    return profile_name, profile


def update_profile(profile_name: str, updates: dict[str, Any]) -> None:
    config = load_config()
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise JiraHelperError(f"Profile not found in config.json ({profile_name})")
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
) -> tuple[int, str, str]:
    method = http_method.upper()
    headers = headers or {}

    with tempfile.TemporaryDirectory(prefix="jira-helper-") as temp_dir:
        header_path = Path(temp_dir) / "headers.txt"
        body_path = Path(temp_dir) / "body.json"
        config_lines = [f'url = "{curl_config_quote(url)}"', f'request = "{method}"']
        for name, value in headers.items():
            config_lines.append(f'header = "{curl_config_quote(name)}: {curl_config_quote(value)}"')
        if payload is not None and method != "GET":
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            config_lines.append('header = "Content-Type: application/json"')
            config_lines.append(f'data = "{curl_config_quote(body)}"')

        command = [
            "curl",
            "--silent",
            "--show-error",
            "--location",
            "--connect-timeout",
            "10",
            "--max-time",
            "60",
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
        raise JiraHelperError(result.stderr.strip() or "curl failed")
    try:
        status_code = int(result.stdout.strip()[-3:])
    except ValueError as exc:
        raise JiraHelperError(f"Could not parse curl HTTP status: {result.stdout}") from exc
    return status_code, headers_text, body_text


def parse_json_body(body: str, label: str) -> Any:
    if not body.strip():
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise JiraHelperError(f"Jira API {label} returned non-JSON body: {body[:500]}") from exc


def retry_after_seconds(headers: str) -> int | None:
    match = re.search(r"(?im)^retry-after:\s*(\d+)", headers)
    return int(match.group(1)) if match else None


def jira_request(
    profile: dict[str, Any],
    path: str,
    *,
    http_method: str = "GET",
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    retries: int = 1,
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

    attempts_left = retries
    transient_left = retries
    while True:
        try:
            status, response_headers, body = run_curl(
                url=url, http_method=http_method, headers=headers, payload=payload
            )
        except JiraHelperError:
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
            raise JiraHelperError("Jira API rate limited: retry later")
        if status >= 500 and transient_left > 0:
            transient_left -= 1
            time.sleep(TRANSIENT_RETRY_SLEEP_SECONDS)
            continue
        break

    data = parse_json_body(body, path)
    if status >= 400:
        if status in (401, 403):
            hint = " (인증 실패: email/API token을 확인하세요. setup-guide 참조)"
        elif status == 404:
            hint = " (경로 또는 이슈 키가 없거나 볼 권한이 없습니다)"
        else:
            hint = ""
        detail = json.dumps(data, ensure_ascii=False) if data else body[:500]
        raise JiraHelperError(
            sanitize_sensitive(f"Jira API {path} HTTP {status}{hint}: {detail}", profile)
        )
    return data


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
        raise JiraHelperError(
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


# --- JQL helpers ---------------------------------------------------------

JQL_RELATIVE_PATTERN = re.compile(r"^-?\d+[mhdw]$")  # -7d, 4h, 30m, 2w
JQL_FUNCTION_PATTERN = re.compile(r"^\w+\(.*\)$")  # startOfWeek(), endOfDay("-1")


def jql_quote(value: str) -> str:
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


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
    if node_type in ("bulletList", "orderedList", "table", "tableRow"):
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
    except JiraHelperError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nerror: 입력이 취소되었습니다.", file=sys.stderr)
        return 1
