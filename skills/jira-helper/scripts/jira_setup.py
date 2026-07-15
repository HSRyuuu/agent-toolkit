#!/usr/bin/env python3
"""Jira helper setup commands (interactive key registration + checks)."""

from __future__ import annotations

import argparse
import getpass

from jira_common import (
    DEFAULT_LIMIT,
    SEARCH_PATH,
    JiraHelperError,
    add_profile_arg,
    config_path,
    ensure_memory_file,
    jira_request,
    load_config,
    load_profile,
    mask_secret,
    normalize_site,
    print_response,
    run_main,
    save_config,
    update_profile,
)


def command_init_keys(args: argparse.Namespace) -> int:
    site = normalize_site(args.site)
    email = args.email.strip()
    if not email or "@" not in email:
        raise JiraHelperError("email이 올바르지 않습니다.")
    api_token = getpass.getpass("Jira API token: ").strip()
    if not api_token:
        raise JiraHelperError("API token이 비어 있습니다.")

    profile_name = args.profile or "default"
    config = load_config(required=False)
    profiles = config.get("profiles")
    if not isinstance(profiles, dict):
        profiles = {}
    profiles[profile_name] = {
        "site": site,
        "email": email,
        "api_token": api_token,
        "default_limit": args.default_limit,
    }
    config["profiles"] = profiles
    config["default_profile"] = profile_name
    save_config(config)
    ensure_memory_file()
    print("Jira API 설정을 저장했습니다.")
    print(f"profile={profile_name} site={site} config={config_path()}")
    return 0


def command_auth_test(args: argparse.Namespace) -> int:
    profile_name, profile = load_profile(args.profile)
    response = jira_request(profile, "/rest/api/3/myself")
    account_id = str(response.get("accountId") or "")
    display_name = str(response.get("displayName") or "")
    if not account_id:
        raise JiraHelperError(f"myself 응답에 accountId가 없습니다: {response}")
    # cache identity so search commands can show who currentUser() is
    update_profile(profile_name, {"account_id": account_id, "display_name": display_name})
    print(
        f"Jira 인증 성공. profile={profile_name} site={profile['site']} "
        f"me={display_name} ({account_id})"
    )
    return 0


def command_search_test(args: argparse.Namespace) -> int:
    profile_name, profile = load_profile(args.profile)
    response = jira_request(
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


def command_profiles(args: argparse.Namespace) -> int:
    config = load_config()
    profiles = config.get("profiles")
    if not isinstance(profiles, dict):
        raise JiraHelperError("config.json에 profiles 설정이 없습니다.")
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
    parser = argparse.ArgumentParser(description="Jira helper setup")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_keys = subparsers.add_parser("init-keys", help="Register Jira credentials locally")
    init_keys.add_argument("--profile", default="default")
    init_keys.add_argument("--site", required=True, help="예: your-org.atlassian.net")
    init_keys.add_argument("--email", required=True, help="Atlassian 계정 email")
    init_keys.add_argument("--default-limit", type=int, default=DEFAULT_LIMIT)
    init_keys.set_defaults(func=command_init_keys)

    auth_test = subparsers.add_parser("auth-test", help="Validate credentials via /myself")
    add_profile_arg(auth_test)
    auth_test.set_defaults(func=command_auth_test)

    search_test = subparsers.add_parser("search-test", help="Validate issue search access")
    add_profile_arg(search_test)
    search_test.set_defaults(func=command_search_test)

    profiles = subparsers.add_parser("profiles", help="List configured profiles")
    profiles.set_defaults(func=command_profiles)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
