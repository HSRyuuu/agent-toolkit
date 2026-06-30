---
name: kb-manage
description: Use when setting up, locating, explaining, migrating, or maintaining the identity and shared conventions of a personal Markdown Knowledge Base.
---

# kb-manage

## Overview

Manage the KB itself: root path, identity, setup files, conventions, `index.md`, and `log.jsonl`. This is a lightweight Markdown source-of-truth KB model adapted from real work notes.

This model intentionally rejects the old `sources -> wiki -> schema` shape. Do not create `_raw/` for source preservation, do not require canonical/daily-log document kinds, and do not treat raw source files as the KB foundation.

## KB Identity

The KB is a curated Markdown repository where maintained documents are the source of truth.

- Human-readable documents are primary.
- LLMs help add, search, lint, and reorganize.
- `index.md` is the content catalog.
- `log.jsonl` is a small work-history pointer for finding files and git history.
- Git history is the durable audit trail.
- Source/provenance is recorded safely in frontmatter or body notes, not by storing raw source copies.
- Security and privacy override source preservation.

## Repository Operating Defaults

Use local KB rules if present. Otherwise use these defaults:

- Record facts, context, decisions, procedures, system knowledge, collaboration norms, and operational notes that should be found later.
- Keep documents current. When new information conflicts with old information, update the owning document and preserve only useful historical context.
- Do not mix confirmed facts with guesses. Mark uncertainty as `확인 필요`, `미정`, `추정`, `unknown`, or `past information`.
- Avoid duplicate ownership. Choose one source-of-truth document for each fact and link or reference it from related documents.
- Read the existing context before changing a document.
- Security-sensitive information is not worth preserving verbatim by default.
- Apply frontmatter rules when creating a new document or making a meaningful update.

## Writing Defaults

Documents should be easy for humans to scan and maintain.

- Make headings describe the flow of the document.
- Keep one central idea per paragraph.
- Split documents when one file starts covering multiple topics, systems, procedures, or decisions.
- Use lists for procedures, conditions, checklists, decisions, and action items.
- Separate background, current state, decisions, next actions, and open questions.
- Prefer exact dates over relative dates when timing matters.
- Use tables only when comparison or repeated attributes become easier to scan.
- Do not add unstated background knowledge or stronger conclusions while cleaning text.
- Make the next action or main conclusion easy to find.

## Maintenance Defaults

- Check what the latest known information is before updating.
- Replace outdated information with the current version when possible.
- Preserve past context only when it helps explain why the current state changed.
- For policy or decision changes, record change date, changed content, and impact scope when known.
- Reduce vague wording that weakens trust; if something is unknown, say it is unknown.
- For large documents, consider whether smaller linked documents would be easier to maintain.

## Skill Split

| Skill | Responsibility |
|---|---|
| `kb-manage` | root path, setup, conventions, migration, index/log identity |
| `kb-write` | create, append, merge, update, and reorganize knowledge |
| `kb-search` | read-only search and Q&A |
| `kb-lint` | health check, drift detection, security candidate reporting |

## Root Resolution

Use the first matching source:

1. User-provided absolute path.
2. The nearest ancestor of the user-provided path or current working directory that looks like a KB.
3. Current working directory, if it looks like a KB.
4. `~/.config/kb/path`, if it exists and points to a directory.

A directory looks like a KB when it has at least one of:

- `AGENTS.md`, `CLAUDE.md`, or `.agents/rules/`
- `index.md`
- `log.jsonl`
- several Markdown documents with KB-style frontmatter
- `.obsidian/` plus Markdown notes

If no root can be resolved, ask for an absolute path. Do not guess from unrelated home directories.

## Root Guidance Files

After resolving the KB root, always check the resolved root, not only the current shell directory, for local guidance.

Read whichever exists, in this order:

1. `AGENTS.md`
2. `CLAUDE.md`
3. `.agents/rules/*.md`

If the agent is working from a nested directory or from another directory entirely, still use the resolved KB root guidance. Local root guidance overrides the generic defaults in this skill.

## Setup

When initializing a KB:

1. Confirm the root path.
2. Create the root directory only after user approval if it does not exist.
3. Create or adapt `AGENTS.md` from `templates/AGENTS.md` if no agent entrypoint exists.
4. Create or adapt `index.md` from `templates/index.md` if missing.
5. Create or adapt `log.jsonl` from `templates/log.jsonl` if missing, replacing placeholder values with the setup date and root-specific summary.
6. Optionally write `~/.config/kb/path` after user approval.
7. Do not create `_raw/` or `_archive/`.
8. Create `_inbox/` only if the user explicitly wants a staging area.

