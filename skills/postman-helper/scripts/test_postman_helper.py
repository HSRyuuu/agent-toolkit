#!/usr/bin/env python3
"""Tests for deterministic postman-helper behavior.

Run with: python3 test_postman_helper.py
Covers the parts that must not silently break: the safety gate, env/method
classification, secret redaction, collection parsing, and secure config writes.
"""

from __future__ import annotations

import importlib.util
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


common = load_module("postman_common")


def check(name: str, cond: bool, detail: str = "") -> bool:
    print(f"[{'PASS' if cond else 'FAIL'}] {name}{f' - {detail}' if detail else ''}")
    return cond


SAMPLE = {
    "info": {"name": "Sample"},
    "variable": [{"key": "base_url", "value": "http://localhost:8080"}],
    "item": [
        {
            "name": "Orders",
            "item": [
                {
                    "name": "List orders",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "Authorization", "value": "Bearer secret-token"}],
                        "url": {
                            "raw": "{{base_url}}/orders?status=paid",
                            "path": ["orders"],
                            "query": [{"key": "status", "value": "paid", "description": "주문 상태"}],
                        },
                    },
                },
                {
                    "name": "Delete order",
                    "request": {"method": "DELETE", "url": {"raw": "{{base_url}}/orders/1", "path": ["orders", "1"]}},
                },
            ],
        }
    ],
}


def case_method_classification() -> bool:
    c = common.classify_method
    return check(
        "classify_method: GET safe / POST confirm / DELETE blocked",
        c("GET") == "safe" and c("post") == "confirm"
        and c("PUT") == "blocked" and c("DELETE") == "blocked" and c("PATCH") == "blocked",
    )


def case_env_classification() -> bool:
    c = common.classify_env
    return check(
        "classify_env: localhost/127.x/[::1]/first-label-dev local, mid-label dev remote",
        c("http://localhost:8080/x") == "local"
        and c("http://127.0.0.2:8080/x") == "local"
        and c("http://[::1]:8080/x") == "local"
        and c("http://dev.example.com/x") == "local"
        and c("http://api.dev.example.com/x") == "remote"
        and c("https://svc.local/x") == "local"
        and c("https://api.example.com/x") == "remote"
        and c("{{base_url}}/x") == "unknown",
        f'{c("http://[::1]:8080/x")}/{c("http://api.dev.example.com/x")}/{c("{{base_url}}/x")}',
    )


def case_gate() -> bool:
    g = common.execution_gate
    return check(
        "execution_gate: only safe+local auto-runs; blocked never; confirm gated",
        g("safe", "local", False)[0] is True
        and g("safe", "remote", False)[0] is False
        and g("safe", "remote", True)[0] is True
        and g("safe", "unknown", False)[0] is False
        and g("confirm", "local", False)[0] is False
        and g("confirm", "local", True)[0] is True
        and g("blocked", "local", True)[0] is False,
    )


def case_iter_requests() -> bool:
    entries = list(common.iter_requests(SAMPLE))
    names = {e["name"] for e in entries}
    folders = {e["folder"] for e in entries}
    return check(
        "iter_requests: walks folders, keeps folder path + method",
        names == {"List orders", "Delete order"} and folders == {"Orders"}
        and entries[0]["method"] == "GET",
        f"names={names}",
    )


def case_redaction() -> bool:
    detail = common.format_request_detail(next(common.iter_requests(SAMPLE)))
    return check(
        "format_request_detail redacts Authorization, keeps query params",
        "secret-token" not in detail and "***redacted***" in detail and "status" in detail,
    )


def case_var_resolution() -> bool:
    varmap = common.build_varmap(SAMPLE, ["base_url=http://localhost:9000"])
    resolved = common.resolve_vars("{{base_url}}/orders", varmap)
    return check(
        "resolve_vars: --var override wins, unknown vars survive",
        resolved == "http://localhost:9000/orders"
        and common.resolve_vars("{{missing}}/x", varmap) == "{{missing}}/x"
        and common.has_unresolved_vars("{{missing}}/x") is True,
    )


def case_url_redaction() -> bool:
    redacted = common.redact_url("http://localhost:8080/orders?status=paid&api_key=sk-123")
    return check(
        "redact_url: sensitive query values hidden, others kept",
        "sk-123" not in redacted and "status=paid" in redacted and "***redacted***" in redacted,
        redacted,
    )


def case_no_redirect_follow() -> bool:
    import inspect
    return check(
        "run_curl does not follow redirects (--location absent)",
        "--location" not in inspect.getsource(common.run_curl),
    )


def case_run_default_is_preview() -> bool:
    """run without --send must never transmit, even for safe+local."""
    import argparse
    import contextlib
    import io
    import json

    run_mod = load_module("postman_run")

    def boom(**_kw):
        raise AssertionError("run_curl called without --send")

    run_mod.run_curl = boom
    with tempfile.TemporaryDirectory(prefix="postman-helper-test-") as tmp:
        col_path = Path(tmp) / "sample.json"
        col_path.write_text(json.dumps(SAMPLE), encoding="utf-8")
        args = argparse.Namespace(
            file=str(col_path), collection=None, profile=None,
            query="List orders", first=False, var=None,
            send=False, confirm=False, max_body=2000,
        )
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                code = run_mod.command_run(args)
        except AssertionError as exc:
            return check("run without --send never transmits", False, str(exc))
    return check(
        "run without --send never transmits (exit 2, preview shown)",
        code == 2 and "미리보기" in out.getvalue(),
    )


def case_secure_write() -> bool:
    with tempfile.TemporaryDirectory(prefix="postman-helper-test-") as tmp:
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


def main() -> int:
    cases = [
        case_method_classification,
        case_env_classification,
        case_gate,
        case_iter_requests,
        case_redaction,
        case_var_resolution,
        case_url_redaction,
        case_no_redirect_follow,
        case_run_default_is_preview,
        case_secure_write,
    ]
    results = [c() for c in cases]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
