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
    format_jsonl,
    format_users,
    parse_permalink,
    print_compact_or_raw,
    range_bounds,
    resolve_channel,
    run_main,
    slack_method,
    token_for,
    update_users_cache_from_members,
    user_token_for,
    users_for_messages,
    validate_output_flags,
)


USER_FALLBACK_ERRORS = {"not_in_channel", "no_permission", "channel_not_found", "missing_scope"}
USER_CHANNEL_TYPES = "public_channel,private_channel"


def _slack_error(response: dict) -> object:
    return response.get("_slack_error") or response.get("error") or response


def _ensure_ok(response: dict, operation: str) -> None:
    if response.get("ok") is True:
        return
    error = _slack_error(response)
    if error == "not_in_channel":
        raise SlackHelperError(
            f"{operation} 접근 권한이 없습니다(not_in_channel). Bot과 User token 모두 직접 읽지 못했습니다. "
            "Slack App의 User Token Scopes에 channels:history 또는 groups:history가 있는지 확인해 주세요. "
            "필요하면 slack_search.py search 결과의 permalink로 대체 확인하세요."
        )
    raise SlackHelperError(f"{operation} failed: {error}")


def _user_token_or_error(args: argparse.Namespace, operation: str) -> str:
    try:
        return user_token_for(args)
    except SlackHelperError as exc:
        raise SlackHelperError(
            f"{operation}를 Bot token으로 직접 읽지 못했고 User token fallback도 사용할 수 없습니다. {exc}"
        ) from exc


def _resolve_channel_for_read(args: argparse.Namespace, bot_token: str) -> tuple[str, str | None]:
    try:
        return resolve_channel(args.channel, bot_token), None
    except SlackHelperError as bot_error:
        user_token = _user_token_or_error(args, "conversations.list")
        try:
            return resolve_channel(args.channel, user_token, types=USER_CHANNEL_TYPES), user_token
        except SlackHelperError as user_error:
            raise SlackHelperError(
                f"Bot token과 User token 모두 '{args.channel}' 채널을 찾지 못했습니다. "
                f"Bot 오류: {bot_error} / User 오류: {user_error}"
            ) from user_error


def _call_conversation_read(
    args: argparse.Namespace,
    operation: str,
    *,
    bot_token: str,
    user_token: str | None,
    payload: dict,
) -> dict:
    if user_token:
        response = slack_method(operation, token=user_token, payload=payload, http_method="GET")
        _ensure_ok(response, operation)
        return response

    response = slack_method(operation, token=bot_token, payload=payload, http_method="GET")
    if response.get("ok") is True:
        return response

    if _slack_error(response) not in USER_FALLBACK_ERRORS:
        _ensure_ok(response, operation)

    fallback_token = _user_token_or_error(args, operation)
    fallback = slack_method(operation, token=fallback_token, payload=payload, http_method="GET")
    _ensure_ok(fallback, operation)
    return fallback


def _print_messages(
    args: argparse.Namespace,
    response: dict,
    *,
    channel_id: str,
    enrich_token: str,
) -> int:
    if args.raw:
        return print_compact_or_raw(response, format_history, raw=True)
    messages = response.get("messages", [])
    users = users_for_messages(messages, enrich_token)
    if getattr(args, "jsonl", False):
        text = format_jsonl(messages, channel=channel_id, users=users)
    else:
        text = format_history(response, channel_id, users=users)
    if text:
        print(text)
    return 0


def command_users(args: argparse.Namespace) -> int:
    response = slack_method(
        "users.list",
        token=token_for(args),
        payload={"limit": args.limit},
        http_method="GET",
    )
    _ensure_ok(response, "users.list")
    update_users_cache_from_members(response.get("members"))
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
    validate_output_flags(args)
    on = getattr(args, "on", None)
    after = getattr(args, "after", None)
    before = getattr(args, "before", None)
    tz_name = getattr(args, "tz", None)
    if on and (after or before):
        raise SlackHelperError("--on은 --after/--before와 함께 쓸 수 없습니다.")
    token = token_for(args)
    channel_id, user_token = _resolve_channel_for_read(args, token)
    payload: dict = {"channel": channel_id, "limit": args.limit}
    if on:
        oldest, latest = day_bounds(on, tz_name)
        payload.update({"oldest": oldest, "latest": latest, "inclusive": "true"})
    elif after or before:
        oldest, latest = range_bounds(after, before, tz_name)
        if oldest:
            payload["oldest"] = oldest
        if latest:
            payload["latest"] = latest
        payload["inclusive"] = "true"
    response = _call_conversation_read(
        args,
        "conversations.history",
        bot_token=token,
        user_token=user_token,
        payload=payload,
    )
    return _print_messages(args, response, channel_id=channel_id, enrich_token=token)


def command_thread(args: argparse.Namespace) -> int:
    validate_output_flags(args)
    permalink = getattr(args, "permalink", None)
    if permalink:
        if args.channel or args.ts:
            raise SlackHelperError("--permalink는 --channel/--ts와 함께 쓸 수 없습니다.")
        args.channel, args.ts = parse_permalink(permalink)
    elif not args.channel or not args.ts:
        raise SlackHelperError(
            "--channel과 --ts를 함께 주거나, 메시지 링크를 --permalink로 넘겨 주세요."
        )
    token = token_for(args)
    channel_id, user_token = _resolve_channel_for_read(args, token)
    response = _call_conversation_read(
        args,
        "conversations.replies",
        bot_token=token,
        user_token=user_token,
        payload={"channel": channel_id, "ts": args.ts, "limit": args.limit},
    )
    return _print_messages(args, response, channel_id=channel_id, enrich_token=token)


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
    history.add_argument("--channel", required=True, help="채널 ID 또는 공개 채널 이름 (이름은 conversations.list로 ID를 찾음)")
    history.add_argument("--limit", type=int, default=20)
    history.add_argument("--on", help="특정 일자(YYYY-MM-DD)의 메시지만 조회. --after/--before와 함께 쓸 수 없음")
    history.add_argument("--after", help="이 일자(YYYY-MM-DD) 00:00부터 조회 (해당 일자 포함)")
    history.add_argument("--before", help="이 일자(YYYY-MM-DD) 자정 직전까지 조회 (해당 일자 포함)")
    history.add_argument("--tz", help="--on/--after/--before의 자정 기준 타임존 (예: Asia/Seoul). 기본은 로컬 타임존")
    history.add_argument("--jsonl", action="store_true", help="한 줄당 JSON 출력 — 임시 분석 스크립트용")
    history.add_argument("--raw", action="store_true", help="compact 대신 원본 JSON 출력")
    history.set_defaults(func=command_channel_history)

    thread = subparsers.add_parser("thread", help="특정 Slack thread만 on-demand 조회")
    add_workspace_arg(thread)
    thread.add_argument("--channel", help="채널 ID 또는 공개 채널 이름 (이름은 conversations.list로 ID를 찾음)")
    thread.add_argument("--ts", help="thread_ts 또는 원 메시지 ts")
    thread.add_argument("--permalink", help="검색 결과의 메시지 링크. --channel/--ts 대신 사용")
    thread.add_argument("--limit", type=int, default=50)
    thread.add_argument("--jsonl", action="store_true", help="한 줄당 JSON 출력 — 임시 분석 스크립트용")
    thread.add_argument("--raw", action="store_true", help="compact 대신 원본 JSON 출력")
    thread.set_defaults(func=command_thread, channel=None, ts=None)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
