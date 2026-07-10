# KB Skills: First-Time Setup

Read this file completely when the user is using the KB skills for the first
time, no KB root resolves, or a KB Python helper reports a missing dependency.

## Runtime Model

The KB workflow has three persistent locations:

- `~/.config/kb/kb-config.json` — registered KB names and default selection
- the absolute KB root path recorded in that config
- `~/.venvs/agent-toolkit-kb` — isolated Python runtime for KB helpers

All bundled-resource resolution is internal to the active skill. Route work by
the skill name:

| Task | Route to |
|---|---|
| setup, root resolution, index, edit guard | `kb-manage` |
| structured search and recent activity | `kb-search` |
| deterministic and judgement lint | `kb-lint` |
| first real document write | `kb-write` |

When a bundled helper is needed, resolve its `scripts/` resource from that
skill itself. Never walk through another skill's directory or assume the four
skills share a parent directory.

## Installation Approval Invariant

Every installation-related mutation requires explicit user confirmation after
the exact source, command, destination, and impact are shown. One confirmation
may cover one fully enumerated batch; newly discovered actions require a new
confirmation. Read-only availability and version checks do not require one.

## Frontmatter Terms

- **YAML frontmatter** is the `---` metadata block at the top of a Markdown
  document.
- **`python-frontmatter`** is the Python package that reads that block. Its
  install name is `python-frontmatter`; its import name is `frontmatter`.
- **`PyYAML`** is the YAML parser used by `python-frontmatter`. Its install name
  is `PyYAML`; its import name is `yaml`.

The bundled `scripts/requirements.txt` locks both packages. Do not rely on
`PyYAML` being installed transitively or reuse a system-wide copy.

## 1. Confirm Skill Availability

Confirm the host exposes `kb-manage`, `kb-write`, `kb-search`, and `kb-lint` by
those names. If any are missing, report the missing skill name. Do not guess an
installation method or install anything without the approval gate.

## 2. Check Python

Use a dedicated virtual environment so Homebrew/system Python remains
untouched. The default KB interpreter is
`~/.venvs/agent-toolkit-kb/bin/python` (`Scripts/python.exe` on Windows).
Confirm the base Python is 3.10 or newer, then route to `kb-manage` and run its
bundled `scripts/check_kb_prerequisites.py`.

If Python is missing or too old, ask whether the user wants to select an
existing Python 3.10+ executable or install one. If the default venv is absent,
or a locked runtime package is missing or mismatched, resolve the bundled
`kb-manage/scripts/requirements.txt`, show its exact path and these commands,
then run them only after approval:

```bash
python3 -m venv ~/.venvs/agent-toolkit-kb
~/.venvs/agent-toolkit-kb/bin/python -m pip install -r <kb-manage-skill>/scripts/requirements.txt
```

Replace the first `python3` with the selected base executable when different.
Do not activate the venv implicitly; invoke its Python path explicitly for
deterministic helper runs. Do not use `sudo`, `--user`,
`--break-system-packages`, or modify a system Python. Rerun the `kb-manage`
prerequisite check with the venv Python and require exit `0`.
The check must confirm exact locked versions of both `python-frontmatter` and
`PyYAML`.

Obsidian Agent Skills are optional. When requested, route to `kb-manage` and
follow its `references/obsidian-skills.md` confirmation gate.

## 3. Configure The KB Root First

Every KB root must be registered in `~/.config/kb/kb-config.json` before any KB
skill uses it. Inspect the config read-only first.

When the file is missing or contains no registered KB, propose
`~/KnowledgeBase` with registration name `personal` and make it the default.
Ask whether to use that proposal or register a different absolute directory;
do not ask an open-ended “where should I write?” question. If the user chooses
another directory, use that exact absolute path. Expand `~` before persisting;
the config stores absolute paths.

Show the exact config and root-directory changes, then get approval. Write the
config before initializing the root. The canonical new-config shape is:

```json
{
  "kbs": { "personal": "/absolute/path/to/kb" },
  "default": "personal"
}
```

Preserve unrelated registrations. On a name collision, ask whether to replace
the existing path or choose a new name. When migrating a legacy `{"path": ...}`
config, convert it to one `kbs` object with explicit names; do not leave both
shapes mixed. An absolute path supplied in a later request is usable only when
it matches a registered root. If the user declines config creation or update,
stop: KB search, lint, and writes cannot continue with an unregistered root.

## 4. Initialize The Root

Route setup to `kb-manage`:

1. Confirm the selected root is already present in `kb-config.json`.
2. Create the root directory after approval when it does not exist.
3. Read existing root guidance and setup files.
4. Create or adapt `AGENTS.md`, `index.md`, and `log.jsonl` from its templates.
5. Remove template placeholders; never leave a nonexistent example link.
6. Do not create `_raw/`. Create `_inbox/` only when requested.

Do not overwrite an existing file without showing the proposed change first.

## 5. Verify The Setup

Use `~/.venvs/agent-toolkit-kb/bin/python` for every helper below and route each
check by skill name:

| Check | Skill | Bundled helper and arguments |
|---|---|---|
| prerequisite | `kb-manage` | `scripts/check_kb_prerequisites.py` |
| registered absolute root | `kb-manage` | `scripts/resolve_kb_root.py /absolute/path/to/kb` |
| registered name | `kb-manage` | `scripts/resolve_kb_root.py personal` |
| config JSON | `kb-manage` | validate `~/.config/kb/kb-config.json` with the selected Python |
| index drift | `kb-manage` | `scripts/kb_build_index.py /absolute/path/to/kb --check` |
| metadata probe | `kb-search` | `scripts/kb_meta_search.py /absolute/path/to/kb --title __kb_setup_probe__` |
| clean lint | `kb-lint` | `scripts/kb_lint.py /absolute/path/to/kb` |

The no-result metadata probe succeeds when it exits `0`; do not create a fake
document just to test search. Root/config checks are mandatory because KB work
never proceeds with an unregistered path.

Setup is complete only when the prerequisite, applicable root/config checks,
index check, metadata probe, and lint all pass. If the user supplies a real
first note, route it to `kb-write`, then confirm `kb-search` can find it.

## Completion Report

Report the selected Python executable, dependency status, registered KB
name/path/default, files created or preserved, verification results, and any
pending first-document check. Do not report or persist any skill installation
location in the KB config.
