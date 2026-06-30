# Knowledge Base Agent Guide

This repository is a Markdown knowledge base. Maintained documents are the source of truth.

## Read First

- Use `index.md` as the document catalog.
- Use `log.jsonl` as a small work-history pointer for finding files and git history.
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

## Document Structure

- New knowledge documents should use YAML frontmatter unless local rules say otherwise.
- Keep `title`, `summary`, `tags`, `aliases`, `created`, and `updated` useful for search.
- Keep root agent entrypoints such as this file free of KB document frontmatter.
- Use ordinary Markdown links for external URLs.
- Add internal links only when they are clearly useful.

## File Naming

- Use the most natural language for the document topic.
- For English filenames, use lowercase kebab-case.
- For non-English filenames, use the local repository convention consistently.
- Keep filenames stable once other documents link to them.
