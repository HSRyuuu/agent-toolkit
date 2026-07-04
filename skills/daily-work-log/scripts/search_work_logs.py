#!/usr/bin/env python3
"""Search saved daily work log Markdown files by frontmatter and body keywords."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from first_pass_candidate_utils import DEFAULT_STATE_ROOT, compact

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FILENAME_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
IGNORED_DIRS = {".git", ".obsidian", "node_modules"}
SNIPPET_LIMIT = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="로그 루트 아래 저장된 daily work log Markdown을 frontmatter/본문 기준으로 검색한다."
    )
    parser.add_argument("--log-root", help="기본값: config.json의 log_root")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_STATE_ROOT / "config.json"),
        help="기본값: ~/.daily-work-log/config.json",
    )
    parser.add_argument("--date", action="append", default=[], help="frontmatter date YYYY-MM-DD; repeatable")
    parser.add_argument("--since", help="date 시작일 YYYY-MM-DD, inclusive")
    parser.add_argument("--until", help="date 종료일 YYYY-MM-DD, inclusive")
    parser.add_argument("--type", dest="doc_type", help="frontmatter type 정확히 일치. 예: daily-work-log")
    parser.add_argument("--tag", action="append", default=[], help="tag substring; repeatable, AND")
    parser.add_argument("--summary", help="frontmatter summary substring")
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        help="summary/tags/본문 keyword substring; repeatable, AND",
    )
    parser.add_argument("--limit", type=int, default=20, help="최대 결과 수. 기본 20, 0이면 무제한")
    parser.add_argument("--json", action="store_true", help="emit JSON array")
    return parser.parse_args()


def resolve_log_root(log_root: str | None, config_path: str) -> Path:
    if log_root:
        return Path(log_root).expanduser()
    config = Path(config_path).expanduser()
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
    except OSError:
        raise SystemExit(f"log root를 찾을 수 없음: --log-root를 지정하거나 {config}에 log_root를 설정하라")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON {config}: {exc}") from exc
    value = data.get("log_root") if isinstance(data, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{config}에 log_root가 없음: --log-root를 지정하라")
    return Path(value).expanduser()


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in IGNORED_DIRS or part.startswith(".") for part in path.relative_to(root).parts[:-1]):
            continue
        files.append(path)
    return files


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    meta: dict[str, Any] = {}
    body_start = len(lines)
    list_key: str | None = None
    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() == "---":
            body_start = index + 1
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if list_key is not None and stripped.startswith("- "):
            meta[list_key].append(unquote(stripped[2:]))
            continue
        list_key = None
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", stripped)
        if not match:
            continue
        key, raw_value = match.group(1), match.group(2).strip()
        if raw_value == "":
            meta[key] = []
            list_key = key
        elif raw_value.startswith("[") and raw_value.endswith("]"):
            inner = raw_value[1:-1].strip()
            meta[key] = [unquote(item.strip()) for item in inner.split(",") if item.strip()] if inner else []
        else:
            meta[key] = unquote(raw_value)
    return meta, "\n".join(lines[body_start:])


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def effective_date(meta: dict[str, Any], path: Path) -> str | None:
    raw = meta.get("date")
    if raw is not None:
        text = str(raw).strip()[:10]
        if DATE_RE.match(text):
            return text
    match = FILENAME_DATE_RE.search(path.stem)
    return match.group(1) if match else None


def matches_all_needles(haystack: list[str], needles: list[str]) -> bool:
    values = [value.casefold() for value in haystack]
    return all(any(needle.casefold() in value for value in values) for needle in needles)


def matched_lines(body: str, queries: list[str], limit: int = SNIPPET_LIMIT) -> list[dict[str, Any]]:
    snippets: list[dict[str, Any]] = []
    needles = [query.casefold() for query in queries]
    for number, line in enumerate(body.splitlines(), start=1):
        folded = line.casefold()
        if any(needle in folded for needle in needles):
            snippets.append({"line": number, "text": compact(line, 200)})
            if len(snippets) >= limit:
                break
    return snippets


def match_doc(
    meta: dict[str, Any],
    body: str,
    doc_date: str | None,
    args: argparse.Namespace,
) -> list[dict[str, Any]] | None:
    """Return matched body snippets when the doc passes all filters, else None."""
    if args.date and doc_date not in args.date:
        return None
    if args.since or args.until:
        if doc_date is None:
            return None
        if args.since and doc_date < args.since:
            return None
        if args.until and doc_date > args.until:
            return None
    if args.doc_type and str(meta.get("type") or "") != args.doc_type:
        return None
    tags = coerce_list(meta.get("tags"))
    if args.tag and not matches_all_needles(tags, args.tag):
        return None
    summary = str(meta.get("summary") or "")
    if args.summary and args.summary.casefold() not in summary.casefold():
        return None
    if args.query:
        meta_text = " ".join([summary, *tags]).casefold()
        folded_body = body.casefold()
        for query in args.query:
            needle = query.casefold()
            if needle not in meta_text and needle not in folded_body:
                return None
        return matched_lines(body, args.query)
    return []


def build_row(path: Path, root: Path, meta: dict[str, Any], doc_date: str | None, snippets: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "abs_path": str(path),
        "date": doc_date,
        "type": meta.get("type"),
        "summary": compact(str(meta.get("summary") or ""), 200),
        "tags": coerce_list(meta.get("tags")),
        "matched_lines": snippets,
    }


def print_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No matching work logs.")
        return
    for row in rows:
        tags = ",".join(row["tags"]) or "-"
        summary = row["summary"] or "-"
        print(f"{row['path']}\tdate={row['date'] or '-'}\ttype={row['type'] or '-'}\ttags={tags}\t{summary}")
        for snippet in row["matched_lines"]:
            print(f"  L{snippet['line']}: {snippet['text']}")


def main() -> int:
    args = parse_args()
    root = resolve_log_root(args.log_root, args.config)
    if not root.is_dir():
        raise SystemExit(f"log root가 디렉터리가 아님: {root}")

    rows: list[dict[str, Any]] = []
    for path in iter_markdown_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        meta, body = parse_frontmatter(text)
        doc_date = effective_date(meta, path)
        snippets = match_doc(meta, body, doc_date, args)
        if snippets is None:
            continue
        rows.append(build_row(path, root, meta, doc_date, snippets))

    rows.sort(key=lambda row: (row["date"] or "", row["path"]), reverse=True)
    total = len(rows)
    if args.limit > 0:
        rows = rows[: args.limit]
    if args.json:
        print(json.dumps({"total": total, "results": rows}, ensure_ascii=False, indent=2))
    else:
        print_table(rows)
        if total > len(rows):
            print(f"... {total - len(rows)} more (use --limit 0 to show all)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
