#!/usr/bin/env python3
"""Small Slack Web API helper that wraps curl and local JSON config."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_DIR = Path("~/.config/slack-helper").expanduser()
DEFAULT_BOT_SCOPES = ["team:read", "users:read", "channels:read"]
SLACK_API_BASE = "https://slack.com/api"
SLACK_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"


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
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.chmod(temp_name, stat.S_IRUSR | stat.S_IWUSR)
    os.replace(temp_name, path)


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
        headers = header_path.read_text(encoding="utf-8", errors="replace")
        body = body_path.read_text(encoding="utf-8", errors="replace")

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
) -> dict[str, Any]:
    status, headers, body = run_curl(
        url=f"{SLACK_API_BASE}/{method}",
        http_method=http_method,
        token=token,
        payload=payload or {},
        content_type=content_type,
    )
    if status == 429:
        retry_after = "unknown"
        match = re.search(r"(?im)^retry-after:\s*(\S+)", headers)
        if match:
            retry_after = match.group(1)
        raise SlackHelperError(f"Rate limited by Slack; retry after {retry_after} seconds")
    if status >= 400:
        raise SlackHelperError(f"Slack API {method} HTTP {status}: {body}")

    response = parse_json_body(body, method)
    if response.get("ok") is not True:
        error = response.get("error", "unknown_error")
        response["_method"] = method
        response["_slack_error"] = error
    return response


def load_oauth_app() -> dict[str, Any]:
    data = read_json(config_dir() / "oauth-app.json")
    for key in ("client_id", "client_secret"):
        if not data.get(key):
            raise SlackHelperError(f"oauth-app.json is missing required key: {key}")
    return data


def configured_scopes(oauth_app: dict[str, Any], args: argparse.Namespace) -> str:
    scopes = args.scopes or oauth_app.get("scopes") or DEFAULT_BOT_SCOPES
    if isinstance(scopes, str):
        return scopes
    if isinstance(scopes, list) and all(isinstance(item, str) for item in scopes):
        return ",".join(scopes)
    raise SlackHelperError("scopes must be a string or list of strings")


def oauth_url(args: argparse.Namespace) -> str:
    oauth_app = load_oauth_app()
    params = {
        "client_id": oauth_app["client_id"],
        "scope": configured_scopes(oauth_app, args),
    }
    redirect_uri = args.redirect_uri or oauth_app.get("redirect_uri")
    if redirect_uri:
        params["redirect_uri"] = redirect_uri
    if args.state:
        params["state"] = args.state
    if args.team:
        params["team"] = args.team
    return f"{SLACK_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def command_oauth_start(args: argparse.Namespace) -> int:
    url = oauth_url(args)
    print(url)
    if args.open:
        opened = webbrowser.open(url)
        if not opened:
            raise SlackHelperError("Could not open browser; use the printed URL manually")
    return 0


def workspace_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "default"


def command_oauth_finish(args: argparse.Namespace) -> int:
    oauth_app = load_oauth_app()
    payload = {
        "code": args.code,
        "client_id": oauth_app["client_id"],
        "client_secret": oauth_app["client_secret"],
    }
    redirect_uri = args.redirect_uri or oauth_app.get("redirect_uri")
    if redirect_uri:
        payload["redirect_uri"] = redirect_uri

    response = slack_method(
        "oauth.v2.access",
        payload=payload,
        content_type="form",
    )
    if response.get("ok") is not True:
        raise SlackHelperError(f"OAuth exchange failed: {response.get('error', response)}")

    team = response.get("team") if isinstance(response.get("team"), dict) else {}
    team_id = team.get("id")
    team_name = team.get("name") or team_id or "default"
    workspace = args.workspace or workspace_slug(str(team_name))

    api_key_path = config_dir() / "api-key.json"
    api_keys = read_json(api_key_path, required=False)
    workspaces = api_keys.setdefault("workspaces", {})
    workspaces[workspace] = {
        "token_type": response.get("token_type", "bot"),
        "token": response.get("access_token"),
        "team_id": team_id,
        "team_name": team.get("name"),
        "app_id": response.get("app_id"),
        "bot_user_id": response.get("bot_user_id"),
        "scope": response.get("scope"),
    }
    authed_user = response.get("authed_user")
    if isinstance(authed_user, dict) and authed_user.get("access_token"):
        workspaces[workspace]["authed_user"] = authed_user
    api_keys["default_workspace"] = workspace
    write_json_secure(api_key_path, api_keys)

    print(json.dumps({
        "ok": True,
        "workspace": workspace,
        "team_id": team_id,
        "team_name": team.get("name"),
        "scope": response.get("scope"),
        "api_key_path": str(api_key_path),
    }, ensure_ascii=False, indent=2))
    return 0


def load_workspace(name: str | None) -> tuple[str, dict[str, Any]]:
    api_keys = read_json(config_dir() / "api-key.json")
    workspace_name = name or api_keys.get("default_workspace")
    if not workspace_name:
        raise SlackHelperError("No workspace specified and no default_workspace is set")
    workspaces = api_keys.get("workspaces")
    if not isinstance(workspaces, dict) or workspace_name not in workspaces:
        raise SlackHelperError(f"Workspace not found in api-key.json: {workspace_name}")
    workspace = workspaces[workspace_name]
    if not isinstance(workspace, dict) or not workspace.get("token"):
        raise SlackHelperError(f"Workspace has no token: {workspace_name}")
    return workspace_name, workspace


def print_response(response: dict[str, Any]) -> int:
    print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def token_for(args: argparse.Namespace) -> str:
    _, workspace = load_workspace(args.workspace)
    return str(workspace["token"])


def command_auth_test(args: argparse.Namespace) -> int:
    return print_response(slack_method("auth.test", token=token_for(args)))


def command_team_info(args: argparse.Namespace) -> int:
    return print_response(slack_method("team.info", token=token_for(args)))


def command_read_sample(args: argparse.Namespace) -> int:
    token = token_for(args)
    response = slack_method("team.info", token=token)
    if response.get("ok") is True:
        return print_response(response)
    if response.get("_slack_error") != "missing_scope":
        return print_response(response)
    fallback = slack_method("auth.test", token=token)
    fallback["_fallback_reason"] = "team.info returned missing_scope"
    return print_response(fallback)


def command_users(args: argparse.Namespace) -> int:
    payload = {"limit": args.limit}
    return print_response(
        slack_method("users.list", token=token_for(args), payload=payload, http_method="GET")
    )


def command_channels(args: argparse.Namespace) -> int:
    payload = {
        "limit": args.limit,
        "types": args.types,
        "exclude_archived": "true" if args.exclude_archived else "false",
    }
    return print_response(
        slack_method(
            "conversations.list",
            token=token_for(args),
            payload=payload,
            http_method="GET",
        )
    )


def load_channel_id(channel: str) -> str:
    if re.match(r"^[CDG][A-Z0-9]+$", channel):
        return channel
    channel_info = read_json(config_dir() / "channel-info.json", required=False)
    channels = channel_info.get("channels", channel_info)
    if isinstance(channels, dict) and isinstance(channels.get(channel), str):
        return channels[channel]
    raise SlackHelperError(
        f"Unknown channel alias '{channel}'. Add it to channel-info.json or pass a Slack channel ID."
    )


def command_channel_history(args: argparse.Namespace) -> int:
    payload = {"channel": load_channel_id(args.channel), "limit": args.limit}
    return print_response(
        slack_method(
            "conversations.history",
            token=token_for(args),
            payload=payload,
            http_method="GET",
        )
    )


def add_workspace_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", help="Workspace key from api-key.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slack Web API helper using curl and ~/.config/slack-helper"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    oauth_start = subparsers.add_parser("oauth-start", help="Print or open Slack OAuth URL")
    oauth_start.add_argument("--open", action="store_true", help="Open the URL in a browser")
    oauth_start.add_argument("--scopes", help="Comma-separated bot scopes")
    oauth_start.add_argument("--redirect-uri", help="Override oauth-app.json redirect_uri")
    oauth_start.add_argument("--state", help="Optional OAuth state value")
    oauth_start.add_argument("--team", help="Optional Slack team ID hint")
    oauth_start.set_defaults(func=command_oauth_start)

    oauth_finish = subparsers.add_parser("oauth-finish", help="Exchange OAuth code for token")
    oauth_finish.add_argument("--code", required=True, help="Temporary code from redirect URL")
    oauth_finish.add_argument("--workspace", help="Workspace key to store in api-key.json")
    oauth_finish.add_argument("--redirect-uri", help="Override oauth-app.json redirect_uri")
    oauth_finish.set_defaults(func=command_oauth_finish)

    auth_test = subparsers.add_parser("auth-test", help="Call Slack auth.test")
    add_workspace_arg(auth_test)
    auth_test.set_defaults(func=command_auth_test)

    team_info = subparsers.add_parser("team-info", help="Call Slack team.info")
    add_workspace_arg(team_info)
    team_info.set_defaults(func=command_team_info)

    read_sample = subparsers.add_parser("read-sample", help="Read one Slack datum")
    add_workspace_arg(read_sample)
    read_sample.set_defaults(func=command_read_sample)

    users = subparsers.add_parser("users", help="Call Slack users.list")
    add_workspace_arg(users)
    users.add_argument("--limit", type=int, default=20)
    users.set_defaults(func=command_users)

    channels = subparsers.add_parser("channels", help="Call Slack conversations.list")
    add_workspace_arg(channels)
    channels.add_argument("--limit", type=int, default=20)
    channels.add_argument(
        "--types",
        default="public_channel",
        help="Slack conversation types, comma-separated",
    )
    channels.add_argument("--include-archived", dest="exclude_archived", action="store_false")
    channels.set_defaults(exclude_archived=True, func=command_channels)

    history = subparsers.add_parser("channel-history", help="Call Slack conversations.history")
    add_workspace_arg(history)
    history.add_argument("--channel", required=True, help="Channel ID or alias")
    history.add_argument("--limit", type=int, default=10)
    history.set_defaults(func=command_channel_history)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except SlackHelperError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
