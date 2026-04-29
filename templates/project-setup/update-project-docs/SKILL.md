---
name: update-project-docs
description: `.claude/`의 에이전트 작업 문서(CLAUDE.md, PROJECT_OVERVIEW.md, SOURCE_MAP.md, DB_SCHEMA.md, DEPLOY.md)를 코드베이스 실제 상태와 비교하여 드리프트를 탐지하고 동기화합니다. 대규모 작업 완료 후, 새 도메인/테이블/엔드포인트 추가 후, PR 전 문서 정합성 점검 시 사용. 트리거 - "문서 동기화", "claude 문서 업데이트", "source map 갱신", "db schema 동기화", "/update-project-docs".
disable-model-invocation: true
argument-hint: "[선택사항: claude | overview | source-map | db-schema | deploy]"
---

# Update Project Docs — 에이전트 작업 문서 최신화

`.claude/` 폴더의 작업 문서가 시간이 지나면서 코드베이스와 어긋나는 것을 막는다. **현재 코드 상태를 진실의 원천으로 삼아** 문서의 드리프트를 탐지하고, 사용자 승인 후 수정한다.

## 적용 범위

| 문서 | 검증 초점 |
|------|----------|
| `.claude/CLAUDE.md` | 도메인 규칙, 문서 매핑, 정보 소유권 표 정확성 |
| `.claude/PROJECT_OVERVIEW.md` | 기술 스택 버전, 마일스톤, 핵심 링크 |
| `.claude/SOURCE_MAP.md` | 등록된 파일 경로 존재 여부, 누락된 주요 파일 |
| `.claude/DB_SCHEMA.md` | 마이그레이션·엔티티·Enum과 테이블 정의 일치 |
| `.claude/DEPLOY.md` | CI/CD 워크플로, 환경변수, 인프라 설정 |

## 실행 시점

- 대규모 기능 구현이 완료된 후
- 새 도메인·테이블·API 엔드포인트를 추가한 후
- 마이그레이션 파일을 추가/수정한 후
- 의존성을 업그레이드한 후 (Next.js, Spring Boot, Python 등 메이저 버전)
- 디렉토리 구조 변경(이동·리네이밍) 후
- PR 직전 문서 정합성 점검

## 핵심 원칙

1. **코드가 진실의 원천** — 문서가 코드와 다르면 코드를 따르도록 문서를 수정한다. 그 반대는 하지 않는다.
2. **모호하면 묻는다** — 코드만으로 판단할 수 없는 비즈니스 규칙·인프라 스펙은 `AskUserQuestion`으로 사용자에게 묻는다.
3. **수정 전 승인** — 자동으로 적용하지 않는다. 발견된 드리프트를 모두 보고한 뒤 사용자 승인을 받고 수정한다.
4. **형식 보존** — 기존 마크다운 형식(테이블 정렬, 섹션 순서, 강조 스타일)을 그대로 유지한다.

## 워크플로우

### Step 0 — 대상 결정

선택적 인수가 제공된 경우 해당 문서만 검사한다:

| 인수 | 대상 |
|------|------|
| `claude` | CLAUDE.md만 |
| `overview` | PROJECT_OVERVIEW.md만 |
| `source-map` | SOURCE_MAP.md만 |
| `db-schema` | DB_SCHEMA.md만 |
| `deploy` | DEPLOY.md만 |
| (없음) | 5개 문서 모두 |

### Step 1 — 프로젝트 스택 자동 탐지

문서 검증 전에 프로젝트의 실제 구조를 파악한다. 결과는 이후 단계에서 어떤 검사를 돌릴지 결정한다.

```bash
# 빌드 도구 / 언어 감지
ls package.json pyproject.toml pom.xml build.gradle build.gradle.kts Cargo.toml go.mod 2>/dev/null

# 프론트엔드 / 백엔드 분리 여부
ls -d frontend backend client server web api 2>/dev/null

# 마이그레이션 도구 감지
ls -d \
  backend/src/main/resources/db/migration \
  prisma/migrations \
  alembic \
  db/migrate \
  migrations \
  2>/dev/null
```

탐지 결과를 사용자에게 한 줄로 요약하고, 검증을 시작한다.

### Step 2 — SOURCE_MAP.md 검증

#### 2a. 등록된 경로 존재 확인

SOURCE_MAP.md에 적힌 모든 파일 경로를 추출하여 실제 존재 여부를 확인한다:

```bash
# 표 셀에서 백틱으로 감싼 경로 추출 후 ls로 검증
# (정규식은 프로젝트 형식에 맞게 조정)
ls <path> 2>/dev/null || echo "MISSING: <path>"
```

**FAIL:** 존재하지 않는 경로 → 행 제거 또는 새 경로로 업데이트
**PASS:** 모든 경로 존재

#### 2b. 등록되지 않은 주요 파일 탐지

코드베이스에서 SOURCE_MAP에 없는 주요 파일을 찾는다. **모든 파일을 등록할 필요는 없다** — 주요 진입점만 대상.

| 파일 종류 | 탐지 명령 (예) |
|----------|---------------|
| 페이지 라우트 (Next.js) | `find <frontend>/app -name "page.tsx" -type f` |
| 페이지 라우트 (Vite/CRA) | `find <frontend>/src -name "*.tsx" -path "*pages/*"` |
| 레이아웃 | `find <frontend>/app -name "layout.tsx"` |
| 공유 컴포넌트 | `ls <frontend>/components/{ui,feature,layout}` |
| API 클라이언트 | `ls <frontend>/lib/api/` 또는 `ls <frontend>/src/api/` |
| 백엔드 컨트롤러/라우터 | `grep -rln "@RestController\|@Controller\|@RequestMapping\|@Router" <backend>` |
| 백엔드 엔티티 | `grep -rln "@Entity\|class.*Schema\|model =" <backend>` |
| 백엔드 서비스 | `grep -rln "@Service\|class.*Service" <backend>` |

**FAIL:** SOURCE_MAP에 없는 주요 파일 → 해당 섹션에 행 추가
**PASS:** 모든 주요 파일 등록됨

#### 2c. 변경된 파일의 설명 정확성

이번 작업으로 변경된 파일에 한해, SOURCE_MAP의 설명이 여전히 정확한지 확인한다:

```bash
git diff main...HEAD --name-only 2>/dev/null || git diff HEAD --name-only
```

변경된 파일이 SOURCE_MAP에 있으면 해당 파일을 읽고 설명을 검증한다. 모호하면 사용자에게 묻는다.

### Step 3 — DB_SCHEMA.md 검증

#### 3a. 마이그레이션 목록 정합성

감지된 마이그레이션 디렉토리를 나열하고 DB_SCHEMA의 "마이그레이션" 섹션과 대조한다:

```bash
# Flyway / Liquibase
ls backend/src/main/resources/db/migration/ 2>/dev/null

# Prisma
ls prisma/migrations/ 2>/dev/null

# Alembic
ls alembic/versions/ 2>/dev/null
```

**FAIL:** DB_SCHEMA에 없는 마이그레이션 발견 → 마이그레이션 섹션 갱신
**PASS:** 모든 마이그레이션이 기록됨

#### 3b. 엔티티/모델과 테이블 대조

엔티티 정의를 찾아 DB_SCHEMA의 테이블과 대조한다:

| ORM | 탐지 패턴 |
|-----|----------|
| JPA (Java/Kotlin) | `grep -rln "@Entity" <backend>` |
| Prisma | `prisma/schema.prisma` 한 파일에 정의 |
| SQLAlchemy | `grep -rln "Base.metadata\|class.*Base" <backend>` |
| TypeORM | `grep -rln "@Entity" <backend>` |
| Django | `grep -rln "class.*models.Model" <backend>` |

각 엔티티에 대해 확인:
- 테이블명이 DB_SCHEMA에 존재하는가
- 컬럼이 DB_SCHEMA의 테이블 정의와 일치하는가
- DB_SCHEMA에는 있지만 엔티티에 없는 컬럼(또는 그 반대)은?

#### 3c. Enum 값 동기화

```bash
# Java/Kotlin
grep -rln "enum class\|public enum" <backend>

# Python
grep -rln "class.*Enum\|StrEnum" <backend>

# Prisma
grep -A5 "enum " prisma/schema.prisma
```

DB_SCHEMA의 "Enum 정리" 섹션과 비교한다.

#### 3d. ER 다이어그램·접근 범위

테이블/FK 변경이 감지되면 ER 다이어그램(텍스트)이 현재 관계를 반영하는지 검토한다.

새 엔티티의 **접근 범위**(유저 한정 / 모두 공유 / 시스템)는 코드만으로 판단하기 어려우므로 `AskUserQuestion`으로 묻는다.

### Step 4 — CLAUDE.md 검증

