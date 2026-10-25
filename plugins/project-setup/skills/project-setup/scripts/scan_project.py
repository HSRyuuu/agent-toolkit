#!/usr/bin/env python3
"""Read-only scan of a project for project-setup.

Prints a project profile: agent hosts in use, existing harness assets,
repository shape, modules and stacks, build/test commands, doc signals.
The scan never writes files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".next", ".nuxt", ".svelte-kit", ".turbo", ".venv", "venv",
    "__pycache__", "build", "coverage", "dist", "node_modules", "out", "target", "vendor",
    ".gradle", ".idea", ".vscode", ".cache", ".pytest_cache", ".mypy_cache", ".codesight",
}
MANIFESTS = {
    "package.json": "node",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "build.gradle": "jvm-gradle",
    "build.gradle.kts": "jvm-gradle",
    "pom.xml": "jvm-maven",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "Gemfile": "ruby",
    "composer.json": "php",
    "pubspec.yaml": "dart",
}
FRAMEWORK_HINTS = {
    "node": [
        ("next", "Next.js"), ("react", "React"), ("vue", "Vue"), ("nuxt", "Nuxt"),
        ("svelte", "Svelte"), ("@nestjs/core", "NestJS"), ("express", "Express"),
        ("fastify", "Fastify"), ("electron", "Electron"), ("react-native", "React Native"),
        ("expo", "Expo"), ("vite", "Vite"), ("prisma", "Prisma"), ("typeorm", "TypeORM"),
        ("drizzle-orm", "Drizzle"), ("tailwindcss", "Tailwind"), ("typescript", "TypeScript"),
    ],
    "python": [
        ("fastapi", "FastAPI"), ("django", "Django"), ("flask", "Flask"),
        ("sqlalchemy", "SQLAlchemy"), ("alembic", "Alembic"), ("pytest", "pytest"),
    ],
    "jvm-gradle": [
        ("spring-boot", "Spring Boot"), ("org.springframework.boot", "Spring Boot"),
        ("kotlin", "Kotlin"), ("querydsl", "QueryDSL"), ("flyway", "Flyway"),
        ("liquibase", "Liquibase"), ("jpa", "JPA"),
    ],
    "jvm-maven": [
        ("spring-boot", "Spring Boot"), ("kotlin", "Kotlin"), ("flyway", "Flyway"),
        ("liquibase", "Liquibase"), ("jpa", "JPA"),
    ],
    "go": [("gin-gonic", "Gin"), ("labstack/echo", "Echo"), ("gorm", "GORM")],
    "rust": [("axum", "Axum"), ("actix", "Actix"), ("tauri", "Tauri")],
}
# Stacks whose routes build_context_map.py extracts; others get stack names only.
CONTEXT_MAP_FULL = {"Next.js", "Spring Boot", "Express"}
KNOWN_DOCS = ["PROJECT_OVERVIEW.md", "DB_SCHEMA.md", "DEPLOY.md", "DESIGN.md", "ADR.md",
              "SOURCE_MAP.md", "CODEBASE_CONTEXT.md"]
MAPPING_HEADERS = re.compile(r"^##\s+(문서 매핑|Document Map(ping)?)\s*$", re.M)
SKILL_DIRS = [".claude/skills", ".agents/skills", ".codex/skills"]
# Paths under these directory names are samples, tooling or copies, not project modules/docs.
NOISE_PARTS = {"templates", "template", "examples", "example", "fixtures", "__fixtures__", "archived",
               "scripts", "tools", "samples", "testdata", "test-data", "skills", "plugins"}


def walk(root: Path, max_depth: int):
    root_depth = len(root.parts)
    for dirpath, dirs, files in os.walk(root):
        depth = len(Path(dirpath).parts) - root_depth
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (d.startswith(".") and d not in {".github", ".claude", ".codex", ".agents"}))
        if depth >= max_depth:
            dirs[:] = []
        yield Path(dirpath), files


def read(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def rel(path: Path, root: Path) -> str:
    r = path.relative_to(root).as_posix()
    return r or "."


def noisy(path: Path, root: Path) -> bool:
    return any(part in NOISE_PARTS or "archive" in part.lower() for part in path.relative_to(root).parts[:-1])


def hangul_ratio(text: str) -> float:
    letters = re.findall(r"[A-Za-z가-힣]", text)
    if not letters:
        return 0.0
    return sum(1 for c in letters if "가" <= c <= "힣") / len(letters)


def git(root: Path, *args: str) -> str:
    try:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def mapping_entries(text: str) -> dict:
    m = MAPPING_HEADERS.search(text)
    if not m:
        return {"has_mapping": False, "docs": [], "skills": []}
    section = text[m.end():]
    nxt = re.search(r"^##\s", section, re.M)
    section = section[: nxt.start()] if nxt else section
    docs, skills = [], []
    for line in section.splitlines():
        cell = re.match(r"^\|\s*`([^`]+)`", line)
        if not cell:
            continue
        val = cell.group(1).strip()
        if val.startswith("<"):
            continue
        (skills if val.startswith("/") else docs).append(val.lstrip("/") if val.startswith("/") else val)
    return {"has_mapping": True, "docs": docs, "skills": skills}


def node_module(path: Path) -> dict:
    data = {}
    try:
        data = json.loads(read(path))
    except json.JSONDecodeError:
        pass
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    scripts = data.get("scripts", {}) or {}
    d = path.parent
    pm = "npm"
    for lock, name in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun"), ("bun.lock", "bun")):
        if (d / lock).exists() or any((p / lock).exists() for p in d.parents):
            pm = name
            break
    run = "npm run" if pm == "npm" else pm
    commands = {}
    for key in ("dev", "build", "test", "lint", "typecheck", "type-check", "format", "e2e"):
        if key in scripts:
            commands[key] = f"{run} {key}" if not (pm == "npm" and key == "test") else "npm test"
    frameworks = [label for dep, label in FRAMEWORK_HINTS["node"] if dep in deps]
    workspaces = bool(data.get("workspaces"))
    return {"frameworks": frameworks, "commands": commands, "package_manager": pm, "workspaces": workspaces,
            "name": data.get("name")}


def text_module(path: Path, kind: str) -> dict:
    text = read(path).lower()
    frameworks = [label for dep, label in FRAMEWORK_HINTS.get(kind, []) if dep in text]
    d = path.parent
    commands = {}
    if kind == "jvm-gradle":
        g = "./gradlew" if (d / "gradlew").exists() or any((p / "gradlew").exists() for p in d.parents) else "gradle"
        commands = {"build": f"{g} build", "test": f"{g} test"}
    elif kind == "jvm-maven":
        m = "./mvnw" if (d / "mvnw").exists() else "mvn"
        commands = {"build": f"{m} package", "test": f"{m} test"}
    elif kind == "python":
        if "pytest" in text or (d / "tests").is_dir() or (d / "pytest.ini").exists():
            commands["test"] = "pytest"
        if "ruff" in text:
            commands["lint"] = "ruff check ."
    elif kind == "go":
        commands = {"build": "go build ./...", "test": "go test ./..."}
    elif kind == "rust":
        commands = {"build": "cargo build", "test": "cargo test"}
    return {"frameworks": sorted(set(frameworks), key=frameworks.index), "commands": commands}


def make_targets(path: Path) -> list[str]:
    return re.findall(r"^([A-Za-z][\w-]*):(?!=)", read(path), re.M)


def scan(root: Path) -> dict:
    root = root.resolve()
    files_seen: list[Path] = []
    dirs_seen: set[str] = set()
    for d, files in walk(root, 4):
        dirs_seen.add(rel(d, root))
        for f in files:
            files_seen.append(d / f)
    names = {p.name for p in files_seen}
    rels = [rel(p, root) for p in files_seen]

    # Hosts and entrypoints
    entry_paths = ["AGENTS.md", "CLAUDE.md", ".claude/CLAUDE.md"]
    entrypoints = []
    for e in entry_paths:
        p = root / e
        if p.exists():
            t = read(p)
            info = {"path": e, "lines": t.count("\n") + 1, "imports_agents_md": bool(re.search(r"^@AGENTS\.md", t, re.M))}
            info.update(mapping_entries(t))
            entrypoints.append(info)
    hosts = {
        "claude": (root / "CLAUDE.md").exists() or (root / ".claude").is_dir(),
        "codex": (root / "AGENTS.md").exists() or (root / ".codex").is_dir() or (root / ".agents").is_dir(),
    }

    # Existing harness
    skills = {}
    for sd in SKILL_DIRS:
        p = root / sd
        if p.is_dir():
            skills[sd] = sorted(x.name for x in p.iterdir() if (x / "SKILL.md").exists())
    docs_found = {}
    for p in files_seen:
        if p.name in KNOWN_DOCS and not noisy(p, root):
            docs_found.setdefault(p.name, []).append(rel(p, root))
    doc_dirs = sorted({str(Path(v[0]).parent) for v in docs_found.values()})
    lessons = (root / ".claude/LESSONS.md").exists()
    rules_dir = root / ".claude/rules"
    rules = sorted(x.name for x in rules_dir.glob("*.md")) if rules_dir.is_dir() else []

    # Modules
    modules = []
    for p in sorted(files_seen, key=lambda x: (len(x.parts), str(x))):
        kind = MANIFESTS.get(p.name)
        if not kind or noisy(p, root):
            continue
        if p.name == "requirements.txt" and (p.parent / "pyproject.toml").exists():
            continue
        if kind == "jvm-gradle" and p.name == "build.gradle" and (p.parent / "build.gradle.kts").exists():
            continue
        info = node_module(p) if kind == "node" else text_module(p, kind)
        modules.append({"path": rel(p.parent, root), "manifest": p.name, "kind": kind, **info})

    workspace_markers = [m for m in ("pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json") if (root / m).exists()]
    settings_gradle = read(root / "settings.gradle") + read(root / "settings.gradle.kts")
    gradle_includes = re.findall(r"include\s*\(?\s*['\"]([^'\"]+)", settings_gradle)
    if any(m.get("workspaces") for m in modules if m["path"] == "."):
        workspace_markers.append("package.json workspaces")
    module_dirs = {m["path"] for m in modules}
    if workspace_markers or gradle_includes:
        shape = "monorepo"
    elif len(module_dirs - {"."}) >= 2 or (len(module_dirs) >= 2 and "." in module_dirs):
        shape = "multi-module"
    else:
        shape = "single"

    frameworks = sorted({f for m in modules for f in m.get("frameworks", [])})
    make = make_targets(root / "Makefile") if (root / "Makefile").exists() else []

    # Signals
    def any_dir(*cands: str) -> list[str]:
        out = [d for d in dirs_seen if any(d == c or d.endswith("/" + c) for c in cands)]
        return sorted(out)[:8]

    def any_file(pattern: str) -> list[str]:
        rx = re.compile(pattern)
        return sorted(r for r in rels if rx.search(r))[:8]

    signals = {
        "db": any_dir("migrations", "migration", "prisma", "alembic", "db/migrate", "db/migration", "entity", "entities", "models")
              + any_file(r"(schema\.prisma|\.sql)$"),
        "deploy": any_file(r"(^\.github/workflows/.+\.ya?ml$|Dockerfile$|docker-compose\.ya?ml$|vercel\.json$|fly\.toml$|netlify\.toml$|Procfile$|app\.ya?ml$|cloudbuild\.ya?ml$)")
                  + any_dir("k8s", "helm", "terraform", "infra", "deploy"),
        "design": any_file(r"(tailwind\.config\.\w+$|\.storybook/|tokens?\.(json|ts|js|css)$)") + any_dir("theme", "tokens", "design-system"),
        "adr": any_dir("adr", "decisions"),
        "env": any_file(r"(^|/)\.env\.(example|sample|template)$"),
    }

    src_suffixes = {".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".kt", ".go", ".rs", ".vue", ".svelte", ".rb", ".php", ".cs", ".swift", ".dart"}
    source_count = 0
    for _d, fs in walk(root, 14):
        source_count += sum(1 for f in fs if Path(f).suffix in src_suffixes)
        if source_count > 50_000:
            break

    # Language of existing docs
    sample = read(root / "README.md", 20_000)
    for e in entrypoints:
        sample += read(root / e["path"], 20_000)
    for v in docs_found.values():
        sample += read(root / v[0], 10_000)
    ratio = hangul_ratio(sample)
    language = "ko" if ratio >= 0.15 else ("en" if sample.strip() else "unknown")

    base = git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").replace("origin/", "")
    return {
        "root": str(root),
        "git": {"is_repo": bool(git(root, "rev-parse", "--is-inside-work-tree")), "base_branch": base or None},
        "hosts": hosts,
        "entrypoints": entrypoints,
        "existing": {"skills": skills, "docs": docs_found, "doc_dirs": doc_dirs, "lessons": lessons, "rules": rules},
        "shape": shape,
        "workspace_markers": workspace_markers + [f"gradle include {g}" for g in gradle_includes[:10]],
        "modules": modules,
        "frameworks": frameworks,
        "make_targets": make[:20],
        "signals": {k: v for k, v in signals.items()},
        "source_files": source_count,
        "context_map_support": "full" if CONTEXT_MAP_FULL & set(frameworks) else ("partial" if source_count else "none"),
        "doc_language": language,
    }


def to_markdown(p: dict) -> str:
    out = [f"# Project profile: {p['root']}", ""]
    out.append(f"- shape: {p['shape']}" + (f" ({', '.join(p['workspace_markers'])})" if p["workspace_markers"] else ""))
    out.append(f"- hosts: claude={p['hosts']['claude']}, codex={p['hosts']['codex']}")
    out.append(f"- doc language: {p['doc_language']}")
    out.append(f"- base branch: {p['git']['base_branch']}")
    out.append(f"- frameworks: {', '.join(p['frameworks']) or '-'}")
    out.append(f"- source files: {p['source_files']}, context map support: {p['context_map_support']}")
    out += ["", "## Modules", "", "| path | kind | frameworks | commands |", "| --- | --- | --- | --- |"]
    for m in p["modules"]:
        cmds = "; ".join(f"{k}: `{v}`" for k, v in m.get("commands", {}).items()) or "-"
        out.append(f"| `{m['path']}` | {m['kind']} | {', '.join(m.get('frameworks', [])) or '-'} | {cmds} |")
    if p["make_targets"]:
        out.append(f"\nMakefile targets: {', '.join(p['make_targets'])}")
    out += ["", "## Existing harness", ""]
    for e in p["entrypoints"]:
        out.append(f"- entrypoint `{e['path']}` ({e['lines']} lines) mapping={e['has_mapping']} docs={e['docs']} skills={e['skills']}" + (" imports @AGENTS.md" if e["imports_agents_md"] else ""))
    if not p["entrypoints"]:
        out.append("- entrypoint: none")
    for d, names in p["existing"]["skills"].items():
        out.append(f"- skills in `{d}`: {', '.join(names) or '-'}")
    for name, paths in p["existing"]["docs"].items():
        out.append(f"- doc {name}: {', '.join(paths)}")
    out.append(f"- LESSONS.md: {p['existing']['lessons']}")
    out.append(f"- .claude/rules: {', '.join(p['existing']['rules']) or '-'}")
    out += ["", "## Signals", ""]
    for k, v in p["signals"].items():
        out.append(f"- {k}: {', '.join(v) if v else '-'}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project_root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    args = ap.parse_args()
    root = Path(args.project_root)
    if not root.is_dir():
        print(f"not a directory: {root}")
        return 2
    profile = scan(root)
    print(json.dumps(profile, ensure_ascii=False, indent=2) if args.json else to_markdown(profile))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
