# Optional Obsidian Skills

Use this reference when a Markdown KB is also an Obsidian vault, or when the
user asks for wikilinks, embeds, callouts, properties, Bases, Canvas, or the
Obsidian CLI.

Obsidian support is optional. Normal `kb-manage`, `kb-write`, `kb-search`, and
`kb-lint` work must remain usable as plain Markdown workflows.

Official source: [`kepano/obsidian-skills`](https://github.com/kepano/obsidian-skills)

## Installation Approval Gate

**Never install automatically.** Read-only availability, command, and conflict
checks do not need confirmation. Before any mutation, show the user:

1. source repository and installation method
2. selected skills (or all skills)
3. exact command or copy operation
4. destination path and existing conflicts
5. prerequisites or additional runtime dependencies
6. reload/restart and verification plan

Then ask for explicit confirmation. One confirmation may cover one clearly
enumerated batch. Any newly discovered prerequisite, changed command, different
target, update, reinstall, enablement, clone, or copy requires a new
confirmation. A broad request such as “set it up” or “install whatever it
needs” is not approval for undisclosed actions.

If the agent would reload, restart, or close the user's application or agent
session, disclose that action and ask first. Telling the user to open a fresh
session does not itself modify their environment.

Do not download, clone, run `npx`, add a marketplace, install a plugin, copy or
symlink skill files, enable a plugin, install Node/Obsidian/Defuddle, update, or
remove anything before this gate passes.

## 1. Check Whether Installation Is Needed

Look for the required skills in the current session:

| Skill | Use only when |
|---|---|
| `obsidian-markdown` | editing Obsidian Markdown, properties, wikilinks, embeds, or callouts |
| `obsidian-bases` | creating or editing `.base` views |
| `json-canvas` | creating or editing `.canvas` files |
| `obsidian-cli` | controlling an open Obsidian app or developing plugins/themes |
| `defuddle` | extracting clean Markdown from web pages |

If the needed skills are already present, do not reinstall them. Obsidian
itself is not required for the first three file-format skills; `obsidian-cli`
requires Obsidian to be open. Installing an Agent Skill does not install its
runtime tools.

## 2. Choose A Method

Prefer one method and do not mix installation mechanisms for the same copy.

| Environment | Preferred option | Notes |
|---|---|---|
| Claude Code | official plugin marketplace | simplest official Claude flow |
| Claude Code or Codex | official `npx skills add` command | needs `npx`; may download and execute the skills installer |
| Codex | manual copy to the Codex skills directory | most explicit control over selected files and conflicts |
| Claude Code | manual copy under the vault's `.claude/` directory | useful for vault-local installation |

Before choosing, inspect existing destinations and conflicts read-only. Ask
whether the user wants every upstream skill or only the skills needed for the
requested Obsidian features.

## 3. Claude Code Marketplace

The upstream README provides these Claude Code commands:

```text
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```

Treat marketplace registration and plugin installation as two disclosed
mutations. Show both commands and get confirmation for the batch before running
either. If the marketplace is already registered, skip the first command. Do
not invent a Codex marketplace equivalent; the upstream marketplace commands
are documented for Claude Code.

Treat the marketplace option as a whole-plugin installation unless its current
prompt explicitly offers a supported subset. If the user wants only selected
skills and the marketplace does not offer that choice, use the `npx` or manual
method after showing and confirming the changed plan.

After installation, open a fresh Claude Code session and verify the selected
skill names are available. If the agent would close or restart the user's
session itself, ask first; otherwise tell the user a fresh session is required.

## 4. `npx skills add` For Claude Code Or Codex

The upstream README provides HTTPS and SSH forms. Prefer HTTPS unless the user
already uses GitHub SSH authentication:

```bash
npx skills add https://github.com/kepano/obsidian-skills
```

SSH alternative:

```bash
npx skills add git@github.com:kepano/obsidian-skills.git
```

Before running either command:

1. Check `command -v npx` and `npx --version` read-only.
2. Explain that `npx` may download and execute the `skills` installer package.
3. Show the source URL, selected target agent, selected skills, destination,
   and exact command.
4. Get explicit confirmation.

If `npx` is missing, do not install Node.js/npm automatically. Explain the
missing prerequisite, show the proposed installation method and impact, and get
a separate confirmation before installing it. After Node installation, show
the `npx skills add` command again and confirm that action before running it.

Follow the installer's prompts rather than assuming a target. Stop if the
prompted destination, selected agent, or overwrite plan differs from what the
user approved.

The upstream `npx` command follows the repository state resolved at install
time; it is not documented as commit-pinned. Disclose that before confirmation.
If reproducibility is required, use a manual installation from a reviewed commit
and include the exact commit SHA and checkout/copy commands in the approved plan.
Do not invent an unsupported `npx` pinning syntax.

## 5. Manual Installation

Manual installation is also a mutating installation. Inspect the source and
destination first, show the exact copy plan, then get confirmation before
cloning, downloading, copying, or overwriting.

### Claude Code

The upstream README says to place the repository contents under `.claude/` in
the Obsidian vault (or other Claude Code working folder). The intended root is:

```text
<vault>/.claude/
```

The final path for each installed skill must be:

```text
<vault>/.claude/skills/<skill-name>/SKILL.md
```

Preserve any existing `.claude/` content. List conflicts and merge only the
approved files; never replace the directory wholesale.

### Codex

Copy the upstream `skills/` entries into the user's Codex skills path, typically
`~/.codex/skills`, so each selected skill ends at:

```text
~/.codex/skills/<skill-name>/SKILL.md
```

Do not assume `~/.codex/skills` when the active Codex home differs. Inspect the
actual configured skills path, list name conflicts, and ask whether to skip,
replace, or choose another destination. Never overwrite an existing skill
silently.

## 6. Runtime Dependencies Are Separate Installs

Installing the skill documents does not install these optional runtimes:

- `obsidian-cli` uses the `obsidian` CLI and requires Obsidian to be open.
- `defuddle` uses the Defuddle CLI.
- the `npx` method requires Node.js/npm/npx.

Check availability read-only. If a runtime is missing, explain which requested
feature needs it and ask whether to install it. Show the exact source, command,
destination, and impact before receiving confirmation. Do not install a runtime
merely because its skill was included; install it only when the user wants the
feature that needs it.

## 7. Verification

After an approved installation:

1. Verify expected skill directories and `SKILL.md` files exist without
   modifying them.
2. Open or ask the user to open a fresh agent session.
3. Verify only the selected skill names are discoverable.
4. For `obsidian-cli`, with Obsidian already open, run `obsidian help` before
   attempting vault operations.
5. Do not create test `.md`, `.base`, or `.canvas` files in the user's vault
   unless that write was separately requested or approved.

Report the method, source, destination, selected skills, runtime dependencies,
verification result, and anything skipped. Installation is not complete merely
because a clone or copy command exited successfully.

## Updates And Removal

Use the same mechanism that installed the skills. Inspect the current source,
destination, and conflicts first. Updating, reinstalling, disabling, deleting,
or switching mechanisms is a new mutation and always requires explicit user
confirmation after the exact action is shown.

## Boundaries

- Do not make Obsidian a dependency of the generic KB model.
- Do not bulk-insert wikilinks merely because the skills are available.
- Do not use Bases, Canvas, embeds, callouts, or CLI operations unless the user
  asks or local KB guidance requires them.
- Prefer regular Markdown links for external URLs.
- Maintained Markdown documents remain the KB source of truth.
