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
1. 템플릿 파일 `~/.daily-work-log/daily-work-log-template.md`가 있는지 확인한다.
2. 대상 날짜를 결정한다. 기본값은 시스템 로컬 타임존 기준 오늘이며, 사용자가 "어제"나 특정 날짜, 기간을 말하면 그 날짜들을 사용한다.
3. `~/.daily-work-log/config.json`을 읽어 `references/custom-setting.md` 기준으로 사용자 설정을 적용하고, 로그 루트를 확정한다. 로그 루트는 아래 "출력 위치" 규칙으로 정해지지 않을 때만 이 시점에 묻는다.
4. 대상 날짜마다 서브에이전트를 하나씩 띄워 아래 "날짜별 작성 절차"를 맡긴다. 상세는 "날짜별 서브에이전트" 절을 따른다.
5. 서브에이전트 결과를 모아 아래 "완료 보고" 형식으로 기록 목록과 `impact-items` 현황을 보여주고, 뺄 항목이 있는지 묻는다.
6. 사용자가 빼거나 바꾸라고 하면 저장한 Markdown과 `final-info.json`을 고친다.

1~3번은 메인 에이전트가 처리한다. 사용자에게 물어야 하는 것은 모두 이 단계에서 끝낸다. 4번부터 완료 보고 전까지는 사용자에게 묻지 않는다. 판단이 애매한 항목도 일단 기록에 넣고, 완료 보고에서 사용자가 빼게 한다.

### 날짜별 작성 절차

한 날짜에 대해 아래를 순서대로 수행한다.

1. Codex/Claude 세션에서 1차 후보 JSON을 수집한다.
2. `numbered-candidates.json`을 만들어 번호와 그룹을 확정한다.
3. 표시 후보 전체(`displayed_candidates`의 1번부터 마지막 번호까지)를 기본 포함으로 `second-pass-digest.json`을 만든다.
4. `final-info.json` skeleton을 만든다.
5. LLM이 digest와 필요한 최소 근거를 확인해 skeleton의 빈 슬롯과 `impact`를 보강한다.
6. 로그 루트 아래 `YYYY/MM/YYYY-MM-DD.md`로 최종 Markdown을 저장한다.

## 날짜별 서브에이전트

날짜별 작성 절차는 세션 후보와 digest JSON이 날짜당 수백 KB라서 메인 컨텍스트에서 돌리지 않는다. 날짜가 하나여도 서브에이전트에 맡긴다.

- Claude Code에서는 Agent 도구로 날짜마다 서브에이전트를 하나씩 띄우고, `model`은 `sonnet`으로 지정한다. 날짜가 여럿이면 한 메시지에서 모두 띄워 병렬로 돌린다.
- 서브에이전트를 띄울 수 없는 환경(Codex 등)에서는 메인 에이전트가 날짜별 작성 절차를 날짜 순서대로 직접 수행한다.
- 날짜마다 중간 산출물 디렉터리가 따로라서 병렬 실행끼리 충돌하지 않는다.

서브에이전트 프롬프트에는 아래를 모두 넣는다. 서브에이전트는 이 대화를 보지 못한다.

- 이 스킬의 base directory와 `SKILL.md` 경로. "날짜별 작성 절차", "필수 Frontmatter", "최종 Markdown 구조", "참조 표기 규칙", "Impact 섹션 (opt-in)", "작성 언어", "안전 규칙" 절과 `references/collect-first-pass-candidates.md`, `references/collect-second-pass-details.md`를 읽고 따르라는 지시
- 대상 날짜, 확정된 로그 루트, 템플릿 경로
- `config.json`에서 읽은 스크립트 옵션 값(`top-limit`, `other-limit`, `include-supporting`)
- 지켜야 할 것: 사용자에게 묻지 않는다. `config.json`과 템플릿 파일을 쓰지 않는다. 그 날짜의 중간 산출물 디렉터리와 최종 Markdown 한 파일만 쓴다.
- 아래 필수 체크리스트를 그대로 옮긴 것
- 아래 반환 형식

필수 체크리스트 (서브에이전트 프롬프트에 그대로 넣는다):

