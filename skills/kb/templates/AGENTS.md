# Knowledge Base Agent Guide

This repository is a Markdown knowledge base. Maintained documents are the source of truth.

This file is the local KB rulebook. Where it conflicts with generic KB skill
conventions, this file wins. Keep intentional differences explicit.

## Read First

- Use `index.md` as the document catalog.
- Use `log.jsonl` as the primary work-history trail for finding files and past work; it works without git. Git history, when this KB is git-backed, is a supplementary reference only.
- Resolve this root only through its registration in `~/.config/kb/kb-config.json`; KB skills must not use an unregistered absolute path.
- If an agent is working from a nested or different directory, it should still resolve this KB root and read this file before changing or answering from the KB.
- Route KB work through the `kb` skill's matching mode:
  - manage for setup, conventions, migration, and root management.
  - write for creating, appending, merging, updating, or reorganizing knowledge.
  - search for read-only search and Q&A.
  - lint for health checks and drift detection.

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
- In git repositories, use the `kb` skill's manage mode and run the bundled edit-mode guard before completing Markdown changes. Use the isolated Python interpreter selected during KB prerequisite setup (default: `~/.venvs/agent-toolkit-kb/bin/python`).
- If the guard reports a protected-file violation, ask whether the change was intentionally made by a human before proceeding.

## Document Structure

- New knowledge documents should use YAML frontmatter unless local rules say otherwise.
- Keep `title`, `summary`, `tags`, `aliases`, `created`, `updated`, and `agent_edit_mode` useful for search and maintenance.
- Keep root agent entrypoints such as this file free of KB document frontmatter.
- Exclude hidden files and directories from KB document discovery, indexing, search, and lint. Read hidden agent guidance separately when instructed.
- Use ordinary Markdown links for external URLs.
- Add internal links only when they are clearly useful.

## File Naming

- Use the most natural language for the document topic.
- For English filenames, use lowercase kebab-case.
- For non-English filenames, use the local repository convention consistently.
- Keep filenames stable once other documents link to them.
