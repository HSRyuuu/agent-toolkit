---
name: publish-agent-toolkit
description: >
  Use only when the user explicitly invokes "$agent-toolkit:publish-agent-toolkit",
  "$publish-agent-toolkit", says "agent-toolkit publish", or asks for the
  agent-toolkit publish/release loop. Do NOT use for ordinary commit, push, PR,
  or plugin reload requests.
---

# Publish Agent Toolkit

## Overview

Run the agent-toolkit release loop in one order: verify, commit, bump the plugin version, push `main`, then update the GitHub-installed plugin on this machine.

Distribution model (README "방식 1 — GitHub에서 설치"): machines install via `/plugin marketplace add HSRyuuu/agent-toolkit`, and both hosts cache the repo keyed by **plugin version** (`~/.claude/plugins/cache/hsryuuu/agent-toolkit/<version>/`, `~/.codex/plugins/cache/hsryuuu/agent-toolkit/<version>/`). Pushing new commits alone changes nothing for installed machines — the version bump is the release.

This skill is intentionally explicit-only. Do not infer it from a normal request such as "commit", "push", or "reload".

## Required Sub-skills

Before acting, read and follow:

- `git-actions` for commit and push rules, including `references/commit.md`
- `local-plugin-manager` only for troubleshooting when the update commands fail or a new session still cannot see the published version

## Preconditions

- The target repository must be `agent-toolkit`.
- The active branch must be `main`.
- Push only to `origin main`.
- Never force push.
- Do not update plugins if commit, version bump, or push fails.
- Do not switch branches, stash, rebase, pull, or resolve conflicts unless the user explicitly asks.

Confirm the repository before mutating state:

```bash
jq -r '.name' .codex-plugin/plugin.json
test -d skills
git branch --show-current
git status --short
```

If the plugin name is not `agent-toolkit` or the branch is not `main`, stop and report the reason.

## Workflow

### 1. Verify Secrets

Run the project-local `verify-secrets` skill (Claude Code: `.claude/skills/verify-secrets/`) before committing, as required by `.claude/CLAUDE.md`. Stop on any finding that is not an approved exception.

### 2. Commit

Use `git-actions` commit rules.

- Inspect `git status --short`, `git diff --stat`, and relevant diffs.
- Stage only files related to the current task.
- If there are no working tree changes, do not create an empty commit. Continue only if `main` has unpushed commits to publish.
- Use the repository's existing commit message style.

### 3. Bump Plugin Version

The plugin version is the cache key on both hosts, so a release without a bump is invisible to installed machines.

If any commit being published changes plugin-visible content (`skills/`, `templates/`, hooks, or either plugin manifest) and the version was not already bumped in those commits:

- Bump `version` in **both** `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` to the **same value**. Patch bump by default; minor when the user says the release is feature-level.
- Never add a `version` to `marketplace.json` `plugins[]` — the `plugin.json` value silently wins and the mismatch confuses cache debugging.
- Commit the bump in the existing style: `chore: bump plugin version to X.Y.Z`.

If nothing plugin-visible changed (repo docs only, local-only files), skip the bump and say so in the report.

### 4. Push Main

Push the current `main` branch directly:

```bash
git push origin main
```

If the push fails, stop. Do not force push and do not update plugins.

### 5. Update Installed Plugins

Third-party marketplaces do not auto-update, so run the update explicitly after a successful push. If one host CLI is unavailable, report that host as skipped and continue with the other.

```bash
# Claude Code — refresh catalog, then update the plugin
claude plugin marketplace update hsryuuu
claude plugin update agent-toolkit@hsryuuu
claude plugin details agent-toolkit@hsryuuu

# Codex — refresh the marketplace snapshot
codex plugin marketplace upgrade hsryuuu
codex plugin list
```

- Confirm the reported version equals the version just pushed. "Already at the latest version" **with the old version number** means the bump commit did not reach `origin main` — fix the push, do not prune caches.
- Do not remove cache directories in this flow; the version bump makes both hosts fetch a fresh snapshot on update.
- Other machines are updated by running these same commands there; they are not reachable from this loop.

### 6. New Session

Both hosts load the new snapshot only in a fresh session. Tell the user to restart Claude Code and Codex sessions before expecting changed skills, hooks, or manifests.

## Report

Report:

- verify-secrets result
- commit hash(es) and message(s), or that no commit was needed
- version bump `old → new`, or why the bump was skipped
- push target and result
- per-host update result with the version each host reports, or why a host was skipped
- reminder that new sessions are required on every machine, and that other machines must run the update commands themselves
