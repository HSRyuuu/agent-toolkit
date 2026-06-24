---
name: setup-self-improvement-loop
description: Use when a project needs a local agent self-improvement loop, .claude/LESSONS.md, or instructions for recording user feedback and preventing repeated agent mistakes.
---

# Setup Self-Improvement Loop

Install or repair the project-local feedback loop that teaches future agents from user corrections.

## Scope

This skill owns only:

| Asset | Default path | Source |
| --- | --- | --- |
| `LESSONS.md` | `.claude/LESSONS.md` | `templates/project-setup/LESSONS.md` |
| Self-improvement instruction | existing `AGENTS.md` or `CLAUDE.md` | small section or bullet |

Do not install project docs, `SOURCE_MAP.md`, `CODEBASE_CONTEXT.md`, or `.claude/skills/*`. Use `setup-project-docs`, `setup-codebase-context-map`, or `setup-project-level-agent-skill` for those.

## Workflow

1. Resolve the target project root from the user path, `git rev-parse --show-toplevel`, or `pwd`.
2. Check whether `.claude/LESSONS.md` exists.
3. Check existing entrypoint files in this order: `AGENTS.md`, `.claude/CLAUDE.md`, `CLAUDE.md`.
4. Recommend the minimal action:
   - create `.claude/LESSONS.md` when missing
   - add a self-improvement note to the entrypoint when no `LESSONS` or `Self-Improvement` instruction exists
   - do nothing when both are present
5. Before editing, show the exact paths and ask for confirmation.
6. Copy only from `templates/project-setup/LESSONS.md`. Do not invent a replacement template.
7. If the destination exists, ask whether to keep it, back it up and replace it, or skip it. Never overwrite silently.
8. After installation, report what changed and what was left untouched.

## Entry Point Text

When the user approves adding an instruction, use a short section like this:

```markdown
## Self-Improvement Loop

- Read `.claude/LESSONS.md` at the start of each session when it exists.
- When the user corrects agent behavior, record the lesson immediately using the file's format.
- If the same mistake repeats, strengthen the existing lesson instead of adding a duplicate.
```

If the entrypoint already has a similar section, preserve the user's wording and add only the missing rule.

## Safety Rules

- Default to read-only recommendation unless the user explicitly asks to apply the setup.
- Create only parent directories required by approved paths.
- Keep `LESSONS.md` out of `docs/`; it is agent operation memory, not project documentation.
- Do not modify `.gitignore`, plugin manifests, or unrelated docs.

## Verification

Run these checks after changes:

```bash
test -f "$TARGET/.claude/LESSONS.md"
rg -n "LESSONS|Self-Improvement|self-improvement" "$TARGET/AGENTS.md" "$TARGET/.claude/CLAUDE.md" "$TARGET/CLAUDE.md" 2>/dev/null
```
