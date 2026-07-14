#!/usr/bin/env python3
"""Tests for deterministic slack-helper behavior.

Covers pure helpers plus config read/write, with no network access.
Run with: python3 test_slack_helper.py
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(
        name, SCRIPT_DIR / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load_module("slack_common")
setup = load_module("slack_setup")


def check(name: str, cond: bool, detail: str = "") -> bool:
    suffix = f" — {detail}" if detail else ""
    print(f"[{'PASS' if cond else 'FAIL'}] {name}{suffix}")
    return cond


def case_curl_config_quote_escapes_control_chars() -> bool:
    quoted = common.curl_config_quote('a"b\\c\nd')
    # A curl config injection would need a raw newline or unescaped quote to break out.
    return check(
        "curl_config_quote escapes quote/backslash/newline",
        quoted == 'a\\"b\\\\c\\nd',
        quoted,
    )


def case_user_identity_plain_name_has_no_user_id() -> bool:
    identity = common.user_identity_from_value("@your-slack-name")
    return check(
        "plain handle strips @ and sets no user_id",
        identity == {"identifier": "your-slack-name"},
        str(identity),
    )


def case_user_identity_detects_member_id() -> bool:
    identity = common.user_identity_from_value("u123abc")
    return check(
        "U-prefixed value is uppercased into user_id",
        identity == {"identifier": "u123abc", "user_id": "U123ABC"},
        str(identity),
    )


def case_merge_user_identity_override_wins() -> bool:
    merged = common.merge_user_identity(
        {"identifier": "old", "name": "keep"},
        {"identifier": "new", "user_id": ""},
    )
    return check(
        "merge keeps non-empty existing and applies non-empty override",
        merged == {"identifier": "new", "name": "keep"},
        str(merged),
    )


def case_split_scopes_trims_and_drops_empty() -> bool:
    scopes = common.split_scopes(" team:read , ,users:read ")
    return check(
        "split_scopes trims whitespace and removes empties",
        scopes == ["team:read", "users:read"],
        str(scopes),
    )


def case_workspace_slug_normalizes() -> bool:
    return check(
        "workspace_slug lowercases and hyphenates",
        setup.workspace_slug("My Team!!") == "my-team"
        and setup.workspace_slug("!!!") == "default",
    )


def case_supported_redirect_uri() -> bool:
    ok = setup.is_supported_redirect_uri("http://localhost:8765/callback")
    bad_https = setup.is_supported_redirect_uri("https://localhost:8765/callback")
    bad_host = setup.is_supported_redirect_uri("http://example.com/callback")
    return check(
        "redirect URI must be http localhost/127.0.0.1",
        ok and not bad_https and not bad_host,
    )


def case_match_user_identity_unique() -> bool:
    members = [
        {"id": "U1", "name": "alice", "profile": {"display_name": "Alice"}},
        {"id": "U2", "name": "bob", "profile": {"display_name": "Bob"}},
    ]
    match = setup.match_user_identity(members, {"identifier": "@bob"})
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
        setup.match_user_identity(members, {"identifier": "sam"})
    except common.SlackHelperError:
        return check("ambiguous match raises SlackHelperError", True)
    return check("ambiguous match raises SlackHelperError", False, "no error raised")


def case_resolve_channel_id_and_name_lookup() -> bool:
    original = common.slack_method

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        return {
            "ok": True,
            "channels": [
                {"id": "C0123456789", "name": "general"},
                {"id": "C0987654321", "name": "backend"},
            ],
        }

    try:
        common.slack_method = fake_slack_method
        direct = common.resolve_channel("C0123456789", "t")
        by_name = common.resolve_channel("#backend", "t")
        missing_raises = False
        try:
            common.resolve_channel("nope", "t")
        except common.SlackHelperError:
            missing_raises = True
    finally:
        common.slack_method = original
    return check(
        "resolve_channel passes IDs, resolves names via API, errors on unknown",
        direct == "C0123456789" and by_name == "C0987654321" and missing_raises,
    )


def case_write_json_secure_permissions() -> bool:
    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        target = Path(tmp) / "nested" / "secret.json"
        common.write_json_secure(target, {"token": "t"})
        file_mode = stat.S_IMODE(target.stat().st_mode)
        dir_mode = stat.S_IMODE(target.parent.stat().st_mode)
        roundtrip = common.read_json(target)
    return check(
        "write_json_secure writes 600 file under 700 dir and roundtrips",
        file_mode == 0o600 and dir_mode == 0o700 and roundtrip == {"token": "t"},
        f"file={oct(file_mode)} dir={oct(dir_mode)}",
    )


def case_common_format_ts_local() -> bool:
    return check(
        "format_ts_local renders Slack ts in the requested timezone",
        common.format_ts_local("1717243200.000100", "Asia/Seoul") == "2024-06-01 21:00",
    )


def case_common_day_bounds_boundaries() -> bool:
    day_bounds = getattr(common, "day_bounds", None)
    if day_bounds is None:
        return check(
            "day_bounds returns KST day boundaries and rejects bad format",
            False,
            "slack_common.day_bounds missing",
        )
    bounds = day_bounds("2026-07-05", "Asia/Seoul")
    invalid_raises = False
    try:
        day_bounds("2026-7-5")
    except common.SlackHelperError:
        invalid_raises = True
    return check(
        "day_bounds returns KST day boundaries and rejects bad format",
        bounds == ("1783177200.000000", "1783263599.999999") and invalid_raises,
        str(bounds),
    )


def case_common_truncate_text() -> bool:
    short = "a" * 120
    long = "b" * 121
    return check(
        "truncate_text preserves 120 chars and ellipsizes longer text",
        common.truncate_text(short) == short
        and common.truncate_text(long) == ("b" * 117) + "...",
    )


def case_common_format_message_line() -> bool:
    message = {
        "ts": "1717243200.000100",
        "user": "U123",
        "text": "hello\nworld",
        "permalink": "https://example.slack.com/archives/C1/p1717243200000100",
    }
    return check(
        "format_message_line emits compact one-line message",
        common.format_message_line(message, "backend", "alice")
        == "[2024-06-01 21:00] #backend @alice: hello world | https://example.slack.com/archives/C1/p1717243200000100",
    )


def case_common_format_message_line_attachment_text() -> bool:
    message = {
        "ts": "1717243200.000100",
        "user": "B123",
        "text": "",
        "attachments": [
            {
                "title": "500 Internal Server Error",
                "text": "POST /api/orders failed",
                "fallback": "500 Internal Server Error - POST /api/orders failed",
            }
        ],
        "permalink": "https://example.test/p1",
    }
    line = common.format_message_line(message, "alerts", "alertbot")
    return check(
        "format_message_line surfaces attachment text when message text is empty",
        "500 Internal Server Error" in line and "POST /api/orders failed" in line,
        line,
    )


def case_common_format_message_line_blocks_dedup() -> bool:
    message = {
        "ts": "1717243200.000100",
        "user": "U123",
        "text": "hello world",
        "blocks": [
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [{"type": "text", "text": "hello world"}],
                    }
                ],
            }
        ],
        "permalink": "https://example.test/p1",
    }
    line = common.format_message_line(message, "backend", "alice")
    return check(
        "format_message_line dedups block text that mirrors message text",
        ": hello world |" in line,
        line,
    )


def case_common_legacy_config_migration() -> bool:
    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "oauth-app.json",
                {
                    "client_id": "CID",
                    "client_secret": "S",
                    "redirect_uri": "http://localhost:8765/callback",
                    "scopes": ["team:read"],
                    "user_scopes": ["search:read"],
                    "user_identity": {"identifier": "sample.user", "name": "old-name"},
                },
            )
            common.write_json_secure(
                Path(tmp) / "api-key.json",
                {
                    "default_workspace": "default",
                    "workspaces": {
                        "default": {"token": "t", "user_identity": {"user_id": "U123"}}
                    },
                },
            )
            common.write_json_secure(
                Path(tmp) / "context.json",
                {
                    "me": {"identifier": "sample.user"},
                    "channels": {
                        "backend": {"id": "C1", "name": "backend", "summary": "backend work"}
                    },
                },
            )
            config = common.load_config()
            config_mode = stat.S_IMODE(common.config_path().stat().st_mode)
            memory_text = (Path(tmp) / "MEMORY.md").read_text(encoding="utf-8")
            legacy_left = [
                name
                for name in common.LEGACY_CONFIG_FILES
                if (Path(tmp) / name).exists()
            ]
        finally:
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    identity = config["workspaces"]["default"]["user_identity"]
    return check(
        "legacy 3-file config migrates into config.json + MEMORY.md and removes old files",
        config["app"]["client_id"] == "CID"
        and "user_identity" not in config["app"]
        and identity == {"identifier": "sample.user", "name": "old-name", "user_id": "U123"}
        and config["default_workspace"] == "default"
        and config_mode == 0o600
        and "backend — C1 — backend work" in memory_text
        and not legacy_left,
        str(identity),
    )


def case_setup_workspace_slug_normalizes() -> bool:
    setup = load_module("slack_setup")
    return check(
        "slack_setup.workspace_slug lowercases and hyphenates",
        setup.workspace_slug("My Team!!") == "my-team"
        and setup.workspace_slug("!!!") == "default",
    )


def case_setup_oauth_url_uses_saved_config() -> bool:
    setup = load_module("slack_setup")
    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "app": {
                        "client_id": "CID123",
                        "client_secret": "S",
                        "redirect_uri": "http://localhost:8765/callback",
                        "scopes": ["team:read", "users:read"],
                        "user_scopes": ["search:read"],
                    }
                },
            )
            args = type(
                "Args",
                (),
                {
                    "scopes": None,
                    "user_scopes": None,
                    "redirect_uri": None,
                    "state": "abc",
                    "team": None,
                },
            )()
            url = setup.oauth_url(args)
        finally:
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    return check(
        "slack_setup.oauth_url composes Slack authorization URL",
        "client_id=CID123" in url
        and "scope=team%3Aread%2Cusers%3Aread" in url
        and "user_scope=search%3Aread%2Cchannels%3Aread%2Cchannels%3Ahistory%2Cgroups%3Aread%2Cgroups%3Ahistory" in url
        and "state=abc" in url,
        url,
    )


def case_setup_save_identity_single_store() -> bool:
    setup = load_module("slack_setup")
    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            missing_workspace_raises = False
            try:
                setup.save_identity({"identifier": "sample.user"})
            except common.SlackHelperError:
                missing_workspace_raises = True
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "default_workspace": "default",
                    "workspaces": {"default": {"token": "t"}},
                },
            )
            saved = setup.save_identity(
                {"identifier": "sample.user", "user_id": "U123"},
                workspace_name="default",
            )
            config = common.load_config()
        finally:
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    return check(
        "slack_setup.save_identity stores identity only in workspace record",
        missing_workspace_raises
        and saved == "default"
        and config["workspaces"]["default"]["user_identity"]["user_id"] == "U123"
        and "user_identity" not in config.get("app", {})
        and "me" not in config,
    )


def case_setup_init_oauth_rejects_non_tty() -> bool:
    setup = load_module("slack_setup")
    args = type(
        "Args",
        (),
        {
            "client_id": None,
            "redirect_uri": None,
            "scopes": None,
            "user_scopes": None,
        },
    )()
    try:
        setup.command_init_oauth(args)
    except common.SlackHelperError:
        return check("slack_setup.init-oauth rejects non-TTY execution", True)
    return check("slack_setup.init-oauth rejects non-TTY execution", False)


def case_read_users_compact_and_raw() -> bool:
    read = load_module("slack_read")
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        calls.append((method, payload or {}))
        return {
            "ok": True,
            "members": [
                {"id": "U1", "name": "alice", "real_name": "Alice", "profile": {}}
            ],
        }

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "default_workspace": "default",
                    "workspaces": {"default": {"token": "t"}},
                },
            )
            read.slack_method = fake_slack_method
            compact = io.StringIO()
            with redirect_stdout(compact):
                read.command_users(type("Args", (), {"workspace": None, "limit": 20, "raw": False})())
            raw = io.StringIO()
            with redirect_stdout(raw):
                read.command_users(type("Args", (), {"workspace": None, "limit": 20, "raw": True})())
        finally:
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    return check(
        "slack_read users defaults compact and supports --raw",
        "U1\talice\tAlice" in compact.getvalue()
        and '"members"' in raw.getvalue()
        and calls[0] == ("users.list", {"limit": 20}),
    )


def case_read_channel_history_and_thread() -> bool:
    read = load_module("slack_read")
    calls: list[tuple[str, dict[str, object]]] = []
    original = common.slack_method

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        calls.append((method, payload or {}))
        if method == "conversations.list":
            return {"ok": True, "channels": [{"id": "C1", "name": "backend"}]}
        if method == "users.info":
            return {"ok": True, "user": {"id": "U1", "name": "alice", "profile": {"display_name": "Alice"}}}
        return {
            "ok": True,
            "messages": [
                {
                    "ts": "1717243200.0",
                    "user": "U1",
                    "text": "hello",
                    "permalink": "https://example.test/p1",
                }
            ],
        }

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "default_workspace": "default",
                    "workspaces": {"default": {"token": "t"}},
                },
            )
            common.slack_method = fake_slack_method
            read.slack_method = fake_slack_method
            history = io.StringIO()
            with redirect_stdout(history):
                read.command_channel_history(
                    type(
                        "Args",
                        (),
                        {"workspace": None, "channel": "backend", "limit": 2, "on": None, "raw": False},
                    )()
                )
            thread = io.StringIO()
            with redirect_stdout(thread):
                read.command_thread(
                    type(
                        "Args",
                        (),
                        {"workspace": None, "channel": "C1", "ts": "1717243200.0", "limit": 50, "raw": False},
                    )()
                )
        finally:
            common.slack_method = original
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    return check(
        "slack_read channel-history resolves channel name and thread calls conversations.replies",
        "[2024-06-01 21:00] #C1 @Alice: hello | https://example.test/p1" in history.getvalue()
        and calls[0][0] == "conversations.list"
        and calls[1] == ("conversations.history", {"channel": "C1", "limit": 2})
        and calls[2] == ("users.info", {"user": "U1"})
        and calls[3] == ("conversations.replies", {"channel": "C1", "ts": "1717243200.0", "limit": 50})
        and "@Alice" in thread.getvalue(),
        str(calls),
    )


def case_read_channel_history_on_date_payload() -> bool:
    read = load_module("slack_read")
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        calls.append((method, payload or {}))
        return {"ok": True, "messages": []}

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "default_workspace": "default",
                    "workspaces": {"default": {"token": "t"}},
                },
            )
            read.slack_method = fake_slack_method
            with redirect_stdout(io.StringIO()):
                read.command_channel_history(
                    type(
                        "Args",
                        (),
                        {"workspace": None, "channel": "C1", "limit": 100, "on": "2026-07-05", "raw": False},
                    )()
                )
        finally:
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    day_bounds = getattr(common, "day_bounds", None)
    if day_bounds is None or not calls:
        return check(
            "channel-history --on adds oldest/latest/inclusive to payload",
            False,
            "day_bounds missing or no API call recorded",
        )
    oldest, latest = day_bounds("2026-07-05")
    return check(
        "channel-history --on adds oldest/latest/inclusive to payload",
        calls[0]
        == (
            "conversations.history",
            {"channel": "C1", "limit": 100, "oldest": oldest, "latest": latest, "inclusive": "true"},
        ),
        str(calls[0]),
    )


def case_read_not_in_channel_uses_user_token_fallback() -> bool:
    read = load_module("slack_read")
    calls: list[tuple[str, str | None, dict[str, object]]] = []
    original = common.slack_method

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        calls.append((method, token, payload or {}))
        if method == "users.info":
            return {"ok": True, "user": {"id": "U1", "name": "alice", "profile": {}}}
        if token == "bot":
            return {"ok": False, "_slack_error": "not_in_channel", "error": "not_in_channel"}
        return {
            "ok": True,
            "messages": [
                {
                    "ts": "1.0",
                    "user": "U1",
                    "text": "fallback ok",
                    "permalink": "https://example.test/thread",
                }
            ],
        }

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "default_workspace": "default",
                    "workspaces": {
                        "default": {
                            "token": "bot",
                            "authed_user": {"access_token": "user"},
                        }
                    },
                },
            )
            common.slack_method = fake_slack_method
            read.slack_method = fake_slack_method
            output = io.StringIO()
            with redirect_stdout(output):
                read.command_thread(
                    type("Args", (), {"workspace": None, "channel": "C1", "ts": "1.0", "limit": 50, "raw": False})()
                )
        finally:
            common.slack_method = original
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    return check(
        "slack_read not_in_channel retries direct read with user token",
        calls
        == [
            ("conversations.replies", "bot", {"channel": "C1", "ts": "1.0", "limit": 50}),
            ("conversations.replies", "user", {"channel": "C1", "ts": "1.0", "limit": 50}),
            ("users.info", "bot", {"user": "U1"}),
        ]
        and "fallback ok" in output.getvalue(),
        str(calls),
    )


def case_read_private_channel_name_uses_user_token_resolution() -> bool:
    read = load_module("slack_read")
    calls: list[tuple[str, str | None, dict[str, object]]] = []
    original = common.slack_method

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        calls.append((method, token, payload or {}))
        if method == "conversations.list" and token == "bot":
            return {"ok": True, "channels": [{"id": "C1", "name": "public"}]}
        if method == "conversations.list" and token == "user":
            return {"ok": True, "channels": [{"id": "G1", "name": "private-team"}]}
        if method == "users.info":
            return {"ok": True, "user": {"id": "U1", "name": "alice", "profile": {}}}
        return {
            "ok": True,
            "messages": [
                {
                    "ts": "2.0",
                    "user": "U1",
                    "text": "private ok",
                    "permalink": "https://example.test/private",
                }
            ],
        }

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "default_workspace": "default",
                    "workspaces": {
                        "default": {
                            "token": "bot",
                            "authed_user": {"access_token": "user"},
                        }
                    },
                },
            )
            common.slack_method = fake_slack_method
            read.slack_method = fake_slack_method
            output = io.StringIO()
            with redirect_stdout(output):
                read.command_channel_history(
                    type(
                        "Args",
                        (),
                        {"workspace": None, "channel": "private-team", "limit": 20, "on": None, "raw": False},
                    )()
                )
        finally:
            common.slack_method = original
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    return check(
        "slack_read resolves private channel names with user token fallback",
        calls
        == [
            (
                "conversations.list",
                "bot",
                {"limit": 200, "types": "public_channel", "exclude_archived": "true"},
            ),
            (
                "conversations.list",
                "user",
                {"limit": 200, "types": "public_channel,private_channel", "exclude_archived": "true"},
            ),
            ("conversations.history", "user", {"channel": "G1", "limit": 20}),
            ("users.info", "bot", {"user": "U1"}),
        ]
        and "private ok" in output.getvalue(),
        str(calls),
    )


def case_search_build_query_options() -> bool:
    search = load_module("slack_search")
    args = type(
        "Args",
        (),
        {
            "from_user": "me",
            "in_channel": "#backend-team",
            "to_me": True,
            "after": "2026-07-01",
            "before": None,
            "on": None,
            "days": None,
            "user_id": "U123",
        },
    )()
    queries = search.build_search_query(["deploy fix"], args)
    multi = search.build_search_query(
        ["alpha", "beta"],
        type(
            "Args",
            (),
            {
                "from_user": None,
                "in_channel": None,
                "to_me": False,
                "after": None,
                "before": None,
                "on": None,
                "days": None,
                "user_id": None,
            },
        )(),
    )
    return check(
        "slack_search build_search_query maps modifiers and splits multiple keywords",
        queries == ['"deploy fix" from:me in:backend-team "<@U123>" after:2026-07-01']
        and multi == ["alpha", "beta"],
        str((queries, multi)),
    )


def case_search_days_after_conflict_and_to_me_error() -> bool:
    search = load_module("slack_search")
    conflict = False
    missing_me = False
    try:
        search.build_search_query(
            ["deploy"],
            type(
                "Args",
                (),
                {
                    "from_user": None,
                    "in_channel": None,
                    "to_me": False,
                    "after": "2026-07-01",
                    "before": None,
                    "on": None,
                    "days": 7,
                    "user_id": None,
                },
            )(),
        )
    except common.SlackHelperError:
        conflict = True
    try:
        search.build_search_query(
            ["deploy"],
            type(
                "Args",
                (),
                {
                    "from_user": None,
                    "in_channel": None,
                    "to_me": True,
                    "after": None,
                    "before": None,
                    "on": None,
                    "days": None,
                    "user_id": None,
                },
            )(),
        )
    except common.SlackHelperError as exc:
        missing_me = "resolve-me" in str(exc)
    return check(
        "slack_search rejects --days/--after conflict and missing --to-me identity",
        conflict and missing_me,
    )


def case_search_empty_query_with_from_allowed() -> bool:
    search = load_module("slack_search")

    def make_args(**overrides):
        fields = {
            "from_user": None,
            "in_channel": None,
            "to_me": False,
            "after": None,
            "before": None,
            "on": None,
            "days": None,
            "user_id": None,
        }
        fields.update(overrides)
        return type("Args", (), fields)()

    allowed = None
    try:
        allowed = search.build_search_query([], make_args(from_user="me", on="2026-07-03"))
    except common.SlackHelperError:
        pass
    bare_raises = False
    try:
        search.build_search_query([], make_args())
    except common.SlackHelperError:
        bare_raises = True
    return check(
        "empty query is allowed with --from but still rejected bare",
        allowed == ["from:me on:2026-07-03"] and bare_raises,
        str(allowed),
    )


def case_search_merge_dedups_and_sorts() -> bool:
    search = load_module("slack_search")
    merged = search.merge_search_matches(
        [
            {"messages": {"matches": [{"channel": {"id": "C1"}, "ts": "2.0", "text": "b"}]}},
            {
                "messages": {
                    "matches": [
                        {"channel": {"id": "C1"}, "ts": "2.0", "text": "dupe"},
                        {"channel": {"id": "C2"}, "ts": "3.0", "text": "c"},
                    ]
                }
            },
        ]
    )
    return check(
        "slack_search merge_search_matches dedups and sorts by ts desc",
        [item["text"] for item in merged] == ["c", "b"],
        str(merged),
    )


def case_search_command_multi_keyword_compact() -> bool:
    search = load_module("slack_search")
    calls: list[tuple[str, dict[str, object]]] = []
    original = common.slack_method

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        if method == "users.info":
            return {"ok": True, "user": {"id": "U1", "name": "alice", "profile": {"display_name": "Alice"}}}
        calls.append((method, payload or {}))
        return {
            "ok": True,
            "messages": {
                "matches": [
                    {
                        "channel": {"id": "C1", "name": "backend"},
                        "ts": "1717243200.0",
                        "user": "U1",
                        "text": str((payload or {}).get("query")),
                        "permalink": "https://example.test/p1",
                    }
                ]
            },
        }

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.slack_method = fake_slack_method
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "default_workspace": "default",
                    "workspaces": {
                        "default": {
                            "token": "t",
                            "authed_user": {"access_token": "u"},
                        }
                    },
                },
            )
            search.slack_method = fake_slack_method
            args = type(
                "Args",
                (),
                {
                    "workspace": None,
                    "query": ["alpha", "beta"],
                    "from_user": None,
                    "in_channel": None,
                    "to_me": False,
                    "after": None,
                    "before": None,
                    "on": None,
                    "days": None,
                    "count": 20,
                    "page": 1,
                    "limit": None,
                    "sort": "timestamp",
                    "sort_dir": "desc",
                    "highlight": False,
                    "jsonl": False,
                    "raw": False,
                },
            )()
            output = io.StringIO()
            with redirect_stdout(output):
                search.command_search(args)
        finally:
            common.slack_method = original
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    return check(
        "slack_search command calls search per keyword and prints compact merged output",
        [call[1]["query"] for call in calls] == ["alpha", "beta"]
        and "#backend @Alice" in output.getvalue(),
        output.getvalue(),
    )


def case_search_limit_auto_paginates() -> bool:
    search = load_module("slack_search")
    calls: list[dict[str, object]] = []
    original = common.slack_method

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        payload = payload or {}
        if method == "users.info":
            return {"ok": True, "user": {"id": "U1", "name": "alice", "profile": {}}}
        calls.append(payload)
        page = int(str(payload.get("page")))
        start = (page - 1) * 100
        size = 100 if page == 1 else 35
        matches = [
            {
                "channel": {"id": "C1", "name": "alerts"},
                "ts": f"{1717243200 + start + index}.0",
                "user": "U1",
                "text": f"alert {start + index}",
                "permalink": f"https://example.test/p{start + index}",
            }
            for index in range(size)
        ]
        return {
            "ok": True,
            "messages": {"matches": matches, "paging": {"page": page, "pages": 2}},
        }

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "default_workspace": "default",
                    "workspaces": {
                        "default": {
                            "token": "t",
                            "authed_user": {"access_token": "u"},
                        }
                    },
                },
            )
            common.slack_method = fake_slack_method
            search.slack_method = fake_slack_method
            args = type(
                "Args",
                (),
                {
                    "workspace": None,
                    "query": ["alert"],
                    "from_user": None,
                    "in_channel": None,
                    "to_me": False,
                    "after": None,
                    "before": None,
                    "on": None,
                    "days": None,
                    "count": 20,
                    "page": 1,
                    "limit": 120,
                    "sort": "timestamp",
                    "sort_dir": "desc",
                    "highlight": False,
                    "jsonl": False,
                    "raw": False,
                },
            )()
            output = io.StringIO()
            with redirect_stdout(output):
                search.command_search(args)
        finally:
            common.slack_method = original
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    lines = [line for line in output.getvalue().splitlines() if line.strip()]
    return check(
        "slack_search --limit walks pages with count=100 and trims merged output to limit",
        [call["page"] for call in calls] == [1, 2]
        and all(call["count"] == 100 for call in calls)
        and len(lines) == 120,
        f"pages={[call['page'] for call in calls]} lines={len(lines)}",
    )


def case_common_parse_permalink() -> bool:
    plain = common.parse_permalink(
        "https://acme.slack.com/archives/C0123456789/p1717243200000100"
    )
    reply = common.parse_permalink(
        "https://acme.slack.com/archives/C0123456789/p1717243999000500"
        "?thread_ts=1717243200.000100&cid=C0123456789"
    )
    invalid_raises = False
    try:
        common.parse_permalink("https://acme.slack.com/messages/general")
    except common.SlackHelperError:
        invalid_raises = True
    return check(
        "parse_permalink extracts channel/ts and prefers thread_ts for replies",
        plain == ("C0123456789", "1717243200.000100")
        and reply == ("C0123456789", "1717243200.000100")
        and invalid_raises,
        str((plain, reply)),
    )


def case_common_resolve_mentions_in_text() -> bool:
    users = {"U1": "Alice"}
    resolved = common.resolve_mentions_in_text(
        "<@U1> <@U2> <@U3|bob> <#C1|backend> <#C2> <!here>", users
    )
    return check(
        "resolve_mentions_in_text maps cached users, labels, channels, and specials",
        resolved == "@Alice @U2 @bob #backend #C2 @here",
        resolved,
    )


def case_common_format_message_line_uses_users_cache() -> bool:
    message = {
        "ts": "1717243200.000100",
        "user": "U1",
        "text": "cc <@U2>",
        "permalink": "https://example.test/p1",
    }
    line = common.format_message_line(message, "backend", users={"U1": "Alice", "U2": "Bob"})
    return check(
        "format_message_line resolves author and mentions from the users cache",
        line == "[2024-06-01 21:00] #backend @Alice: cc @Bob | https://example.test/p1",
        line,
    )


def case_common_range_bounds() -> bool:
    day_start, _ = common.day_bounds("2026-07-01", "Asia/Seoul")
    _, day_end = common.day_bounds("2026-07-05", "Asia/Seoul")
    both = common.range_bounds("2026-07-01", "2026-07-05", "Asia/Seoul")
    only_after = common.range_bounds("2026-07-01", None, "Asia/Seoul")
    inverted_raises = False
    try:
        common.range_bounds("2026-07-05", "2026-07-01", "Asia/Seoul")
    except common.SlackHelperError:
        inverted_raises = True
    bad_tz_raises = False
    try:
        common.range_bounds("2026-07-01", None, "Not/AZone")
    except common.SlackHelperError:
        bad_tz_raises = True
    return check(
        "range_bounds spans inclusive days and rejects inverted range / bad tz",
        both == (day_start, day_end)
        and only_after == (day_start, None)
        and inverted_raises
        and bad_tz_raises,
        str(both),
    )


def case_common_users_cache_roundtrip_and_ensure() -> bool:
    original = common.slack_method
    calls: list[str] = []

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        user_id = str((payload or {}).get("user"))
        calls.append(user_id)
        if user_id == "U5":
            return {"ok": False, "_slack_error": "user_not_found"}
        if user_id == "U2":
            return {"ok": False, "_slack_error": "missing_scope"}
        return {"ok": True, "user": {"id": "U1", "profile": {"display_name": "Alice"}}}

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.save_users_cache({"U9": "Nine"})
            cache_mode = stat.S_IMODE(common.users_cache_path().stat().st_mode)
            common.slack_method = fake_slack_method
            cache = common.ensure_users_cached(["U9", "U1", "U5", "U2", "U3"], "t")
            reloaded = common.load_users_cache()
        finally:
            common.slack_method = original
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    expected = {"U9": "Nine", "U1": "Alice", "U5": "U5"}
    return check(
        "users cache persists at 600, negative-caches dead ids, stops on missing_scope",
        cache_mode == 0o600
        and cache == expected
        and reloaded == expected
        and calls == ["U1", "U5", "U2"],
        f"cache={cache} calls={calls}",
    )


def case_read_thread_permalink_and_jsonl() -> bool:
    read = load_module("slack_read")
    calls: list[tuple[str, dict[str, object]]] = []
    original = common.slack_method

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        calls.append((method, payload or {}))
        if method == "users.info":
            return {"ok": True, "user": {"id": "U1", "profile": {"display_name": "Alice"}}}
        return {
            "ok": True,
            "messages": [
                {"ts": "1717243200.000100", "user": "U1", "text": "root <@U1>", "reply_count": 2}
            ],
        }

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "config.json",
                {"default_workspace": "default", "workspaces": {"default": {"token": "t"}}},
            )
            common.slack_method = fake_slack_method
            read.slack_method = fake_slack_method
            output = io.StringIO()
            with redirect_stdout(output):
                read.command_thread(
                    type(
                        "Args",
                        (),
                        {
                            "workspace": None,
                            "channel": None,
                            "ts": None,
                            "permalink": "https://acme.slack.com/archives/C0123456789/p1717243200000100",
                            "limit": 50,
                            "jsonl": True,
                            "raw": False,
                        },
                    )()
                )
            conflict_raises = False
            try:
                read.command_thread(
                    type(
                        "Args",
                        (),
                        {
                            "workspace": None,
                            "channel": "C1",
                            "ts": None,
                            "permalink": "https://acme.slack.com/archives/C1/p1717243200000100",
                            "limit": 50,
                            "jsonl": False,
                            "raw": False,
                        },
                    )()
                )
            except common.SlackHelperError:
                conflict_raises = True
        finally:
            common.slack_method = original
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    record = json.loads(output.getvalue().splitlines()[0])
    return check(
        "thread --permalink parses channel/ts and --jsonl emits structured lines",
        calls[0]
        == (
            "conversations.replies",
            {"channel": "C0123456789", "ts": "1717243200.000100", "limit": 50},
        )
        and record["channel"] == "C0123456789"
        and record["user_name"] == "Alice"
        and record["text"] == "root @Alice"
        and record["reply_count"] == 2
        and conflict_raises,
        str(record),
    )


def case_read_channel_history_range_payload() -> bool:
    read = load_module("slack_read")
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        calls.append((method, payload or {}))
        return {"ok": True, "messages": []}

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "config.json",
                {"default_workspace": "default", "workspaces": {"default": {"token": "t"}}},
            )
            read.slack_method = fake_slack_method

            def make_args(**overrides):
                fields = {
                    "workspace": None,
                    "channel": "C1",
                    "limit": 100,
                    "on": None,
                    "after": "2026-07-01",
                    "before": "2026-07-05",
                    "tz": "Asia/Seoul",
                    "jsonl": False,
                    "raw": False,
                }
                fields.update(overrides)
                return type("Args", (), fields)()

            with redirect_stdout(io.StringIO()):
                read.command_channel_history(make_args())
            conflict_raises = False
            try:
                read.command_channel_history(make_args(on="2026-07-03"))
            except common.SlackHelperError:
                conflict_raises = True
        finally:
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    oldest, latest = common.range_bounds("2026-07-01", "2026-07-05", "Asia/Seoul")
    return check(
        "channel-history --after/--before/--tz sets inclusive oldest/latest bounds",
        calls[0]
        == (
            "conversations.history",
            {"channel": "C1", "limit": 100, "oldest": oldest, "latest": latest, "inclusive": "true"},
        )
        and conflict_raises,
        str(calls[0] if calls else None),
    )


def case_search_jsonl_output() -> bool:
    search = load_module("slack_search")
    original = common.slack_method

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        if method == "users.info":
            return {"ok": True, "user": {"id": "U1", "profile": {"display_name": "Alice"}}}
        return {
            "ok": True,
            "messages": {
                "matches": [
                    {
                        "channel": {"id": "C1", "name": "backend"},
                        "ts": "1717243200.0",
                        "user": "U1",
                        "text": "deploy done",
                        "permalink": "https://example.test/p1",
                    }
                ]
            },
        }

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "default_workspace": "default",
                    "workspaces": {
                        "default": {"token": "t", "authed_user": {"access_token": "u"}}
                    },
                },
            )
            common.slack_method = fake_slack_method
            search.slack_method = fake_slack_method
            args = type(
                "Args",
                (),
                {
                    "workspace": None,
                    "query": ["deploy"],
                    "from_user": None,
                    "in_channel": None,
                    "to_me": False,
                    "after": None,
                    "before": None,
                    "on": None,
                    "days": None,
                    "count": 20,
                    "page": 1,
                    "limit": None,
                    "sort": "timestamp",
                    "sort_dir": "desc",
                    "highlight": False,
                    "jsonl": True,
                    "raw": False,
                },
            )()
            output = io.StringIO()
            with redirect_stdout(output):
                search.command_search(args)
            conflict_raises = False
            try:
                args.raw = True
                search.command_search(args)
            except common.SlackHelperError:
                conflict_raises = True
        finally:
            common.slack_method = original
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    record = json.loads(output.getvalue().splitlines()[0])
    return check(
        "search --jsonl emits one JSON object per match and rejects --raw combo",
        record["channel"] == "C1"
        and record["channel_name"] == "backend"
        and record["user"] == "U1"
        and record["user_name"] == "Alice"
        and record["text"] == "deploy done"
        and record["permalink"] == "https://example.test/p1"
        and conflict_raises,
        str(record),
    )


def case_setup_doctor_reports_status() -> bool:
    setup = load_module("slack_setup")
    original = common.slack_method

    def fake_slack_method(method, *, token=None, payload=None, http_method="POST", **kwargs):
        return {"ok": True, "team": "acme", "user": "helper"}

    with tempfile.TemporaryDirectory(prefix="slack-helper-test-") as tmp:
        os.environ["SLACK_HELPER_CONFIG_DIR"] = tmp
        try:
            missing_output = io.StringIO()
            with redirect_stdout(missing_output):
                missing_code = setup.command_doctor(type("Args", (), {"workspace": None})())
            common.write_json_secure(
                Path(tmp) / "config.json",
                {
                    "app": {"client_id": "CID", "client_secret": "S"},
                    "default_workspace": "default",
                    "workspaces": {
                        "default": {
                            "token": "bot",
                            "scope": "team:read,users:read,channels:read,channels:history",
                            "authed_user": {
                                "access_token": "user",
                                "scope": "search:read,channels:read",
                            },
                            "user_identity": {"identifier": "alice", "user_id": "U1"},
                        }
                    },
                },
            )
            common.slack_method = fake_slack_method
            setup.slack_method = fake_slack_method
            ok_output = io.StringIO()
            with redirect_stdout(ok_output):
                ok_code = setup.command_doctor(type("Args", (), {"workspace": None})())
        finally:
            common.slack_method = original
            os.environ.pop("SLACK_HELPER_CONFIG_DIR", None)
    text = ok_output.getvalue()
    return check(
        "doctor reports missing config as failure and healthy setup with scope warning",
        missing_code == 1
        and "설정 파일이 없습니다" in missing_output.getvalue()
        and ok_code == 0
        and "Bot token 유효" in text
        and "User token 유효" in text
        and "User scope 부족" in text
        and "identity 확인됨" in text,
        text.splitlines()[-1] if text else "",
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
        case_resolve_channel_id_and_name_lookup,
        case_write_json_secure_permissions,
        case_common_format_ts_local,
        case_common_day_bounds_boundaries,
        case_common_truncate_text,
        case_common_format_message_line,
        case_common_format_message_line_attachment_text,
        case_common_format_message_line_blocks_dedup,
        case_common_legacy_config_migration,
        case_setup_workspace_slug_normalizes,
        case_setup_oauth_url_uses_saved_config,
        case_setup_save_identity_single_store,
        case_setup_init_oauth_rejects_non_tty,
        case_read_users_compact_and_raw,
        case_read_channel_history_and_thread,
        case_read_channel_history_on_date_payload,
        case_read_not_in_channel_uses_user_token_fallback,
        case_read_private_channel_name_uses_user_token_resolution,
        case_search_build_query_options,
        case_search_days_after_conflict_and_to_me_error,
        case_search_empty_query_with_from_allowed,
        case_search_merge_dedups_and_sorts,
        case_search_command_multi_keyword_compact,
        case_search_limit_auto_paginates,
        case_common_parse_permalink,
        case_common_resolve_mentions_in_text,
        case_common_format_message_line_uses_users_cache,
        case_common_range_bounds,
        case_common_users_cache_roundtrip_and_ensure,
        case_read_thread_permalink_and_jsonl,
        case_read_channel_history_range_payload,
        case_search_jsonl_output,
        case_setup_doctor_reports_status,
    ]
    results = [case() for case in cases]
    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
