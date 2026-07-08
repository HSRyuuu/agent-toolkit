# Daily Review

Use for "데일리 리뷰", "특정 일자 하루 정리", "어제/그날 내 슬랙 정리", or "7월 3일에 뭐 했지".

특정 일자의 Slack 대화·스레드 기록을 **나 중심으로** 분석해 하루를 정리한다. 내가 보낸 메시지와 나를 멘션한 메시지가 축이고, 채널 대화는 "내가 뭘 했는지"의 맥락을 보강하는 용도로만 쓴다.

## Steps

1. Read `~/.config/slack-helper/MEMORY.md` for preferences and important channels (없으면 건너뛴다).

2. Primary collection (axis): my messages and my mentions on the target date. 채널·DM 모두 포함된다.

```bash
python3 "<SKILL_DIR>/scripts/slack_search.py" search --from me --on 2026-07-03 --count 50
python3 "<SKILL_DIR>/scripts/slack_search.py" search --to-me --on 2026-07-03 --count 50
```

3. Open only threads with real conversation from step 2.

```bash
python3 "<SKILL_DIR>/scripts/slack_read.py" thread --channel backend --ts 1717243200.000100
```

4. Secondary collection (enrichment): read the day's channel history **only for topics and channels that appeared in step 2**. 나와 무관한 채널 잡담은 리포트에 넣지 않는다.

```bash
python3 "<SKILL_DIR>/scripts/slack_read.py" channel-history --channel backend --on 2026-07-03 --limit 100
```

5. Write the report following the Output Shape below.

## Rules

- 일자를 지정하지 않으면 오늘 날짜로 진행하되, 리포트 첫 줄에 대상 일자를 명시해 사용자가 바로잡을 수 있게 한다.
- `--on`의 날짜 경계는 로컬 타임존 자정 기준이다.
- 직접 읽기가 `not_in_channel`로 실패하면 검색 결과와 permalink로 대체한다.
- 검색 인덱싱 지연이나 DM 검색 범위 제한으로 일부 기록이 누락될 수 있다. 리포트 말미에 이 한계를 한 줄로 표시한다.
- 기본 출력은 채팅 응답이다. 사용자가 요청할 때만 markdown 파일로 저장하고, 저장 위치는 그때 확인한다.

## Output Shape

리포트는 한글로, 위에서부터 이 순서를 따른다. 내용이 없는 섹션은 생략하지 말고 "없음"으로 표기한다.

1. **간단 요약** — 그 날을 2~4문장으로 요약 (최상단).
2. **주요 대화 리뷰** — 채널·스레드별로 내가 참여한 대화의 핵심 내용.
3. **알아둬야 할 것** — 공지, 의사결정, 일정 등 기억할 정보.
4. **TODO** — 대화에서 드러난 내가 할 일.
5. **팔로업 필요 스레드** — 답장하지 않은 멘션, 응답 대기 중인 요청.

각 항목에는 근거가 되는 채널명과 permalink를 붙인다.
