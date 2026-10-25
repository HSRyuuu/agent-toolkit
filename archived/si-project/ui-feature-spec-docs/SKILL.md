---
name: ui-feature-spec-docs
description: >
  Use when deriving a screen-by-screen UI feature specification from frontend
  source code and optional design docs (docx/pdf) for Vue, React, Svelte,
  Angular, Next.js, Nuxt, or SvelteKit. Triggers: "화면별 기능 정의서 만들어줘",
  "UI 기능 명세 정리", "라우터 기반 기능 명세서", "화면설계서랑 소스 교차 검증",
  "ui feature spec", "/ui-feature-spec-docs". Do NOT use for component-only docs
  or UI test execution.
---

# ui-feature-spec-docs — 화면별 기능 정의서 작성 스킬

프론트엔드 소스의 라우터·페이지 구조와 선택적 화면정의서(docx/pdf)를 입력받아 **화면별 기능 정의서**를 단일 통합 markdown 파일로 생성한다. 필요 시 라이브 브라우저(Playwright MCP) 검증을 보조 모드로 추가.

## Overview

핵심 원칙:
- **메인 입력은 소스 + 정의서** — 둘 중 하나만 있어도 동작. 둘 다 있으면 교차 매핑.
- **라이브 브라우저는 보조 모드 (기본 OFF)** — 소스가 없거나 권한/feature flag/조건부 렌더링 검증이 필요할 때만 켠다. 사용자가 명시적으로 요청한 경우에만 ON.
- **Framework-agnostic** — Vue/React/Svelte/Angular/Next.js/Nuxt/SvelteKit 등.
- **단일 파일 출력** — 화면이 50개든 100개든 하나의 markdown으로 통합. 목차로 네비게이션.
- **기능 ID 일관성** — `UI-{kebab-case-screen-name}-{3자리 번호}`.
- **시작 1회 입력 수집, 이후 무질문** — 모호한 점은 시작 시점에 한 번에 묻는다. 작업 중간 사용자 질문 금지. 애매한 케이스는 결과물에 `⚠️ / 🔒 / 🚧 / (TBD)` 마커로 보존하고 사용자가 결과물 받아본 후 결정.
- **발명 금지** — 어느 소스에도 없는 기능을 추측해서 채우지 않는다. 빈 칸은 `(TBD)`.
- **소스의 역할 분리** (보조 모드 ON일 때):
  - 소스코드 = **있을 수 있는** 기능의 정적 목록 (조건부·dead code 포함)
  - 정의서 = **있어야 하는** 기능의 의도 (사람이 적은 spec)
  - 라이브 브라우저 = **실제로 보이는** 기능의 런타임 진실 (권한/feature flag/A-B 분기 적용 후)

## When to Use

**메인 워크플로우 (소스 + 정의서):**
- 기존 프론트엔드 코드에서 화면별 기능 명세서를 역추출
- 화면정의서(docx/pdf)는 있는데 코드와 어긋났는지 검증
- SI 프로젝트에서 화면설계서 산출물의 기능 항목 부분을 일괄 생성
- QA·기획자에게 "이 화면에 어떤 기능이 있나" 일람 전달

**라이브 보조 모드를 켜는 좁은 케이스:**
- **소스코드 접근 불가** — 빌드된 결과물만 운영 중인 legacy, 외주 SPA, 외부 호스팅 사이트
- **권한/role별 분기가 많음** — admin/member/guest별로 실제 보이는 게 다른지 검증
- **feature flag·A-B 분기 검증** — 정적 분석으로는 어느 분기가 활성인지 모름
- **서드파티 위젯 다수** — 외부 컴포넌트가 만드는 버튼이 소스에는 안 잡힘

**사용하지 않을 때:**
- 화면 단위가 아닌 컴포넌트 단위 명세
- 백엔드 API 명세 (`rest-api-design` 또는 별도 스킬)
- 신규 화면 설계(역공학이 아니라 forward design)

## Step 0: 입력 수집 (시작 시 한 번)

**모든 질문은 여기서 한꺼번에 묻고, 이후 단계에서는 묻지 않는다.**

### 필수
- **소스 경로 또는 정의서 경로** 중 최소 하나
  - 소스: 라우터 파일(`src/router/index.ts`, `src/App.tsx`) 또는 페이지 디렉토리(`app/`, `pages/`, `src/routes/`)
  - 정의서: `.docx` / `.pdf` 파일 경로

