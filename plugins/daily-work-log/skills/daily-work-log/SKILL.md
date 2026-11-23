---
name: daily-work-log
description: >
  Use when the user wants to create a personal daily work log from Codex/Claude
  sessions, set up a work-log template, or search saved work logs by
  date, tag, or keyword. Triggers: "daily work log", "오늘 한 일 정리",
  "어제 한 일 정리", "퇴근 전 회고", "지난주에 뭐 했지", "work log 찾아줘".
---

# Daily Work Log

이 스킬은 두 가지 모드를 제공한다.

- **작성 모드**: 세션 로그를 마이닝해 그날의 업무 기록 Markdown을 만든다. 아래 "워크플로우 개요"를 따른다.
- **검색 모드**: 이미 저장된 업무 기록을 날짜·태그·키워드로 찾는다. "지난주에 뭐 했지", "그 작업 언제 했더라", "kafka 관련 기록 찾아줘"처럼 과거 기록을 묻는 요청이면 작성 워크플로우로 들어가지 말고 아래 "저장된 로그 검색" 섹션을 따른다.

## 워크플로우 개요

1. 템플릿 파일 `~/.daily-work-log/daily-work-log-template.md`가 있는지 확인한다.
2. 대상 날짜를 결정한다. 기본값은 시스템 로컬 타임존 기준 오늘이며, 사용자가 "어제"나 특정 날짜, 기간을 말하면 그 날짜들을 사용한다.
3. `~/.daily-work-log/config.json`을 읽어 로그 루트를 확정한다. 로그 루트는 아래 "출력 위치" 규칙으로 정해지지 않을 때만 이 시점에 묻는다.
4. 대상 날짜마다 서브에이전트를 하나씩 띄워 `references/write-daily-log.md`의 절차를 맡긴다. 상세는 "날짜별 서브에이전트" 절을 따른다.
5. 서브에이전트 결과를 모아 아래 "완료 보고" 형식으로 기록 목록과 `impact-items` 현황을 보여주고, 뺄 항목이 있는지 묻는다.
6. 사용자가 빼거나 바꾸라고 하면 저장한 Markdown을 고친다.

1~3번은 메인 에이전트가 처리한다. 사용자에게 물어야 하는 것은 모두 이 단계에서 끝낸다. 4번부터 완료 보고 전까지는 사용자에게 묻지 않는다. 판단이 애매한 항목도 일단 기록에 넣고, 완료 보고에서 사용자가 빼게 한다.

## 날짜별 서브에이전트

하루치 근거는 수만 토큰이라서 메인 컨텍스트에서 읽지 않는다. 날짜가 하나여도 서브에이전트에 맡긴다.

- Claude Code에서는 Agent 도구로 날짜마다 서브에이전트를 하나씩 띄우고, `model`은 `sonnet`으로 지정한다. 날짜가 여럿이면 한 메시지에서 모두 띄워 병렬로 돌린다.
- 서브에이전트를 띄울 수 없는 환경(Codex 등)에서는 메인 에이전트가 `references/write-daily-log.md`를 읽고 날짜 순서대로 직접 수행한다.
- 날짜마다 중간 산출물 디렉터리가 따로라서 병렬 실행끼리 충돌하지 않는다.

서브에이전트 프롬프트에는 아래만 넣는다. 서브에이전트는 이 대화를 보지 못한다. 작성 규칙과 반환 형식은 프롬프트에 옮겨 적지 않는다.

- 이 스킬의 base directory와, `references/write-daily-log.md`를 읽고 그대로 따르라는 지시. 이 스킬의 다른 문서는 읽지 않아도 된다고 적는다.
- 대상 날짜와 확정된 로그 루트

메인 에이전트는 반환값의 `checks`를 확인한다. 아래 중 하나면 그 날짜의 서브에이전트를 한 번 다시 띄운다.

- `skipped`가 있다.
- `evidence_lines`, `candidates`, `item_sections`, `free_form_detail` 중 두 수가 다른 것이 있다.

다시 띄울 때는 빠진 것을 프롬프트에 적고, 이미 저장된 Markdown을 보완하게 한다. 수집은 다시 돌리지 않고 저장된 `evidence.md`를 읽게 한다. 다시 돌려도 빠지면 완료 보고에 그 날짜와 빠진 항목을 한 줄로 알린다. `reference_slots`가 작은 것은 근거에 repo·파일이 없을 수 있으므로 다시 돌리는 조건이 아니다.

