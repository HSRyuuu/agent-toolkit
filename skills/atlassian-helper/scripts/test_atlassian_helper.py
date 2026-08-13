#!/usr/bin/env python3
"""Tests for deterministic atlassian-helper behavior.

Run with: python3 test_atlassian_helper.py
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


common = load_module("atlassian_common")
jira = load_module("jira")
confluence = load_module("confluence")
setup = load_module("atlassian_setup")


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
    except common.AtlassianHelperError:
        pass
    return check("normalize_site accepts hosts/URLs and rejects garbage", ok)


def case_secure_write_permissions() -> bool:
    with tempfile.TemporaryDirectory(prefix="atlassian-helper-test-") as tmp:
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
    with tempfile.TemporaryDirectory(prefix="atlassian-helper-test-") as tmp:
        os.environ["ATLASSIAN_HELPER_CONFIG_DIR"] = tmp
        try:
            path = common.ensure_memory_file()
            file_mode = stat.S_IMODE(path.stat().st_mode)
            text = path.read_text(encoding="utf-8")
        finally:
            os.environ.pop("ATLASSIAN_HELPER_CONFIG_DIR", None)
    return check(
        "ensure_memory_file creates expected template",
        file_mode == 0o600 and "## 자주 쓰는 JQL" in text and "## 자주 쓰는 CQL" in text,
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


def case_text_to_adf_roundtrip() -> bool:
    doc = common.text_to_adf("# 제목\n\n첫 줄\n둘째 줄\n\n- 하나\n- 둘\n")
    types = [block.get("type") for block in doc["content"]]
    text = common.adf_to_text(doc)
    return check(
        "text_to_adf builds heading/paragraph/bulletList and round-trips",
        doc["type"] == "doc"
        and types == ["heading", "paragraph", "bulletList"]
        and "첫 줄\n둘째 줄" in text
        and "- 하나" in text
        and "- 둘" in text,
        f"{types} / {text!r}",
    )


def case_text_to_adf_empty() -> bool:
    doc = common.text_to_adf("")
    return check(
        "text_to_adf never emits an invalid empty doc",
        doc["content"] == [{"type": "paragraph"}],
        str(doc),
    )


def case_text_to_storage_escapes() -> bool:
    html_out = common.text_to_storage("# 제목\n\n<script>x</script> & y\n\n- 하나\n")
    return check(
        "text_to_storage escapes markup and builds blocks",
        "<h2>제목</h2>" in html_out
        and "&lt;script&gt;" in html_out
        and "<script>" not in html_out
        and "<ul><li><p>하나</p></li></ul>" in html_out,
        html_out,
    )


def case_storage_to_text() -> bool:
    text = common.storage_to_text(
        "<h2>제목</h2><p>본문 &amp; 설명<br/>둘째 줄</p><ul><li>하나</li><li>둘</li></ul>"
    )
    return check(
        "storage_to_text strips tags and unescapes entities",
        "제목" in text and "본문 & 설명" in text and "- 하나" in text and "<" not in text,
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
    return jira.build_parser().parse_args(argv)


def _parse_conf(argv: list[str]):
    return confluence.build_parser().parse_args(argv)


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
    clauses.extend(jira._filter_clauses(args))
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
        jira.command_worked(args)
        return check("worked rejects --days with --from", False)
    except common.AtlassianHelperError as exc:
        return check("worked rejects --days with --from", "함께 쓸 수 없습니다" in str(exc))


def case_limit_validation() -> bool:
    args = _parse(["search", "assignee = currentUser()", "--limit", "500"])
    try:
        jira._resolve_limit(args, {})
        return check("limit over 100 rejected", False)
    except common.AtlassianHelperError:
        return check("limit over 100 rejected", True)


def case_default_limit_capped() -> bool:
    return check(
        "profile default_limit is sanitized",
        jira._default_limit({"default_limit": 9999}) == common.MAX_LIMIT
        and jira._default_limit({"default_limit": "junk"}) == common.DEFAULT_LIMIT
        and jira._default_limit({}) == common.DEFAULT_LIMIT,
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
        except common.AtlassianHelperError:
            pass
    args = _parse(["issue", "ABC-123/../x"])
    try:
        jira.command_issue(args)
        ok = False
    except common.AtlassianHelperError as exc:
        ok = ok and "이슈 키 형식" in str(exc)
    return check("issue key validated before any request", ok)


def case_project_key_validation() -> bool:
    ok = common.validate_project_key("ABC") == "ABC"
    for bad in ("ABC/statuses", "A B", ""):
        try:
            common.validate_project_key(bad)
            ok = False
        except common.AtlassianHelperError:
            pass
    return check("project key rejects path-breaking values", ok)


def case_id_validation() -> bool:
    ok = common.validate_id(" 12345 ") == "12345"
    for bad in ("12/34", "../x", "abc", ""):
        try:
            common.validate_id(bad)
            ok = False
        except common.AtlassianHelperError:
            pass
    args = _parse_conf(["page", "123/../secret"])
    try:
        confluence.command_page(args)
        ok = False
    except common.AtlassianHelperError as exc:
        ok = ok and "페이지 ID" in str(exc)
    return check("numeric id validated before any request", ok)


def case_invalid_tz() -> bool:
    try:
        common.format_timestamp("2026-07-14T10:03:21.000+0900", "Not/AZone")
        return check("invalid --tz raises AtlassianHelperError", False)
    except common.AtlassianHelperError as exc:
        return check("invalid --tz raises AtlassianHelperError", "타임존" in str(exc))


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
        data = common.api_request(profile, "/rest/api/3/test")
    finally:
        common.run_curl, common.time.sleep = real_curl, real_sleep
    return check(
        "429 without Retry-After retries once with fixed sleep",
        data == {"ok": True} and len(calls) == 2,
    )


def case_missing_config_error() -> bool:
    with tempfile.TemporaryDirectory(prefix="atlassian-helper-test-") as tmp:
        os.environ["ATLASSIAN_HELPER_CONFIG_DIR"] = str(Path(tmp) / "none")
        try:
            common.load_profile()
            ok = False
        except common.AtlassianHelperError as exc:
            ok = "Missing config file" in str(exc)
        finally:
            os.environ.pop("ATLASSIAN_HELPER_CONFIG_DIR", None)
    return check("missing config raises a clear setup signal", ok)


# --- write-path guards ---------------------------------------------------

ME = {"site": "x.atlassian.net", "email": "a@example.com", "api_token": "t", "account_id": "me-1"}


def case_owner_guard_allows_self() -> bool:
    try:
        common.assert_owner(dict(ME), "me-1", "나", "이슈 ABC-1")
        return check("assert_owner allows my own item", True)
    except common.AtlassianHelperError as exc:
        return check("assert_owner allows my own item", False, str(exc))


def case_owner_guard_blocks_others() -> bool:
    try:
        common.assert_owner(dict(ME), "someone-else", "홍길동", "이슈 ABC-1")
        return check("assert_owner blocks other people's items", False)
    except common.AtlassianHelperError as exc:
        return check(
            "assert_owner blocks other people's items",
            "작성자가 본인이 아닙니다" in str(exc) and "홍길동" in str(exc),
            str(exc),
        )


def case_owner_guard_fails_closed() -> bool:
    """Unknown author must never be treated as mine."""
    calls: list[str] = []

    def fake_curl(**kwargs):
        calls.append(kwargs.get("url", ""))
        return 200, "", '{"accountId": "me-1"}'

    real_curl = common.run_curl
    common.run_curl = fake_curl
    try:
        common.assert_owner({"site": "x.atlassian.net", "email": "a@b.c", "api_token": "t"}, None, "", "페이지 1")
        ok = False
        detail = "no error raised"
    except common.AtlassianHelperError as exc:
        ok = "작성자를 확인할 수 없어" in str(exc)
        detail = str(exc)
    finally:
        common.run_curl = real_curl
    return check(
        "assert_owner fails closed on unknown author (no API call)",
        ok and not calls,
        detail,
    )


def case_delete_requires_yes() -> bool:
    ok = True
    for argv, needle in (
        (["delete", "ABC-1"], "이슈 ABC-1"),
        (["comment-delete", "ABC-1", "--id", "10"], "코멘트 10"),
    ):
        args = _parse(argv)
        try:
            args.func(args)
            ok = False
        except common.AtlassianHelperError as exc:
            ok = ok and "--yes" in str(exc) and needle in str(exc)
    args = _parse_conf(["delete", "123"])
    try:
        args.func(args)
        ok = False
    except common.AtlassianHelperError as exc:
        ok = ok and "--yes" in str(exc)
    return check("delete commands refuse to run without --yes", ok)


def case_edit_requires_a_field() -> bool:
    args = _parse(["edit", "ABC-1"])
    try:
        jira.command_edit(args)
        ok = False
    except common.AtlassianHelperError as exc:
        ok = "수정할 필드가 없습니다" in str(exc)
    conf_args = _parse_conf(["update", "123"])
    try:
        confluence.command_update(conf_args)
        ok = False
    except common.AtlassianHelperError as exc:
        ok = ok and "수정할 내용이 없습니다" in str(exc)
    return check("edit/update reject no-op calls before touching the API", ok)


def case_read_body_exactly_one() -> bool:
    ok = common.read_body("hi", None) == "hi"
    for text, path in ((None, None), ("hi", "/tmp/x")):
        try:
            common.read_body(text, path)
            ok = False
        except common.AtlassianHelperError:
            pass
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
        handle.write("from file")
        temp_path = handle.name
    try:
        ok = ok and common.read_body(None, temp_path) == "from file"
    finally:
        os.unlink(temp_path)
    return check("read_body requires exactly one of --body/--body-file", ok)


def _record_requests(module, responses: dict[str, object]):
    """Patch a command module's api_request/load_profile; record (method, path)."""
    calls: list[tuple[str, str]] = []

    def fake_request(profile, path, **kwargs):
        method = kwargs.get("http_method", "GET")
        calls.append((method, path))
        for prefix, response in responses.items():
            if path.startswith(prefix):
                return response
        return {}

    real_request, real_load = module.api_request, module.load_profile
    module.api_request = fake_request
    module.load_profile = lambda name=None: ("default", dict(ME))

    def restore():
        module.api_request, module.load_profile = real_request, real_load

    return calls, restore


