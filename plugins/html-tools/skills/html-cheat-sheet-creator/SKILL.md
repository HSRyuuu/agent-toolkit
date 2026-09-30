---
name: html-cheat-sheet-creator
description: >
  Use when creating a single self-contained HTML cheat sheet, study card set, or
  reference sheet from learning material, commands, API notes, interview prep,
  or concept summaries. Triggers: "cheat sheet 만들어줘", "치트시트 HTML",
  "학습 카드 HTML", "단일 html 레퍼런스 시트", "스터디 시트",
  "/html-cheat-sheet-creator". Do NOT use for reports/plans, ERDs, PDF, or DOCX.
---

# html-cheat-sheet-creator — 모바일 우선 단일 HTML 치트 시트 생성기

## 이 스킬이 하는 일

어떤 주제(언어 문법, API 요약, 명령어 모음, 면접 질문, 챕터별 핵심 개념 등)든 받아서 **하나의 `.html` 파일**로 출력한다. 그 파일은:

- **외부 의존 0** — CDN, 폰트 링크, JS 라이브러리 모두 없음. 더블클릭만 하면 모바일 사파리·크롬·데스크톱 어디서나 열린다.
- **라이트 테마(흰색 배경)** + **6종 강조 컬러**(tech=sky-blue / soft=orange / mint=green / lilac=purple / pink=magenta / sky=indigo). 탭마다 다른 톤을 줄 수 있고, 모두 CSS 변수(`--theme-color`, `--theme-rgb`)로 cascade 처리됨.
- **상단 고정 2~6 탭** + **좌측 슬라이드 사이드바** + **스크롤 스파이**(현재 보이는 카드를 사이드바에서 자동 하이라이트) + **`<details>` 펼치기** 기본 내장.
- 모바일 1차 타깃이지만 **`min-width: 1080px`에서 사이드바가 자동으로 영구 표시**되어 PC에서도 자연스럽게 동작.

---

## 콘텐츠 모델 (3-레벨)

```
HTML 파일
├── Tab 1 (data-theme="tech")
│   ├── Category 1A (cat-head 카드)
│   │   ├── Item 1A-1 (article.q)
│   │   └── …
│   └── Category 1B
├── Tab 2 (data-theme="soft")
│   └── …
├── Tab 3 (data-theme="mint")          ← 선택
├── Tab 4 (data-theme="lilac")         ← 선택
├── Tab 5 (data-theme="pink")          ← 선택
└── Tab 6 (data-theme="sky")           ← 선택
```

- **Tab** : 2 ~ 6 개. 상단 탭과 1:1 매칭. 큰 분류로 콘텐츠를 나눈다.
- **Category** : 한 탭 내부 그룹. 사이드바에서도 그룹 헤더로 보임.
- **Item (카드)** : 실제 단위 콘텐츠. 제목 + 본문 + 선택적 보조 메모 + 선택적 펼치기.

탭이 1개라면 `html-docs-creator`를 쓴다. 7개 이상이라면 콘텐츠를 더 큰 단위로 묶어 6 이하로 줄인다.

---

## 탭 개수 / 레이아웃

`<div class="tabs" data-cols="N">`의 N 값으로 결정된다. CSS Grid가 알아서 다음 레이아웃을 만든다.

| N | 시각 | 비고 |
|---|---|---|
| 2 | 가로 2 | 1줄 |
| 3 | 가로 3 | 1줄 |
| 4 | 2 × 2 | 2줄 |
| 5 | 3 + 2 | 2줄 (위 3, 아래 2). 아래 2개는 1.5배 넓이로 균형 |
| 6 | 3 × 2 | 2줄 |

탭이 2줄이 되면 topbar가 자동으로 두 배 높이가 되고, `scroll-margin-top: 110px`로 섹션이 가리지 않도록 보정되어 있다.

---

## 테마 (6종)

`data-theme="<테마명>"`로 지정. 섹션·탭버튼·사이드바 part 세 곳에 각각 같은 값으로 달아주면 톤이 cascade로 자동 적용된다.

