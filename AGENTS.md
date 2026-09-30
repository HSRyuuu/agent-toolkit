# PROJECT KNOWLEDGE BASE

**Generated:** 2026-06-21 17:56:42 KST
**Commit:** 184dd02
**Branch:** main

## OVERVIEW

`agent-toolkit` is a personal Claude Code / Codex plugin marketplace (`hsryuuu`) for reusable agent skills,
templates, and future agent assets. Each plugin is installed on its own. This repo is not a conventional app: editing the
skill/template files is the delivery path, and local plugin marketplace registration is the
runtime surface.

Skills ship as one plugin per skill (or per group of related skills): `plugins/<plugin>/skills/<skill>/SKILL.md`. Claude Code and Codex read the same `plugins/` tree.

## STRUCTURE

```text
agent-toolkit/
├── .claude-plugin/marketplace.json   # Claude Code marketplace (plugins[] has no version)
├── .agents/plugins/marketplace.json  # Codex marketplace
├── .claude/skills/          # project-local Claude Code verification skills, not plugin inventory
├── .codex/skills/           # project-local Codex verification skills, not plugin inventory
├── plugins/<plugin>/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   ├── skills/<skill>/SKILL.md
│   └── templates/           # only where a plugin's skills need them (project-setup)
├── scripts/bump-plugin.sh   # bumps both manifests of one plugin
├── templates/rules/         # copied external guideline references
└── docs/catalog.md          # human catalog of plugins and skills
```

## WHERE TO LOOK

