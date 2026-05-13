# 컴포넌트 카탈로그

`base.html`에 모든 CSS·JS가 이미 들어있다. 본문은 아래 컴포넌트들을 조합해서 채운다. **CSS·JS·class 이름은 절대 변경하지 않는다** — 그대로 가져다 써야 디자인이 보장된다.

---

## 0. 섹션 골격

모든 콘텐츠 섹션은 이 패턴을 따른다. nav 링크의 `href="#sec-xxx"`와 `section-anchor`의 `id`가 일치해야 스크롤 스파이가 동작한다.

```html
<div class="section">
  <span class="section-anchor" id="sec-install"></span>
  <h2><span class="num">02</span> 환경 설치 가이드</h2>

  <h3>하위 섹션 제목</h3>
  <p>본문 텍스트.</p>

  <h4>UPPERCASE 라벨용 소제목</h4>
  <!-- ... -->
</div>
```

- `h2`의 `<span class="num">NN</span>`은 섹션 번호. 두 자리 0-패딩 추천(`01`, `02`).
- `h3`는 자동으로 `--accent`(파랑)으로 칠해진다.
- `h4`는 자동 uppercase + tracking — 짧은 라벨용 ("최종 체크리스트", "주의" 같은).

---

## 1. KPI 카드 (수치 강조)

문서 도입부에 핵심 수치 4~6개를 카드로 배치할 때.

```html
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-val">8분</div>
    <div class="kpi-label">Slack 명령 → PR 생성</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-val">100%</div>
    <div class="kpi-label">E2E 테스트 통과</div>
  </div>
</div>
```

**언제 쓰나** — "수치/지표/달성치"를 한눈에 보여주고 싶을 때. 평범한 텍스트 나열보다 강하게 보인다.

---

## 2. 콜아웃 (info / warn / danger / success)

좌측 색상 바가 있는 박스. 짧은 강조 메시지에.

```html
<div class="callout success">
  <span class="callout-icon">✅</span>
  <span><strong>검증 완료</strong> — 파일럿 결과 요약 한 문장.</span>
</div>

<div class="callout info">
  <span class="callout-icon">ℹ</span>
  <span>참고로 알아두면 좋은 사실.</span>
</div>

<div class="callout warn">
  <span class="callout-icon">⚠</span>
  <span><strong>주의</strong> — 흔히 빠지는 함정.</span>
</div>

<div class="callout danger">
  <span class="callout-icon">🔐</span>
  <span><strong>위험</strong> — 보안/데이터 손실 같은 치명 사항.</span>
</div>
```

**색상 의미**:
- `info` (파랑): 보충 설명, 참고
- `success` (초록): 달성·완료·확인
- `warn` (노랑): 주의, 함정, 임시 상황
- `danger` (빨강): 보안, 위험, 절대 금지

---

## 3. 카드 / 카드 그리드 (블록형 콘텐츠)

```html
<!-- 단일 카드 (긴 본문, 인용, 묶음 정보) -->
<div class="card">
  <h4>Gate 1 통과 조건</h4>
  <ul>
    <li>review 차단 코멘트 0개</li>
    <li>QA 모든 시나리오 통과</li>
  </ul>
</div>

<!-- 미니 카드 그리드 (3~4개 항목 비교) -->
<div class="card-grid">
  <div class="mini-card">
    <div class="mc-title">🔐 자격증명 격리</div>
    <div class="mc-body">vault 사용자 분리로 키가 직접 노출되지 않음</div>
  </div>
  <div class="mini-card">
    <div class="mc-title">🛡 5층 보안</div>
    <div class="mc-body">SOUL → 정책 → 샌드박스 → 네트워크 → 감사</div>
  </div>
</div>
```

**언제 쓰나** — "특징 4가지", "옵션 3가지" 같은 짧고 평행한 항목들. 각 항목이 1~2문장이면 mini-card, 더 길면 card.

---

## 4. 태그/뱃지

테이블 셀, 인라인 강조, 분류 라벨.

```html
<span class="tag tag-green">완료</span>
<span class="tag tag-yellow">진행중</span>
<span class="tag tag-red">차단</span>
<span class="tag tag-blue">정보</span>
<span class="tag tag-purple">Step 1</span>
<span class="tag tag-orange">XL</span>
```

**색상 매핑** — green=성공/통과, yellow=주의/대기, red=실패/위험, blue=정보, purple=단계/그룹, orange=경고/규모 큼.

---

## 5. 테이블

비교, 명세, 카탈로그 형태의 데이터.

```html
<div class="tbl-wrap">
  <table>
    <thead>
      <tr><th>위험 ID</th><th>위험</th><th>완화 방법</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="tag tag-red">R1</span></td>
        <td>데이터 유출 — API 토큰 노출</td>
        <td>vault 격리 + 화이트리스트</td>
      </tr>
    </tbody>
  </table>
</div>
```

