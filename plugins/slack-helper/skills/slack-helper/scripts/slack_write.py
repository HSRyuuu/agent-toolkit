#!/usr/bin/env python3
"""Post Slack messages or add emoji reactions (as the authenticated user)."""

from __future__ import annotations

import argparse

from slack_common import (
    SlackHelperError,
    add_workspace_arg,
    parse_permalink,
    resolve_channel,
    resolve_dm,
    run_main,
    slack_method,
    token_for,
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


def command_dm(args: argparse.Namespace) -> int:
    token = user_token_for(args)
    channel_id = resolve_dm(args.user, bot_token=token_for(args), user_token=token, create=True)
    return _report(token, _post(token, channel_id, args.text, None))


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


def command_react(args: argparse.Namespace) -> int:
    if args.permalink:
        if args.channel or args.ts:
            raise SlackHelperError("--permalink는 --channel/--ts와 함께 쓸 수 없습니다.")
        args.channel, args.ts = parse_permalink(args.permalink, prefer_thread=False)
    elif not args.channel or not args.ts:
        raise SlackHelperError("--channel과 --ts를 함께 주거나, 메시지 링크를 --permalink로 넘겨 주세요.")
    token = user_token_for(args)
    channel_id = resolve_channel(args.channel, token, types=WRITE_CHANNEL_TYPES)
    name = args.emoji.strip().strip(":")
    response = slack_method(
        "reactions.add",
        token=token,
        payload={"channel": channel_id, "timestamp": args.ts, "name": name},
    )
    if response.get("ok") is not True:
        error = response.get("_slack_error") or response.get("error") or response
        raise SlackHelperError(f"reactions.add failed: {error}")
    print(f"이모지 추가 완료: :{name}: channel={channel_id} ts={args.ts}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slack 쓰기 명령(post/dm/reply/react)",
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

    dm = subparsers.add_parser("dm", help="1:1 DM 보내기 (im:write, 대화가 없으면 새로 연다)")
    add_workspace_arg(dm)
    dm.add_argument("--user", required=True, help="DM 상대 (U… ID, @핸들, 표시 이름) 또는 DM 채널 ID(D…)")
    dm.add_argument("--text", required=True, help="보낼 메시지 본문")
    dm.set_defaults(func=command_dm)

    reply = subparsers.add_parser("reply", help="스레드 안에 답글 게시")
    add_workspace_arg(reply)
    reply.add_argument("--channel", help="채널 ID 또는 채널 이름")
    reply.add_argument("--ts", help="스레드 원 메시지의 ts (또는 thread_ts)")
    reply.add_argument("--permalink", help="스레드 원 메시지 링크. --channel/--ts 대신 사용")
    reply.add_argument("--text", required=True, help="보낼 답글 본문")
    reply.set_defaults(func=command_reply, channel=None, ts=None)

    react = subparsers.add_parser("react", help="메시지에 이모지 리액션 하나 추가")
    add_workspace_arg(react)
    react.add_argument("--channel", help="채널 ID 또는 채널 이름")
    react.add_argument("--ts", help="대상 메시지의 ts")
    react.add_argument("--permalink", help="대상 메시지 링크. --channel/--ts 대신 사용")
    react.add_argument("--emoji", required=True, help="이모지 이름 (예: thumbsup 또는 :thumbsup:)")
    react.set_defaults(func=command_react, channel=None, ts=None)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
