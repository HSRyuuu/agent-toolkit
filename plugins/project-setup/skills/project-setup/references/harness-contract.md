# 하네스 규약

설치되는 자산이 서로를 찾을 수 있게 하는 약속이다. 설치된 스킬(`sync-docs`, `manage-skills`, `verify-implementation`)과 `scripts/check_harness.py`가 모두 이 규약을 전제로 동작한다. 설치할 때 여기서 벗어나면 하네스가 끊긴다.

## 1. 진입점은 하나가 정본이다

| 프로젝트가 쓰는 호스트 | 정본 | 나머지 |
| --- | --- | --- |
| Claude Code만 | `CLAUDE.md` (루트) 또는 `.claude/CLAUDE.md` | 없음 |
| Codex만 | `AGENTS.md` (루트) | 없음 |
| 둘 다 | `AGENTS.md` (루트) | 루트 `CLAUDE.md`는 `@AGENTS.md`를 가져오는 shim(`templates/entrypoint/CLAUDE.shim.md`). Claude 전용 내용만 둔다 |

이미 진입점이 있으면 그 위치를 정본으로 유지한다. 두 진입점이 각각 매핑 표를 갖고 있으면 둘을 같게 맞추거나 shim 구조로 바꿀지 사용자에게 묻는다.

## 2. 문서 매핑 섹션

정본 진입점에 다음 형식의 섹션이 하나 있다. 모든 설치 자산은 이 섹션에 등록되어야 하네스에 들어온 것이다.

```markdown
## 문서 매핑

- 위 문서에 영향을 주는 변경을 마쳤으면 ... `sync-docs`로 문서를 맞춘다.   ← 규칙 줄 (설치된 자산에 따라)

### 프로젝트 스킬

| 스킬 | 용도 |
| --- | --- |
| `/sync-docs` | ... |

### 외부문서

| 문서 | 용도 |
| --- | --- |
| `docs/PROJECT_OVERVIEW.md` | ... |
| `docs/plans/` | 디렉토리도 등록할 수 있다 (끝에 `/`) |
```

- 첫 컬럼은 백틱으로 감싼다. 스킬은 `/이름`, 문서는 루트 기준 상대 경로다.
- 영어 프로젝트는 `## Document Map` / `### Project Skills` / `### Documents`를 쓴다. 검사 스크립트와 `sync-docs`는 두 표기를 모두 읽는다.
- 실제로 존재하는 것만 적는다. 예시 행을 남기지 않는다.

## 3. 스킬 위치

| 호스트 | 프로젝트 스킬 디렉토리 |
| --- | --- |
| Claude Code | `.claude/skills/<name>/SKILL.md` |
| Codex | 프로젝트가 이미 쓰는 디렉토리(`.agents/skills/` 또는 `.codex/skills/`). 없으면 사용자에게 묻고, 기본 제안은 `.agents/skills/` |

두 호스트를 함께 쓰면 같은 스킬을 양쪽 디렉토리에 같은 내용으로 둔다. 디렉토리 이름과 frontmatter `name`은 같아야 한다.

## 4. 검증 스킬

- `verify-*` 스킬은 스킬 디렉토리 바로 아래 `verify-<name>/`에 있다.
- 커버 범위(파일 패턴)의 정본은 `manage-skills/SKILL.md`의 `## 등록된 검증 스킬` 표다.
- `verify-implementation`은 목록을 갖지 않고 `verify-*/` 디렉토리를 찾아 실행한다. 프로젝트 명령은 그 파일의 `## 기본 검사` 표에 둔다.
- 새 `verify-*`는 진입점 `### 프로젝트 스킬` 표에도 한 줄씩 등록한다.

## 5. 문서 위치

- 프로젝트에 이미 문서 위치 관례가 있으면(`docs/`, `.claude/`, `wiki/` 등) 그대로 따른다.
- 관례가 없으면 사람이 함께 읽는 문서(`PROJECT_OVERVIEW`, `DESIGN`, `ADR`)는 `docs/`, 에이전트 전용 탐색 문서(`SOURCE_MAP`, `CODEBASE_CONTEXT`)는 사용자 선택에 따라 `docs/` 또는 `.claude/`에 둔다.
- 영역 규칙은 `.claude/rules/<area>.md`, 자기개선 기록은 `.claude/LESSONS.md`에 둔다.

## 6. 규칙 줄

진입점에 넣는 규칙 문구는 설치한 자산에 따라 정해져 있다. 문구는 각 `install-*.md`에 있다. 설치하지 않은 자산의 규칙 줄은 넣지 않는다.

| 자산 | 규칙 줄 위치 |
| --- | --- |
| `sync-docs` | `## 문서 매핑` 바로 아래 |
| `lessons` | `## Workflows` 안 `Self-Improvement Loop` 항목 |
| `rules` | `## 문서 매핑` 바로 아래 (영역 규칙 파일을 먼저 읽으라는 줄) |

## 7. placeholder

- `{UPPER_CASE}` 토큰은 설치할 때 반드시 채우거나, 채울 값이 없으면 그 줄·섹션을 지운다. 남으면 `check_harness.py`가 ERROR를 낸다.
- 문서 템플릿 안의 `<...>` 안내는 코드로 채울 수 없는 경우 사람이 채우도록 남겨도 된다. 검사 스크립트는 개수만 INFO로 알린다.
- 템플릿의 설치 안내용 HTML 주석은 지운다.
