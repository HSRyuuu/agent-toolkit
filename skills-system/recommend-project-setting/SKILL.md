---
name: recommend-project-setting
description: 이미 일부 세팅이 된 프로젝트에 agent-toolkit의 자산(스킬·작업 문서·LESSONS.md) 중 빠진 것이나 핵심 섹션이 누락된 것이 있는지 점검·추천받고 싶을 때 사용한다. 기본은 read-only 추천이며, 사용자가 명시적으로 설치를 요청해야 파일을 만진다. 빈 프로젝트의 초기 셋업은 `project-setup`을 사용. 트리거 - "프로젝트 세팅 추천", ".claude 보강", "뭐 더 깔면 좋아?", ".claude 점검", "recommend setting", "/recommend-project-setting".
---

# Recommend Project Setting — 진행 중 프로젝트 세팅 추천

이미 어느 정도 세팅이 된 프로젝트를 스캔해서, agent-toolkit의 자산 중 **빠진 것 / 더 보강하면 좋은 것**을 사용자에게 알려주고, 사용자가 고른 것만 설치한다.

## 추천 자산 한눈에 보기

이 스킬이 분석·추천 대상으로 삼는 자산 전체 목록이다. 각 자산의 종류, 한 줄 설명, 적용 시 필요한 세팅을 요약한다.

| 자산 | 종류 | 한 줄 설명 | 적용 시 필요한 세팅 (기본 위치 / 변경 가능 여부) |
|---|---|---|---|
| `manage-skills` | 스킬 | 세션 변경사항 분석 → `verify-*` 스킬 생성/갱신 | `.claude/skills/manage-skills/` (고정) |
| `verify-implementation` | 스킬 | 등록된 모든 `verify-*` 스킬 통합 실행 | `.claude/skills/verify-implementation/` (고정) |
| `update-project-docs` | 스킬 | 작업 문서를 코드와 동기화 | `.claude/skills/update-project-docs/` (고정) |
| `CLAUDE.md` | 작업 문서 | 진입점 — 도메인 규칙·문서 매핑 | 루트 또는 `.claude/` 중 사용자 선택, 문서 매핑 표 채우기 |
| `PROJECT_OVERVIEW.md` | 작업 문서 | 정체성·기술 스택·마일스톤·핵심 링크 | `docs/PROJECT_OVERVIEW.md` (기본, 사용자 변경 가능) |
| `SOURCE_MAP.md` | 작업 문서 | 소스코드 위치 라우팅 맵 | `docs/SOURCE_MAP.md` (기본, 사용자 변경 가능) |
| `DB_SCHEMA.md` | 작업 문서 | DB 테이블·컬럼·접근 범위 | `docs/DB_SCHEMA.md` (기본, 사용자 변경 가능) |
| `DEPLOY.md` | 작업 문서 | 인프라·도메인·환경변수·롤백 | `docs/DEPLOY.md` (기본, 사용자 변경 가능) |
| `DESIGN.md` | 작업 문서 | 디자인 시스템 — 색상·타이포·컴포넌트 | `docs/DESIGN.md` (기본, 사용자 변경 가능) |
| `ADR.md` | 작업 문서 | Architecture Decision Records — 되돌리기 어려운 결정 로그 | `docs/ADR.md` (기본, 사용자 변경 가능) |
| `LESSONS.md` | 자기개선 | 사용자 피드백 누적, 자기개선 순환 | `.claude/LESSONS.md` (고정) + CLAUDE.md에 Self-Improving 섹션 한 줄 추가 |

> 자산별 상세는 아래 "## 자산별 상세" 섹션 참조. 실제 추천 결과는 Step 3에서 생성된다.
>
> **위치 정책** — 작업 문서 6종(PROJECT_OVERVIEW/SOURCE_MAP/DB_SCHEMA/DEPLOY/DESIGN/ADR)의 기본 위치는 `docs/`다. 사용자가 명시적으로 다른 디렉토리를 요청하면 그곳에 설치한다. LESSONS.md와 스킬 3종은 위치 고정. 어디에 설치하든 CLAUDE.md "문서 매핑" 표에는 **실제 경로 그대로** 기록한다.

## 자산별 상세

각 자산이 무엇이고, 어떤 세팅이 필요하고, 대체 가능한지, 어떤 관련 스킬이 동작하는지를 정의한다. Step 3에서 사용자에게 추천을 보여줄 때 이 섹션의 내용을 그대로 활용한다.

### `manage-skills`
- **역할**: 세션 동안 변경된 파일을 분석해 `verify-<area>` 형태의 검증 스킬을 자동 생성·갱신한다. 등록된 스킬 목록을 관리한다.
- **필요한 세팅**:
  - `.claude/skills/manage-skills/` 디렉토리에 SKILL.md 골격 복사
  - 처음 사용 시 등록 테이블이 비어 있는 상태로 시작
- **대체 가능 여부**: 직접 `verify-*` 스킬을 손으로 만들어 관리할 수 있으나, 변경 추적·등록 표 동기화를 모두 수동으로 해야 함 → **사실상 대체 어려움**
- **관련 스킬**: `verify-implementation` (짝으로 동작 — 생성된 스킬을 실행)
- **자동 추천 조건**: `.claude/skills/manage-skills/SKILL.md`가 없을 때

### `verify-implementation`
- **역할**: 등록된 모든 `verify-*` 스킬을 순차 실행하여 통합 검증 보고서를 만든다.
- **필요한 세팅**:
  - `.claude/skills/verify-implementation/` 디렉토리에 SKILL.md 골격 복사
