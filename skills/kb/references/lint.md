# Lint Mode

## Contents

- Overview
- Default Mode
- Deterministic Checks
- Scope and Reserved Paths
- Checks
- Suggested Commands
- Report Shape
- Do Not

## Overview

Health-check a curated Markdown KB. This lint model follows a source-of-truth document workflow: frontmatter, document clarity, `index.md`, `log.jsonl`, security hygiene, and search quality are what it checks.

**Shared rules:** Read [`conventions.md`](./conventions.md) completely and follow
its rules for KB root resolution, frontmatter fields, uncertainty markers,
`agent_edit_mode`, `index.md` / `log.jsonl`, security, and bundled-resource
routing.

**First-time recovery:** if no registered root resolves, switch to the config
bootstrap in [`manage.md`](./manage.md); never lint an unregistered absolute
path. If the helper exits `3`, follow the runtime setup in
[`getting-started.md`](./getting-started.md). Do not mutate config or install
packages without approval.

## Default Mode

Read-only report. Do not edit files unless the user explicitly asks for a fix and approves the change.

Before checking, resolve the KB root and read local root guidance per the conventions Root Resolution rules.

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

`kb_lint.py` reports frontmatter completeness, invalid or duplicate metadata, date
format, optional status validity, title/H1 mismatch, `index.md` link targets and coverage,
broken relative Markdown and asset links, broken Obsidian wikilinks (filename/path
resolution; code blocks excluded), absolute Markdown path warnings, applicable
history validity, and high-confidence secret candidates. Reported body line
numbers include YAML frontmatter.

Run the bundled `../scripts/kb_lint.py` with the absolute KB root.

Exit `0` clean, `1` findings present, `2` high-confidence secret candidates
present, `3` cannot run because the frontmatter runtime is missing (follow
[`getting-started.md`](./getting-started.md)). Run it with the getting-started
runtime. Treat its output as the factual base for the report, then add the
judgement-only findings below.

## Scope and Reserved Paths

Run `kb_lint.py <root> --files <paths>` to check only changed existing Markdown
files; paths must stay inside the root. Use full lint after moves/deletions,
and for periodic or migration-batch review. `--require-status` enforces roots
that require document status; generic legacy KBs keep it optional.

`_inbox/` and `_archived/` receive title/source, status/path consistency, and
link checks. Full normal metadata is not required there. Other reserved areas
and gitignored documents receive secret scanning only. Search/index exclusions
must not silently disable security scans. Hidden/dependency trees and symlinks
remain outside discovery. Secret scanning covers discovered Markdown and the
applicable log, not every binary or non-Markdown asset.

Unreadable/malformed Markdown is a `parse-error`; other files are still checked.
Parser source lines are not echoed. A malformed document still receives a raw
secret scan when readable. Parse failures are never a clean result.

During judgement review, inspect inbox candidates for a safe source and a body
note explaining the hold. Flag old candidates for promotion/review, not automatic
deletion. Check archived notes link to a replacement when one exists. Check
asset ownership and regeneration instructions in their referring document.

## Checks

If a machine can decide a check reliably, keep it in `[script]`; leave only
judgement-heavy review in `[LLM]`.

Normal-document checks below apply outside reserved paths; reserved-path checks
follow the scope rules above.

### Metadata

- `[script]` missing YAML frontmatter where the KB requires it
- `[script]` missing `title`, `summary`, `tags`, `aliases`, `created`, `updated`
- `[script]` invalid `agent_edit_mode`; expected `read_only`, `append_only`, or `editable`
- `[script]` duplicate aliases after case-insensitive normalization
- `[script]` title/H1 mismatch
- `[script]` invalid or inconsistent date format
- `[LLM]` weak `summary`, sparse `tags`, missing likely aliases
- `[LLM]` `updated` older than a meaningful body change suggested by git history as a supplementary signal; skip this for `append_only` documents, whose `updated` field is intentionally frozen (add a body-level dated note instead)
- `[script:guard]` `read_only` or `append_only` files with git changes that need confirmation

### Index

- `[LLM]` `index.md` missing when the KB expects it
- `[script]` documents absent from `index.md` (reserved `_*` paths are exempt;
  the build script can still include them when desired)
- `[script]` index entries pointing to missing files
- `[LLM]` stale summaries or categories
- `[LLM]` duplicate or near-duplicate entries

### Log

