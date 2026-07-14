#!/usr/bin/env python3
"""Search and aggregate Datadog logs with compact output."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import timedelta
from typing import Any

from datadog_common import (
    DEFAULT_FROM,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    WIDE_LIMIT,
    DatadogHelperError,
    add_profile_arg,
    append_filter,
    collect_key_paths,
    datadog_request,
    extract_frames,
    format_log_event,
    format_log_events,
    format_timestamp,
    load_profile,
    normalize_message,
    parse_time_value,
    print_response,
    response_next_cursor,
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
    # profile defaults must not bypass the --allow-wide guard
    return max(1, min(limit, WIDE_LIMIT))


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
    if limit > WIDE_LIMIT and not allow_wide:
        raise DatadogHelperError(f"--limit {WIDE_LIMIT} 초과는 --allow-wide가 필요합니다.")


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
    page: dict[str, Any] = {"limit": limit}
    cursor = getattr(args, "cursor", None)
    if cursor:
        page["cursor"] = cursor
    return {
        "filter": filter_payload,
        "page": page,
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
    text = format_log_events(response, tz_name=args.tz, show=getattr(args, "show", None))
    if text:
        print(text)
    next_cursor = response_next_cursor(response)
    if next_cursor:
        print(f"\n(more results available; rerun with --cursor {next_cursor})")
    return 0


DEFAULT_ERRORS_MINUTES = 30


def resolve_errors_from(from_time: str | None, minutes: int | None) -> str:
    """errors window: --minutes wins when given, --from is honored, else last 30m."""
    if minutes is not None:
        if minutes < 1:
            raise DatadogHelperError("--minutes는 1 이상이어야 합니다.")
        if from_time is not None:
            raise DatadogHelperError("--from과 --minutes는 함께 쓸 수 없습니다. 하나만 지정하세요.")
        return f"now-{minutes}m"
    if from_time is not None:
        return from_time
    return f"now-{DEFAULT_ERRORS_MINUTES}m"


def command_errors(args: argparse.Namespace) -> int:
    args.status = args.status or "error"
    args.from_time = resolve_errors_from(args.from_time, args.minutes)
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


INTERVAL_PATTERN = re.compile(r"\d+[smhd]")
TIMESERIES_BAR_WIDTH = 24


def _timeseries_points(bucket: dict[str, Any]) -> list[tuple[str, int]]:
    computes = bucket.get("computes")
    if not isinstance(computes, dict):
        return []
    series = computes.get("c0")
    if not isinstance(series, list):
        return []
    points = []
    for point in series:
        if isinstance(point, dict):
            value = point.get("value")
            points.append((str(point.get("time") or "-"), int(value) if isinstance(value, (int, float)) else 0))
    return points


def command_timeseries(args: argparse.Namespace) -> int:
    """Time-bucketed counts (server-side). Shows when a query spiked without downloading events."""
    if not INTERVAL_PATTERN.fullmatch(args.interval):
        raise DatadogHelperError("--interval은 5m, 1h 같은 형식이어야 합니다 (s/m/h/d).")
    if args.top < 1 or args.top > 100:
        raise DatadogHelperError("--top은 1부터 100 사이여야 합니다.")
    _, profile = load_profile(args.profile)
    group_by = None
    if args.by:
        group_by = [
            {
                "facet": facet,
                "limit": args.top,
                "sort": {"type": "measure", "aggregation": "count", "order": "desc"},
            }
            for facet in args.by
        ]
    payload = _aggregate_payload(args, profile, group_by=group_by)
    payload["compute"] = [
        {"aggregation": "count", "interval": args.interval, "type": "timeseries"}
    ]
    response = datadog_request(profile, AGGREGATE_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    buckets = _buckets(response)
    if not buckets:
        print("(no buckets)")
        return 0
    max_value = max(
        (value for bucket in buckets for _, value in _timeseries_points(bucket)),
        default=0,
    )
    print(f"# interval={args.interval} from={payload['filter']['from']} to={payload['filter']['to']}")
    for bucket in buckets:
        by = bucket.get("by")
        if isinstance(by, dict) and by:
            label = " | ".join(f"{facet}={by.get(facet, '-')}" for facet in (args.by or by))
            print(f"\n## {label}")
        for time_text, value in _timeseries_points(bucket):
            bar = "#" * round(value / max_value * TIMESERIES_BAR_WIDTH) if max_value else ""
            print(f"{format_timestamp(time_text, args.tz)}  {value:>8}  {bar}")
    return 0


def command_around(args: argparse.Namespace) -> int:
    """Context view: logs within ±window minutes of a center time, ascending, center marked."""
    if not args.time:
        raise DatadogHelperError("--time이 필요합니다 (ISO8601 또는 epoch 초/밀리초).")
    if args.window < 1 or args.window > 120:
        raise DatadogHelperError("--window는 1부터 120(분) 사이여야 합니다.")
    center = parse_time_value(args.time, args.tz)
    window = timedelta(minutes=args.window)
    args.from_time = (center - window).isoformat()
    args.to_time = (center + window).isoformat()
    args.sort = "timestamp"

    _, profile = load_profile(args.profile)
    payload = _search_payload(args, profile)
    response = datadog_request(profile, SEARCH_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    events = response.get("data")
    events = [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []
    center_label = format_timestamp(center.isoformat(), args.tz)
    print(f"# ±{args.window}m around {center_label} ({len(events)} events)")
    marker_printed = False
    for event in events:
        attrs = event.get("attributes")
        timestamp_raw = attrs.get("timestamp") if isinstance(attrs, dict) else None
        if not marker_printed and timestamp_raw:
            try:
                if parse_time_value(str(timestamp_raw), args.tz) >= center:
                    print(f"\n----- center {center_label} -----")
                    marker_printed = True
            except DatadogHelperError:
                pass
        print()
        print(format_log_event(event, tz_name=args.tz, show=getattr(args, "show", None)))
    if not marker_printed:
        print(f"\n----- center {center_label} -----")
    next_cursor = response_next_cursor(response)
    if next_cursor:
        print(f"\n(more results available; rerun with --cursor {next_cursor})")
    return 0


DEFAULT_PATTERNS_LIMIT = 200


def command_patterns(args: argparse.Namespace) -> int:
    """Cluster messages by shape (numbers/uuids/hex normalized) and rank pattern counts."""
    if args.top < 1 or args.top > 100:
        raise DatadogHelperError("--top은 1부터 100 사이여야 합니다.")
    _, profile = load_profile(args.profile)
    if args.limit is None:
        args.limit = DEFAULT_PATTERNS_LIMIT
    payload = _search_payload(args, profile)
    response = datadog_request(profile, SEARCH_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    events = response.get("data")
    events = events if isinstance(events, list) else []
    counter: Counter[str] = Counter()
    for event in events:
        if not isinstance(event, dict):
            continue
        attrs = event.get("attributes")
        attrs = attrs if isinstance(attrs, dict) else {}
        message = str(attrs.get("message") or "")
        if message.strip():
            counter[normalize_message(message)] += 1
    print(f"# scanned {len(events)} event(s); {len(counter)} pattern(s)")
    for pattern, count in counter.most_common(args.top):
        print(f"{count:>6}  {pattern}")
    if response_next_cursor(response):
        print("\n(sampled window truncated at --limit; counts are per-sample, use count/agg for exact totals)")
    return 0


def command_fields(args: argparse.Namespace) -> int:
    """Discover the attribute schema of matching logs: dotted key paths + sample values."""
    if args.limit is not None:
        raise DatadogHelperError("fields는 --limit 대신 --sample을 사용합니다.")
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
    parser.add_argument("--cursor", help="meta.page.after cursor from a previous truncated search")
    parser.add_argument(
        "--show",
        action="append",
        help="extra attribute to print per event (e.g. @error.kind, @http.status_code); can repeat",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search and aggregate Datadog logs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search Datadog logs")
    add_common_search_args(search)
    search.set_defaults(func=command_search)

    errors = subparsers.add_parser("errors", help="Search recent error logs")
    add_common_search_args(errors)
    errors.add_argument(
        "--minutes",
        type=int,
        default=None,
        help="lookback window in minutes (mutually exclusive with --from; default 30 when neither given)",
    )
    errors.set_defaults(func=command_errors)

    timeline = subparsers.add_parser("timeline", help="Search logs in ascending time order")
    add_common_search_args(timeline)
    timeline.set_defaults(func=command_timeline)

    around = subparsers.add_parser(
        "around", help="Show logs within ±N minutes of a center time (ascending, center marked)"
    )
    add_common_search_args(around)
    around.add_argument("--time", help="center time: ISO8601 (naive uses --tz) or epoch sec/ms")
    around.add_argument("--window", type=int, default=5, help="minutes before/after center (default 5)")
    around.set_defaults(func=command_around)

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

    timeseries = subparsers.add_parser(
        "timeseries", help="Time-bucketed counts (server-side; find spikes and deploy shifts)"
    )
    add_filter_args(timeseries)
    timeseries.add_argument("--interval", default="5m", help="bucket size, e.g. 1m/5m/1h (default 5m)")
    timeseries.add_argument("--by", action="append", help="optional facet to split series by; can repeat")
    timeseries.add_argument("--top", type=int, default=5, help="top-N groups when --by is used (default 5)")
    timeseries.add_argument("--tz", default="Asia/Seoul")
    timeseries.set_defaults(func=command_timeseries)

    patterns = subparsers.add_parser(
        "patterns", help="Cluster log messages by shape and rank pattern counts (client-side sample)"
    )
    add_common_search_args(patterns)
    patterns.add_argument("--top", type=int, default=15, help="top-N patterns to print (default 15)")
    patterns.set_defaults(func=command_patterns)

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
