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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


DEFAULT_CONFIG_DIR = Path("~/.config/slack-helper").expanduser()
CONFIG_FILE = "config.json"
USERS_CACHE_FILE = "users.json"
LEGACY_CONFIG_FILES = ("oauth-app.json", "api-key.json", "context.json", "channel-info.json")
DEFAULT_BOT_SCOPES = ["team:read", "users:read", "channels:read", "channels:history"]
DEFAULT_USER_SCOPES = [
    "search:read",
    "channels:read",
    "channels:history",
    "groups:read",
    "groups:history",
]
DEFAULT_REDIRECT_URI = "http://localhost:8765/slack-helper/callback"
SLACK_API_BASE = "https://slack.com/api"
SLACK_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
USER_ID_RE = re.compile(r"^[UW][A-Z0-9]+$")
CHANNEL_ID_RE = re.compile(r"^[CDG][A-Z0-9]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PERMALINK_RE = re.compile(r"/archives/([CDG][A-Z0-9]+)/p(\d{10})(\d{6})")
USER_MENTION_RE = re.compile(r"<@([UW][A-Z0-9]+)(?:\|([^>]*))?>")
CHANNEL_MENTION_RE = re.compile(r"<#([CDG][A-Z0-9]+)(?:\|([^>]*))?>")
SPECIAL_MENTION_RE = re.compile(r"<!(here|channel|everyone)(?:\|[^>]*)?>")
MAX_RETRY_AFTER_SECONDS = 60
MAX_USER_INFO_FETCH = 25


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


def users_cache_path() -> Path:
    return config_dir() / USERS_CACHE_FILE


def load_users_cache() -> dict[str, str]:
    """user ID → 표시 이름 캐시. 캐시는 보조 데이터라 어떤 오류에도 빈 dict로 넘어간다."""
    try:
        data = read_json(users_cache_path(), required=False)
    except (SlackHelperError, OSError):
        return {}
    users = data.get("users", data)
    if not isinstance(users, dict):
        return {}
    return {
        key: value
        for key, value in users.items()
        if isinstance(key, str) and isinstance(value, str) and value
    }


def save_users_cache(users: dict[str, str]) -> None:
    if not users:
        return
    merged = load_users_cache()
    merged.update(users)
    try:
        write_json_secure(users_cache_path(), {"users": merged})
    except OSError:
        pass


def member_display_name(member: dict[str, Any]) -> str:
    profile = member.get("profile") if isinstance(member.get("profile"), dict) else {}
    for value in (
        profile.get("display_name"),
        profile.get("real_name"),
        member.get("real_name"),
        member.get("name"),
    ):
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(member.get("id") or "-")


def update_users_cache_from_members(members: Any) -> dict[str, str]:
    if not isinstance(members, list):
        return {}
    users = {
        str(member["id"]): member_display_name(member)
        for member in members
        if isinstance(member, dict) and member.get("id")
    }
    save_users_cache(users)
    return users


def collect_user_ids(messages: Any) -> list[str]:
    """메시지 작성자와 본문 멘션에 등장하는 user ID를 중복 없이 모은다."""
    ids: list[str] = []
    if not isinstance(messages, list):
        return ids
    for message in messages:
        if not isinstance(message, dict):
            continue
        user = message.get("user")
        if isinstance(user, str) and USER_ID_RE.match(user):
            ids.append(user)
        for user_id, _label in USER_MENTION_RE.findall(message_display_text(message)):
            ids.append(user_id)
    return list(dict.fromkeys(ids))


def ensure_users_cached(
    user_ids: list[str], token: str, *, max_fetch: int = MAX_USER_INFO_FETCH
) -> dict[str, str]:
    """캐시에 없는 user ID를 users.info로 채운다. 보강 실패는 조용히 넘어간다."""
    cache = load_users_cache()
    unknown = [user_id for user_id in user_ids if user_id and user_id not in cache]
    fetched: dict[str, str] = {}
    for user_id in unknown[:max_fetch]:
        try:
            response = slack_method(
                "users.info", token=token, payload={"user": user_id}, http_method="GET"
            )
        except SlackHelperError:
            break
        member = response.get("user")
        if response.get("ok") is True and isinstance(member, dict):
            fetched[user_id] = member_display_name(member)
        elif response.get("_slack_error") in {
            "missing_scope",
            "not_authed",
            "invalid_auth",
            "token_revoked",
            "account_inactive",
        }:
            break
        else:
            # user_not_found 등 영구 실패 ID는 ID 그대로 캐시해 매 조회마다 재시도하지 않는다.
            fetched[user_id] = user_id
    if fetched:
        save_users_cache(fetched)
        cache.update(fetched)
    return cache


def users_for_messages(messages: Any, token: str) -> dict[str, str]:
    try:
        return ensure_users_cached(collect_user_ids(messages), token)
    except Exception:
        return load_users_cache()


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
            "User token이 없습니다. Slack App의 OAuth & Permissions > "
            "User Token Scopes에 search:read, channels:read, channels:history, "
            "groups:read, groups:history를 추가한 뒤 oauth-start와 oauth-finish를 "
            "다시 실행해 주세요."
        )
    return str(authed_user["access_token"])