그 날짜에 표시 후보가 하나도 없으면 서브에이전트가 `saved: none`과 빈 `items:`를 돌려준다. 메인 에이전트는 반환값만으로 완료 보고를 만들고, 중간 산출물을 다시 읽지 않는다.

## 스크립트 실행 기준

스크립트 예시는 항상 스킬 하네스가 제공하는 `Base directory for this skill` 값을 `<skill-base-dir>`로 두고 실행한다. 특정 프로젝트 CWD나 이 저장소 상대 경로를 가정하지 않는다.

## 템플릿 위치

업무 기록 템플릿 위치:

```text
~/.daily-work-log/daily-work-log-template.md
```

업무 기록 초안을 쓰기 전에 이 파일이 있는지 먼저 확인한다. 파일이 없으면 `references/how-to-set-template.md`를 읽고, 사용자와 대화하며 템플릿을 만든 뒤 일일 업무 기록 작성을 진행한다.

## 중간 산출물

원시 세션 JSONL은 LLM이 직접 읽지 않는다. `scripts/build_day_evidence.py`가 수집부터 근거 파일 생성까지 한 번에 돌린다. 날짜마다 아래 디렉터리에 중간 산출물이 모인다.

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/
├── codex-candidates.json
├── claude-candidates.json
├── numbered-candidates.json
├── second-pass-digest.json
└── evidence.md
```

에이전트가 읽는 것은 `evidence.md`다. 완료 보고의 번호는 `numbered-candidates.json`의 `displayed_candidates[].number`이고, `evidence.md`의 후보 번호와 같다. 사용자가 "4,5"처럼 뺄 번호를 말하면 대화 중 임의로 다시 번호를 매기지 말고 이 번호로 해석한다. 각 스크립트가 하는 일은 `references/collect-pipeline.md`에 있다.

## 완료 보고

모든 날짜의 서브에이전트가 끝난 뒤 한 번만 보고하고, 이 보고에서 뺄 항목과 `impact-items` 변경을 함께 묻는다. 보고는 사람이 훑어 읽는 짧은 보고서다.

형식은 아래 예시를 따른다. 예시만으로 드러나지 않는 규칙:

- 날짜가 여럿이면 날짜마다 `### ✅ YYYY-MM-DD 기록한 작업 내용` 소제목과 표를 하나씩 둔다. 번호는 날짜마다 따로이므로 사용자는 "10-01 3번"처럼 말한다. `Impact` 표의 결과 열은 "10-01 2건, 10-02 없음"처럼 날짜별로 쓰고, 기록이 없는 날짜는 한 줄로 알린다.
- `#` 열에는 `numbered-candidates.json`의 후보 번호를 그대로 쓰고, 합친 항목은 `3, 11, 12`처럼 모두 쓴다.
- 소제목 이모지(✅, 🎯, ⚙️) 외에는 볼드, 이모지, 구분선으로 꾸미지 않는다.
- 기타 후보(`list_section: other`)처럼 근거가 약한 항목이 있으면 표 아래 한 문장으로 번호를 짚는다.

예시:

```markdown
2026-07-02 업무 기록을 7건 저장했다.

### ✅ 2026-07-02 기록한 작업 내용

저장 위치: `~/work-log/2026/07/2026-07-02.md`

| # | 구분 | 제목 | 요약 |
|---|---|---|---|
| 1 | 개발 | user-module 레이어 정리 | 도메인 구조와 레이어 책임 문서화 |
| 2, 5 | 트러블슈팅 | event-worker 재처리 점검 | Kafka 연동 실패 원인 확인 |
| … | … | … | … |
| 7 | 조사 | batch-job 실행 조건 확인 | 실행 조건만 확인, 결론 없음 |

6, 7번은 근거가 약한 기타 후보다.

### 🎯 Impact

등록된 항목 2개 중 1개에서 근거를 찾아 문서 맨 위 `## Impact`에 넣었다.

| 항목 | 찾는 기준 | 결과 |
|---|---|---|
| 개발 완료 | 개발 완료로 보이는 것 | 2건 |
| TODO | 완결되지 않은 것으로 보이는 것 | 없음 |

키워드를 등록하면 Jira 티켓, PR/MR, 최종 결정처럼 매번 보고 싶은 내용을 문서 맨 위에 모아 준다. 항목은 지금 추가·수정·삭제할 수 있다.

