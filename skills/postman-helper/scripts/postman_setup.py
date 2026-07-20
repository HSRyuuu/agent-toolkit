#!/usr/bin/env python3
"""postman-helper setup commands."""

from __future__ import annotations

import argparse
import getpass

from postman_common import (
    PostmanHelperError,
    add_profile_arg,
    config_path,
    ensure_memory_file,
    load_config,
    load_profile,
    mask_secret,
    postman_request,
    run_main,
    save_config,
)


def command_init_key(args: argparse.Namespace) -> int:
    api_key = getpass.getpass("Postman API key (X-Api-Key): ").strip()
    if not api_key:
        raise PostmanHelperError("API key가 비어 있습니다.")
    profile_name = args.profile or "default"
    config = load_config(required=False)
    profiles = config.get("profiles")
    if not isinstance(profiles, dict):
        profiles = {}
    profiles[profile_name] = {"api_key": api_key}
    config["profiles"] = profiles
    config["default_profile"] = profile_name
    save_config(config)
    ensure_memory_file()
    print("Postman API 설정을 저장했습니다.")
    print(f"profile={profile_name} config={config_path()}")
    return 0


def command_auth_test(args: argparse.Namespace) -> int:
    profile_name, profile = load_profile(args.profile)
    data = postman_request(profile, "/me")
    user = data.get("user") if isinstance(data, dict) else None
    who = user.get("username") or user.get("id") if isinstance(user, dict) else "?"
    print(f"Postman API key is valid. profile={profile_name} user={who}")
    return 0


def command_profiles(args: argparse.Namespace) -> int:
    config = load_config()
    profiles = config.get("profiles")
    if not isinstance(profiles, dict):
        raise PostmanHelperError("config.json에 profiles 설정이 없습니다.")
    default = config.get("default_profile")
    for name, profile in sorted(profiles.items()):
        if not isinstance(profile, dict):
            continue
        mark = " (default)" if name == default else ""
        print(f"{name}{mark}: api_key={mask_secret(str(profile.get('api_key') or ''))}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="postman-helper setup")
    sub = parser.add_subparsers(dest="command", required=True)

    init_key = sub.add_parser("init-key", help="Register a Postman API key locally")
    init_key.add_argument("--profile", default="default")
    init_key.set_defaults(func=command_init_key)

    auth = sub.add_parser("auth-test", help="Validate the API key via /me")
    add_profile_arg(auth)
    auth.set_defaults(func=command_auth_test)

    profiles = sub.add_parser("profiles", help="List configured profiles")
    profiles.set_defaults(func=command_profiles)
    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
