#!/usr/bin/env python3
"""Search Slack messages with token-efficient compact output."""

from __future__ import annotations

import argparse
import re
from datetime import date, timedelta
from typing import Any

from slack_common import (
    SlackHelperError,
    add_workspace_arg,
    format_search_results,
    load_context,
    load_workspace,
    load_workspace_identity,
    print_response,
    resolve_channel_name,
    run_main,
    slack_method,
    user_token_for,
)


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _quote_keyword(keyword: str) -> str:
    value = keyword.strip()
    if not value:
        return ""
    if re.search(r"\s", value):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _validate_date(value: str | None, option: str) -> str | None:
    if value is None:
        return None
    if not DATE_RE.match(value):
        raise SlackHelperError(f"{option}는 YYYY-MM-DD 형식이어야 합니다.")
    return value


def _to_me_user_id(args: argparse.Namespace) -> str | None:
    explicit = getattr(args, "user_id", None)
    if explicit:
        return str(explicit)
    context_me = load_context().get("me")
    if isinstance(context_me, dict) and context_me.get("user_id"):
        return str(context_me["user_id"])
    return None


def build_search_query(keywords: list[str], args: argparse.Namespace) -> list[str]:
    terms = [_quote_keyword(keyword) for keyword in keywords if keyword.strip()]
    if not terms:
        if getattr(args, "to_me", False) or getattr(args, "from_user", None):
            terms = [""]
        else:
            raise SlackHelperError("검색어가 비어 있습니다.")

    shared: list[str] = []
    if getattr(args, "from_user", None):
        shared.append(f"from:{args.from_user}")
    if getattr(args, "in_channel", None):
        shared.append(f"in:{resolve_channel_name(args.in_channel)}")
    if getattr(args, "to_me", False):
        user_id = _to_me_user_id(args)
        if not user_id:
            raise SlackHelperError("resolve-me로 내 ID를 먼저 저장하세요.")
        shared.append(f'"<@{user_id}>"')

    if getattr(args, "days", None) is not None and getattr(args, "after", None):
        raise SlackHelperError("--days와 --after는 동시에 사용할 수 없습니다.")
    after = _validate_date(getattr(args, "after", None), "--after")
    before = _validate_date(getattr(args, "before", None), "--before")
    on = _validate_date(getattr(args, "on", None), "--on")
    if after:
        shared.append(f"after:{after}")
    if before:
        shared.append(f"before:{before}")
    if on:
        shared.append(f"on:{on}")
    if getattr(args, "days", None) is not None:
        if args.days < 1:
            raise SlackHelperError("--days는 1 이상이어야 합니다.")
        shared.append(f"after:{(date.today() - timedelta(days=args.days)).isoformat()}")

    return [" ".join([term, *shared]).strip() for term in terms]


def _match_key(match: dict[str, Any]) -> tuple[str, str]:
    channel = match.get("channel")
    if isinstance(channel, dict):
        channel_id = str(channel.get("id") or channel.get("name") or "")
    else:
        channel_id = str(match.get("channel_id") or channel or "")
    return channel_id, str(match.get("ts") or "")


def merge_search_matches(responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for response in responses:
        messages = response.get("messages")
        matches = messages.get("matches", []) if isinstance(messages, dict) else []
        for match in matches:
            if not isinstance(match, dict):
                continue
            by_key.setdefault(_match_key(match), match)
    return sorted(
        by_key.values(),
        key=lambda item: float(str(item.get("ts") or "0").split(".", 1)[0] or 0),
        reverse=True,
    )


def _identity_user_id(args: argparse.Namespace) -> str | None:
    try:
        _, workspace = load_workspace(args.workspace)
    except SlackHelperError:
        return None
    identity = load_workspace_identity(workspace)
    if identity.get("user_id"):
        return str(identity["user_id"])
    return _to_me_user_id(args)


def command_search(args: argparse.Namespace) -> int:
    if args.count < 1 or args.count > 100:
        raise SlackHelperError("--count는 1부터 100 사이여야 합니다.")
    if args.page < 1 or args.page > 100:
        raise SlackHelperError("--page는 1부터 100 사이여야 합니다.")
    if args.to_me and not getattr(args, "user_id", None):
        args.user_id = _identity_user_id(args)

    queries = build_search_query(args.query, args)
    responses = []
    auth_value = user_token_for(args)
    for query in queries:
        payload = {
            "query": query,
            "count": args.count,
            "page": args.page,
            "sort": args.sort,
            "sort_dir": args.sort_dir,
            "highlight": "true" if args.highlight else "false",
        }
        response = slack_method(
            "search.messages",
            token=auth_value,
            payload=payload,
            http_method="GET",
        )
        if response.get("ok") is not True:
            raise SlackHelperError(f"search.messages failed: {response.get('error', response)}")
        responses.append(response)

    if args.raw:
        if len(responses) == 1:
            return print_response(responses[0])
        return print_response({"ok": True, "responses": responses})
    merged = merge_search_matches(responses)
    text = format_search_results({"ok": True, "messages": {"matches": merged}})
    if text:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slack 메시지 검색(search.messages)",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="도움말 출력")
    parser._positionals.title = "명령"
    parser._optionals.title = "옵션"
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Slack 메시지 검색")
    add_workspace_arg(search)
    search.add_argument("query", nargs="*", default=[], help="검색어. 여러 개면 키워드별로 검색 후 병합. --to-me 또는 --from을 쓰면 생략 가능")
    search.add_argument("--from", dest="from_user", help="Slack search from: modifier 값")
    search.add_argument("--in", dest="in_channel", help="채널명 또는 context.json 별칭")
    search.add_argument("--to-me", action="store_true", help="저장된 내 member ID 멘션 검색")
    search.add_argument("--after", help="YYYY-MM-DD")
    search.add_argument("--before", help="YYYY-MM-DD")
    search.add_argument("--on", help="YYYY-MM-DD")
    search.add_argument("--days", type=int, help="최근 N일 after: modifier")
    search.add_argument("--count", type=int, default=20, help="검색 결과 수, 최대 100")
    search.add_argument("--page", type=int, default=1, help="검색 결과 페이지, 최대 100")
    search.add_argument(
        "--sort",
        choices=("score", "timestamp"),
        default="timestamp",
        help="정렬 기준",
    )
    search.add_argument(
        "--sort-dir",
        choices=("asc", "desc"),
        default="desc",
        help="정렬 방향",
    )
    search.add_argument("--highlight", action="store_true", help="검색어 강조 표시 요청")
    search.add_argument("--raw", action="store_true", help="compact 대신 원본 JSON 출력")
    search.set_defaults(func=command_search, user_id=None)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
