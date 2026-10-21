# tabs — 여러 문서를 상단 고정 탭 하나로 묶기

`architecture`, `data-model` 로 만든 문서 여러 개를 **하나의 HTML** 로 묶는다. 맨 위에 탭 막대가 고정되고(스크롤해도 유지), 탭을 누르면 해당 문서가 보인다. 공통 규칙은 `../SKILL.md` 를 따른다.

- 템플릿: `templates/tabs.html`
- 예제: `examples/tabs-example.json` (기존 예제 두 개를 묶는다)
- `kind` 는 `"tabs"` 로 쓴다.
- 이 종류는 새 내용을 만들지 않는다. 탭마다 들어갈 문서의 데이터를 **먼저** 만들고, 그 데이터를 가리키는 묶음 데이터를 쓴다.

## 언제 쓰나

- 같은 주제를 서로 다른 관점으로 만든 문서를 한 페이지에서 오가며 봐야 할 때(예: 호출 흐름 지도 + 데이터 모델 문서).
- 하나의 문서로 합치면 너무 길어지거나, 종류가 달라 한 템플릿에 담을 수 없을 때.
- 탭이 하나뿐이면 묶을 이유가 없다. `render.py` 가 `WARN:` 으로 알려 준다.

## 데이터 스키마

```jsonc
{
  "kind": "tabs",
  "meta": { "title": "탭 제목(브라우저 탭 이름)", "ver": "2026-10-21" },   // 전부 선택
  "tabs": [
    { "id": "flow",  "label": "주문 흐름 지도",    "file": "order-flow.json" },        // file: 이 JSON 이 있는 폴더 기준 상대 경로
    { "id": "model", "label": "리워드 데이터 모델", "data": { "kind": "data-model", "...": "..." } }   // 또는 data: 데이터를 직접 넣는다
  ]
}
```

- `label` 은 필수이다. 탭 막대에 보이는 이름이다.
- `file` 과 `data` 중 **하나만** 쓴다. 문서가 길면 `file` 로 분리하는 편이 낫다.
- `id` 는 선택이다. 생략하면 `tab1`, `tab2` … 이다. 영문으로 시작하는 영문·숫자·`-`·`_` 만 쓴다. 주소의 `#<id>` 로 그 탭을 바로 연다.
- 탭 안의 문서는 `architecture` 또는 `data-model` 이다. `tabs` 안에 `tabs` 를 넣을 수 없다.
- 탭 문서의 `meta.ver` 를 따로 주지 않으면 묶음의 `meta.ver`(또는 오늘 날짜)를 쓴다.

## 동작

- 탭 막대는 맨 위에 `position: sticky` 로 고정된다. 안전 영역(휴대폰 노치) 위쪽 띠는 탭 막대와 같은 색으로 칠한다.
- 탭 전환은 클릭과 좌우 방향키(`←` `→`)로 한다. 탭을 바꾸면 스크롤이 맨 위로 돌아간다.
- 첫 화면은 `#<id>` 가 있으면 그 탭, 없으면 첫 번째 탭이다.
- 뷰어의 라이트·다크 선택(`data-theme`)과 시스템 설정을 탭 안 문서에 그대로 전달한다.

## 문서가 격리되는 방식

- 탭마다 문서의 CSS 와 본문을 `<template>` 에 그대로 담고, 실행할 때 **Shadow DOM** 패널에 복제해 넣는다. 그래서 문서끼리 CSS, id, 전역 이름이 충돌하지 않는다.
- 문서의 `<style>` 은 패널용으로 바뀐다: `:root` 규칙은 `:host` 로, `body` 규칙은 패널 래퍼(`.pg`)로 옮긴다(`render.py` 의 `to_shadow_css`).
- 문서의 스크립트는 그대로 실행하되 `document` 만 해당 패널로 한정한 프록시로 바꾼다. `getElementById`, `querySelector(All)` 는 그 패널 안에서만 찾고, `document.title` 대입은 무시한다.
- 패널은 모든 문서 스크립트가 끝난 뒤에 숨긴다. 숨겨진 상태에서는 SVG 레이아웃 계산이 어긋날 수 있어서다.
- 템플릿이 `<template>` 이므로 JS 없이 파일을 읽는 에이전트도 각 탭의 `<pre id="agenttext">` 를 소스에서 읽을 수 있다. 탭마다 자기 에이전트용 텍스트가 있다. 묶음 전체를 합친 평문은 `render.agent_text(data, base_dir)` 가 돌려주지만 페이지에는 넣지 않는다.

## 문서 쪽 제약

탭에 넣을 문서의 템플릿(스크립트·CSS)은 다음을 지켜야 한다. 새 템플릿을 추가할 때도 같다.

- `<style>` 하나, 본문 뒤 `<script>` 하나만 가진다.
- 문서 전체용 규칙은 `:root` 와 `body` 로만 쓴다(`html` 선택자를 쓰지 않는다).
- 스크립트는 `document.getElementById`, `querySelector`, `createElement(NS)`, `body.appendChild`, `addEventListener` 정도만 쓴다. 문서 전역의 다른 상태(`document.head`, `document.styleSheets` 등)에 기대지 않는다.
- 요소를 찾을 때 `id` 는 문서 안에서만 유일하면 된다. 패널끼리는 같은 `id` 를 써도 된다.

## 확인

- `python3 <skill>/scripts/render.py tabs.json out.html --shot check.png --size 1100,900` 는 첫 탭을, `--hash <탭id>` 를 더하면 그 탭을 찍는다. 탭마다 한 번씩 찍어 본다.
- `ERROR:` 에는 탭 이름이 붙는다(`[모델] flow 의 칸 수가 …`). 어느 탭의 문제인지 바로 알 수 있다.
- 탭을 바꿨을 때 지도의 줌 컨트롤, 흐름 탭, 화면 토글이 해당 패널 안에서 동작하는지 본다.
