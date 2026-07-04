---
name: daily-work-log
description: 개인 daily work log 템플릿을 만들거나, 직군과 무관하게 하루 업무 기록 Markdown을 작성·준비할 때 사용한다. 트리거 - "daily work log", "오늘 작업 기록", "퇴근 전 회고", "업무 일지 템플릿", "daily-work-log template".
---

# Daily Work Log

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
python3 skills/daily-work-log/scripts/build_second_pass_digest.py --date YYYY-MM-DD --selection 4,5,6
python3 skills/daily-work-log/scripts/build_final_info_skeleton.py --date YYYY-MM-DD
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
### Config Server / Spring profile 구조 조사

요약:
- `metatrip-api`가 Spring Cloud Config Server와 Spring profile로 설정을 로딩하는 구조를 조사하고 개념 문서화 관점으로 정리했다.

- 구분: 분석
- 코드 경로
  - `metatrip-api` git repository
- 관련 파일
  - `metatrip-api` `application.yml`, `RedisConfigurer.java`
  - /Users/hsryuuu/dev/personal/tbz-hsryuuu/_inbox/aws-secrets-manager-config-plan.md
- 관련 링크
  - Spring Cloud Config 공식 문서: https://docs.spring.io/spring-cloud-config/
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

- 사용자가 `/Users/.../work-log 여기로 해줘`, `/Users/.../work-log에 저장해줘`처럼 특정 저장 폴더를 지정하면 그 폴더를 로그 루트로 본다. 예: `/Users/hsryuuu/dev/personal/work-log/2026/07/2026-07-02.md`
- 사용자가 `/Users/.../personal 이 아래에 만들어줘`처럼 상위 폴더만 주고 그 아래에 만들라고 하면 `<지정 폴더>/daily-work-log`를 로그 루트로 만든다. 예: `/Users/hsryuuu/dev/personal/daily-work-log/2026/07/2026-07-02.md`
- 사용자의 표현만으로 "지정 경로 자체가 로그 루트인지"와 "`daily-work-log/`를 새로 만들 상위 폴더인지"가 모호하면 최종 Markdown을 쓰기 전에 반드시 한 문장으로 확인 질문을 한다.
- 사용자가 명시한 저장 폴더 뒤에 `daily-work-log/`를 임의로 한 번 더 붙이지 않는다.

도구 설정, low-level JSON, cache, template 파일은 `~/.daily-work-log/` 아래에 둔다. 최종 Markdown 로그만 위 규칙에 따라 사용자가 지정한 로그 루트 아래에 둔다.

## 안전 규칙

- 인증 정보, 원본 private log, 고객 식별자, 회사 소스코드를 업무 기록에 그대로 복사하지 않는다.
- 근거 자료는 사용자의 업무 기록 언어로 요약한다.
- 현재 workspace 밖에 파일을 생성하거나 덮어쓸 때는 먼저 사용자 승인을 받는다.