**원칙**:
- 항상 `<div class="tbl-wrap">`로 감싼다 (모바일 가로 스크롤 + 테두리 라운드).
- 첫 컬럼에 `<span class="tag">` 넣어 식별자/분류를 시각화하면 좋다.
- 셀 안에 `<code>`도 자연스럽게 어울린다.

---

## 6. 코드 블록

`<pre><code>...</code></pre>`로 감싸기만 하면 JS가 자동으로:
- `.code-block` wrapper 추가
- 언어 자동 감지 (yaml/javascript/bash/workflow/python/sql)
- `Copy` 버튼 추가

```html
<pre><code># 그냥 코드 그대로 적기. JS가 자동 처리.
sudo apt update
npm install -g @anthropic-ai/claude-code</code></pre>
```

**주의**: HTML 안에 작성할 때는 `<` `>` `&`를 escape 해야 한다 → `&lt;`, `&gt;`, `&amp;`.

인라인 코드는 그냥 `<code>npm install</code>`. 자동으로 회색 배경 + 테두리.

---

## 7. 단계 리스트 (steps)

번호가 매겨진 절차. 단계마다 동그란 번호 + 본문.

```html
<ul class="steps">
  <li>
    <span class="step-num">1</span>
    <div class="step-body"><strong>Workspace 준비</strong> — 전용 워크스페이스 생성 후 채널 분리.</div>
  </li>
  <li>
    <span class="step-num">2</span>
    <div class="step-body"><strong>App 생성</strong> — From scratch → 이름 입력.</div>
  </li>
</ul>
```

**언제 쓰나** — 순서가 중요한 설치/설정 절차. 5~10단계 정도가 보기 좋다.

---

## 8. 신뢰 경계 카드 (trust-card, 4색)

신호등 식 분류 (g/y/r/b).

```html
<div class="trust-grid">
  <div class="trust-card g">
    <div class="tc-title">🟢 GREEN — 완전 신뢰</div>
    <div>운영자 직접 키 입력<br>GitHub Environment 시크릿</div>
  </div>
  <div class="trust-card y">
    <div class="tc-title">🟡 YELLOW — 조건부</div>
    <div>검토 완료 결과</div>
  </div>
  <div class="trust-card r">
    <div class="tc-title">🔴 RED — 불신</div>
    <div>외부 입력</div>
  </div>
  <div class="trust-card b">
    <div class="tc-title">🔵 BLUE — 격리</div>
    <div>권한 경계</div>
  </div>
</div>
```

**언제 쓰나** — 보안 분류, 우선순위 분류, 위험도 매트릭스 등 4단계 색상 구분이 필요할 때.

---

## 9. 레이어 리스트 (계층 구조)

L1, L2, ... 식 단계별 설명. 좌측에 작은 파란 뱃지.

```html
<div class="layer-list">
  <div class="layer-item">
    <span class="layer-badge">L1</span>
    <div class="layer-body">
      <strong>SOUL — 행동 규칙</strong><br>
      <span style="color:var(--text2);font-size:12px">민감 파일 읽기 금지, rm -rf 실행 금지</span>
    </div>
  </div>
  <div class="layer-item">
    <span class="layer-badge">L2</span>
    <div class="layer-body">
      <strong>정책 — tool deny</strong><br>
      <span style="color:var(--text2);font-size:12px">허용/차단 룰</span>
    </div>
  </div>
</div>
```

**언제 쓰나** — 보안 가드레일, 추상화 계층, 의존 스택 등 "위에서 아래로" 구조.

---

## 10. 파이프라인 (가로 흐름)

`A → B → C → D` 식 단계 흐름. 가로 또는 세로(`flex-direction:column`)로.

```html
<!-- 가로 -->
<div class="pipeline">
  <div class="pipe-step">① Slack 명령</div>
  <span class="pipe-arrow">→</span>
  <div class="pipe-step">② GH dispatch</div>
  <span class="pipe-arrow">→</span>
  <div class="pipe-step">③ 실행 → PR</div>
</div>

<!-- 세로 (긴 단계 설명) -->
<div class="pipeline" style="flex-direction:column;align-items:flex-start">
  <div class="pipe-step" style="width:100%">Slack: <code>/dev "..."</code></div>
  <div class="pipe-arrow">↓</div>
  <div class="pipe-step" style="width:100%">git clone → 보안 검토 → 취약점 목록</div>
  <div class="pipe-arrow">↓</div>
  <div class="pipe-step" style="width:100%">테스트 자동 실행 → 47/47 통과</div>
</div>
```

**언제 쓰나** — 워크플로/요청 흐름/처리 단계. 단계가 4~6개면 가로, 7개 이상이거나 각 단계 설명이 길면 세로.

---

## 11. 스킬/역할 카드 (skill-grid)

팀 역할, 스킬 카탈로그 — 이름·역할·설명 3행 구조.

```html
<div class="skill-grid">
  <div class="skill-card">
    <div class="sk-name">/work</div>
    <div class="sk-role">메타스킬</div>
    <div class="sk-body">표준 4단계 절차 강제, 인계 프로토콜.</div>
  </div>
  <div class="skill-card">
    <div class="sk-name">GSD</div>
    <div class="sk-role">프로젝트 관리</div>
    <div class="sk-body">요구사항 인터뷰, 로드맵, phase 추적.</div>
  </div>
</div>
```

