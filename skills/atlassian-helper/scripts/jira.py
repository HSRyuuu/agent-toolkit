#!/usr/bin/env python3
"""Jira issue read + write. Modify/delete is restricted to issues I authored."""

from __future__ import annotations

import argparse
from typing import Any

from atlassian_common import (
    COUNT_PATH,
    DEFAULT_FIELDS,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    SEARCH_PATH,
    UPLOAD_MAX_TIME_SECONDS,
    AtlassianHelperError,
    adf_summary,
    add_profile_arg,
    api_request,
    assert_owner,
    combine_jql,
    confirm_destructive,
    file_form,
    format_issue,
    format_issues,
    format_timestamp,
    human_size,
    jql_in_clause,
    jql_quote,
    jql_time_value,
    load_profile,
    my_account_id,
    prepare_upload,
    print_response,
    read_body,
    response_issues,
    response_next_page,
    run_main,
    site_url,
    text_to_adf,
    truncate_text,
    validate_id,
    validate_issue_key,
    validate_project_key,
)


def _default_limit(profile: dict[str, Any]) -> int:
    value = profile.get("default_limit", DEFAULT_LIMIT)
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(1, min(limit, MAX_LIMIT))


def _resolve_limit(args: argparse.Namespace, profile: dict[str, Any]) -> int:
    limit = args.limit if args.limit is not None else _default_limit(profile)
    if limit < 1 or limit > MAX_LIMIT:
        raise AtlassianHelperError(f"--limit은 1부터 {MAX_LIMIT} 사이여야 합니다.")
    return limit


def _filter_clauses(args: argparse.Namespace) -> list[str]:
    clauses: list[str] = []
    if getattr(args, "project", None):
        clauses.append(jql_in_clause("project", args.project))
    if getattr(args, "status", None):
        clauses.append(jql_in_clause("status", args.status))
    if getattr(args, "type", None):
        clauses.append(jql_in_clause("issuetype", args.type))
    if getattr(args, "label", None):
        clauses.append(jql_in_clause("labels", args.label))
    if getattr(args, "assignee", None):
        clauses.append(f"assignee = {jql_quote(args.assignee)}")
    if getattr(args, "unresolved", False):
        clauses.append("resolution = EMPTY")
    extra = getattr(args, "jql_and", None)
    if extra:
        clauses.append(f"({extra})")
    return clauses


def _run_jql(args: argparse.Namespace, jql: str) -> int:
    _, profile = load_profile(args.profile)
    limit = _resolve_limit(args, profile)
    query: dict[str, Any] = {
        "jql": jql,
        "maxResults": limit,
        "fields": ",".join(DEFAULT_FIELDS),
    }
    next_page = getattr(args, "next_page", None)
    if next_page:
        query["nextPageToken"] = next_page
    response = api_request(profile, SEARCH_PATH, query=query)
    if args.raw:
        return print_response(response)
    print(f"# jql: {jql}")
    issues = response_issues(response)
    if issues:
        print()
        print(format_issues(issues, tz_name=args.tz))
    else:
        print("(no issues)")
    token = response_next_page(response)
    if token:
        print(f"\n(more results available; rerun with --next-page {token})")
    return 0


def command_search(args: argparse.Namespace) -> int:
    jql = " ".join(args.jql or []).strip()
    if not jql:
        raise AtlassianHelperError("JQL이 필요합니다. 예: search 'assignee = currentUser()'")
    return _run_jql(args, jql)


def command_mine(args: argparse.Namespace) -> int:
    clauses = ["assignee = currentUser()"]
    if args.updated_from:
        clauses.append(f"updated >= {jql_time_value(args.updated_from)}")
    if args.updated_to:
        clauses.append(f"updated <= {jql_time_value(args.updated_to)}")
    if args.created_from:
        clauses.append(f"created >= {jql_time_value(args.created_from)}")
    if args.created_to:
        clauses.append(f"created <= {jql_time_value(args.created_to)}")
    clauses.extend(_filter_clauses(args))
    return _run_jql(args, combine_jql(clauses, order_by=args.order))