### 선택
- **출력 경로** (기본 `./ui-feature-spec.md`)
- **프로젝트명·작성자명** (메타데이터용, 비우면 플레이스홀더)

### 라이브 보조 모드 ON일 때만 추가 수집
사용자가 "playwright로 확인해서" / "라이브 검증 같이" 같이 요청했거나, 소스가 없는 케이스에서만 묻는다:
- **base URL** (예: `http://localhost:5173` — Vite 기본 / `http://localhost:3000` — CRA·Next 기본)
- **로그인 시스템 여부**
  - 비로그인이면 → 그대로 진행
  - 로그인이면 → 테스트 계정(아이디/비밀번호) 또는 사전 로그인된 세션 정보를 시작 시점에 받음. **받지 못하면 라이브 검증은 OFF로 강등** (소스+정의서만으로 진행)
- **검증할 role** (admin/member/guest 등. 기본 하나, 여럿이면 사용자가 우선순위 명시)
- **동적 segment 샘플** — 라우터에 `:id`/`[id]` 등이 있으면 라우트별 샘플 값 (예: `/users/:id → id=1`). 누락된 경로는 라이브 검증에서 자동 스킵.

### Framework 감지 실패 시
Step 1에서 framework 자동 감지가 실패할 가능성이 있으면 Step 0에서 함께 묻는다 (`package.json`을 미리 확인). 이후 단계에서는 묻지 않는다.

**Step 0 끝 = 묻기 끝.** 이후 모든 모호함은 결과물 markdown에 마커로 표기.

## 산출물

단일 markdown 파일. 표 컬럼은 라이브 보조 모드 OFF일 때 5종 / ON일 때 6종.

```markdown
# 화면 기능 명세서

| 항목 | 내용 |
|---|---|
| 프로젝트명 | {프로젝트명} |
| 작성일 | {YYYY-MM-DD} |
| Framework | {감지된 framework} |
| 화면 수 | {N} |
| 라이브 검증 | OFF (또는 ON, base=http://localhost:5173, role=admin) |

## 목차
- [사용자 목록](#사용자-목록)
- [상품 상세](#상품-상세)

## 사용자 목록

- **경로**: /users
- **라우트명**: UserList
- **파일**: `src/views/UserList.vue`
- **설명**: 사용자 목록을 검색·정렬·페이징하여 보여주는 화면

### 기능 목록

| 기능 ID | 기능명 | 설명 | 트리거 | 예상 동작 |
|---|---|---|---|---|
| UI-user-list-001 | 사용자 검색 | 키워드로 사용자 필터 | 검색 버튼 / Enter | 검색 API 호출, 결과 테이블 갱신 |
| UI-user-list-002 | 사용자 정렬 | 컬럼 헤더 클릭 시 정렬 토글 | 컬럼 헤더 클릭 | 정렬 상태 토글, 재조회 |
```

## 기능 ID 규칙

형식: **`UI-{feature-name}-{number}`**

- `feature-name`: 화면명을 kebab-case로 변환
  - 한글 화면명 → 영문 의미 단어로 번역 후 kebab-case (예: `사용자 목록` → `user-list`, `상품 상세` → `product-detail`)
  - 영문 화면명은 그대로 kebab-case
- `number`: 화면 내 3자리 순번, `001`부터 시작
- **화면 간 번호 충돌 없음** — 화면명이 namespace 역할

## 마커 표기 규칙

작업 중 사용자에게 묻지 않고, 모든 애매한 케이스를 markdown 결과물에 다음 마커로 보존한다.

