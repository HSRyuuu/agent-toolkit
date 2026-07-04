---
name: kb-lint
description: Use when health-checking the user's personal Markdown Knowledge Base (KB) for metadata gaps, stale uncertainty, duplicate topics, index/log drift, broken links, or security-sensitive content. Triggers include "kb 점검/린트해줘", "지식베이스 상태 확인", "인덱스/링크 깨진 데 있나". Reports by default; fixes only on explicit request. Not for adding knowledge (use kb-write) or answering questions (use kb-search).
---

# kb-lint

## Overview

Health-check a curated Markdown KB. This lint model follows a source-of-truth document workflow: frontmatter, document clarity, `index.md`, `log.jsonl`, security hygiene, and search quality are what it checks.

**Required orientation:** read
[`kb-manage/references/conventions.md`](../kb-manage/references/conventions.md)
for KB root resolution, frontmatter fields, uncertainty markers, `agent_edit_mode`,
`index.md` / `log.jsonl` rules, security principles, and script paths.

## Default Mode

Read-only report. Do not edit files unless the user explicitly asks for a fix and approves the change.

Before checking, resolve the KB root using the conventions Root Resolution rules and read root guidance files from that resolved root, even if the current shell directory is elsewhere.

Run the two passes in order:

1. **Deterministic pass** — run `kb_lint.py` (see Deterministic Checks). It
   decides everything a machine can decide reliably and is cheap to re-run.
2. **Judgement pass** — read the documents `kb_lint.py` flagged, plus a sample of
   the rest, and apply the LLM-only checks (Content Health, duplicate topics,
   conflicting claims, split candidates, weak summaries, missing aliases).

Fixes are separate and only on explicit request:

- Index rebuild: run `kb_build_index.py --write` (regenerates the Documents
  catalog from frontmatter; preserves the human-written preamble).
- Frontmatter repair for one file: propose the change, then apply after approval.
- Related-document links: add a small focused section after approval.

Never auto-fix sensitive content. Report it and ask.

## Deterministic Checks

`kb_lint.py` reports frontmatter completeness, invalid `agent_edit_mode`, date
format, title/H1 mismatch, `_archived/` depth and read_only rules, `index.md`
link targets and coverage, broken relative Markdown links, `log.jsonl` JSON
validity, and high-confidence secret candidates.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-lint/scripts/kb_lint.py" /path/to/kb
```

Exit `0` clean, `1` findings present, `2` high-confidence secret candidates
present. It needs `python-frontmatter` (see `../kb-search/scripts/requirements.txt`).
Treat its output as the factual base for the report, then add the judgement-only
findings below.

## Checks

### Metadata

- missing YAML frontmatter where the KB requires it
- missing `title`, `summary`, `tags`, `aliases`, `created`, `updated`, `agent_edit_mode`
- invalid `agent_edit_mode`; expected `read_only`, `append_only`, or `editable`
- files under `_archived/` that are nested deeper than one level or do not use `agent_edit_mode: read_only`
- title/H1 mismatch
- invalid or inconsistent date format
- weak `summary`, sparse `tags`, missing likely aliases
- `updated` older than a meaningful body change suggested by git history as a supplementary signal; skip this for `append_only` documents, whose `updated` field is intentionally frozen (add a body-level dated note instead)
- `read_only` or `append_only` files with git changes that need confirmation

### Index

- `index.md` missing when the KB expects it
- documents absent from `index.md`
- index entries pointing to missing files
- stale summaries or categories
- duplicate or near-duplicate entries

### Log

- `log.jsonl` missing — it is the primary work-history trail and is expected by default, unless local KB rules opt out
- malformed `log.jsonl`, when present
- recent changed documents with no approximate log entry
- log entries pointing to missing files, when present
- log entries containing sensitive raw values, when present

`log.jsonl` is the primary work-history trail (it must work without git); git history is a supplementary reference. Neither is a source of truth for facts.

### Content Health

- `확인 필요`, `미정`, `추정`, `과거 정보` items that may need follow-up
- duplicate facts across documents where one source-of-truth document should own the topic
- conflicting claims between documents
- overly broad documents that should be split
- thin documents that need a clearer summary, current-state section, or related links

### Link Health

- broken Markdown links
- broken Obsidian wikilinks, if the KB uses them
- obvious missing related-document links
- excessive wikilinks that reduce readability

Missing related-document links are suggestions, not hard failures. Prefer focused pairs such as concept/system documents linked to usage/procedure documents.

### Security Hygiene

Flag candidates without repeating the raw value, in two tiers so the report does
not drown in false positives:

**High-confidence (auto-flagged by `kb_lint.py`)** — value-shaped matches:
AWS access key IDs, private-key blocks, GitHub/Slack tokens, JWTs, bearer tokens,
`password: <value>` assignments. These are near-certain and lead the report.

**Contextual (LLM judgement)** — keyword-adjacent candidates the linter cannot
confirm from shape alone, reported only after you judge them likely sensitive:

- cookies, sessions, OAuth/JWT, auth headers
- internal IPs, hosts, DB URLs, VPN/SSH/RDP details
- production/staging endpoints and sensitive access procedures
- personal data, account identifiers, customer/partner identifiers
- unresolved vulnerability details or exploit-like payloads

The grep below over-matches on purpose; use it as a candidate list, not a verdict.

## Suggested Commands

Inventory:

```bash
find . -path './.git' -prune -o -path './.obsidian' -prune -o -name '*.md' -print
```

Frontmatter and uncertainty:

```bash
rg -n --glob '*.md' "^---$|^title:|^summary:|^tags:|^aliases:|^created:|^updated:|확인 필요|미정|추정|과거 정보" .
```

Security candidate scan:

```bash
rg -n -i --glob '*.md' --glob '*.jsonl' \
  "password|passwd|token|secret|api[_-]?key|private key|cookie|session|jwt|bearer|ssh|vpn|host|internal|prod|staging|운영|비밀번호|토큰|시크릿|계정" .
```

Index/log drift:

```bash
test -f index.md && rg -n "\\.md\\)|\\.md" index.md
test -f log.jsonl && tail -100 log.jsonl
```

Agent edit-mode guard in git repositories:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/check_agent_edit_mode.py"
```

## Report Shape

```text
===== KB Lint Report =====

Root: /path/to/kb
Documents: N

High risk:
- [security-sensitive-candidate] path/to/file.md:line — value not repeated

Metadata:
- [missing-summary] path/to/file.md

Index/log:
- [index-missing-entry] path/to/file.md
- [log-malformed-json] log.jsonl:line

Content:
- [stale-confirm-needed] path/to/file.md:line
- [possible-duplicate-topic] A.md / B.md

Suggested next actions:
- ...
```

## Do Not

- Do not create `_raw/`, `_archive/`, canonical kinds, or daily-log schemas.
- Do not treat top-level `_archived/` as an error; it is valid when files are one depth below it and use `agent_edit_mode: read_only`.
- Do not silently remove or mask sensitive information.
- Do not rewrite documents during report mode.
- Do not bulk-add wikilinks. Suggest candidates first.
- Do not run git commands that change state.