- **대체 가능 여부**: 각 verify 스킬을 개별 실행해도 동작은 같음. 단, 통합 보고서·일괄 수정 흐름이 사라짐.
- **관련 스킬**: `manage-skills` (생성), 등록된 `verify-*` 스킬들 (실행 대상)
- **자동 추천 조건**: `.claude/skills/verify-implementation/SKILL.md`가 없을 때. 단, `manage-skills` 없이 단독 설치는 의미가 약하므로 함께 추천한다.

### `update-project-docs`
- **역할**: 작업 문서(CLAUDE.md, PROJECT_OVERVIEW.md, SOURCE_MAP.md, DB_SCHEMA.md, DEPLOY.md, DESIGN.md — 기본 `docs/` 또는 사용자 지정 위치)가 코드 실제 상태와 어긋나면 동기화한다.
- **필요한 세팅**:
  - `.claude/skills/update-project-docs/` 디렉토리에 SKILL.md 골격 복사
- **대체 가능 여부**: 직접 문서를 수동으로 갱신할 수 있음. 단, 새 파일·마이그레이션·환경변수가 추가될 때마다 수동 추적해야 함.
- **관련 스킬**: 없음 (독립 동작)
- **자동 추천 조건**: 작업 문서가 1개 이상 있을 때 강하게 추천. 작업 문서가 0개면 약한 추천 (먼저 문서를 깔라고 안내).

### `CLAUDE.md`
- **역할**: Claude가 매 세션 가장 먼저 읽는 진입점. 도메인 규칙·문서 매핑·정보 소유권을 정의.
- **필요한 세팅**:
  - 루트 또는 `.claude/`에 파일 생성 (위치는 사용자 선택)
  - "문서 매핑" 표에 다른 자산 등록
  - (선택) Self-Improving 섹션 — LESSONS.md를 함께 깔 때
- **대체 가능 여부**: 다른 진입점 문서로 대체 어려움. **사실상 필수**.
- **관련 스킬**: `update-project-docs`가 동기화. `project-setup`이 설치 시 문서 매핑 자동 채움.
- **자동 추천 조건**: 양쪽 위치(`/CLAUDE.md`, `.claude/CLAUDE.md`)에 모두 없을 때.
- **부분 갭 추천**: 파일은 있으나 다음 핵심 섹션이 빠진 경우 추가 권유:
  - `## Core Principles`
  - `## Workflows`
  - `## 문서 매핑`
  - `### 3. Self-Improvement Loop` (LESSONS.md를 함께 쓸 때)

### `PROJECT_OVERVIEW.md`
- **역할**: 프로젝트의 정체성·기술 스택·마일스톤·핵심 링크. "이 프로젝트가 뭔지" 첫 인상을 주는 문서.
- **필요한 세팅**:
  - `docs/PROJECT_OVERVIEW.md` 파일 생성 (기본 위치, 사용자가 다른 디렉토리 지정 가능)
  - 기술 스택 표·마일스톤·링크 채우기
- **대체 가능 여부**: README.md로 일부 대체 가능. 단, README는 외부 사용자용·이 문서는 에이전트 컨텍스트용이라 분리가 권장.
- **관련 스킬**: `update-project-docs`가 기술 스택 버전 드리프트 검출.
- **자동 추천 조건**: 기본·대체 위치 어느 곳에도 파일이 없을 때. **필수 권장**.

### `SOURCE_MAP.md`
- **역할**: 소스코드 위치를 빠르게 찾기 위한 라우팅 맵. 페이지 라우트·컴포넌트·서비스·엔티티 위치를 표로 정리.
- **필요한 세팅**:
  - `docs/SOURCE_MAP.md` 파일 생성 (기본 위치, 사용자가 다른 디렉토리 지정 가능)
  - 주요 진입점 파일 등록 (전부 등록할 필요 없음)
- **대체 가능 여부**: 코드를 grep으로 찾을 수 있으나, 큰 코드베이스에서 에이전트 토큰 소비를 줄이는 효과가 큼.
- **관련 스킬**: `update-project-docs`가 누락 파일 자동 검출.
- **자동 추천 조건**: 코드베이스에 `frontend/`, `backend/`, `app/`, `src/` 등 명확한 모놀리식/멀티모듈 구조가 있고, 파일 수가 일정 규모 이상일 때 (Step 2의 자동 탐지 결과 기준).

### `DB_SCHEMA.md`
- **역할**: DB 테이블·컬럼·제약·접근 범위·마이그레이션 목록.
- **필요한 세팅**:
  - `docs/DB_SCHEMA.md` 파일 생성 (기본 위치, 사용자가 다른 디렉토리 지정 가능)
  - ER 다이어그램(텍스트) + 테이블 표 + 접근 범위 채우기
- **대체 가능 여부**: 마이그레이션 파일이 진실의 원천이지만, **접근 범위(유저 한정/공유/시스템)와 인덱스 의도는 코드만으로 알 수 없어** 이 문서가 필요.
- **관련 스킬**: `update-project-docs`가 마이그레이션·엔티티·Enum 동기화.
- **자동 추천 조건**: 프로젝트에 `migrations/`, `prisma/`, `db/migrate/`, `alembic/`, `flyway` 등 마이그레이션 디렉토리가 있을 때.

### `DEPLOY.md`
- **역할**: 인프라·도메인·환경변수·CI/CD·롤백 절차. 인시던트 대응 시 가장 먼저 열리는 문서.
- **필요한 세팅**:
  - `docs/DEPLOY.md` 파일 생성 (기본 위치, 사용자가 다른 디렉토리 지정 가능)
  - 환경변수 표(시크릿 값은 적지 않음, 위치만), CI 워크플로 매핑, 롤백 절차 채우기
