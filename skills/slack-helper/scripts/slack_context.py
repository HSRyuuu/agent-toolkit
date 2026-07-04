#!/usr/bin/env python3
"""Manage slack-helper local context cache."""

from __future__ import annotations

import argparse
from typing import Any

from slack_common import (
    SlackHelperError,
    add_workspace_arg,
    load_context,
    print_response,
    run_main,
    save_context,
    slack_method,
    token_for,
    truncate_text,
)


def command_show(args: argparse.Namespace) -> int:
    context = load_context()
    me = context.get("me") if isinstance(context.get("me"), dict) else {}
    channels = context.get("channels") if isinstance(context.get("channels"), dict) else {}
    if me:
        print(f"me\t{me.get('identifier', '-')}\t{me.get('user_id', '-')}")
    else:
        print("me\t비어 있음")
    if not channels:
        print("channels\t비어 있음")
        return 0
    for alias, entry in sorted(channels.items()):
        if not isinstance(entry, dict):
            continue
        print(
            "\t".join(
                [
                    str(alias),
                    str(entry.get("id") or "-"),
                    str(entry.get("name") or "-"),
                    str(entry.get("summary") or "-"),
                ]
            )
        )
    return 0


def command_add_channel(args: argparse.Namespace) -> int:
    context = load_context()
    channels = context.setdefault("channels", {})
    if not isinstance(channels, dict):
        channels = {}
        context["channels"] = channels
    channels[args.alias] = {
        "id": args.id,
        "name": (args.name or args.alias).lstrip("#"),
        "summary": args.summary or "",
    }
    save_context(context)
    return print_response({"ok": True, "alias": args.alias, "context_path": "context.json"})


def command_remove_channel(args: argparse.Namespace) -> int:
    context = load_context()
    channels = context.setdefault("channels", {})
    if not isinstance(channels, dict) or args.alias not in channels:
        raise SlackHelperError(f"등록된 채널 별칭이 없습니다: {args.alias}")
    del channels[args.alias]
    save_context(context)
    return print_response({"ok": True, "removed": args.alias})


def _channel_text(channel: dict[str, Any]) -> str:
    for key in ("topic", "purpose"):
        value = channel.get(key)
        if isinstance(value, dict) and value.get("value"):
            return str(value["value"])
    return str(channel.get("name") or channel.get("id") or "")


def _draft_summary_from_history(channel: dict[str, Any], token: str, limit: int) -> str:
    channel_id = str(channel.get("id") or "")
    try:
        response = slack_method(
            "conversations.history",
            token=token,
            payload={"channel": channel_id, "limit": limit},
            http_method="GET",
        )
    except SlackHelperError:
        return truncate_text(_channel_text(channel), 80)
    if response.get("ok") is not True:
        return truncate_text(_channel_text(channel), 80)
    messages = response.get("messages", [])
    samples = []
    for message in messages:
        if isinstance(message, dict) and message.get("text"):
            samples.append(str(message["text"]))
    if not samples:
        return truncate_text(_channel_text(channel), 80)
    return truncate_text(" / ".join(samples), 80)


def command_draft_summaries(args: argparse.Namespace) -> int:
    auth_value = token_for(args)
    response = slack_method(
        "conversations.list",
        token=auth_value,
        payload={"limit": args.limit_channels, "types": "public_channel", "exclude_archived": "true"},
        http_method="GET",
    )
    if response.get("ok") is not True:
        raise SlackHelperError(f"conversations.list failed: {response.get('error', response)}")
    channels = response.get("channels", [])
    for channel in channels[: args.limit_channels]:
        if not isinstance(channel, dict):
            continue
        alias = str(channel.get("name") or channel.get("id") or "-").lstrip("#")
        summary = _draft_summary_from_history(channel, auth_value, args.messages_per_channel)
        print(
            "\t".join(
                [
                    alias,
                    str(channel.get("id") or "-"),
                    alias,
                    summary,
                ]
            )
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="slack-helper context.json 관리",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="도움말 출력")
    parser._positionals.title = "명령"
    parser._optionals.title = "옵션"
    subparsers = parser.add_subparsers(dest="command", required=True)

    show = subparsers.add_parser("show", help="저장된 내 식별자와 채널 summary 보기")
    show.set_defaults(func=command_show)

    add_channel = subparsers.add_parser("add-channel", help="context.json에 채널 별칭 추가/갱신")
    add_channel.add_argument("--alias", required=True, help="에이전트가 사용할 채널 별칭")
    add_channel.add_argument("--id", required=True, help="Slack channel ID, 예: C123...")
    add_channel.add_argument("--name", help="Slack 채널명(# 제외)")
    add_channel.add_argument("--summary", help="채널 1줄 요약")
    add_channel.set_defaults(func=command_add_channel)

    remove_channel = subparsers.add_parser("remove-channel", help="context.json에서 채널 별칭 제거")
    remove_channel.add_argument("--alias", required=True, help="제거할 채널 별칭")
    remove_channel.set_defaults(func=command_remove_channel)

    draft = subparsers.add_parser(
        "draft-summaries",
        help="채널 목록과 최근 메시지 일부로 summary 초안을 출력만 함(저장 안 함)",
    )
    add_workspace_arg(draft)
    draft.add_argument("--limit-channels", type=int, default=20, help="초안을 만들 최대 채널 수")
    draft.add_argument("--messages-per-channel", type=int, default=5, help="채널당 읽을 최근 메시지 수")
    draft.set_defaults(func=command_draft_summaries)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