def case_jira_edit_blocked_for_other_author() -> bool:
    """A foreign issue must fail before any PUT reaches Jira."""
    calls, restore = _record_requests(
        jira,
        {
            "/rest/api/3/issue/ABC-1": {
                "fields": {
                    "creator": {"accountId": "other-1", "displayName": "홍길동"},
                    "summary": "남의 티켓",
                }
            }
        },
    )
    args = _parse(["edit", "ABC-1", "--summary", "덮어쓰기 시도"])
    try:
        jira.command_edit(args)
        ok, detail = False, "no error raised"
    except common.AtlassianHelperError as exc:
        ok = "작성자가 본인이 아닙니다" in str(exc)
        detail = str(exc)
    finally:
        restore()
    methods = [method for method, _ in calls]
    return check(
        "jira edit on someone else's issue never issues a write",
        ok and "PUT" not in methods and "POST" not in methods,
        f"{detail} / calls={calls}",
    )


def case_confluence_delete_blocked_for_other_author() -> bool:
    calls, restore = _record_requests(
        confluence,
        {
            common.PAGES_PATH: {"id": "123", "title": "남의 문서", "authorId": "other-1"},
            "/wiki/rest/api/user": {"publicName": "홍길동"},
        },
    )
    args = _parse_conf(["delete", "123", "--yes"])
    try:
        confluence.command_delete(args)
        ok, detail = False, "no error raised"
    except common.AtlassianHelperError as exc:
        ok = "작성자가 본인이 아닙니다" in str(exc)
        detail = str(exc)
    finally:
        restore()
    methods = [method for method, _ in calls]
    return check(
        "confluence delete on someone else's page never issues a DELETE",
        ok and "DELETE" not in methods,
        f"{detail} / calls={calls}",
    )


