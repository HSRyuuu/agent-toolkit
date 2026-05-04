---
name: project-setup
description: 이용 가능한 스킬·문서 골격을 사용자에게 보여주고, 사용자가 선택한 항목만 대상 프로젝트의 `.claude/`에 설치합니다. 선택지는 검증·관리 스킬 3종(manage-skills, verify-implementation, update-project-docs), 코드와 동기화하는 작업 문서 5종(CLAUDE.md, PROJECT_OVERVIEW.md, SOURCE_MAP.md, DB_SCHEMA.md, DEPLOY.md, DESIGN.md), 에이전트가 자기개선용으로 자동 누적하는 LESSONS.md. CLAUDE.md와 PROJECT_OVERVIEW.md는 필수로 권장하며 나머지는 선택. agent-toolkit 플러그인의 `templates/project-setup/` 디렉토리를 골격 원본으로 사용하며 그 디렉토리가 없으면 동작하지 않습니다. 기존 파일이 있으면 절대 임의로 덮어쓰지 않고 반드시 사용자에게 묻습니다. CLAUDE.md를 설치할 경우 사용자가 선택한 문서만 "문서 매핑" 표에 남도록 자동 정리합니다. 트리거 - "프로젝트 셋업", "검증 스킬 설치", "manage-skills 설치", "verify-implementation 설치", "update-project-docs 설치", "프로젝트 초기화", "/project-setup".
---

# Project Setup — 검증 스킬·작업 문서 골격 설치

새 프로젝트(또는 기존 프로젝트)에 검증 스킬·작업 문서 골격을 선택 설치하여, 해당 프로젝트에서 convention 검증 워크플로우와 에이전트 작업 문서 사이클을 즉시 사용할 수 있게 만든다.

## 대전제

이 스킬 전반에 적용되는 절대 규칙. 각 Step에서 다시 반복하지 않으므로 여기서 한 번 명시한다.

1. **충돌 시 반드시 묻는다.** 대상 경로에 이미 파일/디렉토리가 존재하면 어떤 자산이든 `AskUserQuestion`으로 처리 방식을 묻고 결정한다. 묻지 않고 덮어쓰지 않는다. 이 규칙은 스킬·문서·CLAUDE.md 모두에 동일하게 적용된다.
2. **세팅 후 무의미해지는 주석은 자동으로 제거한다.** 템플릿에 들어 있던 안내용 HTML 주석(`<!-- 이 표는 형식 예시... -->` 같은 것)과 placeholder 행(`<...>`이나 `{...}`)은 설치 후 제거하거나 실제 값으로 채운다. 설치 결과물에 작성 안내문이 남아 있으면 안 된다.
3. **묻지 않고 설치를 시작하지 않는다.** Step 0에서 호출 의도를 검증하기 전에는 어떤 파일 작업도 하지 않는다.
4. **템플릿 파일을 임의로 만들어내지 않는다.** `templates/project-setup/`에 없는 자산은 메뉴에서 제외한다. 자체 생성하거나 다른 경로에서 가져오지 않는다.

## 이용 가능한 자산

이 스킬이 대상 프로젝트에 설치할 수 있는 **선택지**다. 각 자산의 성격과 기본 권장 여부:

### 스킬 (선택 시 `.claude/skills/`에 설치)

| 키 | 스킬 | 역할 | 기본 권장 |
|----|------|------|---------|
| `s/manage-skills` | `manage-skills` | 세션 변경사항을 분석해 `verify-*` 스킬을 생성/갱신. 등록된 검증 스킬 목록을 관리. | 선택 |
| `s/verify-implementation` | `verify-implementation` | 등록된 모든 `verify-*` 스킬을 순차 실행하여 통합 검증 보고서 생성. | 선택 |
| `s/update-project-docs` | `update-project-docs` | 작업 문서(기본 `docs/` 또는 사용자 지정 위치)를 코드베이스 실제 상태와 비교하여 드리프트를 동기화. | 선택 |

`manage-skills`/`verify-implementation`은 짝으로 동작한다 — 생성한 `verify-*`를 통합 실행한다. `update-project-docs`는 독립적으로 동작한다.

### 작업 문서 (기본 `docs/` 아래에 설치, 사용자가 다른 위치 지정 가능. CLAUDE.md만 별도 — 루트 또는 `.claude/`)

코드와 동기화되어야 하는 문서. `update-project-docs` 스킬의 검증 대상.

| 키 | 문서 | 역할 | 기본 설치 위치 | 기본 권장 |
|----|------|------|---------------|---------|
| `d/CLAUDE.md` | `CLAUDE.md` | 프로젝트 진입점 — 도메인 규칙·문서 매핑·정보 소유권 | 루트 또는 `.claude/` (사용자 선택) | **필수 권장** |
| `d/PROJECT_OVERVIEW.md` | `PROJECT_OVERVIEW.md` | 프로젝트 정체성·기술 스택·마일스톤·핵심 링크 | `docs/PROJECT_OVERVIEW.md` | **필수 권장** |
| `d/SOURCE_MAP.md` | `SOURCE_MAP.md` | 소스코드 위치 라우팅 맵 | `docs/SOURCE_MAP.md` | 선택 |
| `d/DB_SCHEMA.md` | `DB_SCHEMA.md` | DB 테이블·컬럼·제약·접근 범위 | `docs/DB_SCHEMA.md` | 선택 |
| `d/DEPLOY.md` | `DEPLOY.md` | 인프라·도메인·환경변수·롤백 절차 | `docs/DEPLOY.md` | 선택 |
| `d/DESIGN.md` | `DESIGN.md` | 디자인 시스템 — 색상 팔레트·타이포·컴포넌트 스타일·다크 모드 | `docs/DESIGN.md` | 선택 |
| `d/ADR.md` | `ADR.md` | Architecture Decision Records — 되돌리기 어려운 결정 로그 | `docs/ADR.md` | 선택 |