| 테마 | 색 | 용도 예시 |
|---|---|---|
| `tech` | sky-blue `#0284c7` | 기본 / 기술 / 시스템 |
| `soft` | orange `#c2410c` | 응용 / 비기술 |
| `mint` | green `#15803d` | 데이터 / 통계 / 환경 |
| `lilac` | purple `#7c3aed` | 디자인 / UX / 추상 개념 |
| `pink` | magenta `#be185d` | 마케팅 / 사용자 / 캠페인 |
| `sky` | indigo `#1d4ed8` | 인프라 / 네트워크 / 설계 |

순서·조합은 자유. 굳이 `tech → soft → mint` 순일 필요는 없다.

---

## 워크플로우 (4단계)

### Step 1 — 입력 분류 & 탭 분할 결정

먼저 사용자가 준 콘텐츠를 **몇 개로 나눌지** 정한다 (2~6). 좋은 분할이 없으면 사용자에게 확인한다.

| 입력 형태 | 분할 예시 |
|---|---|
| 언어 문법 모음 | 기본 / 고급 (2) 또는 변수·연산자 / 제어문 / 함수 / 객체 (4) |
| 명령어 / CLI | 자주 / 가끔 (2) 또는 파일 / 프로세스 / 네트워크 (3) |
| 면접 질문 | 기술 / 비기술 (2) |
| 알고리즘 | 데이터 구조 / 알고리즘 기법 (2) 또는 정렬 / 탐색 / 그래프 / DP (4) |
| 디자인 패턴 | 생성 / 구조 / 행동 (3) |
| Cloud 서비스 | 컴퓨트 / 스토리지 / 네트워크 / DB / 관측 (5) |
| 한 학기 강의 노트 | 1~3주 / 4~6주 / 7~9주 / 10~12주 / 13~15주 / 시험 (6) |

### Step 2 — 트리 설계 (= 사이드바 목차)

각 탭 아래 카테고리·항목 트리를 종이/메모에 먼저 적는다.

- 카테고리: 탭당 3 ~ 10 개가 보기 좋음.
- 항목: 카테고리당 2 ~ 10 개. 너무 많으면 사이드바가 길어진다.
- 항목별로 결정할 것:
  - 제목 (한 줄)
  - 본문 (질문/요약/시그니처)
  - 보조 메모(followup) 필요?
  - 펼치기(details) 필요? — 답·예시·자세한 설명
  - 중요도(stars ★) 표시할지 (선택)
- 각 탭의 테마(`data-theme` 값)도 이 단계에서 정한다.

### Step 3 — ID 규칙 적용

사이드바 링크와 article id가 1:1로 매칭되어야 스크롤 스파이가 동작한다.

| 요소 | 규칙 | 예 |
|---|---|---|
| Section id | `tab-1` ~ `tab-6` | `<section id="tab-1">` |
| Tab button | `data-target="tab-N"` (위 id와 매칭) | `<button data-target="tab-1">` |
| 테마 | `data-theme="tech\|soft\|mint\|lilac\|pink\|sky"` — 같은 탭의 button + section + side-part 모두 동일 값 | |
| Category id | `cat-a` ~ `cat-p` (전역) | `<div id="cat-a">` |
| Item id | `q-<카테고리키><번호>` | `q-a1`, `q-a2`, `q-b3` |
| 사이드바 링크 | `<a href="#q-a1">` 와 정확 일치 | — |

### Step 4 — base.html 채우기 + 출력

1. [templates/base.html](templates/base.html)을 그대로 복사한다.
2. `{{...}}` placeholder를 콘텐츠로 치환한다 (37개).
3. 탭이 2개보다 많으면:
   - `.tabs[data-cols="2"]` → `data-cols="N"`으로 바꾼다.
   - `<div class="tabs">` 안에 `<button class="tab-btn">…</button>` 을 N개까지 늘린다.
   - `<div class="sidebar-body">` 안에 `<div class="side-part" data-theme="…">…</div>` 블록을 N개로 늘린다.
   - 본문에 `<section id="tab-N" data-theme="…">…</section>` 블록을 N개로 늘린다.
