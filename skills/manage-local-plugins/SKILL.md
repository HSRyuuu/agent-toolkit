---
name: manage-local-plugins
description: >
  Use when enabling, disabling, installing, removing, reloading, refreshing
  snapshots, checking status, or troubleshooting local Claude Code/Codex plugins
  and marketplaces. Triggers: "플러그인 켜/꺼줘", "plugin reload",
  "marketplace refresh", "새 세션에 스킬이 안 보여", "Unknown command",
  "local plugin cache". Do NOT use for writing plugin skills or manifests.
---

# Manage Local Plugins

## Overview

Manage local Claude Code and Codex plugins with explicit commands. Prefer a transparent command sequence over writing a new toggle script; create a script only when the user asks for repeatable automation or the same lifecycle sequence has become project policy.

## Inputs To Resolve

Before changing plugin state, identify:

- `PLUGIN_NAME`: from `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json`.
- `MARKETPLACE_NAME`: from `.claude-plugin/marketplace.json` or `.agents/plugins/marketplace.json`.
- `PLUGIN_ID`: `<PLUGIN_NAME>@<MARKETPLACE_NAME>`.
- `PLUGIN_ROOT`: absolute path to the plugin repository or marketplace root.
- Host scope: `claude`, `codex`, or both.

Use `jq` when available; otherwise use `python3 -m json.tool` for validation.

## Status First

Run status checks before mutating anything.

```bash
claude plugin marketplace list
claude plugin list
claude plugin details "$PLUGIN_ID"

codex plugin marketplace list
codex plugin list
grep -E "$PLUGIN_NAME|$MARKETPLACE_NAME" "$HOME/.codex/config.toml" || true
find "$HOME/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME" -maxdepth 2 -type f -name plugin.json 2>/dev/null
```

If a CLI is unavailable, report that host as skipped instead of fabricating state.

## Diagnostic Pattern: Source Has Skill, Session Does Not

When a command or skill exists in the plugin repository but the current session reports `Unknown command` or the skill is missing from the loaded skill list, treat it as a snapshot/session problem before editing source code.

Check these three surfaces separately:

- Source repository: confirm `skills/<skill-name>/SKILL.md` exists in `PLUGIN_ROOT`, and inspect recent commits only as evidence that source contains the skill.
- Installed plugin snapshot: inspect the host-specific cache, such as `~/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/skills/` or `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/`.
- Current session: remember that already-running Claude Code or Codex sessions do not reload newly installed skills, hooks, or manifests. A new session is required after refreshing a local plugin.

If the source has the skill but the cache snapshot does not, refresh the installed snapshot for that host. If the cache snapshot has the skill but the current session still does not, start a new session and verify there.

For cross-host plugins, refresh Claude Code and Codex independently. They use separate installation/cache paths, so a successful Claude refresh does not prove the Codex snapshot is current, and vice versa.

## Claude Code

Claude Code has first-class enable and disable commands. Local directory plugin edits usually require a fresh Claude Code session; a separate cache prune is usually not needed.

Register or refresh marketplace:

```bash
claude plugin marketplace add "$PLUGIN_ROOT"
claude plugin marketplace update "$MARKETPLACE_NAME"
```

Turn on:

```bash
claude plugin install "$PLUGIN_ID" || true
claude plugin enable "$PLUGIN_ID"
claude plugin details "$PLUGIN_ID"
```

Turn off:

```bash
claude plugin disable "$PLUGIN_ID"
claude plugin list
```

Reload after source changes:

```bash
claude plugin validate "$PLUGIN_ROOT"
claude plugin marketplace update "$MARKETPLACE_NAME" || true
claude plugin update "$PLUGIN_ID" || true
claude plugin details "$PLUGIN_ID"
```

**Known gotcha — stale skill-invocation cache:** `claude plugin details` reads the source directory live and will show renamed/added/removed skills immediately, which makes it *look* like the reload worked. But the content actually loaded when a skill is invoked comes from a separate versioned snapshot at `~/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`. If `plugin.json`'s `version` field doesn't change, both `claude plugin marketplace update` and `claude plugin update` report "already at the latest version" and do **not** refresh that snapshot — edited/renamed/deleted skill files silently keep serving old content from cache.

If `claude plugin details` shows different skills than what actually fires, force a resync:

```bash
VERSION=$(jq -r '.version' "$PLUGIN_ROOT/.claude-plugin/plugin.json")
rm -rf "$HOME/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION"
claude plugin marketplace update "$MARKETPLACE_NAME"
claude plugin update "$PLUGIN_ID" || true
```

Only remove the resolved `$PLUGIN_NAME/$VERSION` subpath, never the whole `~/.claude/plugins/cache` tree. The safest long-term fix is to bump `version` in `plugin.json` on every source change to a local plugin — that makes the cache key change and forces a real resync instead of relying on manual cache deletion.

Tell the user to start a new Claude Code session after changing plugin state, hooks, skills, or manifests.

## Codex

Codex installs a versioned marketplace snapshot. There is no separate enable/disable toggle equivalent; "off" is uninstall/remove, and "reload" means refreshing the installed snapshot.

Register marketplace:

```bash
codex plugin marketplace add "$PLUGIN_ROOT" --json
codex plugin marketplace list
```

Turn on:

```bash
codex plugin add "$PLUGIN_ID" --json
codex plugin list
```

Turn off:

```bash
codex plugin remove "$PLUGIN_ID" --json
codex plugin list
```

Reload after source changes:

```bash
codex plugin marketplace add "$PLUGIN_ROOT" --json
codex plugin remove "$PLUGIN_ID" --json || true
rm -rf "$HOME/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME"
codex plugin add "$PLUGIN_ID" --json
codex plugin list
```

Use the manual cache removal only for local development refreshes, and only for the resolved plugin cache path. Never remove the whole Codex plugin cache unless the user explicitly asks.

Tell the user to start a new Codex session after any Codex plugin add/remove/reload. Existing sessions keep already-loaded skills and hooks.

## Local Marketplace Shape

For Codex local marketplaces, inspect `.agents/plugins/marketplace.json`. If the plugin source path is a subpath such as `./plugins/<name>`, ensure that path exists from `PLUGIN_ROOT` before running `codex plugin add`.

```bash
jq empty .agents/plugins/marketplace.json .codex-plugin/plugin.json
jq -r '.name, .plugins[].name, .plugins[].source.path // .plugins[].source' .agents/plugins/marketplace.json
```

For Claude Code, validate:

```bash
jq empty .claude-plugin/marketplace.json .claude-plugin/plugin.json
claude plugin validate "$PLUGIN_ROOT"
```

## Reporting

Report:

- Which host changed.
- Whether the action was enable/disable, install/remove, or snapshot refresh.
- The resolved `PLUGIN_ID`.
- Whether a new session is required.
- Any skipped host and why.
