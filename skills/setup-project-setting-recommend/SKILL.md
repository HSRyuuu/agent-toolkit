---
name: setup-project-setting-recommend
description: Use when a user wants read-only recommendations for which setup-* skills or project assets to apply, including .claude setup, project docs, source maps, self-improvement loops, and agent entrypoints.
---

# Setup Project Setting Recommend

Scan a project and recommend which setup skills should be run. This is a read-only router, not an installer.

## Core Rule

Never create, modify, delete, move, or install files from this skill. If the user asks to apply a recommendation, route to the matching `setup-*` skill.

## Recommendation Map

| Need detected | Recommend |
| --- | --- |
| no `AGENTS.md`, `CLAUDE.md`, or `.claude/CLAUDE.md`; missing document map | `setup-agent-entrypoint` |
| large or unfamiliar codebase; missing `SOURCE_MAP.md` or `CODEBASE_CONTEXT.md` | `setup-codebase-context-map` |
| missing `PROJECT_OVERVIEW.md`, `DB_SCHEMA.md`, `DEPLOY.md`, `DESIGN.md`, or `ADR.md` | `setup-project-docs` |
| missing `.claude/skills/manage-skills`, `verify-implementation`, or `update-project-docs` | `setup-project-level-agent-skill` |
| missing `.claude/LESSONS.md` or self-improvement instruction | `setup-self-improvement-loop` |

## Read-Only Scan

1. Resolve the target project root.
2. Scan current entrypoints:
   - `AGENTS.md`
   - `CLAUDE.md`
   - `.claude/CLAUDE.md`
3. Scan project docs:
   - `docs/PROJECT_OVERVIEW.md`
   - `docs/SOURCE_MAP.md`
   - `docs/CODEBASE_CONTEXT.md`
   - `docs/DB_SCHEMA.md`
   - `docs/DEPLOY.md`
   - `docs/DESIGN.md`
   - `docs/ADR.md`
4. Scan agent operation assets:
   - `.claude/LESSONS.md`
   - `.claude/skills/manage-skills/SKILL.md`
   - `.claude/skills/verify-implementation/SKILL.md`
   - `.claude/skills/update-project-docs/SKILL.md`
5. Scan context signals:
   - DB: `migrations/`, `prisma/`, `alembic/`, `db/migrate/`, entities/models
   - deploy: `.github/workflows/`, `Dockerfile`, `vercel.json`, `fly.toml`, cloud config
   - design: frontend dirs, `tailwind.config.*`, `theme/`, `tokens/`, Storybook
   - source map need: `src/`, `app/`, `frontend/`, `backend/`, multiple services, many files

## Output Format

Report recommendations as a compact table:

| Recommendation | Status | Why | Next skill |
| --- | --- | --- | --- |
| Agent entrypoint | missing | no `AGENTS.md` or `CLAUDE.md` found | `setup-agent-entrypoint` |
| Source map | recommended | `src/` and `backend/` detected | `setup-codebase-context-map` |

Use these statuses:

- `missing`: no asset exists and the project likely needs it
- `partial`: asset exists but key mapping or instruction is absent
- `present`: no action needed
- `optional`: useful, but no strong signal was detected

End with a short command-style next step, for example:

```text
Next: run `setup-project-docs` for PROJECT_OVERVIEW.md and DEPLOY.md, then `setup-codebase-context-map`.
```

## Safety Rules

- Do not ask installation questions from this skill. Recommendation is the endpoint.
- If the user says "apply/install", switch to the named `setup-*` skill and follow that skill's confirmation gates.
- Do not infer nonstandard document paths as missing when the user has already told you where docs live; include the user-provided paths in the report.
- Do not recommend old `project-setup` or `recommend-project-setting`; those responsibilities are split across `setup-*` skills.

## Verification

For this skill, verification is read-only:

```bash
git status --short
find "$TARGET" -maxdepth 3 \\( -name AGENTS.md -o -name CLAUDE.md -o -name PROJECT_OVERVIEW.md -o -name SOURCE_MAP.md -o -name LESSONS.md \\) -print 2>/dev/null
```
