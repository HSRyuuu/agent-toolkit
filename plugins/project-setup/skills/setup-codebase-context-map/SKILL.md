---
name: setup-codebase-context-map
description: >
  Use when a project needs source navigation/context map files such as
  SOURCE_MAP.md, CODEBASE_CONTEXT.md, route maps, schema maps, component maps,
  Codesight outputs, or agent source-reading guides. Triggers:
  "create SOURCE_MAP.md", "CODEBASE_CONTEXT.md", "codebase context map",
  "Codesight", "route map", "schema map", "component map". Do NOT use for human
  project docs or AGENTS.md/CLAUDE.md.
---

# Setup Codebase Context Map

Create compact, source-grounded navigation files that help coding agents find the right files before spending tokens on broad repository exploration.

## Core Rule

Keep three layers separate:

| Layer | Purpose | Trust level |
| --- | --- | --- |
| `docs/SOURCE_MAP.md` | Curated routing map for where important code lives | High, but must be kept current |
| `docs/CODEBASE_CONTEXT.md` | Agent reading policy and generated context inventory | Medium |
| `.codesight/` | Optional generated structural hints from Codesight | Navigation aid only |

Generated maps tell agents where to look. They do not replace reading source files before implementation.

## Workflow

1. Inspect the repository root and current docs.
2. Run the generator:

```bash
python3 <skill>/scripts/build_context_map.py <project-root>
```

Use `--run-codesight` only when Node/npx is available and the project owner wants `.codesight/` output refreshed:

```bash
python3 <skill>/scripts/build_context_map.py <project-root> --run-codesight
```

If the project owner wants Codesight installed or wired into MCP/watch/hook workflows, read `references/codesight-install.md` first.

3. Review the generated `docs/SOURCE_MAP.md` and `docs/CODEBASE_CONTEXT.md`.
4. Add missing human-only context by editing the `## Manual Notes` section, not generated sections.
5. Validate path references:

```bash
python3 <skill>/scripts/validate_context_map.py <project-root>
```

6. If this is part of project setup, point the local `AGENTS.md` or `CLAUDE.md` at the generated files and instruct agents to read `SOURCE_MAP.md` first.

## What To Include

`SOURCE_MAP.md` should stay selective. Include files agents would otherwise waste time rediscovering:

- frontend routes, layouts, shared components, API clients, route constants
- backend controllers, services, repositories, entities/models, DTOs
- schema and migration files
- auth, middleware, exception, config, environment, and deployment entrypoints
- tests and high-impact shared files

Do not list every file. If a directory name already explains itself, prefer one directory row over many file rows.

## Codesight Policy

Read `references/codesight-policy.md` before wiring Codesight into a project convention. In short:

- read `.codesight/wiki/index.md` before `.codesight/CODESIGHT.md`
- read one relevant wiki article for narrow tasks
- use `.codesight/CODESIGHT.md` only for broad architecture exploration
- treat Codesight output as stale until source files confirm it

## References

- `references/output-structure.md` - target file layout and ownership boundaries
- `references/source-map-rules.md` - curation and update rules for `SOURCE_MAP.md`
- `references/codesight-policy.md` - safe use of generated Codesight output
- `references/codesight-install.md` - optional Codesight install, refresh, MCP, and CI setup
