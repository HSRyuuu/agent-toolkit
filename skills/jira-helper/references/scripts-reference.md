# Jira Helper Scripts Reference

Use this file for Jira issue reads or when combining scripts freely.

## Common Pattern

1. Read `~/.config/jira-helper/MEMORY.md` first if it exists (프로젝트 별칭,
   자주 쓰는 JQL).
2. 자연어 요청을 전용 커맨드로 매핑한다: 내 티켓 → `mine`, 작업 회고 →
   `worked`, 기한 → `due`, 키워드 → `text`. 전용 커맨드로 안 되는 조건만
   `search`에 raw JQL을 쓴다.
3. 건수만 필요하면 `count`. 이슈를 내려받아 세지 않는다.
4. 상태/프로젝트 이름이 불확실하면 `projects`/`statuses`로 실제 이름을 먼저
   확인한다 (JQL은 이름이 정확해야 한다).
5. 출력 첫 줄의 `# jql: ...`은 실제 실행된 JQL이다. 결과가 이상하면 이 줄로
   조건을 검증한다.
6. `-`로 시작하는 값은 `--updated-from=-7d`처럼 반드시 `=`로 붙인다.
7. Update `MEMORY.md` when an investigation confirms a reusable alias or JQL.

## Scripts

| Script | Use For | Key Commands |
| --- | --- | --- |
| `jira_setup.py` | Credential setup and checks | `init-keys`, `auth-test`, `search-test`, `profiles` |
| `jira_search.py` | Read-only issue search | `search`, `mine`, `worked`, `due`, `text`, `count`, `issue`, `projects`, `statuses` |
| `jira_common.py` | Shared implementation | import-only; do not call as CLI |

## Command Selection

| Need | Command |
| --- | --- |
| 내 티켓 (기간/상태/프로젝트 필터) | `mine` |
| 지난 N일/특정 기간에 작업한 것 (과거 담당 포함) | `worked --days N` 또는 `--from/--to` |
| 기한 임박·연체 티켓 | `due --within N` |
| 키워드로 찾기 (제목/본문/코멘트) | `text "<키워드>"` |
| 복잡한 조건, 전용 커맨드 밖의 필드 | `search '<JQL>'` |
| "몇 건이야?" | `count '<JQL>'` |
| 이슈 하나 자세히 (설명/코멘트) | `issue ABC-123 --comments 5` |
| 프로젝트 키 목록 | `projects` (선택: `--query 이름`) |
| 프로젝트의 상태 이름들 | `statuses --project ABC` |

## Common Flags (mine / worked / due / text)

- `--project ABC` (반복 가능), `--status "In Progress"` (반복 가능),
  `--type Bug`, `--label backend`, `--assignee <email|accountId>`
- `--unresolved` — 미해결만 (`resolution = EMPTY`)
- `--and "<JQL 조각>"` — 전용 커맨드에 임의 조건 추가 (예: `--and "sprint in openSprints()"`)
- `--order "due ASC"` — 정렬 변경 (기본 `updated DESC`, `due`는 `due ASC`)
- `--limit N` (기본 20, 최대 100), `--next-page <token>`, `--raw`, `--tz`

## Examples

내 진행 중 티켓:

```bash
python3 "<SKILL_DIR>/scripts/jira_search.py" mine --status "In Progress" --unresolved
```

이번 주 / 지난 7일 내 티켓 업데이트 (기간 검색):

```bash
python3 "<SKILL_DIR>/scripts/jira_search.py" mine --updated-from="startOfWeek()"
python3 "<SKILL_DIR>/scripts/jira_search.py" mine --updated-from=-7d --project ABC
```

지난 2주 동안 작업한 내용 (담당했다가 넘긴 티켓 포함):

```bash
python3 "<SKILL_DIR>/scripts/jira_search.py" worked --days 14
python3 "<SKILL_DIR>/scripts/jira_search.py" worked --from="2026-06-01" --to="2026-06-30"
```

기한이 7일 안 남았거나 이미 지난 내 티켓 (마감 임박 순):

```bash
python3 "<SKILL_DIR>/scripts/jira_search.py" due --within 7
python3 "<SKILL_DIR>/scripts/jira_search.py" due --within 3 --anyone --project ABC
```

키워드로 티켓 찾기:

```bash
python3 "<SKILL_DIR>/scripts/jira_search.py" text "결제 오류" --project ABC
python3 "<SKILL_DIR>/scripts/jira_search.py" text "login timeout" --mine --status Done
```

raw JQL과 건수:

```bash
python3 "<SKILL_DIR>/scripts/jira_search.py" search 'project = ABC AND sprint in openSprints() ORDER BY rank'
python3 "<SKILL_DIR>/scripts/jira_search.py" count 'project = ABC AND status = Done AND resolved >= -30d'
```

이슈 상세 + 최근 코멘트 5건:

```bash
python3 "<SKILL_DIR>/scripts/jira_search.py" issue ABC-123 --comments 5
```

프로젝트/상태 이름 탐색:

```bash
python3 "<SKILL_DIR>/scripts/jira_search.py" projects --query 백엔드
python3 "<SKILL_DIR>/scripts/jira_search.py" statuses --project ABC
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
변환, 기본 800자) + `## comments`. `count`는 근사치 숫자 하나를 출력한다.
결과가 잘리면 마지막에 `(more results available; rerun with --next-page
<token>)`이 붙는다 — `--limit`을 넓히지 말고 토큰으로 페이지를 넘긴다. 스크립트는
에러 메시지에서 자격증명을 마스킹하며 설정된 token을 출력하지 않는다.

## Limits

- `--limit`: 1–100 (Jira API 페이지 상한), 기본 20 (profile `default_limit`).
- `count`는 근사치다 (Jira approximate-count API). 정확한 건수가 필요한 감사
  용도라면 페이지를 끝까지 세어야 함을 사용자에게 알린다.
- `worked`: `--days`와 `--from`은 배타. 둘 다 없으면 최근 14일.
- `due --within N`: 오늘부터 N일 뒤까지 + 연체 포함. `--include-done`을 주지
  않으면 미해결만.
- `text`: Jira `text ~` 검색은 형태소 기반이라 부분 문자열이 아니라 단어
  단위로 매칭된다. 결과가 비면 키워드를 짧게 나눠 다시 시도한다.
- 시간 값: `-7d`, `startOfWeek()`, `"2026-07-01"` 모두 가능. Jira가 서버
  타임존 기준으로 해석한다.
