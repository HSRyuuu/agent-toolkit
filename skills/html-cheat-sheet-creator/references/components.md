# Components Reference — html-cheat-sheet-creator

CSS class·id·`data-*` 속성 이름은 임의로 바꾸지 않는다. 이 파일에 적힌 그대로 복사해서 쓴다.

---

## 0. 테마 (6종) & 탭 레이아웃

### 사용 가능한 `data-theme` 값

| 테마 | 색 |
|---|---|
| `tech` | sky-blue `#0284c7` |
| `soft` | orange `#c2410c` |
| `mint` | green `#15803d` |
| `lilac` | purple `#7c3aed` |
| `pink` | magenta `#be185d` |
| `sky` | indigo `#1d4ed8` |

테마는 cascade로 적용된다. `<section data-theme="mint">` 안의 모든 카드·카테고리 헤더·details 색이 자동으로 mint 톤이 된다. 사이드바도 `<div class="side-part" data-theme="mint">`로 감싸면 같은 톤 적용.

### `data-cols` 레이아웃 표

| N | 시각 |
|---|---|
| `data-cols="2"` | 가로 2 |
| `data-cols="3"` | 가로 3 |
| `data-cols="4"` | 2 × 2 |
| `data-cols="5"` | 위 3 + 아래 2 |
| `data-cols="6"` | 3 × 2 |

**N과 실제 `<button class="tab-btn">` 개수가 일치해야 한다.**

---

## 1. 상단 탭 (2~6개)

```html
<!-- 4탭 예시 (2x2) -->
<div class="topbar">
  <button class="menu-btn" id="sidebarOpen">☰</button>
  <div class="tabs" data-cols="4">
    <button class="tab-btn active" data-target="tab-1" data-theme="tech">기본<span class="count">12</span></button>
    <button class="tab-btn"        data-target="tab-2" data-theme="soft">응용<span class="count">8</span></button>
    <button class="tab-btn"        data-target="tab-3" data-theme="mint">데이터<span class="count">10</span></button>
    <button class="tab-btn"        data-target="tab-4" data-theme="lilac">UX<span class="count">6</span></button>
  </div>
</div>
```

- `count` `<span>`은 선택. 빼도 됨.
- `data-theme` 값과 사이드바·섹션의 `data-theme` 값은 동일해야 한다.

---

## 2. 사이드바 구조

### 2-1. 전체 골격

```html
<aside class="sidebar" id="sidebar">
  <div class="sidebar-head">
    <div class="title">📑 (sidebar title)</div>
    <button class="close-btn" id="sidebarClose">✕</button>
  </div>
  <div class="sidebar-body">
    <!-- 탭 1개당 side-part 1개 -->
    <div class="side-part" data-theme="tech">
      <div class="side-section-title">A. 기본</div>
      <div class="side-cat">A. Cat1</div>
      <a class="side-link" href="#q-a1">…</a>
      <a class="side-link" href="#q-a2">…</a>
      <div class="side-cat">B. Cat2</div>
      <a class="side-link" href="#q-b1">…</a>
    </div>

    <div class="side-part" data-theme="soft">
      <div class="side-section-title">B. 응용</div>
      <div class="side-cat">C. Cat3</div>
      <a class="side-link" href="#q-c1">…</a>
    </div>

    <!-- … 3~6번째 part는 같은 패턴으로 추가 -->
  </div>
</aside>
```

### 2-2. 사이드바 링크 (1라인)

```html
<a class="side-link" href="#q-a1">
  <span class="num">A1</span>
  <span>항목 라벨 (한 줄)</span>
  <span class="stars">★★★★</span>
</a>
```

- `stars`는 선택. 빼면 그 자리만 비어있음.
- `href`는 article id와 **정확히 일치**해야 한다.
- 링크 톤은 부모 `.side-part`의 `data-theme`에서 자동 상속.

### 2-3. 사이드바 카테고리 헤더

```html
<div class="side-cat">A. 카테고리 이름</div>
```

`<a>`가 아니라 `<div>`. 클릭 대상이 아니다.

### 2-4. 사이드바 part 헤더

```html
<div class="side-section-title">A. 탭 이름</div>
```

