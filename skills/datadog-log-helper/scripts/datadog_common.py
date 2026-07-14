#!/usr/bin/env python3
"""Shared Datadog log helper utilities."""

from __future__ import annotations

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
from zoneinfo import ZoneInfo


DEFAULT_CONFIG_DIR = Path("~/.config/datadog-log-helper").expanduser()
CONFIG_FILE = "config.json"
MEMORY_FILE = "MEMORY.md"
DEFAULT_SITE = "datadoghq.com"
DEFAULT_FROM = "now-15m"
DEFAULT_TO = "now"
DEFAULT_LIMIT = 20
MAX_LIMIT = 1000
MAX_RETRY_AFTER_SECONDS = 60

SITE_ALIASES = {
    "us1": "datadoghq.com",
    "datadoghq.com": "datadoghq.com",
    "app.datadoghq.com": "datadoghq.com",
    "us3": "us3.datadoghq.com",
    "us3.datadoghq.com": "us3.datadoghq.com",
    "us5": "us5.datadoghq.com",
    "us5.datadoghq.com": "us5.datadoghq.com",
    "eu": "datadoghq.eu",
    "datadoghq.eu": "datadoghq.eu",
    "app.datadoghq.eu": "datadoghq.eu",
    "ap1": "ap1.datadoghq.com",
    "ap1.datadoghq.com": "ap1.datadoghq.com",
    "ap2": "ap2.datadoghq.com",
    "ap2.datadoghq.com": "ap2.datadoghq.com",
    "gov": "ddog-gov.com",
    "ddog-gov.com": "ddog-gov.com",
}


class DatadogHelperError(RuntimeError):
    pass


def config_dir() -> Path:
    override = os.environ.get("DATADOG_LOG_HELPER_CONFIG_DIR")
    return Path(override).expanduser() if override else DEFAULT_CONFIG_DIR


def config_path() -> Path:
    return config_dir() / CONFIG_FILE


def memory_path() -> Path:
    return config_dir() / MEMORY_FILE


def read_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise DatadogHelperError(f"Missing config file: {path}")
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise DatadogHelperError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise DatadogHelperError(f"Expected a JSON object in {path}")
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
            "# datadog-log-helper memory\n\n"
            "## 서비스 별칭\n\n"
            "## 로그 접근\n\n"
            "## 로그 스키마\n\n"
            "## 자주 쓰는 쿼리\n\n"
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


def normalize_site(value: str | None) -> str:
    raw = (value or DEFAULT_SITE).strip().lower()
    raw = re.sub(r"^https?://", "", raw).split("/", 1)[0]
    if raw.startswith("api."):
        raw = raw[4:]
    return SITE_ALIASES.get(raw, raw)


def api_base(site: str) -> str:
    normalized = normalize_site(site)
    return f"https://api.{normalized}"


def load_profile(name: str | None = None) -> tuple[str, dict[str, Any]]:
    config = load_config()
    profile_name = name or config.get("default_profile") or "default"
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise DatadogHelperError(f"Profile not found in config.json ({profile_name})")
    profile = profiles[profile_name]
    if not isinstance(profile, dict):
        raise DatadogHelperError(f"Profile must be an object: {profile_name}")
    for key in ("site", "api_key", "app_key"):
        if not profile.get(key):
            raise DatadogHelperError(f"Profile '{profile_name}' has no {key}")
    return profile_name, profile


def mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def sanitize_sensitive(text: str, profile: dict[str, Any] | None = None) -> str:
    sanitized = text
    if profile:
        for key in ("api_key", "app_key"):
            secret = str(profile.get(key) or "")
            if secret:
                sanitized = sanitized.replace(secret, mask_secret(secret))
    sanitized = re.sub(r"(DD-API-KEY:\s*)\S+", r"\1***", sanitized, flags=re.I)
    sanitized = re.sub(r"(DD-APPLICATION-KEY:\s*)\S+", r"\1***", sanitized, flags=re.I)
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

    with tempfile.TemporaryDirectory(prefix="datadog-log-helper-") as temp_dir:
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
        raise DatadogHelperError(result.stderr.strip() or "curl failed")
    try:
        status_code = int(result.stdout.strip()[-3:])
    except ValueError as exc:
        raise DatadogHelperError(f"Could not parse curl HTTP status: {result.stdout}") from exc
    return status_code, headers_text, body_text


def parse_json_body(body: str, label: str) -> dict[str, Any]:
    if not body.strip():
        return {}
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DatadogHelperError(f"Datadog API {label} returned non-JSON body: {body}") from exc
    if not isinstance(data, dict):
        raise DatadogHelperError(f"Datadog API {label} returned non-object JSON")
    return data


def retry_after_message(headers: str) -> str:
    for name in ("retry-after", "x-ratelimit-reset", "x-ratelimit-period"):
        match = re.search(rf"(?im)^{re.escape(name)}:\s*(\S+)", headers)
        if match:
            return f"{name}={match.group(1)}"
    return "retry later"