CLAUDE.md는 도메인 규칙·문서 매핑이 핵심이므로 자동 검증 범위가 좁다.

#### 4a. 문서 매핑 표 정합성

CLAUDE.md에 나열된 문서 경로가 실제 존재하는지 확인한다:

```bash
# 문서 매핑 표의 경로 추출 후 ls
ls .claude/PROJECT_OVERVIEW.md .claude/SOURCE_MAP.md .claude/DB_SCHEMA.md .claude/DEPLOY.md 2>&1
ls .claude/rules/*.md 2>/dev/null
ls .claude/skills/*/SKILL.md 2>/dev/null
```

**FAIL:** 표에 등록됐지만 존재하지 않는 문서 → 행 제거
**FAIL:** 존재하지만 등록되지 않은 문서 → 행 추가 (사용자에게 확인)

#### 4b. 정보 소유권 표 정합성

각 정보가 실제로 그 문서에 있는지, 다른 문서로 이주했는지 확인한다. 자동 판단이 어려우므로 변경 가능성이 높은 항목만 추출하여 사용자에게 질의한다.

#### 4c. 도메인 규칙 — 자동 검증 불가

도메인 규칙은 비즈니스 제약이므로 코드만으로 검증할 수 없다. 변경 의심 시 사용자에게 묻는다:

> "현재 CLAUDE.md의 도메인 규칙이 최신 비즈니스 규칙과 일치합니까? 변경된 항목이 있으면 알려주세요."

### Step 5 — PROJECT_OVERVIEW.md 검증

#### 5a. 기술 스택 버전

빌드 파일의 의존성과 PROJECT_OVERVIEW의 기술 스택 표를 대조한다:

```bash
# Frontend
grep -E '"(next|react|vue|svelte|tailwindcss|typescript)"' package.json 2>/dev/null

# Java/Kotlin
grep -E "(kotlin|springBootVersion|javaVersion)" build.gradle.kts build.gradle 2>/dev/null

# Python
grep -E "^(python|fastapi|django|sqlalchemy)" pyproject.toml requirements.txt 2>/dev/null

# Node backend
grep -E '"(express|nestjs|fastify)"' package.json 2>/dev/null
```

**FAIL:** 버전 불일치 → 해당 행 업데이트

#### 5b. 마일스톤 / 링크

마일스톤·링크는 외부 정보이므로 자동 검증 불가. 사용자에게 묻는다:

> "PROJECT_OVERVIEW의 마일스톤과 핵심 링크가 최신 상태입니까? 추가하거나 갱신할 항목이 있으면 알려주세요."

### Step 6 — DEPLOY.md 검증

#### 6a. CI/CD 워크플로

```bash
ls .github/workflows/ 2>/dev/null
ls .gitlab-ci.yml .circleci/config.yml 2>/dev/null
```

DEPLOY.md의 "CI/CD" 섹션에 나열된 파일과 비교한다. 변경된 워크플로 파일이 있으면 내용을 읽고 트리거 조건·배포 순서가 정확한지 확인한다.

#### 6b. 컨테이너 / 빌드 설정

```bash
ls Dockerfile docker-compose.yml docker-compose.*.yml 2>/dev/null
ls cloud-run-service*.yaml fly.toml render.yaml vercel.json 2>/dev/null
```

DEPLOY.md에 기술된 빌드/배포 설정과 비교한다.

#### 6c. 환경변수 목록

```bash
# Spring Boot
grep -E '\$\{[A-Z_]+' backend/src/main/resources/application*.yml 2>/dev/null

# Node / Next.js
grep -rh "process\.env\." <frontend>/src <frontend>/app <backend>/src 2>/dev/null | \
  grep -oE 'process\.env\.[A-Z_]+' | sort -u

# Python
grep -rh "os.environ\|os.getenv" <backend> 2>/dev/null | grep -oE '"[A-Z_]+"' | sort -u
```

DEPLOY.md의 환경변수 표와 비교한다.

**FAIL:** 코드에서 참조하지만 DEPLOY.md에 미기록 → 표에 추가
**PASS:** 모든 환경변수 기록됨

#### 6d. 인프라 스펙 — 자동 검증 불가

리전·메모리·인스턴스 수 같은 인프라 설정은 코드에서 확인할 수 없으므로 사용자에게 묻는다:

> "DEPLOY.md의 인프라 설정(리전·CPU·메모리·인스턴스 수)이 현재 프로덕션과 일치합니까?"