- `[script]` `log.jsonl` missing in a non-git KB
- `[script]` malformed `log.jsonl`, when present
- `[script]` setup template placeholders left in `log.jsonl`
- `[LLM]` recent changed documents with no approximate log entry
- `[LLM]` recent log entries pointing to missing files, when present; historical
  paths may legitimately have moved or been deleted
- `[script]` log entries containing sensitive raw values, when present

### Content Health

- `[LLM]` `확인 필요`, `미정`, `추정`, `과거 정보` items that may need follow-up
- `[LLM]` duplicate facts across documents where one source-of-truth document should own the topic
- `[LLM]` conflicting claims between documents
- `[LLM]` overly broad documents that should be split
- `[LLM]` thin documents that need a clearer summary, current-state section, or related links

### Link Health

- `[script]` broken Markdown links
- `[script]` absolute filesystem Markdown links reported as `absolute-path-link` warnings
  without checking whether the target exists
- `[script]` broken Obsidian wikilinks (`broken-wikilink`; resolves by filename
  or vault-relative path, ignores code blocks)
- `[LLM]` obvious missing related-document links
- `[LLM]` excessive wikilinks that reduce readability

Missing related-document links are suggestions, not hard failures. Prefer focused pairs such as concept/system documents linked to usage/procedure documents.

### Security Hygiene

Flag candidates without repeating the raw value, in two tiers so the report does
not drown in false positives:

**[script] High-confidence (auto-flagged by `kb_lint.py`)** — value-shaped matches:
AWS access key IDs, private-key blocks, GitHub/Slack tokens, JWTs, bearer tokens,
literal `password: <value>` assignments after excluding variable syntax,
named examples, and recognizable masking. These are near-certain and lead the report.

**[LLM] Contextual (LLM judgement)** — keyword-adjacent candidates the linter cannot
confirm from shape alone, reported only after you judge them likely sensitive:

- cookies, sessions, OAuth/JWT, auth headers
- internal IPs, hosts, DB URLs, VPN/SSH/RDP details
- production/staging endpoints and sensitive access procedures
- personal data, account identifiers, customer/partner identifiers
- unresolved vulnerability details or exploit-like payloads

The grep below over-matches on purpose; use it as a candidate list, not a verdict.

## Suggested Commands

Resolve the KB root per conventions (`scripts/resolve_kb_root.py`), then pass it explicitly to the lint helper.

Inventory:

```bash
find "$KB_ROOT" -path '*/.*' -prune -o -path '*/node_modules' -prune -o -name '*.md' -print
```

Frontmatter and uncertainty:

```bash
rg -n --glob '*.md' --glob '!**/.*/**' --glob '!**/.*' --glob '!**/node_modules/**' \
  "^---$|^title:|^summary:|^tags:|^aliases:|^created:|^updated:|확인 필요|미정|추정|과거 정보" "$KB_ROOT"
```

Security candidate scans (candidate only — review before reporting):

```bash
# Credentials and token-shaped context candidates.
rg -n -i --glob '*.md' --glob '*.jsonl' --glob '!**/.*/**' --glob '!**/.*' --glob '!**/node_modules/**' \
  "password|passwd|token|secret|api[_-]?key|private key|cookie|session|jwt|bearer" "$KB_ROOT"

# Infrastructure, endpoints, and access-path candidates.
rg -n -i --glob '*.md' --glob '*.jsonl' --glob '!**/.*/**' --glob '!**/.*' --glob '!**/node_modules/**' \
  "ssh|vpn|rdp|host|endpoint|internal|prod|staging|database|db[_-]?url|jdbc|redis|kafka" "$KB_ROOT"

# Korean security/access wording candidates.
rg -n -i --glob '*.md' --glob '*.jsonl' --glob '!**/.*/**' --glob '!**/.*' --glob '!**/node_modules/**' \
  "운영|비밀번호|토큰|시크릿|계정|내부|접속|인증|권한" "$KB_ROOT"
```

Index/log drift:

```bash
test -f "$KB_ROOT/index.md" && rg -n "\\.md\\)|\\.md" "$KB_ROOT/index.md"
test -f "$KB_ROOT/log.jsonl" && tail -100 "$KB_ROOT/log.jsonl"
```

For the agent edit-mode guard in git repositories, run the Git Guard from
[`conventions.md`](./conventions.md) (`scripts/check_agent_edit_mode.py`).

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
- Do not report findings for underscore-prefixed paths (`_inbox/`, `_archived/`, ...) other than secret candidates.
- Do not silently remove or mask sensitive information.
- Do not rewrite documents during report mode.
- Do not bulk-add wikilinks. Suggest candidates first.
- Do not run git commands that change state.
