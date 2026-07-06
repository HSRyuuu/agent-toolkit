# Toggle — Turn a Plugin On or Off

Enable/disable (Claude Code) and install/remove (Codex). Run the status checks in [manage.md](manage.md) first, and resolve `PLUGIN_ID` from each host's own state — the same plugin can have different IDs per host (`as-usual@as-usual-local` on Claude, `as-usual@personal` on Codex).

## Claude Code

Claude Code has first-class enable/disable — "off" keeps the plugin installed and registered, just inactive.

Turn on:

```bash
claude plugin install "$PLUGIN_ID" || true   # no-op if already installed
claude plugin enable "$PLUGIN_ID"
claude plugin details "$PLUGIN_ID"
```

Turn off:

```bash
claude plugin disable "$PLUGIN_ID"
claude plugin list
```

Equivalent state in `~/.claude/settings.json` — `enabledPlugins["<PLUGIN_ID>"]` flips between `true`/`false`. Prefer the CLI; if editing JSON directly, validate afterward:

```bash
jq empty ~/.claude/settings.json
```

## Codex

Codex has **no separate enable/disable toggle** — "off" means uninstall/remove. The marketplace registration survives removal, so turning back on is a plain `add`.

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

If `add` fails because the marketplace isn't registered, register it first (per-repo pattern shown; for the shared `personal` marketplace the source is `$HOME`):

```bash
codex plugin marketplace add "$PLUGIN_ROOT" --json
codex plugin marketplace list
```

## After toggling

- **Both hosts**: a new session is required for the change to take effect — running sessions keep already-loaded skills and hooks.
- Toggling does **not** refresh a stale snapshot. If the plugin was re-enabled after source changes, follow [reload.md](reload.md) as well.
- Report per host: action taken, resolved `PLUGIN_ID`, and that a fresh session is needed.