> **위치 정책** — 작업 문서 6종(PROJECT_OVERVIEW/SOURCE_MAP/DB_SCHEMA/DEPLOY/DESIGN/ADR)의 **기본 위치는 `docs/`**다. 사용자가 명시적으로 다른 디렉토리(예: `.claude/`, `documents/`, `wiki/`)를 요청하면 그 위치에 설치한다. CLAUDE.md만 루트 vs `.claude/` 사이에서 사용자가 고르며, `docs/`는 권장 대상이 아니다. 어떤 위치든 최종 CLAUDE.md "문서 매핑" 표에는 **실제 설치된 경로 그대로** 기록된다.

> **CLAUDE.md / PROJECT_OVERVIEW.md는 필수 권장**이다. 이 두 문서는 다른 모든 자산이 의존하는 기본 진입점이므로 메뉴에서 기본 ON 상태로 제시한다. 사용자가 명시적으로 빼면 빼되, 이미 존재하면 그대로 유지하고 병합 여부를 묻는다.

### 자기개선 문서 (선택 시 `.claude/`에 설치, 별도 카테고리)

에이전트가 사용자 피드백을 받아 **자동으로 누적**한다. `update-project-docs`의 동기화 대상이 **아니다** (코드 드리프트와 무관).

| 키 | 문서 | 역할 |
|----|------|------|
| `l/LESSONS.md` | `LESSONS.md` | 자기개선 순환 — 사용자 피드백 누적·규칙화·반복 적용·격상 |

---

모두 **빈 골격(placeholder 포함)** 상태로 설치된다. 각 문서는 사용자가 채워야 한다 — 이 스킬은 임의로 채우지 않는다. 이미 존재하는 파일은 사용자에게 묻지 않고 절대 덮어쓰지 않는다 (대전제 1).

## 사용 시점

- 새 프로젝트를 시작할 때 — 기본 작업 문서·검증 인프라를 한 번에 깔고 싶을 때
- 기존 프로젝트에 검증 워크플로우를 도입할 때
- 다른 프로젝트에서 같은 패턴을 재사용하고 싶을 때

## 사전 조건

- **대상 디렉토리**: git 저장소이거나, 최소한 프로젝트 루트로 명확히 식별 가능해야 한다.
- **템플릿 원본 디렉토리 (필수)**: `${CLAUDE_PLUGIN_ROOT}/templates/project-setup/`
  - 이 디렉토리 자체가 없으면 스킬은 **즉시 중단**한다.
- **템플릿 내 자산은 모두 선택지**: 위 디렉토리에 있는 자산 중 일부가 누락되어 있어도 중단하지 않는다 — 누락된 자산은 메뉴에서 제외하고 진행한다 (Step 2 누락 알림 형식 참고). 단, 카탈로그가 완전히 비면 중단한다.

> `${CLAUDE_PLUGIN_ROOT}`는 Claude Code가 이 plugin의 skill을 실행할 때 자동 주입하는 환경변수다. 절대경로를 하드코딩하면 plugin을 다른 위치로 옮길 때 깨진다.

## 워크플로우

### Step 0 — 호출 의도 확인 (필수, 가장 먼저)

이 스킬은 **대상 프로젝트의 `.claude/`에 파일을 복사하는 부수효과**가 있다. 따라서 모델이 description 매칭으로 자동 트리거한 경우와, 사용자가 직접 부른 경우를 구분해야 한다.

**판정 기준:**

- **명시적 호출** — 사용자 메시지에 다음 중 하나가 포함된 경우, 곧바로 Step 1로 진행한다:
  - `/project-setup` (슬래시 커맨드)
  - "project-setup 실행", "project-setup 돌려"
  - "manage-skills 설치", "verify-implementation 설치", "검증 스킬 설치"
  - "프로젝트 셋업해줘", "프로젝트 초기화해줘"
  - 그 밖에 사용자가 **이 스킬의 동작을 인지하고 호출한 의도가 명확한** 표현
- **암묵적 트리거** — 사용자가 "이 프로젝트 정리하자", "셋업하자" 같은 모호한 표현을 썼거나, 모델이 description 매칭만으로 이 스킬에 도달한 경우

**암묵적 트리거인 경우, 작업을 시작하지 말고 먼저 묻는다** (`AskUserQuestion`):

```
질문: 이 프로젝트에 검증 스킬·작업 문서 골격을 설치할까요?
       (`<TARGET>/.claude/` 아래에 선택한 자산이 새로 생깁니다)

선택지:
  1. 네, 설치 진행 (Step 1부터 계속)
  2. 아니오, 이번엔 건너뛰기
  3. 자세한 설명을 보고 결정 (이 SKILL.md의 "이용 가능한 자산" 섹션을 보여주고 다시 물음)
```

사용자가 "1"을 고르면 Step 1로 진행, "2"면 종료, "3"이면 안내 후 다시 묻는다.

**대전제 3 — 묻지 않고 어떤 파일 작업도 시작하지 않는다.**

### Step 1 — 대상 프로젝트 결정

다음 우선순위로 대상 프로젝트 루트를 결정한다:

1. 사용자가 인수로 경로를 지정한 경우 → 그 경로
2. 현재 working directory가 git 저장소인 경우 → `git rev-parse --show-toplevel`
3. 그 외 → 현재 working directory를 사용하되 사용자에게 확인

```bash
TARGET="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
echo "설치 대상: $TARGET"
```

명확하지 않으면 `AskUserQuestion`으로 사용자에게 확인한다.

### Step 2 — 템플릿 폴더 검증 + 이용 가능 자산 카탈로그

