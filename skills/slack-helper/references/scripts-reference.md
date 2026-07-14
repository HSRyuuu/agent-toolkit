# slack-helper Scripts Reference

Use this file when a Slack request does not exactly match one of the workflow files, or when you need to combine scripts freely.

## Common Pattern

1. Read local memory first: `~/.config/slack-helper/MEMORY.md` (선호 규칙과 채널 별칭·ID가 여기 있다; 없으면 건너뛴다)
2. Search broadly with compact output: `python3 "<SKILL_DIR>/scripts/slack_search.py" search <keywords> --days 7`
3. Open only useful threads: `python3 "<SKILL_DIR>/scripts/slack_read.py" thread --permalink "<검색 결과 라인의 permalink>"` — permalink의 `p...` 숫자를 직접 ts로 바꾸지 않는다. permalink가 없으면 `--channel <id-or-name> --ts <thread_ts>`를 쓴다. (`slack_read.py` tries the bot token first, then retries with the user token when bot access fails)
4. Use `--jsonl` for ad-hoc parsing, and `--raw` only when compact/jsonl output hides a field you truly need.

## Scripts

| Script | Use For | Key Commands |
| --- | --- | --- |
| `slack_setup.py` | OAuth, auth checks, identity setup | `setup-guide`, `init-oauth`, `oauth-start`, `oauth-finish`, `auth-test`, `team-info`, `read-sample`, `doctor`, `set-me`, `resolve-me` |
| `slack_read.py` | direct reads with bot token | `users`, `channels`, `channel-history [--on YYYY-MM-DD 또는 --after/--before] [--tz ...]`, `thread [--permalink URL 또는 --channel/--ts]` |
| `slack_search.py` | search with user token | `search <keywords> [--from ...] [--in ...] [--to-me] [--after ...] [--days ...] [--limit N] [--jsonl]` |
| `slack_common.py` | shared implementation | import-only; do not call as CLI |

`slack_read.py`의 `--channel`은 채널 ID(`C...`) 또는 공개 채널 이름을 받는다. 이름이면 `conversations.list`로 ID를 찾는다. MEMORY.md에 별칭이 기록되어 있으면 에이전트가 거기 적힌 ID를 그대로 넘기는 편이 빠르다.

`channel-history`의 `--after`/`--before`는 양끝 날짜를 포함하는 범위 조회다(`--after 2026-07-01 --before 2026-07-05` = 7/1 00:00 ~ 7/5 자정 직전). `--on`과 함께 쓸 수 없고, 자정 기준 타임존은 `--tz Asia/Seoul`처럼 바꿀 수 있다(기본은 로컬). 참고로 `slack_search.py`의 `after:`/`before:`/`on:`은 Slack 계정 타임존 기준이라 경계 시간대 메시지는 서로 어긋날 수 있다.

설정·연결 문제가 의심되면 진단 조합 대신 `slack_setup.py doctor` 하나로 config/권한/토큰/scope/identity를 일괄 점검한다.

compact 출력의 작성자와 `<@U…>` 멘션은 `~/.config/slack-helper/users.json` 캐시로 자동으로 `@이름`으로 치환된다. 캐시에 없는 사용자는 조회 시 `users.info`로 최대 25명까지 자동 보강되고, 실패해도 조회 자체는 계속된다.

## Search Modifiers

- `--from me` or `--from @handle`: messages from a sender.
- `--in backend`: 채널 이름 그대로 Slack search `in:`에 들어간다. MEMORY.md의 별칭은 에이전트가 실제 채널 이름으로 바꿔서 넘긴다.
- `--to-me`: config.json에 저장된 내 `<@U...>` 멘션을 검색한다. Run `slack_setup.py resolve-me` first if missing.
- `--after YYYY-MM-DD`, `--before YYYY-MM-DD`, `--on YYYY-MM-DD`, or `--days N`.
- `--limit N` (최대 1000): 결과가 100건을 넘을 때 페이지를 자동으로 넘기며 최대 N건 수집한다. `--page`와 함께 쓸 수 없다. 수동 `--page` 반복 대신 항상 이것을 쓴다.
- `--jsonl`: 한 줄당 `{"ts","channel","channel_name","user","user_name","text","permalink"}` JSON을 출력한다(본문은 자르지 않음). 임시 분석 스크립트가 파싱할 때 `--raw` 대신 쓴다. `--raw`와 함께 쓸 수 없다.
- Multiple keywords run as separate searches, then merge by `(channel_id, ts)`.
- Compact 출력은 메시지 `text`가 비어 있으면 attachment/block 본문(제목·내용·fields)을 자동으로 뽑아 보여준다. 봇 알림 채널도 대부분 `--raw` 없이 읽힌다.

## Combination Examples

Project history:

```bash
python3 "<SKILL_DIR>/scripts/slack_search.py" search "project phoenix" decision rollout --after 2026-06-01
python3 "<SKILL_DIR>/scripts/slack_read.py" thread --permalink "https://acme.slack.com/archives/C0123456789/p1717243200000100"
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

Date-range channel read (양끝 날짜 포함):

```bash
python3 "<SKILL_DIR>/scripts/slack_read.py" channel-history --channel backend --after 2026-07-01 --before 2026-07-05 --limit 200
```

## Ad-hoc Scripts (일회용 분석 스크립트)

집계·통계·대량 파싱처럼 기본 스크립트 범위를 넘는 요청은 `references/adhoc-scripts.md`의 임시 스크립트 작성 규칙과 예제를 따라 scratchpad에 일회용 스크립트를 만들어 처리한다.

## Limits

- 이 스킬은 **조회 전용**이다. OAuth scope가 읽기 권한뿐이라 메시지 전송·수정·삭제·리액션은 API 차원에서 불가능하며, 그런 기능을 추가하지도 않는다.
- 기본 User Token Scopes는 `search:read`, `channels:read`, `channels:history`, `groups:read`, `groups:history`다. 공개 채널과 사용자가 들어간 비공개 채널은 User token fallback으로 직접 읽을 수 있다.
- `slack_read.py channel-history` and `thread` try bot access first, then user access. If both direct reads fail, use `slack_search.py search` and rely on permalinks.
- Do not store message bodies in `MEMORY.md`; channel notes stay one line.
