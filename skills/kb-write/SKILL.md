---
name: kb-write
description: >
  Use when the user wants to save, add, file, merge, or organize knowledge in a
  personal Markdown Knowledge Base (KB), including notes, URLs, meetings,
  onboarding, procedures, decisions, and project context. Triggers:
  "kb에 저장/추가/정리해줘", "이거 메모/기록해둬", "지식베이스에 넣어줘". Do NOT use
  for KB search, setup, migration, or linting.
---

# kb-write

## Overview

Add knowledge to a Markdown KB as curated source-of-truth documents. The
maintained document is the truth surface.

**REQUIRED SKILL:** Load `kb-manage` by name and follow its shared conventions
for KB root resolution, frontmatter, `agent_edit_mode`, uncertainty markers,
`index.md` / `log.jsonl`, security, setup, folder structure, and migration.

If this is the user's first KB write or no registered root resolves, route to
`kb-manage` config bootstrap. Every KB root must be registered before writing.
When config is missing or empty, propose `~/KnowledgeBase` and allow the user to
choose another absolute directory.

## Fast Path vs Full Path

Most writes are small. Do not run the full ritual for a one-line note.

- **Fast path** (default): the input is a single topic, contains no
  security-sensitive candidate, and has an obvious owning document (or clearly
  needs one new document). Steps: resolve root → read the target document (and
  `index.md`) → one security scan → write → update `index.md`. Skip the routing
  table and the washing prompt; apply their spirit inline.
- **Full path**: use the sections below (Ambiguity Gate, Multi-document Write,
  Security Gate, Document Washing) when the input spans multiple topics, trips a
  security candidate, needs large restructuring, or conflicts with existing facts.

## Core Principles

- Preserve facts, numbers, dates, names, conditions, uncertainty, and user intent.
- Do not mix confirmed facts with guesses. Use the canonical uncertainty markers
  (`확인 필요`, `미정`, `추정`, `과거 정보`) from conventions.
- Follow the conventions Security Principles storage restrictions; do not store
  sensitive values without explicit user approval (see Security Gate).
- Prefer one focused document per topic, system, procedure, decision, or working
  context.
- Update existing documents when the input changes or extends an existing topic;
  create a new document when the input is a distinct topic someone would search
  for later.
- Keep the KB readable by humans first; Obsidian links and graph health are
  secondary.
- If provenance matters, record a safe `source` value in frontmatter or a short
  body note rather than storing raw source copies.
- Archive retired documents per `kb-manage`: move to top-level `_archived/`, at
  most one grouping subfolder deep, and set `agent_edit_mode: read_only`.

## Required First Reads

Before writing:

1. Resolve the KB root using the conventions Root Resolution rules; if none
   resolves, stop and route to `kb-manage` config bootstrap. Do not write to an
   unregistered absolute path or treat the current directory as a new KB.
2. Read root guidance from the resolved root (`AGENTS.md`, `CLAUDE.md`,
   `.agents/rules/*.md`), even if the shell directory is elsewhere.
3. Read `index.md` if present to find existing topics.
4. Read relevant directory `README.md` files when choosing a folder (intent, not
   inventory).
5. Read relevant existing documents before deciding create/append/merge.
6. Check each target document's `agent_edit_mode` before drafting edits.

If the KB has project-local add/search/security/writing rules, follow those over the generic defaults here.

## Optional Obsidian Skill Use

Use Obsidian skills only when they are available and the write task needs
Obsidian-specific behavior. Route to `kb-manage` for its optional Obsidian
guidance first. Plain Markdown KB writing must work without these skills.