먼저 템플릿 루트 디렉토리 존재 여부를 검사한다. **없으면 즉시 중단**한다.

```bash
TEMPLATE_DIR="${CLAUDE_PLUGIN_ROOT}/templates/project-setup"

if [ ! -d "$TEMPLATE_DIR" ]; then
  echo "ABORT: 템플릿 디렉토리가 없습니다: $TEMPLATE_DIR" >&2
  exit 1
fi
```

다음으로 **이용 가능 자산 카탈로그**를 구성한다. 모델은 카탈로그를 다음 세 그룹으로 메모리에 보관한다:

**스킬 후보** (각 항목: 키, 원본 디렉토리, 설치 대상)

| 키 | 원본 (있을 때만 후보) | 설치 대상 |
|----|---------------------|----------|
| `manage-skills` | `$TEMPLATE_DIR/manage-skills/` | `$TARGET/.claude/skills/manage-skills/` |
| `verify-implementation` | `$TEMPLATE_DIR/verify-implementation/` | `$TARGET/.claude/skills/verify-implementation/` |
| `update-project-docs` | `$TEMPLATE_DIR/update-project-docs/` | `$TARGET/.claude/skills/update-project-docs/` |

**작업 문서 후보** (코드와 동기화되는 문서)

| 키 | 원본 (있을 때만 후보) | 기본 설치 대상 | 권장 |
|----|---------------------|---------------|-----|
| `CLAUDE.md` | `$TEMPLATE_DIR/CLAUDE.md` | `$TARGET/CLAUDE.md` 또는 `$TARGET/.claude/CLAUDE.md` (사용자 선택) | 필수 |
| `PROJECT_OVERVIEW.md` | `$TEMPLATE_DIR/PROJECT_OVERVIEW.md` | `$TARGET/docs/PROJECT_OVERVIEW.md` (기본, 사용자 변경 가능) | 필수 |
| `SOURCE_MAP.md` | `$TEMPLATE_DIR/SOURCE_MAP.md` | `$TARGET/docs/SOURCE_MAP.md` (기본, 사용자 변경 가능) | 선택 |
| `DB_SCHEMA.md` | `$TEMPLATE_DIR/DB_SCHEMA.md` | `$TARGET/docs/DB_SCHEMA.md` (기본, 사용자 변경 가능) | 선택 |
| `DEPLOY.md` | `$TEMPLATE_DIR/DEPLOY.md` | `$TARGET/docs/DEPLOY.md` (기본, 사용자 변경 가능) | 선택 |
| `DESIGN.md` | `$TEMPLATE_DIR/DESIGN.md` | `$TARGET/docs/DESIGN.md` (기본, 사용자 변경 가능) | 선택 |
| `ADR.md` | `$TEMPLATE_DIR/ADR.md` | `$TARGET/docs/ADR.md` (기본, 사용자 변경 가능) | 선택 |

**자기개선 문서 후보** (별도 카테고리, 동기화 대상 아님)

| 키 | 원본 (있을 때만 후보) | 기본 설치 대상 |
|----|---------------------|---------------|
| `LESSONS.md` | `$TEMPLATE_DIR/LESSONS.md` | `$TARGET/.claude/LESSONS.md` |

각 후보의 원본이 실제 존재하는지 확인하고, **없는 항목은 카탈로그에서 제외**한다.

#### 누락 자산 알림 형식 (3-6 명세)

원본이 누락된 자산이 있으면 사용자에게 다음 형식으로 한 번에 보고한다:

```
주의: 다음 자산은 templates/project-setup/에 원본이 없어 메뉴에서 제외합니다.
  - DB_SCHEMA.md (원본 누락: $TEMPLATE_DIR/DB_SCHEMA.md)
  - update-project-docs/SKILL.md (원본 누락: $TEMPLATE_DIR/update-project-docs/SKILL.md)

(이 알림은 사람이 templates/ 자체를 손봐야 할 신호입니다 — 스킬은 자체적으로 보충하지 않습니다.)
```

알림은 한 번만 출력한다. 카탈로그가 완전히 비면 중단한다.

```bash
exists() { [ -e "$1" ]; }
# 각 후보를 exists로 검사하고 AVAILABLE_SKILLS / AVAILABLE_DOCS / AVAILABLE_LESSONS 리스트를 구성
```

### Step 3 — 사용자 자산 선택

이용 가능 자산을 사용자에게 보여준다. **CLAUDE.md / PROJECT_OVERVIEW.md는 기본 ON으로 표기**한다:

```
이용 가능한 자산:

  [스킬]  (.claude/skills/ 아래에 설치)
    1) manage-skills          — 검증 스킬 생성/갱신, 등록 목록 관리
    2) verify-implementation  — 등록된 verify-* 스킬 통합 실행
    3) update-project-docs    — 작업 문서(docs/ 등)를 코드와 동기화

  [작업 문서]  (기본 docs/ 아래에 설치, CLAUDE.md만 루트 또는 .claude/)
    4) CLAUDE.md              — 진입점·도메인 규칙·문서 매핑           [필수 권장 ✓]   → 루트 또는 .claude/
    5) PROJECT_OVERVIEW.md    — 프로젝트 정체성·기술 스택·마일스톤    [필수 권장 ✓]   → docs/ (기본)
    6) SOURCE_MAP.md          — 소스코드 라우팅 맵                                       → docs/ (기본)
    7) DB_SCHEMA.md           — DB 테이블·컬럼·접근 범위                                 → docs/ (기본)
    8) DEPLOY.md              — 인프라·도메인·환경변수·롤백                              → docs/ (기본)
    9) DESIGN.md              — 디자인 시스템·색상·타이포·컴포넌트                       → docs/ (기본)
   10) ADR.md                 — Architecture Decision Records (되돌리기 어려운 결정 로그)  → docs/ (기본)

  [자기개선]  (.claude/ 아래에 설치, 에이전트가 자동 누적)
   11) LESSONS.md             — 사용자 피드백 누적, 자기개선 순환
```