| Task | Location | Notes |
|---|---|---|
| Add or update a plugin skill | `plugins/<plugin>/skills/<name>/SKILL.md` | Every loadable plugin skill lives here. A new plugin also needs both manifests and a row in both marketplace files. |
| Categorize a skill | `docs/catalog.md` or the skill body | Categories are metadata, not loader directories. |
| Update Claude plugin surface | `plugins/<plugin>/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Keep `version` equal to the Codex manifest. |
| Update Codex plugin surface | `plugins/<plugin>/.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` | Keep `version` equal to the Claude manifest. |
| Update local pre-commit verification | `.claude/skills/verify-secrets/`, `.codex/skills/verify-secrets/` | Keep this outside `plugins/`; it is not part of the plugin catalog. |
| Publish the repo end to end | `.claude/skills/publish-workflow/`, `.codex/skills/publish-workflow/` | Owns the release loop. Kept outside `plugins/`, like `verify-secrets`. |
| Document install/update/publish commands | `docs/how-to-install.md` | Single home for host CLI commands, cache-key rules, and troubleshooting. `README.md` links here. |
| Refresh catalog/docs | `README.md`, `docs/catalog.md`, `AGENTS.md`, `.claude/CLAUDE.md` | Use `update-project-docs` after adding/moving/removing skills. |
| Edit project setup templates | `plugins/project-setup/templates/` | These are placeholder skeletons, not facts about this repo. |

## CODE MAP

| Symbol / Entry | Type | Location | Role |
|---|---|---|---|
| `main()` | Python CLI | `plugins/html-tools/skills/html-db-schema-viewer-creator/build.py` | DBML-to-static-site generator. |
| `main()` | Python CLI | `plugins/html-tools/skills/html-db-schema-viewer-creator/tools/mysql_to_dbml.py` | MySQL schema extraction helper. |
| `main()` | Python CLI | `plugins/excel-docs/skills/excel-ui-test-doc-creator/scripts/create_test_doc.py` | Test spec to xlsx writer. |
| `main()` | Python CLI | `plugins/excel-docs/skills/excel-ui-test-doc-creator/scripts/profile_template.py` | Deterministic xlsx template profiler. |
| `main()` | Python CLI | `plugins/excel-docs/skills/excel-ui-test-doc-creator/scripts/verify_test_doc.py` | Output xlsx verifier. |
| `main()` | Python CLI | `plugins/excel-docs/skills/excel-doc-updater/scripts/profile_excel.py` | Form workbook profiler. |
| `main()` | Python CLI | `plugins/excel-docs/skills/excel-doc-updater/scripts/compare_excel.py` | Before/after workbook diff. |
| `main()` | Python CLI | `plugins/slack-helper/skills/slack-helper/scripts/slack_setup.py` / `slack_search.py` / `slack_read.py` | Slack Web API OAuth setup and read/search helpers using curl. |
| `main()` | Python CLI | `plugins/datadog-helper/skills/datadog-helper/scripts/datadog_setup.py` / `datadog_logs.py` / `datadog_apm.py` | Datadog logs/APM read-only helpers using curl. |
| `main()` | Python CLI | `plugins/atlassian-helper/skills/atlassian-helper/scripts/atlassian_setup.py` / `jira.py` / `confluence.py` | Jira + Confluence Cloud read/write helpers using curl; modify/delete guarded by an author check. |
| `parse_docx()` / `parse_pdf()` | Python helpers | `plugins/ui-feature-spec-docs/skills/ui-feature-spec-docs/scripts/parse_design_doc.py` | Screen-doc parser. |

## CONVENTIONS

- `SKILL.md` frontmatter must start the file and include at least `name` and `description`; use `metadata.origin` for imported/adapted skills, not a top-level `origin` key.
- `description` is the trigger surface. Keep it concrete and searchable; do not bury the actual trigger in body prose only.
- The plugin skill inventory is `find plugins -mindepth 4 -maxdepth 4 -path '*/skills/*' -name SKILL.md -print | sort`.
- Claude Code loads `plugins/<plugin>/.claude-plugin/plugin.json`; Codex loads `plugins/<plugin>/.codex-plugin/plugin.json`. Both must carry the same `version`.
- Treat `docs/catalog.md` as a generated human index. The source of truth is live `SKILL.md` frontmatter plus the plugin manifests.
- Skills must be self-contained inside their plugin: reference only files under the same `plugins/<plugin>/` (relative paths), never the repo root or another plugin.
- Keep category labels as metadata. Do not create loader topology by category.
- **Mandatory before commit:** run the project-local `verify-secrets` skill from `.claude/skills/verify-secrets/` or `.codex/skills/verify-secrets/` before any commit, push, PR, or release. If it reports a hit, stop and resolve it or ask the user for an explicit exemption before continuing.
- The local `verify-secrets` skill is intentionally outside the plugin skill root. Do not move it into `plugins/`, do not add it to `docs/catalog.md`, and do not copy its company/secret examples into any file under `plugins/`.
- **Publishing:** the local `publish-workflow` skill owns the release loop — verify-secrets, commit, version bump of each changed plugin (both manifests, `scripts/bump-plugin.sh`), `git push origin main`, then plugin updates. Stop the loop on any failing step. Like `verify-secrets`, it stays outside `plugins/` and out of `docs/catalog.md`. Host CLI commands and cache-key rules live in `docs/how-to-install.md`.
- Both hosts key their plugin cache on `version` (per plugin), so pushing without a bump changes nothing on installed machines. The bump is the release.

## ANTI-PATTERNS

- Do not invent catalog rows, trigger phrases, or recommendations that are not grounded in `SKILL.md` frontmatter.
- Do not treat `plugins/project-setup/templates/*` placeholders as facts about this repo or a target project.
- Do not overwrite user files in setup or Excel flows without the approval gates defined in the relevant skill.
- Do not split Claude Code and Codex onto different plugin trees.

## COMMANDS

```bash
# Current plugin skill inventory
find plugins -mindepth 4 -maxdepth 4 -path '*/skills/*' -name SKILL.md -print | sort
find plugins -mindepth 4 -maxdepth 4 -path '*/skills/*' -name SKILL.md -print | sort | wc -l

# Catalog link check
grep -oE '\(\.\./plugins/[^)]+/SKILL\.md\)' docs/catalog.md | tr -d '()' | sed 's#^../##' | while read p; do test -f "$p" || echo "MISSING: $p"; done

# Plugin validation
python3 /Users/happyhsryu/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py /Users/happyhsryu/dev/personal/agent-toolkit
codex plugin marketplace add /Users/happyhsryu/dev/personal/agent-toolkit
codex plugin list --marketplace hsryuuu --available --json

# JSON sanity for plugin metadata
jq empty .claude-plugin/marketplace.json .agents/plugins/marketplace.json plugins/*/.claude-plugin/plugin.json plugins/*/.codex-plugin/plugin.json

# Git scope before commits
git status --short
git diff --stat

# Mandatory pre-commit secret/company scan
# Run the project-local verify-secrets skill before staging or committing.
```

## NOTES

- This worktree may contain unrelated local changes. Preserve them; stage only the files directly tied to the task.
- `.claude/CLAUDE.md` is the Claude-specific companion. Keep it conceptually aligned with this file when changing repo topology or plugin registration behavior.
- There is no root app build/test pipeline. Validation is manifest checks plus skill-local deterministic scripts.