def command_worked(args: argparse.Namespace) -> int:
    """Issues I touched in a period (past assignee included, sorted by updated)."""
    if args.from_time and args.days is not None:
        raise AtlassianHelperError("--from과 --days는 함께 쓸 수 없습니다. 하나만 지정하세요.")
    if args.days is not None and args.days < 1:
        raise AtlassianHelperError("--days는 1 이상이어야 합니다.")
    from_value = args.from_time or f"-{args.days if args.days is not None else 14}d"
    clauses = [
        "assignee WAS currentUser()",
        f"updated >= {jql_time_value(from_value)}",
    ]
    if args.to_time:
        clauses.append(f"updated <= {jql_time_value(args.to_time)}")
    clauses.extend(_filter_clauses(args))
    return _run_jql(args, combine_jql(clauses, order_by=args.order))


def command_due(args: argparse.Namespace) -> int:
    """Unresolved issues due within N days (overdue included), soonest first."""
    if args.within < 0:
        raise AtlassianHelperError("--within은 0 이상이어야 합니다.")
    clauses = [f'due <= {args.within}d', "due IS NOT EMPTY"]
    if not args.include_done:
        clauses.append("resolution = EMPTY")
    if not args.anyone and not getattr(args, "assignee", None):
        clauses.append("assignee = currentUser()")
    clauses.extend(_filter_clauses(args))
    return _run_jql(args, combine_jql(clauses, order_by=args.order))


def command_text(args: argparse.Namespace) -> int:
    keyword = " ".join(args.keyword or []).strip()
    if not keyword:
        raise AtlassianHelperError("검색어가 필요합니다. 예: text \"결제 오류\"")
    clauses = [f"text ~ {jql_quote(keyword)}"]
    if args.mine:
        clauses.append("assignee = currentUser()")
    clauses.extend(_filter_clauses(args))
    return _run_jql(args, combine_jql(clauses, order_by=args.order))


def command_count(args: argparse.Namespace) -> int:
    jql = " ".join(args.jql or []).strip()
    if not jql:
        raise AtlassianHelperError("JQL이 필요합니다. 예: count 'project = ABC AND status = Done'")
    _, profile = load_profile(args.profile)
    response = api_request(profile, COUNT_PATH, http_method="POST", payload={"jql": jql})
    if args.raw:
        return print_response(response)
    count = response.get("count") if isinstance(response, dict) else None
    print(count if count is not None else response)
    return 0


ISSUE_DETAIL_FIELDS = DEFAULT_FIELDS + ["description", "parent", "components", "fixVersions"]


def command_issue(args: argparse.Namespace) -> int:
    key = validate_issue_key(args.key)
    _, profile = load_profile(args.profile)
    response = api_request(
        profile,
        f"/rest/api/3/issue/{key}",
        query={"fields": ",".join(ISSUE_DETAIL_FIELDS)},
    )
    if args.raw:
        return print_response(response)
    fields = response.get("fields") if isinstance(response, dict) else {}
    fields = fields if isinstance(fields, dict) else {}
    print(format_issue(response, tz_name=args.tz))
    reporter = fields.get("reporter")
    reporter_name = reporter.get("displayName") if isinstance(reporter, dict) else "-"
    parent = fields.get("parent")
    parent_key = parent.get("key") if isinstance(parent, dict) else "-"
    created = format_timestamp(fields.get("created"), args.tz)
    print(f"  reporter={reporter_name} created={created} parent={parent_key}")
    description = fields.get("description")
    if description:
        print("\n## description")
        print(adf_summary(description, limit=args.description_limit))
    if args.comments:
        comments = api_request(
            profile,
            f"/rest/api/3/issue/{key}/comment",
            query={"maxResults": args.comments, "orderBy": "-created"},
        )
        items = comments.get("comments") if isinstance(comments, dict) else []
        items = items if isinstance(items, list) else []
        print(f"\n## comments (최신 {len(items)}건)")
        for comment in items:
            if not isinstance(comment, dict):
                continue
            author = comment.get("author")
            author_name = author.get("displayName") if isinstance(author, dict) else "-"
            created = format_timestamp(comment.get("created"), args.tz)
            body = truncate_text(adf_summary(comment.get("body"), limit=400), 400)
            print(f"\n[id={comment.get('id')}] [{created}] {author_name}")
            print(body)
    return 0


