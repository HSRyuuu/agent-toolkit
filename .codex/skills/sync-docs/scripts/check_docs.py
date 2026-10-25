#!/usr/bin/env python3
"""agent-toolkit의 문서·manifest 정합성을 읽기 전용으로 검사한다.

사용: python3 .claude/skills/sync-docs/scripts/check_docs.py  (repo 루트에서)
출력: 문제마다 한 줄 `[분류] 설명`. 문제가 없으면 `OK` 한 줄, 종료 코드 0.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
problems = []


def bad(kind, msg):
    problems.append(f"[{kind}] {msg}")


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


def frontmatter(path):
    parts = path.read_text(encoding="utf-8").split("---")
    return parts[1] if len(parts) > 2 else ""


# 1. 실제 상태 ---------------------------------------------------------------
plugins = sorted(p.name for p in (ROOT / "plugins").iterdir() if p.is_dir())
skills = sorted(
    (m.parent.parent.parent.name, m.parent.name)
    for m in (ROOT / "plugins").glob("*/skills/*/SKILL.md")
)
skill_names = sorted({s for _, s in skills})

# 2. manifest / marketplace --------------------------------------------------
for path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
    try:
        data = json.loads(read(path))
    except Exception as e:  # noqa: BLE001
        bad("json", f"{path}: {e}")
        continue
    listed = sorted(x["name"] for x in data["plugins"])
    for n in sorted(set(plugins) - set(listed)):
        bad("marketplace", f"{path}에 없는 plugin: {n}")
    for n in sorted(set(listed) - set(plugins)):
        bad("marketplace", f"{path}에 있지만 plugins/에 없는 plugin: {n}")
    if path.startswith(".claude") and any("version" in x for x in data["plugins"]):
        bad("marketplace", f"{path}의 plugins[]에 version이 있다")

for p in plugins:
    versions = {}
    for host in (".claude-plugin", ".codex-plugin"):
        mp = ROOT / "plugins" / p / host / "plugin.json"
        if not mp.exists():
            bad("manifest", f"plugins/{p}/{host}/plugin.json 없음")
            continue
        try:
            m = json.loads(mp.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            bad("json", f"{mp.relative_to(ROOT)}: {e}")
            continue
        versions[host] = m.get("version")
        if m.get("name") != p:
            bad("manifest", f"plugins/{p}/{host}: name={m.get('name')!r}가 디렉토리명과 다름")
    if len(set(versions.values())) > 1:
        bad("version", f"{p}: 두 manifest의 version이 다름 {versions}")

# 3. SKILL.md frontmatter ----------------------------------------------------
for plugin, skill in skills:
    fm = frontmatter(ROOT / "plugins" / plugin / "skills" / skill / "SKILL.md")
    if not re.search(r"^name:\s*\S", fm, re.M) or not re.search(r"^description:", fm, re.M):
        bad("skill", f"plugins/{plugin}/skills/{skill}: frontmatter에 name/description 없음")
    elif not re.search(rf"^name:\s*{re.escape(skill)}\s*$", fm, re.M):
        bad("skill", f"plugins/{plugin}/skills/{skill}: name이 디렉토리명과 다름")

# 4. docs/catalog.md ---------------------------------------------------------
catalog = read("docs/catalog.md")
rows = re.findall(r"^\| `([^`]+)` \| \[([^\]]+)\]\(([^)]+)\)", catalog, re.M)
row_set = {(p, s) for p, s, _ in rows}
for p, s in skills:
    if (p, s) not in row_set:
        bad("catalog", f"docs/catalog.md에 행 없음: {p} / {s}")
for p, s in sorted(row_set - set(skills)):
    bad("catalog", f"docs/catalog.md에 있지만 실제로 없는 스킬: {p} / {s}")
for _, _, link in rows:
    if not (ROOT / "docs" / link).resolve().exists():
        bad("catalog", f"깨진 링크: {link}")
m = re.search(r"Plugins under `plugins/` \| (\d+)", catalog)
if not m or int(m.group(1)) != len(plugins):
    bad("catalog", f"plugin 개수 {m.group(1) if m else '?'} != 실제 {len(plugins)}")
m = re.search(r"Skills under `plugins/\*/skills/` \| (\d+)", catalog)
if not m or int(m.group(1)) != len(skills):
    bad("catalog", f"skill 개수 {m.group(1) if m else '?'} != 실제 {len(skills)}")

# 5. HELP.md: 모든 plugin과 skill 이름이 들어 있어야 한다 ----------------------
help_md = read("HELP.md") if (ROOT / "HELP.md").exists() else ""
if not help_md:
    bad("help", "HELP.md 없음")
for n in sorted(set(plugins) | set(skill_names)):
    if f"`{n}`" not in help_md and help_md:
        bad("help", f"HELP.md에 언급 없음: {n}")

# 6. 문서가 가리키는 경로가 실제로 있는가 -----------------------------------
doc_files = ["README.md", "AGENTS.md", ".claude/CLAUDE.md", "HELP.md", "docs/how-to-install.md", "archived/README.md"]
for d in doc_files:
    if not (ROOT / d).exists():
        bad("doc", f"{d} 없음")
        continue
    text = read(d)
    for ref in sorted(set(re.findall(r"`((?:plugins|old|scripts|templates|\.claude|\.codex|\.agents|docs)/[A-Za-z0-9_./*-]+)`", text))):
        if "*" in ref or ref.endswith("/"):
            ref = ref.rstrip("/")
            if "*" in ref:
                continue
        if not (ROOT / ref).exists():
            bad("path", f"{d}: 존재하지 않는 경로 `{ref}`")

# 7. 옮겨진 스킬을 현재 plugin처럼 쓰고 있지 않은가 ---------------------------
archived_skills = {p.parent.name for p in (ROOT / "archived").glob("**/SKILL.md")}
for d in doc_files + ["docs/catalog.md"]:
    if not (ROOT / d).exists() or d == "archived/README.md":
        continue
    for line in read(d).splitlines():
        for n in archived_skills:
            if re.search(rf"\| `{re.escape(n)}` \|", line) or f"plugins/{n}" in line:
                bad("archived", f"{d}: archived/에 있는 스킬을 현재 것처럼 참조 `{n}`")

# 8. 로컬 스킬: Claude/Codex 사본 이름이 같은가 ------------------------------
local = {h: sorted(p.name for p in (ROOT / h / "skills").glob("*/") if (p / "SKILL.md").exists())
         for h in (".claude", ".codex")}
if local[".claude"] != local[".codex"]:
    bad("local", f".claude/skills {local['.claude']} != .codex/skills {local['.codex']}")
if (ROOT / "archived").exists():
    archived_dirs = sorted(p.name for p in (ROOT / "archived").iterdir() if p.is_dir())
    archivedrd = read("archived/README.md") if (ROOT / "archived/README.md").exists() else ""
    for n in archived_dirs:
        if f"`{n}/`" not in archivedrd and f"`archived/{n}" not in archivedrd and n not in archivedrd:
            bad("archived", f"archived/README.md에 묶음 설명 없음: {n}")

if problems:
    print("\n".join(problems))
    sys.exit(1)
print(f"OK  plugins={len(plugins)} skills={len(skills)}")
