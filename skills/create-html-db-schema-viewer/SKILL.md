---
name: create-html-db-schema-viewer
description: Use when the user provides DB schema information in any form (DB MCP results, DDL/CREATE TABLE, plain-text spec, Mermaid erDiagram .mmd, or DBML) and wants a multi-page static HTML DB viewer with ERD relationship diagram, per-table detail pages, table listing, and DBML source viewer. Output is a directory of HTML/CSS/JS files driven by a single DBML source of truth, optionally built deterministically by build.py + pydbml. 트리거 — "ERD 사이트 만들어줘", "DB 뷰어 정적 사이트", "테이블별 상세 페이지 포함 ERD", "DBML 기반 ERD", "멀티페이지 DB 문서", "schema.dbml viewer", "DDL to multi-page HTML", "DB 스키마 확장형 뷰어", "/create-html-db-schema-viewer".
---

# Create HTML DB Schema Viewer (Multi-page, DBML-driven)

## Overview

기존 v1(single HTML)의 후속. **여러 HTML/CSS/JS 파일로 구성된 정적 사이트**를 출력한다. 진실의 원천은 `schema.dbml`이며, `build.py`가 그것을 파싱해 `assets/schema.js`와 테이블별 상세 페이지를 자동 생성한다.

핵심 원칙:
- **DBML이 단일 IR(intermediate representation)**. 입력 형태(MCP/DDL/평문/.mmd/.dbml)와 무관하게 LLM이 먼저 `schema.dbml`로 정규화한다.
- **CSR 골격**. 모든 페이지는 빈 HTML 골격을 가지고, `window.SCHEMA`를 읽는 페이지별 JS가 동적으로 렌더한다. LLM이 페이지 HTML을 매번 짤 필요가 없다.
- **DB-agnostic**. 특정 DB(Postgres/MySQL/Oracle) 기능에 의존하지 않는 공통 요소만 다룬다.
- **build.py 우선, LLM 직접 작성은 fallback**. `pydbml`이 설치된 환경이면 빌드 스크립트가 결정론적으로 정적 사이트를 생성한다. 안 되면 LLM이 같은 결과물을 만든다.
- **레이아웃 persist는 localStorage만**. 별도 파일을 만들지 않아 파일 깨질 위험 0.

## 출력 디렉토리 구조

```
<out>/
├── schema.dbml                    # 진실의 원천 (사람이 편집)
├── build.py                       # pydbml 기반 빌더 (스킬에서 복사)
├── requirements.txt               # pydbml 한 줄
├── index.html                     # 대시보드 — 요약 + 빠른 진입
├── erd.html                       # 전체 ERD 관계도 (Cytoscape, 카드 드래그, Focus, PNG export)
├── schema.html                    # schema.dbml 원본 view + Copy + dbdiagram.io 열기
├── tables/
│   ├── index.html                 # 테이블 일람 (검색/정렬)
│   └── <name>.html                # 테이블 상세 — 모두 동일 골격, data-table 속성만 다름
└── assets/
    ├── style.css                  # 공유 다크 테마
    ├── nav.js                     # 공통 상단 nav (모든 페이지가 inject)
    ├── schema.js                  # window.SCHEMA = { tables, refs, enums, indexes }
    ├── dashboard.js               # index.html 전용
    ├── erd.js                     # erd.html 전용
    ├── tables.js                  # tables/index.html 전용
    ├── detail.js                  # tables/<name>.html 전용
    └── schema-view.js             # schema.html 전용
```

## DB-agnostic 데이터 모델

`assets/schema.js`가 export하는 `window.SCHEMA` 객체 형태:

```js
window.SCHEMA = {
  source_dbml: "Table users { ... }",       // schema.dbml 원본 (schema.html에서 사용)
  tables: [
    {
      name: "users",
      comment: "사용자 계정",
      columns: [
        {
          name: "id",
          type: "BIGINT",                    // 원본 문자열 그대로 보존
          pk: true,
          uk: false,
          nullable: false,
          default: null,
          comment: "사용자 ID"
        },
        {
          name: "team_id",
          type: "BIGINT",
          pk: false,
          uk: false,
          nullable: true,
          default: null,
          comment: "팀 ID",
          fk: { table: "teams", column: "id" }
        }
      ],
      indexes: [
        { name: "idx_users_email", columns: ["email"], unique: true }
      ]
    }
  ],
  relations: [
    // FK 기반 자동 도출. build.py가 생성. LLM 작성 시에도 채울 것.
    { from: "users", from_col: "team_id", to: "teams", to_col: "id" }
  ],
  enums: [
    { name: "user_role", values: ["admin", "member", "guest"] }
  ]
};
```