1. 템플릿 파일을 먼저 읽고, 최종 Markdown을 그 구조로 쓴다.
2. 표시 후보 전체(`--selection 1-N`)로 digest를 만든다. 후보를 임의로 빼지 않는다.
3. `final-info.json`의 `selected_items`를 보강한다. `impact-items`가 있으면 `impact.findings`도 채운다. skeleton 상태로 두지 않는다. `final-info.json`은 후보 단위 그대로 둔다.
4. 최종 Markdown에서는 같은 주제의 후보를 한 항목으로 합친다. 같은 Jira 티켓의 작업, 같은 repo에서 이어진 작업, 포크 세션과 원래 세션, 추가 지시 세션과 원래 작업이 여기에 해당한다. 주제가 다르면 합치지 않는다. 한 후보는 한 항목에만 넣는다. 합친 항목은 원래 후보 번호를 모두 반환 형식에 적는다.
5. 원인 규명, 결론, 확정한 결정이 있으면 그 항목의 `요약:`과 `## Impact`의 결정사항에 남긴다. 구현 설명 속에 묻어 두지 않는다.
6. 최종 Markdown의 frontmatter 4개 필드를 채운다. `summary`는 한 문장으로 쓰고, `tags`는 나중에 검색할 핵심 키워드 10~15개로 쓴다. 둘 다 비워 두지 않는다.
7. `impact-items`가 있고 근거가 있으면 `## Impact` 섹션을 쓴다.
8. `## 한눈에 보기` 표에 합친 뒤의 모든 항목을 넣는다.
9. 모든 항목마다 `###` 섹션을 쓴다. 각 섹션에는 `요약:`과 `- 구분:`을 두고, 근거에 repo·파일·링크가 있으면 참조 슬롯(`코드 경로`, `관련 파일`, `관련 링크`)을 채운다.
10. 항목별 상세(맥락, 진행 과정, 판단 근거, 남은 일)를 자유 형식 영역에 쓰고, `<!-- 이 아래는 자유 형식 -->` 주석 라인은 지운다.
11. 항목이 많아도 위 단계를 줄이거나 생략하지 않는다.

서브에이전트 반환 형식:

```text
date: YYYY-MM-DD
saved: <최종 Markdown 절대 경로 | none>
items:
- <후보 번호, 합쳤으면 쉼표로 모두> | <top|other, 섞이면 top> | <구분> | <제목> | <한 줄 요약>
impact:
- <name>: <근거 건수>
checks:
- template: <done | skipped>
- final_info_impact: <done | n/a | skipped>
- item_sections: <### 항목 수>/<items 수>
- reference_slots: <참조 슬롯이 있는 항목 수>/<items 수>
- free_form_detail: <done | skipped>
notes: <근거가 약한 항목, 실패한 단계, 참조 슬롯이 없는 항목과 그 이유. 없으면 none>
```

메인 에이전트는 `checks`를 확인한다. `skipped`가 있거나 `item_sections`의 두 수가 다르면, 그 날짜의 서브에이전트를 한 번 다시 띄운다. 이때 빠진 항목을 프롬프트에 적고, 이미 저장된 Markdown과 `final-info.json`을 보완하게 한다. 다시 돌려도 빠지면 완료 보고에 그 날짜와 빠진 항목을 한 줄로 알린다. `reference_slots`가 작은 것은 근거에 repo·파일이 없을 수 있으므로 다시 돌리는 조건이 아니다.

그 날짜에 표시 후보가 하나도 없으면 Markdown을 만들지 않고 `saved: none`과 `items:` 빈 목록을 돌려준다. 메인 에이전트는 이 반환값만으로 완료 보고를 만들고, 중간 산출물 JSON을 다시 읽지 않는다.

## 대상 날짜 규칙

- 사용자가 날짜를 말하지 않으면 시스템 로컬 타임존 기준 오늘을 대상 날짜로 삼는다.
- "어제", "지난 금요일", `2026-07-02`처럼 날짜를 지정하면 그 날짜를 대상 날짜로 삼는다.
- "지난주", "10월 1일~3일"처럼 기간을 말하면 그 기간의 각 날짜를 대상 날짜로 삼는다.
- 세션 타임스탬프는 로컬 타임존으로 변환한 뒤 대상 날짜와 비교한다. Codex 세션은 UTC 저장 디렉터리 경계를 고려해 대상 날짜의 전날, 당일, 다음날 디렉터리를 함께 검사한다.

