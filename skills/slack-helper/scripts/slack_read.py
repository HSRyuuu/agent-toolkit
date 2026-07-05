#!/usr/bin/env python3
"""Read Slack users, channels, history, and threads."""

from __future__ import annotations

import argparse

from slack_common import (
    SlackHelperError,
    add_workspace_arg,
    day_bounds,
    format_channels,
    format_history,
    format_users,
    print_compact_or_raw,
    resolve_channel,
    run_main,
    slack_method,
    token_for,
)


def _ensure_ok(response: dict, operation: str) -> None:
    if response.get("ok") is True:
        return
    error = response.get("_slack_error") or response.get("error") or response
    if error == "not_in_channel":
        raise SlackHelperError(
            f"{operation} 접근 권한이 없습니다(not_in_channel). Bot이 참여한 공개 채널만 직접 읽을 수 있습니다. "
            "필요하면 slack_search.py search 결과의 permalink로 대체 확인하세요."
        )
    raise SlackHelperError(f"{operation} failed: {error}")


def command_users(args: argparse.Namespace) -> int:
    response = slack_method(
        "users.list",
        token=token_for(args),
        payload={"limit": args.limit},
        http_method="GET",
    )
    _ensure_ok(response, "users.list")
    return print_compact_or_raw(response, format_users, raw=args.raw)


def command_channels(args: argparse.Namespace) -> int:
    response = slack_method(
        "conversations.list",
        token=token_for(args),
        payload={
            "limit": args.limit,
            "types": args.types,
            "exclude_archived": "true" if args.exclude_archived else "false",
        },
        http_method="GET",
    )
    _ensure_ok(response, "conversations.list")
    return print_compact_or_raw(response, format_channels, raw=args.raw)


def command_channel_history(args: argparse.Namespace) -> int:
    channel_id = resolve_channel(args.channel)
    payload: dict = {"channel": channel_id, "limit": args.limit}
    if getattr(args, "on", None):
        oldest, latest = day_bounds(args.on)
        payload.update({"oldest": oldest, "latest": latest, "inclusive": "true"})
    response = slack_method(
        "conversations.history",
        token=token_for(args),
        payload=payload,
        http_method="GET",
    )
    _ensure_ok(response, "conversations.history")
    return print_compact_or_raw(
        response,
        lambda payload: format_history(payload, channel_id),
        raw=args.raw,
    )


def command_thread(args: argparse.Namespace) -> int:
    channel_id = resolve_channel(args.channel)
    response = slack_method(
        "conversations.replies",
        token=token_for(args),
        payload={"channel": channel_id, "ts": args.ts, "limit": args.limit},
        http_method="GET",
    )
    _ensure_ok(response, "conversations.replies")
    return print_compact_or_raw(
        response,
        lambda payload: format_history(payload, channel_id),
        raw=args.raw,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slack 읽기 명령(users/channels/history/thread)",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="도움말 출력")
    parser._positionals.title = "명령"
    parser._optionals.title = "옵션"
    subparsers = parser.add_subparsers(dest="command", required=True)

    users = subparsers.add_parser("users", help="Slack users.list 호출")
    add_workspace_arg(users)
    users.add_argument("--limit", type=int, default=20)
    users.add_argument("--raw", action="store_true", help="compact 대신 원본 JSON 출력")
    users.set_defaults(func=command_users)

    channels = subparsers.add_parser("channels", help="Slack conversations.list 호출")
    add_workspace_arg(channels)
    channels.add_argument("--limit", type=int, default=20)
    channels.add_argument(
        "--types",
        default="public_channel",
        help="쉼표로 구분한 Slack conversation types",
    )
    channels.add_argument("--include-archived", dest="exclude_archived", action="store_false", help="보관된 채널도 포함")
    channels.add_argument("--raw", action="store_true", help="compact 대신 원본 JSON 출력")
    channels.set_defaults(exclude_archived=True, func=command_channels)

    history = subparsers.add_parser("channel-history", help="Slack conversations.history 호출")
    add_workspace_arg(history)
    history.add_argument("--channel", required=True, help="채널 ID 또는 context.json/channel-info.json 별칭")
    history.add_argument("--limit", type=int, default=20)
    history.add_argument("--on", help="특정 일자(YYYY-MM-DD)의 메시지만 조회 (로컬 타임존 자정 기준)")
    history.add_argument("--raw", action="store_true", help="compact 대신 원본 JSON 출력")
    history.set_defaults(func=command_channel_history)

    thread = subparsers.add_parser("thread", help="특정 Slack thread만 on-demand 조회")
    add_workspace_arg(thread)
    thread.add_argument("--channel", required=True, help="채널 ID 또는 context.json/channel-info.json 별칭")
    thread.add_argument("--ts", required=True, help="thread_ts 또는 원 메시지 ts")
    thread.add_argument("--limit", type=int, default=50)
    thread.add_argument("--raw", action="store_true", help="compact 대신 원본 JSON 출력")
    thread.set_defaults(func=command_thread)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
