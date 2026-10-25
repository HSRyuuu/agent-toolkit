# 프로젝트 분석

설치 전에 대상 프로젝트를 한 번 분석해 **무엇을 권할지**와 **어떻게 설치할지**를 정한다. 이 단계는 파일을 쓰지 않는다.

## 1. 기계 스캔

```bash
python3 <skill>/scripts/scan_project.py "$TARGET"          # 사람이 읽는 요약
python3 <skill>/scripts/scan_project.py "$TARGET" --json   # 세부 값이 필요할 때
python3 <skill>/scripts/check_harness.py "$TARGET"         # 이미 하네스가 있으면 상태 점검
```

스캔이 주는 것: 호스트(Claude/Codex), 기존 진입점과 매핑 표, 기존 스킬·문서·rules·LESSONS, 저장소 형태(single / multi-module / monorepo), 모듈별 스택과 명령어, 신호(DB·배포·디자인·ADR·env), 문서 언어, 기본 브랜치, 컨텍스트 맵 생성기 지원 수준.

## 2. 직접 읽기

스크립트가 못 보는 것은 직접 확인한다. 넓게 뒤지지 말고 아래만 읽는다.

1. `README.md`와 기존 진입점 — 프로젝트 정체성, 이미 정한 규칙
2. 모듈마다 진입 파일 1~2개와 대표 디렉토리 구조(`ls` 2단계) — 레이어 구조, 명명 관례
3. 테스트 위치와 실행 방식 — 단위·E2E 구분, 명령
4. CI 설정 — 실제로 돌리는 빌드·테스트·린트 명령 (스캔 결과보다 CI가 정확하다)
5. 기존 문서 디렉토리 — 문서가 어디에, 어떤 형식으로 쌓여 있는지

## 3. 프로필 정리

사용자에게 보여 줄 짧은 프로필을 만든다. 이 값이 설치 내용을 정한다.

```markdown
| 항목 | 값 |
| --- | --- |
| 호스트 | Claude Code (`.claude/` 있음), Codex 없음 |
| 형태 | multi-module: `backend/` (Spring Boot·Kotlin), `frontend/` (Next.js) |
| 명령 | `./gradlew test` (backend), `npm run lint`·`npm run build` (frontend) |
| 문서 | `docs/`, 한국어 |
| 기본 브랜치 | `main` |
| 기존 하네스 | `.claude/CLAUDE.md`(매핑 표 없음), 스킬 3개, LESSONS 없음 |
```

## 4. 설치 방식 결정

프로필에 따라 다음과 같이 설치 방식을 정한다. 결정 내용은 설치 계획에 그대로 적는다.

| 프로필 | 설치 방식 |
| --- | --- |
| 호스트 | 하네스 규약 §1에 따라 진입점 전략을 정한다. 둘 다 쓰면 `AGENTS.md` 정본 + `CLAUDE.md` shim을 권한다 |
| 진입점이 이미 있음 | 교체하지 않는다. 빠진 섹션(`## 구조`, `## 명령어`, `## 문서 매핑`)만 덧붙이고 기존 문구는 보존한다 |
| 매핑 표가 이미 있음 | 행만 추가한다. 기존 행의 형식(컬럼, 언어)을 따른다 |
| 문서 위치 관례 있음 | 그 디렉토리에 설치한다. 기존 문서와 같은 이름이면 충돌 처리로 넘긴다 |
| 문서 언어 | 템플릿의 구조(섹션·표 컬럼)는 유지하고 문장은 프로젝트 언어로 쓴다 |
| 형태 single | 진입점 하나, `SOURCE_MAP` 하나 |
| 형태 multi-module / monorepo | 진입점 `## 구조`에 모듈 표를 두고, `SOURCE_MAP`은 모듈별 섹션으로 나눈다. 모듈이 크고 팀이 나뉘면 모듈 디렉토리의 하위 진입점(`<module>/CLAUDE.md` 또는 `AGENTS.md`)을 선택지로 제안한다 |
| 모듈마다 스택이 다름 | `rules`를 모듈(영역)별 파일로 나눠 권한다 (`.claude/rules/backend.md`, `frontend.md`) |
| 명령어 | 진입점 `## 명령어` 표와 `verify-implementation`의 `## 기본 검사` 표를 채운다. CI에서 확인한 명령을 우선한다 |
| 기본 브랜치 | `manage-skills`의 `{BASE_BRANCH}`를 채운다 |
| 컨텍스트 맵 지원 `full` | `build_context_map.py`로 생성한다 |
| 컨텍스트 맵 지원 `partial` | 생성기로 골격을 만들고, 라우트·엔트리포인트는 코드를 읽고 직접 채운다 |
| 컨텍스트 맵 지원 `none` | 소스가 거의 없으면 권하지 않는다 |
| 구 이름 `update-project-docs` 설치됨 | `sync-docs`로 교체를 권한다 (install-skills.md의 이전 절차) |
| 설치된 템플릿 스킬이 원본과 다름 | 프로젝트 맞춤일 수 있다. diff를 보여 주고 갱신 여부를 묻는다. 묻지 않고 덮어쓰지 않는다 |

## 5. 권장 판단

| 자산 | 권장 | 선택 | 권하지 않음 |
| --- | --- | --- | --- |
| entrypoint | 진입점이 없거나 매핑 표가 없음 | — | 정본 진입점과 매핑 표가 모두 있음 |
| docs: PROJECT_OVERVIEW | 없음 | — | 있음 |
| docs: DB_SCHEMA | DB 신호 있음 | ORM만 있고 스키마 파일 없음 | DB 신호 없음 |
| docs: DEPLOY | 배포 신호 있음 | env 예시 파일만 있음 | 배포 신호 없음 |
| docs: DESIGN | 디자인 신호 있음 | 프론트엔드만 있음 | UI 없음 |
| docs: ADR | 모듈 2개 이상 또는 ADR 디렉토리 있음 | 단일 모듈 | — |
| context-map | 소스 파일 100개 이상 또는 multi-module 이상 | 소스 30~100개 | 30개 미만 |
| rules | 모듈마다 스택이 다르거나, 반복되는 관례가 코드에 분명함 | 단일 스택 | 소스가 거의 없음 |
| lessons | 없음 (항상 쓸모 있음) | — | 이미 있음 |
| skill:sync-docs | 매핑할 문서가 하나라도 생김 | — | 매핑할 문서가 없음 |
| skill:manage-skills + verify-implementation | 명령어가 있고 소스가 30개 이상 | 작은 프로젝트 | 소스가 거의 없음 |

이미 있는 자산은 `present`, 있지만 규약을 어기면 `partial`(무엇이 빠졌는지 근거에 적는다)로 표시한다.
