#!/usr/bin/env python3
"""Post Slack messages to a channel or into a thread (as the authenticated user)."""

from __future__ import annotations

import argparse

from slack_common import (
    SlackHelperError,
    add_workspace_arg,
    parse_permalink,
    resolve_channel,
    run_main,
    slack_method,
    user_token_for,
)

# 전송은 항상 사용자 토큰(chat:write)으로 한다 — 본인 이름으로 게시.
WRITE_CHANNEL_TYPES = "public_channel,private_channel"


def _post(token: str, channel_id: str, text: str, thread_ts: str | None) -> dict:
    payload = {"channel": channel_id, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    response = slack_method("chat.postMessage", token=token, payload=payload)
    if response.get("ok") is not True:
        error = response.get("_slack_error") or response.get("error") or response
        raise SlackHelperError(f"chat.postMessage failed: {error}")
    return response


def _permalink(token: str, channel_id: str, ts: str) -> str | None:
    try:
        response = slack_method(
            "chat.getPermalink",
            token=token,
            payload={"channel": channel_id, "message_ts": ts},
            http_method="GET",
        )
    except SlackHelperError:
        return None
    return response.get("permalink") if response.get("ok") is True else None


def _report(token: str, response: dict) -> int:
    channel_id = response.get("channel", "")
    ts = response.get("ts", "")
    link = _permalink(token, channel_id, ts) if channel_id and ts else None
    print(f"전송 완료: channel={channel_id} ts={ts}")
    if link:
        print(f"링크: {link}")
    return 0


def command_post(args: argparse.Namespace) -> int:
    token = user_token_for(args)
    channel_id = resolve_channel(args.channel, token, types=WRITE_CHANNEL_TYPES)
    response = _post(token, channel_id, args.text, None)
    return _report(token, response)


def command_reply(args: argparse.Namespace) -> int:
    permalink = getattr(args, "permalink", None)
    if permalink:
        if args.channel or args.ts:
            raise SlackHelperError("--permalink는 --channel/--ts와 함께 쓸 수 없습니다.")
        args.channel, args.ts = parse_permalink(permalink)
    elif not args.channel or not args.ts:
        raise SlackHelperError(
            "--channel과 --ts를 함께 주거나, 스레드 원 메시지 링크를 --permalink로 넘겨 주세요."
        )
    token = user_token_for(args)
    channel_id = resolve_channel(args.channel, token, types=WRITE_CHANNEL_TYPES)
    response = _post(token, channel_id, args.text, args.ts)
    return _report(token, response)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slack 쓰기 명령(post/reply)",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="도움말 출력")
    parser._positionals.title = "명령"
    parser._optionals.title = "옵션"
    subparsers = parser.add_subparsers(dest="command", required=True)

    post = subparsers.add_parser("post", help="채널에 새 메시지 게시")
    add_workspace_arg(post)
    post.add_argument("--channel", required=True, help="채널 ID 또는 채널 이름 (이름은 conversations.list로 ID를 찾음)")
    post.add_argument("--text", required=True, help="보낼 메시지 본문")
    post.set_defaults(func=command_post)

    reply = subparsers.add_parser("reply", help="스레드 안에 답글 게시")
    add_workspace_arg(reply)
    reply.add_argument("--channel", help="채널 ID 또는 채널 이름")
    reply.add_argument("--ts", help="스레드 원 메시지의 ts (또는 thread_ts)")
    reply.add_argument("--permalink", help="스레드 원 메시지 링크. --channel/--ts 대신 사용")
    reply.add_argument("--text", required=True, help="보낼 답글 본문")
    reply.set_defaults(func=command_reply, channel=None, ts=None)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
