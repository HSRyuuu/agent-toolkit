# slack-helper Scripts Reference

Use this file when a Slack request does not exactly match one of the workflow files, or when you need to combine scripts freely.

## Common Pattern

1. Read local memory first: `~/.config/slack-helper/MEMORY.md` (선호 규칙과 채널 별칭·ID가 여기 있다; 없으면 건너뛴다)
2. Search broadly with compact output: `python3 "<SKILL_DIR>/scripts/slack_search.py" search <keywords> --days 7`
3. Open only useful threads: `python3 "<SKILL_DIR>/scripts/slack_read.py" thread --channel <id-or-name> --ts <thread_ts>` (`slack_read.py` tries the bot token first, then retries with the user token when bot access fails)
4. Use `--raw` only when compact output hides a field you truly need.

## Scripts

| Script | Use For | Key Commands |
| --- | --- | --- |
| `slack_setup.py` | OAuth, auth checks, identity setup | `setup-guide`, `init-oauth`, `oauth-start`, `oauth-finish`, `auth-test`, `team-info`, `read-sample`, `set-me`, `resolve-me` |
| `slack_read.py` | direct reads with bot token | `users`, `channels`, `channel-history [--on YYYY-MM-DD]`, `thread` |
| `slack_search.py` | search with user token | `search <keywords> [--from ...] [--in ...] [--to-me] [--after ...] [--days ...] [--limit N]` |
| `slack_common.py` | shared implementation | import-only; do not call as CLI |

`slack_read.py`의 `--channel`은 채널 ID(`C...`) 또는 공개 채널 이름을 받는다. 이름이면 `conversations.list`로 ID를 찾는다. MEMORY.md에 별칭이 기록되어 있으면 에이전트가 거기 적힌 ID를 그대로 넘기는 편이 빠르다.

## Search Modifiers

- `--from me` or `--from @handle`: messages from a sender.
- `--in backend`: 채널 이름 그대로 Slack search `in:`에 들어간다. MEMORY.md의 별칭은 에이전트가 실제 채널 이름으로 바꿔서 넘긴다.
- `--to-me`: config.json에 저장된 내 `<@U...>` 멘션을 검색한다. Run `slack_setup.py resolve-me` first if missing.
- `--after YYYY-MM-DD`, `--before YYYY-MM-DD`, `--on YYYY-MM-DD`, or `--days N`.
- `--limit N` (최대 1000): 결과가 100건을 넘을 때 페이지를 자동으로 넘기며 최대 N건 수집한다. `--page`와 함께 쓸 수 없다. 수동 `--page` 반복 대신 항상 이것을 쓴다.
- Multiple keywords run as separate searches, then merge by `(channel_id, ts)`.
- Compact 출력은 메시지 `text`가 비어 있으면 attachment/block 본문(제목·내용·fields)을 자동으로 뽑아 보여준다. 봇 알림 채널도 대부분 `--raw` 없이 읽힌다.

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

## Ad-hoc Scripts (일회용 분석 스크립트)

집계·통계·대량 파싱처럼 기본 스크립트 범위를 넘는 요청은 `references/adhoc-scripts.md`의 임시 스크립트 작성 규칙과 예제를 따라 scratchpad에 일회용 스크립트를 만들어 처리한다.

## Limits

- 이 스킬은 **조회 전용**이다. OAuth scope가 읽기 권한뿐이라 메시지 전송·수정·삭제·리액션은 API 차원에서 불가능하며, 그런 기능을 추가하지도 않는다.
- 기본 User Token Scopes는 `search:read`, `channels:read`, `channels:history`, `groups:read`, `groups:history`다. 공개 채널과 사용자가 들어간 비공개 채널은 User token fallback으로 직접 읽을 수 있다.
- `slack_read.py channel-history` and `thread` try bot access first, then user access. If both direct reads fail, use `slack_search.py search` and rely on permalinks.
- Do not store message bodies in `MEMORY.md`; channel notes stay one line.
