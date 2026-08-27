#!/usr/bin/env python3
"""Atlassian helper setup commands (interactive key registration + checks)."""

from __future__ import annotations

import argparse
import getpass
import subprocess
import sys

from atlassian_common import (
    DEFAULT_LIMIT,
    LEGACY_KEYCHAIN_EMAIL_ACCOUNT,
    LEGACY_KEYCHAIN_SERVICE,
    LEGACY_KEYCHAIN_TOKEN_ACCOUNT,
    SEARCH_PATH,
    SPACES_PATH,
    AtlassianHelperError,
    add_profile_arg,
    api_request,
    config_path,
    ensure_memory_file,
    load_config,
    load_profile,
    mask_secret,
    normalize_site,
    print_response,
    run_main,
    save_config,
    update_profile,
)


def save_credentials(
    *, site: str, email: str, api_token: str, profile_name: str, default_limit: int
) -> None:
    """한 프로필을 config.json에 쓴다. token은 화면에 찍지 않는다."""
    site = normalize_site(site)
    email = (email or "").strip()
    if not email or "@" not in email:
        raise AtlassianHelperError(f"email이 올바르지 않습니다: {email!r}")
    if not api_token:
        raise AtlassianHelperError("API token이 비어 있습니다.")

    config = load_config(required=False)
    profiles = config.get("profiles")
    if not isinstance(profiles, dict):
        profiles = {}
    profiles[profile_name] = {
        "site": site,
        "email": email,
        "api_token": api_token,
        "default_limit": default_limit,
    }
    config["profiles"] = profiles
    config["default_profile"] = profile_name
    save_config(config)
    ensure_memory_file()
    print("Atlassian API 설정을 저장했습니다.")
    print(f"profile={profile_name} site={site} email={email} config={config_path()}")


def command_init_keys(args: argparse.Namespace) -> int:
    api_token = getpass.getpass("Atlassian API token: ").strip()
    save_credentials(
        site=args.site,
        email=args.email,
        api_token=api_token,
        profile_name=args.profile or "default",
        default_limit=args.default_limit,
    )
    return 0