`AskUserQuestion`으로 선택 방식을 묻는다:

```
선택 방식:
  1. 권장 설치 (스킬 3 + 필수 문서 2 = CLAUDE.md, PROJECT_OVERVIEW.md) ← 권장
  2. 전체 설치 (모든 카탈로그)
  3. 스킬만 설치
  4. 문서만 설치 (필수 2 + 선택)
  5. 개별 선택 — 각 자산마다 따로 묻기
  6. 취소
```

- **권장** → SELECTED = AVAILABLE_SKILLS + (CLAUDE.md, PROJECT_OVERVIEW.md)
- **전체** → SELECTED = 카탈로그 전체
- **스킬만** → SELECTED = AVAILABLE_SKILLS
- **문서만** → SELECTED = 필수 2 + 사용자 추가 선택
- **개별** → 자산별로 `AskUserQuestion`(설치 / 건너뛰기)을 반복하여 SELECTED 구성. **CLAUDE.md / PROJECT_OVERVIEW.md는 기본 "설치"로 두고 명시적으로 빼야 제외**한다.
- **취소** → 종료

CLAUDE.md가 SELECTED에 포함되면 추가로 묻는다: "루트 (`<TARGET>/CLAUDE.md`) / `.claude/CLAUDE.md` 중 어디에 둘까요?"

SELECTED가 비면 종료한다.

### Step 3.5 — 설치 위치 공지 + 변경 확인 (대전제 1·3)

자산이 결정됐으면 **실제 파일을 만들기 전에 사용자에게 각 자산이 어떤 경로에 생기는지 명시적으로 보여주고 동의를 받는다.** 사용자가 "여기 말고 저기로" 라고 변경을 요청하면 그 위치로 다시 묻고 확정한다.

#### 3.5a. PATHS 맵 초기화

SELECTED 각 자산에 대해 기본 설치 경로를 채운 PATHS 맵을 만든다:

| 자산 | 기본 경로 | 변경 가능? |
|---|---|---|
| 스킬 3종 (manage-skills, verify-implementation, update-project-docs) | `<TARGET>/.claude/skills/<key>/` | 불가 (스킬은 `.claude/skills/` 고정) |
| `CLAUDE.md` | Step 3에서 사용자가 고른 위치 (루트 또는 `.claude/`) | 가능 (루트 ↔ `.claude/`) |
| `PROJECT_OVERVIEW.md` | `<TARGET>/docs/PROJECT_OVERVIEW.md` | 가능 |
| `SOURCE_MAP.md` | `<TARGET>/docs/SOURCE_MAP.md` | 가능 |
| `DB_SCHEMA.md` | `<TARGET>/docs/DB_SCHEMA.md` | 가능 |
| `DEPLOY.md` | `<TARGET>/docs/DEPLOY.md` | 가능 |
| `DESIGN.md` | `<TARGET>/docs/DESIGN.md` | 가능 |
| `ADR.md` | `<TARGET>/docs/ADR.md` | 가능 |
| `LESSONS.md` | `<TARGET>/.claude/LESSONS.md` | **불가 (고정)** |

#### 3.5b. 사용자 공지

PATHS 맵을 다음 형식으로 사용자에게 보여준다:

```
이번 설치로 다음 위치에 파일이 생성됩니다:

  [스킬]                    .claude/skills/ 고정
    - .claude/skills/manage-skills/
    - .claude/skills/verify-implementation/
    - .claude/skills/update-project-docs/

  [작업 문서]               기본 docs/ — 변경 가능
    - docs/PROJECT_OVERVIEW.md
    - docs/SOURCE_MAP.md
    - docs/DB_SCHEMA.md
    - docs/DEPLOY.md
    - docs/DESIGN.md
    - docs/ADR.md

  [진입점]                  사용자 선택
    - CLAUDE.md (루트)  또는  .claude/CLAUDE.md

  [자기개선]                .claude/ 고정
    - .claude/LESSONS.md

(사용자 메시지에 이미 "전부 docs2/ 아래로", "PROJECT_OVERVIEW만 .claude/" 같은
 명시가 있었다면 위 표는 그 결정을 반영해 표시한다.)
```

#### 3.5c. 변경 의사 확인

`AskUserQuestion`으로 묻는다:

```
질문: 위 위치로 진행할까요?

선택지:
  1. 네, 위 경로 그대로 진행
  2. 일부 또는 전체 위치를 바꾸겠습니다
  3. 취소
```

옵션 2를 선택하면 사용자가 변경을 원하는 자산을 자유 텍스트로 받는다 (예: "PROJECT_OVERVIEW만 wiki/로", "전부 documents/ 아래로"). 받은 입력에 따라 PATHS 맵을 갱신하고 3.5b를 다시 보여준 뒤 3.5c를 반복한다.

> **위치 변경의 허용 범위** — 작업 문서 6종은 어떤 디렉토리든 허용한다(예: `documents/`, `wiki/`, `.claude/`, 루트 직속). LESSONS.md와 스킬 3종은 변경 불가 — 사용자가 옮기려 하면 정중히 거절하고 기본 위치를 유지한다.

#### 3.5d. PATHS 확정

옵션 1이거나 2-반복 끝에 사용자가 동의하면 PATHS를 확정한다. 이후 모든 Step은 이 PATHS 맵을 진실의 원천으로 사용한다.

### Step 4 — 충돌 검사 + 자산별 처리 결정 (대전제 1)