---

## 12. 경고 카드 (warn-card, 빨간 박스)

**중요 보안 체크리스트** 같은 강조용. 개별 콜아웃과 다르게 묶음 형태.

```html
<div class="warn-card">
  <div class="warn-card-title">보안 체크리스트 — 운영 중 항상 유지</div>
  <ul class="warn-list">
    <li><strong>인터넷 검색 금지</strong> — egress allowlist 엄격 유지.</li>
    <li><strong>시크릿 하드코딩 금지</strong> — gitleaks 자동 스캔.</li>
  </ul>
</div>
```

---

## 13. 로드맵 (단계별 큰 페이즈)

Week 1, Week 2... 같은 굵직한 단계.

```html
<div class="roadmap">
  <div class="phase">
    <div class="phase-num">1</div>
    <div class="phase-body">
      <div class="phase-title">Week 1 — 기반 구축</div>
      <div class="phase-desc">WSL2 + 사용자 분리 + 패키지 설치 + vault 부트스트랩.</div>
    </div>
  </div>
  <div class="phase">
    <div class="phase-num">2</div>
    <div class="phase-body">
      <div class="phase-title">Week 2 — 가드레일 + 스킬</div>
      <div class="phase-desc">5층 보안 + 4종 스킬 설치 + 스모크 테스트 통과.</div>
    </div>
  </div>
</div>
```

**언제 쓰나** — `pipeline`이 짧은 단계용이라면, `roadmap`은 각 단계 자체가 큰 묶음일 때.

---

## 14. 체크리스트

```html
<ul class="checklist">
  <li>오늘의 세션 목록 확인</li>
  <li>INDEX.md 누락 spec 없음</li>
  <li>API 사용량 70% 미만</li>
</ul>
```

**자동 좌측 ☐ 마크 + 항목별 구분선**. 체크 가능한 항목 나열에.

---

## 15. Before/After 카드 (org-card)

역할 변화, 변경 비교. `<del>` 줄 + 새 설명.

```html
<div class="org-grid">
  <div class="org-card">
    <div class="oc-role">하위 개발자</div>
    <div class="oc-before">반복 코딩, CRUD 구현</div>
    <div class="oc-after">스킬 검증·유지보수, 골든케이스 설계</div>
  </div>
</div>
```

`oc-before`는 자동 line-through. before가 없으면 빈 div를 넣지 말고 그냥 생략.

---

## 16. 인라인 스타일 패턴

자주 필요한 인라인 변형:

```html
<!-- 본문 회색으로 보조 설명 -->
<span style="color:var(--text2);font-size:12px">보조 설명</span>

<!-- 강조 색 (성공) -->
<span style="color:var(--green);font-weight:500">새 평가 기준</span>

<!-- 카드에 위쪽 마진 -->
<div class="card" style="margin-top:12px">...</div>

<!-- 줄긋기 (사라짐) -->
<span style="text-decoration:line-through">기존 방식</span>
```

CSS 변수(`var(--text2)`, `var(--green)` 등)를 그대로 쓰면 색이 일관된다. 하드코딩하지 말 것.

---

## 17. nav 구성

각 섹션마다 nav 링크 한 개. `nav-brand`는 짧은 식별자(문서 약칭).

```html
<nav>
  <div class="nav-inner">
    <span class="nav-brand">문서 약칭 v01</span>
    <a href="#sec-overview">개요</a>
    <a href="#sec-install">설치</a>
    <a href="#sec-security">보안</a>
    <a href="#sec-faq">FAQ</a>
  </div>
</nav>
```

스크롤 시 자동으로 active 표시 — JS가 처리한다. **`href`와 `section-anchor`의 `id`만 일치시키면 끝.**

---

## 빠른 매핑 가이드 — 어떤 정보를 어느 컴포넌트로?

| 입력 정보 형태 | 추천 컴포넌트 |
|---|---|
| 핵심 수치 4~6개 | KPI grid |
| 한 문장 강조 | callout (info/warn/danger/success) |
| 특징/장점 3~4개 | mini-card grid |
| 비교/명세 표 | table |
| 명령어/코드 | `<pre><code>` (자동 감지·복사) |
| 절차 5~10단계 | steps |
| 4색 분류 | trust-grid |
| 계층 L1~L5 | layer-list |
| 짧은 흐름 A→B→C | pipeline (가로) |
| 긴 단계별 흐름 | pipeline (세로) |
| 큰 단계 (주차/페이즈) | roadmap |
| 역할/스킬 카탈로그 | skill-grid |
| 보안 체크리스트 묶음 | warn-card |
| 가능한지 확인 항목 | checklist |
| 변화 전후 비교 | org-grid |
| 위험·이슈 카탈로그 | table + tag |
| FAQ 한 항목 | `<div class="card">` (h3 + 본문) |
