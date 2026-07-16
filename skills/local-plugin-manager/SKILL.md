---
name: local-plugin-manager
description: >
  Use for the full lifecycle of a local Claude Code/Codex plugin or local
  marketplace: scaffolding a new one, registering it, enabling/disabling,
  installing/removing, reloading or refreshing snapshots, checking status, and
  troubleshooting load failures. Triggers: "플러그인 만들기", "plugin scaffold",
  "local marketplace 등록", "플러그인 켜/꺼줘", "plugin reload",
  "marketplace refresh", "새 세션에 스킬이 안 보여", "Unknown command",
  "plugin이 로드 안 됨", "local plugin cache". Do NOT use for writing the skills
  themselves — use create-new-skill.
---

# Local Plugin Manager

Handles the whole life of a personal local plugin on both hosts: **build it → register it → run it → keep it fresh**. The target is a local-directory marketplace you iterate on in place — every source change is picked up on the next session start, with no publish, push, or build step.

Prefer a transparent command sequence over writing a toggle script; create a script only when the user asks for repeatable automation or the same lifecycle sequence has become project policy.

## Names to resolve first

Resolve these before doing anything. Four names look similar but mean different things:

| Name                 | Example                             | What it identifies                                                                                                   |
| -------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **PLUGIN_NAME**      | `agent-toolkit`                     | The plugin itself. From `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json`. Part before `@`.                |
| **MARKETPLACE_NAME** | `hsryuuu`                           | The marketplace exposing it. From `marketplace.json`. The same name can back a local directory source or a GitHub source; appending `-local` (e.g. `as-usual-local`) is a common convention when the marketplace is local-only. |
| **PLUGIN_ID**        | `agent-toolkit@hsryuuu`             | Composite `<PLUGIN_NAME>@<MARKETPLACE_NAME>` — how the host joins the on/off switch to the source.                   |
| **PLUGIN_ROOT**      | `~/dev/personal/agent-toolkit`      | Absolute path where the plugin source lives. Registration points here. Always **absolute**, never `~`-prefixed in JSON. |

Also settle **host scope**: `claude`, `codex`, or both. The hosts use separate registration files and separate cache paths, so a successful Claude refresh proves nothing about the Codex snapshot, and vice versa. The same plugin can even have a different `PLUGIN_ID` per host (see the reference installs below).

Use `jq` when available; otherwise `python3 -m json.tool` for JSON validation.

## Reference installs (real, working local plugins)

Two plugins are set up locally and serve as the canonical examples throughout the references:

| Plugin          | Source repo                        | Claude PLUGIN_ID                    | Codex PLUGIN_ID     | Codex registration pattern                                  |
| --------------- | ---------------------------------- | ----------------------------------- | ------------------- | ----------------------------------------------------------- |
| `agent-toolkit` | `~/dev/personal/agent-toolkit`     | `agent-toolkit@hsryuuu`             | `agent-toolkit@hsryuuu` | per-repo marketplace (`.agents/plugins/marketplace.json` in the repo) |
| `as-usual`      | `~/dev/personal/harness-as-usual`  | `as-usual@as-usual-local`           | `as-usual@personal` | shared home marketplace (`~/.agents/plugins/marketplace.json` + `~/plugins/<name>` symlink) |

Note `as-usual`: same plugin, different marketplace per host. Always resolve `PLUGIN_ID` from the host's own state (`claude plugin list` / `codex plugin list` / `~/.codex/config.toml`), never by assumption.

## Feature routing

Each feature lives in its own reference. Read only the one(s) the task needs:

| Task                                                                     | Reference                    |
| ------------------------------------------------------------------------ | ---------------------------- |
| Create a new plugin from scratch; register an existing repo as a plugin; manifest/marketplace file shapes | [references/setup.md](references/setup.md)   |
| Check status, inspect registration/cache state, validate marketplace shape, understand host folder layouts | [references/manage.md](references/manage.md) |
| Turn a plugin on or off (enable/disable, install/remove)                  | [references/toggle.md](references/toggle.md) |
| Reload after source changes, refresh stale snapshots, "source has it but session doesn't" | [references/reload.md](references/reload.md) |

Rules that apply across all features:

- **Status first.** Run the status checks in `manage.md` before mutating anything.
- **Never delete a whole cache tree.** Only remove the resolved `<MARKETPLACE_NAME>/<PLUGIN_NAME>[/<VERSION>]` subpath, and only when the reference says so.
- **A new session is always required** after changing plugin state, hooks, skills, or manifests. Already-running sessions never reload.
- If a host CLI is unavailable, report that host as skipped instead of fabricating state.

## Reporting

After acting, report:

- Which host(s) changed.
- Whether the action was scaffold, enable/disable, install/remove, or snapshot refresh.
- The resolved `PLUGIN_ID` per host.
- Whether a new session is required.
- Any skipped host and why.

## Why local-directory plugins, vs. alternatives

- **vs. loose files in `~/.claude/skills/`** — plugins give namespacing, version metadata, hook registration, and a single on/off switch.
- **vs. publishing to a git marketplace immediately** — local-directory marketplaces iterate without commit/push; swap the source from `directory` to `git` later without changing internal layout.
- **vs. project-scoped `CLAUDE.md` helpers** — a plugin is global to your install, so skills are available everywhere.
