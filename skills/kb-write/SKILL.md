---
name: kb-write
description: Use when adding, merging, or reorganizing concrete knowledge in a Markdown Knowledge Base, especially from notes, files, URLs, meetings, onboarding, procedures, decisions, or project context.
---

# kb-write

## Overview

Add knowledge to a Markdown KB as curated source-of-truth documents. The maintained document is the truth surface; raw-source preservation, `_raw/`, canonical/daily-log kinds, and `sources -> wiki -> schema` are not part of this workflow.

**Required orientation:** read and follow `kb-manage` for KB root, identity, repository defaults, frontmatter, `index.md`, `log.jsonl`, and shared conventions.

## Core Principles

- Preserve facts, numbers, dates, names, conditions, uncertainty, and user intent.
- Do not mix confirmed facts with guesses. Mark uncertain items as `확인 필요`, `미정`, `추정`, or `과거 정보`.
- Do not store secrets, tokens, passwords, private keys, session/cookie values, internal hosts/IPs, sensitive access steps, or unnecessary personal data without explicit user approval.
- Prefer one focused document per topic, system, procedure, decision, or working context.
- Update existing documents when the input changes or extends an existing topic.
- Create new documents when the input is a distinct topic that someone would naturally search for later.
- Keep the KB readable by humans first; Obsidian links and graph health are secondary.
- Never create `_raw/` for source preservation. If provenance matters, record a safe `source` value in frontmatter or a short source note in the body.

## Required First Reads

Before writing:

1. Resolve the KB root using `kb-manage` rules.
2. Read root guidance files from the resolved KB root, even if the current shell directory is elsewhere: `AGENTS.md`, `CLAUDE.md`, `.agents/rules/*.md`, or equivalent.
3. Read `index.md` if present to find existing topics.
4. Read relevant directory `README.md` files when choosing or using a folder. They describe folder intent, not file inventory.
5. Read relevant existing documents before deciding create/append/merge.
6. Check each target document's `agent_edit_mode` before drafting edits.

If the KB has project-local add/search/security/writing rules, follow those over the generic defaults here.

## Optional Obsidian Skill Use

Use Obsidian skills only when they are available and the write task needs Obsidian-specific behavior. Read `kb-manage` and, when relevant, its `references/obsidian-skills.md` guidance first. Plain Markdown KB writing must work without these skills.

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

## Security Gate

Pause and ask before writing if the input or target document contains:

- passwords, tokens, API keys, private keys, credentials, OAuth/JWT, cookies, sessions
- internal IPs, hosts, DB URLs, VPN/SSH/RDP details, production/staging endpoints
- detailed access procedures, privilege workarounds, security exceptions
- personal information, account identifiers, customer/partner identifiers
- vulnerability reproduction steps or exploit-like payloads

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

Follow `kb-manage` for the authoritative `agent_edit_mode` definition.

| Mode | Write behavior |
|---|---|
| `read_only` | Do not edit the file at all. If the user asks for a change, explain that the file is protected and ask for explicit approval before changing it. |
| `append_only` | Keep the original file text exactly intact. You may add new content anywhere: below a relevant heading, between paragraphs, in a new section, or as a Markdown blockquote/comment near the source context. Prefer `>` blockquotes when adding commentary that should sit beside preserved original text. Do not rewrite sentences, delete text, rename headings, reorder sections, change existing frontmatter values, or clean up formatting. |
| `editable` | Normal KB writing rules apply. Text edits, structure changes, merges, removals, and frontmatter cleanup are allowed when they preserve important facts and meaning. |

If a target file has no `agent_edit_mode`, use local KB rules. If none exist, treat it as `editable` and add `agent_edit_mode: editable` during the next meaningful update.

In a git-backed KB, after writing and before completion or any git action, run the guard from `kb-manage`:

```bash
python3 /path/to/agent-toolkit/skills/kb-manage/scripts/check_agent_edit_mode.py
```

If it reports a `read_only` or `append_only` violation, stop. Tell the user which protected file changed and ask whether the change was intentional. Human edits are allowed, but agent-made protected changes require user confirmation.

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
- Add YAML frontmatter when the KB uses it.
- Required frontmatter default:

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

## Index And Log

After successful writes:

1. Update `index.md` if present.
   - Add or adjust the document link, one-line summary, and tags/category.
   - Keep it content-oriented, not chronological.
2. Append one JSON object to `log.jsonl` if present.
   - Keep it short and parseable.
   - Do not include secrets or sensitive raw details.

Recommended log shape:

```json
{"datetime":"YYYY-MM-DDTHH:MM:SS+09:00","type":"add|update|merge|append","summary":"짧은 작업 요약","files":["path/to/doc.md"],"source":"user-note","commit":null}
```

Use timezone-aware ISO 8601 datetimes. Prefer the KB/user local timezone when known; never write a bare date or timezone-less local time.

If `index.md` or `log.jsonl` does not exist, do not create them unless the user asked for KB setup/management or the local rules say they are required.

## Completion Report

Report briefly:

- created/modified files
- mode used: create, merge, append
- any index/log updates
- `agent_edit_mode` guard result when protected files were touched
- security-sensitive items excluded or masked
- remaining `확인 필요` items

Do not claim the KB is fully up to date unless `index.md`, `log.jsonl`, and related documents were checked.
