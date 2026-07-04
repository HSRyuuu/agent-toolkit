# KB Shared Conventions

Single source of truth for the rules every KB skill shares: KB identity, root
resolution, uncertainty markers, frontmatter, `agent_edit_mode`, `index.md` /
`log.jsonl`, security principles, and the global Do-Not list.

`kb-manage`, `kb-write`, `kb-search`, and `kb-lint` all defer to this file. When
a rule here conflicts with a skill's own prose, this file wins. When local KB
guidance (`AGENTS.md`, `CLAUDE.md`, `.agents/rules/*.md` at the resolved root)
conflicts with this file, the local guidance wins.

## Script Paths

Skill scripts live under the plugin root. In Claude Code the plugin root is
injected as `${CLAUDE_PLUGIN_ROOT}`:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/resolve_kb_root.py"
```

If `${CLAUDE_PLUGIN_ROOT}` is unset (for example under Codex), resolve the path
relative to the invoking `SKILL.md`'s location instead.

## KB Identity

The KB is a curated Markdown repository where maintained documents are the
single source of truth.

- Human-readable documents are primary.
- LLMs help add, search, lint, and reorganize.
- `index.md` is the content catalog.
- `log.jsonl`, when present, is a small work-history pointer for finding files
  and git history, not a source of truth.
- Git history is the durable audit trail.
- Provenance is recorded safely in frontmatter or body notes, never by storing
  raw source copies.
- Security and privacy override source preservation.

This model uses maintained documents as the foundation. It does not use a
`sources -> wiki -> schema` shape, `_raw/` source preservation, or required
`kind: canonical` / `kind: daily-log` document types. Migration away from those
older shapes is described in `kb-manage`.

## Uncertainty Markers

The only uncertainty markers are these four. Do not invent synonyms; consistency
is what lets `kb-lint` and search find every uncertain item.

- `확인 필요` — needs confirmation
- `미정` — undecided
- `추정` — estimated / inferred
- `과거 정보` — past information, possibly stale

Do not mix confirmed facts with guesses. Put currentness and uncertainty in the
document body, never in frontmatter.

## Root Resolution

Resolve the KB root from the first matching source:

1. A user-provided absolute path, or a registered KB name.
2. The current working directory, only when it is inside a **registered** KB root.
3. The configured `default` KB.
4. The single registered KB, when exactly one is configured.

If none resolves (nothing configured, or several KBs registered with no default
and cwd outside all of them), ask the user which KB to use. Never infer a KB root
from an *unregistered* directory, parent directories, `index.md`, `log.jsonl`,
`.obsidian/`, frontmatter, or guidance files. Step 2 only ever selects a root the
user explicitly registered.

The config file `~/.config/kb/kb-config.json` is a UTF-8 JSON object. Single-KB
shape (back-compatible; `kb_root` and `root` are aliases for `path`):

```json
{ "path": "/absolute/path/to/kb" }
```

Multiple-KB shape:

```json
{
  "kbs": { "personal": "/abs/personal", "work": "/abs/work" },
  "default": "personal"
}
```

For the fastest deterministic check:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/resolve_kb_root.py"
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/resolve_kb_root.py" /absolute/path/to/kb
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/resolve_kb_root.py" work   # by registered name
```

The script prints the resolved root on stdout and exits nonzero (with a reason)
when the root is unresolved or ambiguous.

After resolving the root, always read local guidance from the resolved root
(not only the current shell directory), in this order: `AGENTS.md`, `CLAUDE.md`,
`.agents/rules/*.md`. Local root guidance overrides these generic conventions.

## Frontmatter

Use local KB rules if present. Otherwise use this default:

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
agent_edit_mode: editable
---
```

Required fields: `title`, `summary`, `tags`, `aliases`, `created`, `updated`,
`agent_edit_mode`. Optional: `source`.

Field rules:

- `title`: human-readable title; should match or nearly match the H1.
- `summary`: one-sentence summary useful in search results and `index.md`.
- `tags`: searchable keywords such as domain, system, topic, acronym, team, or
  workflow. Lower-kebab-case unless a proper noun has a real spelling.
- `aliases`: alternate names someone may search for, including local-language
  names, English names, acronyms, and old names. Required, but `aliases: []` is
  allowed when a document genuinely has no alternate name — do not invent filler.
- `created`: first creation date in `YYYY-MM-DD`.
- `updated`: last meaningful update date in `YYYY-MM-DD`.
- `source`: safe provenance such as `user-note`, `meeting`, `slack`, `docs`, a
  filename, or a non-sensitive URL.
- `agent_edit_mode`: one of `read_only`, `append_only`, or `editable`. Normal KB
  documents use `editable` unless the owner chooses otherwise.

Writing rules:

- Put frontmatter at the top of Markdown files; use YAML lists for array fields
  even with one value.
- Do not put secrets, credentials, private infrastructure, personal data, or
  sensitive identifiers in frontmatter.

Scope:

- Apply to normal KB documents and KB rule documents.
- Do not add frontmatter to root entrypoints (`AGENTS.md`, `CLAUDE.md`), to
  plugin `SKILL.md` files, or to non-Markdown files.
- Do not add `kind: canonical`, `kind: daily-log`, or raw-source link fields
  unless the local KB already uses them intentionally.

## Agent Edit Mode

`agent_edit_mode` controls what an agent may do to an individual Markdown file.
Human edits are always allowed; this policy exists so agents stop before
rewriting protected notes.

| Value | Agent rule |
|---|---|
| `read_only` | No agent edits. Do not add, delete, rewrite, rename, reformat, or change frontmatter. Ask the user instead. |
| `append_only` | Preserve all existing text exactly. Add new content where it fits (between sections, as notes, or as `>` blockquotes), but do not delete, edit, reorder, or restructure existing text, and do not change existing frontmatter values such as `updated`; add a body note instead unless the user approves. |
| `editable` | Full editing: wording, structure, merges, removals, and frontmatter cleanup are allowed while preserving important facts and source meaning. |

When a file has no `agent_edit_mode`, use local KB rules. If none exist, treat
new documents as `editable` and add the field during the next meaningful update.

### Git Guard

In a git-backed KB, run this guard after changing Markdown files and before
reporting completion or preparing a git action:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/check_agent_edit_mode.py"
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/check_agent_edit_mode.py" --staged
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/check_agent_edit_mode.py" --files path/a.md path/b.md
```

