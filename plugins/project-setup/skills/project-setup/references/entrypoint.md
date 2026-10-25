# entrypoint — AGENTS.md / CLAUDE.md와 문서 매핑

에이전트가 매 세션 처음 읽는 진입점을 만들거나 고친다. 진입점의 **문서 매핑 표**는 `sync-docs`가 관리 대상을 찾는 진실의 원천이다.

## 대상

| 자산 | 위치 | 용도 |
| --- | --- | --- |
| `CLAUDE.md` | 루트 또는 `.claude/CLAUDE.md` | Claude Code 프로젝트 지침. 원본 `templates/CLAUDE.md` |
| `AGENTS.md` | 루트 | Codex 등 공통 에이전트 지침 |
| 문서 매핑 섹션 | 위 진입점 안 | 실제 존재하는 문서·로컬 스킬 목록 |

## 절차

1. `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md`가 있는지 본다.
2. 전략을 하나 권한다.
   - Claude Code만 쓰면 `CLAUDE.md`(루트 또는 `.claude/` 중 사용자가 고름). 새로 만들면 `templates/CLAUDE.md`를 복사하고 `{PROJECT_NAME}`과 개요를 채운다.
   - Codex도 쓰면 `AGENTS.md`를 두고, `CLAUDE.md`와 같은 사실을 말하게 한다.
   - 루트 `CLAUDE.md`가 이미 있으면 그대로 쓴다. 루트와 `.claude/` 둘 다 있을 때 합치는 것은 명시적 승인 후에만 한다.
3. 쓰기 전에 파일 경로와 추가할 섹션을 보여 준다.
4. 기존 진입점은 내용을 보존하고, 승인된 섹션만 추가하거나 바꾼다.

## 문서 매핑 표

`## 문서 매핑` 아래에 실제 설치된 것만 적는다. 템플릿의 예시 행과 안내 주석은 지운다.

```markdown
## 문서 매핑

### 프로젝트 스킬

| 스킬 | 용도 |
| --- | --- |
| `/sync-docs` | 코드 변경 후 아래 문서들을 실제 상태와 맞춘다 |

### 외부문서

| 문서 | 용도 |
| --- | --- |
| `docs/PROJECT_OVERVIEW.md` | 프로젝트 정체성, 스택, 마일스톤, 링크 |
| `docs/SOURCE_MAP.md` | 소스 위치 라우팅 맵. 넓게 탐색하기 전에 먼저 읽는다 |
```

## sync-docs 규칙

`sync-docs`가 설치되어 있으면 진입점에 다음 규칙을 넣는다. 이 한 줄이 있어야 에이전트가 매번 문서를 맞춘다.

```markdown
- 위 매핑 표의 문서에 영향을 주는 변경(라우트·스키마·환경변수·배포·의존성·디렉토리 구조 등)을 마쳤으면, 완료를 보고하거나 커밋하기 전에 `sync-docs`로 문서를 맞춘다.
```

## 검증

```bash
test -f "$TARGET/AGENTS.md" || test -f "$TARGET/CLAUDE.md" || test -f "$TARGET/.claude/CLAUDE.md"
rg -n "문서 매핑|Document Map|sync-docs|LESSONS" "$TARGET/AGENTS.md" "$TARGET/CLAUDE.md" "$TARGET/.claude/CLAUDE.md" 2>/dev/null
```
