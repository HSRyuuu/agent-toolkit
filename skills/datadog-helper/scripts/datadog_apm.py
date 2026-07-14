#!/usr/bin/env python3
"""Search and aggregate Datadog APM spans (read-only) with compact output."""

from __future__ import annotations

import argparse
import json
import re
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
    format_timestamp,
    load_profile,
    parse_time_value,
    print_response,
    response_next_cursor,
    run_main,
    truncate_text,
)

SEARCH_PATH = "/api/v2/spans/events/search"
AGGREGATE_PATH = "/api/v2/spans/analytics/aggregate"

RAW_LIMIT_GUARD = 5
TRACE_DEFAULT_LIMIT = 100
DURATION_METRIC = "@duration"
LATENCY_AGGREGATIONS = ("pc50", "pc95", "pc99")
MEASURE_AGGREGATIONS = (
    "count",
    "cardinality",
    "avg",
    "sum",
    "min",
    "max",
    "pc75",
    "pc90",
    "pc95",
    "pc98",
    "pc99",
)


def _facet_value(value: str) -> str:
    """Quote facet values containing whitespace (e.g. resource_name:"GET /orders")."""
    if re.search(r"\s", value) and not (value.startswith('"') and value.endswith('"')):
        return '"' + value.replace('"', '\\"') + '"'
    return value


def _base_query(args: argparse.Namespace) -> str:
    query = " ".join(args.query or []).strip()
    if not query:
        query = "*"
    query = append_filter(query, f"service:{args.service}" if args.service else None)
    query = append_filter(query, f"env:{args.env}" if args.env else None)
    query = append_filter(
        query, f"resource_name:{_facet_value(args.resource)}" if args.resource else None
    )
    query = append_filter(
        query, f"operation_name:{_facet_value(args.operation)}" if args.operation else None
    )
    query = append_filter(query, f"host:{args.host}" if args.host else None)
    query = append_filter(query, f"trace_id:{args.trace_id}" if args.trace_id else None)
    query = append_filter(query, f"version:{args.version}" if args.version else None)
    if getattr(args, "errors_only", False):
        query = append_filter(query, "status:error")
    return query


def _validate_limit(limit: int, allow_wide: bool) -> None:
    if limit < 1 or limit > MAX_LIMIT:
        raise DatadogHelperError(f"--limit은 1부터 {MAX_LIMIT} 사이여야 합니다.")
    if limit > WIDE_LIMIT and not allow_wide:
        raise DatadogHelperError(f"--limit {WIDE_LIMIT} 초과는 --allow-wide가 필요합니다.")


