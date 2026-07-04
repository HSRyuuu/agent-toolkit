# Knowledge Base Agent Guide

This repository is a Markdown knowledge base. Maintained documents are the source of truth.

This file is the local KB rulebook. Where it conflicts with the AgentToolkit KB
skills' generic conventions, this file wins. Keep it aligned with the skills'
`conventions.md` unless this KB intentionally diverges.

## Read First

- Use `index.md` as the document catalog.
- If `log.jsonl` exists, use it as a small work-history pointer for finding files and git history; a git-backed KB may rely on commit messages instead.
- If an agent is working from a nested or different directory, it should still resolve this KB root and read this file before changing or answering from the KB.
- Use the AgentToolkit KB skills when available:
  - `kb-manage` for setup, conventions, migration, and root management.
  - `kb-write` for creating, appending, merging, updating, or reorganizing knowledge.
  - `kb-search` for read-only search and Q&A.
  - `kb-lint` for health checks and drift detection.

## Core Rules

- Do not mix confirmed facts with guesses. Mark uncertainty explicitly.
- Do not record secrets, credentials, tokens, passwords, private keys, personal data, or sensitive operational details.
- Read existing context before changing a document.
- Preserve meaning while improving structure and readability.
- Avoid duplicate ownership. Choose one source-of-truth document and link or reference it from related documents.
- Prefer exact dates over relative dates when timing matters.
- Respect `agent_edit_mode` in Markdown frontmatter:
  - `read_only`: agents must not edit the file.
  - `append_only`: agents may add new content anywhere, including `>` blockquotes or notes, but must preserve existing text exactly.
  - `editable`: agents may edit text, structure, frontmatter, and remove content when appropriate.
- In git repositories, run the edit-mode guard before completing Markdown changes: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/check_agent_edit_mode.py"` (if `${CLAUDE_PLUGIN_ROOT}` is unset, use the agent-toolkit plugin's `skills/kb-manage/scripts/` path).
- If the guard reports a protected-file violation, ask whether the change was intentionally made by a human before proceeding.

## Document Structure

- New knowledge documents should use YAML frontmatter unless local rules say otherwise.
- Keep `title`, `summary`, `tags`, `aliases`, `created`, `updated`, and `agent_edit_mode` useful for search and maintenance.
- Keep root agent entrypoints such as this file free of KB document frontmatter.
- Use ordinary Markdown links for external URLs.
- Add internal links only when they are clearly useful.

## File Naming

- Use the most natural language for the document topic.
- For English filenames, use lowercase kebab-case.
- For non-English filenames, use the local repository convention consistently.
- Keep filenames stable once other documents link to them.