def command_projects(args: argparse.Namespace) -> int:
    _, profile = load_profile(args.profile)
    response = api_request(
        profile,
        "/rest/api/3/project/search",
        query={"query": args.query, "maxResults": 50},
    )
    if args.raw:
        return print_response(response)
    values = response.get("values") if isinstance(response, dict) else []
    values = values if isinstance(values, list) else []
    for project in values:
        if isinstance(project, dict):
            print(f"{project.get('key')}  {project.get('name')}")
    if not values:
        print("(no projects)")
    return 0


def command_statuses(args: argparse.Namespace) -> int:
    project = validate_project_key(args.project)
    _, profile = load_profile(args.profile)
    response = api_request(profile, f"/rest/api/3/project/{project}/statuses")
    if args.raw:
        return print_response(response)
    if not isinstance(response, list):
        raise AtlassianHelperError(f"예상하지 못한 응답: {response}")
    for issue_type in response:
        if not isinstance(issue_type, dict):
            continue
        statuses = issue_type.get("statuses")
        names = []
        if isinstance(statuses, list):
            for status in statuses:
                if isinstance(status, dict):
                    category = status.get("statusCategory")
                    category_key = category.get("key") if isinstance(category, dict) else "-"
                    names.append(f"{status.get('name')}({category_key})")
        print(f"{issue_type.get('name')}: {', '.join(names)}")
    return 0


# --- Write ---------------------------------------------------------------


def _issue_people(profile: dict[str, Any], key: str) -> dict[str, str]:
    """이슈의 작성자(creator, 없으면 reporter)·담당자·제목."""
    response = api_request(
        profile,
        f"/rest/api/3/issue/{key}",
        query={"fields": "creator,reporter,assignee,summary"},
    )
    fields = response.get("fields") if isinstance(response, dict) else {}
    fields = fields if isinstance(fields, dict) else {}
    author = fields.get("creator") or fields.get("reporter")
    author = author if isinstance(author, dict) else {}
    assignee = fields.get("assignee")
    assignee = assignee if isinstance(assignee, dict) else {}
    return {
        "owner_id": str(author.get("accountId") or ""),
        "owner_name": str(author.get("displayName") or ""),
        "assignee_id": str(assignee.get("accountId") or ""),
        "assignee_name": str(assignee.get("displayName") or ""),
        "summary": str(fields.get("summary") or ""),
    }


def _assert_issue_owner(
    profile: dict[str, Any], key: str, *, allow_assignee: bool = False
) -> None:
    """작성자 게이트. `allow_assignee` 면 담당자 == 본인도 통과한다."""
    people = _issue_people(profile, key)
    assert_owner(
        profile,
        people["owner_id"],
        people["owner_name"],
        f"이슈 {key}",
        assignee_id=people["assignee_id"] if allow_assignee else None,
        assignee_name=people["assignee_name"],
    )


def _comment_author(profile: dict[str, Any], key: str, comment_id: str) -> tuple[str, str]:
    response = api_request(profile, f"/rest/api/3/issue/{key}/comment/{comment_id}")
    author = response.get("author") if isinstance(response, dict) else {}
    author = author if isinstance(author, dict) else {}
    return str(author.get("accountId") or ""), str(author.get("displayName") or "")


def _issue_url(profile: dict[str, Any], key: str) -> str:
    return f"{site_url(profile)}/browse/{key}"


