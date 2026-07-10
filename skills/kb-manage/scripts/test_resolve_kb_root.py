#!/usr/bin/env python3
"""Regression tests for mandatory KB root registration."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("resolve_kb_root.py")
SPEC = importlib.util.spec_from_file_location("resolve_kb_root", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def check(name: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def main() -> int:
    sandbox = Path(tempfile.mkdtemp(prefix="kb-root-config-"))
    config_path = sandbox / "kb-config.json"
    registered_root = sandbox / "registered"
    unregistered_root = sandbox / "unregistered"
    registered_root.mkdir()
    unregistered_root.mkdir()
    MODULE.CONFIG_PATH = config_path

    missing_root, missing_error = MODULE.resolve_root(None)
    missing_config_guidance = (
        missing_root is None
        and missing_error is not None
        and str(Path.home() / "KnowledgeBase") in missing_error
        and str(config_path) in missing_error
    )

    config_path.write_text("{}", encoding="utf-8")
    empty_root, empty_error = MODULE.resolve_root(None)
    empty_config_guidance = (
        empty_root is None
        and empty_error is not None
        and str(Path.home() / "KnowledgeBase") in empty_error
    )

    config_path.write_text(
        json.dumps(
            {
                "kbs": {"personal": str(registered_root)},
                "default": "personal",
            }
        ),
        encoding="utf-8",
    )
    rejected_root, rejected_error = MODULE.resolve_root(str(unregistered_root))
    accepted_root, accepted_error = MODULE.resolve_root(str(registered_root))
    named_root, named_error = MODULE.resolve_root("personal")

    results = [
        check("missing config proposes ~/KnowledgeBase", missing_config_guidance),
        check("empty config proposes ~/KnowledgeBase", empty_config_guidance),
        check(
            "unregistered absolute path is rejected",
            rejected_root is None
            and rejected_error is not None
            and "not registered" in rejected_error,
        ),
        check(
            "registered absolute path resolves",
            accepted_root == registered_root.resolve() and accepted_error is None,
        ),
        check(
            "registered name resolves",
            named_root == registered_root.resolve() and named_error is None,
        ),
    ]
    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
