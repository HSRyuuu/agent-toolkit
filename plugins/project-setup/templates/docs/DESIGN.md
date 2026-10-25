# {PROJECT_NAME} Design System

> 이 문서는 프로젝트의 **시각 정체성·컴포넌트 스타일·인터랙션 규칙**을 한 곳에 정리한다.
> Claude가 UI 코드를 작성/수정할 때 색상·타이포·간격을 추측하지 않고 이 문서만 참조하면 되도록 만든다.
>
> **작성 원칙**
> - 토큰(색상·간격·라운딩)은 **CSS 변수명과 실제 값**을 함께 적는다. 추후 다크 모드/리브랜딩 시 변수만 바꾸면 된다.
> - 컴포넌트별 스타일은 **현재 코드와 일치하는 값**만 적는다. "권장값"이 아니라 "현재 그렇게 되어 있는 값".
> - 변경하면 즉시 갱신한다. 디자인 토큰의 드리프트는 UI 일관성 붕괴로 직결된다.

---

## 1. Visual Theme & Atmosphere

> 이 프로젝트가 어떤 인상을 추구하는지 한두 단락으로 적는다. 톤 & 매너, 타깃 사용자, 핵심 비주얼 결정.

<예: "{PROJECT_NAME}는 전문적이면서도 접근하기 쉬운 ___의 인상을 추구한다. 디자인 언어는 ___ 배경과 ___ 보더를 기반으로 ___이 시각적 앵커 역할을 한다.">

**Key Characteristics:**
- <뉴트럴/컬러풀 캔버스 — 한 줄 설명>
- <브랜드 앵커 (예: 그라디언트 사이드바)>
- <대표 폰트 (예: Pretendard Variable — 한글 최적화)>
- <인터랙션 철학 (예: 절제된 호버 효과, opacity 변화 위주)>
- <다크 모드 지원 여부 및 방식>
- <아이콘 시스템 (라이브러리·기본 크기)>
- <카드 라운딩 등 시그니처 디테일>

---

## 2. Color Palette & Roles

### Primary Brand

| Name | Light | Dark | Usage |
|------|-------|------|-------|
| **Primary** | `<#hex>` | `<#hex>` | <CTA·활성·링크 등> |
| **Primary Foreground** | `<#hex>` | `<#hex>` | Primary 위 텍스트 |
| **Brand Accent** | `<#hex>` | `<#hex>` | <포커스 링·하이라이트> |

### Semantic Colors

| Name | Light | Dark | Usage |
|------|-------|------|-------|
| **Success** | `<#hex>` | `<#hex>` | 정상·성공·완료 |
| **Warning** | `<#hex>` | `<#hex>` | 경고·대기 |
| **Destructive** | `<#hex>` | `<#hex>` | 에러·삭제·실패 |
| **Info** | `<#hex>` | `<#hex>` | 정보·중립 알림 |

### Neutral Scale

| Name | Light | Dark | Usage |
|------|-------|------|-------|
| **Background** | `<#hex>` | `<#hex>` | 페이지 배경 |
| **Foreground** | `<#hex>` | `<#hex>` | 기본 텍스트 |
| **Card** | `<#hex>` | `<#hex>` | 카드/패널 배경 |
| **Muted** | `<#hex>` | `<#hex>` | 비활성·뱃지 배경 |
| **Muted Foreground** | `<#hex>` | `<#hex>` | 보조 텍스트 |
| **Border** | `<#hex>` | `<#hex>` | 보더·구분선 |

### Status Badge Colors (선택)

| Status | Background (Light) | Text (Light) | Background (Dark) | Text (Dark) |
|--------|--------------------|--------------|--------------------|-------------|
| <상태> | `<#hex>` | `<#hex>` | `<#hex>` | `<#hex>` |

### Shadows

- **Card Hover**: `<box-shadow 값>` — <설명>
- **Tooltip / Floating**: `<box-shadow 값>` — <설명>
- <기타 그림자가 있으면 추가>

---

## 3. Typography Rules

### Font Families

- **Primary**: `<폰트 스택>`
- **Monospace**: `<폰트 스택>`
- **로딩 방식**: `<CDN / Google Fonts / 자체 호스팅 / etc.>`

### Hierarchy

| Role | Size | Weight | Line Height | Notes |
|------|------|--------|-------------|-------|
| Page Title | <px> | <weight> | <lh> | <설명> |
| Card Title | <px> | <weight> | <lh> | <설명> |
| Body | <px> | <weight> | <lh> | <설명> |
| Caption / Sub | <px> | <weight> | <lh> | <설명> |
| Badge | <px> | <weight> | — | <설명> |
| Mono / Code | <px> | <weight> | — | <설명> |

### Principles

- <예: "Weight 700은 숫자/제목 전용">
- <예: "Weight 600은 구조적 강조 (카드 타이틀·테이블 헤더)">
- <예: "Monospace는 기술 데이터 전용 (UUID·API 경로)">

---

## 4. Component Stylings

> 이 섹션은 프로젝트가 실제로 사용하는 컴포넌트만 적는다. 사용하지 않는 컴포넌트(예: 모달이 없는 프로젝트)는 통째로 삭제한다.

### Buttons

**Primary**
- Background: `<token>`
- Text: `<token>`
- Height: `<px>`
- Padding: `<px>`
- Border Radius: `<px>`
- Hover: `<효과>`
- Focus: `<효과>`

**Outline / Ghost / Destructive 등 variant가 있으면 같은 형식으로 추가**

### Cards & Containers

- Background: `<token>`
- Border: `<token>`
- Border Radius: `<px>`
- Padding: `<px>`
- Hover: `<효과>` (있으면)