| 영역 | 포함 | 명시적 제외 (DB 종속) |
|---|---|---|
| Table | name, comment | tablespace, storage option |
| Column | name, type(원본), pk, uk, nullable, default, comment, fk | CHARSET/COLLATION, generated expression, identity 세부 |
| Index | name, columns[], unique | type(BTREE/HASH), partial where, include 컬럼 |
| Relation | FK 기반 outgoing/incoming | ON DELETE/UPDATE 절, deferrable |
| Enum | name, values[] (DBML 지원분) | DB-네이티브 enum 세부 (label/i18n 등) |

**컬럼 타입은 원본 문자열 그대로 보존한다** (`VARCHAR(255)`, `JSONB`, `BIGINT` 등). DB-agnostic이라 함은 특정 DB 기능(시퀀스, 트리거, partial index 등)에 의존하지 않는다는 의미이지 타입 문자열을 추상화한다는 의미가 아니다.

## 빌드 파이프라인

```
┌──────────────────────────────┐
│ 입력                          │
│  MCP / DDL / 평문 / .mmd /    │
│  .dbml 중 하나                │
└──────────────┬───────────────┘
               ↓ (LLM이 한 번만)
┌──────────────────────────────┐
│ schema.dbml (single source)  │
└──────────────┬───────────────┘
               ↓ (build.py 또는 LLM)
┌──────────────────────────────┐
│ assets/schema.js +           │
│ tables/<name>.html stubs     │
└──────────────┬───────────────┘
               ↓ (브라우저)
┌──────────────────────────────┐
│ index/erd/tables/schema 페이지│
│ 모두 동적 렌더               │
└──────────────────────────────┘
```

### 권장 경로: `build.py`

1. LLM은 `schema.dbml`만 만들면 끝.
2. 스킬 디렉토리의 `build.py`, `requirements.txt`, `templates/` 전체를 출력 디렉토리로 복사.
3. `pip install -r requirements.txt && python build.py` 실행.
4. `build.py`가 `schema.dbml` 파싱 → `assets/schema.js` + `tables/<name>.html` 자동 생성.

사용자가 schema를 수정한 뒤 다시 빌드하려면:
```bash
$ vim <out>/schema.dbml
$ cd <out> && python build.py
```

### Fallback: LLM 직접 작성

`pydbml` 설치 불가/python 없는 환경이면 LLM이 직접:
1. `schema.dbml` 작성
2. `assets/schema.js`를 `window.SCHEMA = {...}` 형태로 작성 (위 데이터 모델 그대로)
3. `tables/<name>.html`을 테이블 수만큼 복제 — `_table.html` 골격을 그대로 두고 `data-table` 속성만 교체
4. 페이지/CSS/공통 JS는 `templates/`에서 그대로 복사

두 경로의 출력물은 **완전히 동일한 형태**여야 한다.

## 입력 → schema.dbml 매핑

### Case A: DB MCP (Supabase/Postgres/MySQL MCP)

- `list_tables`/컬럼/FK 도구 호출 → DBML로 변환
- 테이블 `comment`, 컬럼 `comment`/`note` 보존
- FK는 `[ref: > other_table.col]` 인라인 또는 `Ref:` 블록으로 표현

### Case B: DDL (`CREATE TABLE …`)

- 각 CREATE TABLE → `Table` 블록
- `PRIMARY KEY` → `[pk]`
- `FOREIGN KEY ... REFERENCES T(c)` → `[ref: > T.c]`
- `NOT NULL` → `[not null]`
- `DEFAULT x` → `[default: x]`
- `COMMENT ON COLUMN` 또는 인라인 COMMENT → `[note: '...']`
- `CREATE INDEX` → `indexes { ... }` 블록
- DB 특화 절(`USING gin`, `INCLUDE (...)`, `WHERE ...`)은 무시

### Case C: 평문 명세서 / Excel 표 / 메모

LLM이 자연어로 직접 DBML 작성. 모호한 경우:
- **타입 누락**: `*_id`→`bigint`, `*_at`→`timestamp`, 그 외 `varchar(255)`
- **FK 추정**: `team_id` → `teams.id` 규칙으로 매칭. 그래도 모호하면 사용자에게 한 번 물음
- **PK 누락**: 보통 `id` 컬럼을 PK로 추정
- **한글 comment는 항상 보존**