- **대체 가능 여부**: 외부 운영 위키(Notion 등)로 대체 가능. 단, 에이전트 컨텍스트에서 즉시 참조하려면 이 문서가 유용.
- **관련 스킬**: `update-project-docs`가 환경변수·CI 파일 드리프트 검출.
- **자동 추천 조건**: `.github/workflows/`, `Dockerfile`, `vercel.json`, `cloud-run-*.yaml` 등 배포 설정 파일이 있을 때.

### `DESIGN.md`
- **역할**: 디자인 시스템 — 색상 팔레트·타이포·컴포넌트 스타일·다크 모드.
- **필요한 세팅**:
  - `docs/DESIGN.md` 파일 생성 (기본 위치, 사용자가 다른 디렉토리 지정 가능)
  - 색상 토큰·폰트·컴포넌트 스타일·인터랙션 규칙 채우기
- **대체 가능 여부**: Figma 링크/Storybook으로 대체 가능. 단, 에이전트가 UI 코드를 작성할 때 토큰을 추측하지 않게 하려면 텍스트 문서가 유리.
- **관련 스킬**: 없음 (독립 문서). PROJECT_OVERVIEW.md의 디자인 토큰 섹션이 이 문서를 참조.
- **자동 추천 조건**: 프론트엔드 디렉토리(`frontend/`, `client/`, `web/`, `app/`)가 있고, `tailwind.config.*` 또는 `theme/`/`tokens/` 디렉토리가 있을 때.

### `ADR.md`
- **역할**: 되돌리기 어려운 아키텍처 결정(예: DB 엔진, 프레임워크, 인증 방식)을 한 파일에 로그형으로 누적. 인덱스 표 + 결정별 섹션.
- **필요한 세팅**:
  - `docs/ADR.md` 파일 생성 (기본 위치, 사용자 변경 가능)
  - 첫 결정을 추가할 때 템플릿 0001 항목을 실제 내용으로 교체하고 인덱스 표 갱신
- **대체 가능 여부**: PR 본문·커밋 메시지·외부 위키로 대체 가능. 단, 시간이 지나면 흩어진 결정을 다시 모으기 어렵다 — 한 곳에 누적하는 가치가 큼.
- **관련 스킬**: `update-project-docs`가 인덱스 표 정합성·`Superseded` 누락 같은 정적 점검만 수행 (코드 자동 동기화 대상은 아님).
- **자동 추천 조건**: 다음 신호 중 하나라도 있으면 강하게 추천:
  - `docs/adr/`, `docs/decisions/`, `adr/` 같은 ADR 관습 디렉토리가 이미 존재 (이 경우 단일 파일 ADR.md로 흡수할지 사용자에게 추가 질문)
  - 프로젝트가 일정 규모 이상(서비스가 다중 모듈, 외부 의존성이 다수)이고 ADR.md가 없음
  - 그 외에는 약한 추천 — 모든 프로젝트에 있으면 좋지만 강제하지 않음

### `LESSONS.md`
- **역할**: 사용자 피드백을 형식대로 누적하여 같은 실수를 반복하지 않게 한다. 에이전트 자기개선 순환.
- **필요한 세팅**:
  - `.claude/LESSONS.md` 파일 생성
  - **+ CLAUDE.md "Workflows"의 "Self-Improvement Loop" 항목에 한 줄 안내 추가** (`사용자의 수정사항이 있을 경우 .claude/LESSONS.md에 정해진 패턴으로 업데이트하세요`)
- **대체 가능 여부**: 대체 어려움. 자기개선 순환 자체가 형식이 정해져 있지 않으면 동작하지 않음.
- **관련 스킬**: 없음 (에이전트가 자동 누적). `update-project-docs`의 동기화 대상 아님.
- **자동 추천 조건**: `.claude/LESSONS.md`가 없거나, CLAUDE.md에 Self-Improvement 섹션이 없을 때.

---

## 사용 시점

- 이미 일부 세팅이 된 프로젝트에 "뭐 더 깔면 좋을지" 묻고 싶을 때
- 다른 프로젝트에 적용한 세팅을 이 프로젝트에도 가져오고 싶을 때
- 새 자산(예: DESIGN.md)이 toolkit에 추가됐는지 보고 일괄 점검할 때

> 빈 프로젝트에 처음 세팅을 깔 때는 `/project-setup`이 적합하다. 이 스킬은 **이미 어느 정도 깔린 프로젝트에 누락분을 추천**하는 용도다.

## 사전 조건

- **대상 디렉토리**: git 저장소이거나, 최소한 프로젝트 루트로 명확히 식별 가능해야 한다.
- **템플릿 원본 디렉토리 (필수)**: `${CLAUDE_PLUGIN_ROOT}/templates/project-setup/`
  - 없으면 즉시 중단.

## 대전제

`project-setup`과 다음 5가지 대전제를 따른다:

0. **기본은 read-only 추천이다.** 이 스킬은 "스캔 → 추천 보고"가 기본 동작이다. **사용자가 명시적으로 "적용해줘 / 설치해줘 / 깔아줘"** 라고 의사를 밝히기 전까지는 **대상 프로젝트의 어떤 파일도 생성·수정·삭제하지 않는다.** 추천 보고만으로 스킬 종료가 정상 케이스다.
1. **충돌 시 반드시 묻는다.** 사용자가 명시적으로 설치를 요청한 뒤에도, 대상에 이미 파일이 있으면 `AskUserQuestion`으로 처리 방식을 묻는다 (그대로 두기 / 백업 후 교체 / 병합 / 취소).
2. **세팅 후 무의미해지는 주석은 자동으로 제거한다.** 안내용 HTML 주석·placeholder 행은 설치 후 정리한다. (이 또한 사용자가 설치를 요청한 경우에만 적용)
3. **묻지 않고 설치를 시작하지 않는다.** Step 0에서 호출 의도를 확인하고, Step 4에서 사용자의 명시적 설치 의사를 한 번 더 확인한 뒤에만 진행.
4. **템플릿 파일을 임의로 만들어내지 않는다.** `templates/project-setup/`에 없는 자산은 추천 대상에서 제외한다.

> 대전제 0은 다른 모든 규칙보다 우선한다. 어떤 단계에서든 "사용자가 적용을 명시적으로 요청했는가?"가 불확실하면 즉시 Step 9 (read-only 종료)로 가서 추천만 보고하고 종료한다.

## 워크플로우

### Step 0 — 호출 의도 확인

파일을 만지기 전에 호출 의도를 확인한다.

> **반드시 강조**: 이 스킬의 기본 동작은 **read-only 스캔·추천**이다. Step 0~3까지는 어떤 파일도 만들거나 수정하지 않는다. 설치는 Step 4에서 사용자가 **명시적으로 설치 의사를 밝힌 경우에만** 시작된다 (대전제 0).

- **명시적 호출** — `/recommend-project-setting`, "프로젝트 세팅 추천해줘", ".claude 뭐 더 깔까", "recommend setting" → 곧바로 Step 1
- **암묵적 트리거** — 모호한 표현이거나 description 매칭만으로 도달한 경우 → 다음을 묻고 진행

```
질문: 이 프로젝트의 .claude/ 세팅을 스캔하고 누락된 자산을 추천할까요?
       (스캔만 하고 자동 설치는 하지 않습니다. 추천 보고를 받은 뒤,
        사용자가 명시적으로 "설치/적용해줘"라고 말씀하시기 전까지는
        프로젝트의 어떤 파일도 변경하지 않습니다.)

선택지:
  1. 네, 스캔 진행 (read-only)
  2. 아니오, 이번엔 건너뛰기
```

### Step 1 — 대상 프로젝트 결정

```bash
TARGET="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
echo "스캔 대상: $TARGET"
```

명확하지 않으면 `AskUserQuestion`으로 사용자에게 확인한다.

### Step 2 — 현재 세팅 스캔

대상 프로젝트의 현재 세팅을 두 레벨로 스캔한다.

#### 2a. 파일 존재 스캔

작업 문서 5종은 **기본 위치(`docs/`)와 과거 위치(`.claude/`) 양쪽**을 모두 확인한다. 어느 한 쪽에라도 있으면 "이미 있음"으로 간주하되, 발견된 실제 경로를 그대로 보고한다 (사용자가 옮길지 묻지는 않음 — 추천 단계에서는 read-only).

```bash
# 진입점 (위치 둘 다 확인)
ls "$TARGET/CLAUDE.md" 2>/dev/null
ls "$TARGET/.claude/CLAUDE.md" 2>/dev/null

# 작업 문서 — 기본 docs/ 우선, .claude/ 보조 (사용자가 다른 위치를 쓸 수도 있음)
for doc in PROJECT_OVERVIEW.md SOURCE_MAP.md DB_SCHEMA.md DEPLOY.md DESIGN.md ADR.md; do
  for loc in "docs/$doc" ".claude/$doc"; do
    [ -f "$TARGET/$loc" ] && echo "FOUND: $loc"
  done
done

# ADR — 디렉토리 관습(adr/, decisions/) 별도 탐지: 단일 ADR.md 추천 시 흡수 후보
ls -d "$TARGET/docs/adr" "$TARGET/docs/decisions" "$TARGET/adr" 2>/dev/null

# 자기개선 문서 (위치 고정)
ls "$TARGET/.claude/LESSONS.md" 2>/dev/null

# 스킬 (위치 고정)
ls -d "$TARGET/.claude/skills/manage-skills" 2>/dev/null
ls -d "$TARGET/.claude/skills/verify-implementation" 2>/dev/null
ls -d "$TARGET/.claude/skills/update-project-docs" 2>/dev/null
```

> 사용자가 `wiki/`, `documents/` 같은 비표준 디렉토리에 둔 경우는 자동 탐지하지 않는다 — 이 경우 "없음"으로 보이지만, Step 4(설치 의사 확인) 이후 사용자가 알려주면 그 경로를 PATHS에 반영한다.

#### 2b. CLAUDE.md 핵심 섹션 스캔 (있을 때만)

CLAUDE.md가 존재하면 다음 섹션의 존재 여부를 grep으로 확인:

```bash
CLAUDE_PATH="$TARGET/.claude/CLAUDE.md"
[ ! -f "$CLAUDE_PATH" ] && CLAUDE_PATH="$TARGET/CLAUDE.md"

grep -q "^## Core Principles" "$CLAUDE_PATH" && CORE=yes || CORE=no
grep -q "^## Workflows" "$CLAUDE_PATH" && WF=yes || WF=no
grep -q "^## 문서 매핑\|^## Document Mapping" "$CLAUDE_PATH" && MAP=yes || MAP=no
grep -q "Self-Improvement\|LESSONS" "$CLAUDE_PATH" && SI=yes || SI=no
```

