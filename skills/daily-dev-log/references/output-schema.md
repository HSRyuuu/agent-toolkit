# Output Schema

Use structured intermediate JSON to keep raw logs separate from personal journal text.

## Source Availability

```json
{
  "date": "2026-07-02",
  "sources": {
    "codex": {
      "available": true,
      "root": "/Users/name/.codex/sessions",
      "date_dir": "/Users/name/.codex/sessions/2026/07/02",
      "file_count": 3,
      "files": ["/absolute/path/session.jsonl"]
    },
    "claude": {
      "available": true,
      "root": "/Users/name/.claude",
      "file_count": 2,
      "files": ["/absolute/path/session.jsonl"],
      "note": "Fast detection note."
    },
    "kb": {
      "available": true,
      "config": "/Users/name/.config/kb/path",
      "root": "/absolute/path/to/kb"
    }
  }
}
```

## Session Candidate

```json
{
  "source": "codex",
  "session_id": "019f...",
  "file": "/absolute/path/to/session.jsonl",
  "started_at": "2026-07-02T12:05:52Z",
  "date": "2026-07-02",
  "cwd": "/path/to/project",
  "thread_source": "user",
  "event_count": 98,
  "user_message_count": 4,
  "assistant_message_count": 12,
  "tool_call_count": 12,
  "tool_names": ["exec_command", "memory_sessions"],
  "clean_user_requests": ["..."],
  "candidate_title": "Short inferred title",
  "confidence": "high"
}
```

## First-Pass Intermediate Artifact

```json
{
  "date": "2026-07-02",
  "stage": "first-pass-filter",
  "source_availability": {},
  "codex_candidates": [],
  "claude_candidates": [],
  "kb_candidates": [
    {
      "source": "kb",
      "path": "relative/or/absolute/path.md",
      "title": "Document title",
      "summary": "Why this may matter today",
      "evidence": ["created=2026-07-02", "updated=2026-07-02"],
      "confidence": "medium"
    }
  ],
  "rejected_or_supporting": [],
  "notes": []
}
```

Use this artifact as the user-facing evidence inventory. Do not perform second-pass extraction until this artifact exists.

Build it with:

```bash
python3 scripts/build_first_pass_artifact.py --date YYYY-MM-DD --sources sources.json --codex codex-filtered.json --claude claude-filtered.json --kb kb-candidates.json
```

## Session Digest

```json
{
  "source": "codex",
  "session_id": "019f...",
  "file": "/absolute/path/to/session.jsonl",
  "metadata": {},
  "messages": [
    {"role": "user", "text": "..."},
    {"role": "assistant", "text": "..."}
  ],
  "tool_calls": [
    {"name": "exec_command", "arguments": "...", "call_id": "call_..."}
  ],
  "tool_outputs": [
    {"call_id": "call_...", "output_excerpt": "..."}
  ],
  "mentioned_paths": ["/path/to/file"],
  "errors": ["..."]
}
```

## Final Daily File

Default path:

```text
<journal-root>/daily/YYYY/MM/YYYY-MM-DD.md
```

The final file should include:

- YAML frontmatter for search
- summary
- selected work items
- troubleshooting
- decisions
- follow-ups
- reflection
- evidence references with safe session ids and paths

Do not include raw session JSONL.
