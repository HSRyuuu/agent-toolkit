# KB Integration

Use KB lookup as optional read-only evidence for what the user documented on the target date.

## When To Search

Search the KB when:

- `kb-search` is available and the daily log would benefit from same-day notes.
- The user asks to include KB notes.
- Session evidence is thin and a configured KB may contain the day's manual notes.

Do not write KB documents from this skill unless the user explicitly asks. `daily-dev-log` writes the personal journal, not the KB.

## Root Resolution

Follow `kb-manage` rules. The KB root is resolved only from:

1. User-provided absolute path.
2. `~/.config/kb/path`, when valid.

If no KB root resolves, skip KB lookup and say it was unavailable.

## Useful Searches

Prefer exact-date searches:

```bash
python3 /path/to/agent-toolkit/skills/kb-search/scripts/kb_recent_activity.py /path/to/kb --date YYYY-MM-DD
python3 /path/to/agent-toolkit/skills/kb-search/scripts/kb_meta_search.py /path/to/kb --created YYYY-MM-DD
python3 /path/to/agent-toolkit/skills/kb-search/scripts/kb_meta_search.py /path/to/kb --updated YYYY-MM-DD
```

Also search body text for the exact date and local-language date forms when needed:

```bash
rg -n "YYYY-MM-DD|YYYY.MM.DD|M/D" /path/to/kb
```

Use found KB documents as candidates or supporting evidence. Cite paths in the candidate list, then include only safe summaries in the final daily log.

## Candidate Shape

Add KB results to the first-pass intermediate artifact under `kb_candidates`:

```json
{
  "source": "kb",
  "path": "relative/or/absolute/path.md",
  "title": "Document title",
  "summary": "Why this may matter today",
  "evidence": ["created=YYYY-MM-DD", "updated=YYYY-MM-DD"],
  "confidence": "medium"
}
```

KB candidates do not require second-pass JSON extraction unless the user selects them for more detail. If selected, read the relevant KB documents directly and summarize only safe experience-level information.
