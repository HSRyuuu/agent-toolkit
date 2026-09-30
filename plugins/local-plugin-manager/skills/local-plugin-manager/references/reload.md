# Reload — Refresh After Source Changes & Troubleshoot Stale State

Use after editing skills, hooks, or manifests in a local plugin, or when a session doesn't see what the source has.

## The three surfaces

Every "my change isn't showing up" problem is a disagreement between three surfaces. Diagnose in this order before editing any source:

1. **Source repository** — `$PLUGIN_ROOT/skills/<skill-name>/SKILL.md` exists?
2. **Installed snapshot** — the host cache:
   - Claude: `~/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/skills/`
   - Codex: `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/<version>/` (local versions may carry a `+codex.<timestamp>` suffix)
3. **Current session** — running sessions never reload newly installed skills, hooks, or manifests.

| Disagreement                        | Fix                                        |
| ----------------------------------- | ------------------------------------------ |
| Source has it, snapshot doesn't     | Refresh the snapshot (below, per host)     |
| Snapshot has it, session doesn't    | Start a new session                        |
| Cross-host mismatch                 | Refresh each host independently — separate caches, separate `PLUGIN_ID`s |

## Claude Code reload

```bash
claude plugin validate "$PLUGIN_ROOT"
claude plugin marketplace update "$MARKETPLACE_NAME" || true
claude plugin update "$PLUGIN_ID" || true
claude plugin details "$PLUGIN_ID"
```

**Known gotcha — stale skill-invocation cache:** `claude plugin details` reads the source directory live and shows renamed/added/removed skills immediately, which makes it *look* like the reload worked. But the content served when a skill actually fires comes from the versioned snapshot at `~/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`. If `plugin.json`'s `version` does not change, both `marketplace update` and `plugin update` report "already at the latest version" and do **not** refresh that snapshot — edited/renamed/deleted skill files silently keep serving old content.

If `details` shows different skills than what actually fires, force a resync:

```bash
VERSION=$(jq -r '.version' "$PLUGIN_ROOT/.claude-plugin/plugin.json")
rm -rf "$HOME/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION"
claude plugin marketplace update "$MARKETPLACE_NAME"
claude plugin update "$PLUGIN_ID" || true
```

Only remove the resolved `$PLUGIN_NAME/$VERSION` subpath, never the whole `~/.claude/plugins/cache` tree.

**Safest long-term habit: bump `version` in `.claude-plugin/plugin.json` on every source change.** The cache key changes and a real resync happens automatically — this is why the local cache shows e.g. `agent-toolkit/0.1.2/` rather than one eternally-stale `0.1.0`.

## Codex reload

Codex "reload" = remove + clear the resolved cache path + re-add:

```bash
codex plugin marketplace add "$PLUGIN_ROOT" --json   # $HOME instead for the shared "personal" marketplace
codex plugin remove "$PLUGIN_ID" --json || true
rm -rf "$HOME/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME"
codex plugin add "$PLUGIN_ID" --json
codex plugin list
```

Use the manual cache removal only for local development refreshes, and only for the resolved plugin path. Never remove the whole Codex plugin cache unless the user explicitly asks.

## Fresh plugin never loaded at all

If a newly scaffolded plugin never appears in any session, work these in order (Claude side; misregistration fails silently):

1. Re-validate all JSON: `jq empty ~/.claude/settings.json "$PLUGIN_ROOT"/.claude-plugin/*.json`
2. `extraKnownMarketplaces` `path` is **absolute**, not `~`-prefixed.
3. `enabledPlugins` key matches `<PLUGIN_NAME>@<MARKETPLACE_NAME>` exactly and is `true`, not `false`.
4. `plugin.json`'s `name` matches the part before `@`.

Codex side:

1. `codex plugin marketplace list` shows the marketplace with the right `source`.
2. The marketplace's `source.path` subpath resolves — check the symlink (`plugins/<name> -> ..` per-repo, or `~/plugins/<name> -> <repo>` for `personal`): `ls -l` and confirm the target exists.
3. `[plugins."<PLUGIN_ID>"]` in `~/.codex/config.toml` has `enabled = true`.
4. `.codex-plugin/plugin.json`'s `"skills"` path points at the real skill root (`./skills/`).

## After any reload

Tell the user to start a new session on the refreshed host — existing sessions keep already-loaded skills and hooks. Report which host was refreshed, the `PLUGIN_ID`, whether a cache path was removed (and which one), and that a fresh session is required.