def command_create(args: argparse.Namespace) -> int:
    project = validate_project_key(args.project)
    summary = (args.summary or "").strip()
    if not summary:
        raise AtlassianHelperError("--summary는 필수입니다.")
    _, profile = load_profile(args.profile)
    fields: dict[str, Any] = {
        "project": {"key": project},
        "issuetype": {"name": args.type},
        "summary": summary,
    }
    if args.description is not None or args.description_file is not None:
        body = read_body(args.description, args.description_file, label="설명")
        fields["description"] = text_to_adf(body)
    if args.assignee_me:
        fields["assignee"] = {"accountId": my_account_id(profile)}
    elif args.assignee:
        fields["assignee"] = {"accountId": args.assignee}
    if args.label:
        fields["labels"] = args.label
    if args.duedate:
        fields["duedate"] = args.duedate
    if args.priority:
        fields["priority"] = {"name": args.priority}
    if args.parent:
        fields["parent"] = {"key": validate_issue_key(args.parent)}
    response = api_request(
        profile, "/rest/api/3/issue", http_method="POST", payload={"fields": fields}
    )
    if args.raw:
        return print_response(response)
    key = str(response.get("key") or "") if isinstance(response, dict) else ""
    print(f"created {key}  {_issue_url(profile, key)}")
    return 0


def command_comment(args: argparse.Namespace) -> int:
    key = validate_issue_key(args.key)
    _, profile = load_profile(args.profile)
    body = read_body(args.body, args.body_file, label="코멘트")
    if not body.strip():
        raise AtlassianHelperError("코멘트 본문이 비어 있습니다.")
    response = api_request(
        profile,
        f"/rest/api/3/issue/{key}/comment",
        http_method="POST",
        payload={"body": text_to_adf(body)},
    )
    if args.raw:
        return print_response(response)
    comment_id = response.get("id") if isinstance(response, dict) else "-"
    print(f"commented on {key} (id={comment_id})  {_issue_url(profile, key)}")
    return 0


def command_attach(args: argparse.Namespace) -> int:
    key = validate_issue_key(args.key)
    path, filename = prepare_upload(args.file, args.name)
    _, profile = load_profile(args.profile)
    response = api_request(
        profile,
        f"/rest/api/3/issue/{key}/attachments",
        http_method="POST",
        form=file_form(path, filename),
        max_time=UPLOAD_MAX_TIME_SECONDS,
    )
    if args.raw:
        return print_response(response)
    uploaded = response[0] if isinstance(response, list) and response else {}
    uploaded = uploaded if isinstance(uploaded, dict) else {}
    print(
        f"attached {uploaded.get('filename') or filename} "
        f"(id={uploaded.get('id') or '-'}, {human_size(uploaded.get('size'))}) to {key}"
        f"  {_issue_url(profile, key)}"
    )
    return 0


def command_edit(args: argparse.Namespace) -> int:
    key = validate_issue_key(args.key)
    fields: dict[str, Any] = {}
    if args.summary:
        fields["summary"] = args.summary
    if args.description is not None or args.description_file is not None:
        fields["description"] = text_to_adf(
            read_body(args.description, args.description_file, label="설명")
        )
    if args.duedate:
        fields["duedate"] = args.duedate
    if args.priority:
        fields["priority"] = {"name": args.priority}
    if args.label:
        fields["labels"] = args.label
    if not fields:
        raise AtlassianHelperError("수정할 필드가 없습니다 (--summary/--description/--duedate/...).")
    _, profile = load_profile(args.profile)
    _assert_issue_owner(profile, key, allow_assignee=True)
    api_request(
        profile, f"/rest/api/3/issue/{key}", http_method="PUT", payload={"fields": fields}
    )
    print(f"updated {key} ({', '.join(sorted(fields))})  {_issue_url(profile, key)}")
    return 0


