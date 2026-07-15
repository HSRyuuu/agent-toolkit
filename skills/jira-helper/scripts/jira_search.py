#!/usr/bin/env python3
"""Read-only Jira issue search with compact output."""

from __future__ import annotations

import argparse
from typing import Any

from jira_common import (
    COUNT_PATH,
    DEFAULT_FIELDS,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    SEARCH_PATH,
    JiraHelperError,
    adf_summary,
    add_profile_arg,
    combine_jql,
    due_label,
    format_issue,
    format_issues,
    format_timestamp,
    issue_assignee,
    issue_status,
    jira_request,
    jql_in_clause,
    jql_quote,
    jql_time_value,
    load_profile,
    print_response,
    response_issues,
    response_next_page,
    run_main,
    truncate_text,
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
        raise JiraHelperError(f"--limit은 1부터 {MAX_LIMIT} 사이여야 합니다.")
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
    response = jira_request(profile, SEARCH_PATH, query=query)
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
        raise JiraHelperError("JQL이 필요합니다. 예: search 'assignee = currentUser()'")
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
        raise JiraHelperError("--from과 --days는 함께 쓸 수 없습니다. 하나만 지정하세요.")
    if args.days is not None and args.days < 1:
        raise JiraHelperError("--days는 1 이상이어야 합니다.")
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
        raise JiraHelperError("--within은 0 이상이어야 합니다.")
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
        raise JiraHelperError("검색어가 필요합니다. 예: text \"결제 오류\"")
    clauses = [f"text ~ {jql_quote(keyword)}"]
    if args.mine:
        clauses.append("assignee = currentUser()")
    clauses.extend(_filter_clauses(args))
    return _run_jql(args, combine_jql(clauses, order_by=args.order))


def command_count(args: argparse.Namespace) -> int:
    jql = " ".join(args.jql or []).strip()
    if not jql:
        raise JiraHelperError("JQL이 필요합니다. 예: count 'project = ABC AND status = Done'")
    _, profile = load_profile(args.profile)
    response = jira_request(profile, COUNT_PATH, http_method="POST", payload={"jql": jql})
    if args.raw:
        return print_response(response)
    count = response.get("count") if isinstance(response, dict) else None
    print(count if count is not None else response)
    return 0


ISSUE_DETAIL_FIELDS = DEFAULT_FIELDS + ["description", "parent", "components", "fixVersions"]


def command_issue(args: argparse.Namespace) -> int:
    key = validate_issue_key(args.key)
    _, profile = load_profile(args.profile)
    response = jira_request(
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
        comments = jira_request(
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
            print(f"\n[{created}] {author_name}")
            print(body)
    return 0


def command_projects(args: argparse.Namespace) -> int:
    _, profile = load_profile(args.profile)
    response = jira_request(
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
    response = jira_request(profile, f"/rest/api/3/project/{project}/statuses")
    if args.raw:
        return print_response(response)
    if not isinstance(response, list):
        raise JiraHelperError(f"예상하지 못한 응답: {response}")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Jira issue search")
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

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
