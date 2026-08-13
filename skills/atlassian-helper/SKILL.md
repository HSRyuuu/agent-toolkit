---
name: atlassian-helper
description: >
  Use when the user asks to set up Atlassian (Jira/Confluence) API credentials,
  find their own tickets by period or status (내 티켓), look up tickets by
  keyword (티켓 찾아줘), list tickets due soon or overdue (기한 임박, 마감,
  연체), review what they worked on over a period (지난 2주 작업한 내용), read
  an issue's detail or comments by key (ABC-123), run raw JQL or count issues,
  create a ticket or comment (티켓 만들어줘, 코멘트 달아줘), edit, transition,
  or delete their own ticket, search, read, create, update, and delete
  Confluence pages (컨플루언스 문서 찾아줘, 위키 페이지 만들어줘, 페이지
  수정해줘), or upload/replace an image or attachment on a page or issue
  (이미지 올려줘, 첨부 파일 업로드, 이미지 바꿔줘/교체해줘, 스크린샷 첨부).
  Triggers: "지라", "Jira", "컨플루언스", "Confluence", "위키", "JQL", "CQL",
  "첨부", "attachment", and in Atlassian context: "기억해", "기억해줘",
  "memory", "MEMORY".
---

# Atlassian Helper

This skill reads and writes Jira Cloud issues and Confluence Cloud pages
through the Atlassian REST API, avoiding MCP and returning compact,
pre-trimmed output. One credential set (site + email + API token) covers both
products.

Keep this file as the router. For any real task, first read
`~/.config/atlassian-helper/MEMORY.md` if it exists and honor saved project
aliases, JQL/CQL fragments, and preferences. Then read only the routed
reference file(s), and call the Python scripts from this skill's `scripts/`
directory. Always use the absolute installed skill directory (`<SKILL_DIR>` in
the reference files) when running scripts or showing commands to the user.

## Identity

- 모든 사용자 안내는 한글로 한다.
- Atlassian site와 email은 설정 단계에서 채팅으로 직접 물어봐 받는다. API token과
  config 내용은 채팅에 붙여넣으라고 요구하지 않는다. token은
  `atlassian_setup.py init-keys`의 터미널 대화형 입력으로만 받는다.
- 설정 확인을 별도 사전 단계로 만들지 않는다. 요청받은 작업의 스크립트를 바로
  실행하고, 설정 파일/인증 오류가 나왔을 때 `references/setup-guide.md`를 읽어
  안내한다.
- 설정 안내는 한 응답에 한 단계만 진행한다. 사용자의 완료 확인과 에이전트
  검증 뒤 다음 단계로 넘어간다.

## Safety Model

| 작업 | 분류 | 게이트 |
| --- | --- | --- |
| 조회 (search, issue, page, count …) | 안전 | 없음 |
| 생성 (issue create, comment, page create, 새 첨부 attach) | 안전 | 실행 전 대상/내용을 사용자에게 한 줄로 확인 |
| 수정 (issue edit, transition, comment-edit, page update, `attach --replace`) | 위험 | **작성자 == 본인**일 때만 실행 |
| 삭제 (issue delete, comment-delete, page delete) | 위험 | **작성자 == 본인** + `--yes` |

작성자 확인은 스크립트가 API로 직접 검사하고, 작성자를 못 읽으면 fail-closed로
중단한다. 우회 플래그는 없다 — 검사 실패를 다른 경로(직접 curl, MCP 등)로 돌아
가지 않고, 작성자가 다르다는 사실과 대안(코멘트 남기기, 작성자에게 요청)을
안내한다. 삭제는 되돌릴 수 없으니 대상 키/ID와 제목을 보여주고 확인을 받은
뒤에만 `--yes`를 붙인다. 판정 필드와 거절 문구는 `references/write-guide.md`.

## Routing