def command_transitions(args: argparse.Namespace) -> int:
    key = validate_issue_key(args.key)
    _, profile = load_profile(args.profile)
    response = api_request(profile, f"/rest/api/3/issue/{key}/transitions")
    if args.raw:
        return print_response(response)
    transitions = response.get("transitions") if isinstance(response, dict) else []
    transitions = transitions if isinstance(transitions, list) else []
    for transition in transitions:
        if isinstance(transition, dict):
            target = transition.get("to")
            target_name = target.get("name") if isinstance(target, dict) else "-"
            print(f"{transition.get('id')}  {transition.get('name')} -> {target_name}")
    if not transitions:
        print("(no transitions available)")
    return 0


def command_transition(args: argparse.Namespace) -> int:
    key = validate_issue_key(args.key)
    _, profile = load_profile(args.profile)
    _assert_issue_owner(profile, key, allow_assignee=True)
    response = api_request(profile, f"/rest/api/3/issue/{key}/transitions")
    transitions = response.get("transitions") if isinstance(response, dict) else []
    transitions = transitions if isinstance(transitions, list) else []
    wanted = (args.to or "").strip().lower()
    match = None
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        target = transition.get("to")
        target_name = str(target.get("name") or "") if isinstance(target, dict) else ""
        if wanted in (
            str(transition.get("id") or "").lower(),
            str(transition.get("name") or "").lower(),
            target_name.lower(),
        ):
            match = transition
            break
    if match is None:
        available = ", ".join(
            str(t.get("name")) for t in transitions if isinstance(t, dict)
        )
        raise AtlassianHelperError(
            f"'{args.to}' 전환을 찾을 수 없습니다. 가능한 전환: {available or '(없음)'}"
        )
    api_request(
        profile,
        f"/rest/api/3/issue/{key}/transitions",
        http_method="POST",
        payload={"transition": {"id": str(match.get("id"))}},
    )
    print(f"transitioned {key} -> {match.get('name')}  {_issue_url(profile, key)}")
    return 0


def command_delete(args: argparse.Namespace) -> int:
    key = validate_issue_key(args.key)
    confirm_destructive(args.yes, f"이슈 {key}")
    _, profile = load_profile(args.profile)
    # 삭제는 되돌릴 수 없다 — 담당자가 아니라 작성자만 통과시킨다.
    summary = _issue_people(profile, key)["summary"]
    _assert_issue_owner(profile, key)
    api_request(
        profile,
        f"/rest/api/3/issue/{key}",
        http_method="DELETE",
        query={"deleteSubtasks": "true" if args.delete_subtasks else "false"},
    )
    print(f"deleted {key} ({truncate_text(summary, 80)})")
    return 0


def command_comment_edit(args: argparse.Namespace) -> int:
    key = validate_issue_key(args.key)
    comment_id = validate_id(args.id, "코멘트 ID")
    _, profile = load_profile(args.profile)
    body = read_body(args.body, args.body_file, label="코멘트")
    account_id, display_name = _comment_author(profile, key, comment_id)
    assert_owner(profile, account_id, display_name, f"{key} 코멘트 {comment_id}")
    api_request(
        profile,
        f"/rest/api/3/issue/{key}/comment/{comment_id}",
        http_method="PUT",
        payload={"body": text_to_adf(body)},
    )
    print(f"updated comment {comment_id} on {key}")
    return 0


def command_comment_delete(args: argparse.Namespace) -> int:
    key = validate_issue_key(args.key)
    comment_id = validate_id(args.id, "코멘트 ID")
    confirm_destructive(args.yes, f"{key} 코멘트 {comment_id}")
    _, profile = load_profile(args.profile)
    account_id, display_name = _comment_author(profile, key, comment_id)
    assert_owner(profile, account_id, display_name, f"{key} 코멘트 {comment_id}")
    api_request(
        profile, f"/rest/api/3/issue/{key}/comment/{comment_id}", http_method="DELETE"
    )
    print(f"deleted comment {comment_id} on {key}")
    return 0