| 마커 | 의미 | 어디에 |
|---|---|---|
| `(TBD)` | 어느 소스에도 정보가 없음. 사용자가 채워야 함 | 표 셀 |
| `⚠️ 매칭 신뢰도 낮음` | 소스↔정의서 매핑 신뢰도 낮음. 양쪽 후보 모두 같은 화면 섹션에 보존 | 화면 메타 또는 표 행 |
| `🚧 미구현` | 정의서에만 있고 소스에 없는 화면/기능 | 화면 첫 줄 또는 표 비고 |
| `⚠️ 미사용 의심` | 소스에만 있고 정의서/라이브에 없는 화면/기능 (dead code 의심) | 표 비고 |
| `🔒 조건부 표시` | 라이브에서 안 보이지만 소스에 있음 — 권한·feature flag 의심 | 표 비고 |
| `📝 spec 누락` | 소스+라이브에는 있지만 정의서 없음 | 표 비고 |
| `🔍 정적 추출 누락` | 라이브에만 있고 소스 추출에서 빠짐 | 표 비고 |
| `🧩 외부 구성` | 정의서+라이브에 있지만 소스에 없음 — 서드파티/iframe 의심 | 표 비고 |
| `⛔ 라이브 검증 실패` | 라이브 보조 모드에서 접속 실패·런타임 에러 | 화면 첫 줄 |
| `🔐 인증 필요로 검증 스킵` | 인증 정보가 부족해 라이브 검증 못 한 화면 | 화면 첫 줄 |

라이브 보조 모드 OFF면 `🔒/📝/🔍/🧩/⛔/🔐` 마커는 사용되지 않는다 (소스↔정의서 2-소스 마커만).

## 워크플로우

### Step 1: 프론트엔드 소스 분석

#### 1-A. Framework 자동 감지

1. **`package.json`의 dependencies/devDependencies**
   - `vue` + `vue-router` → Vue Router
   - `react` + `react-router-dom` → React Router
   - `next` → Next.js (App/Pages Router는 2번에서 구분)
   - `nuxt` → Nuxt
   - `@sveltejs/kit` → SvelteKit
   - `svelte`만 → Svelte
   - `@angular/core` → Angular
2. **디렉토리 구조**
   - `app/page.{tsx,jsx,ts,js}` 또는 `app/layout.*` → Next.js App Router
   - `pages/_app.*` → Next.js Pages Router
   - `pages/**/*.vue` + Nuxt 의존성 → Nuxt
   - `src/routes/+page.svelte` → SvelteKit
3. **둘 다 실패** → Step 0에서 이미 받은 정보를 사용. 그래도 없으면 framework `unknown`으로 표기하고 사용자가 직접 제공한 화면 목록(있다면)으로 진행.

#### 1-B. Framework별 라우터 파싱

| Framework | 화면 목록 추출 위치 |
|---|---|
| Vue Router | `routes` 배열 (`createRouter({ routes: [...] })`) — `path`, `name`, `component`, `children` |
| React Router (v6+) | `<Routes>` 내부 `<Route path="..." element={<Comp/>} />` 또는 `createBrowserRouter([...])` |
| Next.js App Router | `app/**/page.{tsx,jsx,ts,js}` — 폴더 경로가 URL segment |
| Next.js Pages Router | `pages/**/*.{tsx,jsx,ts,js}` (단, `_app`/`_document`/`api/` 제외) |
| Nuxt | `pages/**/*.vue` (`[id].vue` = 동적 segment) |
| SvelteKit | `src/routes/**/+page.svelte` |
| Angular | `RouterModule.forRoot([...])` 또는 `provideRouter([...])`의 `Routes` |
| 직접 제공 | 사용자가 준 화면 목록을 그대로 사용 |

동적 segment(`[id]`, `:id`, `*`)는 **경로에는 그대로 표기**하되 **화면명에는 의미 단어로** 옮긴다 (예: `/users/:id` → "사용자 상세"). 중첩 라우트는 부모-자식 경로를 합쳐 평탄화하고, 화면명에는 계층 반영 (예: "설정 > API 키").

#### 1-C. 화면 메타데이터 수집

각 화면별: 경로(path), 라우트명(name, 없으면 PascalCase 추정), 컴포넌트 파일 경로, (있으면) layout/meta/guard/title.

#### 1-D. 기능 후보 추출 (소스 기반)

| 패턴 | 의미 |
|---|---|
| `@click`, `onClick`, `on:click` | 사용자 액션 (버튼/링크 클릭) |
| 폼 submit 핸들러, `<form onSubmit>`, `@submit` | 데이터 제출 |
| `fetch`/`axios`/`api.*`/`useQuery`/`useMutation` | 외부 통신 |
| `useEffect`/`onMounted`/`onMount`의 로직 | 초기 로딩 동작 |
| 라우터 navigation (`router.push`, `navigate()`, `<Link>`) | 화면 전이 |
| 상태 토글, 모달/드로어 open/close | UI 인터랙션 |

소스만으로 추출이 어려운 항목(비즈니스 규칙, 권한 체크, UX 디테일)은 정의서에서 보충하거나 빈 셀 + `(TBD)`.

