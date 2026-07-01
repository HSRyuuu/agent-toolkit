---
name: kb-search
description: Use when answering questions from a Markdown Knowledge Base, finding related documents, checking existing records, or locating source-of-truth notes without modifying files.
---

# kb-search

## Overview

Search a curated Markdown KB in read-only mode. The maintained documents are the source-of-truth surface. Do not depend on `_raw/`, daily logs, canonical kinds, embeddings, `log.jsonl`, or general web knowledge unless the user explicitly asks outside-KB research.

**Required orientation:** read and follow `kb-manage` for KB root, identity, repository defaults, frontmatter, `index.md`, `log.jsonl`, and shared conventions.

## Core Principles

- Read only. Do not create, edit, delete, stage, commit, or reformat files.
- Prefer KB evidence over memory or general knowledge.
- Include `_archived/` documents in search results when they match. Treat them as archived historical context, not as automatically current facts.
- Distinguish confirmed facts from `확인 필요`, `미정`, `추정`, and `과거 정보`.
- Cite local documents with paths or KB links.
- If the KB does not contain enough information, say so plainly.
- Do not expose sensitive values found during search unless the user specifically needs them and the KB rules allow it.

## Search Order

1. Resolve the KB root using `kb-manage` rules.
2. Read root guidance files from the resolved KB root, even if the current shell directory is elsewhere.
3. Read `index.md` first if it exists.
4. Read relevant directory `README.md` files when folder intent helps narrow the search.
5. Search frontmatter fields: `title`, `summary`, `tags`, `aliases`, `source`, `created`, `updated`.
6. Search filenames and headings.
7. Search body text with exact terms and likely synonyms.
8. Read the most relevant documents or sections.
9. Follow only clearly useful related links; avoid broad graph walks.

## Useful Commands

Inventory:

```bash
find . -path './.git' -prune -o -path './.obsidian' -prune -o -name '*.md' -print
```

Frontmatter/headings/body:

```bash
rg -n --glob '*.md' --glob '!**/.git/**' --glob '!**/.obsidian/**' \
  "title:|summary:|tags:|aliases:|^#{1,6} |검색어|synonym" .
```

Recent KB activity when `log.jsonl` exists:

```bash
tail -100 log.jsonl
rg -n '"files":|"summary":|"datetime":|"type":|"source":|검색어|synonym' log.jsonl
jq -c . log.jsonl >/dev/null
```

If `log.jsonl` is absent, skip these commands without warning unless the user asked to audit KB maintenance files.

Git history fallback:

```bash
git log --oneline -- path/to/doc.md
git log --all --grep='keyword' --oneline
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
- Do not treat `log.jsonl` as a source of truth; use it only to find relevant files or git history, and ignore it when it is absent.
- Do not add bulk Obsidian wikilinks while answering a search question.