def add_output_args(parser: argparse.ArgumentParser) -> None:
    add_profile_arg(parser)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--next-page", help="nextPageToken from a previous truncated search")
    parser.add_argument("--tz", default="Asia/Seoul")
    parser.add_argument("--raw", action="store_true")


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", action="append", help="project key; can repeat")
    parser.add_argument("--status", action="append", help="status name; can repeat")
    parser.add_argument("--type", action="append", help="issue type name; can repeat")
    parser.add_argument("--label", action="append", help="label; can repeat")
    parser.add_argument("--assignee", help="assignee (accountId 또는 email)")
    parser.add_argument("--unresolved", action="store_true", help="resolution = EMPTY 추가")
    parser.add_argument("--and", dest="jql_and", help="추가 JQL 조건 (AND로 결합)")
    parser.add_argument("--order", default="updated DESC", help='ORDER BY 절 (default "updated DESC")')


def add_body_args(parser: argparse.ArgumentParser, flag: str = "--body") -> None:
    parser.add_argument(flag, help="본문 텍스트 (빈 줄=문단, '- '=목록, '# '=제목)")
    parser.add_argument(f"{flag}-file", help="본문 파일 경로 ('-'는 stdin)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jira issue read/write")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search issues with raw JQL")
    add_output_args(search)
    search.add_argument("jql", nargs="*", help="raw JQL query")
    search.set_defaults(func=command_search)

    mine = subparsers.add_parser("mine", help="My issues (assignee = currentUser())")
    add_output_args(mine)
    add_filter_args(mine)
    mine.add_argument("--updated-from", help='예: -7d, "2026-07-01", startOfWeek()')
    mine.add_argument("--updated-to")
    mine.add_argument("--created-from")
    mine.add_argument("--created-to")
    mine.set_defaults(func=command_mine)

    worked = subparsers.add_parser(
        "worked", help="Issues I worked on in a period (assignee WAS currentUser())"
    )
    add_output_args(worked)
    add_filter_args(worked)
    worked.add_argument("--days", type=int, help="lookback days (default 14; --from과 배타)")
    worked.add_argument("--from", dest="from_time", help='예: -14d, "2026-07-01", startOfMonth()')
    worked.add_argument("--to", dest="to_time")
    worked.set_defaults(func=command_worked)

    due = subparsers.add_parser("due", help="Issues due soon (기한 임박, 연체 포함)")
    add_output_args(due)
    add_filter_args(due)
    due.add_argument("--within", type=int, default=7, help="days ahead (default 7)")
    due.add_argument("--anyone", action="store_true", help="내 티켓 제한 해제")
    due.add_argument("--include-done", action="store_true", help="해결된 이슈도 포함")
    due.set_defaults(func=command_due, order="due ASC")

    text = subparsers.add_parser("text", help="Full-text search (summary/description/comments)")
    add_output_args(text)
    add_filter_args(text)
    text.add_argument("keyword", nargs="*", help="검색어 (한 구절로 합쳐서 매칭)")
    text.add_argument("--mine", action="store_true", help="assignee = currentUser() 추가")
    text.set_defaults(func=command_text)

    count = subparsers.add_parser("count", help="Approximate issue count for a JQL")
    add_profile_arg(count)
    count.add_argument("jql", nargs="*", help="raw JQL query")
    count.add_argument("--raw", action="store_true")
    count.set_defaults(func=command_count)

    issue = subparsers.add_parser("issue", help="Issue detail (+ optional recent comments)")
    add_profile_arg(issue)
    issue.add_argument("key", help="예: ABC-123")
    issue.add_argument("--comments", type=int, default=0, help="최근 코멘트 N건 표시")
    issue.add_argument("--description-limit", type=int, default=800)
    issue.add_argument("--tz", default="Asia/Seoul")
    issue.add_argument("--raw", action="store_true")
    issue.set_defaults(func=command_issue)

    projects = subparsers.add_parser("projects", help="List visible projects")
    add_profile_arg(projects)
    projects.add_argument("--query", help="이름/키 부분 일치 필터")
    projects.add_argument("--raw", action="store_true")
    projects.set_defaults(func=command_projects)

    statuses = subparsers.add_parser("statuses", help="Statuses per issue type in a project")
    add_profile_arg(statuses)
    statuses.add_argument("--project", required=True, help="project key")
    statuses.add_argument("--raw", action="store_true")
    statuses.set_defaults(func=command_statuses)

    create = subparsers.add_parser("create", help="Create an issue (안전 작업)")
    add_profile_arg(create)
    create.add_argument("--project", required=True, help="project key")
    create.add_argument("--type", default="Task", help='issue type name (default "Task")')
    create.add_argument("--summary", required=True)
    add_body_args(create, "--description")
    create.add_argument("--assignee-me", action="store_true", help="나에게 배정")
    create.add_argument("--assignee", help="accountId")
    create.add_argument("--label", action="append")
    create.add_argument("--duedate", help="YYYY-MM-DD")
    create.add_argument("--priority")
    create.add_argument("--parent", help="상위 이슈 키 (예: ABC-100)")
    create.add_argument("--raw", action="store_true")
    create.set_defaults(func=command_create)

    comment = subparsers.add_parser("comment", help="Add a comment (안전 작업)")
    add_profile_arg(comment)
    comment.add_argument("key")
    add_body_args(comment)
    comment.add_argument("--raw", action="store_true")
    comment.set_defaults(func=command_comment)

    attach = subparsers.add_parser("attach", help="Attach a file/image to an issue (안전 작업)")
    add_profile_arg(attach)
    attach.add_argument("key")
    attach.add_argument("--file", required=True, help="업로드할 로컬 파일 경로")
    attach.add_argument("--name", help="첨부 파일명 (기본: 원본 파일명)")
    attach.add_argument("--raw", action="store_true")
    attach.set_defaults(func=command_attach)

    edit = subparsers.add_parser("edit", help="Edit an issue I created (작성자 확인)")
    add_profile_arg(edit)
    edit.add_argument("key")
    edit.add_argument("--summary")
    add_body_args(edit, "--description")
    edit.add_argument("--duedate", help="YYYY-MM-DD")
    edit.add_argument("--priority")
    edit.add_argument("--label", action="append", help="라벨 전체를 이 값들로 교체")
    edit.set_defaults(func=command_edit)

    transitions = subparsers.add_parser("transitions", help="List available transitions")
    add_profile_arg(transitions)
    transitions.add_argument("key")
    transitions.add_argument("--raw", action="store_true")
    transitions.set_defaults(func=command_transitions)

    transition = subparsers.add_parser(
        "transition", help="Move an issue I created to another status (작성자 확인)"
    )
    add_profile_arg(transition)
    transition.add_argument("key")
    transition.add_argument("--to", required=True, help="전환 이름/도착 상태 이름/전환 id")
    transition.set_defaults(func=command_transition)

    delete = subparsers.add_parser("delete", help="Delete an issue I created (작성자 확인 + --yes)")
    add_profile_arg(delete)
    delete.add_argument("key")
    delete.add_argument("--yes", action="store_true", help="삭제 확인 (필수)")
    delete.add_argument("--delete-subtasks", action="store_true")
    delete.set_defaults(func=command_delete)

    comment_edit = subparsers.add_parser(
        "comment-edit", help="Edit my own comment (작성자 확인)"
    )
    add_profile_arg(comment_edit)
    comment_edit.add_argument("key")
    comment_edit.add_argument("--id", required=True, help="코멘트 id (issue --comments 출력 참조)")
    add_body_args(comment_edit)
    comment_edit.set_defaults(func=command_comment_edit)

    comment_delete = subparsers.add_parser(
        "comment-delete", help="Delete my own comment (작성자 확인 + --yes)"
    )
    add_profile_arg(comment_delete)
    comment_delete.add_argument("key")
    comment_delete.add_argument("--id", required=True)
    comment_delete.add_argument("--yes", action="store_true", help="삭제 확인 (필수)")
    comment_delete.set_defaults(func=command_comment_delete)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
