# Incident Timeline

Use for "장애 회고", "이슈 타임라인", or "어제 장애 이야기 정리".

## Steps

1. Check known incident channels or aliases.

```bash
python3 skills/slack-helper/scripts/slack_context.py show
```

2. Search broad incident keywords over the target date.

```bash
python3 skills/slack-helper/scripts/slack_search.py search incident outage rollback error --after 2026-07-01 --before 2026-07-02 --count 50
```

3. Read channel history only for likely source channels.

```bash
python3 skills/slack-helper/scripts/slack_read.py channel-history --channel backend --limit 30
```

4. Open decisive threads on demand.

```bash
python3 skills/slack-helper/scripts/slack_read.py thread --channel backend --ts 1717243200.000100
```

## Output Shape

- Timeline in chronological order.
- Separate facts, suspected causes, decisions, follow-ups.
- Keep unresolved claims marked as unverified.