#### 2c. 프로젝트 컨텍스트 자동 탐지

추천 강도(자동 추천 조건) 판정에 쓸 신호를 모은다:

```bash
# 마이그레이션 / DB
ls -d "$TARGET"/migrations "$TARGET"/prisma/migrations "$TARGET"/db/migrate "$TARGET"/alembic 2>/dev/null
ls "$TARGET"/backend/src/main/resources/db/migration/ 2>/dev/null

# 프론트엔드
ls -d "$TARGET"/frontend "$TARGET"/client "$TARGET"/web "$TARGET"/app 2>/dev/null
ls "$TARGET"/tailwind.config.* "$TARGET"/frontend/tailwind.config.* 2>/dev/null

# 배포
ls "$TARGET"/.github/workflows/ "$TARGET"/Dockerfile "$TARGET"/vercel.json "$TARGET"/fly.toml 2>/dev/null
```

탐지 결과는 Step 3 추천 강도 결정에 사용한다.

### Step 3 — 추천 결과 표시

수집된 데이터를 바탕으로 자산별 상태와 추천 등급을 한 표로 만든다.

**추천 등급:**
- **🟢 강력 추천** — 자동 추천 조건이 충족되고 현재 없음 (예: 마이그레이션 디렉토리가 있는데 DB_SCHEMA.md가 없음)
- **🟡 추천** — 자동 추천 조건은 약하지만 일반적으로 있으면 좋은 항목
- **⚪ 옵션** — 프로젝트 성격에 따라 선택 (자동 추천 조건이 충족되지 않음)
- **✅ 이미 있음** — 설치되어 있고 핵심 섹션도 충족
- **🟠 부분 갭** — 파일은 있으나 핵심 섹션이 빠짐 (CLAUDE.md 한정)

```markdown
## 현재 세팅 분석 결과

**대상:** `<TARGET>`

### 자산별 상태

| 자산 | 종류 | 이미 있음 | 추천 등급 | 이유 / 부분 갭 | 대체 가능 | 관련 스킬 |
|---|---|---|---|---|---|---|
| `manage-skills` | 스킬 | ❌ | 🟡 추천 | 검증 자동화 누락 | 어려움 | verify-implementation 짝 |
| `verify-implementation` | 스킬 | ❌ | 🟡 추천 | manage-skills와 함께 | 어려움 | manage-skills |
| `update-project-docs` | 스킬 | ❌ | 🟢 강력 추천 | 작업 문서 N개 있음 | 어려움 | (독립) |
| `CLAUDE.md` | 작업 문서 | ✅ (.claude/) | 🟠 부분 갭 | Self-Improvement 섹션 없음 | 어려움 | project-setup 설치 |
| `PROJECT_OVERVIEW.md` | 작업 문서 | ✅ | ✅ 이미 있음 | — | README로 일부 | update-project-docs 동기화 |
| `SOURCE_MAP.md` | 작업 문서 | ❌ | 🟢 강력 추천 | 모놀리식 구조 감지 | grep으로 대체 | update-project-docs 동기화 |
| `DB_SCHEMA.md` | 작업 문서 | ❌ | 🟢 강력 추천 | prisma/migrations 감지 | 마이그레이션이 원천 | update-project-docs 동기화 |
| `DEPLOY.md` | 작업 문서 | ❌ | 🟢 강력 추천 | .github/workflows 감지 | 외부 위키로 대체 | update-project-docs 동기화 |
| `DESIGN.md` | 작업 문서 | ❌ | 🟢 강력 추천 | tailwind.config.ts 감지 | Figma로 대체 | (독립) |
| `ADR.md` | 작업 문서 | ❌ | 🟡 추천 | (또는 🟢 — 다중 모듈/`docs/adr/` 흡수 후보 감지 시) | PR/위키로 대체 | update-project-docs 정적 점검 |
| `LESSONS.md` | 자기개선 | ❌ | 🟡 추천 | + CLAUDE.md 한 줄 추가 필요 | 어려움 | (자동 누적) |

### 부분 갭 상세 (CLAUDE.md)

- ❌ `## Core Principles` 없음
- ✅ `## Workflows` 있음
- ✅ `## 문서 매핑` 있음
- ❌ Self-Improvement 섹션 없음 (LESSONS.md를 함께 쓰려면 추가 권장)
```

> 표는 실제 스캔 결과로 채운다. 위 형식은 예시.

### Step 4 — 설치 의사 확인 + 사용자 선택

> **대전제 0 적용 지점**: 이 스킬은 Step 3에서 추천 보고를 보여주는 것까지가 기본 동작이다. **사용자가 이 단계에서 명시적으로 설치를 요청하지 않으면, 어떤 파일도 만지지 않고 Step 9(read-only 보고)로 직행한다.**

#### 4a. 설치 의사 게이트 (필수)

추천 보고를 보여준 직후, **첫 번째 질문은 "설치를 진행할지 여부"** 다. `AskUserQuestion`:

```
질문: 위 추천 보고를 보셨습니다. 이 중 일부 또는 전부를 실제로 이 프로젝트에
       설치/적용할까요? (지금까지는 어떤 파일도 변경되지 않았습니다.)

선택지:
  1. 아니오, 보고만 받고 종료 (read-only) ← 기본
  2. 네, 어떤 항목을 깔지 골라보겠습니다