## 스크립트 실행 기준

스크립트 예시는 항상 스킬 하네스가 제공하는 `Base directory for this skill` 값을 `<skill-base-dir>`로 두고 실행한다. 특정 프로젝트 CWD나 이 저장소 상대 경로를 가정하지 않는다.

## 템플릿 위치

업무 기록 템플릿 위치:

```text
~/.daily-work-log/daily-work-log-template.md
```

업무 기록 초안을 쓰기 전에 이 파일이 있는지 먼저 확인한다. 파일이 없으면 `references/how-to-set-template.md`를 읽고, 사용자와 대화하며 템플릿을 만든 뒤 일일 업무 기록 작성을 진행한다.

## 1차 후보 수집

Codex/Claude 세션에서 업무 기록 후보를 찾을 때는 원시 JSONL을 LLM이 직접 읽지 않는다. 먼저 `references/collect-first-pass-candidates.md`를 읽고, Codex와 Claude 전용 수집 스크립트로 `work_units`가 포함된 압축 후보 카드 JSON을 만든다.

기본 저장 위치:

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/
```

이 날짜 디렉터리 아래에 해당 날짜의 1차 후보, 번호 후보, 2차 상세 탐색, 최종 정보 JSON 같은 중간 산출물을 모두 모은다. 파일명으로 단계와 역할을 구분한다.

예:

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/
├── codex-candidates.json
├── claude-candidates.json
├── numbered-candidates.json
├── second-pass-digest.json
└── final-info.json
```

2차 상세 탐색 전에는 반드시 `scripts/build_numbered_candidates.py`로 `numbered-candidates.json`을 만든다. 완료 보고에서 보여주는 번호는 이 파일의 `displayed_candidates[].number`를 그대로 사용한다. 이후 사용자가 "4,5"처럼 뺄 번호를 말하면, 대화 중 임의로 다시 번호를 매기지 말고 저장된 `numbered-candidates.json`을 기준으로 해석한다.

## 완료 보고

모든 날짜의 서브에이전트가 끝난 뒤 한 번만 보고하고, 이 보고에서 뺄 항목과 `impact-items` 변경을 함께 묻는다. 보고는 사람이 훑어 읽는 짧은 보고서다.

형식 규칙:

- 첫 줄은 무엇을 어디에 몇 건 기록했는지 말하는 한 문장이다. 별도 요약 블록을 두지 않는다.
- 기록 목록은 날짜마다 `### ✅ YYYY-MM-DD 기록한 작업 내용` 소제목을 하나씩 두고, 그 아래 저장 경로 한 줄과 표를 둔다. 날짜가 여럿이면 번호는 날짜마다 따로이므로, 사용자는 "10-01 3번"처럼 날짜와 번호로 뺄 항목을 말한다. `Impact` 표의 결과 열은 "10-01 2건, 10-02 없음"처럼 날짜별로 쓴다. 기록이 없는 날짜는 한 줄로 알린다.
- 소제목은 날짜별 `### ✅ YYYY-MM-DD 기록한 작업 내용`, `### 🎯 Impact`, `### ⚙️ 설정`만 쓴다. 소제목 앞 이모지는 이 세 가지로 고정하고, 각 소제목의 첫 문장이 그 섹션의 결론이 되게 한다.
- 기록 목록은 표로 쓴다. `#` 열에는 `numbered-candidates.json`의 후보 번호를 그대로 쓰고, 합친 항목은 `3, 11, 12`처럼 모두 쓴다. 셀은 짧은 명사구로 끝내고, 단서는 표 밖 한 줄로 뺀다.
- 본문은 `~한다` 단정 서술체로 쓰고, 마지막 질문 한 줄만 존댓말로 쓴다.
- 소제목 이모지 외에는 볼드, 이모지, 구분선으로 꾸미지 않는다. 중요한 것은 앞에 둬서 드러낸다.
- 기타 후보(`list_section: other`)처럼 근거가 약한 항목이 있으면 표 아래 한 문장으로 번호를 짚는다. 없으면 쓰지 않는다.

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
| 후보 수 | 하루에 기록할 최대 작업 수 | 상위 15 + 기타 5 |
| 보조 세션 포함 | subagent·sidechain 세션도 후보로 볼지 | 포함 안 함 |
| 검색 결과 수 | 검색 모드에서 보여줄 최대 건수 | 20건 |
| 로그 저장 위치 | 최종 Markdown을 저장할 폴더 | `~/work-log` |

