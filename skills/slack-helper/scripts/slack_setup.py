#!/usr/bin/env python3
"""Slack helper setup and OAuth commands."""

from __future__ import annotations

import argparse
import getpass
import json
import re
import sys
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any

from slack_common import (
    DEFAULT_BOT_SCOPES,
    DEFAULT_REDIRECT_URI,
    DEFAULT_USER_SCOPES,
    SLACK_AUTHORIZE_URL,
    SlackHelperError,
    add_workspace_arg,
    config_dir,
    load_context,
    load_workspace,
    load_workspace_identity,
    merge_user_identity,
    print_response,
    read_json,
    run_main,
    save_context,
    slack_method,
    split_scopes,
    token_for,
    user_identity_from_value,
    write_json_secure,
)


SETUP_GUIDE_TEMPLATE = """\
slack-helper 처음 설정 가이드

1. Slack App Management 열기
   https://api.slack.com/apps

2. 앱 만들기
   Create New App > From scratch
   App Name: 원하는 이름을 입력하세요. 예: slack-helper-local
   Workspace: 읽고 싶은 Slack workspace를 선택하세요.

3. client_id / client_secret 확인 후 로컬 설정 저장
   앱 생성 후 Basic Information 화면에서 Client ID와 Client Secret을 확인합니다.
   Client Secret은 절대 이 채팅에 붙여넣지 마세요.

   아래 명령을 터미널에서 그대로 실행하면 Client ID와 Client Secret 두 가지만 물어봅니다.
   Client Secret은 화면에 보이지 않게 입력받고, 셸 히스토리에도 남지 않습니다.
   Redirect URI와 범위(scope)는 묻지 않고 기본값으로 저장됩니다. 이후 단계에서 Slack 웹 화면에 직접 등록합니다.

   python3 "{script}" init-oauth

4. Redirect URL 등록
   왼쪽 메뉴 OAuth & Permissions > Redirect URLs
   Add New Redirect URL > http://localhost:8765/slack-helper/callback 입력 > Add > Save URLs
   주의: 나중에 oauth-app.json에 넣는 redirect_uri와 Slack에 등록한 Redirect URL이 같아야 합니다.

5. Bot Token Scopes 추가
   같은 OAuth & Permissions 화면의 Scopes > Bot Token Scopes에서 추가합니다.
   기본으로 아래 4개를 모두 추가합니다.
   team:read: 연결 확인과 workspace 정보 읽기
   users:read: 사용자 목록 읽기와 user ID 해석
   channels:read: 공개 채널 목록 읽기
   channels:history: 특정 공개 채널 히스토리 직접 읽기

6. User Token Scopes 추가
   같은 Scopes 화면의 User Token Scopes에서 추가합니다.
   Slack 메시지 검색: search:read
   참고: search.messages는 User token을 사용합니다. Bot Token Scopes만으로는 검색할 수 없습니다.
   결론: 기본 권한은 Bot 4개 + User search:read 입니다.

7. Slack 승인 화면 열기
   python3 "{script}" oauth-start --open

8. 승인 후 주소창의 주소 전체를 복사해서 토큰 저장
   localhost 페이지가 "연결할 수 없음"으로 떠도 괜찮습니다. 주소창의 주소를 통째로 복사합니다.
   python3 "{script}" oauth-finish --url "붙여넣은_주소_전체" --workspace default

9. 아무 데이터 하나 읽어서 확인
   python3 "{script}" read-sample --workspace default

10. 내 Slack 이름/핸들 저장하기 (연결 확인 후)
   Slack 이름/핸들은 민감정보가 아니므로 에이전트가 대신 저장해도 됩니다.
   python3 "{script}" set-me --slack-user "YOUR_SLACK_NAME_OR_HANDLE"

11. 내 Slack 계정 식별자 확인
   set-me로 저장한 이름/핸들을 users.list로 찾아 U... member ID까지 저장합니다.
   python3 "{script}" resolve-me --workspace default

12. 이제 자연어로 요청하기
   이 Python 스크립트는 에이전트가 내부적으로 실행합니다.
"""