```

> 이 게이트는 **생략 불가**다. 사용자가 처음 트리거에서 "추천해줘"라고만 했다면
> 이 단계에서 명시적으로 "설치하겠다"는 의사를 받기 전까지 어떤 파일도 만지지 않는다.
>
> 사용자의 원래 메시지에 이미 **"설치해줘 / 적용해줘 / 깔아줘 / install / apply"** 같은
> 명시적 적용 의사가 포함되어 있었다면 4a를 생략하고 곧바로 4b로 넘어갈 수 있다.
>
> **불확실하면 4a를 반드시 묻는다.**

옵션 1을 선택하면 즉시 Step 9 (read-only 보고)로 이동한다. 그 외 어떤 변경도 일어나지 않는다.

#### 4b. 설치 항목 선택

4a에서 옵션 2를 선택했거나 사용자가 처음부터 명시적 적용 의사를 밝혔던 경우에만 진행한다.

```
선택 방식:
  1. 🟢 강력 추천 항목만 설치
  2. 🟢 + 🟡 + 🟠 (부분 갭 보정 포함) 설치 ← 권장
  3. 전체 추천 (옵션 ⚪까지)
  4. 개별 선택 — 각 항목마다 설치 / 건너뛰기
  5. 역시 설치하지 않고 종료 (read-only로 회귀)
  6. 취소
```

옵션 5/6을 선택하면 즉시 Step 9 (read-only 보고)로 이동한다.

선택 후 SELECTED 리스트를 만든다. CLAUDE.md가 SELECTED에 포함되고 양쪽 위치에 모두 없으면 추가로 묻는다: "루트 / `.claude/` 중 어디에 둘까요?"

#### 4c. 설치 위치 공지 + 변경 확인 (대전제 1·3)

`project-setup`의 Step 3.5와 동일한 절차다. **실제 파일을 만지기 전에** 각 자산이 어떤 경로에 생기는지 사용자에게 공지하고 동의를 받는다.

PATHS 맵 초기값:

| 자산 | 기본 경로 | 변경 가능? |
|---|---|---|
| 스킬 3종 | `<TARGET>/.claude/skills/<key>/` | 불가 |
| `CLAUDE.md` | 4b에서 사용자가 고른 위치 (또는 기존 발견 위치 유지) | 가능 (루트 ↔ `.claude/`) |
| `PROJECT_OVERVIEW.md` | `<TARGET>/docs/PROJECT_OVERVIEW.md` | 가능 |
| `SOURCE_MAP.md` | `<TARGET>/docs/SOURCE_MAP.md` | 가능 |
| `DB_SCHEMA.md` | `<TARGET>/docs/DB_SCHEMA.md` | 가능 |
| `DEPLOY.md` | `<TARGET>/docs/DEPLOY.md` | 가능 |
| `DESIGN.md` | `<TARGET>/docs/DESIGN.md` | 가능 |
| `ADR.md` | `<TARGET>/docs/ADR.md` | 가능 |
| `LESSONS.md` | `<TARGET>/.claude/LESSONS.md` | **불가 (고정)** |

> Step 2a 스캔에서 작업 문서가 이미 `.claude/` 등 비-기본 위치에서 발견됐다면, **"부분 갭 보강"으로 설치하는 경우에 한해** 그 기존 경로를 PATHS의 기본값으로 미리 채운다(같은 자산을 두 곳에 만들지 않기 위함). 신규 설치라면 `docs/`를 기본으로 둔다.

PATHS 맵을 사용자에게 공지하고 변경 의사를 묻는다 (`AskUserQuestion`):

```
이번 설치로 다음 위치에 파일이 생성됩니다:
  <PATHS 맵 출력 — project-setup Step 3.5b와 동일 형식>

질문: 위 위치로 진행할까요?

선택지:
  1. 네, 위 경로 그대로 진행
  2. 일부 또는 전체 위치를 바꾸겠습니다
  3. 취소 (read-only로 회귀)
```

옵션 2를 선택하면 사용자가 변경하고 싶은 자산을 자유 텍스트로 받아 PATHS를 갱신하고 다시 묻는다. **LESSONS.md/스킬 3종을 옮기려는 요청은 정중히 거절**하고 기본 위치를 유지한다.

옵션 3을 선택하면 즉시 Step 9 (read-only 종료)로 이동.

### Step 5 — 충돌 검사 + 처리 방식 결정 (대전제 1)

`project-setup`의 Step 4와 동일한 절차를 따른다. 핵심만:

#### 5a. CLAUDE.md 양쪽 위치 동시 존재
- 권장 위치는 `.claude/CLAUDE.md`. 양쪽에 있으면 정리 옵션을 묻는다.

#### 5b. 충돌 자산 처리 방식
충돌이 1개 이상이면 `AskUserQuestion`:

```
처리 방식:
  1. 그대로 두기                   — 기존 파일 유지, 이 자산은 설치하지 않음
  2. 백업 후 새 템플릿으로 교체    — .bak.<timestamp> 백업 후 깖
  3. 병합                          — 기존 파일 유지 + 템플릿 일부 추가
  4. 자산별 개별 결정
  5. 취소
```

#### 5c. 병합 옵션의 자산별 의미
- **CLAUDE.md** — 본문은 반드시 보존. 사용자가 누락 섹션(Core Principles / Workflows / 문서 매핑 / Self-Improvement)만 골라 추가 가능. 같은 헤더가 이미 있으면 한 번 더 확인.
- **PROJECT_OVERVIEW.md / SOURCE_MAP.md / DB_SCHEMA.md / DEPLOY.md / DESIGN.md** — 본문 보존, 템플릿에는 있지만 기존엔 없는 `##` 섹션만 끝에 추가.
- **ADR.md** — 결정 로그라 "템플릿 섹션 끝에 붙이기"가 인덱스 표/번호 체계를 깬다. 병합 의미 없음 — "그대로 두기" / "백업 후 교체"만 가능.
- **LESSONS.md / 스킬** — 디렉토리·자동 누적 자산이라 병합 의미 없음. "그대로 두기" / "백업 후 교체"만 가능.

