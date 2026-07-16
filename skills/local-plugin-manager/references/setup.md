# Setup — Scaffold and Register a Local Plugin

Creates a new local plugin (or registers an existing repo as one) for Claude Code, Codex, or both. Modeled on the two working local installs: `agent-toolkit` and `as-usual`.

## Target layout

A dual-host plugin repo looks like this (as-usual and agent-toolkit both follow it):

```
<PLUGIN_ROOT>/
├── .claude-plugin/
│   ├── plugin.json         # Claude Code plugin metadata
│   └── marketplace.json    # Claude Code single-plugin marketplace, source "./"
├── .codex-plugin/
│   └── plugin.json         # Codex plugin metadata (skills/hooks paths + interface block)
├── .agents/plugins/
│   └── marketplace.json    # Codex local marketplace metadata (per-repo pattern)
├── plugins/
│   └── <PLUGIN_NAME> -> .. # self-symlink so Codex's "./plugins/<name>" source path resolves to the repo root
├── skills/                 # shared skill root — both hosts read this one directory
│   └── <skill-name>/SKILL.md
├── hooks/                  # optional (as-usual: hooks-codex.json referenced from .codex-plugin/plugin.json)
├── agents/                 # optional
└── commands/               # optional
```

Claude-only? Skip `.codex-plugin/`, `.agents/`, `plugins/`. Codex-only? Skip `.claude-plugin/`.

## Part A — Claude Code

### A1. Metadata files

```bash
mkdir -p "$PLUGIN_ROOT/.claude-plugin" "$PLUGIN_ROOT/skills"
```

`.claude-plugin/plugin.json`:

```json
{
  "name": "<PLUGIN_NAME>",
  "version": "0.1.0",
  "description": "<one-line description>"
}
```

`.claude-plugin/marketplace.json` (single-plugin marketplace pointing at the repo itself):

```json
{
  "name": "<MARKETPLACE_NAME>",
  "owner": { "name": "<your-name-or-handle>" },
  "plugins": [
    {
      "name": "<PLUGIN_NAME>",
      "source": "./",
      "description": "<one-line description>",
      "version": "0.1.0"
    }
  ]
}
```

`"source": "./"` means the plugin *is* this directory. For a multi-plugin marketplace, point `source` at a subdirectory instead.

### A2. Register in `~/.claude/settings.json`

Both keys are top-level objects; create them if missing. Real working example (both local plugins registered):

```json
"extraKnownMarketplaces": {
  "hsryuuu": {
    "source": { "source": "directory", "path": "/Users/<user>/dev/personal/agent-toolkit" }
  },
  "as-usual-local": {
    "source": { "source": "directory", "path": "/Users/<user>/dev/personal/harness-as-usual" }
  }
},
"enabledPlugins": {
  "agent-toolkit@hsryuuu": true,
  "as-usual@as-usual-local": true
}
```

The `path` must be **absolute** — Claude Code does not reliably expand `~` here.

Alternatively, register via CLI instead of editing settings directly:

```bash
claude plugin marketplace add "$PLUGIN_ROOT"
claude plugin install "$PLUGIN_ID"
claude plugin enable "$PLUGIN_ID"
```

## Part B — Codex

Codex reads `.codex-plugin/plugin.json` for the plugin and a `marketplace.json` under `.agents/plugins/` for the marketplace. Two registration patterns are in real use — pick one:

### Pattern 1 — per-repo marketplace (agent-toolkit)

The repo is its own marketplace. Codex marketplace `source.path` must be a subpath, so the repo uses a self-symlink:

```bash
mkdir -p "$PLUGIN_ROOT/.codex-plugin" "$PLUGIN_ROOT/.agents/plugins" "$PLUGIN_ROOT/plugins"
ln -s .. "$PLUGIN_ROOT/plugins/<PLUGIN_NAME>"   # plugins/<name> -> repo root
```

`.agents/plugins/marketplace.json`:

```json
{
  "name": "<MARKETPLACE_NAME>",
  "interface": { "displayName": "<Display Name>" },
  "plugins": [
    {
      "name": "<PLUGIN_NAME>",
      "source": { "source": "local", "path": "./plugins/<PLUGIN_NAME>" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Productivity"
    }
  ]
}
```

Register and install:

```bash
codex plugin marketplace add "$PLUGIN_ROOT" --json
codex plugin add "<PLUGIN_NAME>@<MARKETPLACE_NAME>" --json
```

### Pattern 2 — shared home marketplace (as-usual)

One `personal` marketplace at `$HOME` serves multiple plugins; each plugin is a symlink under `~/plugins/`. Good when you don't want a marketplace file per repo.

```bash
mkdir -p ~/.agents/plugins ~/plugins
ln -s "$PLUGIN_ROOT" ~/plugins/<PLUGIN_NAME>
```

`~/.agents/plugins/marketplace.json` — add an entry to the `plugins` array:

```json
{
  "name": "personal",
  "interface": { "displayName": "Personal" },
  "plugins": [
    {
      "name": "<PLUGIN_NAME>",
      "source": { "source": "local", "path": "./plugins/<PLUGIN_NAME>" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Developer Tools"
    }
  ]
}
```

```bash
codex plugin marketplace add "$HOME" --json
codex plugin add "<PLUGIN_NAME>@personal" --json
```

The resulting Codex `PLUGIN_ID` is `<PLUGIN_NAME>@personal` — different from the Claude side. Record both.

### B1. `.codex-plugin/plugin.json`

Unlike the Claude manifest, Codex wants explicit asset paths and an `interface` block. Working shape (from as-usual, which also ships hooks):

```json
{
  "name": "<PLUGIN_NAME>",
  "version": "0.1.0",
  "description": "<one-line description>",
  "author": { "name": "<your-name>" },
  "skills": "./skills/",
  "hooks": "./hooks/hooks-codex.json",
  "interface": {
    "displayName": "<Display Name>",
    "shortDescription": "<one line>",
    "developerName": "<your-name>",
    "category": "Productivity",
    "capabilities": ["Read", "Write"],
    "defaultPrompt": ["<a sensible starter prompt>"]
  }
}
```

Omit `"hooks"` if there are none. `"skills": "./skills/"` must point at the same skill root Claude uses — one `skills/` directory, two manifests.

Registration lands in `~/.codex/config.toml` (Codex writes this — don't hand-edit unless fixing corruption):

```toml
[marketplaces.hsryuuu]
source_type = "local"
source = "/Users/<user>/dev/personal/agent-toolkit"

[plugins."agent-toolkit@hsryuuu"]
enabled = true
```

## Part C — Sanity-check skill

Plugin loading is silent — no error if registration fails. Drop in a tiny disposable skill and confirm it appears next session. `skills/test-skill/SKILL.md`:

```markdown
---
name: test-skill
description: Sanity-check skill confirming the <PLUGIN_NAME> plugin loaded. Use when the user says "test <PLUGIN_NAME>" or asks whether the plugin is working.
---

# Test Skill

When invoked, respond with exactly:

> <PLUGIN_NAME> plugin loaded successfully.

Nothing else.
```

## Part D — Validate and verify

A missing comma in `settings.json` is the single most common reason a fresh plugin does not load, and neither host will warn you:

```bash
jq empty ~/.claude/settings.json
jq empty "$PLUGIN_ROOT"/.claude-plugin/plugin.json "$PLUGIN_ROOT"/.claude-plugin/marketplace.json
jq empty "$PLUGIN_ROOT"/.codex-plugin/plugin.json "$PLUGIN_ROOT"/.agents/plugins/marketplace.json 2>/dev/null
claude plugin validate "$PLUGIN_ROOT"
```

Then open a **new** session per host (plugins are scanned at session start only) and check:

1. The available-skills list shows `test-skill` (often namespaced `<PLUGIN_NAME>:test-skill`).
2. Saying "test `<PLUGIN_NAME>`" returns the canned response.
3. `/plugin` (Claude) or `codex plugin list` confirms enabled, not just registered.

If it doesn't show up, use the troubleshooting checklist in [reload.md](reload.md).

## Growing the plugin afterward

Once wiring is verified, grow it without touching registration again:

- **New skill** → `skills/<name>/SKILL.md` (frontmatter `name` + `description`). Use create-new-skill.
- **Hook** → script + hooks JSON, referenced from the plugin manifest.
- **Agent** → `agents/<name>/AGENT.md`.
- **Slash command** → `commands/<name>.md`.

Every change ships on the next session start — but see [reload.md](reload.md) for the Codex snapshot refresh and the Claude version-bump gotcha.
