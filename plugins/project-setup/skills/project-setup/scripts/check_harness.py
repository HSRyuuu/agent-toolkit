#!/usr/bin/env python3
"""Read-only check that a project's agent harness is wired together.

Checks the contract in references/harness-contract.md: entrypoint and its
document map, mapped paths exist, registered skills exist, installed skills
are well formed, no installer placeholders are left, and paired assets
(LESSONS rule, sync-docs rule, manage-skills + verify-implementation) agree.

Prints one line per finding: [ERROR] / [WARN] / [INFO]. Exit 1 on any ERROR.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ENTRYPOINTS = ["AGENTS.md", "CLAUDE.md", ".claude/CLAUDE.md"]
SKILL_DIRS = [".claude/skills", ".agents/skills", ".codex/skills"]
MAPPING = re.compile(r"^##\s+(문서 매핑|Document Map(ping)?)\s*$", re.M)
# Placeholders the installer must replace. Doc templates may keep <...> prompts for humans.
HARD_PLACEHOLDERS = re.compile(r"(?<!\$)\{[A-Z][A-Z0-9_]+\}|<skill-name>|<path/to/doc\.md>|<한 줄 설명>")
# Tokens the installer substitutes inside skill templates (skill bodies may mention <...> as prose).
INSTALL_TOKEN = re.compile(r"(?<!\$)\{[A-Z][A-Z0-9_]+\}")
SOFT_PLACEHOLDER = re.compile(r"<[^<>\n]{2,60}>")


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def mapping(text: str):
    m = MAPPING.search(text)
    if not m:
        return None
    sec = text[m.end():]
    nxt = re.search(r"^##\s", sec, re.M)
    sec = sec[: nxt.start()] if nxt else sec
    docs, skills = [], []
    for line in sec.splitlines():
        c = re.match(r"^\|\s*`([^`]+)`", line)
        if not c:
            continue
        v = c.group(1).strip()
        if v.startswith("/"):
            skills.append(v[1:].split()[0])
        else:
            docs.append(v)
    return docs, skills


def frontmatter_name(text: str) -> str | None:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    n = re.search(r"^name:\s*(\S+)", m.group(1), re.M)
    return n.group(1).strip("\"'") if n else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project_root", nargs="?", default=".")
    root = Path(ap.parse_args().project_root).resolve()
    out: list[tuple[str, str]] = []
    add = lambda lvl, msg: out.append((lvl, msg))  # noqa: E731

    entries = {e: read(root / e) for e in ENTRYPOINTS if (root / e).exists()}
    if not entries:
        add("WARN", "진입점(AGENTS.md / CLAUDE.md / .claude/CLAUDE.md)이 없다. 매핑 표가 없으면 sync-docs가 동작하지 않는다.")

    installed: dict[str, Path] = {}
    for sd in SKILL_DIRS:
        d = root / sd
        if not d.is_dir():
            continue
        for s in sorted(d.iterdir()):
            f = s / "SKILL.md"
            if not f.exists():
                continue
            installed.setdefault(s.name, f)
            t = read(f)
            name = frontmatter_name(t)
            if name is None:
                add("ERROR", f"{sd}/{s.name}/SKILL.md: frontmatter name이 없다")
            elif name != s.name:
                add("ERROR", f"{sd}/{s.name}/SKILL.md: name '{name}'이 디렉토리 이름과 다르다")
            hit = INSTALL_TOKEN.search(t)
            if hit:
                add("ERROR", f"{sd}/{s.name}/SKILL.md: 설치 placeholder가 남아 있다 ({hit.group(0)})")
    names = {sd: {p.name for p in (root / sd).iterdir() if (p / "SKILL.md").exists()} for sd in SKILL_DIRS if (root / sd).is_dir()}
    names = {k: v for k, v in names.items() if v}
    if len(names) > 1:
        sets = list(names.values())
        if any(s != sets[0] for s in sets[1:]):
            add("INFO", "호스트별 스킬 디렉토리의 스킬 목록이 다르다: " + "; ".join(f"{k}={sorted(v)}" for k, v in names.items()))

    mapped_docs: set[str] = set()
    mapped_skills: set[str] = set()
    has_mapping = False
    canonical = None
    for e, text in entries.items():
        if re.search(r"^@AGENTS\.md", text, re.M) and "AGENTS.md" in entries:
            add("INFO", f"{e}는 @AGENTS.md를 가져온다. AGENTS.md가 정본이다.")
            continue
        if HARD_PLACEHOLDERS.search(text):
            add("ERROR", f"{e}: 설치 placeholder가 남아 있다 ({HARD_PLACEHOLDERS.search(text).group(0)})")
        mp = mapping(text)
        if mp is None:
            add("WARN", f"{e}: '## 문서 매핑' 섹션이 없다")
            continue
        docs, skills = mp
        has_mapping = True
        if canonical is not None and (set(docs) != mapped_docs or set(skills) != mapped_skills):
            add("WARN", f"{e}와 {canonical}의 매핑 표가 다르다. 한쪽을 정본으로 정하거나 같게 맞춘다.")
        canonical = canonical or e
        mapped_docs |= set(docs)
        mapped_skills |= set(skills)
        base = (root / e).parent
        for d in docs:
            if not ((root / d).exists() or (base / d).exists()):
                add("ERROR", f"{e}: 매핑된 문서가 없다: {d}")
        for s in skills:
            if s not in installed:
                add("WARN", f"{e}: 매핑된 스킬이 프로젝트 스킬 디렉토리에 없다: /{s} (전역·plugin 스킬이면 무시)")

    for name in installed:
        if has_mapping and name not in mapped_skills:
            add("WARN", f"설치된 스킬 /{name}이 문서 매핑 표에 없다")

    # Mapped docs: count unfilled prompts so the user knows what is left.
    for d in sorted(mapped_docs):
        p = root / d
        if p.is_file():
            t = read(p)
            if re.search(r"\{PROJECT_NAME\}", t):
                add("ERROR", f"{d}: {{PROJECT_NAME}}이 그대로 있다")
            n = len(SOFT_PLACEHOLDER.findall(re.sub(r"```.*?```", "", t, flags=re.S)))
            if n:
                add("INFO", f"{d}: 채워지지 않은 <...> 항목 {n}개")

    all_entry = "\n".join(entries.values())
    # Rule lines live outside tables; a mapping row alone does not tell the agent when to act.
    prose = "\n".join(l for l in all_entry.splitlines() if not l.lstrip().startswith("|"))
    if (root / ".claude/LESSONS.md").exists() and "LESSONS" not in prose:
        add("ERROR", ".claude/LESSONS.md가 있지만 진입점에 읽고 기록하라는 규칙이 없다")
    if "sync-docs" in installed:
        if not mapped_docs:
            add("ERROR", "sync-docs가 설치됐지만 매핑된 문서가 없다")
        if "sync-docs" not in prose:
            add("ERROR", "sync-docs가 설치됐지만 진입점에 실행 규칙이 없다")
    if "update-project-docs" in installed and "sync-docs" not in installed:
        add("INFO", "구 이름 update-project-docs가 설치돼 있다. sync-docs로 교체할 수 있다.")
    pair = {"manage-skills", "verify-implementation"}
    if len(pair & set(installed)) == 1:
        add("WARN", "manage-skills와 verify-implementation 중 하나만 설치돼 있다. 둘은 짝으로 동작한다.")
    ms = installed.get("manage-skills")
    if ms is not None:
        body = read(ms)
        sec = re.search(r"^##\s+(등록된 검증 스킬|Registered Verify Skills)\s*$(.*?)(?=^##\s)", body, re.M | re.S)
        registered = set(re.findall(r"^\|\s*`?(verify-[\w-]+)`?\s*\|", sec.group(2), re.M)) if sec else set()
        actual = {n for n in installed if n.startswith("verify-") and n != "verify-implementation"}
        for n in sorted(actual - registered):
            add("WARN", f"manage-skills 등록 표에 없는 verify 스킬: {n}")
        for n in sorted(registered - actual):
            add("WARN", f"manage-skills 등록 표에 있지만 설치되지 않은 스킬: {n}")

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for lvl, msg in sorted(out, key=lambda x: order[x[0]]):
        print(f"[{lvl}] {msg}")
    errors = sum(1 for lvl, _ in out if lvl == "ERROR")
    print("OK" if not errors else f"FAIL ({errors} error)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
