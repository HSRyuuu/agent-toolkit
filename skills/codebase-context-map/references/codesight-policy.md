# Codesight Policy

Codesight output is useful for token-saving navigation, but it is generated analysis.

## Use

- Run `npx codesight --wiki` when available and the project wants `.codesight/` refreshed.
- Start narrow tasks with `.codesight/wiki/index.md`, then read only the relevant article.
- Use `.codesight/CODESIGHT.md` for broad architecture exploration or onboarding.
- Use `.codesight/graph.md` or a blast-radius query before changing highly imported files.

## Do Not Use

- Do not treat Codesight output as source of truth.
- Do not implement from wiki summaries alone.
- Do not store hand-written project policy inside `.codesight/`; keep human policy in `docs/`, `AGENTS.md`, or `CLAUDE.md`.
- Do not read the full `CODESIGHT.md` every session when one wiki article is enough.

## Staleness Rule

If `.codesight/` is older than relevant source changes, report that it may be stale and verify with actual source files.
