---
name: setup-agent-entrypoint
description: >
  Use when a project needs AGENTS.md, CLAUDE.md, .claude/CLAUDE.md, or an agent
  entrypoint that points agents to existing docs, conventions, and local helper
  skills. Triggers: "set up agent instructions", "create AGENTS.md",
  "wire CLAUDE.md", "map project docs". Do NOT use to create docs, source maps,
  LESSONS.md, or local skills.
---

# Setup Agent Entrypoint

Create or repair the small project entrypoint that tells agents where context lives and which project-local conventions matter.

## Scope

This skill owns only entrypoint files and mapping sections:

| Asset | Default path | Purpose |
| --- | --- | --- |
| `AGENTS.md` | project root | Codex and general agent instructions |
| `CLAUDE.md` | project root or `.claude/CLAUDE.md` | Claude Code project instructions |
| Document mapping section | inside the chosen entrypoint | points to docs and local skills already present |

Do not create project docs, `SOURCE_MAP.md`, `CODEBASE_CONTEXT.md`, `.claude/LESSONS.md`, or `.claude/skills/*`. Use the dedicated setup skills for those assets.

## Workflow

1. Resolve the target project root.
2. Scan for existing `AGENTS.md`, `CLAUDE.md`, and `.claude/CLAUDE.md`.
3. Scan read-only for known setup assets:
   - docs: `docs/PROJECT_OVERVIEW.md`, `docs/DB_SCHEMA.md`, `docs/DEPLOY.md`, `docs/DESIGN.md`, `docs/ADR.md`
   - context maps: `docs/SOURCE_MAP.md`, `docs/CODEBASE_CONTEXT.md`, `.codesight/`
   - self-improvement: `.claude/LESSONS.md`
   - local skills: `.claude/skills/*/SKILL.md`
4. Recommend one entrypoint strategy:
   - create `AGENTS.md` for Codex/general agents
   - create or update `.claude/CLAUDE.md` for Claude Code
   - keep an existing root `CLAUDE.md` if the project already uses it intentionally
   - consolidate only after explicit approval when both root `CLAUDE.md` and `.claude/CLAUDE.md` exist
5. Before editing, show the exact file path and sections to add.
6. If a destination exists, preserve existing content and append or replace only the approved mapping section.
7. Report the entrypoint path and every mapped asset.

## Recommended Sections

Use only the sections that match the project:

```markdown
# Project Agent Guide

## Read First

- Start with `docs/PROJECT_OVERVIEW.md` for project identity and current state.
- Use `docs/SOURCE_MAP.md` before broad source exploration when it exists.

## Document Map

| Document | Purpose |
| --- | --- |
| `docs/PROJECT_OVERVIEW.md` | project identity, stack, milestones, links |
| `docs/SOURCE_MAP.md` | source routing map |

## Project-Local Skills

| Skill | Purpose |
| --- | --- |
| `.claude/skills/update-project-docs/SKILL.md` | sync project docs with code changes |
```

Never list assets that do not exist unless the user explicitly wants a planned-state map.

## Safety Rules

- Default to read-only recommendation unless the user explicitly asks to apply changes.
- Never overwrite an entrypoint silently.
- Do not move root `CLAUDE.md` into `.claude/` without explicit approval.
- Keep generated mappings factual: actual paths only.
- Do not edit plugin manifests, package files, or unrelated docs.

## Verification

```bash
test -f "$TARGET/AGENTS.md" || test -f "$TARGET/CLAUDE.md" || test -f "$TARGET/.claude/CLAUDE.md"
rg -n "Document Map|Project-Local Skills|SOURCE_MAP|LESSONS|\\.claude/skills" "$TARGET/AGENTS.md" "$TARGET/CLAUDE.md" "$TARGET/.claude/CLAUDE.md" 2>/dev/null
```