def keychain_secret(service: str, account: str) -> str:
    """macOS Keychain generic password. 없으면 빈 문자열."""
    if sys.platform != "darwin":
        raise AtlassianHelperError("Keychain 마이그레이션은 macOS에서만 됩니다.")
    try:
        return (
            subprocess.check_output(
                ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, OSError):
        return ""


def command_migrate_keychain(args: argparse.Namespace) -> int:
    """구 jira/jira-tec 스킬이 Keychain에 둔 자격증명을 config.json으로 한 번 옮긴다.

    토큰을 새로 발급받을 필요가 없다. Keychain 원본은 지우지 않는다 — auth-test로
    확인한 뒤 사용자가 직접 지운다.
    """
    service = args.service
    email = keychain_secret(service, args.email_account)
    api_token = keychain_secret(service, args.token_account)
    missing = [
        name
        for name, value in ((args.email_account, email), (args.token_account, api_token))
        if not value
    ]
    if missing:
        raise AtlassianHelperError(
            f"Keychain '{service}'에 {', '.join(missing)} 항목이 없습니다. "
            "init-keys로 새로 설정하세요."
        )
    save_credentials(
        site=args.site,
        email=email,
        api_token=api_token,
        profile_name=args.profile or "default",
        default_limit=args.default_limit,
    )
    print(f"Keychain '{service}'에서 옮겼습니다. 다음: auth-test로 확인하세요.")
    print(
        "확인 뒤 구 항목을 지우려면: "
        f'security delete-generic-password -s "{service}" -a "{args.token_account}"'
    )
    return 0


def command_auth_test(args: argparse.Namespace) -> int:
    profile_name, profile = load_profile(args.profile)
    response = api_request(profile, "/rest/api/3/myself")
    account_id = str(response.get("accountId") or "")
    display_name = str(response.get("displayName") or "")
    if not account_id:
        raise AtlassianHelperError(f"myself 응답에 accountId가 없습니다: {response}")
    # cache identity so search commands can show who currentUser() is and so the
    # modify/delete ownership guard can compare without an extra API call
    update_profile(profile_name, {"account_id": account_id, "display_name": display_name})
    print(
        f"Atlassian 인증 성공. profile={profile_name} site={profile['site']} "
        f"me={display_name} ({account_id})"
    )
    return 0


def command_search_test(args: argparse.Namespace) -> int:
    profile_name, profile = load_profile(args.profile)
    response = api_request(
        profile,
        SEARCH_PATH,
        query={
            "jql": "updated >= -30d ORDER BY updated DESC",
            "maxResults": 1,
            "fields": "summary",
        },
    )
    issues = response.get("issues") if isinstance(response, dict) else None
    count = len(issues) if isinstance(issues, list) else 0
    print(f"Jira 이슈 검색이 동작합니다. profile={profile_name} sample_issues={count}")
    return 0


def command_confluence_test(args: argparse.Namespace) -> int:
    profile_name, profile = load_profile(args.profile)
    response = api_request(profile, SPACES_PATH, query={"limit": 1})
    results = response.get("results") if isinstance(response, dict) else None
    count = len(results) if isinstance(results, list) else 0
    print(f"Confluence 접근이 동작합니다. profile={profile_name} sample_spaces={count}")
    return 0


def command_profiles(args: argparse.Namespace) -> int:
    config = load_config()
    profiles = config.get("profiles")
    if not isinstance(profiles, dict):
        raise AtlassianHelperError("config.json에 profiles 설정이 없습니다.")
    rows = []
    for name, profile in sorted(profiles.items()):
        if not isinstance(profile, dict):
            continue
        rows.append(
            {
                "name": name,
                "site": profile.get("site"),
                "email": profile.get("email"),
                "api_token": mask_secret(str(profile.get("api_token") or "")),
                "display_name": profile.get("display_name"),
                "default": name == config.get("default_profile"),
                "default_limit": profile.get("default_limit", DEFAULT_LIMIT),
            }
        )
    return print_response({"profiles": rows})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Atlassian helper setup")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_keys = subparsers.add_parser("init-keys", help="Register Atlassian credentials locally")
    init_keys.add_argument("--profile", default="default")
    init_keys.add_argument("--site", required=True, help="예: your-org.atlassian.net")
    init_keys.add_argument("--email", required=True, help="Atlassian 계정 email")
    init_keys.add_argument("--default-limit", type=int, default=DEFAULT_LIMIT)
    init_keys.set_defaults(func=command_init_keys)

    migrate = subparsers.add_parser(
        "migrate-keychain",
        help="구 jira/jira-tec 스킬의 Keychain 자격증명을 config.json으로 옮긴다 (macOS)",
    )
    migrate.add_argument("--profile", default="default")
    migrate.add_argument("--site", required=True, help="예: your-org.atlassian.net")
    migrate.add_argument("--service", default=LEGACY_KEYCHAIN_SERVICE)
    migrate.add_argument("--email-account", default=LEGACY_KEYCHAIN_EMAIL_ACCOUNT)
    migrate.add_argument("--token-account", default=LEGACY_KEYCHAIN_TOKEN_ACCOUNT)
    migrate.add_argument("--default-limit", type=int, default=DEFAULT_LIMIT)
    migrate.set_defaults(func=command_migrate_keychain)

    auth_test = subparsers.add_parser("auth-test", help="Validate credentials via /myself")
    add_profile_arg(auth_test)
    auth_test.set_defaults(func=command_auth_test)

    search_test = subparsers.add_parser("search-test", help="Validate Jira issue search access")
    add_profile_arg(search_test)
    search_test.set_defaults(func=command_search_test)

    confluence_test = subparsers.add_parser(
        "confluence-test", help="Validate Confluence space access"
    )
    add_profile_arg(confluence_test)
    confluence_test.set_defaults(func=command_confluence_test)

    profiles = subparsers.add_parser("profiles", help="List configured profiles")
    profiles.set_defaults(func=command_profiles)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