뺄 번호나 바꿀 Impact 항목이 있으면 알려주세요. 없으면 이대로 마칩니다.
```

`impact-items`가 없거나 빈 배열이면 `Impact` 섹션은 "등록된 항목이 없다." 한 문장과 기능 소개 한 문장만 쓴다.

`⚙️ 설정` 섹션은 매번 위 예시의 문장과 표를 그대로 쓴다. 예시 열에는 현재 `config.json` 값이 있으면 그 값을 넣고, 없으면 위 기본값을 쓴다. 바꿀 수 있는 값의 전체 목록과 예시는 `references/custom-setting.md`에 있다. 사용자가 설정 변경을 요청하면 그 문서의 "설정을 바꾸는 방법"을 따른다.

사용자 답변 처리:

- 합친 항목의 번호를 모두 받으면 그 항목 전체를 지운다. 일부 번호만 받으면 그 후보에서 온 내용만 항목에서 덜어 낸다.
- 뺄 번호를 받으면 최종 Markdown에서 그 항목의 `## 한눈에 보기` 표 행, `###` 항목, 자유 형식 상세, `## Impact`의 관련 근거를 지우고, `tags`와 `summary`를 남은 항목 기준으로 다시 맞춘다. `final-info.json`의 `selected_candidates`와 `selected_items`에서도 같은 항목을 지운다.
- `impact-items` 추가 요청에는 `name`과 `description`이 모두 필요하다. `description`이 없으면 "이 항목은 어떤 근거를 찾으면 되나요?"처럼 짧게 되물어 채운다.
- 수정 요청은 언급된 필드(`name` 또는 `description`)만 바꾸고, 삭제는 `name`으로 지정한다. `config.json`의 다른 필드는 유지한다.
- 뺄 항목 반영은 메인 에이전트가 저장된 Markdown과 `final-info.json`을 직접 고친다.
- `impact-items`가 바뀌면 메인 에이전트가 `config.json`을 갱신한 뒤, 날짜마다 `sonnet` 서브에이전트를 띄워 `second-pass-digest.json`(필요하면 원본 세션 work unit)을 다시 확인하고 `final-info.json`의 `impact`와 최종 Markdown의 `## Impact`만 새 목록 기준으로 다시 채우게 한다. 서브에이전트를 띄울 수 없으면 메인 에이전트가 직접 한다.
- 고친 뒤에는 바뀐 내용만 한두 줄로 알린다. 전체 보고를 반복하지 않는다.
- "없음", "그대로"처럼 변경이 없으면 추가 질문 없이 마친다.

## 2차 상세 탐색

1차 후보 중 표시 후보 전체를 기준으로 다시 상세 탐색한다. 이때 원시 JSONL을 최종 Markdown에 직접 복사하지 않고, `references/collect-second-pass-details.md` 기준으로 최종 정보 JSON을 만든다.

기본 흐름 (`N`은 `displayed_candidates`의 마지막 번호):

```bash
python3 <skill-base-dir>/scripts/build_second_pass_digest.py --date YYYY-MM-DD --selection 1-N
python3 <skill-base-dir>/scripts/build_final_info_skeleton.py --date YYYY-MM-DD
```

`second-pass-digest.json`은 선택 번호가 가리키는 work unit, session file, 관련 경로만 압축한 중간 자료다. `final-info.json`은 이 skeleton을 LLM이 검토하고 보강해서 완성한다. 스크립트 출력은 확정 문장이 아니라 토큰 절약용 구조화 근거이며, 최종 작성 전에는 LLM이 사실/추정/민감정보를 다시 확인한다.

