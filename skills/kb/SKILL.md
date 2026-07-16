---
name: kb
description: >
  Use when working with a personal Markdown Knowledge Base (KB). Triggers include
  "kb에 저장/추가/정리해줘", "이거 메모/기록해둬", "지식베이스에 넣어줘",
  "kb에서 찾아줘/검색해줘", "지식베이스에 ~ 있나", "전에 정리해둔 거 어디",
  "kb 점검/린트해줘", "지식베이스 상태 확인", "인덱스/링크 깨진 데 있나",
  "kb 만들어줘/셋업", "지식베이스 정리 규칙", "kb 루트 어디", and "인덱스 정리".
  Do not use for ordinary project documentation that is not a registered personal KB.
---

# KB

Route personal Markdown KB work to exactly one primary mode, then follow that
mode's reference. Maintained documents are the source-of-truth surface.

## Routing

Apply the first matching route:

1. **Write** — save, add, file, merge, append, archive, or organize knowledge;
   Korean cues include 저장, 추가, 정리, 기록, 메모, 병합, 아카이브.
   Read [`references/write.md`](references/write.md).
2. **Search** — answer a KB question, find a document, or check whether
   something is recorded without editing; cues include 검색, 질문, 확인, 찾아줘.
   Read [`references/search.md`](references/search.md).
3. **Lint** — health-check metadata, links, uncertainty, duplicates, secrets,
   index/log drift, or KB status; cues include 점검, 린트, 상태, 드리프트.
   Read [`references/lint.md`](references/lint.md).
4. **Manage** — set up or resolve a KB root, explain rules, migrate a layout,
   or maintain identity/index/log infrastructure.
   Read [`references/manage.md`](references/manage.md).

If more than one route is plausible and the primary outcome changes what may be
edited, ask the user which outcome they want. Otherwise use the first match and
invoke a secondary mode only when its own gate is satisfied.

## Shared Invariants

- Read [`references/conventions.md`](references/conventions.md) before acting.
- Resolve only registered KB roots; never infer one from the working directory.
- Read root-local `AGENTS.md`, `CLAUDE.md`, and `.agents/rules/*.md` guidance.
- Search and lint are read-only. Do not edit, install, or change config in them.
- Respect `agent_edit_mode`: protect `read_only` and preserve `append_only` text.
- Keep uncertainty explicit with `확인 필요`, `미정`, `추정`, or `과거 정보`.
- Treat maintained documents—not `log.jsonl` or git history—as factual evidence.
- Never store or repeat sensitive values merely because they were found.

## Approval Gates

Ask before:

- registering or changing a KB root configuration
- installing or changing Python runtime dependencies
- creating a new KB root or overwriting an existing setup file
- writing security-sensitive values, even when the user supplied them
- editing a protected document or applying lint fixes
- moving, deleting, or broadly restructuring existing KB content

## Bundled Resources

- Common rules: `references/conventions.md`
- First-time recovery: `references/getting-started.md`
- Optional Obsidian routing: `references/obsidian-skills.md`
- Runtime helpers and tests: `scripts/`
- Setup starting points: `templates/`

Use bundled Python helpers with the interpreter and locked requirements defined
by the getting-started guide. Do not install into Homebrew or system Python.
