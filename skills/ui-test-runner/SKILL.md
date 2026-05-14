---
name: ui-test-runner
description: >
  화면 기능 명세, 직접 작성한 테스트 시나리오(markdown/JSON), 또는 단순 URL 목록을 입력받아
  Playwright MCP로 실제 dev 서버(예: http://localhost:5173)에 접속해 UI 테스트를 수행하고
  구조화된 결과 JSON + 사람이 읽을 수 있는 markdown 요약을 출력한다.
  Chromium에서 실제 JS가 돌아가는 채로 검증하며, **mutation 요청(POST/PUT/DELETE/PATCH)은
  fetch/XHR 인터셉터 주입으로 모두 가로채서 실제 백엔드에 절대 도달하지 않게** 한다.
  GET 등 read-only 요청은 그대로 통과해 실제 데이터를 사용한다.
  트리거 - "UI 테스트 돌려줘", "화면 테스트 시나리오 실행", "Playwright로 검증", "smoke test",
  "이 명세 기준으로 UI 검증", "/ui-test-runner", "E2E 돌려봐줘", "버튼 눌러보고 결과 확인",
  "프론트 회귀 테스트", "리그레션 체크".
  사용하지 않을 때 - 백엔드 실제 mutation까지 흘려보내고 싶은 통합 테스트, 단위 테스트(Jest 등),
  실제 DB 변경을 동반해야 하는 시나리오, Cypress/Vitest 코드 작성.
---

# ui-test-runner — Playwright MCP 기반 안전한 UI 테스트 러너

## 이 스킬이 하는 일

사용자가 띄운 실제 dev 서버(예: `http://localhost:5173`)에 Playwright MCP로 접속해서 화면을 실제로 조작·검증한다. 다른 스킬을 호출하지 않는 **독립 실행 스킬**.

핵심 두 가지:

1. **실제 브라우저** — Chromium에서 페이지 JS가 그대로 돌아간다. Vue/React/Angular 등 정상 렌더링.
2. **mutation은 절대 백엔드에 안 보낸다** — POST/PUT/DELETE/PATCH는 페이지에 인터셉터를 주입해 모두 차단. 가짜 성공 응답을 즉시 돌려준다. GET 등은 그대로 통과해서 실제 데이터를 본다.

---

## 사전 요구사항: Playwright MCP 설치

이 스킬은 **Microsoft 공식 Playwright MCP**에 강하게 의존한다. 미설치 시 아무 것도 못한다.

설치 명령:

```bash
claude mcp add playwright -- npx -y @playwright/mcp@latest
```

설치 확인:

```bash
claude mcp list
# playwright 가 나오면 OK
```

브라우저 바이너리가 없으면 한 번:

```bash
npx playwright install chromium
```

**스킬 시작 시 확인 절차:** 사용 가능한 도구 목록에 `mcp__playwright__browser_*` 류가 보이지 않으면 즉시 중단하고 다음을 사용자에게 알린다:

> Playwright MCP가 설치되어 있지 않아 실행할 수 없습니다.
> 다음 명령으로 설치 후 Claude Code를 재시작해주세요:
>
> ```
> claude mcp add playwright -- npx -y @playwright/mcp@latest
> npx playwright install chromium
> ```

---

## 절대 위반 금지 — mutation 차단 정책

Playwright MCP는 `page.route()` 를 직접 도구로 노출하지 않는다. 대신 **`browser_evaluate` 로 페이지에 `window.fetch` + `XMLHttpRequest` 인터셉터를 주입**하는 방식으로 같은 효과를 낸다. 의미상 결과는 동일하다: **mutation 요청은 브라우저 밖으로 나가지 않는다.**

규칙:

- 모든 `browser_navigate` **직후** 인터셉터를 다시 주입한다 (페이지 로드 시 리셋되기 때문).
- 인터셉터 주입 실패 → 즉시 테스트 전체 중단. 절대 그냥 진행하지 않는다.
- 기본 모킹 응답: `{ status: 200, body: { ok: true, mocked: true } }`.
- 시나리오에 `mockOverrides` 가 있으면 그 응답을 사용 (에러 응답 테스트 등).
- 가로챈 모든 요청은 결과의 `cases[].mockedRequests` 에 기록한다.

인터셉터 스크립트는 [references/mock-interceptor.js](references/mock-interceptor.js) 그대로 사용. 임의 수정 금지.

---

## 입력 (3가지 중 하나)

| 형태 | 처리 |
|---|---|
| 화면 기능 명세 markdown 파일 (PRD/설계서 등) | [references/scenario-format.md](references/scenario-format.md) §"화면 기능 명세에서 시나리오 도출" 휴리스틱으로 케이스 도출 → 사용자 확인 후 실행 |
| 직접 작성한 시나리오 (markdown 또는 JSON) | [references/scenario-format.md](references/scenario-format.md) 참고. 거의 그대로 파싱 |
| 단순 URL 목록 | 각 URL에 대해 smoke test만 수행 (goto 성공, console error 0, title non-empty) |

추가로 필수:
- **테스트 대상 base URL** (예: `http://localhost:5173`). 시나리오에 들어있으면 그것 사용, 없으면 사용자에게 질문.
- **인증 필요 여부**. 필요하면 자동 로그인 시도 전에 반드시 사용자에게 확인:
  > "이 화면은 로그인이 필요해 보입니다. (a) 미리 로그인된 세션으로 접속하셨다면 그대로 진행하고, (b) 자동 로그인 시도를 원하시면 ID/PW를 알려주세요."

---

## 실행 흐름

```
1. 입력 파싱 → 테스트 케이스 목록 생성
2. 사용자에게 케이스 목록 확인 (특히 명세→자동도출일 때 필수)
3. Playwright MCP 가용성 확인 (미설치면 위 가이드 출력 후 중단)
4. browser_new_page (Chromium, default headed=false. 사용자가 원하면 headed=true)
5. 각 케이스 루프:
   5-1. browser_navigate(baseUrl + case.url)
   5-2. browser_evaluate(references/mock-interceptor.js 본문)   ← 인터셉터 주입
        - 주입 후 window.__uiTestMockInstalled === true 확인
        - 실패 시 즉시 전체 중단
   5-3. case.mockOverrides 가 있으면 browser_evaluate 로
        window.__uiTestMockOverrides = [...] 세팅 후 인터셉터 재주입
   5-4. 액션 수행 (click / fill_form / type_text / press_key 등)
        - 각 step 사이에 element 가시성/안정 대기 (browser_wait_for)
   5-5. 기대 결과 검증 (텍스트 존재, 요소 visible, count 등)
   5-6. browser_take_screenshot → results/<timestamp>/<TC-ID>.png 저장
   5-7. browser_evaluate("return window.__uiTestMockedRequests") 로 가로챈 요청 회수
   5-8. case 결과 객체 생성 (pass/fail + 상세)
   *** 실패해도 다음 케이스로 계속 진행. 끝까지 돌리고 집계.
6. 결과 집계
   - results/<timestamp>/result.json  (스키마는 references/result-example.json)
   - results/<timestamp>/summary.md   (사람이 읽기 좋은 요약)
7. 사용자에게 요약 출력 + 두 파일 경로 안내
```

---

## 산출물

같은 디렉토리(`results/<YYYY-MM-DD_HH-mm>/`)에 두 종류:

1. **`result.json`** — 구조화 결과. 스키마는 [references/result-example.json](references/result-example.json) 참고.
   - `summary.total / pass / fail / startedAt / endedAt / baseUrl / browser / headed`
   - `cases[]`: `id, name, url, data, steps, expected, actual, status, durationMs, screenshot, consoleErrors, mockedRequests`

2. **`summary.md`** — 사람이 읽는 요약. 다음 형식:

```markdown
# UI Test Run · 2026-05-14 09:12

- Base URL: http://localhost:5173
- 결과: 2/3 pass, 1 fail
- 소요: 28s

| ID | 이름 | 결과 | 스크린샷 |
|---|---|---|---|
| TC-001 | 사용자 목록 조회 | ✅ pass | [📷](TC-001.png) |
| TC-002 | 사용자 생성 (mutation 차단) | ✅ pass | [📷](TC-002.png) |
| TC-003 | 에러 응답 시 토스트 노출 | ❌ fail | [📷](TC-003.png) |

## ❌ 실패 상세

### TC-003 에러 응답 시 토스트 노출
- 기대: 에러 토스트가 보인다 / 모달은 여전히 열려있다
- 실제: 에러 토스트 미노출 (선택자 `.toast--error` 5초 timeout)
- console error 1건 — `TypeError: cannot read property 'message' of undefined ...`

## 차단된 mutation 요청 (총 2건)
- POST http://localhost:5173/api/users  → 200 mocked (TC-002)
- POST http://localhost:5173/api/users  → 500 mocked (TC-003, override)
```

---

## 빠른 결정 트리

```
입력이 화면 명세 markdown인가?
  → 휴리스틱으로 케이스 도출 → 사용자에게 케이스 목록 확인 → 실행

입력이 시나리오 markdown/JSON인가?
  → 그대로 파싱 → 실행

입력이 URL 목록인가?
  → 각 URL smoke test (goto + title + console error 체크) → 실행

baseUrl 모름?
  → 사용자에게 질문

인증 필요?
  → 사용자 사전 로그인 또는 ID/PW 요청 확인

Playwright MCP 미설치?
  → 즉시 중단 + 설치 가이드 출력

테스트 중 일부 케이스 실패?
  → 중단 X. 끝까지 수행 후 집계
```

---

## 제약 사항 (요약)

- **mutation은 절대 백엔드에 안 도달한다.** 인터셉터 주입 실패 = 즉시 중단.
- **자동 로그인 전 사용자 확인 필수.** 안전한 기본값은 "사용자가 미리 로그인한 세션 사용".
- **테스트 실패 즉시 중단 X.** 끝까지 돌리고 집계.
- **screenshot은 항상 캡처** (성공이든 실패든) — 디버깅에 결정적.
- **GET 등 read-only 요청은 그대로 통과** — 실제 데이터 보면서 검증해야 의미 있음.
- **헤드리스 기본**. 사용자가 "headed로 보면서 돌려줘"라고 요청하면 `headed=true`로 시작.
- **각 navigate 후 반드시 인터셉터 재주입.** SPA 라우팅이 아닌 full page navigation 시 reset됨.

---

## 자주 실수하는 것

| 실수 | 결과 | 방어 |
|---|---|---|
| `browser_navigate` 후 인터셉터 재주입 안 함 | 다음 mutation이 실제 백엔드로 감 | 모든 navigate 후 즉시 `browser_evaluate(mock-interceptor.js)` |
| `window.__uiTestMockOverrides` 를 인터셉터 *주입 후* 설정 | override 가 적용 안 됨 | overrides → 인터셉터 순서로 평가 |
| Playwright MCP 도구 목록 확인 없이 진행 | 도중에 도구 호출 실패 | 시작 시 `mcp__playwright__browser_*` 존재 확인 |
| 자동 로그인 임의 시도 | 잘못된 계정 잠금/감사 로그 오염 | 무조건 사용자 확인 먼저 |
| 첫 실패에서 throw | 나머지 케이스 보지 못해 디버깅 비용 증가 | try/catch로 케이스 단위 격리. 결과만 fail로 표시 |
| screenshot 저장 경로를 timestamp 없이 고정 | 다음 실행에 덮어써짐 | `results/<YYYY-MM-DD_HH-mm>/` 디렉토리 사용 |
| mutation을 가로채놓고 결과에 안 기록 | 사용자가 무엇이 차단됐는지 못 봄 | 매 케이스 끝에 `window.__uiTestMockedRequests` 회수 |

---

## 참고 자산

- [references/mock-interceptor.js](references/mock-interceptor.js) — `browser_evaluate` 로 주입할 fetch/XHR 오버라이드 (변경 금지)
- [references/scenario-format.md](references/scenario-format.md) — markdown/JSON 시나리오 + URL 목록 + 명세→시나리오 도출 휴리스틱
- [references/result-example.json](references/result-example.json) — 출력 JSON 스키마 예시