### Step 2: 화면정의서 파싱 (있을 경우)

`<skill>/scripts/parse_design_doc.py`를 사용 (`<skill>` = 이 스킬 디렉토리 절대 경로). 의존성이 없으면 한 번 설치:

```bash
pip install -r <skill>/scripts/requirements.txt
python3 <skill>/scripts/parse_design_doc.py <문서 경로> --output /tmp/design_doc.json
```

`<skill>`은 SKILL.md가 위치한 디렉토리 — Claude Code가 스킬을 로드한 경로(예: `~/.claude/plugins/.../skills/ui-feature-spec-docs/`). LLM이 SKILL.md를 읽고 있는 경로 기준으로 절대 경로화하여 사용한다.

JSON에서 화면 단위 섹션을 휴리스틱으로 식별:
- **휴리스틱 1**: "화면명:", "Screen:", "##", "■", "▣" 등으로 시작하는 텍스트
- **휴리스틱 2**: 표 헤더에 "기능", "기능명", "설명", "동작", "이벤트" 등 포함 → 기능 목록 표
- **휴리스틱 3**: 같은 화면명이 반복 출현하면 그 사이의 콘텐츠를 해당 화면 섹션으로 묶음
- **휴리스틱 4**: 페이지 경계가 명확하면 페이지 단위로 화면 분리

**추출 실패 시**: 사용자에게 묻지 않는다. 추출 못한 raw 텍스트를 markdown 하단의 `## 부록 — 정의서 매핑 불가 영역` 섹션에 그대로 보존. 사용자가 결과물 받아본 후 수동 매핑할 수 있게 함.

### Step 3 (보조 모드 ON일 때만): 라이브 브라우저 검증

Step 0에서 라이브 모드 ON + 필요한 정보가 모두 수집된 경우에만 실행. 정보 부족이면 이 단계 전체를 건너뛰고 Step 4로.

**사용 가능한 MCP 도구** (둘 중 하나, 환경에 설치된 것을 사용):
- **Playwright MCP** — 사용자 요청 시 권장
- **chrome-devtools MCP** — 대체. `navigate_page` / `take_snapshot` / `list_console_messages` / `list_network_requests` 등 본 스킬이 요구하는 인터페이스를 모두 제공

도구 이름은 MCP에 따라 다를 수 있지만 의미는 같다. 본 스킬은 아래 단계에서 generic한 동작 이름으로 기술하며, 실제 호출 시 MCP의 실제 함수명을 사용한다.

#### 3-A. 화면별 검증 루프

Step 1에서 추출한 화면 목록 각각에 대해:

1. **navigate** — base URL + 라우트 경로 (동적 segment는 Step 0에서 받은 샘플 값으로 치환. 샘플 없는 경로는 `🔐 샘플 미제공으로 스킵` 표기 후 다음 화면)
2. **로딩 대기** — 네트워크 idle 또는 명시적 selector 출현
3. **DOM snapshot** — 접근성 트리 기반 (`take_snapshot`)
4. **인터랙티브 요소 수집**:
   - `button`, `[role="button"]` — 텍스트/aria-label
   - `a[href]` — 텍스트 + href
   - `input`, `select`, `textarea`, `[contenteditable]` — label + type
   - `form` — submit 버튼 + 필드 묶음
   - `[role="dialog"]`, `[role="menu"]`, `[role="tab"]` — 모달·메뉴·탭
   - `[data-testid]`, `[data-test]` — 테스트 훅
5. **콘솔/네트워크 관찰** — `list_console_messages`, `list_network_requests`로 초기 로딩 API endpoint 수집 ("예상 동작" 보강용)

> 인터랙션(클릭, 폼 제출 등)은 **수행하지 않는다.** 데이터 변경·side effect 위험. Step 0에서 사용자가 명시적으로 허용한 경우에만 진행.

#### 3-B. 실패 처리 (전체 중단 X, 마커 표기 후 계속)

- **접속 실패** (404, network error) → `⛔ 라이브 검증 실패 — {사유}`
- **로그인 페이지로 리다이렉트** → `🔐 인증 필요로 검증 스킵` (Step 0에서 인증 받았는데도 리다이렉트면 세션 만료 의심)
- **JS 에러로 빈 화면** → 콘솔 메시지를 부록 섹션에 보존, 화면에는 `⛔ 런타임 에러` 표기
- **동적 segment 샘플 미제공** → `🔐 샘플 미제공으로 스킵`