최종 정보 JSON은 기본적으로 아래 경로에 둔다.

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/final-info.json
```

최종 Markdown에 들어갈 근거는 긴 원문 발췌보다 파일 경로 모음을 우선한다. 경로는 세션 파일, 사용자가 만든 계획/메모 문서, 확인한 코드 경로처럼 나중에 다시 찾아볼 수 있는 참조로 남긴다.

기록에 포함한 후보 목록은 별도 파일로 만들지 않고, `final-info.json`의 최상위 `selected_candidates` 배열에 함께 기록한다.

## 필수 Frontmatter

모든 일일 업무 기록은 아래 frontmatter 구조를 유지해야 한다.

```yaml
---
date: YYYY-MM-DD
type: daily-work-log
summary: ""
tags: []
---
```

이 네 가지 frontmatter 필드는 필수다. 제거하거나, 이름을 바꾸거나, 다른 스키마로 대체하지 않는다.

`type`은 문서 종류를 제한적으로 식별하는 필드다. 허용값은 `daily-work-log`, `decision-record`, `trouble-shooting`, `learning-note` 네 가지만 사용한다. 이 스킬이 작성하는 일일 업무 기록의 `type` 값은 `daily-work-log`로 둔다. 일일 업무 기록을 모아보거나 필터링하는 용도는 `tags`가 아니라 `type: daily-work-log`를 기준으로 한다.

`tags`는 검색 키워드 필드다. 템플릿이나 초기 초안에는 `tags: []`를 둘 수 있지만, 최종 저장본에서는 문서 작성을 완료한 뒤 "나중에 이 문서를 검색한다면 어떤 키워드로 찾을까?"를 기준으로 에이전트가 판단해 핵심 키워드 10~15개로 작성한다. 태그 값은 고정 목록으로 제한하지 않으며, `daily-work-log`를 의무적으로 넣지 않는다.

## 최종 Markdown 구조

이 문서는 에이전트가 한 번 작성하면 끝나는 문서다. 이후에는 사람이 다시 읽거나 에이전트가 검색하므로, 위쪽은 빠르게 훑을 수 있는 요약, 아래쪽은 자유 형식 상세라는 2단 구조를 유지한다.

frontmatter 바로 아래에는 `# YYYY-MM-DD 업무 기록` 제목을 둔다.

`~/.daily-work-log/config.json`의 `impact-items` 배열에 값이 하나라도 있으면, 템플릿 파일 내용과 무관하게 제목 바로 아래·`## 한눈에 보기`보다 위에 `## Impact` 섹션을 추가한다. 상세 규칙은 아래 "Impact 섹션" 절을 따른다.

첫 본문 섹션은 반드시 `## 한눈에 보기`로 시작한다. 이 섹션에는 선택된 작업 목록을 자유 형식으로 요약한 표를 둔다.

```markdown
| 구분 | 제목 | 요약 |
|---|---|---|
```

`## 한눈에 보기` 아래에는 별도의 `## 작업 요약` 섹션을 만들지 않는다. 표 바로 다음에 각 선택 항목을 `### 항목 제목`으로 이어서 작성한다.

각 `###` 항목은 요약이 중심이며, 아래 순서를 따른다.

1. `요약:` — **필수**. `###` 제목 바로 아래에 둔다. 무엇을 왜 했고 어떻게 판단했는지, 나중에 이 항목만 읽어도 기억을 복원할 수 있게 쓴다.
2. `- 구분:` — 분석/문제해결/결정 같은 대표 성격 하나.
3. 참조 목록 — `코드 경로`, `관련 파일`, `관련 링크` 슬롯 중 필요한 것만 사용한다. 표기는 아래 "참조 표기 규칙"을 따르고, 2-depth list까지 허용한다.

맥락, 진행/확인, 판단/배운 점, 결론, 남은 일 같은 상세 소제목은 필수가 아니며 `###` 항목 안에 고정 슬롯으로 넣지 않는다. 상세 내용이 필요하면 초안 작성 중에는 `<!-- 이 아래는 자유 형식 -->` 마커 아래에 작성한다.

```markdown
### API 응답 정책 정리

요약:
- `order-api`의 응답 정책과 예외 흐름을 확인하고 일지에 남길 수준으로 정리했다.

- 구분: 분석
- 코드 경로
  - `order-api` git repository
- 관련 파일
  - `order-api` `OrderController.java`, `ErrorResponse.java`
  - /Users/hsryuuu/dev/personal/example-project/_inbox/api-response-plan.md
- 관련 링크
  - API design note(응답 정책 참고): https://example.com/api-design
```