def case_confluence_update_bumps_version_for_own_page() -> bool:
    calls, restore = _record_requests(
        confluence,
        {
            common.PAGES_PATH: {
                "id": "123",
                "title": "내 문서",
                "authorId": ME["account_id"],
                "version": {"number": 4},
                "body": {"storage": {"value": "<p>old</p>"}},
            }
        },
    )
    payloads: list[dict] = []
    real_request = confluence.api_request

    def capture(profile, path, **kwargs):
        if kwargs.get("http_method") == "PUT":
            payloads.append(kwargs.get("payload") or {})
        return real_request(profile, path, **kwargs)

    confluence.api_request = capture
    args = _parse_conf(["update", "123", "--body", "새 본문"])
    try:
        confluence.command_update(args)
        ok = True
    except common.AtlassianHelperError as exc:
        ok, payloads = False, [{"error": str(exc)}]
    finally:
        restore()
    payload = payloads[0] if payloads else {}
    return check(
        "confluence update on my own page bumps version and converts the body",
        ok
        and payload.get("version", {}).get("number") == 5
        and payload.get("body", {}).get("value") == "<p>새 본문</p>",
        str(payload),
    )


def case_confluence_search_cql() -> bool:
    args = _parse_conf(["search", "결제", "오류", "--space", "DEV", "--mine"])
    captured: dict[str, object] = {}

    def fake_request(profile, path, **kwargs):
        captured.update(kwargs.get("query") or {})
        return {"results": []}

    real_request, real_load = confluence.api_request, confluence.load_profile
    confluence.api_request = fake_request
    confluence.load_profile = lambda name=None: ("default", dict(ME))
    try:
        confluence.command_search(args)
    finally:
        confluence.api_request, confluence.load_profile = real_request, real_load
    cql = str(captured.get("cql"))
    return check(
        "confluence search builds a quoted CQL query",
        cql == 'type = page AND text ~ "결제 오류" AND space = "DEV" '
        "AND creator = currentUser() ORDER BY lastmodified DESC",
        cql,
    )


