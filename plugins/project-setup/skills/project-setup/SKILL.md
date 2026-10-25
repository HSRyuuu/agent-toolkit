---
name: project-setup
description: >
  Use when the user wants to know which project-level agent harness assets fit
  the current project, or wants some or all of them installed — AGENTS.md/CLAUDE.md
  entrypoint with a document map, PROJECT_OVERVIEW·DB_SCHEMA·DEPLOY·DESIGN·ADR
  docs, SOURCE_MAP/CODEBASE_CONTEXT context map, .claude/rules area rules,
  .claude/LESSONS.md self-improvement loop, and project-local skills (sync-docs,
  manage-skills, verify-implementation). Analyzes the project first and installs
  only what the user picks. Triggers: "프로젝트 셋업", "/project-setup",
  "이 프로젝트에 뭐 세팅하면 좋아?", "프로젝트 세팅 점검", "하네스 세팅", "CLAUDE.md 세팅해줘",
  "AGENTS.md 만들어줘", "SOURCE_MAP 만들어줘", "LESSONS.md 추가", "sync-docs 설치",
  "verify-implementation 설치", "프로젝트 레벨 스킬 설치", "하네스 점검". Do NOT use to
  sync docs in a project that already has them (that project's own sync-docs
  does it) or to install global/plugin skills.
---

# Project Setup

대상 프로젝트를 분석해 적용할 수 있는 프로젝트 레벨 하네스(진입점, 문서, 규칙, 로컬 스킬)를 안내하고, **사용자가 고른 것만** 그 프로젝트에 맞는 방식으로 설치한다. 설치한 것들이 서로 이어져 동작하도록 하네스 규약을 지키고, 끝에 검사 스크립트로 확인한다.

이 plugin에서 스킬은 이것 하나다. `templates/`는 설치용 원본, `references/`는 단계별 절차, `scripts/`는 분석·생성·검사 도구다.

## 경로

- `<skill>` = 이 `SKILL.md`가 있는 디렉토리
- `<plugin>` = `<skill>/../..`. 설치 원본은 `<plugin>/templates/`
- `$TARGET` = 설치 대상 프로젝트 루트

## 자산 카탈로그

| 키 | 자산 | 설치 위치 (기본) | 원본 | 절차 |
| --- | --- | --- | --- | --- |
| `entrypoint` | 정본 진입점 + `## 구조`·`## 명령어`·`## 문서 매핑` | `AGENTS.md` / `CLAUDE.md` | `templates/entrypoint/` | `references/install-entrypoint.md` |
| `docs:<name>` | `PROJECT_OVERVIEW`, `DB_SCHEMA`, `DEPLOY`, `DESIGN`, `ADR` (코드로 확인되는 섹션은 채움) | 문서 디렉토리 | `templates/docs/` | `references/install-docs.md` |
| `context-map` | `SOURCE_MAP.md`, `CODEBASE_CONTEXT.md` | 문서 디렉토리 또는 `.claude/` | `<skill>/scripts/build_context_map.py` | `references/install-context-map.md` |
| `rules` | 영역별 코딩 규칙 (코드에서 확인한 관례) | `.claude/rules/<area>.md` | `templates/rules/RULES.md` | `references/install-rules.md` |
| `lessons` | `LESSONS.md` + 진입점 자기개선 규칙 | `.claude/LESSONS.md` | `templates/LESSONS.md` | `references/install-lessons.md` |
| `skill:sync-docs` | 매핑된 문서를 코드 변경에 맞춰 늘 최신으로 유지 (자동 호출) | 스킬 디렉토리 | `templates/skills/sync-docs/` | `references/install-skills.md` |
| `skill:manage-skills` | 세션 변경을 보고 `verify-*` 스킬을 만들고 고침 | 스킬 디렉토리 | `templates/skills/manage-skills/` | `references/install-skills.md` |
| `skill:verify-implementation` | 기본 검사(빌드·테스트·린트)와 모든 `verify-*` 실행 | 스킬 디렉토리 | `templates/skills/verify-implementation/` | `references/install-skills.md` |

