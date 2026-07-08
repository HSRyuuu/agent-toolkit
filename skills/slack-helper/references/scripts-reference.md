# slack-helper Scripts Reference

Use this file when a Slack request does not exactly match one of the workflow files, or when you need to combine scripts freely.

## Common Pattern

1. Read local memory first: `~/.config/slack-helper/MEMORY.md` (선호 규칙과 채널 별칭·ID가 여기 있다; 없으면 건너뛴다)
2. Search broadly with compact output: `python3 "<SKILL_DIR>/scripts/slack_search.py" search <keywords> --days 7`
3. Open only useful threads: `python3 "<SKILL_DIR>/scripts/slack_read.py" thread --channel <id-or-name> --ts <thread_ts>`
4. Use `--raw` only when compact output hides a field you truly need.

## Scripts

| Script | Use For | Key Commands |
| --- | --- | --- |
| `slack_setup.py` | OAuth, auth checks, identity setup | `setup-guide`, `init-oauth`, `oauth-start`, `oauth-finish`, `auth-test`, `team-info`, `read-sample`, `set-me`, `resolve-me` |
| `slack_read.py` | direct reads with bot token | `users`, `channels`, `channel-history [--on YYYY-MM-DD]`, `thread` |
| `slack_search.py` | search with user token | `search <keywords> [--from ...] [--in ...] [--to-me] [--after ...] [--days ...]` |
| `slack_common.py` | shared implementation | import-only; do not call as CLI |

`slack_read.py`의 `--channel`은 채널 ID(`C...`) 또는 공개 채널 이름을 받는다. 이름이면 `conversations.list`로 ID를 찾는다. MEMORY.md에 별칭이 기록되어 있으면 에이전트가 거기 적힌 ID를 그대로 넘기는 편이 빠르다.

## Search Modifiers

- `--from me` or `--from @handle`: messages from a sender.
- `--in backend`: 채널 이름 그대로 Slack search `in:`에 들어간다. MEMORY.md의 별칭은 에이전트가 실제 채널 이름으로 바꿔서 넘긴다.
- `--to-me`: config.json에 저장된 내 `<@U...>` 멘션을 검색한다. Run `slack_setup.py resolve-me` first if missing.
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
- Do not store message bodies in `MEMORY.md`; channel notes stay one line.