### ⚙️ 설정

아래 항목을 바꿀 수 있다. 설정 파일은 `~/.daily-work-log/config.json`이고, 대화로 요청해도 된다.

| 항목 | 설명 | 예시 |
|---|---|---|
| Impact 항목 | 기록 맨 위 `## Impact`에 매번 모아 볼 내용 | Jira 티켓, PR/MR, TODO |
| 본문 템플릿 | 작업 항목의 참조 슬롯과 자유 형식 영역 구성 | `관련 링크` 슬롯 빼기 |
| 후보 수 | 하루에 볼 최대 세션 수 | 상위 40 + 기타 10 |
| 보조 세션 포함 | subagent·sidechain 세션도 후보로 볼지 | 포함 안 함 |
| 검색 결과 수 | 검색 모드에서 보여줄 최대 건수 | 20건 |
| 로그 저장 위치 | 최종 Markdown을 저장할 폴더 | `~/work-log` |

뺄 번호나 바꿀 Impact 항목이 있으면 알려주세요. 없으면 이대로 마칩니다.
```

`impact-items`가 없거나 빈 배열이면 `Impact` 섹션은 "등록된 항목이 없다." 한 문장과 기능 소개 한 문장만 쓴다.

`⚙️ 설정` 섹션은 매번 위 예시의 문장과 표를 그대로 쓴다. 예시 열에는 현재 `config.json` 값이 있으면 그 값을 넣고, 없으면 위 기본값을 쓴다. 바꿀 수 있는 값의 전체 목록과 예시는 `references/custom-setting.md`에 있다. 사용자가 설정 변경을 요청하면 그 문서의 "설정을 바꾸는 방법"을 따른다.

사용자 답변 처리:

- 합친 항목의 번호를 모두 받으면 그 항목 전체를 지운다. 일부 번호만 받으면 그 후보에서 온 내용만 항목에서 덜어 낸다.
- 뺄 번호를 받으면 최종 Markdown에서 그 항목의 `## 한눈에 보기` 표 행, `###` 항목, 자유 형식 상세, `## Impact`의 관련 근거를 지우고, `tags`와 `summary`를 남은 항목 기준으로 다시 맞춘다.
- `impact-items` 추가 요청에는 `name`과 `description`이 모두 필요하다. `description`이 없으면 "이 항목은 어떤 근거를 찾으면 되나요?"처럼 짧게 되물어 채운다.
- 수정 요청은 언급된 필드(`name` 또는 `description`)만 바꾸고, 삭제는 `name`으로 지정한다. `config.json`의 다른 필드는 유지한다.
- 뺄 항목 반영은 메인 에이전트가 저장된 Markdown을 직접 고친다.
- `impact-items`가 바뀌면 메인 에이전트가 `config.json`을 갱신한 뒤, 날짜마다 `sonnet` 서브에이전트를 띄운다. 서브에이전트는 `build_day_evidence.py --date YYYY-MM-DD --render-only`로 `evidence.md`를 다시 만들어 읽고, `references/write-daily-log.md`의 "Impact 섹션" 규칙대로 최종 Markdown의 `## Impact`만 다시 쓴다. 서브에이전트를 띄울 수 없으면 메인 에이전트가 직접 한다.
- 고친 뒤에는 바뀐 내용만 한두 줄로 알린다. 전체 보고를 반복하지 않는다.
- "없음", "그대로"처럼 변경이 없으면 추가 질문 없이 마친다.

## 작성 규칙

frontmatter, 본문 구조, 참조 표기, `## Impact`, 작성 언어 규칙은 `references/write-daily-log.md`가 정본이다. 메인 에이전트가 저장된 Markdown을 고칠 때도 그 문서의 규칙을 따른다.

`impact-items`는 opt-in이다. `config.json`에 없거나 빈 배열이면 `## Impact`를 만들지 않는다. `log_root`와 달리 값이 없다고 묻지 않는다. 사용자가 먼저 언급하거나 설정을 요청할 때만 `config.json`에 저장한다. 각 원소는 `name`(섹션에 쓸 라벨)과 `description`(이 라벨에 해당하는 근거를 판단할 기준)을 가진다.

```json
[
  {"name": "개발 완료", "description": "개발 완료로 보이는 것"},
  {"name": "TODO", "description": "완결되지 않은 것으로 보이는 것"}
]
```

