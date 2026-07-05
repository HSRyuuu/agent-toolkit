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

Run the agent-toolkit project release loop in one order: commit, push `main`, then reload local Codex and Claude Code plugin state.

This skill is intentionally explicit-only. Do not infer it from a normal request such as "commit", "push", or "reload".

## Required Sub-skills

Before acting, read and follow:

- `git-actions` for commit and push rules, including `references/commit.md`
- `manage-local-plugins` for local plugin reload rules

## Preconditions

- The target repository must be `agent-toolkit`.
- The active branch must be `main`.
- Push only to `origin main`.
- Never force push.
- Do not reload if commit or push fails.
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

### 1. Commit

Use `git-actions` commit rules.

- Inspect `git status --short`, `git diff --stat`, and relevant diffs.
- Stage only files related to the current task.
- If there are no working tree changes, do not create an empty commit. Continue to push only if `main` has commits to publish or the user explicitly wants a reload of current `main`.
- Use the repository's existing commit message style.

### 2. Push Main

Push the current `main` branch directly:

```bash
git push origin main
```

If the push fails, stop. Do not force push and do not reload.

### 3. Reload Plugins

After a successful push, reload both Codex and Claude Code using `manage-local-plugins`.

Run status checks first. If one host CLI is unavailable, report that host as skipped and continue with the available host.

#### Codex

Resolve the installed plugin id from current Codex state when possible. Prefer the installed `agent-toolkit@...` entry shown by `codex plugin list`; fall back to the marketplace metadata only when the plugin is not currently installed.

Follow the Codex reload sequence from `manage-local-plugins`:

```bash
codex plugin marketplace add "$PLUGIN_ROOT" --json
codex plugin remove "$PLUGIN_ID" --json || true
rm -rf "$HOME/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME"
codex plugin add "$PLUGIN_ID" --json
codex plugin list
```

Remove only the resolved cache path for `agent-toolkit`. Never remove the whole Codex plugin cache.

#### Claude Code

Claude Code local plugin edits usually require a fresh Claude Code session to take effect. A separate cache prune is usually not needed.

Follow the Claude Code reload sequence from `manage-local-plugins`:

```bash
claude plugin validate "$PLUGIN_ROOT"
claude plugin marketplace update "$MARKETPLACE_NAME" || true
claude plugin update "$PLUGIN_ID" || true
claude plugin details "$PLUGIN_ID"
```

If Claude Code reports the plugin details successfully, tell the user to start a new Claude Code session before expecting changed skills, hooks, or manifests to be loaded.

## Report

Report:

- commit hash and message, or that no commit was needed
- push target and result
- resolved Codex plugin id and reload result
- resolved Claude Code plugin id and reload result, or why Claude Code was skipped
- reminder that new Codex and Claude Code sessions are required for newly loaded skills/hooks
