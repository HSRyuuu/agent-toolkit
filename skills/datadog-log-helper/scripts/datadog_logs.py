#!/usr/bin/env python3
"""Search and aggregate Datadog logs with compact output."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Any

from datadog_common import (
    DEFAULT_FROM,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    DatadogHelperError,
    add_profile_arg,
    append_filter,
    collect_key_paths,
    datadog_request,
    extract_frames,
    format_log_events,
    load_profile,
    print_response,
    run_main,
)

SEARCH_PATH = "/api/v2/logs/events/search"
AGGREGATE_PATH = "/api/v2/logs/analytics/aggregate"


def _default_limit(profile: dict[str, Any]) -> int:
    value = profile.get("default_limit", DEFAULT_LIMIT)
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(1, min(limit, MAX_LIMIT))


def _base_query(args: argparse.Namespace) -> str:
    query = " ".join(args.query or []).strip()
    if not query:
        query = "*"
    query = append_filter(query, f"service:{args.service}" if args.service else None)
    query = append_filter(query, f"env:{args.env}" if args.env else None)
    query = append_filter(query, f"status:{args.status}" if args.status else None)
    query = append_filter(query, f"host:{args.host}" if args.host else None)
    query = append_filter(query, f"@trace_id:{args.trace_id}" if args.trace_id else None)
    query = append_filter(query, f"@version:{args.version}" if args.version else None)
    return query


RAW_LIMIT_GUARD = 5


def _validate_limit(limit: int, allow_wide: bool) -> None:
    if limit < 1 or limit > MAX_LIMIT:
        raise DatadogHelperError(f"--limit은 1부터 {MAX_LIMIT} 사이여야 합니다.")
    if limit > 500 and not allow_wide:
        raise DatadogHelperError("--limit 500 초과는 --allow-wide가 필요합니다.")


def _validate_raw(limit: int, allow_wide: bool) -> None:
    """Raw events are ~1k tokens each; block accidental context floods."""
    if limit > RAW_LIMIT_GUARD and not allow_wide:
        raise DatadogHelperError(
            f"--raw는 이벤트당 출력이 크므로 --limit {RAW_LIMIT_GUARD} 초과 시 "
            "--allow-wide가 필요합니다. 집계가 목적이면 count/agg를 쓰세요."
        )


def _time_filter(args: argparse.Namespace, profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "from": args.from_time or profile.get("default_from") or DEFAULT_FROM,
        "to": args.to_time,
        "query": _base_query(args),
    }


def _search_payload(
    args: argparse.Namespace,
    profile: dict[str, Any],
    *,
    force_sort: str | None = None,
    force_limit: int | None = None,
) -> dict[str, Any]:
    allow_wide = getattr(args, "allow_wide", False)
    if force_limit is not None:
        limit = force_limit
    else:
        limit = args.limit if args.limit is not None else _default_limit(profile)
        _validate_limit(limit, allow_wide)
    if getattr(args, "raw", False):
        _validate_raw(limit, allow_wide)
    filter_payload = _time_filter(args, profile)
    if args.index:
        filter_payload["indexes"] = args.index
    return {
        "filter": filter_payload,
        "page": {"limit": limit},
        "sort": force_sort or getattr(args, "sort", None) or "-timestamp",
    }


def _aggregate_payload(
    args: argparse.Namespace,
    profile: dict[str, Any],
    *,
    group_by: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    filter_payload = _time_filter(args, profile)
    if args.index:
        filter_payload["indexes"] = args.index
    payload: dict[str, Any] = {
        "compute": [{"aggregation": "count"}],
        "filter": filter_payload,
    }
    if group_by:
        payload["group_by"] = group_by
    return payload


def _buckets(response: dict[str, Any]) -> list[dict[str, Any]]:
    data = response.get("data")
    if not isinstance(data, dict):
        return []
    buckets = data.get("buckets")
    return buckets if isinstance(buckets, list) else []


def _bucket_count(bucket: dict[str, Any]) -> int:
    computes = bucket.get("computes")
    if isinstance(computes, dict):
        value = computes.get("c0")
        if isinstance(value, (int, float)):
            return int(value)
    return 0


def command_search(args: argparse.Namespace) -> int:
    _, profile = load_profile(args.profile)
    payload = _search_payload(args, profile)
    response = datadog_request(profile, SEARCH_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    text = format_log_events(response, tz_name=args.tz)
    if text:
        print(text)
    return 0


def command_errors(args: argparse.Namespace) -> int:
    args.status = args.status or "error"
    if args.minutes is not None:
        if args.minutes < 1:
            raise DatadogHelperError("--minutes는 1 이상이어야 합니다.")
        args.from_time = f"now-{args.minutes}m"
    return command_search(args)


def command_timeline(args: argparse.Namespace) -> int:
    args.sort = "timestamp"
    return command_search(args)


def command_count(args: argparse.Namespace) -> int:
    """Exact server-side count for a query. No event download, no sampling bias."""
    _, profile = load_profile(args.profile)
    payload = _aggregate_payload(args, profile)
    response = datadog_request(profile, AGGREGATE_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    total = sum(_bucket_count(bucket) for bucket in _buckets(response))
    print(total)
    return 0


def command_agg(args: argparse.Namespace) -> int:
    """Server-side group-by counts (top-N per facet). Replaces raw-download + Counter."""
    facets = args.by or []
    if not facets:
        raise DatadogHelperError("--by <facet>이 최소 1개 필요합니다. 예: --by @request_uri")
    if args.top < 1 or args.top > 100:
        raise DatadogHelperError("--top은 1부터 100 사이여야 합니다.")
    _, profile = load_profile(args.profile)
    group_by = [
        {
            "facet": facet,
            "limit": args.top,
            "sort": {"type": "measure", "aggregation": "count", "order": "desc"},
        }
        for facet in facets
    ]
    payload = _aggregate_payload(args, profile, group_by=group_by)
    response = datadog_request(profile, AGGREGATE_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    rows = []
    for bucket in _buckets(response):
        by = bucket.get("by")
        if not isinstance(by, dict):
            continue
        label = " | ".join(f"{facet}={by.get(facet, '-')}" for facet in facets)
        rows.append((_bucket_count(bucket), label))
    rows.sort(key=lambda row: row[0], reverse=True)
    for count, label in rows:
        print(f"{count:>8}  {label}")
    if not rows:
        print("(no buckets)")
    return 0


def command_fields(args: argparse.Namespace) -> int:
    """Discover the attribute schema of matching logs: dotted key paths + sample values."""
    _, profile = load_profile(args.profile)
    sample = args.sample
    if sample < 1 or sample > 20:
        raise DatadogHelperError("--sample은 1부터 20 사이여야 합니다.")
    payload = _search_payload(args, profile, force_limit=sample)
    response = datadog_request(profile, SEARCH_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    events = response.get("data")
    if not isinstance(events, list) or not events:
        print("(no events)")
        return 0
    paths: dict[str, str] = {}
    for event in events:
        if isinstance(event, dict):
            attrs = event.get("attributes")
            if isinstance(attrs, dict):
                collect_key_paths(attrs, out=paths)
    print(f"# sampled {len(events)} event(s); unique attribute paths: {len(paths)}")
    for path in sorted(paths):
        print(f"{path} = {paths[path]}")
    return 0


def command_frames(args: argparse.Namespace) -> int:
    """Extract app stack frames (e.g. at com.example...) from matching log messages."""
    if not args.prefix:
        raise DatadogHelperError("--prefix가 필요합니다. 예: --prefix com.example")
    _, profile = load_profile(args.profile)
    payload = _search_payload(args, profile)
    response = datadog_request(profile, SEARCH_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    events = response.get("data")
    events = events if isinstance(events, list) else []
    counter: Counter[str] = Counter()
    matched_events = 0
    for event in events:
        if not isinstance(event, dict):
            continue
        attrs = event.get("attributes")
        attrs = attrs if isinstance(attrs, dict) else {}
        texts = [str(attrs.get("message") or "")]
        custom = attrs.get("attributes")
        if isinstance(custom, dict):
            error = custom.get("error")
            if isinstance(error, dict):
                texts.append(str(error.get("stack") or ""))
        frames = extract_frames("\n".join(texts), args.prefix)
        if frames:
            matched_events += 1
            counter.update(frames)  # one count per event per frame
    print(f"# scanned {len(events)} event(s); {matched_events} contained '{args.prefix}' frames")
    for frame, count in counter.most_common(args.top):
        print(f"{count:>6}  {frame}")
    return 0


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    add_profile_arg(parser)
    parser.add_argument("query", nargs="*", help="Datadog log search query")
    parser.add_argument("--service")
    parser.add_argument("--env")
    parser.add_argument("--status")
    parser.add_argument("--host")
    parser.add_argument("--trace-id")
    parser.add_argument("--version")
    parser.add_argument("--index", action="append", help="Datadog log index; can repeat")
    parser.add_argument("--from", dest="from_time", default=None)
    parser.add_argument("--to", dest="to_time", default="now")
    parser.add_argument("--raw", action="store_true")


def add_common_search_args(parser: argparse.ArgumentParser) -> None:
    add_filter_args(parser)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--sort", choices=("timestamp", "-timestamp"), default="-timestamp")
    parser.add_argument("--tz", default="Asia/Seoul")
    parser.add_argument("--allow-wide", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search and aggregate Datadog logs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search Datadog logs")
    add_common_search_args(search)
    search.set_defaults(func=command_search)

    errors = subparsers.add_parser("errors", help="Search recent error logs")
    add_common_search_args(errors)
    errors.add_argument("--minutes", type=int, default=30)
    errors.set_defaults(func=command_errors)

    timeline = subparsers.add_parser("timeline", help="Search logs in ascending time order")
    add_common_search_args(timeline)
    timeline.set_defaults(func=command_timeline)

    count = subparsers.add_parser(
        "count", help="Exact hit count for a query (server-side aggregate)"
    )
    add_filter_args(count)
    count.set_defaults(func=command_count)

    agg = subparsers.add_parser(
        "agg", help="Group-by counts per facet (server-side aggregate, top-N)"
    )
    add_filter_args(agg)
    agg.add_argument("--by", action="append", help="facet to group by; can repeat (e.g. @request_uri)")
    agg.add_argument("--top", type=int, default=10, help="top-N buckets per facet (default 10)")
    agg.set_defaults(func=command_agg)

    fields = subparsers.add_parser(
        "fields", help="Show attribute key paths + sample values from a few matching events"
    )
    add_common_search_args(fields)
    fields.add_argument("--sample", type=int, default=3, help="events to sample (default 3, max 20)")
    fields.set_defaults(func=command_fields)

    frames = subparsers.add_parser(
        "frames", help="Extract app stack frames from matching log messages"
    )
    add_common_search_args(frames)
    frames.add_argument("--prefix", help="package prefix to match (e.g. com.example)")
    frames.add_argument("--top", type=int, default=20, help="top-N frames to print (default 20)")
    frames.set_defaults(func=command_frames)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
