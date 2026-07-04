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

Read-only report. Do not edit files unless the user explicitly asks for a fix mode and approves the proposed changes.

Before checking, resolve the KB root using the conventions Root Resolution rules and read root guidance files from that resolved root, even if the current shell directory is elsewhere.

Allowed fix modes:

- `--fix-index`: update `index.md` entries from current documents.
- `--fix-frontmatter FILE`: propose and apply frontmatter repairs for one file after approval.
- `--boost-links FILE`: add a small related-documents section after approval.

Never auto-fix sensitive content. Report it and ask.

## Checks

### Metadata

- missing YAML frontmatter where the KB requires it
- missing `title`, `summary`, `tags`, `aliases`, `created`, `updated`, `agent_edit_mode`
- invalid `agent_edit_mode`; expected `read_only`, `append_only`, or `editable`
- files under `_archived/` that are nested deeper than one level or do not use `agent_edit_mode: read_only`
- title/H1 mismatch
- invalid or inconsistent date format
- weak `summary`, sparse `tags`, missing likely aliases
- `updated` older than a meaningful body change indicated by git history; skip this for `append_only` documents, whose `updated` field is intentionally frozen (add a body-level dated note instead)
- `read_only` or `append_only` files with git changes that need confirmation

### Index

- `index.md` missing when the KB expects it
- documents absent from `index.md`
- index entries pointing to missing files
- stale summaries or categories
- duplicate or near-duplicate entries

### Log

- malformed `log.jsonl`, when present
- recent changed documents with no approximate log entry, when the KB maintains `log.jsonl`
- log entries pointing to missing files, when present
- log entries containing sensitive raw values, when present

`log.jsonl` is an aid for finding work and git history. It is not a source of truth.

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

Flag candidates without repeating the raw value:

- passwords, tokens, API keys, private keys, credentials
- cookies, sessions, OAuth/JWT, auth headers
- internal IPs, hosts, DB URLs, VPN/SSH/RDP details
- production/staging endpoints and sensitive access procedures
- personal data, account identifiers, customer/partner identifiers
- unresolved vulnerability details or exploit-like payloads

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