def _validate_raw(limit: int, allow_wide: bool) -> None:
    """Raw span events are large; block accidental context floods."""
    if limit > RAW_LIMIT_GUARD and not allow_wide:
        raise DatadogHelperError(
            f"--raw는 스팬당 출력이 크므로 --limit {RAW_LIMIT_GUARD} 초과 시 "
            "--allow-wide가 필요합니다. 집계가 목적이면 count/agg/latency를 쓰세요."
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
        limit = args.limit if args.limit is not None else DEFAULT_LIMIT
        _validate_limit(limit, allow_wide)
    if getattr(args, "raw", False):
        _validate_raw(limit, allow_wide)
    page: dict[str, Any] = {"limit": limit}
    cursor = getattr(args, "cursor", None)
    if cursor:
        page["cursor"] = cursor
    return {
        "data": {
            "type": "search_request",
            "attributes": {
                "filter": _time_filter(args, profile),
                "page": page,
                "sort": force_sort or getattr(args, "sort", None) or "-timestamp",
            },
        }
    }


def _aggregate_payload(
    args: argparse.Namespace,
    profile: dict[str, Any],
    *,
    compute: list[dict[str, Any]],
    group_by: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    attributes: dict[str, Any] = {
        "compute": compute,
        "filter": _time_filter(args, profile),
    }
    if group_by:
        attributes["group_by"] = group_by
    return {"data": {"type": "aggregate_request", "attributes": attributes}}


def _group_by(facets: list[str], top: int) -> list[dict[str, Any]]:
    return [
        {
            "facet": facet,
            "limit": top,
            "sort": {"type": "measure", "aggregation": "count", "order": "desc"},
        }
        for facet in facets
    ]


def _buckets(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Spans aggregate buckets: data[].attributes.{by,computes} (list, unlike logs)."""
    data = response.get("data")
    if not isinstance(data, list):
        return []
    buckets = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("attributes"), dict):
            buckets.append(item["attributes"])
    return buckets


def _bucket_compute(bucket: dict[str, Any], key: str = "c0") -> Any:
    computes = bucket.get("computes")
    if isinstance(computes, dict):
        return computes.get(key)
    compute = bucket.get("compute")
    if isinstance(compute, dict):
        return compute.get(key)
    return None


def _bucket_count(bucket: dict[str, Any], key: str = "c0") -> int:
    value = _bucket_compute(bucket, key)
    return int(value) if isinstance(value, (int, float)) else 0


def _bucket_label(bucket: dict[str, Any], facets: list[str]) -> str:
    by = bucket.get("by")
    by = by if isinstance(by, dict) else {}
    return " | ".join(f"{facet}={by.get(facet, '-')}" for facet in facets)


def format_duration_ns(value: Any) -> str:
    """Span durations/percentiles are nanoseconds; print a human unit."""
    if not isinstance(value, (int, float)):
        return "-"
    ns = float(value)
    if ns >= 60_000_000_000:
        return f"{ns / 60_000_000_000:.1f}min"
    if ns >= 1_000_000_000:
        return f"{ns / 1_000_000_000:.2f}s"
    if ns >= 1_000_000:
        return f"{ns / 1_000_000:.1f}ms"
    if ns >= 1_000:
        return f"{ns / 1_000:.0f}µs"
    return f"{ns:.0f}ns"


def _attrs(event: dict[str, Any]) -> dict[str, Any]:
    attrs = event.get("attributes")
    return attrs if isinstance(attrs, dict) else {}


def _custom_attrs(event: dict[str, Any]) -> dict[str, Any]:
    attrs = _attrs(event)
    for key in ("custom", "attributes"):
        custom = attrs.get(key)
        if isinstance(custom, dict):
            return custom
    return {}


def span_field(event: dict[str, Any], key: str) -> Any:
    attrs = _attrs(event)
    if attrs.get(key) is not None:
        return attrs[key]
    return _custom_attrs(event).get(key)


def span_text(event: dict[str, Any], key: str) -> str:
    value = span_field(event, key)
    return str(value) if value is not None else "-"


def span_env(event: dict[str, Any]) -> str:
    value = span_text(event, "env")
    if value != "-":
        return value
    tags = _attrs(event).get("tags")
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str) and tag.startswith("env:"):
                return tag.split(":", 1)[1]
    return "-"


def span_show_field(event: dict[str, Any], key: str) -> str:
    """Resolve a --show field. `@a.b.c` walks the custom attribute tree."""
    if not key.startswith("@"):
        return span_text(event, key)
    node: Any = _custom_attrs(event)
    for part in key[1:].split("."):
        if isinstance(node, dict):
            node = node.get(part)
        else:
            node = None
            break
    if node is None:
        return "-"
    if isinstance(node, (dict, list)):
        return truncate_text(json.dumps(node, ensure_ascii=False), 120)
    return truncate_text(str(node), 120)


def span_start(event: dict[str, Any]) -> str:
    for key in ("start_timestamp", "timestamp", "start"):
        value = span_field(event, key)
        if value is not None:
            return str(value)
    return ""


def format_span_event(
    event: dict[str, Any],
    *,
    tz_name: str | None = None,
    show: list[str] | None = None,
) -> str:
    timestamp = format_timestamp(span_start(event), tz_name)
    status = span_text(event, "status")
    service = span_text(event, "service")
    resource = truncate_text(span_text(event, "resource_name"), 120)
    operation = span_text(event, "operation_name")
    duration = format_duration_ns(_span_duration_ns(event))
    lines = [
        f"[{timestamp}] status={status} service={service} env={span_env(event)} duration={duration}",
        f"resource={resource} operation={operation} type={span_text(event, 'type')}",
        f"trace_id={span_text(event, 'trace_id')} span_id={span_text(event, 'span_id')} "
        f"parent_id={span_text(event, 'parent_id')}",
    ]
    if show:
        lines.append(" ".join(f"{key}={span_show_field(event, key)}" for key in show))
    return "\n".join(lines)


def _span_duration_ns(event: dict[str, Any]) -> Any:
    value = span_field(event, "duration")
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def _events(response: dict[str, Any]) -> list[dict[str, Any]]:
    events = response.get("data")
    if not isinstance(events, list):
        return []
    return [event for event in events if isinstance(event, dict)]


def _print_events(
    response: dict[str, Any], args: argparse.Namespace, events: list[dict[str, Any]] | None = None
) -> int:
    events = _events(response) if events is None else events
    blocks = [
        format_span_event(event, tz_name=args.tz, show=getattr(args, "show", None))
        for event in events
    ]
    if blocks:
        print("\n\n".join(blocks))
    else:
        print("(no spans)")
    next_cursor = response_next_cursor(response)
    if next_cursor:
        print(f"\n(more results available; rerun with --cursor {next_cursor})")
    return 0


def command_search(args: argparse.Namespace) -> int:
    _, profile = load_profile(args.profile)
    payload = _search_payload(args, profile)
    response = datadog_request(profile, SEARCH_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    return _print_events(response, args)


def command_trace(args: argparse.Namespace) -> int:
    """All indexed spans of one trace, ascending, with offsets from the first span."""
    if not args.trace_id:
        raise DatadogHelperError("--trace-id가 필요합니다. 예: --trace-id 1234567890abcdef")
    if args.limit is None:
        args.limit = TRACE_DEFAULT_LIMIT
    _, profile = load_profile(args.profile)
    payload = _search_payload(args, profile, force_sort="timestamp")
    response = datadog_request(profile, SEARCH_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    events = _events(response)
    if not events:
        print("(no spans)")
        print("힌트: 인덱싱된 스팬만 조회됩니다. 기간(--from)을 트레이스 발생 시각에 맞추세요.")
        return 0
    origin = None
    try:
        origin = parse_time_value(span_start(events[0]), args.tz)
    except DatadogHelperError:
        pass
    print(f"# trace {args.trace_id}: {len(events)} indexed span(s)")
    for event in events:
        offset = "-"
        if origin is not None:
            try:
                delta = parse_time_value(span_start(event), args.tz) - origin
                offset = f"+{delta.total_seconds() * 1000:.0f}ms"
            except DatadogHelperError:
                pass
        print()
        print(f"offset={offset}")
        print(format_span_event(event, tz_name=args.tz, show=getattr(args, "show", None)))
    next_cursor = response_next_cursor(response)
    if next_cursor:
        print(f"\n(more results available; rerun with --cursor {next_cursor})")
    return 0


def command_count(args: argparse.Namespace) -> int:
    """Exact server-side span count. No event download, no sampling bias."""
    _, profile = load_profile(args.profile)
    payload = _aggregate_payload(args, profile, compute=[{"aggregation": "count", "type": "total"}])
    response = datadog_request(profile, AGGREGATE_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    total = sum(_bucket_count(bucket) for bucket in _buckets(response))
    print(total)
    return 0


def command_agg(args: argparse.Namespace) -> int:
    """Server-side group-by (top-N per facet); optional measure like pc95 of @duration."""
    facets = args.by or []
    if not facets:
        raise DatadogHelperError("--by <facet>이 최소 1개 필요합니다. 예: --by resource_name")
    if args.top < 1 or args.top > 100:
        raise DatadogHelperError("--top은 1부터 100 사이여야 합니다.")
    if args.agg not in MEASURE_AGGREGATIONS:
        raise DatadogHelperError(f"--agg는 {', '.join(MEASURE_AGGREGATIONS)} 중 하나여야 합니다.")
    if args.agg not in ("count", "cardinality") and not args.measure:
        raise DatadogHelperError(f"--agg {args.agg}에는 --measure가 필요합니다. 예: --measure @duration")
    compute: dict[str, Any] = {"aggregation": args.agg, "type": "total"}
    if args.measure:
        compute["metric"] = args.measure
    _, profile = load_profile(args.profile)
    payload = _aggregate_payload(
        args, profile, compute=[compute], group_by=_group_by(facets, args.top)
    )
    response = datadog_request(profile, AGGREGATE_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    duration_measure = args.measure == DURATION_METRIC and args.agg not in ("count", "cardinality")
    rows = []
    for bucket in _buckets(response):
        value = _bucket_compute(bucket)
        numeric = value if isinstance(value, (int, float)) else 0
        rows.append((numeric, _bucket_label(bucket, facets)))
    rows.sort(key=lambda row: row[0], reverse=True)
    for value, label in rows:
        rendered = format_duration_ns(value) if duration_measure else f"{value:g}"
        print(f"{rendered:>10}  {label}")
    if not rows:
        print("(no buckets)")
    return 0


def command_latency(args: argparse.Namespace) -> int:
    """Latency profile per group: count + p50/p95/p99 of @duration (server-side)."""
    facets = args.by or ["service"]
    if args.top < 1 or args.top > 100:
        raise DatadogHelperError("--top은 1부터 100 사이여야 합니다.")
    compute = [{"aggregation": "count", "type": "total"}] + [
        {"aggregation": aggregation, "metric": DURATION_METRIC, "type": "total"}
        for aggregation in LATENCY_AGGREGATIONS
    ]
    _, profile = load_profile(args.profile)
    payload = _aggregate_payload(args, profile, compute=compute, group_by=_group_by(facets, args.top))
    response = datadog_request(profile, AGGREGATE_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    rows = []
    for bucket in _buckets(response):
        count = _bucket_count(bucket, "c0")
        percentiles = [
            format_duration_ns(_bucket_compute(bucket, f"c{index}"))
            for index in range(1, len(LATENCY_AGGREGATIONS) + 1)
        ]
        rows.append((count, percentiles, _bucket_label(bucket, facets)))
    rows.sort(key=lambda row: row[0], reverse=True)
    header = "   count  " + "  ".join(f"{name:>8}" for name in LATENCY_AGGREGATIONS)
    print(header)
    for count, percentiles, label in rows:
        cells = "  ".join(f"{value:>8}" for value in percentiles)
        print(f"{count:>8}  {cells}  {label}")
    if not rows:
        print("(no buckets)")
    return 0


INTERVAL_PATTERN = re.compile(r"\d+[smhd]")
TIMESERIES_BAR_WIDTH = 24


def _timeseries_points(bucket: dict[str, Any]) -> list[tuple[str, int]]:
    series = _bucket_compute(bucket)
    if not isinstance(series, list):
        return []
    points = []
    for point in series:
        if isinstance(point, dict):
            value = point.get("value")
            points.append(
                (str(point.get("time") or "-"), int(value) if isinstance(value, (int, float)) else 0)
            )
    return points


def command_timeseries(args: argparse.Namespace) -> int:
    """Time-bucketed span counts (server-side). Shows when a query spiked."""
    if not INTERVAL_PATTERN.fullmatch(args.interval):
        raise DatadogHelperError("--interval은 5m, 1h 같은 형식이어야 합니다 (s/m/h/d).")
    if args.top < 1 or args.top > 100:
        raise DatadogHelperError("--top은 1부터 100 사이여야 합니다.")
    _, profile = load_profile(args.profile)
    compute = [{"aggregation": "count", "type": "timeseries", "interval": args.interval}]
    group_by = _group_by(args.by, args.top) if args.by else None
    payload = _aggregate_payload(args, profile, compute=compute, group_by=group_by)
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
    filter_payload = payload["data"]["attributes"]["filter"]
    print(f"# interval={args.interval} from={filter_payload['from']} to={filter_payload['to']}")
    for bucket in buckets:
        by = bucket.get("by")
        if isinstance(by, dict) and by:
            print(f"\n## {_bucket_label(bucket, args.by or sorted(by))}")
        for time_text, value in _timeseries_points(bucket):
            bar = "#" * round(value / max_value * TIMESERIES_BAR_WIDTH) if max_value else ""
            print(f"{format_timestamp(time_text, args.tz)}  {value:>8}  {bar}")
    return 0


def command_services(args: argparse.Namespace) -> int:
    """Active services in the window via span aggregation (needs only apm_read)."""
    args.by = ["service"]
    return command_agg(args)


def command_fields(args: argparse.Namespace) -> int:
    """Discover the span attribute schema: dotted key paths + sample values."""
    if args.limit is not None:
        raise DatadogHelperError("fields는 --limit 대신 --sample을 사용합니다.")
    if args.sample < 1 or args.sample > 20:
        raise DatadogHelperError("--sample은 1부터 20 사이여야 합니다.")
    _, profile = load_profile(args.profile)
    payload = _search_payload(args, profile, force_limit=args.sample)
    response = datadog_request(profile, SEARCH_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    events = _events(response)
    if not events:
        print("(no spans)")
        return 0
    paths: dict[str, str] = {}
    for event in events:
        attrs = event.get("attributes")
        if isinstance(attrs, dict):
            collect_key_paths(attrs, out=paths)
    print(f"# sampled {len(events)} span(s); unique attribute paths: {len(paths)}")
    for path in sorted(paths):
        print(f"{path} = {paths[path]}")
    return 0


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    add_profile_arg(parser)
    parser.add_argument("query", nargs="*", help="Datadog span search query")
    parser.add_argument("--service")
    parser.add_argument("--env")
    parser.add_argument("--resource", help="resource_name filter (e.g. 'GET /orders')")
    parser.add_argument("--operation", help="operation_name filter (e.g. servlet.request)")
    parser.add_argument("--host")
    parser.add_argument("--trace-id")
    parser.add_argument("--version")
    parser.add_argument("--errors-only", action="store_true", help="add status:error to the query")
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
        help="extra span attribute to print (e.g. @http.status_code, @db.statement); can repeat",
    )


def _add_agg_args(parser: argparse.ArgumentParser, *, default_top: int) -> None:
    parser.add_argument("--top", type=int, default=default_top, help="top-N buckets (max 100)")
    parser.add_argument("--tz", default="Asia/Seoul")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search and aggregate Datadog APM spans (read-only)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search indexed spans")
    add_common_search_args(search)
    search.set_defaults(func=command_search)

    trace = subparsers.add_parser(
        "trace", help="All indexed spans of one trace, ascending with offsets"
    )
    add_common_search_args(trace)
    trace.set_defaults(func=command_trace)

    count = subparsers.add_parser("count", help="Exact span count (server-side aggregate)")
    add_filter_args(count)
    count.set_defaults(func=command_count)

    agg = subparsers.add_parser(
        "agg", help="Group-by aggregation per facet (count or a measure like pc95 @duration)"
    )
    add_filter_args(agg)
    agg.add_argument("--by", action="append", help="facet to group by; can repeat (e.g. resource_name)")
    agg.add_argument("--agg", default="count", help=f"aggregation ({', '.join(MEASURE_AGGREGATIONS)})")
    agg.add_argument("--measure", help="measure facet for non-count aggregations (e.g. @duration)")
    _add_agg_args(agg, default_top=10)
    agg.set_defaults(func=command_agg)

    latency = subparsers.add_parser(
        "latency", help="count + p50/p95/p99 of @duration per group (default --by service)"
    )
    add_filter_args(latency)
    latency.add_argument("--by", action="append", help="facet to group by (default service)")
    _add_agg_args(latency, default_top=10)
    latency.set_defaults(func=command_latency)

    timeseries = subparsers.add_parser(
        "timeseries", help="Time-bucketed span counts (find spikes and deploy shifts)"
    )
    add_filter_args(timeseries)
    timeseries.add_argument("--interval", default="5m", help="bucket size, e.g. 1m/5m/1h (default 5m)")
    timeseries.add_argument("--by", action="append", help="optional facet to split series by; can repeat")
    _add_agg_args(timeseries, default_top=5)
    timeseries.set_defaults(func=command_timeseries)

    services = subparsers.add_parser(
        "services", help="Active services in the window (span count per service)"
    )
    add_filter_args(services)
    services.add_argument("--agg", default="count", help=argparse.SUPPRESS)
    services.add_argument("--measure", help=argparse.SUPPRESS)
    _add_agg_args(services, default_top=50)
    services.set_defaults(func=command_services)

    fields = subparsers.add_parser(
        "fields", help="Show span attribute key paths + sample values from a few spans"
    )
    add_common_search_args(fields)
    fields.add_argument("--sample", type=int, default=3, help="spans to sample (default 3, max 20)")
    fields.set_defaults(func=command_fields)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