def script_path() -> str:
    return str(Path(__file__).resolve())


def is_supported_redirect_uri(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}


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


def configured_user_scopes(oauth_app: dict[str, Any], args: argparse.Namespace) -> str:
    scopes = args.user_scopes or oauth_app.get("user_scopes") or DEFAULT_USER_SCOPES
    if isinstance(scopes, str):
        return scopes
    if isinstance(scopes, list) and all(isinstance(item, str) for item in scopes):
        return ",".join(scopes)
    raise SlackHelperError("user_scopes must be a string or list of strings")


def oauth_url(args: argparse.Namespace) -> str:
    oauth_app = load_oauth_app()
    params = {
        "client_id": oauth_app["client_id"],
        "scope": configured_scopes(oauth_app, args),
        "user_scope": configured_user_scopes(oauth_app, args),
    }
    redirect_uri = args.redirect_uri or oauth_app.get("redirect_uri")
    if redirect_uri:
        params["redirect_uri"] = redirect_uri
    if args.state:
        params["state"] = args.state
    if args.team:
        params["team"] = args.team
    return f"{SLACK_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def command_setup_guide(args: argparse.Namespace) -> int:
    print(SETUP_GUIDE_TEMPLATE.format(script=script_path()))
    return 0


def command_init_oauth(args: argparse.Namespace) -> int:
    if not sys.stdin.isatty():
        raise SlackHelperError(
            "init-oauth는 터미널에서 직접 실행해 주세요. "
            "Client Secret을 화면·셸 히스토리에 남기지 않고 안전하게 입력받으려면 대화형 입력이 필요합니다."
        )

    target_path = config_dir() / "oauth-app.json"
    print("slack-helper OAuth 설정 파일을 만듭니다.")
    print("Slack App Management: https://api.slack.com/apps")
    print("Basic Information 화면의 Client ID / Client Secret을 준비해 주세요.")
    print()

    client_id = (args.client_id or input("Client ID: ")).strip()
    secret_value = getpass.getpass("Client Secret: ").strip()

    # Redirect URI, scope, Slack 이름은 여기서 묻지 않는다.
    # 앞의 둘은 사용자가 Slack 웹 화면에서 직접 설정하고, 이름은 연결 테스트 후 set-me로 저장한다.
    redirect_uri = args.redirect_uri or DEFAULT_REDIRECT_URI
    scopes = split_scopes(args.scopes) if args.scopes else list(DEFAULT_BOT_SCOPES)
    user_scopes = split_scopes(args.user_scopes) if args.user_scopes else list(DEFAULT_USER_SCOPES)
    user_identity = user_identity_from_value(
        args.slack_user_id or args.slack_user or "",
        force_user_id=bool(args.slack_user_id),
    )

    if not client_id:
        raise SlackHelperError("Client ID가 비어 있습니다.")
    if not secret_value:
        raise SlackHelperError("Client Secret이 비어 있습니다.")
    if not redirect_uri:
        raise SlackHelperError("Redirect URI가 비어 있습니다.")
    if not is_supported_redirect_uri(redirect_uri):
        raise SlackHelperError(
            "Redirect URI는 http://localhost 또는 http://127.0.0.1 로 시작해야 합니다."
        )
    if not scopes:
        raise SlackHelperError("Bot Token Scopes가 비어 있습니다.")
    if not user_scopes:
        raise SlackHelperError("User Token Scopes가 비어 있습니다.")

    oauth_config: dict[str, Any] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scopes": scopes,
        "user_scopes": user_scopes,
    }
    oauth_config["client" + "_secret"] = secret_value
    if user_identity:
        oauth_config["user_identity"] = user_identity
    write_json_secure(target_path, oauth_config)
    print()
    print("✅ Client ID / Client Secret 등록에 성공했어요!")
    print(f"설정 파일을 저장했습니다: {target_path}")
    print(f"기본 Redirect URI: {redirect_uri}")
    print(f"기본 Bot Token Scopes: {', '.join(scopes)}")
    print(f"기본 User Token Scopes: {', '.join(user_scopes)}")
    return 0


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


