#!/usr/bin/env python3
"""Datadog helper setup commands."""

from __future__ import annotations

import argparse
import getpass
from typing import Any

from datadog_common import (
    DEFAULT_FROM,
    DEFAULT_LIMIT,
    DEFAULT_SITE,
    DatadogHelperError,
    add_profile_arg,
    config_path,
    datadog_request,
    ensure_memory_file,
    load_config,
    load_profile,
    mask_secret,
    normalize_site,
    print_response,
    run_main,
    save_config,
)


def command_init_keys(args: argparse.Namespace) -> int:
    api_key = getpass.getpass("Datadog API key: ").strip()
    app_key = getpass.getpass("Datadog application key: ").strip()
    if not api_key:
        raise DatadogHelperError("API key가 비어 있습니다.")
    if not app_key:
        raise DatadogHelperError("Application key가 비어 있습니다.")

    profile_name = args.profile or "default"
    site = normalize_site(args.site or DEFAULT_SITE)
    config = load_config(required=False)
    profiles = config.get("profiles")
    if not isinstance(profiles, dict):
        profiles = {}
    profiles[profile_name] = {
        "site": site,
        "api_key": api_key,
        "app_key": app_key,
        "default_from": args.default_from,
        "default_limit": args.default_limit,
    }
    config["profiles"] = profiles
    config["default_profile"] = profile_name
    save_config(config)
    ensure_memory_file()
    print("Datadog API 설정을 저장했습니다.")
    print(f"profile={profile_name} site={site} config={config_path()}")
    return 0


def command_auth_test(args: argparse.Namespace) -> int:
    profile_name, profile = load_profile(args.profile)
    response = datadog_request(
        profile,
        "/api/v1/validate",
        http_method="GET",
        require_app_key=False,
    )
    valid = response.get("valid")
    if valid is not True:
        raise DatadogHelperError(f"API key validation failed: {response}")
    print(f"Datadog API key is valid. profile={profile_name} site={profile['site']}")
    return 0


def command_logs_test(args: argparse.Namespace) -> int:
    profile_name, profile = load_profile(args.profile)
    payload: dict[str, Any] = {
        "filter": {
            "from": args.from_time,
            "to": "now",
            "query": args.query,
        },
        "page": {"limit": 1},
        "sort": "-timestamp",
    }
    if args.index:
        payload["filter"]["indexes"] = [args.index]
    response = datadog_request(
        profile,
        "/api/v2/logs/events/search",
        http_method="POST",
        payload=payload,
    )
    count = len(response.get("data", [])) if isinstance(response.get("data"), list) else 0
    print(f"Datadog log search works. profile={profile_name} events={count}")
    return 0


def command_apm_test(args: argparse.Namespace) -> int:
    profile_name, profile = load_profile(args.profile)
    payload: dict[str, Any] = {
        "data": {
            "type": "search_request",
            "attributes": {
                "filter": {
                    "from": args.from_time,
                    "to": "now",
                    "query": args.query,
                },
                "page": {"limit": 1},
                "sort": "-timestamp",
            },
        }
    }
    response = datadog_request(
        profile,
        "/api/v2/spans/events/search",
        http_method="POST",
        payload=payload,
    )
    count = len(response.get("data", [])) if isinstance(response.get("data"), list) else 0
    print(f"Datadog APM span search works. profile={profile_name} spans={count}")
    return 0


def command_profiles(args: argparse.Namespace) -> int:
    config = load_config()
    profiles = config.get("profiles")
    if not isinstance(profiles, dict):
        raise DatadogHelperError("config.json에 profiles 설정이 없습니다.")
    rows = []
    for name, profile in sorted(profiles.items()):
        if not isinstance(profile, dict):
            continue
        rows.append(
            {
                "name": name,
                "site": profile.get("site"),
                "api_key": mask_secret(str(profile.get("api_key") or "")),
                "app_key": mask_secret(str(profile.get("app_key") or "")),
                "default": name == config.get("default_profile"),
                "default_from": profile.get("default_from", DEFAULT_FROM),
                "default_limit": profile.get("default_limit", DEFAULT_LIMIT),
            }
        )
    return print_response({"profiles": rows})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Datadog helper setup")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_keys = subparsers.add_parser("init-keys", help="Register Datadog keys locally")
    init_keys.add_argument("--profile", default="default")
    init_keys.add_argument("--site", default=DEFAULT_SITE)
    init_keys.add_argument("--default-from", default=DEFAULT_FROM)
    init_keys.add_argument("--default-limit", type=int, default=DEFAULT_LIMIT)
    init_keys.set_defaults(func=command_init_keys)

    auth_test = subparsers.add_parser("auth-test", help="Validate API key")
    add_profile_arg(auth_test)
    auth_test.set_defaults(func=command_auth_test)

    logs_test = subparsers.add_parser("logs-test", help="Validate log search access")
    add_profile_arg(logs_test)
    logs_test.add_argument("--from", dest="from_time", default="now-15m")
    logs_test.add_argument("--query", default="*")
    logs_test.add_argument("--index")
    logs_test.set_defaults(func=command_logs_test)

    apm_test = subparsers.add_parser("apm-test", help="Validate APM span search access (apm_read)")
    add_profile_arg(apm_test)
    apm_test.add_argument("--from", dest="from_time", default="now-15m")
    apm_test.add_argument("--query", default="*")
    apm_test.set_defaults(func=command_apm_test)

    profiles = subparsers.add_parser("profiles", help="List configured profiles")
    profiles.set_defaults(func=command_profiles)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
