#!/usr/bin/env python3
"""Regenerate the Documents catalog in index.md from document frontmatter.

The generated table lives between marker comments so a human-written preamble
(title, "Start Here", folder guidance) is preserved across regenerations:

    <!-- kb:documents:start -->
    ...generated tables...
    <!-- kb:documents:end -->

Modes:
    (default)   print the spliced index.md to stdout
    --write     write the result back to index.md
    --check     exit 1 if index.md is out of date (no write); for lint/CI

Reuses the shared frontmatter loader from the kb-search scripts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Import contract: see kb-manage/references/conventions.md (Script Paths).
SEARCH_SCRIPTS = Path(__file__).resolve().parents[2] / "kb-search" / "scripts"
sys.path.insert(0, str(SEARCH_SCRIPTS))

from kb_frontmatter import KbDoc, coerce_list, load_docs, normalize_date  # noqa: E402

START = "<!-- kb:documents:start -->"
END = "<!-- kb:documents:end -->"

# Root entrypoints and folder notes never belong in the document catalog.
SKIP_NAMES = {"index.md", "readme.md", "agents.md", "claude.md"}


def is_catalog_doc(doc: KbDoc) -> bool:
    if doc.path.name.lower() in SKIP_NAMES:
        return False
    # A catalog entry needs at least a title or summary to be meaningful.
    return bool(doc.metadata.get("title") or doc.metadata.get("summary"))


def bucket(doc: KbDoc) -> str:
    top = doc.relpath.split("/", 1)[0]
    if top == "_archived":
        return "archived"
    if top == "_inbox":
        return "inbox"
    return "documents"


def cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def row(doc: KbDoc) -> str:
    title = cell(str(doc.metadata.get("title") or doc.path.stem))
    summary = cell(str(doc.metadata.get("summary") or ""))
    tags = " ".join(f"`{cell(t)}`" for t in coerce_list(doc.metadata.get("tags")))
    updated = normalize_date(doc.metadata.get("updated")) or "-"
    return f"| [{title}](./{doc.relpath}) | {summary} | {tags} | {updated} |"


def table(docs: list[KbDoc]) -> str:
    header = "| Document | Summary | Tags | Updated |\n|---|---|---|---|"
    if not docs:
        return header + "\n| _(none)_ | | | |"
    body = "\n".join(row(d) for d in sorted(docs, key=lambda d: d.relpath))
    return header + "\n" + body


def build_block(root: Path) -> str:
    docs = [d for d in load_docs(root) if is_catalog_doc(d)]
    buckets: dict[str, list[KbDoc]] = {"documents": [], "inbox": [], "archived": []}
    for doc in docs:
        buckets[bucket(doc)].append(doc)

    parts = ["## Documents", "", table(buckets["documents"]), ""]
    if buckets["inbox"]:
        parts += ["## Inbox", "", table(buckets["inbox"]), ""]
    if buckets["archived"]:
        parts += ["## Archived", "", table(buckets["archived"]), ""]
    return "\n".join(parts).rstrip() + "\n"


def default_preamble() -> str:
    return (
        "# Knowledge Base Index\n\n"
        "이 문서는 KB의 문서 카탈로그이다. 자세한 사실은 각 원문 문서를 기준으로 확인한다.\n\n"
    )


def splice(existing: str | None, block: str) -> str:
    # `block` ends with a newline, so wrapped is `START\n...\nEND` (no trailing
    # newline); callers add exactly one, keeping regeneration idempotent.
    wrapped = f"{START}\n{block}{END}"
    if existing is None:
        return default_preamble() + wrapped + "\n"

    if START in existing and END in existing:
        pre, rest = existing.split(START, 1)
        _, post = rest.split(END, 1)
        return f"{pre}{wrapped}{post}"

    marker = "\n## Documents"
    if marker in existing:
        pre = existing.split(marker, 1)[0].rstrip() + "\n\n"
        return f"{pre}{wrapped}\n"

    return existing.rstrip() + "\n\n" + wrapped + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate index.md Documents catalog from frontmatter.")
    parser.add_argument("root", nargs="?", default=".", help="KB root directory")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="write the result back to index.md")
    group.add_argument("--check", action="store_true", help="exit 1 if index.md is out of date")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    index_path = root / "index.md"
    existing = index_path.read_text(encoding="utf-8") if index_path.exists() else None

    block = build_block(root)
    result = splice(existing, block)

    if args.check:
        if existing != result:
            print("index.md is out of date; run kb_build_index.py --write", file=sys.stderr)
            return 1
        print("index.md is up to date.")
        return 0

    if args.write:
        index_path.write_text(result, encoding="utf-8")
        print(f"Wrote {index_path}")
        return 0

    print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
