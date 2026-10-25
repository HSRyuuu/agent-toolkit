# entrypoint — 진입점과 문서 매핑

에이전트가 매 세션 처음 읽는 진입점을 만들거나 보강한다. 다른 자산이 모두 이 파일의 `## 문서 매핑`에 등록되므로 **항상 마지막에** 설치한다. 규약은 `harness-contract.md` §1·§2를 따른다.

## 원본

| 파일 | 용도 |
| --- | --- |
| `templates/entrypoint/ENTRYPOINT.md` | 정본 진입점. `CLAUDE.md` 또는 `AGENTS.md`로 저장한다 |
| `templates/entrypoint/CLAUDE.shim.md` | 두 호스트를 함께 쓸 때의 루트 `CLAUDE.md` |

## 새로 만들 때

1. 프로필의 진입점 전략에 따라 경로를 정한다(규약 §1). Claude Code만 쓰면 루트와 `.claude/` 중 사용자가 고른다.
2. `ENTRYPOINT.md`를 복사하고 토큰을 채운다.

| 토큰 | 채우는 값 | 출처 |
| --- | --- | --- |
| `{PROJECT_NAME}` | 프로젝트 이름 | README 제목, 매니페스트 `name`, 디렉토리 이름 |
| `{ONE_LINER}` | 무엇을 위한 프로젝트인지 한 줄 | README 첫 문단. 없으면 사용자에게 묻는다 |
| `{OVERVIEW_BULLETS}` | 코드로 알 수 없는 맥락 3~5줄 (목표, 사용자, 이미 내린 결정). `PROJECT_OVERVIEW`를 설치하면 그 문서를 가리키는 줄을 첫 줄로 둔다 | README, 사용자 답 |
| `{STRUCTURE_ROWS}` | 모듈 표 `\| 경로 \| 역할 \| 스택 \|`. single이면 주요 디렉토리 3~6개 | 프로필 modules, 직접 읽기 |
| `{COMMAND_ROWS}` | `\| 테스트 \| \`./gradlew test\` \| \`backend/\` \|` 형식의 행 | CI 설정 > 프로필 commands > Makefile |
| `{MAPPING_RULES}` | 설치한 자산의 규칙 줄(규약 §6). 없으면 줄을 지운다 | 각 install 문서 |
| `{SKILL_ROWS}` | 설치한 프로젝트 스킬 행 | install-skills.md |
| `{DOC_ROWS}` | 설치했거나 이미 있던 문서 행 | install-docs.md 등 |

3. `## Core Principles`와 `## Workflows`는 기본으로 포함한다. 사용자가 원치 않으면 두 섹션을 통째로 뺀다.
4. 채울 값이 없는 섹션(`## 구조`가 무의미한 아주 작은 저장소 등)은 섹션째 지운다. 토큰을 남기지 않는다.

## 두 호스트를 함께 쓸 때

1. `AGENTS.md`를 위 절차로 만든다.
2. 루트 `CLAUDE.md`를 `CLAUDE.shim.md`로 만든다. `{CLAUDE_ONLY_NOTES}`에는 Claude Code에만 해당하는 내용(서브에이전트, 슬래시 커맨드 사용법 등)을 넣고, 없으면 `## Claude Code 전용` 섹션을 지운다.
3. 이미 루트 `CLAUDE.md`에 내용이 있으면 shim으로 바꾸기 전에, 그 내용을 `AGENTS.md`로 옮길지 묻는다. 묻지 않고 옮기지 않는다.

## 이미 있을 때

- 정본은 그대로 둔다. 템플릿으로 교체하지 않는다.
- 빠진 섹션만 덧붙인다: `## 구조`, `## 명령어`, `## 문서 매핑`. 이미 같은 역할의 섹션이 다른 이름으로 있으면 그 섹션을 쓴다.
- 매핑 표가 있으면 행만 추가한다. 기존 컬럼과 표기(언어, 정렬)를 따른다.
- 이미 설치돼 있지만 매핑 표에 없는 스킬·문서가 있으면 등록할지 묻는다.
- 루트 `CLAUDE.md`와 `.claude/CLAUDE.md`가 둘 다 있으면 어느 쪽이 정본인지 묻는다. 합치는 것은 명시적 승인 후에만 한다.

## 검증

```bash
python3 <skill>/scripts/check_harness.py "$TARGET"
```

진입점 관련 ERROR(placeholder 잔존, 매핑된 문서 없음)가 없어야 한다.
