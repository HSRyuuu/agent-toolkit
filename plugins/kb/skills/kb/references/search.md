# Search Mode

Search a registered Markdown KB read-only. Read `conventions.md` first; root
local guidance wins. Maintained documents supply evidence. History, drafts, and
archives help locate evidence but do not establish current behavior.

## Search Until the Question Is Covered

1. Resolve the registered root, then read its local guidance. Run helpers with
   the dedicated interpreter from `getting-started.md`.
2. Extract the question's subjects and identifiers. Search short phrases and
   known alternate names separately; `--query` splits on spaces and requires
   every term. Do not pass a whole Korean sentence as one AND query.
3. Run `kb_meta_search.py <root> --query <terms> --limit 10`. Default scope
   includes `maintained` and legacy `unspecified` knowledge documents.
4. For code/table/column identifiers, always also run the query with `--content`.
   For other questions, read candidates and run `--content` whenever any requested
   fact is still unsupported, even if metadata returned one or more matches.
5. Read the matching section and enough surrounding context to preserve its
   conditions and exceptions. A title, score, or snippet alone is not evidence.
6. If active evidence remains insufficient, repeat with `--scope all --content`.
   Separate draft and historical results in the answer. If only those exist,
   state that current evidence is missing. Do not turn a plan into shipped behavior.
7. Follow a small number of useful related links. Read directory README files
   only for folder intent, and index.md only for a repository-wide overview.

A search is complete when each requested fact has a cited section, a clearly
marked uncertainty, or an explicit information gap. A metadata miss alone does
not establish absence. Before reporting absence, try body search and relevant
alternate names. `updated` is the edit date, not a verification date or an
automatic authority tie-breaker. Compare source, environment, revision/date,
claim scope, and uncertainty in the body. Report unresolved conflicts.

## Helper Contract

The scripts are executable helpers; run them rather than reimplementing them.
Paths below are relative to this skill's directory:

```text
scripts/kb_meta_search.py <root> --query "refund" --content --limit 10
scripts/kb_meta_search.py <root> --query "cache timeout" --scope all --content --json
scripts/kb_meta_search.py <root> --tag kafka --updated-since 2026-06-01
scripts/kb_meta_search.py <root> --query "routing" --include-guidance
scripts/kb_recent_activity.py <root> --since 2026-07-01
```

- `--content` searches metadata, headings, and body with AND semantics across
  them. Metadata matches rank more highly; body hits provide a file line and
  short snippet. Search with another phrase if AND terms are too restrictive.
- `--scope active` is the default; `--scope all` adds draft/historical documents,
  including `_inbox/` and `_archived/`. It does not include private documents.
- `_personal/`, gitignored documents, hidden/dependency trees, and symlinks are
  excluded from shared reads. General lookup also excludes README, index,
  AGENTS, CLAUDE, and Markdown asset notes. `--include-guidance` allows the latter
  group for setup/rules questions, without bypassing private exclusions.
- Rows include `status`, score and matched fields. Content matches also include
  `line` and `snippet`. These are locators; inspect the actual source before citing.
- Exit 0 means the scan completed, including a legitimate no-match result.
  Exit 2 means invalid arguments, unreadable scope, or a partial read/parse failure.
  Partial search still emits usable rows and value-free error paths on stderr;
  disclose the incomplete search and do not claim absence. Exit 3 means the
  frontmatter runtime is missing.
- Recent activity includes all document statuses in the shared scope and uses
  the same partial-read exit behavior. Dates do not establish factual currency.

If the dedicated runtime is unavailable, follow `getting-started.md`. For an
urgent read-only lookup, use `rg` without `--hidden`, `--no-ignore`, or `-L`,
explicitly exclude `_personal/**`, then distinguish draft/archive and guidance
paths before reading. Disclose that structured metadata parsing was unavailable.
Do not install anything merely to answer a read-only query without authorization.

## Answer and History

Give a direct answer, cite source files/sections, and identify relevant gaps or
staleness. Do not expose sensitive values found in snippets or documents.
Git log/blame or legacy log.jsonl can locate the maintained document; cite that
document for facts. Search never edits documents, index, config, or history.