def print_response(response: dict[str, Any]) -> int:
    print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _resolve_tz(tz_name: str | None) -> Any:
    if not tz_name:
        return datetime.now().astimezone().tzinfo
    try:
        return ZoneInfo(tz_name)
    except Exception as exc:
        raise SlackHelperError(f"알 수 없는 타임존입니다: {tz_name} (예: Asia/Seoul)") from exc


def day_bounds(date_str: str, tz_name: str | None = None, option: str = "--on") -> tuple[str, str]:
    """하루(자정~다음날 자정 직전)의 Slack ts 경계를 소수 6자리 epoch 문자열로 반환한다."""
    value = date_str.strip()
    if not DATE_RE.match(value):
        raise SlackHelperError(f"{option}은 YYYY-MM-DD 형식이어야 합니다 (입력값: {date_str})")
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SlackHelperError(f"{option} 날짜가 유효하지 않습니다 (입력값: {date_str})") from exc
    tz = _resolve_tz(tz_name)
    start = datetime.combine(day, datetime.min.time(), tzinfo=tz)
    next_start = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=tz)
    return f"{start.timestamp():.6f}", f"{next_start.timestamp() - 0.000001:.6f}"


def range_bounds(
    after: str | None, before: str | None, tz_name: str | None = None
) -> tuple[str | None, str | None]:
    """--after/--before 일자 범위(양끝 날짜 포함)의 Slack ts 경계를 반환한다."""
    oldest = day_bounds(after, tz_name, option="--after")[0] if after else None
    latest = day_bounds(before, tz_name, option="--before")[1] if before else None
    if oldest and latest and float(oldest) > float(latest):
        raise SlackHelperError("--after 날짜가 --before보다 늦습니다.")
    return oldest, latest


def parse_permalink(url: str) -> tuple[str, str]:
    """Slack permalink에서 (channel_id, ts)를 뽑는다. 답글 permalink면 thread_ts를 우선한다."""
    value = url.strip().strip('"').strip("'")
    parsed = urllib.parse.urlparse(value)
    match = PERMALINK_RE.search(parsed.path)
    if not match:
        raise SlackHelperError(
            "permalink에서 채널/ts를 찾지 못했습니다. "
            "https://<workspace>.slack.com/archives/<채널ID>/p<숫자16자리> 형태인지 확인해 주세요."
        )
    channel_id = match.group(1)
    ts = f"{match.group(2)}.{match.group(3)}"
    params = urllib.parse.parse_qs(parsed.query)
    thread_ts = (params.get("thread_ts") or [""])[0].strip()
    if thread_ts:
        ts = thread_ts
    cid = (params.get("cid") or [""])[0].strip().upper()
    if cid and CHANNEL_ID_RE.match(cid):
        channel_id = cid
    return channel_id, ts


def format_ts_local(ts: str | float | int, tz_name: str | None = None) -> str:
    value = str(ts).split(".", 1)[0]
    try:
        seconds = int(value)
    except ValueError:
        return str(ts)
    if tz_name:
        return datetime.fromtimestamp(seconds, tz=ZoneInfo(tz_name)).strftime("%Y-%m-%d %H:%M")
    return datetime.fromtimestamp(seconds).strftime("%Y-%m-%d %H:%M")


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


