#!/usr/bin/env python3
"""Generate lightweight agent navigation files for a codebase."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "vendor",
}

SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
    ".svelte",
}

CONFIG_NAMES = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "package.json",
    "pnpm-workspace.yaml",
    "turbo.json",
    "vite.config.ts",
    "vite.config.js",
    "next.config.ts",
    "next.config.js",
    "nuxt.config.ts",
    "tailwind.config.ts",
    "tailwind.config.js",
    "tsconfig.json",
    "pyproject.toml",
    "requirements.txt",
    "poetry.lock",
    "Pipfile",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    return data[:limit]


def list_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        files = [root / line for line in result.stdout.splitlines() if line.strip()]
        if files:
            return [p for p in files if p.is_file() and not is_skipped(p, root)]
    except (OSError, subprocess.CalledProcessError):
        pass

    files: list[Path] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".cache")]
        for name in names:
            path = Path(current) / name
            if path.is_file() and not is_skipped(path, root):
                files.append(path)
    return sorted(files)


def is_skipped(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    return any(part in SKIP_DIRS for part in parts)


def detect_stack(files: list[Path], root: Path) -> list[str]:
    names = {p.name for p in files}
    rels = {rel(p, root) for p in files}
    stack: list[str] = []
    if "package.json" in names:
        stack.append("Node/JavaScript")
    if "next.config.js" in names or "next.config.ts" in names or any("/app/" in f for f in rels):
        stack.append("Next.js")
    if "vite.config.ts" in names or "vite.config.js" in names:
        stack.append("Vite")
    if any(p.suffix in {".tsx", ".jsx"} for p in files):
        stack.append("React")
    if "pyproject.toml" in names or "requirements.txt" in names:
        stack.append("Python")
    if "go.mod" in names:
        stack.append("Go")
    if "Cargo.toml" in names:
        stack.append("Rust")
    if "pom.xml" in names or "build.gradle" in names or "build.gradle.kts" in names:
        stack.append("Java/Spring")
    return dedupe(stack)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def next_route_from_app(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts
    if "app" not in parts or path.name not in {"page.tsx", "page.jsx", "page.ts", "page.js", "layout.tsx", "layout.jsx"}:
        return None
    app_index = parts.index("app")
    route_parts = list(parts[app_index + 1 : -1])
    visible = [p for p in route_parts if not (p.startswith("(") and p.endswith(")")) and not p.startswith("_")]
    route = "/" + "/".join(visible)
    return route.rstrip("/") or "/"


def next_route_from_pages(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts
    if "pages" not in parts or path.suffix not in {".js", ".jsx", ".ts", ".tsx"}:
        return None
    pages_index = parts.index("pages")
    route_parts = list(parts[pages_index + 1 :])
    if route_parts and route_parts[-1].startswith("index."):
        route_parts = route_parts[:-1]
    else:
        route_parts[-1] = Path(route_parts[-1]).stem
    if route_parts and route_parts[0] == "api":
        return None
    route = "/" + "/".join(route_parts)
    return route.rstrip("/") or "/"


def spring_routes(path: Path) -> list[str]:
    text = read_text(path)
    if "@RestController" not in text and "@Controller" not in text:
        return []
    class_prefix = extract_annotation_path(text, "RequestMapping") or ""
    routes: list[str] = []
    for ann in ["GetMapping", "PostMapping", "PutMapping", "PatchMapping", "DeleteMapping", "RequestMapping"]:
        for match in re.finditer(rf"@{ann}\s*(?:\(([^)]*)\))?", text):
            value = extract_path_value(match.group(1) or "")
            if ann == "RequestMapping" and match.start() < text.find("class "):
                continue
            method = ann.replace("Mapping", "").upper() or "REQUEST"
            full = join_route(class_prefix, value)
            routes.append(f"{method} {full}")
    return dedupe(routes)


def extract_annotation_path(text: str, annotation: str) -> str | None:
    match = re.search(rf"@{annotation}\s*\(([^)]*)\)", text)
    if not match:
        return None
    return extract_path_value(match.group(1))


def extract_path_value(args: str) -> str:
    match = re.search(r'["\']([^"\']+)["\']', args)
    return match.group(1) if match else ""


def join_route(prefix: str, path: str) -> str:
    combined = "/".join([prefix.strip("/"), path.strip("/")]).strip("/")
    return "/" + combined if combined else "/"


def js_routes(path: Path) -> list[str]:
    text = read_text(path)
    routes: list[str] = []
    for match in re.finditer(r"\b(get|post|put|patch|delete|all)\s*\(\s*['\"]([^'\"]+)['\"]", text, re.I):
        routes.append(f"{match.group(1).upper()} {match.group(2)}")
    for match in re.finditer(r"\b(app|router)\.(get|post|put|patch|delete|all)\s*\(\s*['\"]([^'\"]+)['\"]", text, re.I):
        routes.append(f"{match.group(2).upper()} {match.group(3)}")
    return dedupe(routes)


def classify(files: list[Path], root: Path) -> dict[str, list[tuple[str, str, str]]]:
    data: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for path in files:
        r = rel(path, root)
        name = path.name
        stem_lower = path.stem.lower()
        lower = r.lower()

        app_route = next_route_from_app(path, root)
        pages_route = next_route_from_pages(path, root)
        if app_route and name.startswith("page."):
            data["frontend_routes"].append((app_route, r, "Next app route"))
        if app_route and name.startswith("layout."):
            data["frontend_layouts"].append((r, r, "Next app layout"))
        if pages_route:
            data["frontend_routes"].append((pages_route, r, "Next pages route"))

        if path.suffix in {".tsx", ".jsx", ".vue", ".svelte"} and (
            "/components/" in f"/{lower}" or "/_components/" in f"/{lower}" or name[:1].isupper()
        ):
            data["components"].append((r, r, component_description(path)))

        if "/lib/api/" in f"/{lower}" or "/api/" in f"/{lower}" and path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
            data["api_clients"].append((r, r, "API client or API route helper"))

        if path.suffix == ".java" or path.suffix == ".kt":
            if "controller" in stem_lower or "controller/" in lower:
                routes = spring_routes(path)
                data["controllers"].append((r, r, ", ".join(routes[:4]) if routes else "HTTP entrypoint"))
            elif "service" in stem_lower or "service/" in lower:
                data["services"].append((r, r, "Business logic"))
            elif "repository" in stem_lower or "repository/" in lower:
                data["repositories"].append((r, r, "Data access"))
            elif any(key in stem_lower or f"/{key}/" in lower for key in ["entity", "model", "domain"]):
                data["models"].append((r, r, "Domain model"))
            elif "dto" in stem_lower or "/dto/" in lower:
                data["dtos"].append((r, r, "Request/response DTO"))

        if path.suffix in {".js", ".ts", ".mjs", ".cjs"}:
            for route in js_routes(path):
                data["backend_routes"].append((route, r, "JS route handler"))

        if any(token in lower for token in ["schema", "migration", "migrations", "prisma", "alembic", "flyway", "liquibase"]):
            if path.suffix in {".sql", ".prisma", ".ts", ".js", ".py", ".java", ".kt", ".xml", ".yaml", ".yml"}:
                data["schema"].append((r, r, "Schema or migration"))

        if name in CONFIG_NAMES or lower.startswith(".github/workflows/") or lower.startswith("config/") or "/config/" in lower:
            data["config"].append((r, r, "Configuration"))

        if any(part in lower for part in ["auth", "middleware", "security", "exception", "error"]):
            if path.suffix in SOURCE_SUFFIXES:
                data["common"].append((r, r, "Cross-cutting concern"))

        if any(part in lower for part in ["test", "spec", "e2e", "__tests__"]):
            if path.suffix in SOURCE_SUFFIXES:
                data["tests"].append((r, r, "Test or scenario"))

    return {k: dedupe_rows(v) for k, v in data.items()}


def component_description(path: Path) -> str:
    text = read_text(path, 20_000)
    flags = []
    if '"use client"' in text or "'use client'" in text:
        flags.append("client")
    props = re.search(r"(?:interface|type)\s+([A-Z][A-Za-z0-9_]*Props)\b", text)
    if props:
        flags.append(f"props: {props.group(1)}")
    return "UI component" + (f" ({', '.join(flags)})" if flags else "")


def dedupe_rows(rows: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str, str]] = []
    for row in rows:
        key = (row[0], row[1])
        if key not in seen:
            seen.add(key)
            out.append(row)
    return sorted(out, key=lambda row: row[1])


def import_counts(files: list[Path], root: Path) -> list[tuple[str, int]]:
    by_stem: dict[str, str] = {}
    by_no_ext_rel: dict[str, str] = {}
    for path in files:
        if path.suffix in SOURCE_SUFFIXES:
            rel_path = rel(path, root)
            by_stem[path.stem] = rel_path
            by_no_ext_rel[str(path.with_suffix("").relative_to(root).as_posix())] = rel_path

    counts: Counter[str] = Counter()
    import_re = re.compile(r"(?:from\s+['\"]([^'\"]+)['\"]|import\s+.*?from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))")
    for path in files:
        if path.suffix not in SOURCE_SUFFIXES:
            continue
        for match in import_re.finditer(read_text(path, 80_000)):
            spec = next((g for g in match.groups() if g), "")
            if spec.startswith("."):
                target = (path.parent / spec).resolve()
                try:
                    rel_target = target.relative_to(root.resolve()).as_posix()
                    resolved = by_no_ext_rel.get(rel_target, rel_target)
                    if (root / resolved).exists():
                        counts[resolved] += 1
                except ValueError:
                    pass
            else:
                stem = Path(spec).name
                if stem in by_stem:
                    counts[by_stem[stem]] += 1
    return counts.most_common(12)


def preserve_manual_notes(existing: Path) -> str:
    if not existing.exists():
        return "## Manual Notes\n\nAdd human-only routing notes here. The generator preserves this section on refresh.\n"
    text = read_text(existing)
    match = re.search(r"^## Manual Notes\b.*", text, re.M | re.S)
    if match:
        return match.group(0).rstrip() + "\n"
    return "## Manual Notes\n\nAdd human-only routing notes here. The generator preserves this section on refresh.\n"


def table(headers: list[str], rows: list[tuple[str, str, str]], limit: int = 40) -> str:
    if not rows:
        return "_No entries detected._\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(f"`{cell}`" if i < 2 else cell for i, cell in enumerate(row)) + " |")
    if len(rows) > limit:
        lines.append(f"| _...{len(rows) - limit} more_ |  |  |")
    return "\n".join(lines) + "\n"


def render_source_map(root: Path, files: list[Path], data: dict[str, list[tuple[str, str, str]]], manual: str) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    stack = ", ".join(detect_stack(files, root)) or "unknown"
    hot = [(path, path, f"Imported by {count} files") for path, count in import_counts(files, root)]
    source_count = sum(1 for p in files if p.suffix in SOURCE_SUFFIXES)
    return f"""# {root.name} Source Map