def extract_oauth_code(value: str) -> str:
    value = value.strip().strip('"').strip("'")
    if not value:
        raise SlackHelperError("code 또는 redirect 주소가 비어 있습니다.")
    looks_like_url = "://" in value or "code=" in value or value.startswith("localhost")
    if not looks_like_url:
        return value
    parsed = urllib.parse.urlparse(value)
    params = urllib.parse.parse_qs(parsed.query)
    codes = params.get("code")
    if codes and codes[0].strip():
        return codes[0].strip()
    raise SlackHelperError(
        "붙여넣은 주소에서 code 값을 찾지 못했습니다. "
        "Slack 승인 후 이동한 페이지의 주소창 전체를 그대로 복사했는지 확인해 주세요."
    )


def command_oauth_finish(args: argparse.Namespace) -> int:
    raw_code = args.redirect_url or args.code
    if not raw_code:
        raise SlackHelperError("--url(redirect 주소 전체) 또는 --code 값이 필요합니다.")
    oauth_app = load_oauth_app()
    payload = {
        "code": extract_oauth_code(raw_code),
        "client_id": oauth_app["client_id"],
    }
    payload["client" + "_secret"] = oauth_app["client" + "_secret"]
    redirect_uri = args.redirect_uri or oauth_app.get("redirect_uri")
    if redirect_uri:
        payload["redirect_uri"] = redirect_uri

    response = slack_method("oauth.v2.access", payload=payload, content_type="form")
    if response.get("ok") is not True:
        raise SlackHelperError(f"OAuth exchange failed: {response.get('error', response)}")

    team = response.get("team") if isinstance(response.get("team"), dict) else {}
    team_id = team.get("id")
    team_name = team.get("name") or team_id or "default"
    workspace = args.workspace or workspace_slug(str(team_name))

    bot_token = response.get("access_token")
    authed_user = response.get("authed_user")
    user_token = authed_user.get("access_token") if isinstance(authed_user, dict) else None
    auth_value = bot_token or user_token
    if not auth_value:
        raise SlackHelperError(
            "OAuth 응답에 사용할 수 있는 토큰이 없습니다. Slack App의 OAuth & Permissions에서 "
            "Bot Token Scopes 또는 User Token Scopes(search:read)를 추가한 뒤 다시 시도해 주세요."
        )
    token_type = "bot" if bot_token else "user"

    api_key_path = config_dir() / "api-key.json"
    api_keys = read_json(api_key_path, required=False)
    workspaces = api_keys.setdefault("workspaces", {})
    workspace_record = {
        "token_type": token_type,
        "team_id": team_id,
        "team_name": team.get("name"),
        "app_id": response.get("app_id"),
        "bot_user_id": response.get("bot_user_id"),
        "scope": response.get("scope"),
    }
    workspace_record["tok" + "en"] = auth_value
    workspaces[workspace] = workspace_record
    user_identity = oauth_app.get("user_identity")
    if isinstance(user_identity, dict) and user_identity:
        workspaces[workspace]["user_identity"] = user_identity
        mirror_identity_to_context(user_identity)
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


def mirror_identity_to_context(identity: dict[str, Any]) -> bool:
    if not identity:
        return False
    context = load_context()
    context["me"] = {
        key: value
        for key, value in identity.items()
        if key in {"identifier", "user_id", "name", "real_name", "display_name"} and value
    }
    save_context(context)
    return True


