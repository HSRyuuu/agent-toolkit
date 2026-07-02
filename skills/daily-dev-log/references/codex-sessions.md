# Codex Sessions

Codex Desktop stores raw session events as JSONL files.

## Common Location

```text
~/.codex/sessions/YYYY/MM/DD/*.jsonl
```

Do not assume this location exists. If it is absent, report that Codex session evidence is unavailable and continue with other evidence.

## Event Model

Read files line-by-line as JSON objects. Relevant event shapes seen in Codex sessions:

| Event | Meaning |
|---|---|
| `.type == "session_meta"` | session id, cwd, source, thread source, timestamp |
| `.type == "response_item" and .payload.type == "message"` | user, assistant, developer messages |
| `.type == "response_item" and .payload.type == "function_call"` | tool call request |
| `.type == "response_item" and .payload.type == "function_call_output"` | tool call result |
| `.type == "response_item" and .payload.type == "reasoning"` | reasoning metadata; ignore for daily logs |
| `.type == "event_msg"` | UI/runtime status; use only for timing or final-answer fallback |

Primary human sessions usually have `session_meta.payload.thread_source == "user"`. Treat `subagent`, `guardian`, and similar thread sources as supporting evidence unless the user explicitly wants internal agent activity.

## Clean User Request Rule

The first user message can include environment instructions, `AGENTS.md`, and old transcript context. For work candidates:

1. Prefer later user messages that are short and specific.
2. Strip or summarize blocks headed by `# AGENTS.md instructions`, `<INSTRUCTIONS>`, `<environment_context>`, `<permissions instructions>`, and transcript dumps.
3. Keep the user's actual request text verbatim when it is visible.
4. If the clean request cannot be isolated confidently, mark confidence `medium` or `low`.

## Scripts

Collect candidates:

```bash
python3 /path/to/agent-toolkit/skills/daily-dev-log/scripts/collect_codex_sessions.py --date YYYY-MM-DD
```

First-pass filter:

```bash
python3 /path/to/agent-toolkit/skills/daily-dev-log/scripts/filter_codex_candidates.py codex-collection.json
```

Extract one session digest:

```bash
python3 /path/to/agent-toolkit/skills/daily-dev-log/scripts/extract_codex_session.py /path/to/session.jsonl
```

Both scripts output JSON.
