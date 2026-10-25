---
name: project-setup
description: >
  Use when the user wants to know which project-level agent assets fit the
  current project, or wants some or all of them installed — AGENTS.md/CLAUDE.md
  entrypoint with a document map, PROJECT_OVERVIEW·DB_SCHEMA·DEPLOY·DESIGN·ADR
  docs, SOURCE_MAP/CODEBASE_CONTEXT context map, .claude/LESSONS.md
  self-improvement loop, and project-local skills (sync-docs, manage-skills,
  verify-implementation). Triggers: "프로젝트 셋업", "/project-setup", "이 프로젝트에 뭐 세팅하면
  좋아?", "프로젝트 세팅 점검", "CLAUDE.md 세팅해줘", "AGENTS.md 만들어줘", "SOURCE_MAP 만들어줘",
  "LESSONS.md 추가", "sync-docs 설치", "verify-implementation 설치", "프로젝트 레벨 스킬 설치".
  Do NOT use to sync docs in a project that already has them (that project's own
  sync-docs does it) or to install global/plugin skills.
---

# Project Setup

대상 프로젝트를 읽어 적용할 수 있는 프로젝트 레벨 자산을 상태표로 안내하고, 사용자가 고른 것만 설치한다. 이 스킬이 유일한 진입점이다. 설치 원본은 이 plugin의 `templates/`에, 자산별 세부 절차는 `references/`에 있다.

## 경로 기준

- `<skill>` = 이 `SKILL.md`가 있는 디렉토리
- `<plugin>` = `<skill>/../..` (plugin 루트). 템플릿은 `<plugin>/templates/`에 있다.
- `$TARGET` = 설치 대상 프로젝트 루트

## 자산 카탈로그

| 키 | 자산 | 설치 위치 | 원본 | 절차 |
| --- | --- | --- | --- | --- |
| `entrypoint` | `AGENTS.md` / `CLAUDE.md` + 문서 매핑 표 | 루트 또는 `.claude/CLAUDE.md` | `templates/CLAUDE.md` | `references/entrypoint.md` |
| `docs` | `PROJECT_OVERVIEW.md`, `DB_SCHEMA.md`, `DEPLOY.md`, `DESIGN.md`, `ADR.md` | `docs/` | `templates/docs/` | `references/project-docs.md` |
| `context-map` | `SOURCE_MAP.md`, `CODEBASE_CONTEXT.md` (+ 선택 `.codesight/`) | `docs/` | `<skill>/scripts/build_context_map.py` | `references/context-map.md` |
| `lessons` | `.claude/LESSONS.md` + 진입점의 자기개선 규칙 | `.claude/` | `templates/LESSONS.md` | `references/self-improvement.md` |
| `skill:sync-docs` | 매핑된 문서를 코드 변경에 맞춰 늘 최신으로 유지하는 스킬 | `.claude/skills/sync-docs/` | `templates/skills/sync-docs/` | `references/local-skills.md` |
| `skill:manage-skills` | 세션 변경을 보고 `verify-*` 스킬을 만들고 고친다 | `.claude/skills/manage-skills/` | `templates/skills/manage-skills/` | `references/local-skills.md` |
| `skill:verify-implementation` | 등록된 `verify-*` 스킬을 모두 돌려 통합 검증 | `.claude/skills/verify-implementation/` | `templates/skills/verify-implementation/` | `references/local-skills.md` |

`manage-skills`와 `verify-implementation`은 짝으로 권한다. 원본이 디스크에 없는 자산은 메뉴에서 빼고 보고한다.

## 워크플로우

### 1. 대상 결정

사용자가 준 경로, `git rev-parse --show-toplevel`, `pwd` 순으로 `$TARGET`을 정한다. 대상이 이 plugin을 담은 저장소 자신이면 정말 그곳에 설치할지 묻는다.

### 2. 읽기 전용 스캔

파일을 만들거나 고치지 않고 다음을 확인한다.