여러 role로 검증할 경우 role별로 결과를 분리 저장, markdown에는 비고에 명시.

### Step 4: 교차 매핑

**사용자에게 보고하지 않고** 모든 결과를 직접 markdown에 반영한다.

#### 4-A. 화면 단위 매핑

기준 (우선순위 순):
1. **경로 일치** — 소스 라우트 path = 정의서 명시 경로 = (보조 모드) 라이브 navigated URL path
2. **화면명 일치** — 라우트 name/컴포넌트명 ↔ 정의서 제목 ↔ 라이브 `<title>`/`<h1>`
3. **휴리스틱** — 부분 일치, 유사도. **신뢰도 낮으면 묻지 말고 `⚠️ 매칭 신뢰도 낮음`으로 표기**, 양쪽 후보를 같은 화면 섹션에 모두 보존.

화면별 분류 (라이브 OFF면 4그룹, ON이면 7그룹):

| 라이브 OFF (소스+정의서) | 표기 |
|---|---|
| 소스 + 정의서 일치 | 정상 (마커 없음) |
| 소스에만 있음 | `⚠️ 미사용 의심` |
| 정의서에만 있음 | `🚧 미구현` |
| 매칭 신뢰도 낮음 | `⚠️ 매칭 신뢰도 낮음` + 후보 보존 |

| 라이브 ON (3소스) | 표기 |
|---|---|
| 3소스 일치 | 정상 |
| 소스+정의서, 라이브 X | `🔒 조건부 표시` 또는 `⛔ 라이브 검증 실패` (사유에 따라) |
| 소스+라이브, 정의서 X | `📝 spec 누락` |
| 정의서+라이브, 소스 X | `🧩 외부 구성` |
| 소스만 | `⚠️ 미사용 의심` |
| 정의서만 | `🚧 미구현` |
| 라이브만 | `🔍 정적 추출 누락` |

#### 4-B. 기능 단위 매핑 (화면 내)

매칭된 화면 안에서 기능 항목들도 같은 분류 규칙 적용. 기능 ID는 화면 내 namespace에서 `001`부터 순번. 마커는 비고 컬럼 또는 마지막 컬럼(`출처`)에 표기.

### Step 5: 단일 markdown 생성

각 화면별 섹션을 만들고, 기능 목록 표를 채운다.

**기본 5컬럼 (라이브 OFF):**
```markdown
| 기능 ID | 기능명 | 설명 | 트리거 | 예상 동작 |
|---|---|---|---|---|
| UI-user-list-001 | 사용자 검색 | 키워드 필터 | 검색 버튼 / Enter | 검색 API 호출 |
| UI-user-list-002 | 사용자 정렬 | 컬럼 헤더 클릭 정렬 | 컬럼 헤더 클릭 | (TBD) |
```

**6컬럼 (라이브 ON, +출처):**
```markdown
| 기능 ID | 기능명 | 설명 | 트리거 | 예상 동작 | 출처 |
|---|---|---|---|---|---|
| UI-user-list-001 | 사용자 검색 | 키워드 필터 | 검색 버튼 / Enter | GET /api/users | ✅ 소스+정의서+라이브 |
| UI-user-list-002 | 관리자 메뉴 | 관리자 전용 | 메뉴 버튼 | 드롭다운 | 🔒 조건부 표시 (admin role) |
| UI-user-list-003 | 엑셀 다운로드 | xlsx export | 다운로드 버튼 | 파일 다운로드 | 📝 spec 누락 |
```

특수 화면은 섹션 첫 줄에 한 줄 주석:
- `> 🚧 미구현 — 정의서 p.14 기준으로만 작성됨`
- `> ⛔ 라이브 검증 실패 — {사유}`
- `> 🔍 정적 분석에서 누락된 화면 — 라이브에서만 발견`
- `> ⚠️ 매칭 신뢰도 낮음 — 소스의 'UserList'와 정의서의 '회원 목록'으로 추정`

목차는 화면 수만큼 자동 생성, anchor는 한글 그대로.

