# Root Resolution

Daily dev logs are personal documents. Resolve the journal root only from explicit user intent or the dedicated config file.

## Resolution Order

1. User-provided absolute path.
2. `~/.config/daily-dev-log/path`, if it exists and points to a directory.

If neither source resolves, ask the user for an absolute journal root. Do not infer the root from the current project, a company repository, Obsidian markers, or the presence of Markdown files.

The global config file has no extension. It is a UTF-8 plaintext file named `path`; the first non-empty line is the absolute journal root.

Example:

```text
/Users/happyhsryu/Documents/personal-work-journal
```

## Fast Check

Run:

```bash
python3 /path/to/agent-toolkit/skills/daily-dev-log/scripts/resolve_daily_dev_log_root.py
```

With a user-provided path:

```bash
python3 /path/to/agent-toolkit/skills/daily-dev-log/scripts/resolve_daily_dev_log_root.py /absolute/path/to/journal
```

The script prints the resolved root on stdout. If it fails, ask the user to provide an absolute path or to create/update `~/.config/daily-dev-log/path`.

## Default Folder Shape

Use this shape unless the user's existing journal guidance says otherwise:

```text
<journal-root>/
├── daily/
│   └── YYYY/
│       └── MM/
│           └── YYYY-MM-DD.md
├── troubleshooting/
│   └── YYYY/
│       └── YYYY-MM-DD-short-title.md
├── weekly/
├── index/
│   └── sessions-YYYY-MM-DD.json
└── README.md
```

Create folders only when saving an approved output.
