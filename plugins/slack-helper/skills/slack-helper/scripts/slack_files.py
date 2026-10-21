#!/usr/bin/env python3
"""Slack 메시지의 파일을 조회·다운로드하고, 로컬 파일을 업로드한다 (User token)."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

from slack_common import (
    SlackHelperError,
    add_workspace_arg,
    config_dir,
    curl_config_quote,
    parse_permalink,
    resolve_channel,
    resolve_dm,
    run_main,
    slack_method,
    token_for,
    user_token_for,
)

DEFAULT_DEST = "~/Downloads/slack-helper"
CHANNEL_TYPES = "public_channel,private_channel"


def _curl(url: str, *, token: str | None = None, output: Path | None = None, upload: Path | None = None) -> tuple[int, str]:
    """바이너리 안전 curl. 토큰은 argv가 아니라 stdin 설정으로 넘긴다. (HTTP 상태, Content-Type)을 돌려준다."""
    lines = [f'url = "{curl_config_quote(url)}"']
    if token:
        lines.append(f'header = "Authorization: Bearer {curl_config_quote(token)}"')
    if upload:
        lines += ['request = "POST"', f'data-binary = "@{curl_config_quote(str(upload))}"']
    command = [
        "curl", "--silent", "--show-error", "--location",
        "--connect-timeout", "10", "--max-time", "600",
        "--output", str(output or os.devnull),
        "--write-out", "%{http_code} %{content_type}",
        "--config", "-",
    ]
    result = subprocess.run(
        command, input="\n".join(lines) + "\n", text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode != 0:
        raise SlackHelperError(result.stderr.strip() or "curl failed")
    status, _, content_type = result.stdout.strip().partition(" ")
    return int(status or 0), content_type


def _call(method: str, token: str, payload: dict, *, http_method: str = "GET", content_type: str = "json") -> dict:
    response = slack_method(method, token=token, payload=payload, http_method=http_method, content_type=content_type)
    if response.get("ok") is not True:
        raise SlackHelperError(f"{method} failed: {response.get('_slack_error') or response.get('error') or response}")
    return response


def human_size(size: object) -> str:
    value = float(size or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return "-"


def format_files(files: list[dict]) -> str:
    return "\n".join(
        f"{f.get('id')} | {f.get('name') or f.get('title') or '-'} | {human_size(f.get('size'))} | {f.get('mimetype') or '-'}"
        for f in files
    )


def _message_ref(args: argparse.Namespace) -> tuple[str, str, str]:
    """(채널, 메시지 ts, 스레드 부모 ts). 답글 permalink여도 그 메시지 자신의 파일을 찾는다."""
    if args.permalink:
        if args.channel or args.ts:
            raise SlackHelperError("--permalink는 --channel/--ts와 함께 쓸 수 없습니다.")
        channel, ts = parse_permalink(args.permalink, prefer_thread=False)
        return channel, ts, parse_permalink(args.permalink)[1]
    if not args.channel or not args.ts:
        raise SlackHelperError("--channel과 --ts를 함께 주거나, 메시지 링크를 --permalink로 넘겨 주세요.")
    return args.channel, args.ts, args.ts


def _message_files(args: argparse.Namespace, token: str) -> list[dict]:
    channel, ts, parent = _message_ref(args)
    channel_id = resolve_channel(channel, token, types=CHANNEL_TYPES)
    response = _call(
        "conversations.replies", token,
        {"channel": channel_id, "ts": parent, "oldest": ts, "latest": ts, "inclusive": "true", "limit": 10},
    )
    for message in response.get("messages", []):
        if isinstance(message, dict) and message.get("ts") == ts:
            files = [f for f in message.get("files", []) if isinstance(f, dict)]
            if not files:
                raise SlackHelperError("이 메시지에는 첨부 파일이 없습니다.")
            return files
    raise SlackHelperError("메시지를 찾지 못했습니다. 스레드 답글이면 답글 링크(--permalink)를 그대로 넘겨 주세요.")


def command_list(args: argparse.Namespace) -> int:
    print(format_files(_message_files(args, user_token_for(args))))
    return 0


def _unique_path(dest: Path, name: str) -> Path:
    safe = Path(name).name or "file"  # 경로 구분자 제거 — dest 밖으로 쓰지 못하게 한다.
    path = dest / safe
    count = 1
    while path.exists():
        path = dest / f"{Path(safe).stem} ({count}){Path(safe).suffix}"
        count += 1
    return path


def command_download(args: argparse.Namespace) -> int:
    token = user_token_for(args)
    has_message = bool(args.permalink or args.channel or args.ts)
    if args.file and has_message:
        raise SlackHelperError("--file은 --permalink/--channel/--ts와 함께 쓸 수 없습니다.")
    if not args.file and not has_message:
        raise SlackHelperError("--file F… 또는 파일이 달린 메시지(--permalink)를 지정해 주세요.")
    ids = args.file or [str(f["id"]) for f in _message_files(args, token)]
    dest = Path(args.dest).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    for file_id in ids:
        info = _call("files.info", token, {"file": file_id}).get("file") or {}
        url = info.get("url_private_download") or info.get("url_private")
        if not url:
            raise SlackHelperError(f"{file_id}: 다운로드 주소가 없습니다(삭제되었거나 접근 권한이 없는 파일).")
        target = _unique_path(dest, str(info.get("name") or file_id))
        with tempfile.NamedTemporaryFile(dir=dest, prefix=".slack-dl-", delete=False) as handle:
            partial = Path(handle.name)
        try:
            status, content_type = _curl(str(url), token=token, output=partial)
            # 권한이 없으면 Slack이 파일 대신 로그인 HTML 페이지를 200으로 돌려준다.
            if status != 200 or (content_type.startswith("text/html") and not str(info.get("mimetype", "")).startswith("text/html")):
                raise SlackHelperError(f"{file_id}: 다운로드 실패(HTTP {status}). files:read 권한과 파일 접근 권한을 확인해 주세요.")
            os.replace(partial, target)
        finally:
            partial.unlink(missing_ok=True)
        print(f"다운로드 완료: {target} ({human_size(target.stat().st_size)})")
    return 0


def _check_uploadable(path: Path) -> None:
    if not path.is_file():
        raise SlackHelperError(f"파일을 찾을 수 없습니다: {path}")
    if path.stat().st_size == 0:
        raise SlackHelperError(f"빈 파일은 올릴 수 없습니다: {path}")
    # 토큰이 들어 있는 설정 폴더는 실수로도 올라가면 안 된다.
    if config_dir().resolve() in path.resolve().parents:
        raise SlackHelperError("Slack 설정 폴더의 파일은 업로드할 수 없습니다.")


def _upload_target(args: argparse.Namespace, token: str) -> tuple[str, str | None]:
    if sum(map(bool, (args.channel, args.user, args.permalink))) != 1:
        raise SlackHelperError("--channel, --user, --permalink 중 하나만 지정해 주세요.")
    if args.ts and not args.channel:
        raise SlackHelperError("--ts는 --channel과 함께 써야 합니다. 스레드 링크는 --permalink로 넘겨 주세요.")
    if args.permalink:
        channel, ts = parse_permalink(args.permalink)
        return resolve_channel(channel, token, types=CHANNEL_TYPES), ts
    if args.user:
        return resolve_dm(args.user, bot_token=token_for(args), user_token=token, create=True), None
    return resolve_channel(args.channel, token, types=CHANNEL_TYPES), args.ts


def command_upload(args: argparse.Namespace) -> int:
    paths = [Path(p).expanduser() for p in args.file]
    for path in paths:
        _check_uploadable(path)
    if args.title and len(paths) > 1:
        raise SlackHelperError("--title은 파일이 하나일 때만 쓸 수 있습니다.")
    token = user_token_for(args)
    channel_id, thread_ts = _upload_target(args, token)
    uploaded = []
    for path in paths:
        slot = _call(
            "files.getUploadURLExternal", token,
            {"filename": path.name, "length": path.stat().st_size},
            http_method="POST", content_type="form",
        )
        status, _ = _curl(str(slot["upload_url"]), upload=path)
        if status != 200:
            raise SlackHelperError(f"{path.name}: 파일 전송 실패(HTTP {status}).")
        uploaded.append({"id": slot["file_id"], "title": args.title or path.name})
    payload: dict = {"files": uploaded, "channel_id": channel_id}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    if args.text:
        payload["initial_comment"] = args.text
    response = _call("files.completeUploadExternal", token, payload, http_method="POST")
    for entry in response.get("files", []):
        print(f"업로드 완료: {entry.get('name') or entry.get('title')} id={entry.get('id')} 링크: {entry.get('permalink', '-')}")
    return 0


def _add_message_source(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--channel", help="채널 ID 또는 이름")
    parser.add_argument("--ts", help="메시지 ts")
    parser.add_argument("--permalink", help="메시지 링크. --channel/--ts 대신 사용")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Slack 파일 명령(list/download/upload)", add_help=False)
    parser.add_argument("-h", "--help", action="help", help="도움말 출력")
    parser._positionals.title = "명령"
    parser._optionals.title = "옵션"
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_ = subparsers.add_parser("list", help="메시지에 달린 파일 목록 (files:read)")
    add_workspace_arg(list_)
    _add_message_source(list_)
    list_.set_defaults(func=command_list)

    download = subparsers.add_parser("download", help="파일 다운로드 (files:read). 메시지의 파일 전부 또는 --file ID")
    add_workspace_arg(download)
    _add_message_source(download)
    download.add_argument("--file", action="append", help="파일 ID(F…). 여러 번 지정 가능")
    download.add_argument("--dest", default=DEFAULT_DEST, help=f"저장 폴더 (기본 {DEFAULT_DEST})")
    download.set_defaults(func=command_download)

    upload = subparsers.add_parser("upload", help="로컬 파일 업로드 (files:write, 본인 이름)")
    add_workspace_arg(upload)
    upload.add_argument("--file", action="append", required=True, help="올릴 로컬 파일 경로. 여러 번 지정 가능")
    upload.add_argument("--channel", help="올릴 채널 ID 또는 이름")
    upload.add_argument("--ts", help="--channel과 함께, 스레드 원 메시지 ts")
    upload.add_argument("--user", help="1:1 DM 상대 (U… ID, @핸들, 표시 이름)")
    upload.add_argument("--permalink", help="스레드 원 메시지 링크. 그 스레드에 올린다")
    upload.add_argument("--text", help="파일과 함께 보낼 메시지")
    upload.add_argument("--title", help="Slack에 표시할 파일 제목 (파일 하나일 때)")
    upload.set_defaults(func=command_upload)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