> Source navigation map for coding agents.
> Paths are relative to the project root.
> Generated: {now}
> Stack hints: {stack}
> Source files scanned: {source_count}

## Reading Policy

1. Use this file to find likely source locations.
2. Read actual source files before implementing or changing behavior.
3. Treat generated sections as routing hints, not source of truth.
4. Put context the generator cannot infer under `## Manual Notes`.

## Frontend Routes

{table(["Route", "File", "Description"], data.get("frontend_routes", []))}
## Frontend Layouts

{table(["File", "Path", "Description"], data.get("frontend_layouts", []))}
## Components

{table(["Component/File", "Path", "Description"], data.get("components", []), limit=60)}
## API Clients And Helpers

{table(["File", "Path", "Description"], data.get("api_clients", []))}
## Backend Routes

{table(["Route", "File", "Description"], data.get("backend_routes", []))}
## Controllers

{table(["Name/File", "Path", "Description"], data.get("controllers", []))}
## Services

{table(["Name/File", "Path", "Description"], data.get("services", []))}
## Repositories

{table(["Name/File", "Path", "Description"], data.get("repositories", []))}
## Models And DTOs

{table(["Name/File", "Path", "Description"], data.get("models", []) + data.get("dtos", []))}
## Schema And Migrations

{table(["File", "Path", "Description"], data.get("schema", []))}
## Common Auth Middleware Config