부모 `.side-part[data-theme="…"]`로부터 색을 받는다. 별도 클래스 불필요.

---

## 3. 카테고리 헤더 (본문)

```html
<div id="cat-a" class="cat-head">
  <div class="cat-id">CATEGORY A</div>
  <h3>카테고리 제목</h3>
  <div class="cat-desc">한 줄 컨텍스트 설명 (선택).</div>
</div>
```

부모 `<section data-theme="…">`에서 톤이 cascade 됨. 별도 class 불필요.

- id 규칙: `cat-a` ~ `cat-p` (영문 1자, 전역 유일).

---

## 4. 카드 변형 (6종)

### 4-1. 최소형 — 제목 + 본문만

명령어, 단축키, 짧은 정의에 적합.

```html
<article id="q-a1" class="q">
  <h4 class="q-title">
    <span class="qnum">A1</span>
    <span class="qtitle-txt">명령어 이름</span>
  </h4>
  <div class="qbody">
    한 줄 설명. <code>command --flag</code> 처럼 인라인 코드 포함 가능.
  </div>
</article>
```

### 4-2. 최소형 + 중요도

```html
<article id="q-a2" class="q">
  <h4 class="q-title">
    <span class="qnum">A2</span>
    <span class="qtitle-txt">제목</span>
    <span class="stars">★★★★★</span>
  </h4>
  <div class="qbody">…</div>
</article>
```

### 4-3. 본문 + 보조 메모 (followup)

체크리스트나 짧은 부연이 필요할 때.

```html
<article id="q-a3" class="q">
  <h4 class="q-title">
    <span class="qnum">A3</span>
    <span class="qtitle-txt">제목</span>
  </h4>
  <div class="qbody">본문.</div>
  <div class="followup">
    <div class="label">메모</div>
    <ul>
      <li>주의점 1</li>
      <li>주의점 2</li>
    </ul>
  </div>
</article>
```

`label` 텍스트는 자유 (Follow-up / Notes / 체크 / Tip 등).

### 4-4. 본문 + 펼치기 (details)

핵심은 짧게 본문, 자세한 설명은 펼치기로 숨김.

```html
<article id="q-a4" class="q">
  <h4 class="q-title">
    <span class="qnum">A4</span>
    <span class="qtitle-txt">개념 이름</span>
    <span class="stars">★★★</span>
  </h4>
  <div class="qbody">한 줄 정의.</div>
  <details class="answer">
    <summary>💡 자세히 보기</summary>
    <div class="ans-body">
      <p>긴 설명, 예시, 반례 등.</p>
    </div>
  </details>
</article>
```

`summary` 텍스트는 자유. **`<summary>`는 `<details>`의 첫 자식이어야 한다.**

### 4-5. 본문 + followup + 펼치기 (완전형)

```html
<article id="q-a5" class="q">
  <h4 class="q-title">
    <span class="qnum">A5</span>
    <span class="qtitle-txt">제목</span>
    <span class="stars">★★★★</span>
  </h4>
  <div class="qbody">질문 또는 핵심 요약.</div>
  <div class="followup">
    <div class="label">CHECK</div>
    <ul>
      <li>체크 1</li>
      <li>체크 2</li>
    </ul>
  </div>
  <details class="answer">
    <summary>💡 답</summary>
    <div class="ans-body">… (아래 ans-body 컴포넌트 참고)</div>
  </details>
</article>
```

### 4-6. 테마별 카드

카드는 부모 `<section data-theme="…">`에서 톤을 받는다. 카드 자체에는 테마 class 불필요.

```html
<section id="tab-3" class="section" data-theme="mint">
  …
  <article id="q-c1" class="q">… mint 톤 자동 적용 …</article>
</section>
```

---

## 5. ans-body 안에서 쓸 수 있는 컴포넌트

`<details>` 안의 `.ans-body` 영역.

### 5-1. 섹션 헤더 (h5)

```html
<h5>섹션 헤더 (대문자·테마색)</h5>
```

자동 대문자화·tracking 적용. 테마색은 cascade로.

### 5-2. 강조 / 인라인 코드

```html
<p>일반 텍스트에 <strong>강조</strong>는 흰색, <code>inline code</code>는 노랑.</p>
```