def case_confluence_search_needs_a_filter() -> bool:
    args = _parse_conf(["search"])
    try:
        confluence.command_search(args)
        return check("confluence search refuses an unbounded query", False)
    except common.AtlassianHelperError as exc:
        return check("confluence search refuses an unbounded query", "검색어" in str(exc))


def case_prepare_upload_validation() -> bool:
    with tempfile.TemporaryDirectory(prefix="atlassian-helper-test-") as tmp:
        good = Path(tmp) / "flow.png"
        good.write_bytes(b"\x89PNG\r\n")
        empty = Path(tmp) / "empty.png"
        empty.write_bytes(b"")
        path, name = common.prepare_upload(str(good))
        ok = path == good and name == "flow.png"
        _, renamed = common.prepare_upload(str(good), "diagram.png")
        ok = ok and renamed == "diagram.png"
        for bad_args in (
            (str(empty), None),
            (str(Path(tmp) / "missing.png"), None),
            (str(tmp), None),
            (str(good), "../escape.png"),
        ):
            try:
                common.prepare_upload(*bad_args)
                ok = False
            except common.AtlassianHelperError:
                pass
        form = common.file_form(good, "flow.png")
    return check(
        "prepare_upload accepts a real file and rejects empty/missing/dir/path-escape names",
        ok and form == [f'file=@"{good.resolve()}";filename="flow.png";type=image/png'],
        str(form),
    )


def case_repin_attachment_version() -> bool:
    body = (
        '<ac:image ac:width="900"><ri:attachment ri:filename="flow.png" '
        'ri:version-at-save="1" /></ac:image>'
        '<p><ri:attachment ri:filename="notes.md" ri:version-at-save="1" /></p>'
    )
    bumped, count = confluence._repin_attachment(body, "flow.png", 2)
    same, zero = confluence._repin_attachment(bumped, "flow.png", 2)
    return check(
        "_repin_attachment rewrites only the target filename and is idempotent",
        count == 1
        and 'ri:filename="flow.png" ri:version-at-save="2"' in bumped
        and 'ri:filename="notes.md" ri:version-at-save="1"' in bumped
        and zero == 0
        and same == bumped,
        f"count={count} zero={zero}",
    )


