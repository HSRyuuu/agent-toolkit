#!/usr/bin/env python3
"""Tests for deterministic datadog-helper behavior.

Run with: python3 test_datadog_helper.py
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load_module("datadog_common")
logs = load_module("datadog_logs")
apm = load_module("datadog_apm")


def check(name: str, cond: bool, detail: str = "") -> bool:
    suffix = f" - {detail}" if detail else ""
    print(f"[{'PASS' if cond else 'FAIL'}] {name}{suffix}")
    return cond


def case_normalize_site() -> bool:
    return check(
        "normalize_site supports aliases and URLs",
        common.normalize_site("https://app.datadoghq.eu/account") == "datadoghq.eu"
        and common.normalize_site("api.us3.datadoghq.com") == "us3.datadoghq.com"
        and common.normalize_site("us1") == "datadoghq.com",
    )


def case_secure_write_permissions() -> bool:
    with tempfile.TemporaryDirectory(prefix="datadog-helper-test-") as tmp:
        target = Path(tmp) / "nested" / "config.json"
        common.write_json_secure(target, {"api_key": "abc"})
        file_mode = stat.S_IMODE(target.stat().st_mode)
        dir_mode = stat.S_IMODE(target.parent.stat().st_mode)
        data = common.read_json(target)
    return check(
        "write_json_secure writes 600 file under 700 dir",
        file_mode == 0o600 and dir_mode == 0o700 and data == {"api_key": "abc"},
        f"file={oct(file_mode)} dir={oct(dir_mode)}",
    )


def case_memory_file_created_securely() -> bool:
    with tempfile.TemporaryDirectory(prefix="datadog-helper-test-") as tmp:
        os.environ["DATADOG_LOG_HELPER_CONFIG_DIR"] = tmp
        try:
            path = common.ensure_memory_file()
            file_mode = stat.S_IMODE(path.stat().st_mode)
            text = path.read_text(encoding="utf-8")
        finally:
            os.environ.pop("DATADOG_LOG_HELPER_CONFIG_DIR", None)
    return check(
        "ensure_memory_file creates expected template",
        file_mode == 0o600 and "## 로그 접근" in text and "## 자주 쓰는 쿼리" in text,
    )


def case_sensitive_sanitizing() -> bool:
    profile = {"api_key": "<API_KEY>", "app_key": "<APP_KEY>"}
    text = common.sanitize_sensitive(
        "DD-API-KEY: <API_KEY> DD-APPLICATION-KEY: <APP_KEY>",
        profile,
    )
    return check(
        "sanitize_sensitive masks configured keys",
        "1234567890abcdef" not in text and "abcdef1234567890" not in text,
        text,
    )


def case_format_log_events() -> bool:
    response = {
        "data": [
            {
                "id": "abc",
                "attributes": {
                    "timestamp": "2026-07-08T01:02:03Z",
                    "status": "error",
                    "service": "payments-api",
                    "host": "host-1",
                    "message": "hello\nworld",
                    "attributes": {"env": "prod", "trace_id": "123"},
                },
            }
        ]
    }
    text = common.format_log_events(response, tz_name="UTC")
    return check(
        "format_log_events emits compact event",
        "service=payments-api" in text
        and "env=prod" in text
        and "hello world" in text
        and "trace_id=123" in text,
        text,
    )


def case_base_query_composes_filters() -> bool:
    class Args:
        query = ["timeout"]
        service = "payments-api"
        env = "prod"
        status = "error"
        host = None
        trace_id = "123"
        version = None

    query = logs._base_query(Args())
    return check(
        "_base_query composes Datadog filters",
        query == "timeout service:payments-api env:prod status:error @trace_id:123",
        query,
    )


def _filter_args(**overrides):
    class Args:
        query = ['"ERROR 1 ---"']
        service = "prd-some-service"
        env = None
        status = None
        host = None
        trace_id = None
        version = None
        index = None
        from_time = "now-24h"
        to_time = "now"

    for key, value in overrides.items():
        setattr(Args, key, value)
    return Args()


def case_aggregate_payload_count() -> bool:
    payload = logs._aggregate_payload(_filter_args(), {})
    return check(
        "_aggregate_payload builds count compute without group_by",
        payload["compute"] == [{"aggregation": "count"}]
        and payload["filter"]["from"] == "now-24h"
        and payload["filter"]["query"] == '"ERROR 1 ---" service:prd-some-service'
        and "group_by" not in payload,
        str(payload),
    )


def case_aggregate_payload_group_by() -> bool:
    group_by = [
        {
            "facet": "@request_uri",
            "limit": 10,
            "sort": {"type": "measure", "aggregation": "count", "order": "desc"},
        }
    ]
    payload = logs._aggregate_payload(_filter_args(), {}, group_by=group_by)
    return check(
        "_aggregate_payload includes group_by facets",
        payload.get("group_by") == group_by,
        str(payload.get("group_by")),
    )


def case_bucket_helpers() -> bool:
    response = {
        "data": {
            "buckets": [
                {"by": {"@request_uri": "/play/element"}, "computes": {"c0": 34}},
                {"by": {"@request_uri": "/play/main"}, "computes": {"c0": 30}},
            ]
        }
    }
    buckets = logs._buckets(response)
    counts = [logs._bucket_count(b) for b in buckets]
    return check(
        "_buckets/_bucket_count parse aggregate response",
        counts == [34, 30] and logs._buckets({"data": None}) == [],
        str(counts),
    )


def case_collect_key_paths() -> bool:
    event_attrs = {
        "timestamp": "2026-07-13T01:02:03Z",
        "attributes": {
            "request_uri": "/play/element",
            "headers": {
                "x-forwarded-path": "/play/element",
                "authorization": "Bearer secret-jwt-value",
                "cookie": "JSESSIONID=abc",
            },
            "tags_list": ["env:prd", "team:play"],
        },
    }
    paths = common.collect_key_paths(event_attrs)
    return check(
        "collect_key_paths walks nested dicts and redacts sensitive keys",
        paths.get("attributes.request_uri") == "/play/element"
        and "attributes.headers.x-forwarded-path" in paths
        and "attributes.tags_list" in paths
        and paths.get("attributes.headers.authorization") == "***redacted***"
        and paths.get("attributes.headers.cookie") == "***redacted***",
        str(sorted(paths)),
    )


def case_extract_frames() -> bool:
    trace = (
        "org.hibernate.NonUniqueResultException: 2 results\n"
        "\tat org.hibernate.AbstractSelectionQuery.uniqueElement(AbstractSelectionQuery.java:586)\n"
        "\tat com.example.shop.repository.OrderQueryRepository.get(OrderQueryRepository.java:52)\n"
        "\tat com.example.shop.service.OrderService.orders(OrderService.java:88)\n"
        "\tat com.example.shop.repository.OrderQueryRepository.get(OrderQueryRepository.java:52)\n"
    )
    frames = common.extract_frames(trace, "com.example")
    return check(
        "extract_frames returns unique app frames in order",
        frames
        == [
            "com.example.shop.repository.OrderQueryRepository.get(OrderQueryRepository.java:52)",
            "com.example.shop.service.OrderService.orders(OrderService.java:88)",
        ],
        str(frames),
    )


def case_raw_limit_guard() -> bool:
    ok_small = ok_wide = blocked = False
    try:
        logs._validate_raw(5, False)
        ok_small = True
    except common.DatadogHelperError:
        pass
    try:
        logs._validate_raw(50, True)
        ok_wide = True
    except common.DatadogHelperError:
        pass
    try:
        logs._validate_raw(6, False)
    except common.DatadogHelperError:
        blocked = True
    return check(
        "_validate_raw blocks raw over 5 events without --allow-wide",
        ok_small and ok_wide and blocked,
    )


def case_default_limit_is_20() -> bool:
    return check(
        "default limit is 20",
        common.DEFAULT_LIMIT == 20 and logs._default_limit({}) == 20,
    )


def case_errors_from_resolution() -> bool:
    conflict_blocked = False
    try:
        logs.resolve_errors_from("now-1h", 10)
    except common.DatadogHelperError:
        conflict_blocked = True
    return check(
        "resolve_errors_from honors --from, defaults to 30m, blocks conflicts",
        logs.resolve_errors_from("now-24h", None) == "now-24h"
        and logs.resolve_errors_from(None, None) == "now-30m"
        and logs.resolve_errors_from(None, 10) == "now-10m"
        and conflict_blocked,
    )


def case_default_limit_clamped_to_wide_limit() -> bool:
    return check(
        "profile default_limit cannot bypass the --allow-wide guard",
        logs._default_limit({"default_limit": 800}) == common.WIDE_LIMIT
        and logs._default_limit({"default_limit": 100}) == 100,
    )


def case_search_payload_cursor() -> bool:
    args = _filter_args(cursor="abc123", limit=None, raw=False, allow_wide=False)
    payload = logs._search_payload(args, {})
    return check(
        "_search_payload includes page cursor when given",
        payload["page"] == {"limit": 20, "cursor": "abc123"},
        str(payload["page"]),
    )


def case_response_next_cursor() -> bool:
    return check(
        "response_next_cursor reads meta.page.after",
        common.response_next_cursor({"meta": {"page": {"after": "XYZ"}}}) == "XYZ"
        and common.response_next_cursor({"meta": {"page": {}}}) is None
        and common.response_next_cursor({}) is None,
    )


def case_timeseries_points() -> bool:
    bucket = {
        "computes": {
            "c0": [
                {"time": "2026-07-14T01:00:00Z", "value": 12},
                {"time": "2026-07-14T01:05:00Z", "value": 3},
            ]
        }
    }
    points = logs._timeseries_points(bucket)
    return check(
        "_timeseries_points parses timeseries compute buckets",
        points == [("2026-07-14T01:00:00Z", 12), ("2026-07-14T01:05:00Z", 3)]
        and logs._timeseries_points({"computes": {"c0": 5}}) == [],
        str(points),
    )


def case_parse_time_value() -> bool:
    iso = common.parse_time_value("2026-07-14 10:03:21", "Asia/Seoul")
    epoch_ms = common.parse_time_value("1752454800000")
    invalid_blocked = False
    try:
        common.parse_time_value("not-a-time")
    except common.DatadogHelperError:
        invalid_blocked = True
    return check(
        "parse_time_value handles naive ISO with tz and epoch millis",
        iso.isoformat() == "2026-07-14T01:03:21+00:00"
        and epoch_ms.tzname() == "UTC"
        and invalid_blocked,
        iso.isoformat(),
    )


def case_normalize_message() -> bool:
    normalized = common.normalize_message(
        "Failed order 8f14e45f-ceea-4b67-a4b4-3c9e12ab34cd retry 3 "
        "after 1500ms at 10.0.3.7:8080 token deadbeefdeadbeef99"
    )
    return check(
        "normalize_message collapses uuid/hex/numbers",
        normalized == "Failed order <uuid> retry <num> after <num>ms at <num> token <hex>",
        normalized,
    )


def case_event_show_field() -> bool:
    event = {
        "id": "e1",
        "attributes": {
            "status": "error",
            "attributes": {"error": {"kind": "TimeoutError"}, "http": {"status_code": 504}},
        },
    }
    return check(
        "event_show_field walks dotted custom paths",
        common.event_show_field(event, "@error.kind") == "TimeoutError"
        and common.event_show_field(event, "@http.status_code") == "504"
        and common.event_show_field(event, "@missing.path") == "-"
        and common.event_show_field(event, "status") == "error",
    )


def case_memory_template_has_alias_sections() -> bool:
    with tempfile.TemporaryDirectory(prefix="datadog-helper-test-") as tmp:
        os.environ["DATADOG_LOG_HELPER_CONFIG_DIR"] = tmp
        try:
            text = common.ensure_memory_file().read_text(encoding="utf-8")
        finally:
            os.environ.pop("DATADOG_LOG_HELPER_CONFIG_DIR", None)
    return check(
        "memory template includes alias and schema sections",
        "## 서비스 별칭" in text and "## 로그 스키마" in text,
    )


def _span_args(**overrides):
    class Args:
        query = []
        service = "payments-api"
        env = "prod"
        resource = None
        operation = None
        host = None
        trace_id = None
        version = None
        errors_only = False
        index = None
        from_time = "now-1h"
        to_time = "now"

    for key, value in overrides.items():
        setattr(Args, key, value)
    return Args()


def case_apm_base_query_composes_filters() -> bool:
    args = _span_args(resource="GET /orders", errors_only=True, trace_id="abc123")
    query = apm._base_query(args)
    return check(
        "apm _base_query composes span filters",
        query
        == '* service:payments-api env:prod resource_name:"GET /orders" trace_id:abc123 status:error',
        query,
    )


def case_apm_search_payload_is_wrapped() -> bool:
    args = _span_args(limit=None, raw=False, allow_wide=False, cursor="CUR", sort=None)
    payload = apm._search_payload(args, {})
    attributes = payload.get("data", {}).get("attributes", {})
    return check(
        "apm _search_payload wraps request in data.attributes",
        payload["data"]["type"] == "search_request"
        and attributes["filter"]["from"] == "now-1h"
        and attributes["page"] == {"limit": 20, "cursor": "CUR"}
        and attributes["sort"] == "-timestamp",
        str(payload),
    )


def case_apm_aggregate_payload_is_wrapped() -> bool:
    payload = apm._aggregate_payload(
        _span_args(),
        {},
        compute=[{"aggregation": "count", "type": "total"}],
        group_by=apm._group_by(["resource_name"], 10),
    )
    attributes = payload["data"]["attributes"]
    return check(
        "apm _aggregate_payload wraps compute/filter/group_by",
        payload["data"]["type"] == "aggregate_request"
        and attributes["compute"] == [{"aggregation": "count", "type": "total"}]
        and attributes["group_by"][0]["facet"] == "resource_name",
        str(attributes),
    )


def case_apm_buckets_parse_list_response() -> bool:
    response = {
        "data": [
            {
                "type": "bucket",
                "attributes": {"by": {"service": "payments-api"}, "computes": {"c0": 42}},
            },
            {"type": "bucket", "attributes": {"by": {"service": "orders-api"}, "compute": {"c0": 7}}},
        ]
    }
    buckets = apm._buckets(response)
    counts = [apm._bucket_count(bucket) for bucket in buckets]
    return check(
        "apm _buckets parses spans aggregate list (computes and compute)",
        counts == [42, 7] and apm._buckets({"data": {}}) == [],
        str(counts),
    )


def case_format_duration_ns() -> bool:
    return check(
        "format_duration_ns picks human units",
        apm.format_duration_ns(1_500_000_000) == "1.50s"
        and apm.format_duration_ns(241_700_000) == "241.7ms"
        and apm.format_duration_ns(3_200) == "3µs"
        and apm.format_duration_ns(None) == "-",
        apm.format_duration_ns(241_700_000),
    )


def case_format_span_event() -> bool:
    event = {
        "id": "sp1",
        "attributes": {
            "start_timestamp": "2026-07-14T01:02:03Z",
            "status": "error",
            "service": "payments-api",
            "resource_name": "POST /orders",
            "operation_name": "servlet.request",
            "trace_id": "t-1",
            "span_id": "s-1",
            "parent_id": "p-1",
            "type": "web",
            "custom": {"duration": 241_700_000, "env": "prod", "http": {"status_code": 500}},
        },
    }
    text = apm.format_span_event(event, tz_name="UTC", show=["@http.status_code"])
    return check(
        "format_span_event emits compact span block",
        "service=payments-api" in text
        and "duration=241.7ms" in text
        and "resource=POST /orders" in text
        and "env=prod" in text
        and "trace_id=t-1" in text
        and "@http.status_code=500" in text,
        text,
    )


def case_apm_timeseries_points() -> bool:
    bucket = {
        "computes": {
            "c0": [
                {"time": "2026-07-14T01:00:00Z", "value": 12},
                {"time": "2026-07-14T01:05:00Z", "value": 3},
            ]
        }
    }
    points = apm._timeseries_points(bucket)
    return check(
        "apm _timeseries_points parses timeseries computes",
        points == [("2026-07-14T01:00:00Z", 12), ("2026-07-14T01:05:00Z", 3)]
        and apm._timeseries_points({"computes": {"c0": 5}}) == [],
        str(points),
    )


def case_apm_raw_limit_guard() -> bool:
    blocked = False
    try:
        apm._validate_raw(6, False)
    except common.DatadogHelperError:
        blocked = True
    ok_wide = False
    try:
        apm._validate_raw(50, True)
        ok_wide = True
    except common.DatadogHelperError:
        pass
    return check("apm _validate_raw mirrors the logs raw guard", blocked and ok_wide)


def case_config_dir_prefers_new_env_var() -> bool:
    os.environ["DATADOG_HELPER_CONFIG_DIR"] = "/tmp/new-dir"
    os.environ["DATADOG_LOG_HELPER_CONFIG_DIR"] = "/tmp/old-dir"
    try:
        preferred = str(common.config_dir())
    finally:
        os.environ.pop("DATADOG_HELPER_CONFIG_DIR", None)
        os.environ.pop("DATADOG_LOG_HELPER_CONFIG_DIR", None)
    return check(
        "config_dir prefers DATADOG_HELPER_CONFIG_DIR over legacy env var",
        preferred == "/tmp/new-dir",
        preferred,
    )


def main() -> int:
    cases = [
        case_normalize_site,
        case_secure_write_permissions,
        case_memory_file_created_securely,
        case_sensitive_sanitizing,
        case_format_log_events,
        case_base_query_composes_filters,
        case_aggregate_payload_count,
        case_aggregate_payload_group_by,
        case_bucket_helpers,
        case_collect_key_paths,
        case_extract_frames,
        case_raw_limit_guard,
        case_default_limit_is_20,
        case_errors_from_resolution,
        case_default_limit_clamped_to_wide_limit,
        case_search_payload_cursor,
        case_response_next_cursor,
        case_timeseries_points,
        case_parse_time_value,
        case_normalize_message,
        case_event_show_field,
        case_memory_template_has_alias_sections,
        case_apm_base_query_composes_filters,
        case_apm_search_payload_is_wrapped,
        case_apm_aggregate_payload_is_wrapped,
        case_apm_buckets_parse_list_response,
        case_format_duration_ns,
        case_format_span_event,
        case_apm_timeseries_points,
        case_apm_raw_limit_guard,
        case_config_dir_prefers_new_env_var,
    ]
    results = [case() for case in cases]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
