# 임시 스크립트 작성 규칙 (Ad-hoc Scripts)

집계·통계·대량 파싱처럼 기본 스크립트 범위를 넘는 요청(예: "어제 알림 전부 에러 종류별로 세줘")은 일회용 Python 스크립트를 만들어 처리한다. 이 파일의 규칙과 예제를 따른다. 예제는 few-shot이다: 새 스크립트는 아래 좋은 예제의 구조(subprocess 래퍼 → 방어적 파싱 → 컴팩트 출력)를 그대로 변형해서 만든다.

## 규칙

**위치와 수명**

- 스크립트는 **scratchpad(세션 임시 디렉토리)에만** 만든다. 스킬 디렉토리나 사용자 프로젝트에 저장하지 않는다.
- 중간 산출물(JSON 덤프 등)도 scratchpad에만 쓴다. 메시지 본문이나 토큰을 다른 곳에 파일로 남기지 않는다.

**Slack 접근 (가장 중요)**

- Slack 접근은 **반드시 이 스킬의 스크립트를 `subprocess`로 호출**해서 한다. `slack_search.py`·`slack_read.py`만 진입점이다.
- 토큰 로딩·인증·Slack API 호출을 재구현하지 않는다. `~/.config/slack-helper/config.json`을 직접 읽지 않는다. `urllib`/`requests`로 `slack.com`을 직접 호출하지 않는다.
- 조회 전용이다. 어떤 경우에도 전송·수정·삭제 동작을 넣지 않는다.

**안정성**

- `subprocess.run(...)`에는 항상 `capture_output=True, text=True, timeout=120`을 준다.
- `returncode != 0`이면 stderr를 포함해 즉시 중단한다. 자동 재시도 루프를 만들지 않는다 (실패 원인은 에이전트가 보고 판단한다).
- 페이지 순회를 직접 구현하지 않는다. 100건 초과 수집은 `--limit N`(최대 1000)이 대신한다.
- 파싱 입력은 `--jsonl`을 기본으로 쓴다: 한 줄당 `{"ts","channel","channel_name","user","user_name","text","permalink"}` JSON이고, 본문이 잘리지 않으며 attachment/block 본문도 `text`에 합쳐져 있다(`" · "` 구분).
- attachment의 세부 구조(fields 등)가 꼭 필요할 때만 `--raw`로 넘어간다. `--raw` 파싱은 방어적으로 한다: `.get(...) or` 체인으로 접근하고, 필드가 없어도 `KeyError`/`TypeError`로 죽지 않게 한다. `--limit`+`--raw` 조합의 출력은 페이지가 하나면 단일 응답 객체, 여러 개면 `{"ok": true, "responses": [...]}`다 (`payload.get("responses") or [payload]` 패턴으로 두 형태 모두 처리).

**출력**

- stdout에는 집계·요약 결과만 컴팩트하게 출력한다. 수집한 원본 메시지 전체를 덤프하지 않는다 (에이전트 컨텍스트 = 토큰 비용).
- 사용자에게는 스크립트 코드가 아니라 결과만 보여준다. 무엇을 했는지는 한 줄로 설명한다.

**시작 전 확인**

- 먼저 `--limit`과 compact 출력만으로 충분한지 시도한다. 스크립트 파싱이 필요하면 `--jsonl`, 원본 필드 구조까지 필요할 때만 `--raw` 순서로 올린다.
- `<SKILL_DIR>`는 설치된 스킬의 절대 경로다. cwd 기준 상대 경로를 쓰지 않는다.

## 좋은 예제

"7월 7일 알림 채널 메시지를 에러 제목별로 집계" 요청을 처리하는 일회용 스크립트:

```python
#!/usr/bin/env python3
"""2026-07-07 #example-alerts 알림을 에러 제목별로 집계한다. (일회용, scratchpad 전용)"""
import json
import subprocess
import sys
from collections import Counter

SEARCH = "<SKILL_DIR>/scripts/slack_search.py"  # 설치된 스킬의 절대 경로로 치환


def run_search_jsonl(*args: str) -> list[dict]:
    result = subprocess.run(
        ["python3", SEARCH, "search", *args, "--jsonl"],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        sys.exit(f"slack_search 실패: {result.stderr.strip()}")
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def chunks_of(record: dict) -> list[str]:
    # --jsonl의 text는 [메시지 본문, attachment 제목, attachment 본문, ...]이 " · "로 합쳐진 값이다.
    return [c.strip() for c in str(record.get("text") or "").split(" · ") if c.strip()] or ["(내용 없음)"]


records = run_search_jsonl("--in", "example-alerts", "--on", "2026-07-07", "--limit", "300")
chunk_lists = [chunks_of(record) for record in records]

# 알림 봇은 본문 text가 매번 같은 고정 문구(예: "This is a fallback message.")이고
# 실제 제목은 attachment에 있는 경우가 많다. 첫 조각이 사실상 전부 동일하면 다음 조각을 제목으로 쓴다.
first_counts = Counter(chunks[0] for chunks in chunk_lists)
generic_firsts = {value for value, count in first_counts.items() if count >= max(3, len(chunk_lists) * 0.8)}


def alert_title(chunks: list[str]) -> str:
    picked = chunks[1] if chunks[0] in generic_firsts and len(chunks) > 1 else chunks[0]
    return picked.splitlines()[0]


counter: Counter[str] = Counter(alert_title(chunks) for chunks in chunk_lists)

total = sum(counter.values())
print(f"총 {total}건")
for title, count in counter.most_common(20):
    print(f"{count:4d}  {title}")
```

이 예제가 지키는 것: 진입점은 `slack_search.py` 하나, 페이지 순회는 `--limit`에 위임, timeout·returncode 처리, `--jsonl` 한 줄 단위 파싱, `or` 체인 방어 파싱, 고정 문구 본문 뒤에 제목이 오는 알림 봇 처리, 출력은 집계 결과만.

## 잘못된 예제 (이렇게 만들지 않는다)

```python
# ❌ 토큰을 직접 읽고 Slack API를 직접 호출 — 인증 재구현 금지
config = json.load(open(os.path.expanduser("~/.config/slack-helper/config.json")))
requests.get("https://slack.com/api/search.messages", headers={"Authorization": f"Bearer {config[...]}"})

# ❌ 페이지 무한 루프 직접 구현 — --limit이 대신한다, 종료 조건 실수로 API를 무한 호출할 수 있다
page = 1
while True:
    out = subprocess.run(["python3", SEARCH, "search", "alert", "--page", str(page)], ...)
    page += 1

# ❌ timeout·에러 처리 없음 — 스크립트가 조용히 멈추거나 빈 결과로 잘못된 집계를 낸다
out = subprocess.check_output(["python3", SEARCH, "search", "alert", "--raw"])

# ❌ 방어 없는 파싱 — attachments가 없는 메시지에서 즉시 죽는다
title = match["attachments"][0]["title"]

# ❌ 원본 전체 덤프 — 수백 건의 메시지 JSON이 그대로 컨텍스트에 들어온다
print(json.dumps(payload, ensure_ascii=False, indent=2))
```

## 체크리스트

스크립트를 실행하기 전에 확인한다.

- [ ] scratchpad 안에 만들었다
- [ ] Slack 접근이 전부 `slack_search.py`/`slack_read.py` subprocess 호출이다
- [ ] `timeout`과 `returncode` 처리가 있다
- [ ] 페이지 순회를 직접 만들지 않았다 (`--limit` 사용)
- [ ] 파싱 입력으로 `--jsonl`을 먼저 검토했다 (`--raw`는 원본 구조가 필요할 때만)
- [ ] 필드 누락에도 죽지 않는다
- [ ] stdout이 집계·요약만 출력한다