### Template Usage

Setup templates live next to this skill:

- `templates/AGENTS.md`
- `templates/index.md`
- `templates/log.jsonl`

Use the templates as starting points, not as immutable boilerplate. Replace placeholders, remove irrelevant lines, and preserve any local rules that already exist. Do not overwrite an existing setup file without showing the intended change first.

### `index.md` Default Shape

```markdown
# Knowledge Base Index

이 문서는 KB의 문서 카탈로그이다. 자세한 사실은 각 원문 문서를 기준으로 확인한다.

## Documents

| Document | Summary | Tags | Updated |
|---|---|---|---|
| [Example](./example.md) | One-line summary. | `kb` | 2026-06-30 |
```

### `log.jsonl` Default Shape

Each line is one JSON object:

```json
{"date":"YYYY-MM-DD","type":"setup|add|update|merge|append|lint","summary":"짧은 작업 요약","files":["index.md"],"source":"agent","commit":null}
```

Rules:

- one JSON object per line
- no trailing commas
- no secrets or sensitive raw values
- paths relative to KB root
- `commit` may be `null` until a commit exists

## Frontmatter Default

Use the local KB rules if present. Otherwise use:

```yaml
---
title: "문서 제목"
summary: "한 문장 요약"
tags:
  - "kb"
aliases:
  - "검색할 만한 다른 이름"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
source: "user-note"
---
```

Required fields:

- `title`
- `summary`
- `tags`
- `aliases`
- `created`
- `updated`

Optional:

- `source`

Field rules:

- `title`: human-readable document title; should match or nearly match the H1.
- `summary`: one-sentence summary useful in search results and `index.md`.
- `tags`: searchable keywords such as domain, system, topic, acronym, team, or workflow.
- `aliases`: alternate names someone may search for, including local language names, English names, acronyms, and old names.
- `created`: first creation date in `YYYY-MM-DD`.
- `updated`: last meaningful update date in `YYYY-MM-DD`.
- `source`: safe provenance such as `user-note`, `meeting`, `slack`, `docs`, a filename, or a non-sensitive URL.

Writing rules:

- Put frontmatter at the top of Markdown files.
- Use YAML lists for array fields, even with one value.
- Keep tag values consistent; use lower-kebab-case unless a proper noun has a real spelling.
- Put currentness, uncertainty, and past-information markers in the body, not frontmatter.
- Do not put secrets, credentials, private infrastructure, personal data, or sensitive internal identifiers in frontmatter.

Scope defaults:

- Apply this frontmatter to normal KB documents and KB rule documents.
- Do not require frontmatter for root agent entrypoints such as `AGENTS.md` or `CLAUDE.md`.
- Do not mix KB frontmatter into plugin skill files such as `SKILL.md`; those files use skill frontmatter.
- Do not add frontmatter to non-Markdown files.

Do not add `kind: canonical`, `kind: daily-log`, or raw-source link fields unless the local KB already intentionally uses them.

## Migration From Old KB Model

When a KB already has `_raw/`, daily logs, or `kind: canonical`:

1. Do not delete anything automatically.
2. Explain that the new model treats maintained documents as source of truth.
3. Suggest a migration plan:
   - keep existing raw files untouched until reviewed
   - stop creating new `_raw/` files
   - convert valuable canonical pages into normal KB documents
   - keep dated notes only when they are useful as documents, not because the schema requires them
   - build `index.md`
   - start `log.jsonl`
4. Ask before moving, deleting, or rewriting old files.

## Index Maintenance

`index.md` should help humans and LLMs choose documents quickly.

Include:

- document link
- one-line summary
- important tags or category
- updated date when available

Do not include every heading or long excerpts.

## Log Maintenance

`log.jsonl` exists to make git history easier to navigate. It is not a replacement for git and not a source of truth.

Append entries for:

- setup
- document add/update/merge/append
- lint runs with meaningful findings
- index rebuilds
- migrations

Do not log routine read-only searches unless the user asks to keep a research trail.

## Do Not

- Do not create `_raw/` automatically.
- Do not preserve raw source text by default.
- Do not require Obsidian-specific features.
- Do not bulk-insert wikilinks.
- Do not modify git state.
- Do not overwrite existing setup files without showing the change.