Step 3.5에서 확정된 **PATHS 맵의 경로**를 기준으로 각 SELECTED 자산이 대상에 이미 존재하는지 확인한다. **CLAUDE.md는 양쪽 위치(루트 / .claude/)를 모두 검사**한다 (3-1 케이스). 또한 작업 문서는 사용자가 위치를 옮긴 경우 **이전 기본 위치(`docs/`)와 새 지정 위치 양쪽**을 한 번 확인해 사용자에게 흔적이 있는지 알려준다 (강제 처리는 하지 않음).

```bash
for asset in "${SELECTED[@]}"; do
  DEST="${PATHS[$asset]}"
  if [ -e "$DEST" ]; then
    CONFLICTS+=("$asset")
  fi
done

# CLAUDE.md 특수 케이스 — 양쪽 동시 존재 검사
if [ -e "$TARGET/CLAUDE.md" ] && [ -e "$TARGET/.claude/CLAUDE.md" ]; then
  CLAUDE_DUAL=true
fi
```

#### 4a. 양쪽 위치 동시 존재 (CLAUDE.md 한정, 3-1)

`CLAUDE_DUAL=true`인 경우 먼저 다음을 묻는다:

```
질문: 이 프로젝트에는 CLAUDE.md가 루트(`<TARGET>/CLAUDE.md`)와 `.claude/CLAUDE.md` 양쪽에 모두 있습니다.
       권장 위치는 `.claude/CLAUDE.md` 한 곳입니다. 어떻게 처리할까요?

선택지:
  1. 루트 CLAUDE.md를 .claude/로 옮기고 통합 (루트 파일 백업 후 .claude/로 이동, 내용 병합 여부는 다음 단계에서 묻기)
  2. 루트 CLAUDE.md를 그대로 유지하고 이번 설치도 루트 기준으로 진행 (.claude/CLAUDE.md는 손대지 않음)
  3. 취소하고 사용자가 직접 정리
```

선택 1이면 루트 파일을 `.bak.<timestamp>`로 백업한 뒤 `.claude/`로 옮기고, 이후 4b에서 `.claude/CLAUDE.md` 충돌로 분기. 선택 2면 루트 가정으로 진행하고 다른 충돌 자산만 4b로 진행.

#### 4b. 충돌 자산별 처리 방식 (대전제 1)

충돌이 1개 이상이면 다음 옵션을 `AskUserQuestion`으로 제시한다 (2-3 명확화):

```
충돌이 발견된 자산: <목록>

처리 방식을 선택하세요:
  1. 그대로 두기                   — 기존 파일을 유지하고 이 자산은 설치하지 않음
  2. 백업 후 새 템플릿으로 교체    — 기존 파일을 .bak.<timestamp>로 백업하고 템플릿을 그대로 깖
  3. 병합                          — 기존 파일은 유지하고 템플릿의 일부만 추가/머지 (상세는 4c)
  4. 자산별 개별 결정              — 각 충돌 자산마다 위 1~3 중 선택
  5. 취소                          — 전체 작업 중단
```

**대전제 1 — 묻지 않고 덮어쓰지 않는다.** 옵션 2를 선택해야만 백업 후 교체.

#### 4c. 병합 옵션의 자산별 의미 (3-4)

"병합"은 자산 종류에 따라 의미가 다르다. 사용자가 "병합"을 선택하면 자산별로 다음을 추가 질의한다:

- **CLAUDE.md** (3-4) — 사용자의 기존 파일은 **반드시 그대로 유지**한다. 템플릿 CLAUDE.md의 어느 섹션을 합칠지 묻는다:

  ```
  CLAUDE.md 병합 옵션 (기존 본문은 그대로 둠):
    A. Core Principles 섹션을 추가/덮어쓰기
    B. Workflows 섹션을 추가/덮어쓰기
    C. 문서 매핑 섹션을 추가/덮어쓰기 (이번 설치된 자산 기준으로 자동 채움)
    D. 위 항목 중 일부만 선택
    E. 병합 안 함 (기존 그대로 유지)
  ```

  병합 적용 시 이미 존재하는 같은 헤더(`## Core Principles` 등)는 사용자에게 한 번 더 확인 후 교체한다. **문서 매핑 섹션은 사용자 선택일 뿐 강제하지 않는다.**

- **PROJECT_OVERVIEW.md / SOURCE_MAP.md / DB_SCHEMA.md / DEPLOY.md / DESIGN.md** — 기존 파일을 그대로 유지하고, 템플릿에는 있지만 기존 파일에는 없는 **상위 섹션(`##`)만 끝에 추가**한다. 같은 헤더가 이미 있으면 추가하지 않는다.

- **ADR.md** — 결정 로그 형식이라 "템플릿 섹션을 끝에 붙이기"가 무의미하다(인덱스 표·번호 체계가 깨짐). 병합은 의미 없음 — 옵션에서 제외하고 "그대로 두기" / "백업 후 교체"만 가능.

- **LESSONS.md** — 자동 누적 문서이므로 병합은 의미 없음. 옵션에서 제외하고 "그대로 두기"만 가능.

- **스킬 (디렉토리)** — 디렉토리 단위 자산이므로 병합은 의미 없음. "그대로 두기" / "백업 후 교체" 둘 중 하나만 가능.

병합 옵션이 자산 종류상 불가하면 처리 옵션에서 자동으로 제거하고 사용자에게 한 줄로 알린다.

### Step 5 — 디렉토리 생성

PATHS 맵의 각 경로에서 부모 디렉토리만 자동 생성한다. **PATHS에 없는 디렉토리는 만들지 않는다** — 이 원칙으로 기본 `docs/`, 사용자 지정 `wiki/`, `.claude/` 어떤 것이든 동일하게 처리한다.