| Request | Read First | Main Scripts |
| --- | --- | --- |
| First setup, missing config, API token, 401/403 auth error | `references/setup-guide.md` | `atlassian_setup.py` |
| 내 티켓 (기간/상태/프로젝트 필터) | `references/scripts-reference.md` | `jira.py mine` |
| 지난 N일/이번 주 작업한 내용 | `references/scripts-reference.md` | `jira.py worked` |
| 기한 임박/연체 티켓 (마감 얼마 안 남은) | `references/scripts-reference.md` | `jira.py due` |
| 키워드로 티켓 찾기 ("~~ 티켓 찾아줘") | `references/scripts-reference.md` | `jira.py text` |
| 이슈 상세, 코멘트 보기 (ABC-123) | `references/scripts-reference.md` | `jira.py issue` |
| 복잡한 조건, 직접 JQL 조합 | `references/jql-patterns.md` | `jira.py search`, `count` |
| 티켓/코멘트 생성 | `references/write-guide.md` | `jira.py create`, `comment` |
| 티켓 수정/상태 변경/삭제 | `references/write-guide.md` | `jira.py edit`, `transition`, `delete` |
| 컨플루언스 문서 검색/읽기 | `references/scripts-reference.md` | `confluence.py search`, `page` |
| 컨플루언스 문서 작성/수정/삭제 | `references/write-guide.md` | `confluence.py create`, `update`, `delete` |
| 이미지·첨부 업로드/교체 (페이지 이미지 바꿔줘, 스크린샷 첨부) | `references/write-guide.md` | `confluence.py attach`, `attachments`, `jira.py attach` |
| 프로젝트/상태/스페이스 이름 탐색 | `references/scripts-reference.md` | `jira.py projects`, `statuses`, `confluence.py spaces` |

## Local Files

`~/.config/atlassian-helper/` contains two local files:

- `config.json` - Atlassian profiles (site, email, API token, cached identity).
  Scripts only read/write it.
- `MEMORY.md` - Agent-managed Markdown for project/space aliases, people,
  frequently used JQL/CQL fragments, and workflow preferences.

The config directory should be `700`; `config.json` and `MEMORY.md` should be
`600`. Never store API tokens, issue/page bodies, customer data, or secrets in
`MEMORY.md`. 이전 이름(`~/.config/jira-helper/`)으로 설정한 사용자는 그 디렉터리를
그대로 계속 쓴다 — 스크립트가 자동으로 fallback한다.

## Scripts

- `atlassian_setup.py`: `init-keys`, `auth-test`, `search-test`,
  `confluence-test`, `profiles`
- `jira.py`: 읽기 `search`, `mine`, `worked`, `due`, `text`, `count`, `issue`,
  `projects`, `statuses`, `transitions` / 쓰기 `create`, `comment`, `attach`,
  `edit`, `transition`, `delete`, `comment-edit`, `comment-delete`
- `confluence.py`: 읽기 `search`, `page`, `spaces`, `attachments` / 쓰기
  `create`, `update`, `delete`, `comment`, `attach`
- `atlassian_common.py`: import-only shared implementation

자연어 요청은 가능한 한 전용 커맨드(`mine`/`worked`/`due`/`text`)로 매핑하고,
전용 커맨드로 표현이 안 되는 조건만 `search`에 raw JQL을 조합한다 (JQL/CQL 작성은
`references/jql-patterns.md` 참조). 건수만 필요하면 이슈를 내려받지 말고
`count`를 쓴다. 상태/프로젝트/스페이스 이름이 불확실하면
`projects`/`statuses`/`spaces`로 먼저 확인한다. `-`로 시작하는 값은 반드시
`--updated-from=-7d`처럼 `=`로 붙인다.

## Memory

`MEMORY.md`에는 다음 세션이 다시 발견하지 않아도 되는 접근 지식만 남긴다 —
프로젝트/스페이스 별칭, 팀/사람, 자주 쓰는 JQL/CQL, 조회 선호. API token,
이슈/문서 본문 원문, 고객 데이터는 어떤 경우에도 저장하지 않는다.

저장을 요청받았거나(“기억해”, “저장해둬”, “memory”) 탐색 중 재사용 가능한
사실을 새로 확인했으면 `references/memory.md`를 읽고 그대로 따른다.

## Rules

- 쓰기 명령을 실행하기 전에 무엇을 어디에 쓰는지 한 줄로 요약해 사용자에게
  확인받는다. 사용자가 이미 구체적으로 지시했다면 그대로 실행한다.
- Default to bounded reads: limit 20, 기간 필터를 붙일 수 있으면 붙인다.
- 결과가 잘리면 `--limit`을 넓히기 전에 `--next-page <token>`으로 페이지를
  넘긴다 (출력 마지막의 안내 참조).
- Prefer compact output. Use `--raw` only when the compact output hides a
  field you truly need, and keep the limit small.
- Treat API errors as setup signals. On missing config or 401/403, route to
  `references/setup-guide.md`.
- Do not write issue/page contents into repo files. Only write durable
  user-approved access hints to `MEMORY.md`.