문서 하단:
```markdown
## 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|---|---|---|---|
| v1.0 | YYYY-MM-DD | (자동 생성) | 초안 — 소스 N건 + 정의서 M건 (+ 라이브 K건) 기반 |

## 검증 메타

| 항목 | 값 |
|---|---|
| Framework | Vue 3 + Vue Router |
| 라이브 검증 | OFF (또는 ON, base=http://localhost:5173, role=admin, 검증 시각=2026-05-14 15:30 KST) |
| 동적 segment 샘플 | `:id=1` (없으면 생략) |

## 부록 — 정의서 매핑 불가 영역

(정의서에서 화면 단위로 분리하지 못한 raw 텍스트가 여기에 그대로 들어감. 사용자가 검토 후 수동 매핑)
```

**기존에 같은 경로의 파일이 있으면 자동 백업** — 원본 파일을 `{stem}.{YYYYMMDD-HHMMSS}.bak.md`로 이름 변경 후 새 파일을 작성한다 (`stem` = 확장자를 뺀 파일명; 예: `ui-feature-spec.md` → `ui-feature-spec.20260514-153012.bak.md`). 사용자에게 묻지 않는다 (백업이 있으니 안전).

## Common Mistakes

| 실수 | 결과 |
|---|---|
| **작업 중간에 사용자에게 질문** | 본 스킬은 시작 1회 수집 후 무질문이 원칙. 애매한 건 마커로 결과물에 보존. |
| **Step 0에서 안 받은 정보를 중간에 추측** | 추측해서 메우면 발명. 누락된 입력은 결과물 마커로 표기하고 진행. |
| Framework 감지 실패한 채로 추측 진행 | Step 0에서 받았어야 함. 그래도 모르면 `unknown`으로 표기. |
| 동적 segment를 화면명에 그대로 (`UserList[id]`) | 의미 단어로 옮긴다. |
| 정의서 추출 실패를 발명으로 메움 | 부록 섹션에 raw 텍스트로 보존하고 사용자 검토 대기. |
| 기능 ID를 화면 간 전역 순번으로 | 화면 내 namespace로 격리, 추가/삭제 시 안정성. |
| 여러 markdown 파일로 분리 | 단일 통합 파일. 분리는 사용자가 명시 요청한 경우만. |
| 한글 화면명을 그대로 ID로 (`UI-사용자-목록-001`) | 영문 kebab-case. 한글은 섹션 제목에만. |
| 기존 출력 파일 덮어쓰기 전 사용자 확인 | 자동 백업으로 처리. 묻지 않는다. |
| 표 컬럼 임의 변경 | OFF=5컬럼 / ON=6컬럼 고정. |
| 라이브 검증 시 추측 URL로 접속 | Step 0에서 받은 base URL만 사용. 정보 부족이면 라이브 OFF로 강등. |
| 라이브에서 클릭/폼 제출 등 인터랙션 임의 수행 | side effect 위험. Step 0에서 명시 허용한 경우만. |
| 라이브 접속 1건 실패로 전체 중단 | 실패는 `⛔` 표기, 나머지 화면 계속. |
| 라이브에서 안 보임을 dead code로 단정 | 권한·feature flag 가능. `🔒 조건부 표시`로 표기. |
| 라이브 결과로 정의서/소스를 덮어씀 | 셋은 동등한 증거. 충돌은 마커, 판단은 사용자. |
| 인증 정보 없는데 로그인 시스템에 라이브 검증 시도 | Step 0에서 받지 못했으면 라이브 OFF로 강등하고 소스+정의서만으로 진행. |

## Quick Reference

```
Step 0: 입력 1회 수집 (소스/정의서/출력경로, 라이브 모드면 base URL·인증·role·segment 샘플)
  ↓
Step 1: framework 감지 + 라우터 파싱 → 화면 목록 + 기능 후보
Step 2: docx/pdf 파싱 (있을 때) → 정의서 기반 기능 + 매핑 불가는 부록에 보존
Step 3 (보조 모드 ON일 때만): 화면별 navigate + snapshot → 라이브 가시 요소
Step 4: 교차 매핑 → 마커 부여 (⚠️/🔒/🚧/📝/🔍/🧩/⛔/🔐)
Step 5: 단일 markdown 생성 (5 또는 6컬럼) → ./ui-feature-spec.md (기존 파일은 자동 백업)
```

부속 파일:
- `scripts/parse_design_doc.py` — docx/pdf → JSON 변환기
- `scripts/requirements.txt` — `python-docx`, `pypdf`