| Situation during write | Helpful skill | Use it for | Keep `kb-write` responsible for |
|---|---|---|---|
| Creating or editing Obsidian-flavored notes | `obsidian-markdown` | wikilinks, embeds, callouts, properties/frontmatter syntax, Obsidian Markdown conventions | document ownership, factual preservation, security gate, washing, index/log updates |
| User asks to add internal links between notes | `obsidian-markdown` | checking wikilink syntax and suggesting focused links | avoiding bulk links; only adding links that support the document's meaning |
| User asks for a database-like Obsidian view | `obsidian-bases` | `.base` files, table/card views, filters, formulas, summaries | deciding which KB documents are source of truth and whether a view is needed |
| User asks for a visual map or canvas | `json-canvas` | `.canvas` files, nodes, edges, groups, relationships | preserving the source documents and not replacing them with a canvas-only artifact |
| User asks to interact with an Obsidian vault directly | `obsidian-cli` | vault search, note creation, note updates, plugin/theme-oriented vault operations | applying KB root guidance, write modes, security review, and completion reporting |
| User provides a web page to turn into a note | `defuddle` | extracting clean Markdown from a web page | curating the extracted content into a maintained KB document instead of storing raw source |

Do not use Obsidian skills just because a KB has `.obsidian/`. Use them when the requested output or local KB rules actually need Obsidian behavior.

## Input Handling

| Input | Action |
|---|---|
| Pasted text | Treat the provided text as the source context. |
| Local file path | Read the file, then write a curated KB document or update. Do not copy the source into `_raw/`. |
| URL | Read/extract the useful content if available, then store only the curated result and safe source reference. |
| Archive request | Move the document to top-level `_archived/<filename>.md`, set `agent_edit_mode: read_only`, and update `index.md`/`log.jsonl` if maintained. |
| Stub or unfinished document | Move it to `_inbox/stubs/` when it only names a future topic or says "to be written". Do not leave it in a normal topic folder where it may look authoritative. |
| Broad question | Do not add. Use `kb-search` unless the user explicitly asks to file the answer back. |
| Ambiguous note | Ask only when a wrong document choice would be risky; otherwise choose the most natural location. |

## Ambiguity Gate

Do not ask by default, but pause before writing when a wrong choice could lose meaning or scatter ownership.

Ask or present a short split plan when:

- one input clearly contains multiple topics that should land in different documents
- part of the input belongs in an existing document and part needs a new document
- several existing documents could own the same fact
- the user asks for a merge but the target section is unclear
- the input conflicts with existing facts and the current source of truth is not obvious

When asking, state what is ambiguous and propose the smallest useful options. Preserve all input until the user decides.

## Multi-document Write

Use this when one input contains multiple durable knowledge units.

1. Split the input into the smallest useful units by topic, system, procedure, decision, or working context.
2. For each unit, choose one route:
   - `merge`: update an existing source-of-truth document
   - `append`: add to an intentionally accumulating document
   - `create`: make a new document when no existing document naturally owns it
   - `skip`: do not store broad questions, duplicates, or unsafe details
3. Read `index.md`, relevant directory `README.md` files, and candidate target documents before final routing.
4. Proceed without asking only when every unit has a clear owner, no content conflict, no security gate issue, and no protected edit-mode issue.
5. When routing is ambiguous, stop before writing that unit. Present candidate targets and ask the user to decide where it belongs.

Candidate routing format:

| Unit | Candidate target | Route | Why this target | Decision needed |
|---|---|---|---|---|
| Short unit label | `path/to/doc.md` or new path | `merge/create/append/skip` | One-line reason | Ask the user to choose or confirm |

Do not scatter facts across documents by guessing. Preserve the original input until the user resolves ambiguous routing.

## Security Gate

Pause and ask before writing when the input or target document matches the
conventions Security Principles storage-restriction list.

Ask with value-free wording:

```text
문서에 넣기 전에 보안 확인이 필요합니다.

- 후보: [값을 직접 반복하지 않고 종류와 위치만]
- 위험: [유출 시 문제]
- 권장: [마스킹/요약/제외/확인 필요]

원문 그대로 포함할까요, 마스킹/요약해서 남길까요, 아니면 제외할까요?
```

Use this internal review prompt before every write:

```text
Security review:
1. Does the input or target document include credentials, secrets, internal access details, private infrastructure, personal data, customer/partner identifiers, or exploit-level vulnerability details?
2. If yes, classify the candidate conservatively and stop before writing. Do not repeat the sensitive value. Ask whether to keep, mask, summarize, or exclude it.
3. If no, continue.
4. Before the final write, scan the draft again for unapproved sensitive values.
```

Redaction rules:

- Passwords, tokens, secrets, private keys, API keys, cookies, and sessions are not stored verbatim by default. Use `[REDACTED]`, `[token omitted]`, or a local-language equivalent when a marker is useful.
- Internal hosts, IPs, production/staging endpoints, database connection details, VPN/SSH/RDP details, and admin URLs require explicit approval if exact values are necessary. Usually summarize them by role, such as `internal API server`, `production database`, or `VPN-only service`.
- Preserve procedural knowledge, but summarize or withhold steps that would enable privilege bypass, unauthorized access, or exploitation.
- Keep only the minimum necessary personal/account/customer/partner context.
- If new input reveals that existing KB content already contains sensitive values, ask whether to clean the existing document before adding more.
- If redaction would make the document misleading or unusable, mark the gap as `needs confirmation` or the local equivalent.

Completion check:

- No unapproved secret, credential, key, token, session, or password remains.
- Exact internal hosts/IPs/URLs/account identifiers have an approval reason if retained.
- Sensitive procedures are not more detailed than necessary.
- Redacted sections still preserve the useful meaning or explicitly mark the missing context.

## Agent Edit Mode Gate

Conventions holds the authoritative `agent_edit_mode` definition. As write
behavior: `read_only` — do not edit; explain it is protected and ask before any
change. `append_only` — keep original text exactly, add new content around it
(prefer `>` blockquotes for commentary), never rewrite/delete/reorder or change
existing frontmatter values. `editable` — normal writing applies.

If a target file has no `agent_edit_mode`, use local KB rules; if none, treat it
as `editable` and add the field during the next meaningful update.

In a git-backed KB, after writing and before completion or any git action, run
the guard, scoped to the files this task touched:

Route to `kb-manage` and run its bundled edit-mode guard for the target files.

If it reports a `read_only` or `append_only` violation, stop. Name the protected
file and ask whether the change was intentional. Human edits are allowed; agent
protected changes require confirmation.

In a non-git KB, the guard cannot compare against tracked history. Respect the field directly and ask before any protected change.

## Document Washing Protocol

Apply this internal prompt when turning rough input into a KB document:

```text
Document wash:
1. Preserve facts, numbers, conditions, dates, names, responsibility boundaries, technical terms, conclusions, and user intent.
2. Improve sentence length, duplicate phrasing, heading hierarchy, list structure, table structure, and reading order.
3. Do not add facts, background knowledge, stronger claims, or inferred conclusions.
4. Keep uncertainty visible with `확인 필요`, `미정`, `추정`, or `과거 정보`.
5. Prefer conservative work-document tone unless local rules say otherwise.
6. Use tables only when they improve scanning or comparison.
7. Final check: the title, headings, and lists should let a reader understand the document quickly without losing the original meaning.
```

Default editing level:

- Light wash: preserve order and meaning; fix wording, duplication, and clarity.
- Structure wash: reorganize headings, sections, lists, or tables when the input is long or scattered.
- Tone wash: change tone only when the user or local rules request it.

Preservation rules:

- Do not fill missing background from general knowledge.
- Keep negations, limitations, exceptions, dates, numbers, owners, system names, and responsibility boundaries intact.
- If a phrase carries the author's intent or local working context, do not erase it just to make the prose smoother.
- If the user asks for "only typos", "expression only", or "preserve as much as possible", narrow the edit.
- If the user asks for "make it readable", "document style", or "report style", improve structure and flow while preserving meaning.

## Write Modes

### Create New Document

Use when no existing document naturally owns the topic.

