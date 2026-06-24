# Output Structure

The skill creates or updates a small agent-facing documentation set.

```text
docs/
  SOURCE_MAP.md        # selective routing map for important source locations
  CODEBASE_CONTEXT.md  # reading policy, generated inventory, optional Codesight pointers
.codesight/            # optional generated analysis, refreshed only with --run-codesight
```

## Ownership

| File | Owner | Update mode |
| --- | --- | --- |
| `docs/SOURCE_MAP.md` | mixed generated + human notes | generator refreshes detected sections and preserves `## Manual Notes` |
| `docs/CODEBASE_CONTEXT.md` | generated | generator overwrites |
| `.codesight/*` | Codesight | `npx codesight --wiki` or project-specific Codesight command |

## Agent Read Order

For narrow implementation work:

1. `AGENTS.md` or `CLAUDE.md`
2. `docs/SOURCE_MAP.md`
3. `.codesight/wiki/index.md` if present
4. one relevant `.codesight/wiki/*.md` article if useful
5. actual source files

For broad architecture discovery:

1. `docs/CODEBASE_CONTEXT.md`
2. `.codesight/CODESIGHT.md` if present
3. `docs/SOURCE_MAP.md`
4. source files for any claim that affects implementation
