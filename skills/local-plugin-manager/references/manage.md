# Manage — Status, Inspection, and Host Layouts

Read-only management: check what is registered, enabled, installed, and cached on each host. Run this **before** any mutation in toggle.md or reload.md.

## Status commands

```bash
# Claude Code
claude plugin marketplace list
claude plugin list
claude plugin details "$PLUGIN_ID"

# Codex
codex plugin marketplace list
codex plugin list
grep -E "$PLUGIN_NAME|$MARKETPLACE_NAME" "$HOME/.codex/config.toml" || true
find "$HOME/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME" -maxdepth 2 -type f -name plugin.json 2>/dev/null
```

If a CLI is unavailable, report that host as skipped instead of fabricating state.

**Caution:** `claude plugin details` reads the *source directory* live, not the installed snapshot — it can look current while the snapshot serving actual skill invocations is stale. Snapshot truth lives in the cache paths below; see [reload.md](reload.md).

## Where each host keeps state

### Claude Code

| Surface                | Path                                                             | Notes                                                        |
| ---------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------ |
| Registration + on/off  | `~/.claude/settings.json` → `extraKnownMarketplaces`, `enabledPlugins` | Directory-source marketplaces with absolute paths.     |
| Installed snapshot     | `~/.claude/plugins/cache/<MARKETPLACE>/<PLUGIN>/<VERSION>/`      | Versioned copy actually served on skill invocation.          |
| Git marketplaces       | `~/.claude/plugins/marketplaces/<name>/`                         | Cloned marketplace repos (e.g. `claude-plugins-official`).   |
| Plugin data            | `~/.claude/plugins/data/`                                        | Per-plugin runtime data; not part of the snapshot.           |

Real cache state with both local plugins installed:

```
~/.claude/plugins/cache/
├── hsryuuu/agent-toolkit/0.1.2/
└── as-usual-local/as-usual/0.1.0/
```

The `<VERSION>` directory name comes from `plugin.json`'s `version` field — this is why a version bump forces a fresh snapshot (see reload.md).

### Codex

| Surface               | Path                                                            | Notes                                                                 |
| --------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------- |
| Registration + on/off | `~/.codex/config.toml` → `[marketplaces.<name>]`, `[plugins."<id>"]` | Written by the `codex plugin` CLI; avoid hand-editing.           |
| Installed snapshot    | `~/.codex/plugins/cache/<MARKETPLACE>/<PLUGIN>/<VERSION>/`      | Version may carry a `+codex.<timestamp>` build suffix for local installs. |
| Marketplace metadata  | `<marketplace-source>/.agents/plugins/marketplace.json` (per-repo) or `~/.agents/plugins/marketplace.json` (shared `personal`) | See setup.md for the two patterns. |

Real cache state:

```
~/.codex/plugins/cache/
├── hsryuuu/agent-toolkit/0.1.2+codex.20260705013442/
└── personal/as-usual/0.1.0/
```

And the matching `config.toml` sections:

```toml
[marketplaces.hsryuuu]
source_type = "local"
source = "/Users/<user>/dev/personal/agent-toolkit"

[marketplaces.personal]
source_type = "local"
source = "/Users/<user>"

[plugins."agent-toolkit@hsryuuu"]
enabled = true

[plugins."as-usual@personal"]
enabled = true
```

Note `as-usual` is `as-usual@personal` here but `as-usual@as-usual-local` on the Claude side — always resolve `PLUGIN_ID` per host from this state, never by assumption.

## Validate marketplace shape

For Codex, if a plugin's `source.path` is a subpath such as `./plugins/<name>`, confirm that path resolves from the marketplace source dir (both real installs satisfy this via symlink — `plugins/agent-toolkit -> ..` in the repo, `~/plugins/as-usual -> <repo>` in home):

```bash
jq empty .agents/plugins/marketplace.json .codex-plugin/plugin.json
jq -r '.name, .plugins[].name, .plugins[].source.path // .plugins[].source' .agents/plugins/marketplace.json
ls -l plugins/ 2>/dev/null   # check the symlink target exists

# Claude Code
jq empty .claude-plugin/marketplace.json .claude-plugin/plugin.json
claude plugin validate "$PLUGIN_ROOT"
```

## Quick health matrix

For a full health check of one plugin, confirm each cell and report the table:

| Surface            | Claude Code                                          | Codex                                                  |
| ------------------ | ---------------------------------------------------- | ------------------------------------------------------ |
| Source manifest OK | `jq empty .claude-plugin/*.json`                     | `jq empty .codex-plugin/plugin.json`                   |
| Registered         | `extraKnownMarketplaces` has the marketplace         | `[marketplaces.<name>]` in config.toml                 |
| Enabled            | `enabledPlugins["<id>"] == true`                     | `[plugins."<id>"] enabled = true`                      |
| Snapshot present   | `~/.claude/plugins/cache/<mkt>/<plugin>/<version>/`  | `~/.codex/plugins/cache/<mkt>/<plugin>/<version>/`     |
| Session sees it    | skill listed in a fresh session                      | skill listed in a fresh session                        |

Any row where source is ahead of snapshot, or snapshot ahead of session → go to [reload.md](reload.md).