- Choose the most natural filename language.
- Follow the target folder's `README.md` when present.
- Korean business docs: `한글_파일명.md`.
- English technical terms: `lower-kebab-case.md`.
- Add YAML frontmatter using the schema in conventions (Frontmatter) when the KB
  uses it.

### Merge Into Existing Document

Use when the new input updates current knowledge.

- Read the full relevant section first.
- Respect `agent_edit_mode` before merging; `read_only` cannot be merged into, and `append_only` can only receive additive notes.
- Preserve existing facts unless the new input clearly supersedes them.
- If new and old information conflict, do not silently choose; mark the conflict and what needs confirmation.
- Update `updated` when the KB uses that frontmatter field and the file is `editable`; for `append_only`, add an update note instead unless the user approves changing frontmatter.

### Append To Existing Document

Use when the document intentionally accumulates dated notes, examples, or change history.

- Add the new material where it fits the existing structure.
- For `append_only`, preserve the original text exactly and add content around it without rewriting it.
- Avoid repeating the same fact in multiple sections.
- Include exact dates when dates affect meaning.

### Archive Existing Document

Use when the user wants to retire a KB document without deleting it.

- Follow the `_archived/` rules from `kb-manage`.
- Preserve the original filename unless `_archived/` already has that file.
- Keep the document content intact except for the minimum frontmatter change needed to set `agent_edit_mode: read_only`.
- Do not invent extra archive metadata unless local KB rules require it or the user asks.

### Move To Inbox Stub

Use when a document is only a placeholder and does not yet contain maintained knowledge.

- Move it under top-level `_inbox/stubs/`.
- Keep or add frontmatter so it remains searchable.
- Add tags such as `inbox` and `stub` while preserving useful topic tags.
- Remove it from the main maintained-document section of `index.md`; if helpful, list it under a clearly labeled "Inbox" or "Stubs" section.
- When the stub becomes a real document, move it to the owning folder and update `summary`, `tags`, related links, `index.md`, and `log.jsonl` if maintained.

### Related Document Links

Add a small related-documents section when it improves human navigation and search follow-up.

Best candidates:

- a concept/system page and its usage/procedure page
- an architecture page and a troubleshooting page
- a glossary page and a domain/system page that depends on the term

Keep links selective. Do not bulk-add wikilinks or graph-style links. Use normal Markdown links unless local Obsidian rules say otherwise.

## Index And Log

After successful writes:

1. Update `index.md` if present.
   - Add or adjust the document link, one-line summary, and tags/category.
   - Keep it content-oriented, not chronological.
2. Append one JSON object to `log.jsonl` — it is the primary work-history
   trail and works without git.
   - Keep it short and parseable.
   - Do not include secrets or sensitive raw details.

Recommended log shape:

```json
{"datetime":"YYYY-MM-DDTHH:MM:SS+09:00","type":"add|update|merge|append","summary":"짧은 작업 요약","files":["path/to/doc.md"],"source":"user-note","commit":null}
```

Use timezone-aware ISO 8601 datetimes. Prefer the KB/user local timezone when known; never write a bare date or timezone-less local time.

If `index.md` does not exist, do not create it unless the user asked for KB setup/management or the local rules say it is required. If `log.jsonl` is missing, create it with this write's entry (it is the default work-history file) unless local KB rules opt out; mention the creation in the completion report. A log problem should never block the write itself.

In a git-backed KB, git is a supplementary reference: when the user commits KB work, suggest the `kb: add|update|merge|append <doc> — <summary>` commit-message convention from conventions so git history stays searchable, but never treat a commit as a substitute for the `log.jsonl` entry.

## Completion Report

Report briefly:

- created/modified files
- mode used: create, merge, append
- routing summary when one input was split across multiple documents
- any index/log updates
- `agent_edit_mode` guard result when protected files were touched
- security-sensitive items excluded or masked
- remaining `확인 필요` items

Do not claim the KB is fully up to date unless `index.md`, `log.jsonl`, and related documents were checked.
