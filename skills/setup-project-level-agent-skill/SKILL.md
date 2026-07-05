---
name: setup-project-level-agent-skill
description: >
  Use when a target project needs project-local .claude/skills installed from
  agent-toolkit templates. Triggers: "install local agent skills",
  "add manage-skills", "add verify-implementation", "add update-project-docs",
  "project-level Claude skills". Do NOT use for global/plugin skills, docs,
  source maps, LESSONS.md, AGENTS.md, or CLAUDE.md.
---

# Setup Project-Level Agent Skill

Install selected helper skills into a target project's `.claude/skills/` directory.

## Scope

This skill owns only project-local skill installation:

| Skill | Default path | Template source |
| --- | --- | --- |
| `manage-skills` | `.claude/skills/manage-skills/` | `templates/project-setup/manage-skills/` |
| `verify-implementation` | `.claude/skills/verify-implementation/` | `templates/project-setup/verify-implementation/` |
| `update-project-docs` | `.claude/skills/update-project-docs/` | `templates/project-setup/update-project-docs/` |

Do not create project docs, `SOURCE_MAP.md`, `CODEBASE_CONTEXT.md`, `LESSONS.md`, `AGENTS.md`, or `CLAUDE.md`.

## Recommendation Guide

| Situation | Recommendation |
| --- | --- |
| User wants project-specific verification skills generated over time | install `manage-skills` and `verify-implementation` together |
| User already has docs that need drift checks | install `update-project-docs` |
| Project has no local `.claude/skills/` yet | explain that these are project-local overrides before installing |
| Same skill exists globally or in another plugin | warn that local `.claude/skills/` may take precedence |

## Workflow

1. Resolve the target project root.
2. Confirm the user wants project-local skill installation, not just a recommendation.
3. Verify `templates/project-setup/` exists and include only templates that exist on disk.
4. Show available skills and ask which to install.
5. For each selected skill, show source and destination.
6. Check for destination conflicts:
   - keep existing and skip
   - back up existing directory to `.bak.<timestamp>` and replace
   - install under a different name
   - cancel
7. Check for same-name global/plugin skills when practical and warn before local override.
8. Copy approved template directories only.
9. Report installed, skipped, renamed, and backed-up items.

## Safety Rules

- Never overwrite a directory without explicit approval.
- Do not merge skill directories; skill installation is copy, skip, rename, or backup-and-replace.
- Do not edit the copied `SKILL.md` unless the user explicitly asks for project customization.
- Do not register these skills in plugin manifests; target-project `.claude/skills/` loading is local to that project.

## Verification

Run the checks that match the selected skills:

```bash
test -f "$TARGET/.claude/skills/manage-skills/SKILL.md"
test -f "$TARGET/.claude/skills/verify-implementation/SKILL.md"
test -f "$TARGET/.claude/skills/update-project-docs/SKILL.md"
find "$TARGET/.claude/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort
```