{table(["File", "Path", "Description"], data.get("common", []) + data.get("config", []), limit=60)}
## Tests

{table(["File", "Path", "Description"], data.get("tests", []), limit=60)}
## High Impact Files

{table(["File", "Path", "Description"], hot)}
{manual}
"""


def render_context(root: Path, files: list[Path], data: dict[str, list[tuple[str, str, str]]], codesight_ran: bool) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    codesight = root / ".codesight"
    wiki_index = codesight / "wiki" / "index.md"
    stack = ", ".join(detect_stack(files, root)) or "unknown"
    counts = {key: len(value) for key, value in data.items()}
    codesight_line = "present" if codesight.exists() else "not present"
    if codesight_ran:
        codesight_line += " (refreshed during this run)"
    return f"""# {root.name} Codebase Context

> Generated: {now}
> Stack hints: {stack}

## Agent Read Order

For narrow tasks:

1. `docs/SOURCE_MAP.md`
2. `.codesight/wiki/index.md` if present
3. one relevant `.codesight/wiki/*.md` article if useful
4. actual source files

For broad architecture questions:

1. `docs/CODEBASE_CONTEXT.md`
2. `.codesight/CODESIGHT.md` if present
3. actual source files for implementation-sensitive claims

## Generated Inventory

| Signal | Count |
| --- | ---: |
| Files scanned | {len(files)} |
| Frontend routes | {counts.get("frontend_routes", 0)} |
| Components | {counts.get("components", 0)} |
| Backend route hints | {counts.get("backend_routes", 0)} |
| Controllers | {counts.get("controllers", 0)} |
| Services | {counts.get("services", 0)} |
| Repositories | {counts.get("repositories", 0)} |
| Models/DTOs | {counts.get("models", 0) + counts.get("dtos", 0)} |
| Schema/migration files | {counts.get("schema", 0)} |
| Tests | {counts.get("tests", 0)} |

