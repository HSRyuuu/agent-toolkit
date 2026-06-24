---
name: setup-project-docs
description: Use when a project needs initial human-maintained documentation skeletons such as PROJECT_OVERVIEW.md, DB_SCHEMA.md, DEPLOY.md, DESIGN.md, or ADR.md, excluding SOURCE_MAP.md, CODEBASE_CONTEXT.md, LESSONS.md, and local agent skills.
---

# Setup Project Docs

Recommend and install the small set of human-maintained project documents that are not owned by other setup skills.

## Scope

This skill owns only these documents:

| Document | Default path | When to recommend |
| --- | --- | --- |
| `PROJECT_OVERVIEW.md` | `docs/PROJECT_OVERVIEW.md` | almost always; captures identity, stack, milestones, links |
| `DB_SCHEMA.md` | `docs/DB_SCHEMA.md` | migrations, ORM schema, entities, or database usage exist |
| `DEPLOY.md` | `docs/DEPLOY.md` | CI/CD, Docker, Vercel, cloud config, env vars, or domains exist |
| `DESIGN.md` | `docs/DESIGN.md` | frontend UI, Tailwind/theme tokens, design system, or Figma links exist |
| `ADR.md` | `docs/ADR.md` | meaningful architecture decisions or multi-module complexity exist |

Explicitly excluded:

| Excluded asset | Owner |
| --- | --- |
| `SOURCE_MAP.md`, `CODEBASE_CONTEXT.md`, `.codesight/` | `setup-codebase-context-map` |
| `.claude/LESSONS.md` | `setup-self-improvement-loop` |
| `.claude/skills/*` | `setup-project-level-agent-skill` |
| `AGENTS.md`, `CLAUDE.md` | future entrypoint setup skill or manual project policy |

## Workflow

1. Resolve the target project root.
2. Scan read-only for signals:
   - DB: `migrations/`, `prisma/`, `alembic/`, `db/migrate/`, entities/models
   - deploy: `.github/workflows/`, `Dockerfile`, `vercel.json`, `fly.toml`, cloud config
   - design: frontend dirs, `tailwind.config.*`, `theme/`, `tokens/`, Storybook
   - ADR: `docs/adr/`, `docs/decisions/`, multiple services/modules
3. Present a recommendation table with status, reason, and default path.
4. Stop after recommendation unless the user explicitly asks to install or apply.
5. If installing, include only documents selected by the user and only templates that exist in `templates/project-setup/`.
6. Show the exact destination paths before writing.
7. On conflict, ask whether to keep existing, back up and replace, append missing top-level sections, or cancel.
8. Copy or merge approved documents, then report the result.

## Merge Rules

- For `PROJECT_OVERVIEW.md`, `DB_SCHEMA.md`, `DEPLOY.md`, and `DESIGN.md`, merge means append template `##` sections that are missing from the existing file.
- For `ADR.md`, do not section-merge by default. ADR indexes and numbering are easy to corrupt; prefer keep, backup-and-replace, or manual update.
- Remove only installation-only HTML comments from copied templates. Preserve useful placeholders that tell the project owner what to fill in.

## Safety Rules

- Default behavior is read-only recommendation.
- Do not create `SOURCE_MAP.md`, `CODEBASE_CONTEXT.md`, `LESSONS.md`, local skills, `AGENTS.md`, or `CLAUDE.md`.
- Do not invent templates; skip any missing source file and report it.
- Do not alter `.gitignore`, package files, manifests, or unrelated docs.

## Verification

After installation, verify only the selected documents:

```bash
for doc in PROJECT_OVERVIEW.md DB_SCHEMA.md DEPLOY.md DESIGN.md ADR.md; do
  test -f "$TARGET/docs/$doc" && echo "FOUND docs/$doc"
done
```
