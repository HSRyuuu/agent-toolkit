---
name: create-claude-plugin
description: Scaffold a new local Claude Code plugin from scratch — directory structure, plugin.json, marketplace.json, settings.json registration, and load verification. Use whenever the user wants to create a new plugin, register a local directory as a Claude Code marketplace, set up a personal toolkit/skill-collection plugin, or troubleshoot why a newly created plugin is not loading. Trigger phrases include "플러그인 만들기", "plugin 세팅", "plugin scaffold", "local marketplace 등록", "plugin이 로드 안 됨".
---

# Creating a Local Claude Code Plugin

This skill walks through building a new Claude Code plugin from an empty directory and registering it as a local-directory marketplace. The result is a plugin you can iterate on in place — every change is picked up on the next session start, with no publish, push, or build step.

## When this is the right approach

Use the local-directory marketplace pattern when:

- The plugin is personal — only you will use it.
- You want to edit skills/agents/hooks and have the changes reflected on the next session.
- You're not ready to publish to a git-based marketplace.

For a published, multi-plugin marketplace the file shapes are nearly identical, but `marketplace.json` lives in a separate repo and lists multiple plugin entries. This skill focuses on the single-plugin local case because that's the most common starting point.

## What you'll produce

```
<plugin-root>/
├── .claude-plugin/
│   ├── plugin.json         # plugin metadata
│   └── marketplace.json    # marketplace metadata (single-plugin marketplace pointing at "./")
├── skills/                 # at least one skill so you can verify the plugin loaded
│   └── <skill-name>/SKILL.md
├── agents/                 # optional, add later
├── hooks/                  # optional, add later
└── commands/               # optional, add later
```

Plus two edits in `~/.claude/settings.json`:

- A new entry under `extraKnownMarketplaces` registering the directory as a marketplace.
- A new entry under `enabledPlugins` flipping the plugin on.

## Step 1 — Decide names up front

Three names look similar but mean different things. Keeping them distinct up front avoids confusion later:

| Name                 | Example                                   | What it identifies                                                                                                                                                                         |
| -------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **plugin name**      | `agent-toolkit`                         | The plugin itself. Goes in `plugin.json` and is the part before `@` in `enabledPlugins`.                                                                                                   |
| **marketplace name** | `agent-toolkit-local`                   | The marketplace that exposes the plugin. Goes in `marketplace.json` and `extraKnownMarketplaces`. Convention: append `-local` to the plugin name so it's obvious it's a local-only source. |
| **directory path**   | `/Users/.../dev/personal/agent-toolkit` | Where the plugin lives on disk. The `extraKnownMarketplaces` entry points here. Use an **absolute** path.                                                                                  |

The `enabledPlugins` key is the composite `<plugin-name>@<marketplace-name>` — e.g. `agent-toolkit@agent-toolkit-local`. This composite is how Claude Code joins the on/off switch to the source.

## Step 2 — Create the plugin directory and metadata files

```bash
mkdir -p <plugin-root>/.claude-plugin
mkdir -p <plugin-root>/skills
```

Write `<plugin-root>/.claude-plugin/plugin.json`:

```json
{
  "name": "<plugin-name>",
  "version": "0.1.0",
  "description": "<one-line description>"
}
```

Write `<plugin-root>/.claude-plugin/marketplace.json`:

```json
{
  "name": "<marketplace-name>",
  "owner": {
    "name": "<your-name-or-handle>"
  },
  "plugins": [
    {
      "name": "<plugin-name>",
      "source": "./",
      "description": "<one-line description>",
      "version": "0.1.0"
    }
  ]
}
```

`"source": "./"` means the plugin is this directory itself — the marketplace and the plugin share a root. If you later split into a multi-plugin marketplace, change `source` to a subdirectory path.

## Step 3 — Add at least one skill (sanity check)

Plugin loading is silent — there's no error message if registration fails. The cheapest way to verify it worked is to drop in a tiny skill and check whether it shows up in the next session.