```bash
# 스킬은 항상 .claude/skills/ 아래
if [ ${#SELECTED_SKILLS[@]} -gt 0 ]; then
  mkdir -p "$TARGET/.claude/skills"
fi

# CLAUDE.md(.claude/ 위치 선택 시)·LESSONS.md 가 있으면
if [ -n "${PATHS[CLAUDE.md]:-}" ] && [[ "${PATHS[CLAUDE.md]}" == *"/.claude/"* ]]; then
  mkdir -p "$TARGET/.claude"
fi
if [ -n "${PATHS[LESSONS.md]:-}" ]; then
  mkdir -p "$TARGET/.claude"
fi

# 작업 문서는 PATHS의 부모 디렉토리만 생성 (기본은 docs/, 사용자 지정 시 그곳)
for doc in PROJECT_OVERVIEW.md SOURCE_MAP.md DB_SCHEMA.md DEPLOY.md DESIGN.md ADR.md; do
  [ -n "${PATHS[$doc]:-}" ] && mkdir -p "$(dirname "${PATHS[$doc]}")"
done
```

> `.claude/`나 `docs/`의 git 포함 여부는 프로젝트 정책이므로 임의로 `.gitignore`를 수정하지 않는다.

### Step 6 — 선택된 자산 설치

각 SELECTED 자산을 종류별로 처리한다. Step 4에서 결정된 처리 방식에 따라 분기.

**스킬 (디렉토리 단위)**:

설치 전에 글로벌 동명 스킬 검사 (3-5):

```bash
# 같은 이름의 스킬이 다른 marketplace/plugin에 있는지 확인 (참고용)
ls ~/.claude/plugins/*/skills/<key>/ 2>/dev/null
```

같은 이름의 스킬이 외부에 존재하면 **복사하기 전에 사용자에게 묻는다**:

```
질문: 같은 이름의 `<key>` 스킬이 다른 plugin/marketplace에 이미 있습니다.
       프로젝트 로컬 `.claude/skills/`에 설치하면 이쪽이 우선되어 외부 스킬을 가립니다.
       어떻게 할까요?

선택지:
  1. 그래도 프로젝트 로컬에 설치 (외부 스킬을 의도적으로 오버라이드)
  2. 이름을 바꿔 설치 (예: `<key>-local`)
  3. 이번엔 설치하지 않음
```

이후 결정에 따라 복사:

```bash
cp -r "$TEMPLATE_DIR/<key>" "$TARGET/.claude/skills/<key 또는 변경된 이름>"
```

**문서 (CLAUDE.md 외 단일 파일)** — Step 4 결정에 따라:

- "백업 후 교체": `cp <dest> <dest>.bak.$(date +%s) && cp <src> <dest>`
- "병합": Step 4c 규칙에 따라 헤더 단위 추가
- "그대로 두기": 아무것도 하지 않음

**CLAUDE.md (단일 파일, 위치는 사용자 선택)** — Step 4a/4b/4c 결정에 따라 처리.

설치 후 각 자산의 결과 파일이 존재하는지 `ls -la`로 검증한다. 또한 스킬의 경우 골격이 "초기 상태"인지 확인한다 (manage-skills/verify-implementation는 등록 테이블이 비어 있어야 함):

```bash
[ -f "$TARGET/.claude/skills/manage-skills/SKILL.md" ] && \
  grep -q "아직 등록된 검증 스킬이 없습니다" "$TARGET/.claude/skills/manage-skills/SKILL.md"
```

### Step 7 — CLAUDE.md 문서 매핑 채우기

CLAUDE.md가 이번 설치에 포함된 경우에만 실행한다. **단, Step 4c에서 사용자가 "문서 매핑 섹션 병합"을 거부했다면 이 Step도 건너뛴다** (3-4).

복사된 CLAUDE.md의 **"문서 매핑" 섹션**은 두 개의 빈 표를 가진다(템플릿 형식): "프로젝트 스킬"과 "외부문서". 이 표를 이번 설치에서 실제 설치된 자산으로 채운다.

#### 7a. 프로젝트 스킬 표 채우기

설치된 스킬 각각에 대해 다음 한 행을 추가한다:

| 스킬 | 용도 |
|---|---|
| `/<key>` | <한 줄 설명 — 이 SKILL.md "이용 가능한 자산" 섹션의 설명을 그대로 사용> |

예시 — `manage-skills`/`update-project-docs` 둘만 설치된 경우:

```markdown
| 스킬 | 용도 |
|---|---|
| `/manage-skills` | 세션 변경사항을 분석해 verify-* 스킬을 생성/갱신, 등록 목록 관리 |
| `/update-project-docs` | 작업 문서(기본 docs/ 또는 사용자 지정 위치)를 코드베이스 실제 상태와 비교해 드리프트 동기화 |
```

#### 7b. 외부문서 표 채우기

설치된 문서(CLAUDE.md 자기 자신은 제외) 각각에 대해 **PATHS 맵의 실제 설치 경로**를 그대로 적은 한 행을 추가한다. 기본 위치(`docs/`)에 깔았든 사용자가 지정한 다른 위치에 깔았든 상관없이, **표에는 실제 경로가 그대로 들어가야 한다** — 사용자가 CLAUDE.md만 보고도 어디에 있는지 알 수 있어야 한다.

| 문서 | 용도 |
|---|---|
| `<PATHS의 실제 경로>` | <한 줄 설명> |

LESSONS.md를 설치했으면 외부문서 표에 함께 등록한다 (자기개선 문서지만 진입 정보로서 가치가 있음).

예시 — `SOURCE_MAP.md`+`DB_SCHEMA.md`를 기본 위치(`docs/`)에 설치하고 LESSONS.md도 함께 설치한 경우:

