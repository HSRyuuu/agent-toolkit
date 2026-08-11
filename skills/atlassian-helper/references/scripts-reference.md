# Atlassian Helper Scripts Reference

Use this file for Jira issue / Confluence page reads, or when combining
scripts freely. 쓰기(생성·수정·삭제)는 `write-guide.md`를 읽는다.

## Common Pattern

1. Read `~/.config/atlassian-helper/MEMORY.md` first if it exists (프로젝트/
   스페이스 별칭, 자주 쓰는 JQL/CQL).
2. 자연어 요청을 전용 커맨드로 매핑한다: 내 티켓 → `mine`, 작업 회고 →
   `worked`, 기한 → `due`, 키워드 → `text`, 문서 검색 → `confluence.py search`.
   전용 커맨드로 안 되는 조건만 `search`에 raw JQL을 쓴다.
3. 건수만 필요하면 `count`. 이슈를 내려받아 세지 않는다.
4. 상태/프로젝트/스페이스 이름이 불확실하면 `projects`/`statuses`/`spaces`로
   실제 이름을 먼저 확인한다 (JQL/CQL은 이름이 정확해야 한다).
5. 출력 첫 줄의 `# jql: ...` / `# cql: ...`은 실제 실행된 쿼리다. 결과가
   이상하면 이 줄로 조건을 검증한다.
6. `-`로 시작하는 값은 `--updated-from=-7d`처럼 반드시 `=`로 붙인다.
7. Update `MEMORY.md` when an investigation confirms a reusable alias or query.

## Scripts

| Script | Use For | Key Commands |
| --- | --- | --- |
| `atlassian_setup.py` | Credential setup and checks | `init-keys`, `auth-test`, `search-test`, `confluence-test`, `profiles` |
| `jira.py` | Jira issues (read + write) | `search`, `mine`, `worked`, `due`, `text`, `count`, `issue`, `projects`, `statuses`, `transitions`, `create`, `comment`, `edit`, `transition`, `delete`, `comment-edit`, `comment-delete` |
| `confluence.py` | Confluence pages (read + write) | `search`, `page`, `spaces`, `create`, `update`, `delete`, `comment` |
| `atlassian_common.py` | Shared implementation | import-only; do not call as CLI |

## Command Selection

| Need | Command |
| --- | --- |
| 내 티켓 (기간/상태/프로젝트 필터) | `jira.py mine` |
| 지난 N일/특정 기간에 작업한 것 (과거 담당 포함) | `jira.py worked --days N` 또는 `--from/--to` |
| 기한 임박·연체 티켓 | `jira.py due --within N` |
| 키워드로 티켓 찾기 (제목/본문/코멘트) | `jira.py text "<키워드>"` |
| 복잡한 조건, 전용 커맨드 밖의 필드 | `jira.py search '<JQL>'` |
| "몇 건이야?" | `jira.py count '<JQL>'` |
| 이슈 하나 자세히 (설명/코멘트) | `jira.py issue ABC-123 --comments 5` |
| 프로젝트 키 목록 | `jira.py projects` (선택: `--query 이름`) |
| 프로젝트의 상태 이름들 | `jira.py statuses --project ABC` |
| 컨플루언스 문서 검색 | `confluence.py search "<키워드>" --space DEV` |
| 내가 쓴 문서 목록 | `confluence.py search --mine` |
| 문서 하나 읽기 (+코멘트) | `confluence.py page <id> --comments 5` |
| 스페이스 키 목록 | `confluence.py spaces` (선택: `--query 이름`) |
| 티켓/문서 만들기·고치기·지우기 | `write-guide.md` 참조 |

## Common Flags (mine / worked / due / text)

- `--project ABC` (반복 가능), `--status "In Progress"` (반복 가능),
  `--type Bug`, `--label backend`, `--assignee <email|accountId>`
- `--unresolved` — 미해결만 (`resolution = EMPTY`)
- `--and "<JQL 조각>"` — 전용 커맨드에 임의 조건 추가 (예: `--and "sprint in openSprints()"`)
- `--order "due ASC"` — 정렬 변경 (기본 `updated DESC`, `due`는 `due ASC`)
- `--limit N` (기본 20, 최대 100), `--next-page <token>`, `--raw`, `--tz`

## Jira Examples

내 진행 중 티켓:

```bash
python3 "<SKILL_DIR>/scripts/jira.py" mine --status "In Progress" --unresolved
```

이번 주 / 지난 7일 내 티켓 업데이트 (기간 검색):

```bash
python3 "<SKILL_DIR>/scripts/jira.py" mine --updated-from="startOfWeek()"
python3 "<SKILL_DIR>/scripts/jira.py" mine --updated-from=-7d --project ABC
```

