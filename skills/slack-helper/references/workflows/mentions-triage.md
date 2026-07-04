# Mentions Triage

Use for "내 멘션 정리", "놓친 요청 찾아줘", or "내가 답장 안 한 멘션".

## Steps

1. Load identity and key channels.

```bash
python3 skills/slack-helper/scripts/slack_context.py show
```

2. Search recent mentions with compact output.

```bash
python3 skills/slack-helper/scripts/slack_search.py search request question follow-up --to-me --days 7 --count 50
```

3. Open only threads that look actionable.

```bash
python3 skills/slack-helper/scripts/slack_read.py thread --channel backend --ts 1717243200.000100
```

4. Classify results:
   - Needs my reply
   - Already answered
   - FYI only
   - Needs more context

## Output Shape

- Top 3 urgent items first.
- Include channel, requester, permalink, and one sentence reason.
- Mention if `resolve-me` or context setup is missing before searching.
