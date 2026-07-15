# JQL Patterns

Use this file when composing raw JQL for `jira_search.py search` / `count`,
or when adding conditions via `--and`.

## Core Filters

| Need | JQL Fragment |
| --- | --- |
| 내 티켓 | `assignee = currentUser()` |
| 내가 만든 티켓 | `reporter = currentUser()` |
| 과거에 내가 담당했던 티켓 | `assignee WAS currentUser()` |
| 프로젝트 | `project = ABC` / `project IN (ABC, XYZ)` |
| 상태 | `status = "In Progress"` / `status IN ("To Do", "In Progress")` |
| 상태 카테고리 (보드 열과 무관하게) | `statusCategory = "In Progress"` (`"To Do"`, `"Done"`) |
| 이슈 타입 | `issuetype = Bug` |
| 라벨 | `labels = backend` |
| 미해결 | `resolution = EMPTY` |
| 특정 기간 업데이트 | `updated >= -7d AND updated <= endOfDay()` |
| 특정 기간 생성 | `created >= "2026-07-01" AND created < "2026-08-01"` |
| 기한 | `due <= 7d AND due IS NOT EMPTY` |
| 최근 해결 | `resolved >= -30d` |
| 텍스트 검색 | `text ~ "결제 오류"` (제목만: `summary ~ "..."`) |
| 스프린트 | `sprint in openSprints()` / `sprint in closedSprints()` |
| 에픽 하위 | `parent = ABC-100` |
| 특정 사람 | `assignee = "hong@example.com"` (email 또는 accountId) |

## Time Values

- 상대값: `-7d`, `-4h`, `-2w` (따옴표 없이)
- 함수: `startOfDay()`, `startOfWeek()`, `startOfMonth()`, `endOfDay("-1")`,
  `now()` — 괄호 안 인자로 오프셋 가능
- 날짜: `"2026-07-01"` 또는 `"2026-07-01 14:00"` (따옴표 필수)
- `updated >= startOfWeek()`의 "주 시작"은 Jira 사이트 설정을 따른다 (보통 월요일).

## Status Changes (작업 이력 추적)

| Need | JQL Fragment |
| --- | --- |
| 이 기간에 내가 상태를 바꾼 | `status CHANGED BY currentUser() AFTER -14d` |
| 이 기간에 Done으로 간 | `status CHANGED TO Done AFTER startOfWeek()` |
| 특정 기간 담당자였던 | `assignee WAS currentUser() DURING ("2026-06-01", "2026-06-30")` |

## Ordering

- 기본: `ORDER BY updated DESC`
- 기한 정렬: `ORDER BY due ASC` (EMPTY due는 뒤로 간다)
- 보드 순서: `ORDER BY rank`
- 우선순위: `ORDER BY priority DESC, updated DESC`

## Heuristics

- 상태 이름은 사이트마다 다르다. 확신이 없으면 `statuses --project ABC`로
  실제 이름을 확인하거나 `statusCategory`를 쓴다.
- `text ~`는 단어 단위 매칭이다. 긴 문장보다 핵심 단어 1~2개가 잘 잡힌다.
- 값에 공백/한글이 있으면 항상 따옴표로 감싼다. 스크립트의 전용 플래그
  (`--status` 등)는 자동으로 처리한다.
- 사람을 email로 못 찾으면 accountId가 필요할 수 있다. 이슈 `--raw` 출력의
  `assignee.accountId`에서 확인해 MEMORY에 저장해둔다.
- 잘못된 필드/상태 이름은 HTTP 400으로 돌아온다. 에러 본문의 메시지를 읽고
  이름을 교정한다 — 설정 문제(401/403)와 혼동하지 않는다.

## Memory Candidates

When a search confirms a reusable pattern, save only the access hint:

```markdown
- 스프린트 리뷰 — project = ABC AND sprint in openSprints() AND assignee = currentUser()
- 백엔드 버그 큐 — project = ABC AND issuetype = Bug AND statusCategory != Done
```

Do not save issue bodies or private data.
