# Obsidian Skills Reference

Use this reference when a Markdown KB is also an Obsidian vault, or when the user asks for Obsidian-specific features such as wikilinks, embeds, callouts, properties, Bases, Canvas, or the Obsidian CLI.

Normal KB work does not require Obsidian skills. `kb-manage`, `kb-write`, `kb-search`, and `kb-lint` must still work as plain Markdown/Git workflows.

## Available Skill Check

Before using Obsidian-specific behavior, check whether the current session has relevant Obsidian skills available.

Relevant skill names may include:

- `obsidian-markdown`
- `obsidian-bases`
- `json-canvas`
- `obsidian-cli`
- `defuddle`

If the needed Obsidian skill is available, use it only for the specific Obsidian feature. Continue to follow the resolved KB root's `AGENTS.md` or `CLAUDE.md`.

## Missing Skill Prompt

If the user asks for Obsidian-specific work and the relevant Obsidian skill is not available, ask before suggesting or installing anything:

```text
현재 세션에 Obsidian용 스킬이 없습니다.

Obsidian Markdown, Bases, Canvas, CLI 작업을 더 정확히 처리할 수 있도록
https://github.com/kepano/obsidian-skills 저장소의 스킬을 추가할까요?
```

Do not add, clone, install, or enable the repository without explicit user approval.

## Suggested Source

Use this repository when the user approves adding Obsidian skills:

- `https://github.com/kepano/obsidian-skills`

The repository provides Agent Skills for Obsidian-compatible agents. Its README lists these skills:

- `obsidian-markdown`: Obsidian Flavored Markdown, wikilinks, embeds, callouts, properties
- `obsidian-bases`: Obsidian Bases files
- `json-canvas`: JSON Canvas files
- `obsidian-cli`: Obsidian vault interaction through the Obsidian CLI
- `defuddle`: clean Markdown extraction from web pages

## Boundaries

- Do not make Obsidian a dependency of the generic KB model.
- Do not bulk-insert wikilinks just because Obsidian skills are available.
- Do not use Bases, Canvas, embeds, callouts, or CLI operations unless the user asks or the local KB guidance clearly expects them.
- Prefer regular Markdown links for external URLs.
- Preserve the KB's source-of-truth document model: maintained Markdown documents remain primary.