### 5-3. 인용/예시 박스

```html
<div class="quote">"여기에 예시 문장 / 인용구를 넣는다."</div>
```

이탤릭·왼쪽 보더·연한 회색.

### 5-4. 핵심 키워드 박스 (녹색)

```html
<div class="tech-req">
  <span class="lab">✅ KEY POINTS</span>
  키워드 1 / 키워드 2 / 키워드 3
</div>
```

`lab` 텍스트와 그 뒤 본문 모두 자유. 톤은 항상 녹색(전역 `--ok`).

### 5-5. 리스트

```html
<ul>
  <li>점 1</li>
  <li>점 2</li>
</ul>

<ol>
  <li>1단계</li>
  <li>2단계</li>
</ol>
```

---

## 6. 뱃지 (Hero 영역)

```html
<span class="badge">테마색 뱃지 (cascade)</span>
<span class="badge tip">회색 뱃지 (메타 정보)</span>
```

`.badge` 단독은 부모 색에서 cascade 받는다. 즉, hero 외부 wrap엔 `data-theme`이 없으므로 폴백 색(tech 톤). 다른 톤을 주려면 hero를 감싸는 부모에 `data-theme`을 추가:

```html
<header class="hero" data-theme="mint">
  …
  <span class="badge">mint 톤</span>
</header>
```

---

## 7. 색 팔레트 변경하기

CSS `:root`와 `[data-theme="…"]` 매핑이 분리되어 있어, 두 가지 방법이 있다.

### 7-1. 폴백 색 (테마 미지정 영역)

```css
:root {
  --theme-color: #0284c7;  /* 폴백 */
  --theme-rgb: 2 132 199;
}
```

### 7-2. 개별 테마 색

```css
[data-theme="tech"]  { --theme-color: #0284c7; --theme-rgb: 2 132 199; }
[data-theme="soft"]  { --theme-color: #c2410c; --theme-rgb: 194 65 12; }
[data-theme="mint"]  { --theme-color: #15803d; --theme-rgb: 21 128 61; }
[data-theme="lilac"] { --theme-color: #7c3aed; --theme-rgb: 124 58 237; }
[data-theme="pink"]  { --theme-color: #be185d; --theme-rgb: 190 24 93; }
[data-theme="sky"]   { --theme-color: #1d4ed8; --theme-rgb: 29 78 216; }
```

여기서 한 줄만 바꾸면 그 테마를 쓰는 모든 영역의 톤이 바뀐다. `--theme-rgb`는 `rgb()` 함수에 그대로 들어가므로 R G B를 **공백으로** 구분한 3 숫자여야 한다 (콤마 X).

### 7-3. 전역 팔레트

| 변수 | 의미 | 기본값 |
|---|---|---|
| `--bg` | 배경 | `#ffffff` |
| `--panel` | 카드 배경 / 사이드바 | `#f7f8fb` |
| `--panel-2` | hover 배경 | `#eef0f5` |
| `--line` | 보더 | `#e2e5ec` |
| `--text` | 본문 | `#1a1d24` |
| `--text-dim` | 부가 텍스트 | `#5b6477` |
| `--accent` | stars 색 (모든 테마 공통) | `#b45309` (amber) |
| `--ok` | tech-req 보더 / 키워드 박스 | `#15803d` (green) |

---

## 8. 절대 변경 금지 항목

| 항목 | 이유 |
|---|---|
| `<section id="tab-1">` ~ `<section id="tab-6">` ID 형식 | JS가 `data-target`으로 참조 |
| `data-target="tab-N"`, `data-cols="N"`, `data-theme="…"` 속성 | 탭 활성화·레이아웃·테마 cascade JS/CSS |
| `<button id="sidebarOpen">`, `id="sidebarClose"`, `id="sidebarBackdrop"`, `id="sidebar"` | JS event 바인딩 |
| `class="side-link"`, `class="tab-btn"`, `class="cat-head"`, `class="q"`, `class="side-part"` | JS selector / CSS cascade |
| `<script>` 블록 전체 | 위 식별자에 의존. 손대면 전부 깨짐 |
| CSS의 `[data-theme="…"]` 변수 매핑 | 톤이 사라짐 |
