#!/usr/bin/env python3
"""Shared Slack helper utilities for local CLI scripts."""

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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


DEFAULT_CONFIG_DIR = Path("~/.config/slack-helper").expanduser()
CONFIG_FILE = "config.json"
LEGACY_CONFIG_FILES = ("oauth-app.json", "api-key.json", "context.json", "channel-info.json")
DEFAULT_BOT_SCOPES = ["team:read", "users:read", "channels:read", "channels:history"]
DEFAULT_USER_SCOPES = ["search:read"]
DEFAULT_REDIRECT_URI = "http://localhost:8765/slack-helper/callback"
SLACK_API_BASE = "https://slack.com/api"
SLACK_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
USER_ID_RE = re.compile(r"^[UW][A-Z0-9]+$")
CHANNEL_ID_RE = re.compile(r"^[CDG][A-Z0-9]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_RETRY_AFTER_SECONDS = 60


class SlackHelperError(RuntimeError):
    pass


def config_dir() -> Path:
    override = os.environ.get("SLACK_HELPER_CONFIG_DIR")
    return Path(override).expanduser() if override else DEFAULT_CONFIG_DIR


def read_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise SlackHelperError(f"Missing config file: {path}")
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SlackHelperError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SlackHelperError(f"Expected a JSON object in {path}")
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


def split_scopes(value: str) -> list[str]:
    scopes = [scope.strip() for scope in value.split(",")]
    return [scope for scope in scopes if scope]


def normalize_user_identifier(value: str) -> str:
    return value.strip().lstrip("@").strip()


def user_identity_from_value(value: str, *, force_user_id: bool = False) -> dict[str, str]:
    normalized = normalize_user_identifier(value)
    if not normalized:
        return {}

    identity = {"identifier": normalized}
    upper_value = normalized.upper()
    if force_user_id or USER_ID_RE.match(upper_value):
        identity["user_id"] = upper_value
    return identity


def merge_user_identity(
    existing: dict[str, Any] | None,
    override: dict[str, str] | None = None,
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(existing, dict):
        merged.update({key: value for key, value in existing.items() if value})
    if override:
        merged.update({key: value for key, value in override.items() if value})
    return merged


def curl_config_quote(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def parse_json_body(body: str, method: str) -> dict[str, Any]:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SlackHelperError(f"Slack API {method} returned non-JSON body: {body}") from exc
    if not isinstance(payload, dict):
        raise SlackHelperError(f"Slack API {method} returned non-object JSON")
    return payload


def run_curl(
    *,
    url: str,
    http_method: str = "POST",
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    content_type: str = "json",
) -> tuple[int, str, str]:
    payload = payload or {}
    method = http_method.upper()

    if method == "GET" and payload:
        query = urllib.parse.urlencode(
            {key: value for key, value in payload.items() if value is not None}
        )
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"

    with tempfile.TemporaryDirectory(prefix="slack-helper-") as temp_dir:
        header_path = Path(temp_dir) / "headers.txt"
        body_path = Path(temp_dir) / "body.json"

        config_lines = [f'url = "{curl_config_quote(url)}"']
        config_lines.append(f'request = "{method}"')
        if token:
            config_lines.append(
                f'header = "Authorization: Bearer {curl_config_quote(token)}"'
            )
        if method != "GET":
            if content_type == "form":
                data = urllib.parse.urlencode(payload)
                config_lines.append('header = "Content-Type: application/x-www-form-urlencoded"')
            else:
                data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
                config_lines.append('header = "Content-Type: application/json"')
            config_lines.append(f'data = "{curl_config_quote(data)}"')

        command = [
            "curl",
            "--silent",
            "--show-error",
            "--location",
            "--connect-timeout",
            "10",
            "--max-time",
            "30",
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
        headers = (
            header_path.read_text(encoding="utf-8", errors="replace")
            if header_path.exists()
            else ""
        )
        body = (
            body_path.read_text(encoding="utf-8", errors="replace")
            if body_path.exists()
            else ""
        )

    if result.returncode != 0:
        raise SlackHelperError(result.stderr.strip() or "curl failed")
    try:
        status_code = int(result.stdout.strip()[-3:])
    except ValueError as exc:
        raise SlackHelperError(f"Could not parse curl HTTP status: {result.stdout}") from exc
    return status_code, headers, body


def slack_method(
    method: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    http_method: str = "POST",
    content_type: str = "json",
    retries: int = 1,
) -> dict[str, Any]:
    attempts_left = retries
    while True:
        status, headers, body = run_curl(
            url=f"{SLACK_API_BASE}/{method}",
            http_method=http_method,
            token=token,
            payload=payload or {},
            content_type=content_type,
        )
        if status != 429:
            break
        match = re.search(r"(?im)^retry-after:\s*(\S+)", headers)
        retry_after = match.group(1) if match else "unknown"
        wait_seconds = int(retry_after) if retry_after.isdigit() else None
        if attempts_left > 0 and wait_seconds is not None and wait_seconds <= MAX_RETRY_AFTER_SECONDS:
            attempts_left -= 1
            time.sleep(wait_seconds)
            continue
        raise SlackHelperError(f"Rate limited by Slack; retry after {retry_after} seconds")
    if status >= 400:
        raise SlackHelperError(f"Slack API {method} HTTP {status}: {body}")

    response = parse_json_body(body, method)
    if response.get("ok") is not True:
        error = response.get("error", "unknown_error")
        response["_method"] = method
        response["_slack_error"] = error
    return response


def config_path() -> Path:
    return config_dir() / CONFIG_FILE


def _memory_channel_lines(context: dict[str, Any], channel_info: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    channels = context.get("channels")
    if isinstance(channels, dict):
        for alias, entry in sorted(channels.items()):
            if not isinstance(entry, dict):
                continue
            channel_id = str(entry.get("id") or "-")
            note = str(entry.get("summary") or entry.get("name") or "").strip()
            lines.append(f"- {alias} — {channel_id}" + (f" — {note}" if note else ""))
    legacy = channel_info.get("channels", channel_info)
    if isinstance(legacy, dict):
        for alias, channel_id in sorted(legacy.items()):
            if isinstance(channel_id, str):
                lines.append(f"- {alias} — {channel_id}")
    return lines


def _migrate_channels_to_memory(context: dict[str, Any], channel_info: dict[str, Any]) -> None:
    lines = _memory_channel_lines(context, channel_info)
    if not lines:
        return
    memory_path = config_dir() / "MEMORY.md"
    existing = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
    if not existing:
        existing = "# slack-helper memory\n"
    block = "\n## 채널\n" + "\n".join(lines) + "\n"
    memory_path.write_text(existing.rstrip("\n") + "\n" + block, encoding="utf-8")
    os.chmod(memory_path, stat.S_IRUSR | stat.S_IWUSR)


def _migrate_legacy_config(target: Path) -> bool:
    """구버전 3분할 config(oauth-app/api-key/context)를 config.json 하나로 합친다."""
    directory = config_dir()
    oauth_app = read_json(directory / "oauth-app.json", required=False)
    api_keys = read_json(directory / "api-key.json", required=False)
    context = read_json(directory / "context.json", required=False)
    channel_info = read_json(directory / "channel-info.json", required=False)
    if not oauth_app and not api_keys:
        return False

    config: dict[str, Any] = {}
    app = {key: value for key, value in oauth_app.items() if key != "user_identity"}
    if app:
        config["app"] = app
    if api_keys.get("default_workspace"):
        config["default_workspace"] = api_keys["default_workspace"]
    workspaces = api_keys.get("workspaces")
    config["workspaces"] = workspaces if isinstance(workspaces, dict) else {}

    context_me = context.get("me")
    oauth_identity = oauth_app.get("user_identity")
    fallback_identity = merge_user_identity(
        context_me if isinstance(context_me, dict) else None,
        oauth_identity if isinstance(oauth_identity, dict) else None,
    )
    for workspace in config["workspaces"].values():
        if not isinstance(workspace, dict):
            continue
        existing = workspace.get("user_identity")
        merged = merge_user_identity(
            fallback_identity, existing if isinstance(existing, dict) else None
        )
        if merged:
            workspace["user_identity"] = merged

    write_json_secure(target, config)
    _migrate_channels_to_memory(context, channel_info)
    for name in LEGACY_CONFIG_FILES:
        legacy_path = directory / name
        if legacy_path.exists():
            legacy_path.unlink()
    return True


def load_config(*, required: bool = True) -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        _migrate_legacy_config(path)
    return read_json(path, required=required)


def save_config(data: dict[str, Any]) -> None:
    write_json_secure(config_path(), data)


def load_workspace(name: str | None) -> tuple[str, dict[str, Any]]:
    config = load_config()
    workspace_name = name or config.get("default_workspace")
    if not workspace_name:
        raise SlackHelperError("No workspace specified and no default_workspace is set")
    workspaces = config.get("workspaces")
    if not isinstance(workspaces, dict) or workspace_name not in workspaces:
        raise SlackHelperError(f"Workspace not found in config.json ({workspace_name})")
    workspace = workspaces[workspace_name]
    if not isinstance(workspace, dict) or not workspace.get("token"):
        raise SlackHelperError(f"Workspace has no token: {workspace_name}")
    return workspace_name, workspace


def load_workspace_identity(workspace: dict[str, Any]) -> dict[str, Any]:
    identity = workspace.get("user_identity")
    return identity if isinstance(identity, dict) else {}


def token_for(args: Any) -> str:
    _, workspace = load_workspace(args.workspace)
    return str(workspace["token"])


def user_token_for(args: Any) -> str:
    _, workspace = load_workspace(args.workspace)
    authed_user = workspace.get("authed_user")
    if not isinstance(authed_user, dict) or not authed_user.get("access_token"):
        raise SlackHelperError(
            "검색용 User token이 없습니다. Slack App의 OAuth & Permissions > "
            "User Token Scopes에 search:read를 추가한 뒤 oauth-start와 oauth-finish를 "
            "다시 실행해 주세요."
        )
    return str(authed_user["access_token"])


def print_response(response: dict[str, Any]) -> int:
    print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def day_bounds(date_str: str, tz_name: str | None = None) -> tuple[str, str]:
    """하루(자정~다음날 자정 직전)의 Slack ts 경계를 소수 6자리 epoch 문자열로 반환한다."""
    value = date_str.strip()
    if not DATE_RE.match(value):
        raise SlackHelperError(f"--on은 YYYY-MM-DD 형식이어야 합니다 (입력값: {date_str})")
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SlackHelperError(f"--on 날짜가 유효하지 않습니다 (입력값: {date_str})") from exc
    tz = ZoneInfo(tz_name) if tz_name else datetime.now().astimezone().tzinfo
    start = datetime.combine(day, datetime.min.time(), tzinfo=tz)
    next_start = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=tz)
    return f"{start.timestamp():.6f}", f"{next_start.timestamp() - 0.000001:.6f}"


def format_ts_utc(ts: str | float | int) -> str:
    value = str(ts).split(".", 1)[0]
    try:
        seconds = int(value)
    except ValueError:
        return str(ts)
    return datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def truncate_text(text: str, limit: int = 120) -> str:
    normalized = re.sub(r"\s+", " ", str(text)).strip()
    if len(normalized) <= limit:
        return normalized
    if limit <= 3:
        return "." * limit
    return normalized[: limit - 3] + "..."


def _message_channel_id(message: dict[str, Any]) -> str:
    channel = message.get("channel")
    if isinstance(channel, dict):
        return str(channel.get("id") or channel.get("name") or "-")
    return str(message.get("channel_id") or channel or "-")


def _message_channel_name(message: dict[str, Any]) -> str:
    channel = message.get("channel")
    if isinstance(channel, dict):
        return str(channel.get("name") or channel.get("id") or "-").lstrip("#")
    return str(message.get("channel_name") or message.get("channel_id") or channel or "-").lstrip("#")


def _message_user_name(message: dict[str, Any]) -> str:
    user = message.get("user")
    if isinstance(user, dict):
        return str(user.get("name") or user.get("id") or "-")
    return str(
        message.get("user_name")
        or message.get("username")
        or message.get("display_name")
        or user
        or "-"
    )


def _block_texts(blocks: Any) -> list[str]:
    texts: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "text" and isinstance(value, str):
                    texts.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(blocks)
    return texts


def _attachment_texts(attachments: Any) -> list[str]:
    texts: list[str] = []
    if not isinstance(attachments, list):
        return texts
    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue
        parts = [
            value
            for value in (attachment.get(key) for key in ("title", "pretext", "text"))
            if isinstance(value, str) and value.strip()
        ]
        if not parts and isinstance(attachment.get("fallback"), str):
            parts = [attachment["fallback"]]
        fields = attachment.get("fields")
        if isinstance(fields, list):
            for field in fields:
                if not isinstance(field, dict):
                    continue
                for key in ("title", "value"):
                    value = field.get(key)
                    if isinstance(value, str) and value.strip():
                        parts.append(value)
        texts.extend(parts)
        texts.extend(_block_texts(attachment.get("blocks")))
    return texts


def message_display_text(message: dict[str, Any]) -> str:
    """봇 알림처럼 text가 비고 attachment/block에만 본문이 있는 메시지도 compact 출력에서 읽히게 합친다."""
    base = re.sub(r"\s+", " ", str(message.get("text") or "")).strip()
    parts: list[str] = [base] if base else []
    seen: set[str] = set(parts)
    extras = [
        *_attachment_texts(message.get("attachments")),
        *_block_texts(message.get("blocks")),
    ]
    for raw in extras:
        normalized = re.sub(r"\s+", " ", raw).strip()
        if not normalized or normalized in seen or (base and normalized in base):
            continue
        seen.add(normalized)
        parts.append(normalized)
    return " · ".join(parts)


def format_message_line(
    message: dict[str, Any],
    channel_name: str | None = None,
    user_name: str | None = None,
) -> str:
    channel = (channel_name or _message_channel_name(message)).lstrip("#")
    user = (user_name or _message_user_name(message)).lstrip("@")
    display = message_display_text(message)
    base = re.sub(r"\s+", " ", str(message.get("text") or "")).strip()
    text = truncate_text(display, 120 if display == base else 200)
    permalink = str(message.get("permalink") or "-")
    return f"[{format_ts_utc(message.get('ts', '-'))}] #{channel} @{user}: {text} | {permalink}"


def format_search_results(response: dict[str, Any]) -> str:
    messages = response.get("messages")
    matches = messages.get("matches", []) if isinstance(messages, dict) else []
    lines = [
        format_message_line(match)
        for match in matches
        if isinstance(match, dict)
    ]
    return "\n".join(lines)


def format_history(response: dict[str, Any], channel: str | None = None) -> str:
    messages = response.get("messages", [])
    lines = [
        format_message_line(message, channel_name=channel)
        for message in messages
        if isinstance(message, dict)
    ]
    return "\n".join(lines)


def format_channels(response: dict[str, Any]) -> str:
    channels = response.get("channels", [])
    lines = []
    for channel in channels:
        if not isinstance(channel, dict):
            continue
        fields = [
            str(channel.get("id") or "-"),
            str(channel.get("name") or "-"),
            f"private={bool(channel.get('is_private'))}",
        ]
        if channel.get("num_members") is not None:
            fields.append(f"members={channel.get('num_members')}")
        lines.append("\t".join(fields))
    return "\n".join(lines)


def format_users(response: dict[str, Any]) -> str:
    members = response.get("members", [])
    lines = []
    for member in members:
        if not isinstance(member, dict):
            continue
        profile = member.get("profile") if isinstance(member.get("profile"), dict) else {}
        display = profile.get("display_name") or profile.get("real_name") or member.get("real_name") or "-"
        lines.append("\t".join([str(member.get("id") or "-"), str(member.get("name") or "-"), str(display)]))
    return "\n".join(lines)


def resolve_channel(value: str, token: str) -> str:
    """채널 ID는 그대로 쓰고, 채널 이름이면 conversations.list로 ID를 찾는다."""
    channel = value.strip().lstrip("#")
    if CHANNEL_ID_RE.match(channel):
        return channel
    cursor = ""
    while True:
        payload: dict[str, Any] = {
            "limit": 200,
            "types": "public_channel",
            "exclude_archived": "true",
        }
        if cursor:
            payload["cursor"] = cursor
        response = slack_method(
            "conversations.list", token=token, payload=payload, http_method="GET"
        )
        if response.get("ok") is not True:
            raise SlackHelperError(
                f"conversations.list failed: {response.get('error', response)}"
            )
        for entry in response.get("channels", []):
            if isinstance(entry, dict) and entry.get("name") == channel and entry.get("id"):
                return str(entry["id"])
        metadata = response.get("response_metadata")
        cursor = str(metadata.get("next_cursor") or "") if isinstance(metadata, dict) else ""
        if not cursor:
            break
    raise SlackHelperError(
        f"'{value}' 채널을 찾지 못했습니다. slack_read.py channels로 채널 이름/ID를 확인해 주세요."
    )


def add_workspace_arg(parser: Any) -> None:
    parser.add_argument("--workspace", help="config.json에 저장된 workspace 이름")


def print_compact_or_raw(response: dict[str, Any], formatter: str | Any, *, raw: bool = False) -> int:
    if raw:
        return print_response(response)
    text = formatter(response) if callable(formatter) else str(formatter)
    if text:
        print(text)
    return 0


def run_main(parser_builder: Any) -> int:
    parser = parser_builder()
    args = parser.parse_args()
    try:
        return args.func(args)
    except SlackHelperError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nerror: 입력이 취소되었습니다.", file=sys.stderr)
        return 1