템플릿 맨 아래에는 반드시 아래 주석 마커를 둔다. 이 마커는 템플릿/초안 작성 단계에서 요약 영역과 자유 형식 상세 영역을 구분하기 위한 작업용 경계다. 마커 위쪽 `###` 항목들은 최대한 요약으로 유지하고, 각 항목의 상세 내용(맥락, 진행 과정, 판단 근거, 배운 점, 남은 일 등)은 에이전트가 이 마커 아래에 자유 형식으로 작성한다. 사용자가 그날의 맥락에 맞춰 직접 덧붙이는 메모도 이 아래에 둔다. 단, 최종 Markdown 저장본에서는 `<!-- 이 아래는 자유 형식 -->` 주석 라인을 제거하고, 그 아래에 작성한 상세 내용만 일반 본문으로 남긴다.

```markdown
<!-- 이 아래는 자유 형식 -->
```

## 참조 표기 규칙

참조는 "나중에 다시 찾을 수 있는 최소 표기"를 기준으로 세 종류로 구분한다.

- **git repo로 관리되는 소스코드**: repo 이름만으로 식별할 수 있으므로 full path를 쓰지 않는다. 코드 경로는 `` `repo-name` git repository ``, 파일은 `` `repo-name` `FileName.java` `` 형태로 짧게 쓴다.
- **로컬 전용 파일**: git이나 온라인 어디에도 없어서 local path 없이는 다시 찾을 수 없는 파일만 절대 경로(full path)로 쓴다.
- **인터넷 링크**: `링크 명(요약): URL` 형태로 쓴다.

repo 이름, 파일명, 명령어, 코드 식별자, 설정 키 같은 기술 식별자는 본문에서도 백틱(`인라인 코드`)을 적극 활용한다.

Claude/Codex 세션 파일(`~/.claude/projects/...`, `~/.codex/sessions/...`)은 언제든 캐시 정리하듯 삭제될 수 있는 파일이므로, 최종 Markdown에 세션/근거 참조로 남기지 않는다. 세션 경로는 `final-info.json` 같은 중간 산출물까지만 유지한다.

## Impact 섹션 (opt-in)

`~/.daily-work-log/config.json`의 `impact-items`는 사용자가 매번 최종 Markdown 맨 위에서 바로 확인하고 싶은 항목을 직접 정의하는 객체 배열이다. 각 객체는 `name`(섹션에 쓸 라벨)과 `description`(이 라벨에 해당하는 근거가 무엇인지 LLM이 판단할 기준)을 가진다. 예:

```json
[
  {"name": "개발 완료", "description": "개발 완료로 보이는 것"},
  {"name": "TODO", "description": "완결되지 않은것으로 보이는 것"}
]
```

- opt-in이다. `impact-items`가 없거나 빈 배열이면 `## Impact`를 만들지 않고 기존 동작과 완전히 동일하게 작성한다. `log_root`와 달리 값이 없다고 물어보지 않는다. 사용자가 먼저 언급하거나 설정을 요청할 때만 config에 저장한다.
- `impact-items`에 값이 하나라도 있으면 `## Impact`를 제목 바로 아래·`## 한눈에 보기`보다 위에 넣는다. 이 위치와 존재 여부는 사용자의 템플릿 파일 내용과 무관하게 항상 이 규칙을 따른다.
- 섹션 안 라벨과 순서는 `impact-items` 배열의 `name`과 순서를 그대로 사용한다. 각 라벨은 `- **{name}**` 형태로 굵게 표시한다. 최종 Markdown에는 `description`을 그대로 노출하지 않는다 — `description`은 2차 탐색에서 LLM이 근거를 판단하는 기준으로만 쓴다.
- 그날 어떤 선택 항목에서도 근거를 찾지 못한 라벨은 생략한다. 빈 그룹을 만들지 않는다. 모든 라벨이 비면 `## Impact` 섹션 자체를 생략한다.
- 근거가 repo에 종속된 항목(예: PR/MR 기록, git branch)은 repo별로 묶어서 표기한다. 표기 방식은 위 "참조 표기 규칙"을 그대로 따른다(repo 이름은 short-form, 로컬 전용 파일만 full path).
- 추출은 1차/2차 수집 스크립트에 새 정규식 신호를 추가하지 않는다. 2차 상세 탐색에서 LLM이 선택 후보의 원문을 읽으며 각 `impact-items` 항목의 `description`을 기준으로 해당 근거가 있는지 함께 확인해서 채운다. 근거가 없으면 지어내지 않고 빈 채로 둔다.
- 인증정보, 고객 식별자, 회사 소스코드 원문을 그대로 옮기지 않는 안전 규칙은 `## Impact`에도 동일하게 적용된다.