자산 사이의 약속(진입점 정본, 매핑 섹션 형식, 스킬 위치, 규칙 줄, placeholder)은 `references/harness-contract.md`에 있다. 설치 전에 한 번 읽는다.

## 워크플로우

### 1. 대상 결정

사용자가 준 경로, `git rev-parse --show-toplevel`, `pwd` 순으로 `$TARGET`을 정한다. 대상이 이 plugin을 담은 저장소 자신이면 정말 그곳에 설치할지 묻는다.

### 2. 분석

`references/analyze.md`를 따른다. `scan_project.py`로 기계 스캔을 하고, 스크립트가 못 보는 부분(README, 모듈 진입 파일, CI, 기존 문서)을 직접 읽어 **프로필**을 만든다. 하네스가 이미 있으면 `check_harness.py`로 상태를 점검한다. 이 단계는 파일을 쓰지 않는다.

### 3. 안내

프로필과 상태표를 보여 준다.

```markdown
**프로필** — Claude Code · multi-module (`backend/` Spring Boot·Kotlin, `frontend/` Next.js) · 문서 `docs/`, 한국어 · 기본 브랜치 `main`

| 자산 | 상태 | 근거 | 권장 | 설치 방식 |
| --- | --- | --- | --- | --- |
| entrypoint | partial | `.claude/CLAUDE.md`에 매핑 표·명령어 없음 | 권장 | 기존 파일 유지, 섹션만 추가 |
| docs:DB_SCHEMA | missing | Flyway 마이그레이션 12개 | 권장 | `docs/`에 생성, 테이블·Enum은 마이그레이션에서 채움 |
| context-map | missing | 소스 150개, Next.js·Spring | 권장 | 생성기 사용 (full 지원) |
| rules | missing | 모듈마다 스택이 다름 | 권장 | `backend.md`, `frontend.md` |
| skill:sync-docs | missing | 매핑할 문서가 생김 | 권장 | `.claude/skills/` |
| docs:DESIGN | optional | Tailwind 설정만 있음 | 선택 | 토큰만 채움 |
```

상태는 `present` / `partial` / `missing` / `optional`, 권장은 `권장` / `선택` / `불필요`다. 판단 기준은 `analyze.md` §5.

사용자가 안내만 원했으면("뭐 세팅하면 좋아?", "점검해줘") 여기서 끝낸다.

### 4. 선택

무엇을 설치할지 묻는다: 권장 전체 / 개별 선택 / 취소. 사용자가 처음부터 특정 자산을 지목했으면 그 자산만 대상으로 한다.

**고른 것만 설치한다.** 다만 고른 자산이 동작하려면 다른 자산이 필요할 때는 알리고 함께 설치할지 묻는다. 묻지 않고 더하지 않는다.

| 고른 자산 | 필요한 것 | 없을 때 |
| --- | --- | --- |
| 모든 문서·rules·스킬 | 정본 진입점의 `## 문서 매핑` | 진입점이 있으면 매핑 섹션만 추가한다(설치 계획에 표시). 진입점이 없으면 `entrypoint`를 함께 설치할지 묻는다. 거절하면 "매핑되지 않아 sync-docs가 관리하지 못한다"고 알리고 진행한다 |
| `skill:sync-docs` | 매핑된 문서 1개 이상 | 문서도 고를지 묻는다 |
| `skill:manage-skills` | `skill:verify-implementation` (반대도 같다) | 짝을 함께 설치할지 묻는다 |
| `lessons` | 진입점 규칙 줄 | 진입점에 규칙 줄을 넣는 것까지가 `lessons` 설치다 |

### 5. 설치 계획

쓰기 전에 계획을 한 번에 보여 주고 승인받는다.