### Step 7 — 통합 보고서

```markdown
## Update Project Docs 보고서

### 검증 결과 요약

| 문서 | 상태 | 자동 수정 가능 | 질의 필요 |
|------|------|---------------|----------|
| SOURCE_MAP.md | X개 이슈 | N | M |
| DB_SCHEMA.md | X개 이슈 | N | M |
| CLAUDE.md | X개 이슈 | N | M |
| PROJECT_OVERVIEW.md | X개 이슈 | N | M |
| DEPLOY.md | X개 이슈 | N | M |

### 자동 수정 가능

| # | 문서 | 섹션 | 유형 | 상세 |
|---|------|------|------|------|
| 1 | SOURCE_MAP.md | 페이지 라우트 | 누락 | `/new-page` 미등록 |
| 2 | DB_SCHEMA.md | <table> | 컬럼 누락 | `new_column` 미기록 |

### 질의 필요

| # | 문서 | 질문 |
|---|------|------|
| 1 | DB_SCHEMA.md | 새 엔티티 `<entity>`의 접근 범위는? |
| 2 | DEPLOY.md | 인프라 스펙이 현재 프로덕션과 일치합니까? |
```

### Step 8 — 사용자 승인 및 수정

#### 8a. 모호한 항목 질의

"질의 필요" 항목을 `AskUserQuestion`으로 하나씩 묻는다. 사용자 답변을 반영하여 자동 수정 목록에 합친다.

#### 8b. 수정 방식 확인

`AskUserQuestion`:

| 선택지 | 동작 |
|--------|------|
| 전체 수정 | 모든 이슈를 자동 수정 |
| 개별 수정 | 각 이슈마다 진단·수정안 보여주고 승인/거부 |
| 건너뛰기 | 변경 없이 종료 |

#### 8c. 수정 적용

승인된 사항을 `Edit`으로 적용한다. **기존 마크다운 형식 보존**:
- 테이블 열 정렬
- 섹션 순서
- 강조 스타일(굵기, 인용)

### Step 9 — 수정 후 검증

수정된 파일을 다시 읽어 다음을 확인한다:
- 테이블 열 수 일관성
- 닫히지 않은 코드 블록 / 인라인 코드
- 깨진 링크/참조

```markdown
## 수정 완료

| 문서 | 수정 항목 | 검증 |
|------|----------|------|
| SOURCE_MAP.md | N개 | PASS |
| DB_SCHEMA.md | M개 | PASS |

모든 .claude/ 작업 문서가 코드베이스와 동기화되었습니다.
```

---

## 예외사항

다음은 **문제가 아니다**:

1. **사소한 문체 차이** — 기술적으로 정확하면 수정 불필요
2. **인프라 스펙** — 코드에서 확인 불가한 값(리전·메모리·인스턴스 수)은 사용자 승인 없이 변경하지 않음
3. **유틸리티/헬퍼 파일** — 모든 파일을 SOURCE_MAP에 등록할 필요 없음. 주요 진입점(페이지·컴포넌트·서비스·컨트롤러·엔티티)만 대상
4. **테스트 픽스처/목 데이터** — SOURCE_MAP 등록 불필요
5. **접근 범위 같은 비즈니스 규칙** — 코드만으로 판단 어려운 항목은 사용자에게 질의
6. **빌드 도구의 플러그인 버전** — PROJECT_OVERVIEW에 적는 것은 메이저 프레임워크 버전(언어·프레임워크·DB)만 해당
7. **마이그레이션 SQL 본문** — DB_SCHEMA의 마이그레이션 섹션에는 버전·파일명·요약만 기록. SQL 본문은 마이그레이션 파일이 진실의 원천
8. **모노레포가 아닌 프로젝트** — `<frontend>`/`<backend>` 분리가 없으면 단일 디렉토리 기준으로 검사. 표는 그에 맞게 단순화

## Related Files

| File | Purpose |
|------|---------|
| `.claude/CLAUDE.md` | 진입점 — 도메인 규칙, 문서 매핑, 정보 소유권 |
| `.claude/PROJECT_OVERVIEW.md` | 프로젝트 정체성·기술 스택·마일스톤·링크 |
| `.claude/SOURCE_MAP.md` | 소스코드 라우팅 맵 |
| `.claude/DB_SCHEMA.md` | DB 스키마·접근 범위·마이그레이션 |
| `.claude/DEPLOY.md` | 인프라·CI/CD·환경변수·롤백 |
