# Claude Sessions

Claude Code session storage can vary by installation. Use tolerant discovery and parsing.

## Candidate Locations

Search these roots when they exist:

```text
~/.claude/projects/**/*.jsonl
~/.claude/**/*.jsonl
```

Prefer files whose JSON event timestamps fall on the target date. If no timestamp exists, use file mtime only as a weak fallback and mark confidence `low`.

## Tolerant Event Model

Claude JSONL may contain events shaped like:

- top-level `type`
- top-level `timestamp`
- `message.role`
- `message.content`
- `cwd`, `session_id`, `uuid`, or similar metadata
- tool use/tool result blocks inside message content arrays

Do not assume a fixed schema. Parse conservatively:

- user text from top-level `message.role == "user"` or `type == "user"`
- assistant text from top-level `message.role == "assistant"` or `type == "assistant"`
- tool names from content blocks with `type == "tool_use"` or fields named `name`
- timestamps from `timestamp`, `created_at`, or nested equivalents

## Scripts

Collect candidates:

```bash
python3 /path/to/agent-toolkit/skills/daily-dev-log/scripts/collect_claude_sessions.py --date YYYY-MM-DD
```

First-pass filter:

```bash
python3 /path/to/agent-toolkit/skills/daily-dev-log/scripts/filter_claude_candidates.py claude-collection.json
```

Extract one session digest:

```bash
python3 /path/to/agent-toolkit/skills/daily-dev-log/scripts/extract_claude_session.py /path/to/session.jsonl
```

Both scripts output JSON and should tolerate unknown fields.