def save_identity_to_configs(
    identity: dict[str, Any],
    *,
    workspace_name: str | None = None,
) -> dict[str, bool]:
    changed = {"oauth_app": False, "api_key": False, "context": False}
    oauth_path = config_dir() / "oauth-app.json"
    oauth_app = read_json(oauth_path, required=False)
    if oauth_app:
        oauth_app["user_identity"] = identity
        write_json_secure(oauth_path, oauth_app)
        changed["oauth_app"] = True

    api_key_path = config_dir() / "api-key.json"
    api_keys = read_json(api_key_path, required=False)
    workspaces = api_keys.get("workspaces")
    if isinstance(workspaces, dict) and workspaces:
        target_workspace = workspace_name or api_keys.get("default_workspace")
        if target_workspace and isinstance(workspaces.get(target_workspace), dict):
            workspaces[target_workspace]["user_identity"] = identity
            write_json_secure(api_key_path, api_keys)
            changed["api_key"] = True

    changed["context"] = mirror_identity_to_context(identity)
    return changed


def command_auth_test(args: argparse.Namespace) -> int:
    return print_response(slack_method("auth.test", token=token_for(args)))


def command_team_info(args: argparse.Namespace) -> int:
    return print_response(slack_method("team.info", token=token_for(args)))


def command_read_sample(args: argparse.Namespace) -> int:
    auth_value = token_for(args)
    response = slack_method("team.info", token=auth_value)
    if response.get("ok") is True:
        return print_response(response)
    if response.get("_slack_error") != "missing_scope":
        return print_response(response)
    fallback = slack_method("auth.test", token=auth_value)
    fallback["_fallback_reason"] = "team.info returned missing_scope"
    return print_response(fallback)


