# PROJECT KNOWLEDGE BASE

**Generated:** 2026-06-21 17:56:42 KST
**Commit:** 184dd02
**Branch:** main

## OVERVIEW

`agent-toolkit` is a personal Claude Code / Codex plugin bundle for reusable agent skills,
templates, and future agent assets. This repo is not a conventional app: editing the
skill/template files is the delivery path, and local plugin marketplace registration is the
runtime surface.

Claude Code and Codex use the same active plugin skill root: `skills/`.

## STRUCTURE

```text
agent-toolkit/
├── .claude-plugin/          # Claude Code plugin manifest + local marketplace
├── .codex-plugin/           # Codex plugin manifest
├── .agents/plugins/         # Codex local marketplace metadata
├── plugins/agent-toolkit    # local marketplace source entry
├── skills/                  # single active plugin skill root
├── templates/               # copy-on-install templates and copied rule references
└── docs/catalog.md          # human catalog of skill names/triggers
```

## WHERE TO LOOK

| Task | Location | Notes |
|---|---|---|
| Add or update a plugin skill | `skills/<name>/SKILL.md` | Every loadable plugin skill lives here. |
| Categorize a skill | `docs/catalog.md` or the skill body | Categories are metadata, not loader directories. |
| Update Claude plugin surface | `.claude-plugin/plugin.json` | Keep the skill root aligned with `skills/`. |
| Update Codex plugin surface | `.codex-plugin/plugin.json` | Keep the skill root aligned with `skills/`. |
| Refresh catalog/docs | `README.md`, `docs/catalog.md`, `AGENTS.md`, `.claude/CLAUDE.md` | Use `update-project-docs` after adding/moving/removing skills. |
| Edit project setup templates | `templates/project-setup/` | These are placeholder skeletons, not facts about this repo. |

## CODE MAP

| Symbol / Entry | Type | Location | Role |
|---|---|---|---|
| `main()` | Python CLI | `skills/html-db-schema-viewer-creator/build.py` | DBML-to-static-site generator. |
| `main()` | Python CLI | `skills/html-db-schema-viewer-creator/tools/mysql_to_dbml.py` | MySQL schema extraction helper. |
| `main()` | Python CLI | `skills/excel-ui-test-doc-creator/scripts/create_test_doc.py` | Test spec to xlsx writer. |
| `main()` | Python CLI | `skills/excel-ui-test-doc-creator/scripts/profile_template.py` | Deterministic xlsx template profiler. |
| `main()` | Python CLI | `skills/excel-ui-test-doc-creator/scripts/verify_test_doc.py` | Output xlsx verifier. |
| `main()` | Python CLI | `skills/excel-doc-updater/scripts/profile_excel.py` | Form workbook profiler. |
| `main()` | Python CLI | `skills/excel-doc-updater/scripts/compare_excel.py` | Before/after workbook diff. |
| `main()` | JS CLI | `skills/writing-skills/render-graphs.js` | Render Graphviz blocks from skill docs. |
| `parse_docx()` / `parse_pdf()` | Python helpers | `skills/ui-feature-spec-docs/scripts/parse_design_doc.py` | Screen-doc parser. |

## CONVENTIONS

- `SKILL.md` frontmatter must start the file and include at least `name` and `description`; use `metadata.origin` for imported/adapted skills, not a top-level `origin` key.
- `description` is the trigger surface. Keep it concrete and searchable; do not bury the actual trigger in body prose only.
- The plugin skill inventory is `find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort`.
- Claude Code loads `.claude-plugin/plugin.json`; Codex loads `.codex-plugin/plugin.json`. Both must point at the same `skills/` plugin skill root.
- Treat `docs/catalog.md` as a generated human index. The source of truth is live `SKILL.md` frontmatter plus the plugin manifests.
- Keep category labels as metadata. Do not create loader topology by category.

## ANTI-PATTERNS

- Do not invent catalog rows, trigger phrases, or recommendations that are not grounded in `SKILL.md` frontmatter.
- Do not treat `templates/project-setup/*` placeholders as facts about this repo or a target project.
- Do not overwrite user files in setup or Excel flows without the approval gates defined in the relevant skill.
- Do not split Claude Code and Codex onto different active skill roots.

## COMMANDS

```bash
# Current plugin skill inventory
find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort
find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort | wc -l

# Catalog link check
grep -oE '\(\.\./skills/[^)]+/SKILL\.md\)' docs/catalog.md | tr -d '()' | sed 's#^../##' | while read p; do test -f "$p" || echo "MISSING: $p"; done

# Plugin validation
python3 /Users/happyhsryu/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py /Users/happyhsryu/dev/personal/agent-toolkit
codex plugin marketplace add /Users/happyhsryu/dev/personal/agent-toolkit
codex plugin list --marketplace agent-toolkit-local --available --json

# JSON sanity for plugin metadata
jq empty .claude-plugin/plugin.json
jq empty .claude-plugin/marketplace.json
jq empty .codex-plugin/plugin.json
jq empty .agents/plugins/marketplace.json

# Git scope before commits
git status --short
git diff --stat
```

## NOTES

- This worktree may contain unrelated local changes. Preserve them; stage only the files directly tied to the task.
- `.claude/CLAUDE.md` is the Claude-specific companion. Keep it conceptually aligned with this file when changing repo topology or plugin registration behavior.
- There is no root app build/test pipeline. Validation is manifest checks plus skill-local deterministic scripts.