## Codesight

Status: {codesight_line}

| File | Use |
| --- | --- |
| `.codesight/wiki/index.md` | Start here for targeted Codesight navigation |
| `.codesight/CODESIGHT.md` | Use for broad generated architecture context |
| `.codesight/graph.md` | Use for import impact hints |

Wiki index exists: `{str(wiki_index.relative_to(root)) if wiki_index.exists() else "no"}`

## Staleness Rule

Generated maps help choose files to read. Before editing, verify behavior against actual source files.
"""


def run_codesight(root: Path) -> bool:
    try:
        subprocess.run(["npx", "-y", "codesight", "--wiki"], cwd=root, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", nargs="?", default=".", help="Project root to scan")
    parser.add_argument("--output-dir", default="docs", help="Output directory relative to project root")
    parser.add_argument("--run-codesight", action="store_true", help="Run npx codesight --wiki before writing docs")
    parser.add_argument("--dry-run", action="store_true", help="Print target paths without writing files")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        raise SystemExit(f"Project root not found: {root}")

    codesight_ran = run_codesight(root) if args.run_codesight else False
    files = list_files(root)
    data = classify(files, root)
    out_dir = root / args.output_dir
    source_map_path = out_dir / "SOURCE_MAP.md"
    context_path = out_dir / "CODEBASE_CONTEXT.md"
    manual = preserve_manual_notes(source_map_path)

    source_map = render_source_map(root, files, data, manual)
    context = render_context(root, files, data, codesight_ran)

    if args.dry_run:
        print(source_map_path)
        print(context_path)
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    source_map_path.write_text(source_map, encoding="utf-8")
    context_path.write_text(context, encoding="utf-8")
    print(f"Wrote {source_map_path}")
    print(f"Wrote {context_path}")
    if args.run_codesight and not codesight_ran:
        print("WARNING: codesight refresh failed or npx/codesight is unavailable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
