---
name: kb-manage
description: >
  Use when setting up or maintaining a personal Markdown Knowledge Base (KB):
  resolving the KB root, explaining conventions, migrating an old layout, or
  maintaining index.md/log.jsonl. Triggers: "kb 만들어줘/셋업", "지식베이스 정리 규칙",
  "kb 루트 어디", "인덱스 정리". Do NOT use for adding knowledge, search, or health
  checks.
---

# kb-manage

## Overview

Manage the KB itself: root path, identity, setup files, `index.md`, and
`log.jsonl`. This is a lightweight Markdown source-of-truth KB model where
maintained documents are the truth surface.

**Shared conventions live in one place:** read
[`references/conventions.md`](./references/conventions.md) for KB identity, root
resolution, uncertainty markers, frontmatter, `agent_edit_mode`, `index.md` /
`log.jsonl` rules, security principles, and script paths. This SKILL.md covers
only the manage-specific work: setup, templates, folder structure, migration,
and index/log maintenance.

## Repository Operating Defaults

Use local KB rules if present. Otherwise:

- Record facts, context, decisions, procedures, system knowledge, collaboration
  norms, and operational notes that should be found later.
- Keep documents current. When new information conflicts with old, update the
  owning document and preserve only useful historical context.
- Retire documents by moving them to top-level `_archived/` and setting
  `agent_edit_mode: read_only`.
- Avoid duplicate ownership. Choose one source-of-truth document for each fact
  and link related documents to it.
- Read existing context before changing a document.
- Apply frontmatter rules (see conventions) on creation and meaningful updates.

## Writing Defaults

Documents should be easy for humans to scan and maintain.

- Make headings describe the flow of the document.
- Keep one central idea per paragraph.
- Split a document when it starts covering multiple topics, systems, procedures,
  or decisions.
- Use lists for procedures, conditions, checklists, decisions, and action items.
- Separate background, current state, decisions, next actions, and open questions.
- Prefer exact dates over relative dates when timing matters.
- Use tables only when comparison or repeated attributes are easier to scan.
- Do not add unstated background knowledge or stronger conclusions while cleaning.
- Make the next action or main conclusion easy to find.
- Follow `kb-write` Related Document Links for selective related-document links.

## Maintenance Defaults

- Check the latest known information before updating.
- Replace outdated information with the current version when possible.
- Preserve past context only when it explains why the current state changed.
- For policy or decision changes, record change date, changed content, and impact
  scope when known.
- Reduce vague wording; if something is unknown, say so.
- For large documents, consider whether smaller linked documents maintain better.

## Skill Split

| Skill | Responsibility |
|---|---|
| `kb-manage` | root path, setup, conventions home, migration, index/log identity |
| `kb-write` | create, append, merge, update, and reorganize knowledge |
| `kb-search` | read-only search and Q&A |
| `kb-lint` | health check, drift detection, security candidate reporting |

## Root Resolution and Guidance

Resolve the KB root and read local root guidance exactly as described in
[`references/conventions.md`](./references/conventions.md) (Root Resolution). Do
not infer a root from the working directory. After resolving, read the resolved
root's `AGENTS.md` / `CLAUDE.md` / `.agents/rules/*.md`; local guidance overrides
generic defaults.

## Optional Obsidian Support

If the KB is also an Obsidian vault, or the user asks for Obsidian Markdown,
Bases, Canvas, CLI, wikilinks, embeds, callouts, or properties, read
[`references/obsidian-skills.md`](./references/obsidian-skills.md). Do not require
Obsidian skills for normal KB work.

## Setup

When initializing a KB:

1. Confirm the root path.
2. Create the root directory only after user approval if it does not exist.
3. Create or adapt `AGENTS.md` from `templates/AGENTS.md` if no agent entrypoint
   exists.
4. Create or adapt `index.md` from `templates/index.md` if missing.
5. Create `log.jsonl` from `templates/log.jsonl` — it is the primary
   work-history trail and must work without git (see conventions). Replace
   placeholders with the setup datetime and a root-specific summary. Skip it
   only when the user explicitly opts out of a work-history file.
6. Register this KB in `~/.config/kb/kb-config.json` after user approval
   (create the file or add/update the `kbs` entry). Registration lets other
   directories resolve the KB root automatically. If the user explicitly
   declines, skip registration and tell them they will need to provide the
   absolute KB path in each session.
7. Do not create `_raw/`.
8. Create `_inbox/` only if the user explicitly wants a staging area.