def _message_user_name(message: dict[str, Any], users: dict[str, str] | None = None) -> str:
    user = message.get("user")
    if isinstance(user, dict):
        return str(user.get("name") or user.get("id") or "-")
    if users and isinstance(user, str) and user in users:
        return users[user]
    return str(
        message.get("user_name")
        or message.get("username")
        or message.get("display_name")
        or user
        or "-"
    )


def resolve_mentions_in_text(text: str, users: dict[str, str] | None = None) -> str:
    """`<@U…>`/`<#C…|name>` 원시 멘션을 사람이 읽는 `@이름`/`#채널`로 바꾼다."""
    mapping = users or {}

    def _user(match: re.Match[str]) -> str:
        label = (match.group(2) or "").strip()
        name = label or mapping.get(match.group(1)) or match.group(1)
        return f"@{name}"

    def _channel(match: re.Match[str]) -> str:
        label = (match.group(2) or "").strip()
        return f"#{label or match.group(1)}"

    value = USER_MENTION_RE.sub(_user, text)
    value = CHANNEL_MENTION_RE.sub(_channel, value)
    return SPECIAL_MENTION_RE.sub(lambda match: f"@{match.group(1)}", value)


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
    users: dict[str, str] | None = None,
) -> str:
    channel = (channel_name or _message_channel_name(message)).lstrip("#")
    user = (user_name or _message_user_name(message, users)).lstrip("@")
    display = message_display_text(message)
    base = re.sub(r"\s+", " ", str(message.get("text") or "")).strip()
    limit = 120 if display == base else 200
    text = truncate_text(resolve_mentions_in_text(display, users), limit)
    permalink = str(message.get("permalink") or "-")
    return f"[{format_ts_local(message.get('ts', '-'))}] #{channel} @{user}: {text} | {permalink}"


def format_search_results(response: dict[str, Any], users: dict[str, str] | None = None) -> str:
    messages = response.get("messages")
    matches = messages.get("matches", []) if isinstance(messages, dict) else []
    lines = [
        format_message_line(match, users=users)
        for match in matches
        if isinstance(match, dict)
    ]
    return "\n".join(lines)


def format_history(
    response: dict[str, Any],
    channel: str | None = None,
    users: dict[str, str] | None = None,
) -> str:
    messages = response.get("messages", [])
    lines = [
        format_message_line(message, channel_name=channel, users=users)
        for message in messages
        if isinstance(message, dict)
    ]
    return "\n".join(lines)


def format_jsonl(
    messages: Any,
    channel: str | None = None,
    users: dict[str, str] | None = None,
) -> str:
    """임시 분석 스크립트용 한 줄 JSON. 본문은 자르지 않고 멘션만 치환한다."""
    lines: list[str] = []
    if not isinstance(messages, list):
        return ""
    for message in messages:
        if not isinstance(message, dict):
            continue
        user = message.get("user")
        user_id = str(user.get("id") or "") if isinstance(user, dict) else str(user or "")
        record: dict[str, Any] = {
            "ts": str(message.get("ts") or ""),
            "channel": channel or _message_channel_id(message),
        }
        channel_name = _message_channel_name(message)
        if channel_name not in ("-", record["channel"]):
            record["channel_name"] = channel_name
        if user_id:
            record["user"] = user_id
        user_name = _message_user_name(message, users)
        if user_name not in ("-", user_id):
            record["user_name"] = user_name
        record["text"] = resolve_mentions_in_text(message_display_text(message), users)
        for key in ("thread_ts", "reply_count"):
            if message.get(key) is not None:
                record[key] = message[key]
        if message.get("permalink"):
            record["permalink"] = str(message["permalink"])
        lines.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
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


def resolve_channel(value: str, token: str, *, types: str = "public_channel") -> str:
    """채널 ID는 그대로 쓰고, 채널 이름이면 conversations.list로 ID를 찾는다."""
    channel = value.strip().lstrip("#")
    if CHANNEL_ID_RE.match(channel):
        return channel
    cursor = ""
    while True:
        payload: dict[str, Any] = {
            "limit": 200,
            "types": types,
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


def validate_output_flags(args: Any) -> None:
    """--raw/--jsonl 충돌을 API 호출 전에 거른다. 명령 함수 첫 줄에서 호출한다."""
    if getattr(args, "raw", False) and getattr(args, "jsonl", False):
        raise SlackHelperError("--raw와 --jsonl은 동시에 쓸 수 없습니다.")


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
