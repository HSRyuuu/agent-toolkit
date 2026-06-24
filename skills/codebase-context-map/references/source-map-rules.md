# Source Map Rules

`SOURCE_MAP.md` is a routing map, not a full inventory.

## Include

- entrypoints: routes, pages, controllers, commands, workers, hooks
- core domain layers: service, repository, entity/model, DTO/schema
- shared UI and API clients
- auth, middleware, config, env, deployment, migrations
- high-impact files imported by many files
- test entrypoints and scenario folders

## Exclude

- generated files, caches, build output, lockfiles
- every component in a large UI tree when a directory row is enough
- implementation details that will drift quickly
- policy, business, or architectural decisions that belong in `PROJECT_OVERVIEW.md`, `DB_SCHEMA.md`, `DEPLOY.md`, `DESIGN.md`, or `ADR.md`

## Maintenance

- Keep paths project-root relative.
- Prefer one table row per meaningful location.
- Keep descriptions to one line.
- Preserve `## Manual Notes` for context the generator cannot infer.
- After moving or deleting source files, re-run validation.
