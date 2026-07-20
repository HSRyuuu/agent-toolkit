#!/usr/bin/env python3
"""Shared postman-helper utilities.

Read-first over Postman collections from two sources — the Postman cloud API
(X-Api-Key) or a local exported collection JSON file — plus a guarded executor
for saved requests. import-only; do not call as CLI.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path
from typing import Any, Iterator


DEFAULT_CONFIG_DIR = Path("~/.config/postman-helper").expanduser()
CONFIG_FILE = "config.json"
MEMORY_FILE = "MEMORY.md"
API_BASE = "https://api.getpostman.com"
DEFAULT_LIMIT = 50
TRANSIENT_RETRY_SLEEP_SECONDS = 2

# --- execution safety -------------------------------------------------------
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CONFIRM_METHODS = {"POST"}
BLOCKED_METHODS = {"PUT", "PATCH", "DELETE"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
LOCAL_SUFFIXES = (".local", ".localhost", ".test")
LOCAL_LABELS = {"dev", "development", "local", "localhost"}
# body modes we can faithfully replay through curl
EXECUTABLE_BODY_MODES = {"", "none", "raw", "urlencoded"}

SENSITIVE_KEY_PATTERN = re.compile(
    r"(authorization|cookie|set-cookie|token|secret|password|passwd|api[-_]?key|"
    r"x-api-key|credential|session|bearer|access[-_]?key)",
    re.I,
)


class PostmanHelperError(RuntimeError):
    pass


# --- config -----------------------------------------------------------------
def config_dir() -> Path:
    override = os.environ.get("POSTMAN_HELPER_CONFIG_DIR")
    return Path(override).expanduser() if override else DEFAULT_CONFIG_DIR


def config_path() -> Path:
    return config_dir() / CONFIG_FILE


def memory_path() -> Path:
    return config_dir() / MEMORY_FILE


def read_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise PostmanHelperError(f"Missing config file: {path}")
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise PostmanHelperError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PostmanHelperError(f"Expected a JSON object in {path}")
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


def load_config(*, required: bool = True) -> dict[str, Any]:
    return read_json(config_path(), required=required)


def save_config(data: dict[str, Any]) -> None:
    write_json_secure(config_path(), data)


def ensure_memory_file() -> Path:
    path = memory_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            "# postman-helper memory\n\n"
            "## 워크스페이스 / 컬렉션\n\n"
            "## 로컬 컬렉션 파일 경로\n\n"
            "## 자주 찾는 엔드포인트\n\n"
            "## 실행 환경 (local/dev base URL)\n\n"
            "## 선호\n",
            encoding="utf-8",
        )
    try:
        os.chmod(path.parent, stat.S_IRWXU)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return path


def load_profile(name: str | None = None) -> tuple[str, dict[str, Any]]:
    config = load_config()
    profile_name = name or config.get("default_profile") or "default"
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise PostmanHelperError(f"Profile not found in config.json ({profile_name})")
    profile = profiles[profile_name]
    if not isinstance(profile, dict) or not profile.get("api_key"):
        raise PostmanHelperError(f"Profile '{profile_name}' has no api_key")
    return profile_name, profile


def mask_secret(value: str) -> str:
    return "***" if len(value) <= 8 else f"{value[:4]}...{value[-4:]}"


# --- http -------------------------------------------------------------------
def _curl_quote(value: str) -> str:
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
    body: str | None = None,
    content_type: str | None = None,
) -> tuple[int, float, str, str]:
    """Return (status_code, time_total_seconds, response_headers, body)."""
    method = http_method.upper()
    headers = headers or {}
    with tempfile.TemporaryDirectory(prefix="postman-helper-") as temp_dir:
        header_path = Path(temp_dir) / "headers.txt"
        body_path = Path(temp_dir) / "body.out"
        config_lines = [f'url = "{_curl_quote(url)}"', f'request = "{method}"']
        for name, value in headers.items():
            config_lines.append(
                f'header = "{_curl_quote(name)}: {_curl_quote(value)}"'
            )
        if body is not None and method != "GET":
            if content_type:
                config_lines.append(f'header = "Content-Type: {_curl_quote(content_type)}"')
            config_lines.append(f'data = "{_curl_quote(body)}"')
        # redirects are NOT followed: a local URL judged safe could 302 to a
        # remote host and curl would forward the custom headers there
        command = [
            "curl", "--silent", "--show-error",
            "--connect-timeout", "10", "--max-time", "60",
            "--dump-header", str(header_path),
            "--output", str(body_path),
            "--write-out", "%{http_code} %{time_total}",
            "--config", "-",
        ]
        result = subprocess.run(
            command, input="\n".join(config_lines) + "\n", text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        headers_text = header_path.read_text(encoding="utf-8", errors="replace")
        body_text = body_path.read_text(encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise PostmanHelperError(result.stderr.strip() or "curl failed")
    parts = result.stdout.strip().split()
    try:
        status_code = int(parts[0])
        time_total = float(parts[1]) if len(parts) > 1 else 0.0
    except (ValueError, IndexError) as exc:
        raise PostmanHelperError(f"Could not parse curl output: {result.stdout}") from exc
    return status_code, time_total, headers_text, body_text


def postman_request(profile: dict[str, Any], path: str, *, query: dict[str, Any] | None = None) -> Any:
    """GET the Postman cloud API and return parsed JSON."""
    url = f"{API_BASE}{path}"
    if query:
        params = urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
        if params:
            url = f"{url}?{params}"
    headers = {"Accept": "application/json", "X-Api-Key": str(profile["api_key"])}
    transient_left = 1
    while True:
        try:
            status, _t, _h, body = run_curl(url=url, headers=headers)
        except PostmanHelperError:
            if transient_left > 0:
                transient_left -= 1
                time.sleep(TRANSIENT_RETRY_SLEEP_SECONDS)
                continue
            raise
        if status >= 500 and transient_left > 0:
            transient_left -= 1
            time.sleep(TRANSIENT_RETRY_SLEEP_SECONDS)
            continue
        break
    try:
        data = json.loads(body) if body.strip() else {}
    except json.JSONDecodeError as exc:
        raise PostmanHelperError(f"Postman API {path} returned non-JSON: {body[:200]}") from exc
    if status >= 400:
        detail = json.dumps(data, ensure_ascii=False) if data else body
        detail = detail.replace(str(profile.get("api_key") or ""), "***")
        raise PostmanHelperError(f"Postman API {path} HTTP {status}: {detail}")
    return data


# --- collection source ------------------------------------------------------
def load_collection(source: str, *, is_file: bool, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the inner collection object ({info, item, variable}) from a local
    file path (is_file) or by Postman collection uid (cloud)."""
    if is_file:
        raw = read_json(Path(source).expanduser())
    else:
        if profile is None:
            raise PostmanHelperError("cloud collection requires a profile")
        raw = postman_request(profile, f"/collections/{source}")
    collection = raw.get("collection") if isinstance(raw.get("collection"), dict) else raw
    if not isinstance(collection, dict) or "item" not in collection:
        raise PostmanHelperError("Not a Postman collection (no 'item' array).")
    return collection


