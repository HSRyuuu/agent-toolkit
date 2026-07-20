#!/usr/bin/env python3
"""postman-helper read commands: workspaces, collections, endpoint search, request detail."""

from __future__ import annotations

import argparse

from postman_common import (
    DEFAULT_LIMIT,
    PostmanHelperError,
    add_profile_arg,
    add_source_args,
    format_endpoint_line,
    format_request_detail,
    iter_requests,
    load_profile,
    match_request,
    postman_request,
    resolve_source,
    run_main,
    url_raw,
)


def command_workspaces(args: argparse.Namespace) -> int:
    _name, profile = load_profile(args.profile)
    data = postman_request(profile, "/workspaces")
    workspaces = data.get("workspaces") if isinstance(data, dict) else None
    if not workspaces:
        print("(워크스페이스 없음)")
        return 0
    for ws in workspaces:
        if isinstance(ws, dict):
            print(f"{ws.get('id')}  {ws.get('name')}  ({ws.get('type', '-')})")
    return 0


def command_collections(args: argparse.Namespace) -> int:
    _name, profile = load_profile(args.profile)
    query = {"workspace": args.workspace} if args.workspace else None
    data = postman_request(profile, "/collections", query=query)
    collections = data.get("collections") if isinstance(data, dict) else None
    if not collections:
        print("(컬렉션 없음)")
        return 0
    for col in collections:
        if isinstance(col, dict):
            print(f"{col.get('uid')}  {col.get('name')}")
    return 0


def command_endpoints(args: argparse.Namespace) -> int:
    collection = resolve_source(args)
    limit = args.limit
    method = args.method.upper() if args.method else None
    shown = 0
    total = 0
    for entry in iter_requests(collection):
        if method and entry["method"] != method:
            continue
        if args.query and not match_request(entry, args.query):
            continue
        total += 1
        if shown < limit:
            print(format_endpoint_line(entry))
            shown += 1
    if total == 0:
        print("(일치하는 엔드포인트 없음)")
    elif total > shown:
        print(f"\n... {total - shown}건 더 있음 (--limit {total} 로 전체 표시)")
    return 0


def command_request(args: argparse.Namespace) -> int:
    collection = resolve_source(args)
    matches = [
        e for e in iter_requests(collection)
        if match_request(e, args.query)
    ]
    if not matches:
        raise PostmanHelperError(f"'{args.query}'에 일치하는 요청이 없습니다.")
    if len(matches) > 1 and not args.first:
        print(f"'{args.query}'에 {len(matches)}건 일치. 더 좁히거나 --first 로 첫 건 선택:")
        for e in matches[:20]:
            print(format_endpoint_line(e))
        return 0
    print(format_request_detail(matches[0]))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="postman-helper reads")
    sub = parser.add_subparsers(dest="command", required=True)

    ws = sub.add_parser("workspaces", help="List Postman workspaces (cloud)")
    add_profile_arg(ws)
    ws.set_defaults(func=command_workspaces)

    cols = sub.add_parser("collections", help="List collections in a workspace (cloud)")
    add_profile_arg(cols)
    cols.add_argument("--workspace", help="workspace id (omit for all)")
    cols.set_defaults(func=command_collections)

    eps = sub.add_parser("endpoints", help="List/search endpoints in a collection")
    add_profile_arg(eps)
    add_source_args(eps)
    eps.add_argument("--query", help="filter by name/path/method/url substring")
    eps.add_argument("--method", help="filter by HTTP method")
    eps.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    eps.set_defaults(func=command_endpoints)

    req = sub.add_parser("request", help="Show one request's params/headers/body")
    add_profile_arg(req)
    add_source_args(req)
    req.add_argument("query", help="name/path substring identifying the request")
    req.add_argument("--first", action="store_true", help="pick first match when ambiguous")
    req.set_defaults(func=command_request)
    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
