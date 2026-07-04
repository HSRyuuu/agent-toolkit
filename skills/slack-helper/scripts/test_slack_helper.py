#!/usr/bin/env python3
"""Tests for deterministic slack-helper behavior.

Covers pure helpers plus config read/write, with no network access.
Run with: python3 test_slack_helper.py
"""

from __future__ import annotations

import importlib.util
import os
import stat
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def load_module():
    spec = importlib.util.spec_from_file_location(
        "slack_api", SCRIPT_DIR / "slack_api.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


slack = load_module()


def check(name: str, cond: bool, detail: str = "") -> bool:
    suffix = f" — {detail}" if detail else ""
    print(f"[{'PASS' if cond else 'FAIL'}] {name}{suffix}")
    return cond


def case_curl_config_quote_escapes_control_chars() -> bool:
    quoted = slack.curl_config_quote('a"b\\c\nd')
    # A curl config injection would need a raw newline or unescaped quote to break out.
    return check(
        "curl_config_quote escapes quote/backslash/newline",
        quoted == 'a\\"b\\\\c\\nd',
        quoted,
    )


def case_user_identity_plain_name_has_no_user_id() -> bool:
    identity = slack.user_identity_from_value("@your-slack-name")
    return check(
        "plain handle strips @ and sets no user_id",
        identity == {"identifier": "your-slack-name"},
        str(identity),
    )


def case_user_identity_detects_member_id() -> bool:
    identity = slack.user_identity_from_value("u123abc")
    return check(
        "U-prefixed value is uppercased into user_id",
        identity == {"identifier": "u123abc", "user_id": "U123ABC"},
        str(identity),
    )


def case_merge_user_identity_override_wins() -> bool:
    merged = slack.merge_user_identity(
        {"identifier": "old", "name": "keep"},
        {"identifier": "new", "user_id": ""},
    )
    return check(
        "merge keeps non-empty existing and applies non-empty override",
        merged == {"identifier": "new", "name": "keep"},
        str(merged),
    )


def case_split_scopes_trims_and_drops_empty() -> bool:
    scopes = slack.split_scopes(" team:read , ,users:read ")
    return check(
        "split_scopes trims whitespace and removes empties",
        scopes == ["team:read", "users:read"],
        str(scopes),
    )


def case_workspace_slug_normalizes() -> bool:
    return check(
        "workspace_slug lowercases and hyphenates",
        slack.workspace_slug("My Team!!") == "my-team"
        and slack.workspace_slug("!!!") == "default",
    )


def case_supported_redirect_uri() -> bool:
    ok = slack.is_supported_redirect_uri("http://localhost:8765/callback")
    bad_https = slack.is_supported_redirect_uri("https://localhost:8765/callback")
    bad_host = slack.is_supported_redirect_uri("http://example.com/callback")
    return check(
        "redirect URI must be http localhost/127.0.0.1",
        ok and not bad_https and not bad_host,
    )


def case_match_user_identity_unique() -> bool:
    members = [
        {"id": "U1", "name": "alice", "profile": {"display_name": "Alice"}},
        {"id": "U2", "name": "bob", "profile": {"display_name": "Bob"}},
    ]
    match = slack.match_user_identity(members, {"identifier": "@bob"})
    return check(
        "match_user_identity finds unique member by handle",
        match["id"] == "U2",
        str(match.get("id")),
    )


def case_match_user_identity_ambiguous_errors() -> bool:
    members = [
        {"id": "U1", "name": "sam", "profile": {}},
        {"id": "U2", "name": "other", "real_name": "sam", "profile": {}},
    ]
    try:
        slack.match_user_identity(members, {"identifier": "sam"})
    except slack.SlackHelperError:
        return check("ambiguous match raises SlackHelperError", True)
    return check("ambiguous match raises SlackHelperError", False, "no error raised")


def case_load_channel_id_passthrough_and_alias() -> bool:
    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            direct = slack.load_channel_id("C0123456789")
            slack.write_json_secure(
                Path(tmp) / "channel-info.json",
                {"channels": {"general": "C0123456789"}},
            )
            alias = slack.load_channel_id("general")
            missing_raises = False
            try:
                slack.load_channel_id("nope")
            except slack.SlackHelperError:
                missing_raises = True
        finally:
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    return check(
        "load_channel_id passes IDs, resolves aliases, errors on unknown",
        direct == "C0123456789" and alias == "C0123456789" and missing_raises,
    )


def case_write_json_secure_permissions() -> bool:
    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        target = Path(tmp) / "nested" / "secret.json"
        slack.write_json_secure(target, {"token": "xoxb-abc"})
        file_mode = stat.S_IMODE(target.stat().st_mode)
        dir_mode = stat.S_IMODE(target.parent.stat().st_mode)
        roundtrip = slack.read_json(target)
    return check(
        "write_json_secure writes 600 file under 700 dir and roundtrips",
        file_mode == 0o600 and dir_mode == 0o700 and roundtrip == {"token": "xoxb-abc"},
        f"file={oct(file_mode)} dir={oct(dir_mode)}",
    )


def main() -> int:
    cases = [
        case_curl_config_quote_escapes_control_chars,
        case_user_identity_plain_name_has_no_user_id,
        case_user_identity_detects_member_id,
        case_merge_user_identity_override_wins,
        case_split_scopes_trims_and_drops_empty,
        case_workspace_slug_normalizes,
        case_supported_redirect_uri,
        case_match_user_identity_unique,
        case_match_user_identity_ambiguous_errors,
        case_load_channel_id_passthrough_and_alias,
        case_write_json_secure_permissions,
    ]
    results = [case() for case in cases]
    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