지난 2주 동안 작업한 내용 (담당했다가 넘긴 티켓 포함):

```bash
python3 "<SKILL_DIR>/scripts/jira.py" worked --days 14
python3 "<SKILL_DIR>/scripts/jira.py" worked --from="2026-06-01" --to="2026-06-30"
```

기한이 7일 안 남았거나 이미 지난 내 티켓 (마감 임박 순):

```bash
python3 "<SKILL_DIR>/scripts/jira.py" due --within 7
python3 "<SKILL_DIR>/scripts/jira.py" due --within 3 --anyone --project ABC
```

키워드로 티켓 찾기 / raw JQL과 건수 / 이슈 상세:

```bash
python3 "<SKILL_DIR>/scripts/jira.py" text "결제 오류" --project ABC
python3 "<SKILL_DIR>/scripts/jira.py" search 'project = ABC AND sprint in openSprints() ORDER BY rank'
python3 "<SKILL_DIR>/scripts/jira.py" count 'project = ABC AND status = Done AND resolved >= -30d'
python3 "<SKILL_DIR>/scripts/jira.py" issue ABC-123 --comments 5
```

프로젝트/상태 이름 탐색:

```bash
python3 "<SKILL_DIR>/scripts/jira.py" projects --query 백엔드
python3 "<SKILL_DIR>/scripts/jira.py" statuses --project ABC
```

## Confluence Examples

문서 검색 (검색어 없이 쓰려면 `--space`/`--title`/`--mine` 중 하나는 필요):

```bash
python3 "<SKILL_DIR>/scripts/confluence.py" search "결제 오류" --space DEV
python3 "<SKILL_DIR>/scripts/confluence.py" search --mine --limit 10
python3 "<SKILL_DIR>/scripts/confluence.py" search --title "회의록" --updated-from "2026-07-01"
```

문서 읽기 (본문은 storage XHTML을 평문으로 변환, 기본 4000자):

```bash
python3 "<SKILL_DIR>/scripts/confluence.py" page 1234567890 --comments 3
python3 "<SKILL_DIR>/scripts/confluence.py" page 1234567890 --storage   # 원본 XHTML
```

스페이스 목록:

```bash
python3 "<SKILL_DIR>/scripts/confluence.py" spaces --query 개발
```

## Output

Compact issue output is one issue per block; the first line echoes the JQL:

```text
# jql: assignee = currentUser() AND ... ORDER BY updated DESC

ABC-123  [In Progress]  Bug/High  due=2026-07-20(D-5)
  로그인 실패 시 에러 메시지 개선
  assignee=홍길동 updated=2026-07-14 10:03 labels=backend
```

`due=`에는 D-day 마커가 붙는다: `(D-5)` 5일 남음, `(D-DAY)` 오늘,
`(OVERDUE 2d)` 2일 연체. `issue`는 상세 블록 + `## description`(ADF를 평문으로
변환, 기본 800자) + `## comments`(각 코멘트에 `[id=...]`가 붙는다 —
`comment-edit`/`comment-delete`에 그대로 쓴다). `count`는 근사치 숫자 하나를
출력한다. 결과가 잘리면 마지막에 `(more results available; rerun with
--next-page <token>)`이 붙는다 — `--limit`을 넓히지 말고 토큰으로 페이지를
넘긴다.

Confluence 검색은 페이지 한 건당 `<id>  [스페이스]  제목  updated=...` + 발췌
한 줄이다. 쓰기 명령은 결과 키/ID와 URL 한 줄을 출력한다. 스크립트는 에러
메시지에서 자격증명을 마스킹하며 설정된 token을 출력하지 않는다.

## Limits

- `--limit`: 1–100 (API 페이지 상한), 기본 20 (profile `default_limit`).
- `count`는 근사치다 (Jira approximate-count API). 정확한 건수가 필요한 감사
  용도라면 페이지를 끝까지 세어야 함을 사용자에게 알린다.
- `worked`: `--days`와 `--from`은 배타. 둘 다 없으면 최근 14일.
- `due --within N`: 오늘부터 N일 뒤까지 + 연체 포함. `--include-done`을 주지
  않으면 미해결만.
- `text` / CQL `text ~`: 형태소 기반이라 부분 문자열이 아니라 단어 단위로
  매칭된다. 결과가 비면 키워드를 짧게 나눠 다시 시도한다.
- 시간 값: JQL은 `-7d`, `startOfWeek()`, `"2026-07-01"` 모두 가능. CQL
  `lastmodified`는 `"2026-07-01"` 같은 날짜 문자열을 쓴다.
- Confluence 페이지 ID는 숫자다. URL의 `/pages/<id>/` 부분이거나 검색 출력의
  첫 열이다.