4. 카테고리·카드를 카테고리당 / 탭당 필요한 수만큼 복제한다. 템플릿에 완전형 카드(A1) + 간단형 카드(B1) 두 가지 예시가 있다.
5. **CSS와 `<script>` 블록은 절대 건드리지 않는다.** 사이드바·탭·스크롤 스파이 동작이 깨진다.
6. 결과 파일명: `<주제>_cheat_sheet.html` 권장. 사용자가 다른 규칙을 주면 따른다.

---

## 카드 변형

[references/components.md](references/components.md)에 카드 6종 변형(중요도 유/무 × 본문만 / 본문+메모 / 본문+메모+펼치기)을 정리해 두었다. 그대로 복사해서 쓴다.

전형 패턴:

| 콘텐츠 유형 | 추천 카드 형태 |
|---|---|
| 명령어 / 단축키 | 제목 + 짧은 본문, details 없음 |
| API 한 줄 요약 | 제목 + 본문(시그니처) + details(예시 코드) |
| 면접 질문·암기 항목 | 제목 + 질문(qbody) + followup + details(답변) |
| 개념 / 정의 | 제목 + 본문 + details(예시·반례) |

---

## 검증 (필수)

작성 후 ID 매칭과 태그 균형을 한 번에 검사:

```bash
python3 -c "
import re
h=open('OUT.html').read()
a=set(re.findall(r'<article id=\"(q-[a-z0-9]+)\"',h))
s=set(re.findall(r'<a class=\"side-link[^\"]*\" href=\"#(q-[a-z0-9]+)\"',h))
print('only in article:', a-s)
print('only in sidebar:', s-a)
# 탭 ↔ 섹션 매칭
tt=set(re.findall(r'data-target=\"(tab-\d+)\"',h))
ts=set(re.findall(r'<section id=\"(tab-\d+)\"',h))
print('only in tab buttons:', tt-ts)
print('only in sections:', ts-tt)
# data-cols 일치 확인
m=re.search(r'<div class=\"tabs\" data-cols=\"(\d+)\"', h)
print('data-cols:', m.group(1) if m else 'NONE', 'vs tab count:', len(tt))
# 태그 균형
print('details:',  h.count('<details'), '/', h.count('</details>'))
print('article:',  h.count('<article'), '/', h.count('</article>'))
print('section:',  h.count('<section'), '/', h.count('</section>'))
"
```

모든 `only in *`이 `set()` + `data-cols == tab count` + 각 태그 open/close 균형이면 통과.

---

## 자주 하는 실수

| 실수 | 결과 | 고침 |
|---|---|---|
| article id와 사이드바 href 불일치 | 스크롤 스파이/이동 깨짐 | 검증 스크립트로 확인 |
| `<details>` 안에 `<summary>` 빠뜨림 | 펼치기 미동작 | summary는 details 첫 자식 필수 |
| `data-cols` 값과 실제 탭 수 불일치 | 탭 그리드 깨짐 (빈 칸 / 줄바꿈 이상) | 둘이 일치해야 함 (예: 4 탭이면 `data-cols="4"`) |
| Tab의 `data-target`과 Section `id` 불일치 | 탭 클릭 시 스크롤 안됨, 활성화 깨짐 | `tab-1`~`tab-6` 일관 |
| 같은 탭의 button·section·side-part가 서로 다른 `data-theme` 값 | 톤이 따로 놂 | 세 곳에 같은 값 적용 |
| `<section id="tech">`를 그대로 두고 `<section id="tab-1">`만 추가 | id 중복으로 JS 오동작 | section id는 `tab-N`만 사용. 기존 `tech`/`soft` id 호환은 없음 |
| 카드를 너무 길게 작성 | 스크롤 스파이 점프 거리 큼 | 카드는 짧게, 자세한 건 `<details>`로 |

---

## 영감 (Real-world)

이 스킬의 베이스가 된 첫 사례: 64-카드 학습 시트 (2 탭, tech + soft). 사이드바 74개 링크와 article 74개가 1:1로 매칭, 데스크톱·모바일 양쪽에서 검증됨. 이후 N=2~6 탭 모두 지원하도록 확장. 같은 골격으로 명령어 모음, API 레퍼런스, 문법 노트, 한 학기 수업 정리 등 어떤 주제든 빠르게 만들 수 있다.
