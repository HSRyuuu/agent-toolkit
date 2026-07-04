---
name: daily-work-log
description: Codex/Claude 세션 로그와 선택적 KB 기록을 마이닝해 개인 daily work log Markdown을 작성·준비하거나 템플릿을 만들고, 이미 저장된 업무 기록을 날짜·태그·키워드로 검색할 때 사용한다. 트리거 - "daily work log", "오늘 한 일 정리", "어제 한 일 정리", "오늘 작업 기록", "퇴근 전 회고", "업무 일지 템플릿", "daily-work-log template", "업무 기록 검색", "지난주에 뭐 했지", "그때 그 작업 언제 했더라", "work log 찾아줘".
---

# Daily Work Log

이 스킬은 두 가지 모드를 제공한다.

- **작성 모드**: 세션 로그/KB를 마이닝해 그날의 업무 기록 Markdown을 만든다. 아래 "워크플로우 개요"를 따른다.
- **검색 모드**: 이미 저장된 업무 기록을 날짜·태그·키워드로 찾는다. "지난주에 뭐 했지", "그 작업 언제 했더라", "kafka 관련 기록 찾아줘"처럼 과거 기록을 묻는 요청이면 작성 워크플로우로 들어가지 말고 아래 "저장된 로그 검색" 섹션을 따른다.

## 워크플로우 개요

1. 템플릿 파일 `~/.daily-work-log/daily-work-log-template.md`가 있는지 확인한다.
2. 대상 날짜를 결정한다. 기본값은 시스템 로컬 타임존 기준 오늘이며, 사용자가 "어제"나 특정 날짜를 말하면 그 날짜를 사용한다.
3. Codex/Claude 세션과 선택적 KB 기록에서 1차 후보 JSON을 수집한다.
4. `numbered-candidates.json`을 만들어 사용자에게 보여줄 번호와 그룹을 확정한다.
5. 사용자가 포함할 후보 번호를 선택한다.
6. 선택 후보만 기준으로 `second-pass-digest.json`을 만든다.
7. `final-info.json` skeleton을 만든다.
8. LLM이 digest와 필요한 최소 근거를 확인해 skeleton의 빈 슬롯을 보강한다.
9. 사용자에게 최종 요약과 저장 위치를 확인한다.
10. 승인된 로그 루트 아래 `YYYY/MM/YYYY-MM-DD.md`로 최종 Markdown을 저장한다.

## 대상 날짜 규칙

- 사용자가 날짜를 말하지 않으면 시스템 로컬 타임존 기준 오늘을 대상 날짜로 삼는다.
- "어제", "지난 금요일", `2026-07-02`처럼 날짜를 지정하면 그 날짜를 대상 날짜로 삼는다.
- 세션·KB log 타임스탬프는 로컬 타임존으로 변환한 뒤 대상 날짜와 비교한다. Codex 세션은 UTC 저장 디렉터리 경계를 고려해 대상 날짜의 전날, 당일, 다음날 디렉터리를 함께 검사한다.

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

KB가 설정되어 있으면 같은 1차 수집 단계에서 KB 후보도 선택적으로 수집한다. KB root가 설정되어 있지 않거나, KB를 찾을 수 없거나, 해당 날짜 후보가 없으면 사용자에게 언급하지 않고 생략한다.

기본 저장 위치:

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/
```

이 날짜 디렉터리 아래에 해당 날짜의 1차 후보, 사용자 선택, 2차 상세 탐색, 최종 정보 JSON 같은 중간 산출물을 모두 모은다. 파일명으로 단계와 역할을 구분한다.

예:

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/
├── codex-candidates.json
├── claude-candidates.json
├── kb-candidates.json
├── numbered-candidates.json
├── second-pass-digest.json
└── final-info.json
```

1차 후보를 사용자에게 보여주기 전에는 반드시 `scripts/build_numbered_candidates.py`로 `numbered-candidates.json`을 만든다. 사용자에게 보여주는 번호는 이 파일의 `displayed_candidates[].number`를 그대로 사용한다. 이후 사용자가 "4,5,6"처럼 선택하면, 대화 중 임의로 다시 번호를 매기지 말고 저장된 `numbered-candidates.json`을 기준으로 해석한다.

## 2차 상세 탐색

사용자가 1차 후보에서 포함할 항목을 고르면, 선택된 후보만 기준으로 다시 상세 탐색한다. 이때 원시 JSONL이나 KB 원문을 최종 Markdown에 직접 복사하지 않고, `references/collect-second-pass-details.md` 기준으로 최종 정보 JSON을 만든다.

선택 이후 기본 흐름:

```bash
python3 <skill-base-dir>/scripts/build_second_pass_digest.py --date YYYY-MM-DD --selection 4,5,6
python3 <skill-base-dir>/scripts/build_final_info_skeleton.py --date YYYY-MM-DD
```

`second-pass-digest.json`은 선택 번호가 가리키는 work unit, session file, KB 문서, 관련 경로만 압축한 중간 자료다. `final-info.json`은 이 skeleton을 LLM이 검토하고 보강해서 완성한다. 스크립트 출력은 확정 문장이 아니라 토큰 절약용 구조화 근거이며, 최종 작성 전에는 LLM이 사실/추정/민감정보를 다시 확인한다.

최종 정보 JSON은 기본적으로 아래 경로에 둔다.

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/final-info.json
```

최종 Markdown에 들어갈 근거는 긴 원문 발췌보다 파일 경로 모음을 우선한다. 경로는 세션 파일, KB 문서, 사용자가 만든 계획/메모 문서, 확인한 코드 경로처럼 나중에 다시 찾아볼 수 있는 참조로 남긴다.

사용자가 고른 후보 목록은 별도 파일로 만들지 않고, `final-info.json`의 최상위 `selected_candidates` 배열에 함께 기록한다.

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

`tags`는 검색 키워드 필드다. 템플릿이나 초기 초안에는 `tags: []`를 둘 수 있지만, 최종 저장본에서는 문서 작성을 완료한 뒤 "나중에 이 문서를 검색한다면 어떤 키워드로 찾을까?"를 기준으로 에이전트가 판단해 충분히 작성한다. 태그 값은 고정 목록으로 제한하지 않으며, `daily-work-log`를 의무적으로 넣지 않는다.

## 최종 Markdown 구조

이 문서는 에이전트가 한 번 작성하면 끝나는 문서다. 이후에는 사람이 다시 읽거나 에이전트가 검색하므로, 위쪽은 빠르게 훑을 수 있는 요약, 아래쪽은 자유 형식 상세라는 2단 구조를 유지한다.

frontmatter 바로 아래에는 `# YYYY-MM-DD 업무 기록` 제목을 둔다.

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
- 사용자가 경로를 명시하지 않았고 config도 없으면 최종 Markdown을 쓰기 전에 로그 루트를 질문하고, 확정된 뒤 `config.json`에 저장한다.
- 사용자가 `/Users/.../work-log 여기로 해줘`, `/Users/.../work-log에 저장해줘`처럼 특정 저장 폴더를 지정하면 그 폴더를 로그 루트로 본다. 예: `/Users/hsryuuu/dev/personal/work-log/2026/07/2026-07-02.md`
- 사용자가 `/Users/.../personal 이 아래에 만들어줘`처럼 상위 폴더만 주고 그 아래에 만들라고 하면 `<지정 폴더>/daily-work-log`를 로그 루트로 만든다. 예: `/Users/hsryuuu/dev/personal/daily-work-log/2026/07/2026-07-02.md`
- 사용자의 표현만으로 "지정 경로 자체가 로그 루트인지"와 "`daily-work-log/`를 새로 만들 상위 폴더인지"가 모호하면 최종 Markdown을 쓰기 전에 반드시 한 문장으로 확인 질문을 한다.
- 사용자가 명시한 저장 폴더 뒤에 `daily-work-log/`를 임의로 한 번 더 붙이지 않는다.

config 파일 스키마:

```json
{"log_root": "/absolute/path"}
```

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
- 결과는 날짜 내림차순이며 기본 20건으로 제한된다(`--limit 0`이면 전체).
- 사용자가 말한 키워드로 결과가 없으면 동의어·영문/한글 표기 변형으로 1~2회 재시도한 뒤, 그래도 없으면 "기록 없음"을 그대로 말한다.
- 스크립트 결과에서 유력한 파일만 골라 Read로 열어 답한다. 검색 중에는 어떤 로그 파일도 수정하지 않는다.
- 답변에는 근거가 된 로그 파일 경로를 함께 남긴다.

## 안전 규칙

- 인증 정보, 원본 private log, 고객 식별자, 회사 소스코드를 업무 기록에 그대로 복사하지 않는다.
- 근거 자료는 사용자의 업무 기록 언어로 요약한다.
- 현재 workspace 밖에 파일을 생성하거나 덮어쓸 때는 먼저 사용자 승인을 받는다.
- 예외: 이 스킬의 중간 산출물, cache, template, `config.json`은 `~/.daily-work-log/` 아래 쓰기가 사전 승인된 것으로 본다. 최종 Markdown 로그는 위 출력 위치 규칙에 따라 로그 루트가 확정된 뒤에만 쓴다.