### Template Usage

Setup templates live next to this skill: `templates/AGENTS.md`,
`templates/index.md`, `templates/log.jsonl`. Use them as starting points, not
immutable boilerplate. Replace placeholders, remove irrelevant lines, and
preserve existing local rules. Do not overwrite an existing setup file without
showing the intended change first.

### Directory `README.md` Files

Use `README.md` for folder-level intent notes. Root `index.md` remains the
KB-wide catalog; directory `README.md` files explain how a folder should be used.

Keep them short. Include only: folder purpose, what belongs, what does not belong
when the boundary is easy to confuse, and naming guidance when useful. Do not use
them as file lists, detailed catalogs, changelogs, or substitutes for root
`index.md`. Add or expand one when the user describes how a folder should be used,
such as "이 폴더는 앞으로 이렇게 쓸거야."

## Inbox Documents

Use top-level `_inbox/` for material that should stay findable but is not yet a
maintained source-of-truth document.

Good `_inbox/` candidates:

- unclassified notes waiting for routing
- short source material that still needs washing
- unfinished stubs that only have a title/frontmatter or "to be written" content
- documents that would look authoritative if left in a normal topic folder

Use `_inbox/stubs/` for placeholders that name a future topic but do not yet hold
useful maintained knowledge (planned API specs, auth notes, standards, system
pages).

Rules:

- `_inbox/` documents are temporary candidates, not current source of truth.
- Do not rely on `_inbox/` to preserve raw sensitive source text.
- When a stub becomes useful, move it to the proper topic folder, update
  frontmatter/tags, and update `index.md` / `log.jsonl` if maintained.
- If `index.md` lists `_inbox/` documents, put them in a clearly labeled "Inbox"
  or "Stubs" section.

## Archived Documents

Use `_archived/` for documents the owner wants to keep but no longer treat as
active current knowledge.

Rules:

- The archive folder is exactly top-level `_archived/`, one depth deep, such as
  `_archived/old-project-notes.md`. Do not create subfolders or alternate names
  such as `_archive/`.
- Archived documents are still normal Markdown KB documents and may be found by
  search. Links from active documents to them are allowed.
- Do not add a separate archive-specific edit ban. Set `agent_edit_mode:
  read_only` and follow the normal Agent Edit Mode rules (see conventions).

When archiving a document:

1. Move it to `_archived/<filename>.md`, preserving the filename unless there is
   a collision.
2. Set or update frontmatter `agent_edit_mode: read_only`. The git guard treats
   this editable→read_only transition as an informational note, not a violation.
3. Update `index.md` and `log.jsonl` when the KB maintains them.

## Migration From Old KB Model

This model uses maintained documents as the foundation, not a
`sources -> wiki -> schema` shape, `_raw/` preservation, or required
`kind: canonical` / `kind: daily-log` types. When a KB already has `_raw/`, daily
logs, or `kind: canonical`:

1. Do not delete anything automatically.
2. Explain that the new model treats maintained documents as source of truth.
3. Suggest a migration plan:
   - keep existing raw files untouched until reviewed
   - stop creating new `_raw/` files
   - convert valuable canonical pages into normal KB documents
   - keep dated notes only when useful as documents, not because a schema required
     them
   - build `index.md`
   - start `log.jsonl` as the work-history trail (regardless of git)
4. Ask before moving, deleting, or rewriting old files.

## Index Maintenance

`index.md` helps humans and LLMs choose documents quickly. See conventions for
the shape. Keep it content-oriented, not chronological, and do not include every
heading or long excerpts.

Prefer regenerating the Documents catalog from frontmatter instead of editing it
by hand. The build script preserves the human-written preamble (everything before
the `<!-- kb:documents:start -->` marker) and rewrites only the generated tables:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/kb_build_index.py" /path/to/kb            # preview
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/kb_build_index.py" /path/to/kb --write    # apply
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/kb_build_index.py" /path/to/kb --check    # drift check
```

It needs `python-frontmatter` (see `../kb-search/scripts/requirements.txt`).

## Log Maintenance

`log.jsonl` is the primary work-history trail and must work without git (see
conventions). Maintain it by default: append entries for setup,
add/update/merge/append, lint runs with meaningful findings, index rebuilds, and
migrations. If it is missing in an existing KB, treat that as a maintenance gap
and offer to start it. Git history, when the KB is git-backed, is a
supplementary reference only. Do not log routine read-only searches unless the
user asks for a research trail.
