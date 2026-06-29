# KB LLM Wiki Schema

This reference defines the shared operating model for the `kb-*` skills.

## Core Model

The KB follows a `sources -> wiki -> schema` model.

- `sources`: original inputs such as URL captures, copied files, inbox notes, and dated daily logs.
- `wiki`: canonical wiki documents that an LLM and a human can reread as current synthesized knowledge.
- `schema`: these operating rules, document kinds, templates, naming rules, and validation checks.

Obsidian compatibility is useful, but folder shape must not outrank canonical documents,
source links, and wiki links.

## Document Kinds

| Kind | Purpose | Typical Location | Notes |
| --- | --- | --- | --- |
| `source` | Preserve original input or extracted source text. | `_raw/` | Do not use as the primary answer surface when a canonical wiki exists. |
| `inbox` | Hold unprocessed input. | `_inbox/` | Process later through `kb-add` inbox mode. |
| `archive` | Keep old material intentionally out of active flow. | `_archive/` | Do not auto-move or delete. |
| `daily-log` | Preserve date-bound context such as onboarding notes or meeting notes. | shallow topic folder | Link to the relevant canonical wiki when possible. |
| `canonical` | Maintain the current synthesized knowledge for a topic. | shallow topic folder | Prefer this for search answers and future updates. |

## Frontmatter

Recommended frontmatter:

```yaml
---
kind: canonical | daily-log | source
tags: [topic, project]
created: YYYY-MM-DD
updated: YYYY-MM-DD
source:
  - "[[_raw/example]]"
canonical: "[[topic-guide]]"     # daily-log only
related:
  - "[[other-note]]"
---
```

Required by kind:

- `canonical`: `kind`, `tags`, `created`
- `daily-log`: `kind`, `tags`, `created`, `canonical`
- `source`: `kind`, `created`

The helper script may report `missing-required-frontmatter` when these are absent.

## Naming

- Canonical wiki: stable topic name without a date, such as `tripbtoz-onboarding.md`.
- Daily log: stable topic name plus ISO date suffix, such as `tripbtoz-onboarding-2026-06-29.md`.
- Raw source: slugified original title or filename under `_raw/`.
- Special folders use `_` prefix. Topic folders do not.

## Link Rules

- A daily log should link to its canonical wiki with frontmatter `canonical` or a body wiki link.
- A canonical wiki should link back to relevant daily logs in a `## Related Logs` or `## 관련 로그` section.
- Raw source files should be referenced by at least one canonical or daily-log document.
- Search should prefer canonical wiki documents and use sources/logs as supporting evidence.

## Facts-Preserving Updates

`facts-preserving` means an update may reorganize, deduplicate, clarify, or merge text
without removing true facts, weakening source traceability, or changing meaning.

Allowed with preview and user approval:

- merge duplicate bullets that state the same fact,
- move a dated observation into a stable canonical section,
- rewrite wording for clarity while keeping the same fact and source link,
- add a missing canonical/log reciprocal link.

Not allowed without explicit remove/delete flow:

- delete a factual claim,
- overwrite a value with a conflicting value,
- remove source links,
- silently discard dated context,
- convert uncertainty into certainty.

## `kb-add` Mode Contract

First matching row wins.

| Priority | Condition | Mode |
| --- | --- | --- |
| 1 | User explicitly asks remove/delete | `remove` |
| 2 | User explicitly asks modify/change/merge | `modify-preview` |
| 3 | New input is cumulative guide content and canonical exists | `merge-preview` |
| 4 | New input is date-bound log content | `daily-log + canonical-link` |
| 5 | New topic with no canonical candidate | `new-canonical` |

`modify-preview` and `merge-preview` must show the target area, before/after content,
facts-preserving rationale, and approval prompt before writing.

## Helper Issue Codes

- `missing-required-frontmatter`
- `raw-source-unlinked`
- `daily-log-without-canonical-link`
- `canonical-missing-related-section`
- `unknown-kind`

