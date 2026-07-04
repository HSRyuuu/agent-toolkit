# slack-helper Scripts Reference

Use this file when a Slack request does not exactly match one of the three workflow files, or when you need to combine scripts freely.

## Common Pattern

1. Read local context first: `python3 "<SKILL_DIR>/scripts/slack_context.py" show`
2. Search broadly with compact output: `python3 "<SKILL_DIR>/scripts/slack_search.py" search <keywords> --days 7`
3. Open only useful threads: `python3 "<SKILL_DIR>/scripts/slack_read.py" thread --channel <id-or-alias> --ts <thread_ts>`
4. Use `--raw` only when compact output hides a field you truly need.

## Scripts

| Script | Use For | Key Commands |
| --- | --- | --- |
| `slack_setup.py` | OAuth, auth checks, identity setup | `setup-guide`, `init-oauth`, `oauth-start`, `oauth-finish`, `auth-test`, `team-info`, `read-sample`, `set-me`, `resolve-me` |
| `slack_context.py` | local context cache | `show`, `add-channel`, `remove-channel`, `draft-summaries` |
| `slack_read.py` | direct reads with bot token | `users`, `channels`, `channel-history`, `thread` |
| `slack_search.py` | search with user token | `search <keywords> [--from ...] [--in ...] [--to-me] [--after ...] [--days ...]` |
| `slack_common.py` | shared implementation | import-only; do not call as CLI |

## Search Modifiers

- `--from me` or `--from @handle`: messages from a sender.
- `--in backend`: channel name or context alias; alias resolves to channel name for Slack search.
- `--to-me`: searches for stored `<@U...>` mention. Run `slack_setup.py resolve-me` first if missing.
- `--after YYYY-MM-DD`, `--before YYYY-MM-DD`, `--on YYYY-MM-DD`, or `--days N`.
- Multiple keywords run as separate searches, then merge by `(channel_id, ts)`.

## Combination Examples

Project history:

```bash
python3 "<SKILL_DIR>/scripts/slack_search.py" search "project phoenix" decision rollout --after 2026-06-01
python3 "<SKILL_DIR>/scripts/slack_read.py" thread --channel backend --ts 1717243200.000100
```

Person/channel focused search:

```bash
python3 "<SKILL_DIR>/scripts/slack_context.py" show
python3 "<SKILL_DIR>/scripts/slack_search.py" search migration --from @sample.user --in backend --days 30
```

Keyword monitoring snapshot:

```bash
python3 "<SKILL_DIR>/scripts/slack_search.py" search incident deploy rollback --days 7 --count 50
python3 "<SKILL_DIR>/scripts/slack_read.py" thread --channel C0123456789 --ts 1717243200.000100
```

## Limits

- `slack_read.py channel-history` and `thread` require bot access to that channel.
- If direct read fails with `not_in_channel`, use `slack_search.py search` and rely on permalinks.
- Do not store message bodies in `context.json`; summaries should stay one line.
