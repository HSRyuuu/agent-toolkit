#!/usr/bin/env python3
"""Tests for deterministic jira-helper behavior.

Run with: python3 test_jira_helper.py
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load_module("jira_common")
search = load_module("jira_search")
setup = load_module("jira_setup")


def check(name: str, cond: bool, detail: str = "") -> bool:
    suffix = f" - {detail}" if detail else ""
    print(f"[{'PASS' if cond else 'FAIL'}] {name}{suffix}")
    return cond


def case_normalize_site() -> bool:
    ok = (
        common.normalize_site("your-org.atlassian.net") == "https://your-org.atlassian.net"
        and common.normalize_site("https://your-org.atlassian.net/browse/ABC-1")
        == "https://your-org.atlassian.net"
        and common.normalize_site("HTTP://Your-Org.Atlassian.Net")
        == "https://your-org.atlassian.net"
    )
    try:
        common.normalize_site("notahost")
        ok = False
    except common.JiraHelperError:
        pass
    return check("normalize_site accepts hosts/URLs and rejects garbage", ok)


def case_secure_write_permissions() -> bool:
    with tempfile.TemporaryDirectory(prefix="jira-helper-test-") as tmp:
        target = Path(tmp) / "nested" / "config.json"
        common.write_json_secure(target, {"api_token": "abc"})
        file_mode = stat.S_IMODE(target.stat().st_mode)
        dir_mode = stat.S_IMODE(target.parent.stat().st_mode)
        data = common.read_json(target)
    return check(
        "write_json_secure writes 600 file under 700 dir",
        file_mode == 0o600 and dir_mode == 0o700 and data == {"api_token": "abc"},
        f"file={oct(file_mode)} dir={oct(dir_mode)}",
    )


def case_memory_file_created_securely() -> bool:
    with tempfile.TemporaryDirectory(prefix="jira-helper-test-") as tmp:
        os.environ["JIRA_HELPER_CONFIG_DIR"] = tmp
        try:
            path = common.ensure_memory_file()
            file_mode = stat.S_IMODE(path.stat().st_mode)
            text = path.read_text(encoding="utf-8")
        finally:
            os.environ.pop("JIRA_HELPER_CONFIG_DIR", None)
    return check(
        "ensure_memory_file creates expected template",
        file_mode == 0o600 and "## 자주 쓰는 JQL" in text and "## 프로젝트 별칭" in text,
    )


def case_sensitive_sanitizing() -> bool:
    profile = {"email": "user@example.com", "api_token": "SECRETTOKEN12345"}
    text = common.sanitize_sensitive(
        f"Authorization: Basic {common.basic_auth_header(profile).split(' ', 1)[1]} "
        "token=SECRETTOKEN12345",
        profile,
    )
    return check(
        "sanitize_sensitive masks token and Authorization header",
        "SECRETTOKEN12345" not in text and "Basic ***" in text,
        text,
    )


def case_jql_quote_escapes() -> bool:
    return check(
        "jql_quote escapes quotes and backslashes",
        common.jql_quote('say "hi" \\ bye') == '"say \\"hi\\" \\\\ bye"',
        common.jql_quote('say "hi" \\ bye'),
    )


def case_jql_time_value() -> bool:
    return check(
        "jql_time_value keeps relative/functions raw, quotes dates",
        common.jql_time_value("-7d") == "-7d"
        and common.jql_time_value("startOfWeek()") == "startOfWeek()"
        and common.jql_time_value('endOfDay("-1")') == 'endOfDay("-1")'
        and common.jql_time_value("2026-07-01") == '"2026-07-01"',
    )


def case_jql_in_clause() -> bool:
    return check(
        "jql_in_clause single vs multiple values",
        common.jql_in_clause("status", ["Done"]) == 'status = "Done"'
        and common.jql_in_clause("status", ["To Do", "In Progress"])
        == 'status IN ("To Do", "In Progress")',
    )


def case_combine_jql() -> bool:
    return check(
        "combine_jql joins clauses with AND + ORDER BY",
        common.combine_jql(["a = 1", "", "b = 2"], order_by="updated DESC")
        == "a = 1 AND b = 2 ORDER BY updated DESC",
    )


def case_adf_to_text() -> bool:
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "hello "},
                    {"type": "mention", "attrs": {"text": "@길동"}},
                ],
            },
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "item one"}],
                            }
                        ],
                    }
                ],
            },
        ],
    }
    text = common.adf_summary(doc)
    return check(
        "adf_summary flattens paragraphs, mentions, lists",
        "hello @길동" in text and "- item one" in text,
        text,
    )


def case_due_label() -> bool:
    tz = "Asia/Seoul"
    today = datetime.now(common.ZoneInfo(tz)).date()
    soon = (today + timedelta(days=3)).strftime("%Y-%m-%d")
    past = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    return check(
        "due_label renders D-day and overdue markers",
        common.due_label(soon, tz).endswith("(D-3)")
        and common.due_label(past, tz).endswith("(OVERDUE 2d)")
        and common.due_label(today.strftime("%Y-%m-%d"), tz).endswith("(D-DAY)")
        and common.due_label(None, tz) == "-",
    )


def case_format_issue() -> bool:
    issue = {
        "key": "ABC-123",
        "fields": {
            "summary": "로그인   실패 시\n에러 메시지 개선",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Bug"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "홍길동"},
            "duedate": None,
            "updated": "2026-07-14T10:03:21.000+0900",
            "labels": ["backend"],
        },
    }
    text = common.format_issue(issue, tz_name="Asia/Seoul")
    return check(
        "format_issue emits compact block",
        "ABC-123  [In Progress]  Bug/High" in text
        and "로그인 실패 시 에러 메시지 개선" in text
        and "assignee=홍길동" in text
        and "2026-07-14 10:03" in text
        and "labels=backend" in text,
        text,
    )


def case_format_issue_unassigned() -> bool:
    issue = {"key": "ABC-1", "fields": {"summary": "x", "assignee": None}}
    text = common.format_issue(issue)
    return check("format_issue marks unassigned issues", "assignee=(미배정)" in text, text)


def _parse(argv: list[str]):
    return search.build_parser().parse_args(argv)


def case_mine_jql() -> bool:
    args = _parse(
        [
            "mine",
            "--updated-from=-7d",
            "--status",
            "In Progress",
            "--status",
            "To Do",
            "--project",
            "ABC",
            "--unresolved",
        ]
    )
    clauses = ["assignee = currentUser()", f"updated >= {common.jql_time_value('-7d')}"]
    clauses.extend(search._filter_clauses(args))
    jql = common.combine_jql(clauses, order_by=args.order)
    return check(
        "mine composes assignee/date/status/project JQL",
        jql
        == 'assignee = currentUser() AND updated >= -7d AND project = "ABC" '
        'AND status IN ("In Progress", "To Do") AND resolution = EMPTY '
        "ORDER BY updated DESC",
        jql,
    )


def case_due_defaults() -> bool:
    args = _parse(["due"])
    return check(
        "due defaults: within 7d, order by due ASC",
        args.within == 7 and args.order == "due ASC" and not args.anyone,
    )


def case_worked_conflicting_args() -> bool:
    args = _parse(["worked", "--days", "7", "--from=-30d"])
    try:
        search.command_worked(args)
        return check("worked rejects --days with --from", False)
    except common.JiraHelperError as exc:
        return check("worked rejects --days with --from", "함께 쓸 수 없습니다" in str(exc))


def case_limit_validation() -> bool:
    args = _parse(["search", "assignee = currentUser()", "--limit", "500"])
    try:
        search._resolve_limit(args, {})
        return check("limit over 100 rejected", False)
    except common.JiraHelperError:
        return check("limit over 100 rejected", True)


def case_default_limit_capped() -> bool:
    return check(
        "profile default_limit is sanitized",
        search._default_limit({"default_limit": 9999}) == common.MAX_LIMIT
        and search._default_limit({"default_limit": "junk"}) == common.DEFAULT_LIMIT
        and search._default_limit({}) == common.DEFAULT_LIMIT,
    )


def case_response_paging() -> bool:
    ok = (
        common.response_next_page({"nextPageToken": "tok"}) == "tok"
        and common.response_next_page({}) is None
        and common.response_issues({"issues": [{"key": "A-1"}, "junk"]}) == [{"key": "A-1"}]
    )
    return check("response paging/issue extraction", ok)


def case_issue_key_validation() -> bool:
    ok = common.validate_issue_key(" ABC-123 ") == "ABC-123"
    for bad in ("ABC-123/comment", "ABC-123?x=1", "../secret", "ABC", ""):
        try:
            common.validate_issue_key(bad)
            ok = False
        except common.JiraHelperError:
            pass
    args = _parse(["issue", "ABC-123/../x"])
    try:
        search.command_issue(args)
        ok = False
    except common.JiraHelperError as exc:
        ok = ok and "이슈 키 형식" in str(exc)
    return check("issue key validated before any request", ok)


def case_project_key_validation() -> bool:
    ok = common.validate_project_key("ABC") == "ABC"
    for bad in ("ABC/statuses", "A B", ""):
        try:
            common.validate_project_key(bad)
            ok = False
        except common.JiraHelperError:
            pass
    return check("project key rejects path-breaking values", ok)


def case_invalid_tz() -> bool:
    try:
        common.format_timestamp("2026-07-14T10:03:21.000+0900", "Not/AZone")
        return check("invalid --tz raises JiraHelperError", False)
    except common.JiraHelperError as exc:
        return check("invalid --tz raises JiraHelperError", "타임존" in str(exc))


def case_mask_secret_no_leak() -> bool:
    masked = common.mask_secret("SECRETTOKEN12345")
    return check(
        "mask_secret leaks no token characters",
        "SECR" not in masked and "2345" not in masked and masked == "***(len=16)",
        masked,
    )


def case_rate_limit_retry_without_header() -> bool:
    profile = {"site": "x.atlassian.net", "email": "a@example.com", "api_token": "t"}
    calls: list[int] = []

    def fake_curl(**kwargs):
        calls.append(1)
        if len(calls) == 1:
            return 429, "", "{}"
        return 200, "", '{"ok": true}'

    real_curl, real_sleep = common.run_curl, common.time.sleep
    common.run_curl, common.time.sleep = fake_curl, lambda _s: None
    try:
        data = common.jira_request(profile, "/rest/api/3/test")
    finally:
        common.run_curl, common.time.sleep = real_curl, real_sleep
    return check(
        "429 without Retry-After retries once with fixed sleep",
        data == {"ok": True} and len(calls) == 2,
    )


def case_missing_config_error() -> bool:
    with tempfile.TemporaryDirectory(prefix="jira-helper-test-") as tmp:
        os.environ["JIRA_HELPER_CONFIG_DIR"] = str(Path(tmp) / "none")
        try:
            common.load_profile()
            ok = False
        except common.JiraHelperError as exc:
            ok = "Missing config file" in str(exc)
        finally:
            os.environ.pop("JIRA_HELPER_CONFIG_DIR", None)
    return check("missing config raises a clear setup signal", ok)


def main() -> int:
    cases = [
        case_normalize_site,
        case_secure_write_permissions,
        case_memory_file_created_securely,
        case_sensitive_sanitizing,
        case_jql_quote_escapes,
        case_jql_time_value,
        case_jql_in_clause,
        case_combine_jql,
        case_adf_to_text,
        case_due_label,
        case_format_issue,
        case_format_issue_unassigned,
        case_mine_jql,
        case_due_defaults,
        case_worked_conflicting_args,
        case_limit_validation,
        case_default_limit_capped,
        case_response_paging,
        case_issue_key_validation,
        case_project_key_validation,
        case_invalid_tz,
        case_mask_secret_no_leak,
        case_rate_limit_retry_without_header,
        case_missing_config_error,
    ]
    results = [case() for case in cases]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