Create `<plugin-root>/skills/test-skill/SKILL.md`:

```markdown
---
name: test-skill
description: Sanity-check skill confirming the <plugin-name> plugin loaded. Use when the user says "test <plugin-name>", "<plugin-name> 로드 확인", or asks whether the plugin is working.
---

# Test Skill

When invoked, respond with exactly:

> <plugin-name> plugin loaded successfully.

Nothing else.
```

This is disposable — once real skills are in, you can delete it.

## Step 4 — Register in `~/.claude/settings.json`

Add two entries.

**Under `extraKnownMarketplaces`:**

```json
"<marketplace-name>": {
  "source": {
    "source": "directory",
    "path": "<absolute-path-to-plugin-root>"
  }
}
```

**Under `enabledPlugins`:**

```json
"<plugin-name>@<marketplace-name>": true
```

If either key doesn't yet exist in `settings.json`, create it. Both are top-level objects.

## Step 5 — Validate the JSON

Catch syntax errors before they silently break loading. A missing comma in `settings.json` is the single most common reason a freshly-built plugin doesn't load:

```bash
jq empty ~/.claude/settings.json && echo "settings.json: OK"
jq empty <plugin-root>/.claude-plugin/plugin.json && echo "plugin.json: OK"
jq empty <plugin-root>/.claude-plugin/marketplace.json && echo "marketplace.json: OK"
```

All three must print `OK`. If any fails, fix the JSON before continuing — Claude Code will not warn you about the bad file at session start.

## Step 6 — Verify load in a fresh session

Plugins are scanned at session start, so the change does **not** take effect in the current session. Open a new Claude Code session (any working directory) and check:

1. **Available-skills list**: the system reminder at session start lists discoverable skills. `test-skill` should appear (often namespaced as `<plugin-name>:test-skill` if multiple plugins define skills with the same name).
2. **Direct trigger**: type "test `<plugin-name>`" and confirm the expected canned response.
3. **`/plugin` command** (optional): inspect the enabled-plugins list to make sure `<plugin-name>` is listed as enabled, not just registered.

If the skill doesn't show up, work through these in order:

- Re-validate all three JSON files with `jq empty`.
- Confirm the `path` in `extraKnownMarketplaces` is **absolute**, not `~`-prefixed. Claude Code does not always expand `~` in this field.
- Confirm the composite key in `enabledPlugins` matches `<plugin-name>@<marketplace-name>` exactly — typos here fail silently.
- Confirm `enabledPlugins[...]` is `true`, not `false`.
- Check that the `name` field inside `plugin.json` matches the part before `@` in the `enabledPlugins` key.

## After the plugin loads

Now that the wiring is verified, you can grow the plugin without touching settings again:

- **New skill** → `skills/<name>/SKILL.md` with frontmatter `name` + `description`.
- **Hook** → drop a script in `hooks/` and reference it from `plugin.json` under a top-level `"hooks"` key (matcher → command). See an existing plugin's `plugin.json` for the exact shape.
- **Agent** → `agents/<name>/AGENT.md`.
- **Slash command** → `commands/<name>.md`.

Every change ships on the next session start. No rebuild, no install step — that's the entire point of local-directory marketplaces.

## Why this pattern, vs. alternatives

- **vs. dropping skills directly into `~/.claude/skills/`**: Plugins give you namespacing, version metadata, hook registration, and a single on/off switch in `enabledPlugins`. Loose files in `~/.claude/skills/` have none of that and become hard to disable selectively.
- **vs. publishing to a git-based marketplace immediately**: Local-directory marketplaces let you iterate without committing or pushing. When the plugin matures and you want to share it, swap the `extraKnownMarketplaces` source from `directory` to `git` (or move `marketplace.json` to a public repo) — the plugin's internal layout doesn't change at all.
- **vs. a single project-scoped `.claude/CLAUDE.md` with helpers**: Project-scoped instructions only apply when you're working in that directory. A plugin is global to your Claude Code installation, so the skills are available everywhere.