### Step 6 — 디렉토리 생성

Step 4c에서 확정된 PATHS 맵의 부모 디렉토리만 생성한다. 작업 문서가 기본 `docs/`로 가든 사용자 지정 위치로 가든 동일한 규칙으로 처리된다.

```bash
# 스킬은 항상 .claude/skills/ 아래
[ ${#SELECTED_SKILLS[@]} -gt 0 ] && mkdir -p "$TARGET/.claude/skills"

# CLAUDE.md(.claude/ 위치 선택 시) · LESSONS.md
if { [ -n "${PATHS[CLAUDE.md]:-}" ] && [[ "${PATHS[CLAUDE.md]}" == *"/.claude/"* ]]; } \
     || [ -n "${PATHS[LESSONS.md]:-}" ]; then
  mkdir -p "$TARGET/.claude"
fi

# 작업 문서: PATHS 부모 디렉토리만 생성
for doc in PROJECT_OVERVIEW.md SOURCE_MAP.md DB_SCHEMA.md DEPLOY.md DESIGN.md ADR.md; do
  [ -n "${PATHS[$doc]:-}" ] && mkdir -p "$(dirname "${PATHS[$doc]}")"
done
```

### Step 7 — 선택 자산 설치

자산 종류별로 처리. **모두 Step 5에서 결정된 방식을 따른다.**

**스킬**:

설치 전 글로벌 동명 스킬 검사:
```bash
ls ~/.claude/plugins/*/skills/<key>/ 2>/dev/null
```
존재하면 사용자에게 묻고 결정 (오버라이드 / 이름 변경 / 스킵).

이후 복사:
```bash
cp -r "$TEMPLATE_DIR/<key>" "$TARGET/.claude/skills/<key 또는 변경된 이름>"
```

**문서 (CLAUDE.md 외 단일 파일)**:
- "백업 후 교체": `cp <dest> <dest>.bak.$(date +%s) && cp <src> <dest>`
- "병합": Step 5c 규칙대로 헤더 단위 추가
- "그대로 두기": 아무것도 하지 않음

**CLAUDE.md**: 위와 동일하되 위치(루트/.claude/)는 사용자 선택대로.

**LESSONS.md 특수 처리** — LESSONS.md를 새로 깔거나 CLAUDE.md에 Self-Improvement가 없는 경우, CLAUDE.md "Workflows" 섹션에 다음 한 줄을 추가할지 묻는다:

```markdown
### N. Self-Improvement Loop

- 사용자의 수정사항이 있을 경우 **`.claude/LESSONS.md`** 에 정해진 패턴으로 업데이트하세요.
- 같은 실수를 반복하지 않도록 스스로 규칙을 정하세요.
- 세션 시작 시 LESSONS 내용을 리뷰하세요.
```

이미 있으면 추가하지 않는다.

### Step 8 — CLAUDE.md 문서 매핑 갱신

이번 설치로 새로 들어온 자산(스킬·작업 문서·LESSONS.md)이 있으면 CLAUDE.md "문서 매핑" 표에 행을 **추가**한다 (이미 있는 행은 건드리지 않음). CLAUDE.md를 이번에 새로 깔았다면 `project-setup`의 Step 7과 동일한 절차로 표 전체를 채운다.

**중요 — 표에 적는 경로는 PATHS 맵의 실제 설치 경로 그대로.** 기본 `docs/`에 깔았으면 `docs/<file>`, 사용자가 `wiki/`로 옮겼으면 `wiki/<file>`로 적는다. CLAUDE.md만 보고 모든 문서를 찾을 수 있어야 한다.

예시 — 사용자가 `PROJECT_OVERVIEW.md`만 `wiki/`로, 나머지는 기본 `docs/`로 두고 LESSONS.md도 함께 깐 경우:

```markdown
| 문서 | 용도 |
|---|---|
| `wiki/PROJECT_OVERVIEW.md` | 프로젝트 정체성·기술 스택·마일스톤·핵심 링크 |
| `docs/SOURCE_MAP.md` | 소스코드 위치 라우팅 맵 |
| `.claude/LESSONS.md` | 사용자 피드백 누적, 자기개선 순환 |
```

> CLAUDE.md가 SELECTED에 없거나, 사용자가 5c에서 "문서 매핑 병합 거부"를 선택했다면 이 Step을 건너뛴다.

### Step 9 — 보고

두 가지 형태가 있다. **read-only 종료** vs **설치 후 종료**.

#### 9a. read-only 종료 (Step 4a에서 옵션 1 또는 4b에서 옵션 5/6 선택 시)

```markdown
## Recommend Project Setting — read-only 보고 종료

**대상:** `<project-root>`

**상태:** 사용자가 설치를 명시적으로 요청하지 않아 **어떤 파일도 변경되지 않았습니다.**

**추천 요약:** (Step 3 표 재인용)
- 🟢 강력 추천: <N>건
- 🟡 추천: <N>건
- 🟠 부분 갭: <N>건
- ⚪ 옵션: <N>건

**나중에 설치하려면:**
- `/recommend-project-setting`을 다시 실행하고 Step 4a에서 "설치 진행"을 선택
- 또는 처음부터 "프로젝트 세팅 추천하고 강력 추천 항목 설치까지 해줘" 처럼 명시적 적용 의사를 같이 전달
```