예시:

```markdown
## Impact

- **Jira Ticket**
  - PROJ-1234, PROJ-1250
- **PR/MR 기록**
  - `order-api`: `feature/PROJ-1234-refund` → PR #482 (merged)
  - `payment-api`: `fix/PROJ-1250-timeout` → MR !210 (open)
- **최종 개발 결정 사항**
  - API 응답 정책은 기존 구조를 유지하고 예외 흐름만 추가하기로 결정함
```

## 작성 언어

일일 업무 기록 본문은 기본적으로 한글로 작성한다. 다만 frontmatter key, 고정 `type` 값, `tags`, 파일 경로, 명령어, 코드 식별자, 기술 용어처럼 영어가 더 자연스럽거나 관례적인 항목은 영어를 유지한다.

## 출력 위치

최종 Markdown은 사용자가 지정한 **로그 루트** 아래에 `YYYY/MM/YYYY-MM-DD.md` 형태로 저장한다. 로그 루트는 연도 폴더(`2026/`, `2027/` 등)가 바로 생기는 폴더다.

```text
<log-root>/YYYY/MM/YYYY-MM-DD.md
```

경로 해석 규칙:

- 사용자가 이번 대화에서 로그 루트를 명시하면 그 경로를 사용하고 `~/.daily-work-log/config.json`의 `log_root`에 저장한다.
- 사용자가 경로를 명시하지 않았고 `~/.daily-work-log/config.json`에 `log_root`가 있으면 그 값을 재사용한다. 이때 재사용한 경로를 한 줄로 알린다.
- 사용자가 경로를 명시하지 않았고 config도 없으면 1차 수집을 시작하기 전에 로그 루트를 질문하고, 확정된 뒤 `config.json`에 저장한다. 수집 이후에는 끝까지 묻지 않고 진행해야 하므로 이 질문을 저장 직전까지 미루지 않는다.
- 사용자가 `/Users/.../work-log 여기로 해줘`, `/Users/.../work-log에 저장해줘`처럼 특정 저장 폴더를 지정하면 그 폴더를 로그 루트로 본다. 예: `/Users/hsryuuu/dev/personal/work-log/2026/07/2026-07-02.md`
- 사용자가 `/Users/.../personal 이 아래에 만들어줘`처럼 상위 폴더만 주고 그 아래에 만들라고 하면 `<지정 폴더>/daily-work-log`를 로그 루트로 만든다. 예: `/Users/hsryuuu/dev/personal/daily-work-log/2026/07/2026-07-02.md`
- 사용자의 표현만으로 "지정 경로 자체가 로그 루트인지"와 "`daily-work-log/`를 새로 만들 상위 폴더인지"가 모호하면 1차 수집을 시작하기 전에 반드시 한 문장으로 확인 질문을 한다.
- 사용자가 명시한 저장 폴더 뒤에 `daily-work-log/`를 임의로 한 번 더 붙이지 않는다.

`config.json`에 둘 수 있는 키(`log_root`, `impact-items`, 수집·검색 한도)와 예시는 `references/custom-setting.md`에 있다. 모든 키는 선택이며, `impact-items`의 `## Impact` 섹션 규칙은 위 "Impact 섹션 (opt-in)" 절을 따른다.

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

- 인증 정보, 원본 private log, 고객 식별자, 회사 소스코드를 업무 기록에 그대로 복사하지 않는다.
- 근거 자료는 사용자의 업무 기록 언어로 요약한다.
- 현재 workspace 밖에 파일을 생성하거나 덮어쓸 때는 먼저 사용자 승인을 받는다.
- 예외: 이 스킬의 중간 산출물, cache, template, `config.json`은 `~/.daily-work-log/` 아래 쓰기가 사전 승인된 것으로 본다. 최종 Markdown 로그는 위 출력 위치 규칙에 따라 로그 루트가 확정된 뒤에만 쓴다.
