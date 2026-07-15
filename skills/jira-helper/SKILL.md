---
name: jira-helper
description: >
  Use when the user asks to set up Jira API credentials, search Jira issues,
  find their own tickets by period or status (내 티켓, 이번 주 내 이슈), look up
  tickets by keyword (~~ 티켓 찾아줘), list tickets due soon or overdue
  (기한 임박, 마감, 연체), review what they worked on over a period (지난 2주
  작업한 내용), read an issue's detail or comments by key (ABC-123), run raw
  JQL, count issues, or manage local Jira access memory. Triggers: "지라",
  "Jira 검색", "내 티켓", "JQL", "기한 얼마 안 남은", "마감 임박", "이번
  주/지난 달 작업", "티켓 찾아줘", "이슈 상태", and in Jira context: "기억해",
  "기억해줘", "memory", "MEMORY". Do NOT use for creating, editing,
  transitioning, or deleting Jira issues — this skill is read-only.
---

# Jira Helper

This skill explores Jira Cloud issues through the Jira REST API, avoiding MCP
and returning compact, pre-trimmed output. It is strictly read-only toward
Jira: use it for local credential setup, my-ticket period/status searches,
keyword searches, due-date triage, worked-on reviews, issue detail/comment
reads, raw JQL, and maintaining the user's Jira access memory.

Keep this file as the router. For any real task, first read
`~/.config/jira-helper/MEMORY.md` if it exists and honor saved project
aliases, JQL fragments, and preferences. Then read only the routed reference
file(s), and call the Python scripts from this skill's `scripts/` directory.
Always use the absolute installed skill directory (`<SKILL_DIR>` in the
reference files) when running scripts or showing commands to the user.

## Identity

- 모든 사용자 안내는 한글로 한다.
- Jira site와 email은 설정 단계에서 채팅으로 직접 물어봐 받는다. API token과
  config 내용은 채팅에 붙여넣으라고 요구하지 않는다. token은
  `jira_setup.py init-keys`의 터미널 대화형 입력으로만 받는다.
- 설정 확인을 별도 사전 단계로 만들지 않는다. 요청받은 작업의 스크립트를 바로
  실행하고, 설정 파일/인증 오류가 나왔을 때 `references/setup-guide.md`를 읽어
  안내한다.
- 설정 안내는 한 응답에 한 단계만 진행한다. 사용자의 완료 확인과 에이전트
  검증 뒤 다음 단계로 넘어간다.

## Routing

| Request | Read First | Main Scripts |
| --- | --- | --- |
| First setup, missing config, API token, 401/403 auth error | `references/setup-guide.md` | `jira_setup.py` |
| 내 티켓 (기간/상태/프로젝트 필터) | `references/scripts-reference.md` | `jira_search.py mine` |
| 지난 N일/이번 주 작업한 내용 | `references/scripts-reference.md` | `jira_search.py worked` |
| 기한 임박/연체 티켓 (마감 얼마 안 남은) | `references/scripts-reference.md` | `jira_search.py due` |
| 키워드로 티켓 찾기 ("~~ 티켓 찾아줘") | `references/scripts-reference.md` | `jira_search.py text` |
| 이슈 상세, 코멘트 보기 (ABC-123) | `references/scripts-reference.md` | `jira_search.py issue` |
| 복잡한 조건, 직접 JQL 조합 | `references/jql-patterns.md` | `jira_search.py search`, `count` |
| 몇 건인지 세기 | `references/scripts-reference.md` | `jira_search.py count` |
| 프로젝트/상태 이름 탐색 (JQL 값을 모를 때) | `references/scripts-reference.md` | `jira_search.py projects`, `statuses` |

## Local Files

`~/.config/jira-helper/` contains two local files:

- `config.json` - Jira profiles (site, email, API token, cached identity).
  Scripts only read/write it.