```markdown
| 문서 | 용도 |
|---|---|
| `docs/SOURCE_MAP.md` | 소스코드 위치 라우팅 맵 |
| `docs/DB_SCHEMA.md` | DB 테이블·컬럼·접근 범위 |
| `.claude/LESSONS.md` | 사용자 피드백 누적, 자기개선 순환 |
```

예시 — 사용자가 `PROJECT_OVERVIEW.md`만 `wiki/`로, 나머지는 기본 `docs/`로 둔 경우:

```markdown
| 문서 | 용도 |
|---|---|
| `wiki/PROJECT_OVERVIEW.md` | 프로젝트 정체성·기술 스택·마일스톤·핵심 링크 |
| `docs/SOURCE_MAP.md` | 소스코드 위치 라우팅 맵 |
```

> 실제 경로를 적는 이유 — `update-project-docs`나 다른 에이전트가 이 표를 읽고 문서를 찾아간다. 잘못된 경로가 적히면 동기화가 깨진다.

#### 7c. 템플릿 안내 주석·placeholder 행 제거 (대전제 2)

CLAUDE.md 템플릿의 "문서 매핑" 섹션 상단에 있는 안내용 HTML 주석과 placeholder 행을 채워 넣은 후 제거한다. **매칭 규칙은 정확 문자열이 아닌 다음 패턴 기반 서브스트링**이다:

- 안내 HTML 주석: `<!--`로 시작하고 `-->`로 끝나는 블록 중 본문에 "여기에 ... 매핑한다" 또는 "형식 예시" 또는 "교체하고, 없는 항목은 삭제" 중 하나라도 포함된 블록 → 통째로 제거
- placeholder 행: `| /<skill-name> |`, `| <path/to/doc.md> |`, `| <한 줄 설명> |` 처럼 **꺾쇠 안에 영문 단어가 들어 있는** 데모 행 → 제거
- 실제 자산이 하나도 없는 표는 빈 표로 두지 말고 **표 헤더까지 함께 삭제**한다 (또는 "(없음)" 한 줄로 대체)

대전제 2 — 설치 결과물에 작성 안내문이 남아 있으면 안 된다. **다른 모든 템플릿 문서(PROJECT_OVERVIEW.md, SOURCE_MAP.md 등)에 대해서도 동일 규칙 적용**: 설치 후 "여기에 ...를 적는다" 같은 인용구 안내(`> ` 시작)는 사용자가 채워야 할 placeholder 표 자체가 충분히 자명하면 굳이 남길 필요 없으나, **본 스킬은 사용자가 직접 편집할 여지를 남기기 위해 인용구 안내는 보존**한다 (HTML 주석만 삭제 대상).

#### 7d. 형식 검증

수정 후 다음을 확인한다:
- 표의 헤더와 데이터 행 열 수가 일치
- 닫히지 않은 코드 블록 없음
- "## Workflows" 섹션은 그대로 둔다 — 사용자가 직접 채우는 영역

### Step 8 — 설치 보고

```markdown
## Project Setup 완료

**대상:** `<project-root>`

**설치된 스킬** (실제 선택된 항목만):
- `.claude/skills/<key>/SKILL.md`
- ...

**설치된 작업 문서** (실제 선택된 항목만, PATHS 맵의 실제 경로 그대로):
- `<CLAUDE.md 경로>` (루트 또는 .claude/ 중 선택된 위치)
- `docs/<key>` (기본 위치) 또는 `<사용자 지정 경로>` ...

**자기개선 문서:**
- `.claude/LESSONS.md` (선택 시)

**처리 방식별 분류:**
- 신규 설치: <목록>
- 백업 후 교체: <목록> + 백업 파일 경로 (`.bak.<timestamp>`)
- 병합 적용: <목록> + 합쳐진 섹션 요약
- 그대로 둠 (설치 스킵): <목록>

**메뉴에서 제외된 자산:** (템플릿에 원본이 없어 후보에서 제외된 항목)

**외부 동명 스킬 알림:** (있는 경우)
- `<key>` — `<외부 위치>`에도 존재. 이번 설치로 프로젝트 로컬이 우선됨.

**다음 단계:**
1. 새 Claude Code 세션에서 설치된 스킬이 로드됩니다.
2. 설치된 문서의 placeholder를 프로젝트 정보로 채우세요.
3. (manage-skills 설치 시) 코드 변경 후 `/manage-skills`로 `verify-*` 스킬을 생성하세요.
4. (verify-implementation 설치 시) 검증이 필요할 때 `/verify-implementation`을 실행하세요.
5. (update-project-docs 설치 시) 작업 문서가 코드와 어긋날 때 `/update-project-docs`로 동기화하세요.
6. (LESSONS.md 설치 시) 사용자 피드백이 있을 때마다 LESSONS.md에 lesson을 추가하세요 — 자동으로 갱신되는 문서가 아닌, 에이전트가 의식적으로 누적하는 문서입니다.
```

> 보고서의 각 섹션은 **실제 일어난 일만** 나열한다. 설치되지 않은 자산은 보고서에 등장하지 않는다.

## 설치 후 동작 방식

설치한 스킬·문서·규칙은 다음과 같이 협업한다 (각각 선택 설치이므로 일부만 깔려 있어도 동작한다):