def datadog_request(
    profile: dict[str, Any],
    path: str,
    *,
    http_method: str = "GET",
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    require_app_key: bool = True,
    retries: int = 1,
) -> dict[str, Any]:
    base = api_base(str(profile.get("site") or DEFAULT_SITE))
    url = f"{base}{path}"
    if query:
        params = urllib.parse.urlencode(
            {key: value for key, value in query.items() if value is not None}
        )
        if params:
            url = f"{url}?{params}"
    headers = {
        "Accept": "application/json",
        "DD-API-KEY": str(profile["api_key"]),
    }
    if require_app_key:
        headers["DD-APPLICATION-KEY"] = str(profile["app_key"])

    attempts_left = retries
    while True:
        status, response_headers, body = run_curl(
            url=url, http_method=http_method, headers=headers, payload=payload
        )
        if status != 429:
            break
        detail = retry_after_message(response_headers)
        wait_match = re.search(r"(?:retry-after|x-ratelimit-reset)=(\d+)", detail)
        wait_seconds = int(wait_match.group(1)) if wait_match else None
        if attempts_left > 0 and wait_seconds is not None and wait_seconds <= MAX_RETRY_AFTER_SECONDS:
            attempts_left -= 1
            time.sleep(wait_seconds)
            continue
        raise DatadogHelperError(f"Datadog API rate limited: {detail}")

    data = parse_json_body(body, path)
    if status >= 400:
        detail = json.dumps(data, ensure_ascii=False) if data else body
        raise DatadogHelperError(
            sanitize_sensitive(f"Datadog API {path} HTTP {status}: {detail}", profile)
        )
    return data


def print_response(response: dict[str, Any]) -> int:
    print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def truncate_text(text: str, limit: int = 240) -> str:
    normalized = re.sub(r"\s+", " ", str(text)).strip()
    if len(normalized) <= limit:
        return normalized
    if limit <= 3:
        return "." * limit
    return normalized[: limit - 3] + "..."


def format_timestamp(value: Any, tz_name: str | None = None) -> str:
    if not value:
        return "-"
    text = str(value)
    try:
        normalized = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        tz = ZoneInfo(tz_name) if tz_name else datetime.now().astimezone().tzinfo
        return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    except ValueError:
        return text


def _attrs(event: dict[str, Any]) -> dict[str, Any]:
    attrs = event.get("attributes")
    return attrs if isinstance(attrs, dict) else {}


def _custom_attrs(event: dict[str, Any]) -> dict[str, Any]:
    attrs = _attrs(event).get("attributes")
    return attrs if isinstance(attrs, dict) else {}


def event_field(event: dict[str, Any], key: str) -> str:
    attrs = _attrs(event)
    custom = _custom_attrs(event)
    value = attrs.get(key)
    if value is None:
        value = custom.get(key)
    return str(value) if value is not None else "-"


def event_env(event: dict[str, Any]) -> str:
    value = event_field(event, "env")
    if value != "-":
        return value
    tags = _attrs(event).get("tags")
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str) and tag.startswith("env:"):
                return tag.split(":", 1)[1]
    return "-"


def event_trace_id(event: dict[str, Any]) -> str:
    for key in ("trace_id", "dd.trace_id", "traceId"):
        value = event_field(event, key)
        if value != "-":
            return value
    return "-"


def format_log_event(event: dict[str, Any], *, tz_name: str | None = None) -> str:
    attrs = _attrs(event)
    timestamp = format_timestamp(attrs.get("timestamp"), tz_name)
    status = event_field(event, "status")
    service = event_field(event, "service")
    env = event_env(event)
    host = event_field(event, "host")
    message = truncate_text(str(attrs.get("message") or event_field(event, "message")))
    event_id = str(event.get("id") or "-")
    trace_id = event_trace_id(event)
    lines = [
        f"[{timestamp}] status={status} service={service} env={env} host={host}",
        message,
        f"id={event_id} trace_id={trace_id}",
    ]
    return "\n".join(lines)


def format_log_events(response: dict[str, Any], *, tz_name: str | None = None) -> str:
    events = response.get("data")
    if not isinstance(events, list):
        return ""
    blocks = [
        format_log_event(event, tz_name=tz_name)
        for event in events
        if isinstance(event, dict)
    ]
    return "\n\n".join(blocks)


SENSITIVE_KEY_PATTERN = re.compile(
    r"(authorization|cookie|set-cookie|token|secret|password|passwd|api[-_]?key|"
    r"app[-_]?key|credential|session)",
    re.I,
)


def collect_key_paths(
    obj: Any,
    prefix: str = "",
    out: dict[str, str] | None = None,
    max_depth: int = 6,
) -> dict[str, str]:
    """Walk a nested dict and collect dotted key paths with a truncated sample value.

    Values under sensitive-looking keys (authorization, cookie, token, ...) are redacted.
    """
    if out is None:
        out = {}
    if max_depth < 0:
        return out
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                collect_key_paths(value, path, out, max_depth - 1)
                continue
            if SENSITIVE_KEY_PATTERN.search(str(key)):
                out.setdefault(path, "***redacted***")
            elif isinstance(value, list):
                sample = truncate_text(json.dumps(value, ensure_ascii=False), 80)
                out.setdefault(path, sample)
            else:
                out.setdefault(path, truncate_text(str(value), 80))
    return out


def extract_frames(text: str, prefix: str) -> list[str]:
    """Extract unique Java-style stack frames matching a package prefix, in order."""
    pattern = rf"at\s+({re.escape(prefix)}[\w.$<>]+)\(([^)]*)\)"
    seen: list[str] = []
    for method, location in re.findall(pattern, text):
        frame = f"{method}({location})" if location else method
        if frame not in seen:
            seen.append(frame)
    return seen


def append_filter(query: str, fragment: str | None) -> str:
    if not fragment:
        return query
    query = query.strip()
    return f"{query} {fragment}".strip() if query else fragment


def add_profile_arg(parser: Any) -> None:
    parser.add_argument("--profile", help="config.json profile name")


def run_main(parser_builder: Any) -> int:
    parser = parser_builder()
    args = parser.parse_args()
    try:
        return args.func(args)
    except DatadogHelperError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nerror: 입력이 취소되었습니다.", file=sys.stderr)
        return 1