#### 9b. 설치 후 종료

```markdown
## Recommend Project Setting 완료

**대상:** `<project-root>`

**스캔 결과 요약:**
- 이미 있던 자산: <개수>
- 신규 설치: <개수>
- 부분 갭 보정 (병합): <개수>
- 사용자가 스킵: <개수>

**신규 설치된 자산:** (PATHS 맵의 실제 경로 그대로)
- `.claude/skills/<key>/SKILL.md`
- `docs/<doc>` (기본 위치) 또는 `<사용자 지정 경로>/<doc>` ...
- `.claude/LESSONS.md` (위치 고정, 설치된 경우)

**병합으로 추가된 섹션:**
- `CLAUDE.md`: + Self-Improvement Loop 섹션
- `PROJECT_OVERVIEW.md`: + 디자인/UX 토큰 섹션 (템플릿 기준)

**백업된 파일:** (`.bak.<timestamp>`)
- ...

**그대로 둔 자산 (사용자 선택):**
- `docs/DESIGN.md` (이미 있어 그대로 둠)

**메뉴에서 제외된 자산:** (템플릿에 원본이 없어 후보에서 제외된 항목)

**외부 동명 스킬 알림:** (있는 경우)
- `<key>` — `<외부 위치>`에도 존재. 이번 설치로 프로젝트 로컬이 우선됨.

**다음 단계:**
1. 새 Claude Code 세션에서 설치된 스킬이 로드됩니다.
2. 새 문서의 placeholder를 프로젝트 정보로 채우세요.
3. `update-project-docs`를 함께 깔았다면 코드와 문서가 어긋날 때 `/update-project-docs`로 동기화하세요.
4. 다시 보강이 필요하면 언제든 `/recommend-project-setting`을 다시 실행하세요.
```

> 보고서의 각 섹션은 **실제 일어난 일만** 나열한다.

## project-setup과의 차이

| 항목 | `project-setup` | `recommend-project-setting` |
|---|---|---|
| 가정 | 빈 / 신규 프로젝트 | 이미 일부 세팅된 프로젝트 |
| 핵심 가치 | 카탈로그를 보여주고 골격을 깔아준다 | 현재 상태를 스캔하고 누락분을 추천한다 |
| **기본 동작** | 설치 지향 (사용자 승인 후 깖) | **read-only 추천** (명시적 설치 요청이 없으면 변경 없음) |
| 사용자 관문 | "전체/스킬만/문서만/개별" 메뉴 | (1) 설치 의사 게이트 → (2) "강력추천/추천+부분갭/전체/개별/보고만" 메뉴 |
| 부분 갭 분석 | 없음 | 있음 (CLAUDE.md 핵심 섹션 누락 검출 등) |
| 추천 등급 | 없음 (모두 동등 선택지) | 🟢🟡⚪ 등급 표시 |
| read-only 모드 | 없음 | **기본값**. Step 4a에서 명시적 설치 의사가 없으면 자동 적용 |
| 충돌 처리 | 동일 (대전제 1) | 동일 (대전제 1). 단 설치 게이트(대전제 0)를 통과한 뒤에만 도달 |

두 스킬은 **자산 카탈로그·설치 로직을 공유**한다. 사용자가 어느 단계에 있느냐에 따라 다른 입구를 제공할 뿐이다. 결정적 차이는 **기본 동작의 안전성** — `recommend-project-setting`은 명시적 설치 요청 없이는 어떤 파일도 만지지 않는다.

## 예외사항

다음은 **문제가 아니다**:

1. **추천 결과가 비어 있음** — 모든 자산이 이미 깔려 있고 부분 갭도 없으면 보고만 하고 종료. 오류 아님.
2. **사용자가 "보고만 받고 종료"를 선택 (Step 4a 옵션 1)** — **가장 흔한 정상 케이스**. read-only가 기본 동작이다.
3. **사용자가 추천만 요청하고 적용 의사를 밝히지 않음** — Step 4a 게이트에서 옵션 1로 종료. 어떤 파일도 변경되지 않는다. 정상.
4. **자동 추천 조건은 충족되지만 사용자가 명시적으로 거부** — 권유는 한 번만. 강제하지 않는다.
5. **CLAUDE.md가 양쪽 위치에 동시 존재** — Step 5a에서 사용자에게 묻고 정리. (단 사용자가 Step 4a를 통과한 경우에만 도달)
6. **다른 플러그인에 같은 이름 스킬이 있음** — Step 7에서 사용자에게 묻고 결정. (단 사용자가 Step 4a를 통과한 경우에만 도달)

## Related Files

| File | Purpose |
|------|---------|
| `templates/project-setup/` | 추천·설치할 자산 원본 (`project-setup`과 공유) |
| `skills-system/project-setup/SKILL.md` | 빈 프로젝트용 자매 스킬 (자산 카탈로그·설치 로직 공유) |
| `<target>/.claude/skills/<key>/SKILL.md` | 설치 결과물 (스킬, 위치 고정) |
| `<target>/docs/<doc>` (기본 / 사용자 지정 시 다른 경로) | 설치 결과물 (작업 문서 5종) |
| `<target>/.claude/LESSONS.md` | 설치 결과물 (자기개선, 위치 고정) |
| `<target>/CLAUDE.md` 또는 `<target>/.claude/CLAUDE.md` | 신규 설치되거나 Step 5c·8에서 일부 섹션이 병합된 결과물 |
