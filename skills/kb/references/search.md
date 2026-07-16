# Search Mode

## Overview

Search a curated Markdown KB in read-only mode. The maintained documents are the source-of-truth surface. Do not cite `log.jsonl` as evidence for a fact; it is the primary work-history pointer for locating relevant files and past work, while the documents themselves hold the facts. Do not rely on embeddings or general web knowledge unless the user explicitly asks for outside-KB research.

**Shared rules:** Read [`conventions.md`](./conventions.md) completely and follow
its rules for KB root resolution, frontmatter fields, uncertainty markers, `index.md` /
`log.jsonl` rules, and bundled-resource routing.

**First-time recovery:** if no registered root resolves, switch to the config
bootstrap in [`manage.md`](./manage.md); never search an unregistered absolute
path. If the config is missing or empty, propose `~/KnowledgeBase` while
allowing another absolute directory. For missing runtime packages, follow the
first-time setup in [`manage.md`](./manage.md).
Do not mutate config or install packages without approval.

## Core Principles

- Read only. Do not create, edit, delete, stage, commit, or reformat files.
- Prefer KB evidence over memory or general knowledge.
- Include `_archived/` documents in search results when they match. Treat them as archived historical context, not as automatically current facts.
- Distinguish confirmed facts from `확인 필요`, `미정`, `추정`, and `과거 정보`.
- Cite local documents with paths or KB links.
- If the KB does not contain enough information, say so plainly.
- Do not expose sensitive values found during search unless the user specifically needs them and the KB rules allow it.

## Search Order

1. Resolve the KB root using the conventions Root Resolution rules.
2. Read root guidance files from the resolved KB root, even if the current shell directory is elsewhere.
3. Read `index.md` first if it exists.
4. Read relevant directory `README.md` files when folder intent helps narrow the search.
5. Search frontmatter fields: `title`, `summary`, `tags`, `aliases`, `source`, `created`, `updated`.
6. Search filenames and headings.
7. Search body text with exact terms and likely synonyms.
8. Read the most relevant documents or sections.
9. Follow only clearly useful related links; avoid broad graph walks.

## Useful Commands

Use [`manage.md`](./manage.md) to resolve the root, then pass the resolved absolute root to
the search helpers bundled with this skill:

- `../scripts/kb_meta_search.py <KB_ROOT> --updated 2026-07-01`
- `../scripts/kb_meta_search.py <KB_ROOT> --created 2026-07-01 --tag kafka`
- `../scripts/kb_meta_search.py <KB_ROOT> --updated-since 2026-06-01 --updated-until 2026-06-30`
- `../scripts/kb_recent_activity.py <KB_ROOT> --date 2026-07-01`
- `../scripts/kb_recent_activity.py <KB_ROOT> --since 2026-06-28`

Use these scripts before `rg` when the query is about structured frontmatter
fields such as `title`, `summary`, `tags`, `aliases`, `source`, `created`,
`updated`, or `agent_edit_mode`. They require the locked `python-frontmatter`
and `PyYAML` runtime from the bundled `../scripts/requirements.txt`. Follow the
first-time recovery guide when it is absent or mismatched; for a read-only
search that cannot wait for approved installation, fall back to `rg` and
disclose that structured metadata parsing was unavailable.

Run bundled Python helpers with `~/.venvs/agent-toolkit-kb/bin/python` by
default. Do not install dependencies into Homebrew/system Python.

Inventory:

```bash
find "$KB_ROOT" -path '*/.*' -prune -o -path '*/node_modules' -prune -o -name '*.md' -print
```

Structure fields and headings:

```bash
rg -n --glob '*.md' --glob '!**/.*/**' --glob '!**/.*' --glob '!**/node_modules/**' \
  "title:|summary:|tags:|aliases:|^#{1,6} " "$KB_ROOT"
```

Body keyword search (replace `<검색어>` and `<synonym>`):

```bash
rg -n --glob '*.md' --glob '!**/.*/**' --glob '!**/.*' --glob '!**/node_modules/**' \
  "<검색어>|<synonym>" "$KB_ROOT"
```

Recent KB activity — check `log.jsonl` first; it is the primary work-history
trail and works without git:

```bash
test -f "$KB_ROOT/log.jsonl" && tail -100 "$KB_ROOT/log.jsonl"
test -f "$KB_ROOT/log.jsonl" && rg -n '"files":|"summary":|"datetime":|"type":|"source":|<검색어>|<synonym>' "$KB_ROOT/log.jsonl"
test -f "$KB_ROOT/log.jsonl" && jq -c . "$KB_ROOT/log.jsonl" >/dev/null
```

If `log.jsonl` is absent, note the gap only when the user asked about KB
maintenance; for a normal search, fall back to git history when available and
otherwise rely on frontmatter dates.

Git history — a supplementary reference in a git-backed KB (it never replaces
`log.jsonl`). Use it for diffs, blame, and change archaeology. Commits may
follow the `kb: add|update|merge|append <doc> — <summary>` convention:

```bash
git log --oneline -- path/to/doc.md          # history of one document
git log --oneline --grep='^kb:'              # all KB work, newest first
git log --all --grep='keyword' --oneline     # find a change by topic keyword
git log --oneline --name-only -n 20          # recent changes with touched files
```

## Candidate Selection

Prioritize:

1. `index.md` entries whose title/summary/tags match the question.
2. Documents whose title or aliases match the user's wording.
3. Documents with current `updated` dates or body-level 기준일.
4. Documents with exact terms from the question.
5. Related documents linked from the strongest candidate.

When a result is under `_archived/`, include it if useful but label it as archived in the answer.

Limit full reads to the smallest useful set. For broad questions, return the top matches rather than every hit.

## Answer Format

Answer with:

- direct answer or "정보 부족"
- evidence files
- uncertainty or stale areas
- suggested next search/write action only when useful

Example:

```markdown
확인된 내용은 ... 입니다.

근거:
- path/to/doc.md — 핵심 기준
- path/to/related.md — 보조 맥락

확인 필요:
- ...
```

## Do Not

- Do not update `index.md` or `log.jsonl` during search.
- Do not infer missing company/project facts from general knowledge.
- Do not treat `log.jsonl` as a source of truth for facts; it is the primary work-history pointer for finding relevant files and past work, and maintained documents remain the truth surface.
- Do not add bulk Obsidian wikilinks while answering a search question.
