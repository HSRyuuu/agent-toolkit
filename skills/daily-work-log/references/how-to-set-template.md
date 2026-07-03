# Daily Work Log 템플릿 설정 방법

먼저 아래 템플릿 파일이 있는지 확인한다.

```text
~/.daily-work-log/daily-work-log-template.md
```

파일이 있으면 일일 업무 기록 템플릿으로 사용한다. 파일이 없으면 사용자와 대화하며 템플릿을 만든 뒤, 승인받은 최종 템플릿을 정확히 이 경로에 작성한다.

## 필수 Frontmatter

템플릿은 반드시 아래 네 가지 필드로 시작해야 한다. 이 필드는 필수이며 선택 사항이 아니다.

```yaml
---
date: YYYY-MM-DD
type: daily-work-log
summary: ""
tags:
  - daily-work-log
---
```

작성 규칙:

- `date`: 대상 업무 기록 일자로 `YYYY-MM-DD`를 교체한다. 해당 일자의 로그에 고정하며 ISO 형식을 사용한다.
- `type`: 일일 업무 기록에서는 `daily-work-log`를 사용한다. daily 템플릿에서는 이 값을 바꾸지 않는다.
- `summary`: 로그 내용이 정해진 뒤 한 문장의 한글 요약을 작성한다. 검색하기 쉽고, 사실 기반이며, 짧게 쓴다. 자연스러운 경우 영어 기술 용어를 허용한다.
- `tags`: 항상 `daily-work-log`를 포함한다. 사용자가 개인 태그 체계를 요청한 경우에만 태그를 추가하며, 추가 태그는 lowercase kebab-case를 사용한다.

## 작성 언어

일일 업무 기록 본문은 기본적으로 한글로 작성한다. 다만 frontmatter key, `daily-work-log` 같은 고정 값, tag, 명령어, 파일 경로, 코드 식별자, 제품명, 기술 용어는 영어가 더 자연스러우면 영어를 유지한다.

## 기본 템플릿

사용자가 기본값을 원하면 아래의 최소 템플릿을 사용한다.

```markdown
---
date: YYYY-MM-DD
type: daily-work-log
summary: ""
tags:
  - daily-work-log
---

# YYYY-MM-DD 업무 기록

## 요약

-

## 작업

-

## 후속 작업

- [ ]
```

## 템플릿 생성 대화 흐름

템플릿이 없을 때:

1. `~/.daily-work-log/daily-work-log-template.md`가 없다고 설명한다.
2. 기본 템플릿을 보여준다.
3. 필수 frontmatter 아래의 섹션을 추가, 삭제, 이름 변경할지 묻는다.
4. 날짜 placeholder 규칙을 제외하고 필수 frontmatter는 그대로 유지한다.
5. 필요하면 `~/.daily-work-log/`를 만들고, 승인받은 템플릿을 `daily-work-log-template.md`에 작성한다.

사용자 승인 없이 템플릿 파일을 작성하지 않는다.