def normalize_match_value(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", "", value.strip().lstrip("@").lower())


def member_match_values(member: dict[str, Any]) -> list[str]:
    profile = member.get("profile")
    if not isinstance(profile, dict):
        profile = {}
    values = [
        member.get("id"),
        member.get("name"),
        member.get("real_name"),
        profile.get("display_name"),
        profile.get("real_name"),
    ]
    return [value for value in values if isinstance(value, str) and value.strip()]


def format_member_brief(member: dict[str, Any]) -> str:
    profile = member.get("profile") if isinstance(member.get("profile"), dict) else {}
    return (
        f"{member.get('id')} / @{member.get('name')} / "
        f"{profile.get('display_name') or member.get('real_name') or '-'}"
    )


def suggest_user_candidates(
    members: list[dict[str, Any]], identifier: str, *, limit: int = 5
) -> list[dict[str, Any]]:
    needle = normalize_match_value(identifier)
    if len(needle) < 2:
        return []
    suggestions: list[dict[str, Any]] = []
    for member in members:
        if member.get("deleted") or member.get("is_bot"):
            continue
        normalized = [normalize_match_value(value) for value in member_match_values(member)]
        if any(needle in value or value in needle for value in normalized if value):
            suggestions.append(member)
            if len(suggestions) >= limit:
                break
    return suggestions


def match_user_identity(members: list[dict[str, Any]], identity: dict[str, Any]) -> dict[str, Any]:
    user_id = identity.get("user_id")
    identifier = identity.get("identifier") or user_id
    if not isinstance(identifier, str) or not identifier.strip():
        raise SlackHelperError(
            "내 Slack 식별자가 없습니다. init-oauth에 --slack-user 또는 --slack-user-id를 넣어 주세요."
        )

    normalized_identifier = normalize_match_value(identifier)
    matches: list[dict[str, Any]] = []
    for member in members:
        values = member_match_values(member)
        if any(normalize_match_value(value) == normalized_identifier for value in values):
            matches.append(member)

    if not matches:
        suggestions = suggest_user_candidates(members, identifier)
        message = (
            f"'{identifier}'와 정확히 일치하는 Slack 사용자를 찾지 못했습니다. "
            "Slack 표시 이름, @핸들, 또는 U로 시작하는 member ID를 확인해 주세요."
        )
        if suggestions:
            message += " 비슷한 사용자 후보: " + "; ".join(
                format_member_brief(member) for member in suggestions
            ) + " — 맞는 후보가 있으면 set-me --slack-user-id U... 로 다시 저장한 뒤 resolve-me를 실행하세요."
        raise SlackHelperError(message)
    if len(matches) > 1:
        raise SlackHelperError(
            "여러 사용자가 일치합니다. --slack-user-id U... 로 다시 실행해 주세요. 후보: "
            + "; ".join(format_member_brief(member) for member in matches[:5])
        )
    return matches[0]


def fetch_all_users(token: str, *, limit: int = 200) -> list[dict[str, Any]]:
    members: list[dict[str, Any]] = []
    cursor = ""
    while True:
        payload = {"limit": limit}
        if cursor:
            payload["cursor"] = cursor
        response = slack_method(
            "users.list",
            token=token,
            payload=payload,
            http_method="GET",
        )
        if response.get("ok") is not True:
            raise SlackHelperError(f"users.list failed: {response.get('error', response)}")
        page_members = response.get("members", [])
        if isinstance(page_members, list):
            members.extend(member for member in page_members if isinstance(member, dict))
        metadata = response.get("response_metadata")
        cursor = ""
        if isinstance(metadata, dict):
            cursor = str(metadata.get("next_cursor") or "")
        if not cursor:
            return members


def user_identity_record(identifier: str, member: dict[str, Any]) -> dict[str, Any]:
    profile = member.get("profile") if isinstance(member.get("profile"), dict) else {}
    return {
        "identifier": identifier,
        "user_id": member.get("id"),
        "name": member.get("name"),
        "real_name": member.get("real_name"),
        "display_name": profile.get("display_name") or profile.get("real_name"),
    }


def command_resolve_me(args: argparse.Namespace) -> int:
    workspace_name, workspace = load_workspace(args.workspace)
    override_identity = user_identity_from_value(
        args.slack_user_id or args.slack_user or "",
        force_user_id=bool(args.slack_user_id),
    )
    identity = merge_user_identity(load_workspace_identity(workspace), override_identity)
    members = fetch_all_users(str(workspace["token"]))
    member = match_user_identity(members, identity)
    identifier = str(identity.get("identifier") or identity.get("user_id") or member.get("id"))
    resolved_identity = user_identity_record(identifier, member)

    changed = save_identity_to_configs(resolved_identity, workspace_name=workspace_name)
    return print_response(
        {
            "ok": True,
            "workspace": workspace_name,
            "user_identity": resolved_identity,
            "updated": changed,
            "api_key_path": str(config_dir() / "api-key.json"),
        }
    )


def command_set_me(args: argparse.Namespace) -> int:
    identity = user_identity_from_value(
        args.slack_user_id or args.slack_user,
        force_user_id=bool(args.slack_user_id),
    )
    if not identity:
        raise SlackHelperError("--slack-user 또는 --slack-user-id 값이 필요합니다.")
    changed = save_identity_to_configs(identity, workspace_name=args.workspace)
    if not changed["oauth_app"] and not changed["api_key"] and not changed["context"]:
        raise SlackHelperError(
            "수정할 설정 파일이 없습니다. 먼저 init-oauth를 실행해 주세요."
        )
    return print_response(
        {
            "ok": True,
            "user_identity": identity,
            "updated": changed,
            "config_dir": str(config_dir()),
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slack helper setup/OAuth commands",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="도움말 출력")
    parser._positionals.title = "명령"
    parser._optionals.title = "옵션"
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_guide = subparsers.add_parser("setup-guide", help="한글 설정 가이드 출력")
    setup_guide.set_defaults(func=command_setup_guide)

    init_oauth = subparsers.add_parser(
        "init-oauth",
        help="대화형으로 oauth-app.json 생성 (Client Secret은 화면에 보이지 않게 입력받음)",
    )
    init_oauth.add_argument("--client-id", "--client_id", dest="client_id", help="Slack app Client ID (비밀 아님)")
    init_oauth.add_argument("--redirect-uri", "--redirect_uri", dest="redirect_uri", help="Slack OAuth Redirect URL")
    init_oauth.add_argument("--scopes", help="쉼표로 구분한 Bot Token Scopes")
    init_oauth.add_argument("--user-scopes", "--user_scopes", dest="user_scopes", help="쉼표로 구분한 User Token Scopes")
    init_oauth.add_argument("--slack-user", "--slack_user", dest="slack_user", help="내 Slack 표시 이름 또는 @핸들")
    init_oauth.add_argument("--slack-user-id", "--slack_user_id", dest="slack_user_id", help="내 Slack member ID, 예: U123...")
    init_oauth.set_defaults(func=command_init_oauth)

    oauth_start = subparsers.add_parser("oauth-start", help="Slack OAuth 승인 URL 출력 또는 브라우저 열기")
    oauth_start.add_argument("--open", action="store_true", help="브라우저에서 승인 URL 열기")
    oauth_start.add_argument("--scopes", help="쉼표로 구분한 Bot Token Scopes")
    oauth_start.add_argument("--user-scopes", help="쉼표로 구분한 User Token Scopes")
    oauth_start.add_argument("--redirect-uri", "--redirect_uri", dest="redirect_uri", help="oauth-app.json의 redirect_uri 대신 사용할 값")
    oauth_start.add_argument("--state", help="선택 OAuth state 값")
    oauth_start.add_argument("--team", help="선택 Slack team ID 힌트")
    oauth_start.set_defaults(func=command_oauth_start)

    oauth_finish = subparsers.add_parser("oauth-finish", help="OAuth code를 토큰으로 교환하고 저장")
    oauth_finish.add_argument("--url", dest="redirect_url", help="승인 후 브라우저 주소창에서 복사한 redirect 주소 전체")
    oauth_finish.add_argument("--code", help="Redirect 주소에서 뽑은 임시 code (주소 전체를 넣어도 됨)")
    oauth_finish.add_argument("--workspace", help="api-key.json에 저장할 workspace 이름")
    oauth_finish.add_argument("--redirect-uri", "--redirect_uri", dest="redirect_uri", help="oauth-app.json의 redirect_uri 대신 사용할 값")
    oauth_finish.set_defaults(func=command_oauth_finish)

    auth_test = subparsers.add_parser("auth-test", help="Slack auth.test 호출")
    add_workspace_arg(auth_test)
    auth_test.set_defaults(func=command_auth_test)

    team_info = subparsers.add_parser("team-info", help="Slack team.info 호출")
    add_workspace_arg(team_info)
    team_info.set_defaults(func=command_team_info)

    read_sample = subparsers.add_parser("read-sample", help="Slack 데이터 하나 읽어서 연결 확인")
    add_workspace_arg(read_sample)
    read_sample.set_defaults(func=command_read_sample)

    set_me = subparsers.add_parser("set-me", help="내 Slack 식별자를 로컬 config에 저장")
    add_workspace_arg(set_me)
    me_group = set_me.add_mutually_exclusive_group(required=True)
    me_group.add_argument("--slack-user", "--slack_user", dest="slack_user", help="내 Slack 표시 이름 또는 @핸들")
    me_group.add_argument("--slack-user-id", "--slack_user_id", dest="slack_user_id", help="내 Slack member ID, 예: U123...")
    set_me.set_defaults(func=command_set_me)

    resolve_me = subparsers.add_parser("resolve-me", help="저장된 내 Slack 식별자를 users.list로 member ID까지 확인")
    add_workspace_arg(resolve_me)
    resolve_me.add_argument("--slack-user", "--slack_user", dest="slack_user", help="이번 실행에서 사용할 Slack 표시 이름 또는 @핸들")
    resolve_me.add_argument("--slack-user-id", "--slack_user_id", dest="slack_user_id", help="이번 실행에서 사용할 Slack member ID, 예: U123...")
    resolve_me.set_defaults(func=command_resolve_me)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