def collection_varmap(collection: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for var in collection.get("variable") or []:
        if isinstance(var, dict) and var.get("key") is not None:
            out[str(var["key"])] = str(var.get("value", ""))
    return out


VAR_PATTERN = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def resolve_vars(text: str, varmap: dict[str, str]) -> str:
    if not text:
        return text
    return VAR_PATTERN.sub(lambda m: varmap.get(m.group(1), m.group(0)), text)


def has_unresolved_vars(text: str) -> bool:
    return bool(VAR_PATTERN.search(text or ""))


# --- collection parsing -----------------------------------------------------
def url_raw(url: Any) -> str:
    if isinstance(url, str):
        return url
    if isinstance(url, dict):
        if url.get("raw"):
            return str(url["raw"])
        host = url.get("host")
        host_str = ".".join(host) if isinstance(host, list) else str(host or "")
        path = url.get("path")
        path_str = "/".join(str(p) for p in path) if isinstance(path, list) else str(path or "")
        return f"{host_str}/{path_str}".rstrip("/")
    return ""


def url_path(url: Any) -> str:
    """Best-effort path portion for display (leading slash, no query)."""
    if isinstance(url, dict) and isinstance(url.get("path"), list):
        return "/" + "/".join(str(p) for p in url["path"])
    raw = url_raw(url)
    raw = raw.split("?", 1)[0]
    m = re.match(r"^[a-zA-Z][\w+.-]*://[^/]+(/.*)$", raw)
    if m:
        return m.group(1)
    # {{base_url}}/orders style
    parts = raw.split("/", 1)
    return "/" + parts[1] if len(parts) > 1 else raw


def iter_requests(collection: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Walk the item tree, yielding each leaf request with its folder path."""
    def walk(items: Any, folders: list[str]) -> Iterator[dict[str, Any]]:
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            if isinstance(item.get("item"), list):  # folder
                yield from walk(item["item"], folders + [name])
            elif isinstance(item.get("request"), (dict, str)):  # leaf request
                request = item["request"]
                if isinstance(request, str):
                    request = {"method": "GET", "url": request}
                yield {
                    "name": name,
                    "folder": " / ".join(folders),
                    "method": str(request.get("method", "GET")).upper(),
                    "url": request.get("url"),
                    "request": request,
                }
    yield from walk(collection.get("item"), [])


def match_request(entry: dict[str, Any], query: str) -> bool:
    q = query.lower()
    haystack = f"{entry['name']} {entry['folder']} {entry['method']} {url_raw(entry['url'])}".lower()
    return q in haystack


# --- formatting -------------------------------------------------------------
def truncate(text: str, limit: int = 200) -> str:
    normalized = re.sub(r"\s+", " ", str(text)).strip()
    return normalized if len(normalized) <= limit else normalized[: limit - 3] + "..."


def redact_value(key: str, value: str) -> str:
    return "***redacted***" if SENSITIVE_KEY_PATTERN.search(str(key)) else truncate(value, 200)


def redact_url(url: str) -> str:
    """Display-only: redact sensitive query param values in a resolved URL."""
    parts = urllib.parse.urlsplit(url)
    if not parts.query:
        return url
    query = "&".join(
        f"{k}=***redacted***" if SENSITIVE_KEY_PATTERN.search(k) else f"{k}={v}"
        for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    )
    return urllib.parse.urlunsplit(parts._replace(query=query))


def format_endpoint_line(entry: dict[str, Any]) -> str:
    loc = f"  ({entry['folder']})" if entry["folder"] else ""
    return f"[{entry['method']:6}] {url_path(entry['url'])} — {entry['name']}{loc}"


def _kv_list(items: Any, label: str) -> list[str]:
    lines: list[str] = []
    for it in items or []:
        if not isinstance(it, dict) or it.get("disabled"):
            continue
        key = str(it.get("key", ""))
        value = redact_value(key, str(it.get("value", "")))
        desc = truncate(it.get("description") or "", 80)
        suffix = f"  — {desc}" if desc else ""
        lines.append(f"  {key} = {value}{suffix}")
    return [f"{label}:"] + lines if lines else []


def format_request_detail(entry: dict[str, Any]) -> str:
    request = entry["request"]
    url = entry["url"]
    lines = [
        f"{entry['method']} {url_raw(url)}",
        f"name: {entry['name']}" + (f"   folder: {entry['folder']}" if entry["folder"] else ""),
    ]
    if isinstance(request.get("description"), str) and request["description"].strip():
        lines += ["", truncate(request["description"], 400)]
    if isinstance(url, dict):
        lines += [""] + _kv_list(url.get("variable"), "path variables")
        lines += _kv_list(url.get("query"), "query params")
    lines += _kv_list(request.get("header"), "headers")
    body = request.get("body")
    if isinstance(body, dict) and body.get("mode"):
        mode = body["mode"]
        lines += ["", f"body ({mode}):"]
        if mode == "raw":
            lang = ((body.get("options") or {}).get("raw") or {}).get("language", "text")
            lines.append(f"  language={lang}")
            lines.append("  " + truncate(body.get("raw") or "", 400))
        elif mode in ("urlencoded", "formdata"):
            lines += _kv_list(body.get(mode), f"  {mode}") or ["  (empty)"]
        elif mode == "graphql":
            gql = body.get("graphql") or {}
            lines.append("  " + truncate(gql.get("query") or "", 300))
        else:
            lines.append(f"  ({mode})")
    auth = request.get("auth")
    if isinstance(auth, dict) and auth.get("type"):
        lines += ["", f"auth: {auth['type']} (값은 실행 시에만 사용, 여기선 미표시)"]
    return "\n".join(lines)


def format_response_headers(headers_text: str) -> str:
    out = []
    for line in headers_text.splitlines():
        if ":" not in line:
            if line.startswith("HTTP/"):
                out.append(line.strip())
            continue
        key, _, value = line.partition(":")
        out.append(f"  {key.strip()}: {redact_value(key, value.strip())}")
    return "\n".join(out)


# --- execution gate ---------------------------------------------------------
def classify_method(method: str) -> str:
    m = (method or "GET").upper()
    if m in SAFE_METHODS:
        return "safe"
    if m in CONFIRM_METHODS:
        return "confirm"
    if m in BLOCKED_METHODS:
        return "blocked"
    return "confirm"  # unknown verbs: treat as needing confirmation


def host_of(resolved_url: str) -> str:
    m = re.match(r"^[a-zA-Z][\w+.-]*://([^/]+)", resolved_url)
    host = m.group(1) if m else resolved_url.split("/", 1)[0]
    host = host.split("@")[-1].strip().lower()
    if host.startswith("["):  # [::1]:8080 — strip brackets, keep the address
        return host[1:].split("]", 1)[0]
    return host.split(":")[0]


def classify_env(resolved_url: str) -> str:
    if has_unresolved_vars(resolved_url):
        return "unknown"
    host = host_of(resolved_url)
    if not host:
        return "unknown"
    if host in LOCAL_HOSTS or host.startswith("127.") or host.endswith(LOCAL_SUFFIXES):
        return "local"
    # only the FIRST label counts: dev.example.com is local,
    # api.dev.evil.com is not (any-label matching was a gate bypass)
    if host.split(".", 1)[0] in LOCAL_LABELS:
        return "local"
    return "remote"


def execution_gate(method_class: str, env_class: str, confirmed: bool) -> tuple[bool, str]:
    """Return (allowed, reason). Auto-run only for safe+local; blocked never runs."""
    if method_class == "blocked":
        return False, "PUT/PATCH/DELETE는 이 스킬에서 실행할 수 없습니다 (파괴적 요청)."
    if method_class == "safe" and env_class == "local":
        return True, "safe method + local/dev env → 자동 실행 가능"
    if confirmed:
        return True, f"method={method_class} env={env_class} → 사용자 확인(--confirm)으로 실행"
    if method_class == "confirm":
        return False, f"POST(또는 비표준 메서드)는 사용자 확인이 필요합니다 (env={env_class}). 실행하려면 --confirm."
    return False, f"local/dev 환경이 아니므로 자동 실행하지 않습니다 (env={env_class}). 실행하려면 --confirm."


# --- cli plumbing -----------------------------------------------------------
def add_profile_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", help="config.json profile name")


def add_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--collection", help="Postman collection uid (cloud)")
    parser.add_argument("--file", help="local exported collection JSON path")


def resolve_source(args: argparse.Namespace) -> dict[str, Any]:
    if getattr(args, "file", None):
        return load_collection(args.file, is_file=True)
    if getattr(args, "collection", None):
        _name, profile = load_profile(getattr(args, "profile", None))
        return load_collection(args.collection, is_file=False, profile=profile)
    raise PostmanHelperError("--collection <uid> 또는 --file <path> 중 하나가 필요합니다.")


def build_varmap(collection: dict[str, Any], overrides: list[str] | None) -> dict[str, str]:
    varmap = collection_varmap(collection)
    for pair in overrides or []:
        if "=" not in pair:
            raise PostmanHelperError(f"--var 형식은 key=value 입니다: {pair}")
        key, _, value = pair.partition("=")
        varmap[key.strip()] = value
    return varmap


def run_main(parser_builder: Any) -> int:
    parser = parser_builder()
    args = parser.parse_args()
    try:
        return args.func(args)
    except PostmanHelperError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nerror: 입력이 취소되었습니다.", file=sys.stderr)
        return 1
