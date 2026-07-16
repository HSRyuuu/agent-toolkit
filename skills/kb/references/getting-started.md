# KB Skill: First-Time Setup

Read this file completely when the user is using the KB skills for the first
time, no KB root resolves, or a KB Python helper reports a missing dependency.

## Runtime Model

The KB workflow has three persistent locations:

- `~/.config/kb/kb-config.json` — registered KB names and default selection
- the absolute KB root path recorded in that config
- `~/.venvs/agent-toolkit-kb` — isolated Python runtime for KB helpers

All bundled-resource resolution is internal to the `kb` skill. Route work by
mode:

| Task | Mode |
|---|---|
| setup, root resolution, index, edit guard | manage |
| structured search and recent activity | search |
| deterministic and judgement lint | lint |
| first real document write | write |

When a bundled helper is needed, resolve it from this skill's `scripts/`
directory. Never walk through another skill directory.

## Installation Approval Invariant

Follow the Installation Approval rules in
[`conventions.md`](./conventions.md) for every installation-related mutation in
this guide.

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

Confirm the host exposes the `kb` skill by that name. If it is missing, report
the missing skill name. Do not guess an
installation method or install anything without the approval gate.

## 2. Check Python

Use a dedicated virtual environment so Homebrew/system Python remains
untouched. The default KB interpreter is
`~/.venvs/agent-toolkit-kb/bin/python` (`Scripts/python.exe` on Windows).
Confirm the base Python is 3.10 or newer, then use manage mode and run the
bundled `scripts/check_kb_prerequisites.py`.

If Python is missing or too old, ask whether the user wants to select an
existing Python 3.10+ executable or install one. If the default venv is absent,
or a locked runtime package is missing or mismatched, resolve the bundled
`scripts/requirements.txt`, show its exact path and these commands,
then run them only after approval:

```bash
python3 -m venv ~/.venvs/agent-toolkit-kb
~/.venvs/agent-toolkit-kb/bin/python -m pip install -r <kb-skill>/scripts/requirements.txt
```

Replace the first `python3` with the selected base executable when different.
Do not activate the venv implicitly; invoke its Python path explicitly for
deterministic helper runs. Do not use `sudo`, `--user`,
`--break-system-packages`, or modify a system Python. Rerun the manage-mode
prerequisite check with the venv Python and require exit `0`.
The check must confirm exact locked versions of both `python-frontmatter` and
`PyYAML`.

Obsidian Agent Skills are optional. When requested, use manage mode and
follow its `references/obsidian-skills.md` confirmation gate.

## 3. Configure The KB Root First

Every KB root must be registered in `~/.config/kb/kb-config.json` before any
mode uses it. Inspect the config read-only first.

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

Use manage mode for setup:

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

| Check | Mode | Bundled helper and arguments |
|---|---|---|
| prerequisite | manage | `scripts/check_kb_prerequisites.py` |
| registered absolute root | manage | `scripts/resolve_kb_root.py /absolute/path/to/kb` |
| registered name | manage | `scripts/resolve_kb_root.py personal` |
| config JSON | manage | validate `~/.config/kb/kb-config.json` with the selected Python |
| index drift | manage | `scripts/kb_build_index.py /absolute/path/to/kb --check` |
| metadata probe | search | `scripts/kb_meta_search.py /absolute/path/to/kb --title __kb_setup_probe__` |
| clean lint | lint | `scripts/kb_lint.py /absolute/path/to/kb` |

The no-result metadata probe succeeds when it exits `0`; do not create a fake
document just to test search. Root/config checks are mandatory because KB work
never proceeds with an unregistered path.

Setup is complete only when the prerequisite, applicable root/config checks,
index check, metadata probe, and lint all pass. If the user supplies a real
first note, use write mode, then confirm search mode can find it.

## Completion Report

Report the selected Python executable, dependency status, registered KB
name/path/default, files created or preserved, verification results, and any
pending first-document check. Do not report or persist any skill installation
location in the KB config.