### Inputs & Forms

- Height: `<px>`
- Border: `<token>`
- Border Radius: `<px>`
- Background: `<token>`
- Focus: `<효과>`
- Placeholder: `<token>`

### Badges

- Shape: `<rounded-full / sharp>`
- Padding: `<px>`
- Font: `<size weight>`
- Variants: `<default / success / warning / destructive>`

### Tabs / Tables / Progress / Navigation 등

> 프로젝트에 있는 컴포넌트만 같은 형식으로 추가한다.

---

## 5. Layout Principles

### Spacing System

- Base unit: **<px>**
- Scale: `<2, 4, 8, 12, 16, 24, 32 ...>`
- Section gaps: `<px>`
- Card padding: `<px>`
- Page padding: `<px>`

### Grid & Container

- Page max-width: `<px>`
- <주요 그리드 — 예: "Stat Grid 4열 (900px+) → 2열 (~900px)">

### Shell Structure

```
<여기에 텍스트로 앱 셸 구조를 그린다 — Sidebar / TopBar / Content 등>
```

### Whitespace Philosophy

- <예: "기능적 여백 — 콘텐츠 그룹핑을 위한 16–24px 외에는 추가 여백 없음">

### Border Radius Scale

| Token | Value | Usage |
|-------|-------|-------|
| Sharp | `<px>` | <설명> |
| Small | `<px>` | <설명> |
| Standard | `<px>` | <설명> |
| Card | `<px>` | <설명> |
| Pill | 9999px | <뱃지·칩> |

---

## 6. Depth & Elevation

| Level | Treatment | Usage |
|-------|-----------|-------|
| Level 0 (Flat) | <설명> | <페이지 배경 등> |
| Level 1 (Contained) | <설명> | <카드·입력 필드> |
| Level 2 (Hover) | <설명> | <카드 호버> |
| Level 3 (Floating) | <설명> | <툴팁·드롭다운> |

**Shadow Philosophy**: <한 단락 — 어떤 상황에 그림자를 쓰고 안 쓰는지>

---

## 7. Dark Mode

> 다크 모드를 지원하지 않으면 이 섹션 통째로 삭제.

### 전환 메커니즘

- <예: "`<html>`에 `.dark` 클래스 토글, Pinia/Zustand store 관리, localStorage 키 `<key>`">
- <시스템 설정(`prefers-color-scheme`) 감지 여부>

### 변환 원칙

- 모든 색상은 CSS 변수 참조 — 하드코딩 금지
- <예: "Semantic 색상은 다크에서 밝기를 한 단계 올려 가독성 확보">

### 특수 처리

- <예: "input[type=date] 캘린더 아이콘: `filter: invert(1)`">
- <예: "스크롤바 색상 다크 변종">

---

## 8. Do's and Don'ts

### Do

- 모든 색상에 CSS 변수(`var(--*)`)를 사용
- <예: "카드는 항상 `border-radius: <px>` + `1px solid var(--border)` 조합">
- <예: "버튼은 `<Button>` 컴포넌트만 사용 — 직접 스타일링 금지">
- <기타 프로젝트 규칙>

### Don't

- 하드코딩된 색상값 사용 금지
- <예: "사이드바 그라디언트 방향/색상 변경 금지 — 브랜드 아이덴티티">
- <예: "Weight 700을 본문 텍스트에 사용 금지">
- <기타 금지 항목>

---

## 9. Responsive Behavior

### Breakpoints

| Name | Width | Key Changes |
|------|-------|-------------|
| Mobile | < <px> | <설명> |
| Tablet | <range> | <설명> |
| Desktop | <px>+ | <설명> |

### Collapsing Strategy

- <예: "Stat Grid 4열 → 2열 (900px 미만)">
- <예: "Sidebar: 펼침 240px / 접힘 64px (아이콘만)">

---

## 10. Animation & Transition

| Element | Property | Duration | Easing | Notes |
|---------|----------|----------|--------|-------|
| <대상> | <property> | <ms> | <easing> | <설명> |

**원칙**: <예: "모든 전환은 0.1–0.3s. 기능적 피드백 목적, 장식 애니메이션 없음">

---

## 11. Agent Prompt Guide

> Claude/AI 에이전트가 UI 코드를 작성할 때 빠르게 참조할 수 있는 요약. 위 섹션을 다 읽지 않고도 "흔한 케이스"를 바로 처리할 수 있게 한다.

### Quick Color Reference

- Page background: `<token>` (`<#hex>` / `<#hex 다크>`)
- Text: `<token>` (`<#hex>` / `<#hex 다크>`)
- Card: `<token>` (`<#hex>` / `<#hex 다크>`)
- Border: `<token>` (`<#hex>` / `<#hex 다크>`)
- Primary: `<token>` (`<#hex>` / `<#hex 다크>`)

### Example Component Prompts

- "<예시 프롬프트 1 — 카드 만들기>"
- "<예시 프롬프트 2 — KPI 카드>"
- "<예시 프롬프트 3 — 테이블>"

### Iteration Guide

1. 색상은 항상 CSS 변수
2. 카드 = `<라운딩>` + `<보더>` — 기본 단위
3. 버튼은 반드시 `<Button>` 컴포넌트 사용
4. 아이콘은 `<라이브러리>`에서 import — 크기 `<px>` 중 선택
5. 그림자는 호버/플로팅에서만
6. 다크 모드 항상 고려 — 하드코딩 색상은 `.dark` 셀렉터로 오버라이드

---

## 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| v0.1 | YYYY-MM-DD | <이름> | 초안 작성 |