## 출력 위치

최종 Markdown은 사용자가 지정한 **로그 루트** 아래에 `YYYY/MM/YYYY-MM-DD.md` 형태로 저장한다. 로그 루트는 연도 폴더(`2026/`, `2027/` 등)가 바로 생기는 폴더다.

```text
<log-root>/YYYY/MM/YYYY-MM-DD.md
```

경로 해석 규칙:

- 사용자가 이번 대화에서 경로를 말하면 그 폴더를 로그 루트로 쓰고 `config.json`의 `log_root`에 저장한다. 예: `/Users/me/work-log 여기로 해줘` → `/Users/me/work-log/2026/07/2026-07-02.md`. "이 아래에 만들어줘"처럼 상위 폴더만 주면 `<그 폴더>/daily-work-log`를 로그 루트로 쓴다. 둘 중 어느 뜻인지 모호하면 1차 수집 전에 한 문장으로 묻는다. 지정한 폴더 뒤에 `daily-work-log/`를 임의로 덧붙이지 않는다.
- 경로를 말하지 않았으면 `config.json`의 `log_root`를 재사용하고, 재사용한 경로를 한 줄로 알린다.
- 둘 다 없으면 1차 수집 전에 로그 루트를 묻고 `config.json`에 저장한다. 수집 이후에는 끝까지 묻지 않으므로 이 질문을 저장 직전까지 미루지 않는다.

`config.json`에 둘 수 있는 키(`log_root`, `impact-items`, 수집·검색 한도)와 예시는 `references/custom-setting.md`에 있다. 모든 키는 선택이다.

도구 설정, low-level JSON, cache, template 파일은 `~/.daily-work-log/` 아래에 둔다. 최종 Markdown 로그만 위 규칙에 따라 사용자가 지정한 로그 루트 아래에 둔다.

## 저장된 로그 검색

로그 루트 아래 최종 Markdown을 검색할 때는 파일을 하나씩 직접 읽지 말고 먼저 `scripts/search_work_logs.py`로 후보를 좁힌다. 이 스크립트는 read-only이며, frontmatter(`date`, `type`, `summary`, `tags`)와 본문 키워드를 기준으로 필터링한다.

```bash
# 날짜 범위로 찾기 (지난주에 뭐 했지)
python3 <skill-base-dir>/scripts/search_work_logs.py --since 2026-06-23 --until 2026-06-27

# 태그 + 키워드로 찾기 (kafka 작업 언제 했더라)
python3 <skill-base-dir>/scripts/search_work_logs.py --tag kafka --query "consumer lag"

# 특정 날짜, JSON 출력
python3 <skill-base-dir>/scripts/search_work_logs.py --date 2026-07-01 --json
```

동작 규칙:

- 로그 루트는 `--log-root`를 지정하지 않으면 `~/.daily-work-log/config.json`의 `log_root`를 사용한다. config에도 없으면 스크립트가 에러를 내므로, 사용자에게 로그 루트를 물어본 뒤 `--log-root`로 전달한다.
- `--tag`와 `--query`는 반복 지정할 수 있고 AND로 결합된다. `--query`는 `summary`, `tags`, 본문을 함께 검색하며, 매칭된 본문 라인을 최대 3개까지 스니펫으로 보여준다.
- 결과는 날짜 내림차순이며 기본 20건으로 제한된다(`--limit 0`이면 전체). `config.json`에 `search-limit`이 있으면 그 값을 `--limit`으로 넘긴다.
- 사용자가 말한 키워드로 결과가 없으면 동의어·영문/한글 표기 변형으로 1~2회 재시도한 뒤, 그래도 없으면 "기록 없음"을 그대로 말한다.
- 스크립트 결과에서 유력한 파일만 골라 Read로 열어 답한다. 검색 중에는 어떤 로그 파일도 수정하지 않는다.
- 답변에는 근거가 된 로그 파일 경로를 함께 남긴다.

## 안전 규칙

- 인증 정보, 원본 private log, 고객 식별자, 회사 소스코드를 업무 기록에 그대로 복사하지 않는다. 상세는 `references/write-daily-log.md` "안전 규칙"을 따른다.
- 이 스킬은 `~/.daily-work-log/`와 확정된 로그 루트 아래에만 쓴다. 두 곳에 쓸 때는 다시 묻지 않는다. 서브에이전트도 저장 전에 다시 묻지 않는다.
