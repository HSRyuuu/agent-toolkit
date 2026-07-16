---
name: kb
description: >
  Use when working with a personal Markdown Knowledge Base (KB): saving or
  organizing knowledge ("kb에 저장해줘", "이거 기록해둬"), finding what is
  recorded ("kb에서 찾아줘"), health-checking the KB ("kb 점검해줘"), or
  setting up and managing a KB root ("kb 셋업"). Do not use for ordinary
  project documentation that is not a registered personal KB.
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

Read [`references/conventions.md`](references/conventions.md) before acting in
any mode. It is the single source of truth for root resolution, local root
guidance, frontmatter, `agent_edit_mode`, uncertainty markers, `index.md` /
`log.jsonl`, and security. Search and lint are read-only.

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
by the getting-started guide.