- 진입점: `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md`, 그 안의 문서 매핑 표
- 문서: `docs/` 아래 카탈로그 문서들. 사용자가 다른 문서 위치를 알려 주면 그 경로를 본다.
- 자기개선: `.claude/LESSONS.md`, 진입점의 `LESSONS` / `Self-Improvement` 언급
- 로컬 스킬: `.claude/skills/*/SKILL.md` (Codex를 쓰는 프로젝트면 `.codex/skills/`, `.agents/skills/`도)
- 신호
  - DB: `migrations/`, `prisma/`, `alembic/`, `db/migrate/`, entity/model 디렉토리
  - 배포: `.github/workflows/`, `Dockerfile`, `vercel.json`, `fly.toml`, 클라우드 설정
  - 디자인: 프론트엔드 디렉토리, `tailwind.config.*`, `theme/`, `tokens/`, Storybook
  - 소스 맵 필요: `src/`, `app/`, `frontend/`, `backend/`, 여러 서비스·모듈, 파일 수가 많음
  - ADR: `docs/adr/`, `docs/decisions/`, 여러 모듈

### 3. 상태표로 안내

```markdown
| 자산 | 상태 | 근거 | 권장 |
| --- | --- | --- | --- |
| entrypoint | partial | `CLAUDE.md`는 있으나 문서 매핑 표 없음 | 권장 |
| docs: DB_SCHEMA.md | missing | `prisma/` 감지 | 권장 |
| context-map | missing | `frontend/`, `backend/` 감지 | 권장 |
| skill:sync-docs | missing | 매핑할 문서가 생김 | 권장 |
| docs: DESIGN.md | optional | UI 신호 없음 | 선택 |
```

상태는 `present`(조치 불필요), `partial`(있지만 핵심 매핑·규칙 빠짐), `missing`(없고 필요해 보임), `optional`(신호는 약하지만 쓸모 있음) 중 하나다. 기본 권장은 `entrypoint`, `docs: PROJECT_OVERVIEW.md`, 그리고 문서를 하나라도 두면 `skill:sync-docs`다.

사용자가 안내만 원했으면 여기서 끝낸다.

### 4. 선택 받기

적용을 원하면 무엇을 설치할지 묻는다: 권장 항목 전체 / 개별 선택 / 취소. 사용자가 처음부터 특정 자산을 지목했으면("SOURCE_MAP 만들어줘") 스캔은 그 자산 위주로 하고, 그것만 확인 후 진행한다. 확인 질문은 Claude Code에서는 `AskUserQuestion`, 입력 도구가 없는 호스트에서는 짧은 직접 질문으로 한다.

### 5. 적용

선택된 자산마다 해당 `references/*.md`를 읽고 따른다. 진입점이 실제로 설치된 것만 매핑하도록 순서는 다음과 같다.

1. `docs` → 2. `context-map` → 3. `lessons` → 4. `skill:*` → 5. `entrypoint`

`entrypoint`를 고르지 않았더라도 진입점이 이미 있으면, 새로 설치한 문서·스킬을 그 매핑 표에 추가할지 묻는다. 매핑 표에 없는 문서는 `sync-docs`가 관리하지 않기 때문이다.

### 6. 검증과 보고

각 reference의 검증 명령을 돌리고, 설치·건너뜀·백업·이름 변경 항목과 남은 권장 사항을 보고한다.

## 공통 규칙

- **묻기 전에 쓰지 않는다.** 4단계 확인 전에는 어떤 파일도 만들지 않는다.
- **충돌 시 묻는다.** 대상 경로에 이미 있으면 유지 / `.bak.<timestamp>` 백업 후 교체 / (문서라면) 빠진 섹션만 추가 / 취소 중에서 고르게 한다. 조용히 덮어쓰지 않는다.
- **템플릿을 지어내지 않는다.** `templates/`에 없는 원본은 만들지 않고 건너뛴 뒤 보고한다.
- **설치용 안내는 지운다.** 템플릿의 설치 안내용 HTML 주석은 지운다. 실제 값으로 채울 수 있는 placeholder는 채우고, 채울 수 없는 것은 프로젝트 담당자가 채우도록 남긴다.
- **매핑은 사실만.** 진입점 매핑 표에는 실제로 존재하는 경로만 적는다.
- **범위 밖은 건드리지 않는다.** `.gitignore`, 패키지 파일, plugin manifest, 관련 없는 문서는 수정하지 않는다.