### Case D: Mermaid erDiagram (`.mmd`)

- `TABLE { ... }` 블록 → `Table`
- `<type> <name> PK` → `[pk]`
- `<type> <name> FK` → 관계 라인(`A }o--|| B`)에서 매칭. FK 컬럼이 명시 안 되어 있으면 `*_id` 규칙
- 카디널리티 라벨(`}o--||`)은 DBML 관계로 변환 (`<`, `>`, `-`, `<>`)

### Case E: DBML(.dbml)

이미 IR. 정규화 거의 불필요. 단, 다음만 확인:
- 모든 FK가 정확히 존재하는 테이블/컬럼을 가리키는지
- `enum` 정의가 사용된 컬럼 타입과 일치하는지

## 페이지 추가 패턴 (확장성)

새 페이지 추가 시 3단계:
1. `templates/<page>.html` 골격 작성 (HTML body에 빈 컨테이너 + `data-page` 속성)
2. `templates/assets/<page>.js` 작성 (`window.SCHEMA` 읽어서 렌더)
3. `templates/assets/nav.js`의 `NAV_LINKS` 배열에 한 줄 추가

확장 후보 (v2에서는 미구현, 패턴만 제공):
- `relations.html` — FK 매트릭스 일람
- `indexes.html` — 인덱스 일람
- `enums.html` — DBML enum 일람
- `compare.html` — 두 schema.dbml 버전 diff
- `diagrams/<area>.html` — 도메인별 sub-ERD

## 레이아웃 persist (위험 0 단순화)

- `erd.html`에서 카드를 드래그하면 위치가 **localStorage에 자동 저장**.
- 새로고침해도 같은 브라우저에선 유지.
- "Reset Layout" 버튼 → localStorage 클리어 → dagre auto-layout 복귀.
- **별도 layout.json 파일은 만들지 않는다** (파일 깨질 위험 0).
- 브라우저/사용자 간 위치 공유는 **URL 해시**로만 (focus된 테이블 이름 정도, 기존 동작 유지).

## Verification

빌드 후 `index.html`을 브라우저에서 열어 확인:

1. **대시보드** — Tables/Relations/Indexes 카운트가 입력 정보와 일치
2. **erd.html** — 모든 테이블 카드가 렌더되고, FK 화살표가 보임. 카드 헤더 드래그로 이동 가능. 새로고침해도 위치 유지.
3. **tables/index.html** — 모든 테이블이 표로 나오고 검색/정렬 동작
4. **tables/<name>.html** — Columns / Indexes / Relations 세 섹션이 모두 보임. "Back to ERD" / 관련 테이블 링크 동작.
5. **schema.html** — schema.dbml 원본이 표시되고, "Copy" 버튼이 클립보드에 복사. "Open in dbdiagram.io" 링크 동작.
6. file:// 더블클릭으로 열어도 모든 페이지가 정상 동작 (fetch 미사용, `window.SCHEMA` 전역).

## Common Mistakes

| 실수 | 결과 |
|---|---|
| `schema.dbml`을 안 만들고 바로 `schema.js` 작성 | 진실의 원천 부재. 재빌드/공유 불가. **항상 .dbml부터** |
| 페이지 HTML에 데이터를 inline (CSR 골격 위반) | 페이지 추가 비용 폭발. `window.SCHEMA` 한 군데만 |
| DB-특화 요소를 DBML에 우겨넣음 (`USING gin`, partial where) | DB-agnostic 위반. 표준 DBML 문법만 |
| `tables/<name>.html`을 매 테이블마다 손으로 작성 | `_table.html` 골격 + `data-table` 속성만. 본문은 `detail.js`가 채움 |
| `layout.json` 등 별도 레이아웃 파일 만들기 | 파일 깨질 위험. localStorage만 사용 |
| 컬럼 타입을 추상화 (`bigint`→`int`) | 정보 손실. 원본 문자열 그대로 보존 |
| FK 형식 다르게 (`"users#id"`) | DBML 표준 `users.id` 점 구분만 |

## Quick Reference

```
입력 (MCP/DDL/평문/.mmd/.dbml)
  → schema.dbml 작성
  → 스킬의 templates/ + build.py + requirements.txt 를 출력 디렉토리로 복사
  → python build.py  (또는 fallback: LLM이 schema.js + tables/<name>.html 직접 작성)
  → open <out>/index.html
```
