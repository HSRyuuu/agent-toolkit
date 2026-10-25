---
name: html-docs-creator
description: >
  Use when converting user-provided text, meeting notes, plans, specs, reports,
  bullet lists, or spoken notes into one self-contained HTML document. Triggers:
  "이 내용 HTML로 정리해줘", "보고서/계획서/설계서 HTML로", "문서 HTML 변환",
  "회의 내용 HTML 페이지로", "단일 파일 HTML 문서", "self-contained HTML report",
  "/html-docs-creator". Do NOT use for PDF/DOCX output or framework apps.
---

# html-docs-creator — 단일 파일 HTML 문서 생성기

## 이 스킬이 하는 일

어떤 형태의 input(문서·구두 설명·bullet 메모·녹취 텍스트)이든 받아서, **하나의 `.html` 파일**로 출력한다. 그 파일은:

- **외부 의존 0** — CDN, 폰트 링크, JS 라이브러리 모두 없음. 더블클릭만 하면 어디서든 열린다.
- **노션 화이트모드 + HP Electric Blue (#024ad8)** 단일 강조 컬러 시스템.
- **상단 고정 nav** + **스크롤 스파이**(현재 섹션 자동 하이라이트) + **`<pre>` 자동 처리**(언어 감지 라벨 + Copy 버튼) 가 기본 내장.
- max-width 860px의 긴 글 읽기 최적화 레이아웃.

레퍼런스 결과물: `workspace/오픈클로_개발환경_구축_계획서_Windows_WSL_2026-04-22_v05.html`

---

## 워크플로우 (4단계)

### Step 1 — 입력 분류

사용자가 무엇을 줬는지 먼저 확인한다.

| 입력 형태 | 처리 방법 |
|---|---|
| 정형 문서(이미 섹션이 잡힌 markdown/텍스트) | 섹션 그대로 매핑 |
| 비정형 메모/구두 설명 | 의미 단위로 섹션을 직접 끊어준다 |
| 짧은 한두 줄 요청만 | **사용자에게 1~2가지만 추가 질문**한다 (제목, 주요 섹션, 톤) |

> 입력 길이가 매우 짧을 때는 환각을 채워 넣지 말고 사용자에게 "어떤 섹션이 필요하냐"고 물어보는 편이 낫다.

### Step 2 — 섹션 설계 (= nav 항목 설계)

생성될 문서의 **섹션 목록을 먼저 결정**한다. 이게 곧 nav 링크가 된다. 5~12개가 보기 좋다.

전형 패턴(없는 섹션은 빼고, 필요한 섹션은 추가):

```
01 개요/핵심 결론       ← 도입부 KPI + 한 문단 요약
02 설치/시작 가이드     ← steps + pre code
03 상세 설명/구조       ← layer-list, table
04 ...
NN 주의사항             ← warn-card
NN+1 발전 방향/로드맵   ← roadmap
NN+2 FAQ                ← card 반복
```

각 섹션에 `id="sec-xxx"` (kebab-case) 를 부여한다.

### Step 3 — 컴포넌트 매핑

각 섹션의 콘텐츠를 어떤 컴포넌트로 표현할지 정한다.

**반드시 [references/components.md](references/components.md)를 읽고** 매핑 가이드 표(섹션 17 끝)를 참고한다. CSS class 이름을 임의로 바꾸지 않는다. 임의 색·임의 폰트도 추가하지 않는다.

### Step 4 — base.html 채우기 + 출력

1. [templates/base.html](templates/base.html)을 그대로 복사한다.
2. 다음 placeholder를 치환:
   - `{{TITLE}}` — `<title>` 태그 안 (브라우저 탭 제목)
   - `{{NAV_BRAND}}` — 좌상단 짧은 식별자 (예: "오픈클로 v05 WIN")
   - `{{DOC_TITLE}}` — 첫 `<h1>` 안 큰 제목
   - `{{DOC_META}}` — 제목 아래 회색 메타 한 줄 (날짜·버전·기준 등)
   - `{{FOOTER_LINE_1}}`, `{{FOOTER_LINE_2}}` — 하단 푸터
3. `<nav>` 안의 `<a>` 들을 Step 2의 섹션 목록으로 교체한다.
4. `<main>` 안에 섹션별 `<div class="section">...</div>` 블록을 추가한다.
5. **CSS와 `<script>` 블록은 절대 건드리지 않는다.** 자동 동작이 깨진다.
6. 결과물 파일명: `{주제어}_{유형}_{YYYY-MM-DD}_v{NN}.html` 권장. 사용자가 다른 규칙을 주면 따른다.

저장 위치 — 사용자가 명시 안 했으면 `workspace/` 또는 현재 cwd. 명시했으면 그 경로.

---

## 디자인 핵심 원칙 (어겨선 안 되는 것)

1. **외부 CDN 금지** — 결과물은 단일 파일. `<link href="https://...">` `<script src="https://...">` 추가 금지. 시스템 폰트(`-apple-system, 'Segoe UI', 'Noto Sans KR'`, 코드는 `'SF Mono'` 계열)만.
2. **색은 CSS 변수로만** — `var(--accent)`, `var(--green)`, `var(--text2)` 식. `#3366ff` 식 하드코딩 금지.
3. **강조 컬러는 HP Electric Blue 단일** — 다른 강조색을 추가하지 않는다. 시맨틱은 green/yellow/red 만 쓴다.
4. **컴포넌트 class 변경 금지** — `.kpi-card`, `.callout`, `.mini-card` 같은 이름을 그대로 사용. 새 class를 임의로 만들지 않는다.
5. **`<pre><code>`는 그대로** — JS가 자동으로 wrap·라벨·copy 버튼을 추가한다. 미리 `<div class="code-block">`로 감싸지 말 것 (이중 wrap).
6. **HTML 안 코드는 escape** — `<pre>` 안에 `&`·`<`·`>` 가 등장하면 `&amp;`·`&lt;`·`&gt;` 로 변환.
7. **nav `href`와 `section-anchor` `id` 일치** — 둘이 어긋나면 스크롤 스파이 작동 안함.
8. **max-width 860px 유지** — `<main>`의 너비를 임의로 늘리지 않는다. 긴 글 가독성 기준.

---

## 빠른 결정 트리

```
입력 길이 너무 짧음(2~3줄)?
  → 사용자에게 제목·섹션 목록·톤 1~2가지 질문
  → 답 받으면 진행

입력에 표/명세가 많음?
  → table + tag 위주로 매핑

입력에 절차/단계가 많음?
  → steps + pre code + roadmap

입력이 비교/장단점 분석?
  → mini-card grid + table + callout

입력이 보안·위험 카탈로그?
  → table(tag) + warn-card + trust-grid + layer-list

입력이 회의록·발표자료?
  → KPI grid(핵심 수치) + section별 mini-card / table / pipeline

확신 안 설 때:
  → references/components.md 의 §빠른 매핑 가이드 표 참고
```

---

## 최종 검증 체크리스트

HTML을 쓰고 난 뒤 사용자에게 넘기기 전에 빠르게 확인:

- [ ] 외부 URL이 `<head>`나 `<body>`에 들어있지 않다 (`grep -E 'href="https?://|src="https?://'`)
- [ ] CSS의 `:root` 토큰을 그대로 유지했다 (변경 안함)
- [ ] `<script>` 블록을 그대로 유지했다 (코드 자동 처리·nav 스파이)
- [ ] nav의 모든 `<a href="#sec-XXX">`에 대응되는 `id="sec-XXX"`가 본문에 존재
- [ ] `<pre>` 안의 `<`, `>`, `&` 가 escape 됨
- [ ] `<h1>`은 한 개, 각 섹션은 `<h2><span class="num">NN</span> 제목</h2>` 형식
- [ ] 모든 `class` 이름이 base.html에 정의된 것만 사용 (임의 클래스 X)
- [ ] 브라우저로 한 번 열어봄 (`open <파일>`) — nav 클릭, 코드 Copy 버튼, 모바일 폭 정상 동작

---

## 입력 → 출력 매핑 예시

**Input**: "사내 React 프로젝트 코드 컨벤션 정리해줘. 폴더 구조, 네이밍 룰, 금지 패턴, 검토 체크리스트가 필요해."

**섹션 설계**:
1. `sec-overview` — 한 문단 요약 + KPI(룰 개수 같은 수치)
2. `sec-folders` — 폴더 구조: `<pre>` 트리 + 카드
3. `sec-naming` — 네이밍 룰: table
4. `sec-forbidden` — 금지 패턴: warn-card + table(tag-red)
5. `sec-review` — 검토 체크리스트: checklist

**컴포넌트 선택 결과**: KPI grid 1개, table 2개, warn-card 1개, checklist 1개, pre code 1~2개. 끝.

---

## 자주 실수하는 것

| 실수 | 결과 | 방어 |
|---|---|---|
| nav `<a>`에 `href="#section1"`, anchor에 `id="sec-section1"` | 스크롤 스파이가 작동 안 한다 | href와 id를 똑같이 적는다 |
| `<pre>`를 `<div class="code-block">`로 미리 감쌈 | JS가 한 번 더 감싸 이중 wrapper | 그냥 `<pre><code>`만 적는다 |
| 새 색상을 인라인으로 추가 (`style="color:#ff0066"`) | 일관성 깨짐 | 기존 시맨틱 색 재활용 (`var(--red)` 등) |
| 표 안에 직접 줄바꿈 `<br>` 남발 | 모바일에서 깨짐 | 셀이 길면 차라리 행을 분리 |
| `<pre>` 안에 raw `&` 사용 | 브라우저가 entity로 해석 | `&amp;` 로 escape |
| h1을 여러 개 사용 | SEO·접근성 저하 | 문서당 h1 한 개. 섹션은 h2 |

---

## 참고 자산

- [templates/base.html](templates/base.html) — CSS·JS·구조 풀패키지 (이걸 복사해서 시작)
- [references/components.md](references/components.md) — 17개 컴포넌트 카탈로그 + 매핑 가이드
- `workspace/오픈클로_개발환경_구축_계획서_Windows_WSL_2026-04-22_v05.html` — 최종 결과물 레퍼런스 (이 디자인 그대로 재현하는 게 목표)