```markdown
| # | 파일 | 처리 | 내용 |
| --- | --- | --- | --- |
| 1 | `docs/DB_SCHEMA.md` | 생성 | 마이그레이션 12개에서 테이블 8개·Enum 3개 채움, 접근 범위는 비워 둠 |
| 2 | `.claude/rules/backend.md` | 생성 | Kotlin·Spring 관례 7개 (근거 파일 포함) |
| 3 | `.claude/skills/sync-docs/` | 생성 | 원본 복사 |
| 4 | `.claude/CLAUDE.md` | 수정 | `## 명령어`·`## 문서 매핑` 섹션 추가, 기존 내용 유지 |

충돌: 없음 · 설치 중 물어볼 것: 프로젝트 한 줄 정의
```

충돌이 있는 파일은 처리 칸에 선택지를 적고 이 단계에서 함께 고르게 한다(유지 / 백업 후 교체 / 빠진 섹션만 추가 / 취소).

### 6. 설치

승인된 계획대로 `references/install-*.md`를 따른다. 진입점이 실제로 설치된 것만 가리키도록 순서는 다음과 같다.

1. `docs` → 2. `context-map` → 3. `rules` → 4. `lessons` → 5. `skill:*` → 6. `entrypoint`(새로 만들거나 섹션·행·규칙 줄 추가)

설치 중 코드로 알 수 없는 값은 모아서 한 번에 묻는다. 답이 없으면 `<...>`로 남긴다.

### 7. 검증

```bash
python3 <skill>/scripts/check_harness.py "$TARGET"
```

ERROR가 있으면 고치고 다시 돌린다. 같은 ERROR가 두 번 연속 남으면 멈추고 이유를 보고한다. `context-map`을 설치했으면 `validate_context_map.py`도 돌린다.

### 8. 보고

- 설치·수정·건너뜀·백업한 파일
- 사람이 채워야 할 곳 (`<...>` 개수와 문서)
- 이제 하네스가 어떻게 동작하는지: 어떤 상황에 어떤 스킬이 실행되는지 2~4줄 (예: "코드 변경 후 커밋 전에 `sync-docs`가 자동으로 문서를 맞춘다", "`/manage-skills`로 첫 `verify-*` 스킬을 만든다")
- 이번에 고르지 않은 권장 자산

## 다시 실행할 때

이미 설치된 프로젝트에서 다시 호출하면 같은 흐름으로 동작하며, 상태표가 갱신 제안 역할을 한다.

- 설치된 템플릿 스킬이 원본과 다르면 diff를 보여 주고 갱신할지 묻는다. 프로젝트 맞춤일 수 있으므로 묻지 않고 덮어쓰지 않는다.
- 구 이름 `update-project-docs`는 `sync-docs`로 교체를 권한다.
- 매핑 표에 없는 문서·스킬이 있으면 등록할지 묻는다.

## 공통 규칙

- **묻기 전에 쓰지 않는다.** 5단계 승인 전에는 어떤 파일도 만들거나 고치지 않는다.
- **고른 것만 설치한다.** 필요한 전제가 빠졌으면 알리고 묻는다.
- **기존 것을 존중한다.** 기존 진입점·문서·규칙은 교체하지 않고 빠진 부분만 더한다. 조용히 덮어쓰지 않는다.
- **분석한 사실만 쓴다.** 코드로 확인한 값만 채우고, 확인하지 못한 값은 `<...>`로 남긴다. 시크릿 값은 적지 않는다.
- **템플릿을 지어내지 않는다.** `templates/`에 없는 원본은 만들지 않고 보고한다.
- **토큰을 남기지 않는다.** `{UPPER_CASE}` 토큰은 채우거나 그 줄을 지운다.
- **범위 밖은 건드리지 않는다.** `.gitignore`, 패키지 파일, CI 설정, plugin manifest는 수정하지 않는다.
- 확인 질문은 Claude Code에서는 `AskUserQuestion`, 입력 도구가 없는 호스트에서는 짧은 직접 질문으로 한다.
