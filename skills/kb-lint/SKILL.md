---
name: kb-lint
description: Use when checking a Markdown Knowledge Base for metadata gaps, stale uncertainty, duplicate topics, index/log drift, broken links, or security-sensitive content.
---

# kb-lint

## Overview

Health-check a curated Markdown KB. This lint model follows a source-of-truth document workflow: frontmatter, document clarity, `index.md`, `log.jsonl`, security hygiene, and search quality matter more than raw-source preservation or canonical/daily-log schemas.

**Required orientation:** read and follow `kb-manage` for KB root, identity, repository defaults, frontmatter, `index.md`, `log.jsonl`, and shared conventions.

## Default Mode

Read-only report. Do not edit files unless the user explicitly asks for a fix mode and approves the proposed changes.

Before checking, resolve the KB root using `kb-manage` rules and read root guidance files from that resolved root, even if the current shell directory is elsewhere.

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
- title/H1 mismatch
- invalid or inconsistent date format
- weak `summary`, sparse `tags`, missing likely aliases
- `updated` older than a meaningful body change indicated by git history
- `read_only` or `append_only` files with git changes that need confirmation

### Index

- `index.md` missing when the KB expects it
- documents absent from `index.md`
- index entries pointing to missing files
- stale summaries or categories
- duplicate or near-duplicate entries

### Log

- malformed `log.jsonl`
- recent changed documents with no approximate log entry
- log entries pointing to missing files
- log entries containing sensitive raw values

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
python3 /path/to/agent-toolkit/skills/kb-manage/scripts/check_agent_edit_mode.py
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
- Do not silently remove or mask sensitive information.
- Do not rewrite documents during report mode.
- Do not bulk-add wikilinks. Suggest candidates first.
- Do not run git commands that change state.
