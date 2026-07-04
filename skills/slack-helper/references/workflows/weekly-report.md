# Weekly Report

Use for "주간보고 초안", "이번 주 내가 한 일", or "업무일지 재료 모아줘".

## Steps

1. Load my identity and important channels.

```bash
python3 "<SKILL_DIR>/scripts/slack_context.py" show
```

2. Search my messages across the week.

```bash
python3 "<SKILL_DIR>/scripts/slack_search.py" search deploy review decision --from me --days 7 --count 50
```

3. Narrow by major channel when needed.

```bash
python3 "<SKILL_DIR>/scripts/slack_search.py" search deploy --from me --in backend --days 7
```

4. Open threads only for items that need evidence.

```bash
python3 "<SKILL_DIR>/scripts/slack_read.py" thread --channel backend --ts 1717243200.000100
```

## Output Shape

- Group by project or channel.
- Include completed work, decisions, blockers, and next actions.
- Prefer concise bullets with permalinks for traceability.