- **`/manage-skills`** — 코드 변경 후 실행하여 새 `verify-<area>` 스킬을 생성/갱신. `manage-skills`/`verify-implementation` 두 SKILL.md의 등록 테이블이 동기화된다.
- **`/verify-implementation`** — 등록된 모든 `verify-*` 스킬을 순차 실행하여 통합 검증.
- **`/update-project-docs`** — 코드와 어긋난 **작업 문서**(CLAUDE.md, PROJECT_OVERVIEW.md, SOURCE_MAP.md, DB_SCHEMA.md, DEPLOY.md, DESIGN.md, ADR.md 중 설치한 것 — 기본 `docs/` 또는 사용자 지정 위치)를 코드 기준으로 동기화. ADR.md는 결정 로그라 코드와 자동 동기화 대상은 아니지만, 인덱스 표 정합성·`Superseded` 상태 누락 같은 정적 점검에 한정해 다룬다. 문서의 실제 위치는 CLAUDE.md "문서 매핑" 표를 진실의 원천으로 삼는다. **LESSONS.md는 동기화 대상이 아니다** — 에이전트가 사용자 피드백을 받을 때마다 직접 누적한다.
- **`.claude/LESSONS.md`** — 매 세션 시작 시 에이전트가 가장 먼저 읽고, 사용자 피드백이 들어오면 즉시 형식에 맞춰 추가한다.

이 스킬(`project-setup`)은 위 사이클이 시작될 수 있도록 **골격만 까는** 역할에 한정된다. 프로젝트별 `verify-*` 스킬은 만들지 않는다 — 그건 `/manage-skills`의 책임 영역이다.

## 예외사항

다음은 **문제가 아니다**:

1. **빈 `.claude/` 디렉토리** — 정상 케이스. 사용자가 선택한 자산만 골라 설치한다.
2. **CLAUDE.md / PROJECT_OVERVIEW.md를 명시적으로 빼는 사용자** — 권장만 하고 강제하지 않는다.
3. **부분 설치** — 사용자가 일부 자산만 선택하는 것은 정상. 누락된 자산을 강제로 채우지 않는다.
4. **이미 다른 `verify-*` 스킬이 설치된 프로젝트** — 선택된 자산만 설치하고 다른 스킬에는 손대지 않는다. `manage-skills`/`verify-implementation`도 함께 설치되었다면 등록 테이블에 기존 스킬을 수동 추가해야 함을 사용자에게 안내한다.
5. **다른 플러그인/마켓플레이스에 같은 이름 스킬이 있는 경우** — Step 6에서 사용자에게 묻고 결정. 자동 처리하지 않는다.
6. **카탈로그의 일부 자산 누락** — 템플릿 폴더에 일부 파일이 없으면 메뉴에서 제외하고 진행. 카탈로그가 완전히 비어야만 중단한다.
7. **CLAUDE.md가 양쪽 위치(루트/.claude/)에 동시 존재** — Step 4a에서 사용자에게 묻고 정리.

## Related Files

| File | Purpose |
|------|---------|
| `templates/project-setup/manage-skills/SKILL.md` | 설치할 manage-skills 골격 (이 스킬이 복사하는 원본) |
| `templates/project-setup/verify-implementation/SKILL.md` | 설치할 verify-implementation 골격 (이 스킬이 복사하는 원본) |
| `templates/project-setup/update-project-docs/SKILL.md` | 설치할 update-project-docs 골격 (이 스킬이 복사하는 원본) |
| `templates/project-setup/CLAUDE.md` | CLAUDE.md 신규 생성 시 사용하는 템플릿 (placeholder 표 포함, 설치 후 Step 8에서 채워짐) |
| `templates/project-setup/PROJECT_OVERVIEW.md` | 프로젝트 개요 골격 (정체성·스택·마일스톤·링크) |
| `templates/project-setup/SOURCE_MAP.md` | 소스코드 라우팅 맵 골격 |
| `templates/project-setup/DB_SCHEMA.md` | DB 스키마 골격 (ER 다이어그램·테이블·접근 범위) |
| `templates/project-setup/DEPLOY.md` | 배포 정보 골격 (인프라·환경변수·롤백) |
| `templates/project-setup/DESIGN.md` | 디자인 시스템 골격 (색상·타이포·컴포넌트·다크 모드) |
| `templates/project-setup/ADR.md` | Architecture Decision Records 골격 (인덱스 표 + ADR-0001 형식 예시) |
| `templates/project-setup/LESSONS.md` | 자기개선 순환 골격 (사용자 피드백 lesson 형식·운영 규칙) |
| `<target>/.claude/skills/manage-skills/SKILL.md` | 설치 결과물 |
| `<target>/.claude/skills/verify-implementation/SKILL.md` | 설치 결과물 |
| `<target>/.claude/skills/update-project-docs/SKILL.md` | 설치 결과물 |
| `<target>/CLAUDE.md` 또는 `<target>/.claude/CLAUDE.md` | (선택) 템플릿 기반으로 생성되거나 Step 4c 병합 옵션에 따라 일부 섹션이 합쳐진 결과물 |
| `<target>/docs/PROJECT_OVERVIEW.md` (기본 / 사용자 지정 시 다른 경로) | (선택) 설치된 프로젝트 개요 골격 |
| `<target>/docs/SOURCE_MAP.md` (기본 / 사용자 지정 시 다른 경로) | (선택) 설치된 라우팅 맵 골격 |
| `<target>/docs/DB_SCHEMA.md` (기본 / 사용자 지정 시 다른 경로) | (선택) 설치된 DB 스키마 골격 |
| `<target>/docs/DEPLOY.md` (기본 / 사용자 지정 시 다른 경로) | (선택) 설치된 배포 정보 골격 |
| `<target>/docs/DESIGN.md` (기본 / 사용자 지정 시 다른 경로) | (선택) 설치된 디자인 시스템 골격 |
| `<target>/docs/ADR.md` (기본 / 사용자 지정 시 다른 경로) | (선택) 설치된 Architecture Decision Records 골격 |
| `<target>/.claude/LESSONS.md` | (선택) 설치된 lesson 골격 (위치 고정) |