def case_attach_refuses_silent_overwrite() -> bool:
    calls, restore = _record_requests(
        confluence,
        {
            f"{common.CONTENT_PATH}/123/child/attachment": {
                "results": [{"id": "att9", "title": "flow.png", "version": {"number": 1}}]
            }
        },
    )
    with tempfile.TemporaryDirectory(prefix="atlassian-helper-test-") as tmp:
        target = Path(tmp) / "flow.png"
        target.write_bytes(b"\x89PNG\r\n")
        args = _parse_conf(["attach", "123", "--file", str(target)])
        try:
            confluence.command_attach(args)
            ok, detail = False, "no error raised"
        except common.AtlassianHelperError as exc:
            ok, detail = "--replace" in str(exc), str(exc)
        finally:
            restore()
    methods = [method for method, _ in calls]
    return check(
        "confluence attach refuses to overwrite a same-name attachment without --replace",
        ok and "POST" not in methods,
        f"{detail} / calls={calls}",
    )


def case_attach_replace_blocked_for_other_author() -> bool:
    calls, restore = _record_requests(
        confluence,
        {
            f"{common.CONTENT_PATH}/123/child/attachment": {
                "results": [{"id": "att9", "title": "flow.png", "version": {"number": 1}}]
            },
            common.PAGES_PATH: {"id": "123", "title": "남의 문서", "authorId": "other-1"},
            "/wiki/rest/api/user": {"publicName": "홍길동"},
        },
    )
    with tempfile.TemporaryDirectory(prefix="atlassian-helper-test-") as tmp:
        target = Path(tmp) / "flow.png"
        target.write_bytes(b"\x89PNG\r\n")
        args = _parse_conf(["attach", "123", "--file", str(target), "--replace"])
        try:
            confluence.command_attach(args)
            ok, detail = False, "no error raised"
        except common.AtlassianHelperError as exc:
            ok, detail = "작성자가 본인이 아닙니다" in str(exc), str(exc)
        finally:
            restore()
    methods = [method for method, _ in calls]
    return check(
        "confluence attach --replace on someone else's page never uploads",
        ok and "POST" not in methods and "PUT" not in methods,
        f"{detail} / calls={calls}",
    )


def case_upload_sets_xsrf_header() -> bool:
    captured: dict[str, object] = {}

    def fake_curl(**kwargs):
        captured.update(kwargs)
        return 200, "", "{}"

    real_curl = common.run_curl
    common.run_curl = fake_curl
    try:
        common.api_request(
            dict(ME), "/rest/api/3/issue/ABC-1/attachments", http_method="POST", form=["file=@x"]
        )
    finally:
        common.run_curl = real_curl
    headers = captured.get("headers") or {}
    return check(
        "multipart requests send X-Atlassian-Token: no-check and the form parts",
        headers.get("X-Atlassian-Token") == "no-check" and captured.get("form") == ["file=@x"],
        str(captured.get("form")),
    )


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
        case_text_to_adf_roundtrip,
        case_text_to_adf_empty,
        case_text_to_storage_escapes,
        case_storage_to_text,
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
        case_id_validation,
        case_invalid_tz,
        case_mask_secret_no_leak,
        case_rate_limit_retry_without_header,
        case_missing_config_error,
        case_owner_guard_allows_self,
        case_owner_guard_blocks_others,
        case_owner_guard_fails_closed,
        case_delete_requires_yes,
        case_edit_requires_a_field,
        case_read_body_exactly_one,
        case_jira_edit_blocked_for_other_author,
        case_confluence_delete_blocked_for_other_author,
        case_confluence_update_bumps_version_for_own_page,
        case_confluence_search_cql,
        case_confluence_search_needs_a_filter,
        case_prepare_upload_validation,
        case_repin_attachment_version,
        case_attach_refuses_silent_overwrite,
        case_attach_replace_blocked_for_other_author,
        case_upload_sets_xsrf_header,
    ]
    results = [case() for case in cases]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
