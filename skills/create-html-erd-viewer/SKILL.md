---
name: create-html-erd-viewer
description: Use when the user provides any kind of database schema info (DB MCP query results, DDL/CREATE TABLE statements, plain-text schema notes, Mermaid erDiagram .mmd, schema 명세서, table lists) and wants it visualized as a single self-contained interactive ERD HTML viewer (no external JSON, one file). 트리거 - "ERD HTML 만들어줘", "DB 시각화 HTML", "인터랙티브 ERD", "테이블 관계도 단일 HTML", "mmd to HTML", "DDL to ERD viewer", "DB 스키마 인터랙티브 뷰".
---

# Create ERD Viewer (Single HTML)

## Overview

DB 정보를 한 가지 포맷(`schema.tables[]` JS 객체)으로 정규화한 뒤, **`template.html`의 schema 영역만 교체**해 단일 HTML 파일로 출력한다.

핵심 제약:
- **단일 HTML 한 파일**. 외부 JSON·CSS·JS 분리 절대 금지.
- 라이브러리(Cytoscape, dagre, html2canvas)는 CDN 참조 그대로. inline 시도 금지.
- 카드 디자인·인터랙션·레이아웃 등 **schema 영역 외 코드는 손대지 않음**.

`template.html`은 이 스킬 디렉토리에 함께 있는 자체 ERD 뷰어. 카드 드래그앤드롭, FK/PK 컬러 배지, 사이드바 검색, Focus mode, 텍스트 선택·복사, Copy 버튼, PNG export, URL 해시 공유 등 모든 기능을 포함한다.

## Schema 데이터 모델 (LLM이 만드는 유일한 산출물)

```js
{
  name: "USERS",                                    // 노드 ID
  comment: "사용자",                                 // 한글 설명 (선택)
  columns: [
    { name: "id",      type: "BIGINT",       pk: true, comment: "사용자 ID" },
    { name: "email",   type: "VARCHAR(255)",           comment: "이메일" },
    { name: "team_id", type: "BIGINT", fk: "TEAMS.id", comment: "팀 ID" },
  ]
}
```

| 필드 | 필수 | 비고 |
|---|---|---|
| `name` (table/column) | ✓ | `name`은 cytoscape 노드 id로 사용. 영문/숫자/언더스코어 권장 |
| `comment` | – | 한글 OK. 입력에 한글 코멘트 있으면 반드시 살릴 것 |
| `columns[].type` | ✓ | DB가 알려주는 타입을 그대로 (`VARCHAR(20)`, `BIGINT`, `DATETIME` 등) |
| `columns[].pk` | – | PK면 `true` |
| `columns[].fk` | – | `"TABLE.column"` 점 구분 문자열. 다른 형식 금지 |

**`schema.relations`는 손대지 말 것.** 템플릿이 `fk` 필드를 스캔해 자동 생성.

## Workflow

1. **입력 형식 판별** — DB MCP / DDL / 평문 / `.mmd` 중 무엇인가
2. **schema.tables[] 추출** (아래 매핑 참조)
3. **`template.html` 을 사용자가 지정한 출력 경로로 복사** (기본: `./erd.html`)
4. **마커 영역만 교체**:
   ```js
   // === SCHEMA TABLES START ===
   tables: [
     /* TABLES_PLACEHOLDER */     ← 이 한 줄을 변환된 tables 배열로 대체
   ],
   // === SCHEMA TABLES END ===
   ```
5. 사용자에게 `open <output>.html` 안내. 끝.

## Input → Schema 매핑

### Case A: DB MCP (Supabase, Postgres, MySQL MCP 등)

- `list_tables` / 컬럼 / FK 도구를 호출해 메타데이터 수집
- 응답 JSON을 schema 모델에 매핑:
  - 테이블 → `tables[].name` + `comment` (DB의 description/comment 컬럼)
  - 컬럼 → `columns[].name` + `type` + `comment`
  - PK 제약 → `pk: true`
  - FK 제약 → `fk: "참조테이블.참조컬럼"`

### Case B: DDL (`CREATE TABLE …`)

- `CREATE TABLE` 블록별로 분리
- 컬럼 라인 파싱: 이름, 타입, NOT NULL, COMMENT
- `PRIMARY KEY (col)` 또는 인라인 `col … PRIMARY KEY` → `pk: true`
- `FOREIGN KEY (col) REFERENCES T(c)` 또는 인라인 `REFERENCES T(c)` → `fk: "T.c"`
- `COMMENT ON COLUMN …` 또는 컬럼 라인 끝 `COMMENT '...'` → `comment`

### Case C: 평문 명세서 / 일반 텍스트 / Excel 표 텍스트

LLM이 자연어로 직접 schema 객체 작성. 정보가 모호하면:
- **타입 누락**: 컬럼명에서 추정 (`*_id` → `BIGINT` 또는 `VARCHAR(20)`, `*_at` → `DATETIME`, 그 외 → `VARCHAR(255)`)
- **FK 대상 모호**: 컬럼명 규칙(`team_id` → `TEAMS.id`)으로 매칭. 그래도 모호하면 사용자에게 한 번 물음
- **PK 미표기**: 보통 `id` 컬럼을 PK로 추정
- **한글 코멘트는 항상 살릴 것**

### Case D: Mermaid erDiagram (`.mmd`)

```
erDiagram
  USERS {
    bigint id PK
    string email
    bigint team_id FK
  }
  USERS }o--|| TEAMS : "belongs to"
```

- `TABLE { ... }` 블록 → tables[]
- 컬럼 라인 파싱 패턴: `<type> <name> [PK|FK]`
- relation 라인 (`A }o--|| B`)에서 카디널리티는 무시하고, FK 컬럼이 명시 안 되어 있으면 컬럼명 규칙으로 매칭 (`A.b_id` → `B.id`)

## Common Mistakes

| 실수 | 결과 |
|---|---|
| 데이터를 외부 JSON으로 분리 | 사용자 요구 위반. 무조건 단일 HTML 한 파일 |
| `relations` 배열을 손으로 채움 | 템플릿 자동생성과 충돌. `fk` 필드만 채울 것 |
| FK 형식 다르게 (`"users#id"`, `"USERS->id"` 등) | 정확히 `"TABLE.column"` 점 구분만 허용 |
| 한글 컬럼/테이블 코멘트 누락 | `comment` 필드로 항상 보존 |
| CDN script 태그를 라이브러리 inline으로 변환 | 파일만 수MB로 부풀림. CDN 그대로 둘 것 |
| 카드 CSS·JS·HTML 구조 변경 | 템플릿은 schema 영역 **외부 절대 손대지 않음** |
| 마커(`// === SCHEMA TABLES START/END ===`) 제거 | 다음 갱신 작업이 깨짐. 마커 보존 |

## Quick Reference

```
입력 (MCP/DDL/평문/.mmd)
  → schema.tables[] 객체로 정규화
  → template.html 복사
  → /* TABLES_PLACEHOLDER */ 영역만 교체
  → 단일 HTML 파일 저장
```

## Verification

생성한 HTML이 정상인지 확인:
1. `open <output>.html` 으로 브라우저에서 열기
2. 헤더에 `Tables N · Relations M` 카운트가 입력 정보와 일치
3. 좌측 사이드바에 모든 테이블이 표시되고 한글 코멘트가 보임
4. 카드 클릭 → Focus mode가 이웃 테이블만 강조
5. 카드 헤더를 잡고 드래그하면 이동
6. 검색창에 컬럼명 일부 입력 → 그 컬럼을 가진 테이블만 필터됨
7. `Export PNG` 버튼이 전체 ERD를 캡처