Protection is judged by each file's **baseline** (pre-change) `agent_edit_mode`:

- `read_only` baseline: any tracked content change, rename, or deletion is a
  violation (exit 1).
- `append_only` baseline: the previous tracked file must remain an exact ordered
  subsequence of the new file; additions anywhere pass, deletions / edits /
  reordering / frontmatter value changes fail.
- Transitions into a protected mode are allowed. Creating a new protected file,
  or archiving an `editable` document to `read_only`, is reported as an
  informational `Notes:` line, not a violation.
- `--files` limits the check to the listed paths (use it to check only the
  documents this task touched); with no `--files`, all changed Markdown is
  checked (use for lint).
- Exit `0`: no violations. Exit `1`: violation — stop and ask the user whether
  the change was human-intended. Exit `2`: no usable git baseline.

Git cannot prove whether a human or an agent made a change. On a reported
violation, name the protected file and ask: `이 변경이 사람이 의도한 변경이 맞나요?`
Continue only after the user confirms. For a non-git KB, this check is not
enforceable from history; rely on the frontmatter rule and explicit approval.

## index.md

`index.md` is the human- and LLM-facing document catalog. Include a document
link, one-line summary, important tags/category, and `updated` date when
available. Do not include every heading or long excerpts. Keep it
content-oriented, not chronological.

Default shape:

```markdown
# Knowledge Base Index

이 문서는 KB의 문서 카탈로그이다. 자세한 사실은 각 원문 문서를 기준으로 확인한다.

## Documents

| Document | Summary | Tags | Updated |
|---|---|---|---|
| [Example](./example.md) | One-line summary. | `kb` | 2026-06-30 |
```

List `_inbox/` and `_archived/` documents, when included, under clearly labeled
sections so readers do not mistake them for maintained documents.

## log.jsonl

`log.jsonl` is optional. It exists only to make git history easier to navigate;
it is not a source of truth and not a replacement for git. In a git-backed KB,
`git log --oneline --name-only` provides the same information for free, so
`log.jsonl` is created only for a non-git KB or when the user wants a work-history
file. If it is absent during search or exploration, ignore it and continue.

When the KB maintains it, each line is one JSON object:

```json
{"datetime":"YYYY-MM-DDTHH:MM:SS+09:00","type":"setup|add|update|merge|append|lint","summary":"짧은 작업 요약","files":["index.md"],"source":"agent","commit":null}
```

Rules: one object per line, no trailing commas, no secrets, paths relative to KB
root, `datetime` includes a timezone offset (KB/user local timezone when known),
`commit` may be `null` until a commit exists.

When a KB is git-backed, prefer a searchable commit message convention so git
history stays navigable without `log.jsonl`:

```text
kb: add|update|merge|append <doc> — <short summary>
```

## Security Principles

Do not store, in documents or `log.jsonl`, without explicit user approval:

- passwords, tokens, API keys, private keys, credentials, OAuth/JWT, cookies,
  sessions
- internal IPs, hosts, DB URLs, VPN/SSH/RDP details, production/staging endpoints
- detailed access procedures, privilege workarounds, security exceptions
- personal data, account identifiers, customer/partner identifiers
- vulnerability reproduction steps or exploit-like payloads

Redaction defaults: mask secrets (`[REDACTED]`), summarize infrastructure by
role (`internal API server`, `production database`), keep only the minimum
necessary personal context, and preserve procedural meaning while withholding
exploit-level detail. If a secret was already committed, recommend rotating the
value first; rewriting git history is the user's decision. `kb-write` holds the
operational security gate; `kb-lint` reports candidates without repeating values.

## Do Not

- Do not create `_raw/` or preserve raw source text by default.
- Do not require Obsidian-specific features.
- Do not bulk-insert wikilinks; suggest focused pairs instead.
- Do not modify git state from a read-only skill.
- Do not overwrite existing setup files without showing the change first.
