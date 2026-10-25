---
name: sync-docs
description: >
  Use after finishing a change that may affect any document listed in this
  project's CLAUDE.md/AGENTS.md "문서 매핑" table — routes, pages, APIs, DB schema
  or migrations, env vars, deploy config, dependencies, directory structure —
  and before reporting the work done, committing, or opening a PR, so those
  documents match the code. Also use for "문서 동기화", "문서 맞춰줘", "docs 갱신", "source
  map 갱신", "sync docs", "/sync-docs". Do NOT use to create new documents or to
  edit documents that are not in the mapping table.
argument-hint: "[선택: 매핑 표의 특정 문서 — 예: SOURCE_MAP.md, source-map, db-schema]"
---

# Sync Docs

진입점 매핑 표에 등록된 문서가 코드와 어긋나지 않게 늘 맞춘다. 기준은 항상 **실제 코드와 파일**이다. 문서끼리 맞추지 않는다.

## 원칙

1. **매핑 표가 대상 목록이다.** `CLAUDE.md` / `.claude/CLAUDE.md` / `AGENTS.md`의 `## 문서 매핑`(또는 `## Document Map`) 표에 적힌 문서만 손댄다. 새 문서를 만들지 않는다.
2. **코드로 확인되는 것은 바로 고친다.** 라우트, 파일 경로, 테이블·컬럼, 마이그레이션, 환경변수 이름, 의존성 버전처럼 코드에서 확인되는 사실은 묻지 않고 반영한다.
3. **코드로 알 수 없는 것은 묻는다.** 비즈니스 규칙, 마일스톤, 인프라 스펙, 접근 정책처럼 코드로 검증할 수 없는 내용은 추측하지 않고 사용자에게 묻는다. 답이 없으면 바꾸지 않는다.
4. **형식을 지킨다.** 기존 섹션 헤더, 표 컬럼, 강조 스타일, 언어 표기를 그대로 두고 그 안에 끼워 넣는다. 새 섹션이 필요해 보이면 먼저 묻는다.
5. **지우는 것은 묻는다.** 코드에서 사라진 항목의 행을 지우기 전에 확인받는다.

## 워크플로우

### 1. 대상 추출

진입점을 `CLAUDE.md`, `.claude/CLAUDE.md`, `AGENTS.md` 순으로 찾는다. 매핑 표에서 데이터 행 첫 셀의 백틱 경로를 모은다.

- 슬래시 커맨드 행(`/<skill>`)은 스킬이므로 뺀다.
- placeholder 행(`<path/to/doc.md>`)은 뺀다.
- 진입점 자신은 기본 대상이 아니다. 인수로 `claude`/`agents`를 주거나 매핑 표에 직접 있으면 포함한다.

다음이면 멈추고 알린다.

- 진입점이 없음 → 진입점과 매핑 표를 먼저 만들어야 한다.
- 매핑 표가 없거나 비어 있음 → 갱신할 문서를 매핑 표에 등록한 뒤 다시 실행한다.
- 매핑된 경로의 파일이 없음 → 그 행을 매핑 표에서 지울지 제안한다. 파일을 만들지 않는다.

인수가 있으면 대상을 하나로 좁힌다(정확한 파일명 → 약식 `source-map`·`db-schema`·`deploy`·`overview`·`design` → 부분 일치).

### 2. 변경 범위 파악

```bash
git status --short
git diff --name-status "$(git merge-base HEAD origin/HEAD 2>/dev/null || echo HEAD)"
```

이번 작업 맥락(이 세션에서 바꾼 파일)이 있으면 그것을 먼저 쓴다. 바뀐 파일을 보고 영향받을 문서를 고른다.

| 문서 종류 | 영향 신호 |
| --- | --- |
| `SOURCE_MAP.md` 류 | 소스 파일·디렉토리 추가, 삭제, 이동 |
| `DB_SCHEMA.md` 류 | 마이그레이션, ORM 스키마, entity/model 변경 |
| `DEPLOY.md` 류 | `.github/workflows/`, `Dockerfile`, `vercel.json`, `fly.toml`, 환경변수 사용처 변경 |
| `PROJECT_OVERVIEW.md` 류 | `package.json`, `pyproject.toml`, `build.gradle*`, `Cargo.toml`, `go.mod` 변경 |
| `DESIGN.md` 류 | `tailwind.config.*`, `theme/`, `tokens/`, 공용 UI 컴포넌트 변경 |
| 그 외 | 문서 내용과 바뀐 파일을 대조 |

영향받는 문서가 없으면 "갱신할 문서 없음"을 한 줄로 보고하고 끝낸다.

### 3. 어긋남 찾기

영향받는 문서를 읽고, 문서가 말하는 사실을 바뀐 코드와 대조한다. 문서에 적힌 경로가 실제로 있는지도 확인한다. 각 어긋남을 다음 중 하나로 분류한다.

- **자동**: 코드로 확인되는 추가·변경
- **확인**: 사라진 항목의 삭제, 새 섹션 필요
- **질문**: 코드로 알 수 없는 내용

### 4. 적용

- **자동** 항목은 바로 고친다.
- **확인**·**질문** 항목은 한 번에 모아 묻고, 답한 것만 반영한다.

고친 뒤 표 컬럼 수, 닫히지 않은 코드 블록, 깨진 매핑 표가 없는지 확인한다.

### 5. 보고

```markdown
| 문서 | 반영 | 남은 항목 |
| --- | --- | --- |
| docs/SOURCE_MAP.md | `/orders` 라우트 추가 | — |
| docs/DB_SCHEMA.md | `users.phone_number` 추가 | 접근 범위 확인 필요 |
```

## 하지 않을 것

- 매핑되지 않은 문서, 새 문서를 만들거나 고치지 않는다.
- 기술적으로 맞는 문장을 문체 때문에 다시 쓰지 않는다.
- 코드로 확인하지 않은 내용을 사실처럼 적지 않는다.
