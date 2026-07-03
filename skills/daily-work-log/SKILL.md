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
~/.daily-work-log/first-pass/YYYY-MM-DD/
```

## 필수 Frontmatter

모든 일일 업무 기록은 아래 frontmatter 구조를 유지해야 한다.

```yaml
---
date: YYYY-MM-DD
type: daily-work-log
summary: ""
tags:
  - daily-work-log
---
```

이 네 가지 frontmatter 필드는 필수다. 제거하거나, 이름을 바꾸거나, 다른 스키마로 대체하지 않는다.

## 작성 언어

일일 업무 기록 본문은 기본적으로 한글로 작성한다. 다만 frontmatter key, 고정 type 값, tag, 파일 경로, 명령어, 코드 식별자, 기술 용어처럼 영어가 더 자연스럽거나 관례적인 항목은 영어를 유지한다.

## 출력 위치

사용자가 설정한 journal root를 사용한다. 사람이 읽는 최종 Markdown 로그의 권장 위치:

```text
~/personal/daily-work-log/
```

기본 일일 기록 경로:

```text
<journal-root>/daily/YYYY/MM/YYYY-MM-DD.md
```

도구 설정, low-level JSON, cache, template 파일은 `~/.daily-work-log/` 아래에 둔다. 최종 Markdown 로그는 사용자의 journal root 아래에 둔다.

## 안전 규칙

- 인증 정보, 원본 private log, 고객 식별자, 회사 소스코드를 업무 기록에 그대로 복사하지 않는다.
- 근거 자료는 사용자의 업무 기록 언어로 요약한다.
- 현재 workspace 밖에 파일을 생성하거나 덮어쓸 때는 먼저 사용자 승인을 받는다.
