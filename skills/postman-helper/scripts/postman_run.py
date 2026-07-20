#!/usr/bin/env python3
"""postman-helper guarded executor for saved requests.

Safety is enforced HERE, not in prose. Two independent gates:

1. Nothing is EVER transmitted without --send. The default is a preview.
   --send exists so that transmission only happens when the user explicitly
   asked to execute — the agent must not pass it otherwise.
2. Method/env gate: GET/HEAD/OPTIONS are safe, POST needs --confirm,
   PUT/PATCH/DELETE are blocked (even with --send --confirm). Safe methods
   against a non-local host also need --confirm.
"""

from __future__ import annotations

import argparse
import urllib.parse

from postman_common import (
    EXECUTABLE_BODY_MODES,
    PostmanHelperError,
    add_profile_arg,
    add_source_args,
    build_varmap,
    classify_env,
    classify_method,
    execution_gate,
    format_response_headers,
    iter_requests,
    match_request,
    redact_url,
    redact_value,
    resolve_source,
    resolve_vars,
    run_curl,
    run_main,
    truncate,
    url_raw,
)


def _resolve_headers(request: dict, varmap: dict[str, str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for h in request.get("header") or []:
        if isinstance(h, dict) and not h.get("disabled") and h.get("key"):
            headers[str(h["key"])] = resolve_vars(str(h.get("value", "")), varmap)
    return headers


def _resolve_body(request: dict, varmap: dict[str, str]) -> tuple[str | None, str | None]:
    """Return (body_string, content_type) or raise if the mode can't be replayed."""
    body = request.get("body")
    if not isinstance(body, dict) or not body.get("mode") or body["mode"] == "none":
        return None, None
    mode = body["mode"]
    if mode not in EXECUTABLE_BODY_MODES:
        raise PostmanHelperError(f"body 형식 '{mode}'는 자동 실행을 지원하지 않습니다.")
    if mode == "raw":
        lang = ((body.get("options") or {}).get("raw") or {}).get("language", "text")
        ctype = "application/json" if lang == "json" else "text/plain"
        return resolve_vars(str(body.get("raw") or ""), varmap), ctype
    # urlencoded
    pairs = [
        (str(it.get("key", "")), resolve_vars(str(it.get("value", "")), varmap))
        for it in body.get("urlencoded") or []
        if isinstance(it, dict) and not it.get("disabled")
    ]
    return urllib.parse.urlencode(pairs), "application/x-www-form-urlencoded"


def command_run(args: argparse.Namespace) -> int:
    collection = resolve_source(args)
    matches = [e for e in iter_requests(collection) if match_request(e, args.query)]
    if not matches:
        raise PostmanHelperError(f"'{args.query}'에 일치하는 요청이 없습니다.")
    if len(matches) > 1 and not args.first:
        raise PostmanHelperError(
            f"'{args.query}'에 {len(matches)}건 일치. 더 좁히거나 --first 를 쓰세요."
        )
    entry = matches[0]
    request = entry["request"]
    varmap = build_varmap(collection, args.var)

    method = entry["method"]
    resolved_url = resolve_vars(url_raw(entry["url"]), varmap)
    method_class = classify_method(method)
    env_class = classify_env(resolved_url)
    allowed, reason = execution_gate(method_class, env_class, args.confirm)

    print(f"{method} {redact_url(resolved_url)}")
    print(f"판정: method={method_class} env={env_class} → {'전송 가능' if allowed else '차단'}")
    print(f"사유: {reason}")

    if not allowed:
        return 0 if method_class == "blocked" else 2

    headers = _resolve_headers(request, varmap)
    body, ctype = _resolve_body(request, varmap)
    if not args.send:
        print("\n[미리보기] 전송하지 않았습니다:")
        for k, v in headers.items():
            print(f"  {k}: {redact_value(k, v)}")
        if body is not None:
            print(f"  body: {truncate(body, 300)}")
        print("\n전송하려면 --send 를 붙이세요 (사용자가 실행을 명시적으로 요청한 경우에만).")
        return 2

    status, elapsed, resp_headers, resp_body = run_curl(
        url=resolved_url, http_method=method, headers=headers, body=body, content_type=ctype
    )
    print(f"\nHTTP {status}  ({elapsed:.3f}s)")
    if 300 <= status < 400:
        print("(리다이렉트는 따라가지 않습니다 — Location 헤더를 확인하세요)")
    print(format_response_headers(resp_headers))
    print("\nbody:")
    print(truncate(resp_body, args.max_body))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="postman-helper guarded runner")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Execute a saved request (safety-gated)")
    add_profile_arg(run)
    add_source_args(run)
    run.add_argument("query", help="name/path substring identifying the request")
    run.add_argument("--first", action="store_true", help="pick first match when ambiguous")
    run.add_argument("--var", action="append", help="override variable: key=value (repeatable)")
    run.add_argument(
        "--send", action="store_true",
        help="actually transmit; without it run is always a no-send preview. "
             "Pass ONLY when the user explicitly asked to execute the request.",
    )
    run.add_argument("--confirm", action="store_true", help="user-approved execution for non-auto cases")
    run.add_argument("--max-body", type=int, default=2000, help="truncate response body")
    run.set_defaults(func=command_run)
    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