- `MEMORY.md` - Agent-managed Markdown for project aliases, people, frequently
  used JQL fragments, and workflow preferences.

The config directory should be `700`; `config.json` and `MEMORY.md` should be
`600`. Never store API tokens, issue bodies, customer data, or secrets in
`MEMORY.md`.

## Scripts

- `jira_setup.py`: `init-keys`, `auth-test`, `search-test`, `profiles`
- `jira_search.py`: `search`, `mine`, `worked`, `due`, `text`, `count`,
  `issue`, `projects`, `statuses`
- `jira_common.py`: import-only shared implementation

자연어 요청은 가능한 한 전용 커맨드(`mine`/`worked`/`due`/`text`)로 매핑하고,
전용 커맨드로 표현이 안 되는 조건만 `search`에 raw JQL을 조합한다 (JQL 작성은
`references/jql-patterns.md` 참조). 건수만 필요하면 이슈를 내려받지 말고
`count`를 쓴다. 상태/프로젝트 이름이 불확실하면 `projects`/`statuses`로 먼저
확인한다. `-`로 시작하는 값은 반드시 `--updated-from=-7d`처럼 `=`로 붙인다.

## Memory

`MEMORY.md` stores durable Jira access knowledge so the next session does not
rediscover it:

- **프로젝트 별칭**: 사용자가 부르는 이름 ↔ 프로젝트 키 (예: "백엔드" → `ABC`)
- **팀/사람**: 자주 검색하는 동료의 표시 이름/이메일
- **자주 쓰는 JQL**: 재사용 가능한 JQL 조각과 용도
- **선호**: 기본 조회 범위, 기본 프로젝트, "이번 주" 기준 등

Update triggers — do not wait passively:

1. **명시 트리거**: 사용자 메시지에 "기억", "기억해", "기억해줘", "저장해둬",
   "memory", "MEMORY" 같은 단어가 나오면 메모리 요청으로 간주한다. 저장 대상이
   명확하면 묻지 말고 바로 알맞은 섹션에 추가하고 추가된 라인을 그대로
   보고한다. 모호하면 후보 1~3개를 제시하고 한 번만 묻는다. 이미 있으면 기존
   라인을 갱신하거나 "이미 저장되어 있다"고 알린다.
2. **탐색이 끝났을 때**: 조사 과정에서 새로 확인된 프로젝트 키, 별칭, 유효했던
   JQL 패턴이 있으면 마지막 응답에서 저장할지 한 문장으로 제안한다.
3. 같은 사실을 두 번째 세션에서 다시 발견했다면 즉시 저장을 제안한다.

API token, 이슈 본문 원문, 고객 데이터는 어떤 경우에도 저장하지 않는다.

```markdown
# jira-helper memory

## 프로젝트 별칭
- 백엔드 — ABC — 백엔드 팀 메인 보드

## 팀/사람
- 길동 — 홍길동 (hong@example.com)

## 자주 쓰는 JQL
- 스프린트 리뷰 — project = ABC AND sprint in openSprints() AND assignee = currentUser()

## 선호
- 기본 조회 프로젝트는 ABC
```

## Rules

- **이 스킬은 조회 전용이다.** 이슈 생성·수정·상태 변경·삭제·코멘트 작성을
  제공하지 않는다. 사용자가 쓰기 작업을 요청하면 이 스킬 범위 밖임을 안내한다.
- Default to bounded reads: limit 20, 기간 필터를 붙일 수 있으면 붙인다.
- 결과가 잘리면 `--limit`을 넓히기 전에 `--next-page <token>`으로 페이지를
  넘긴다 (출력 마지막의 안내 참조).
- Prefer compact output. Use `--raw` only when the compact output hides a
  field you truly need, and keep the limit small.
- Treat API errors as setup signals. On missing config or 401/403, route to
  `references/setup-guide.md`.
- Do not write issue contents into repo files. Only write durable
  user-approved access hints to `MEMORY.md`.
