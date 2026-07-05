---
name: create-mermaid-erd
description: >
  Use when the user wants an ERD or database relationship diagram from a PRD,
  domain description, table list, DDL, DB schema, or existing Mermaid ERD.
  Triggers: "ERD 만들어줘", "테이블 관계도", "DB 설계 시각화", "데이터 모델링",
  "개념 ERD", "논리 ERD", "물리 ERD", "mermaid ERD", "DB 스키마 그려줘",
  "ERD HTML 미리보기".
---

# ERD 생성 스킬

## 레퍼런스

`references/` 디렉토리에 HR 플랫폼 도메인의 완성 예제 3종이 있다. ERD 생성 시 해당 수준의 레퍼런스를 읽고 구조·문법·스타일링을 그대로 따른다.

| 수준 | 파일 | 설명 |
|------|------|------|
| Conceptual | `conceptual-erd-example.mmd` | 엔티티 + 관계만, 속성 없음 |
| Logical | `logical-erd-example.mmd` | 한글 속성명 + 추상 타입 + PK/FK |
| Physical | `physical-erd-example.mmd` | 영문 컬럼명 + DB 종속 타입 + 인덱스 |

---

## 1. ERD 수준 정의

| 수준 | 엔티티 | 속성명 | 타입 | PK/FK | 인덱스/DDL | 관계 라벨 |
|------|--------|--------|------|-------|-----------|----------|
| **Conceptual** | O | X | X | X | X | 한글 동사 |
| **Logical** | O | 한글 | 추상 (`Long`, `String`, `Enum` 등) | O | X | 한글 동사 |
| **Physical** | O | 영문 snake_case | DB 종속 (`BIGINT`, `VARCHAR(50)` 등) | O | O | 영문 동사 |

**추상 타입 목록** (논리 ERD 전용): `Long`, `String`, `Int`, `Float`, `Boolean`, `Date`, `DateTime`, `Text`, `Enum`

---

## 2. 입력 처리 절차

### 2-1. 입력 수용

사용자가 제공할 수 있는 입력 형태:
- 자연어 프롬프트 ("쇼핑몰 ERD 만들어줘")
- 파일 (`.md`, `.pdf`, `.txt` 등 — PRD, 요구사항 정의서, 테이블 목록)
- 기존 ERD 파일 (`.mmd` — 수정/확장 요청)

### 2-2. ERD 수준 확인

사용자가 수준을 명시하지 않으면 질문한다:
> "어떤 수준의 ERD를 원하시나요? 개념(엔티티+관계만), 논리(속성+타입 포함), 물리(DB 컬럼+인덱스 포함) 중 선택해주세요."

### 2-3. 데이터 모델 도출

1. **도메인 식별** — 주요 업무 영역을 먼저 식별한다 (예: 조직관리, 급여, 채용)
2. **엔티티 도출** — 각 도메인의 핵심 명사를 엔티티로 추출한다
3. **관계 정의** — 카디널리티(1:1, 1:N, N:M)와 관계 동사를 정의한다
4. **속성 정의** (논리/물리만) — 엔티티별 속성, 타입, 제약조건을 결정한다

---

## 3. Mermaid 출력 규칙

### 3-1. 파일 구조

```mermaid
---
config:
  theme: dark
  look: handDrawn
  layout: elk
---
erDiagram
	direction BT

	엔티티정의들...

	관계정의들...

	엔티티:::클래스 적용들...

	classDef 정의들...
```

순서가 중요하다: **엔티티 → 관계 → 클래스 적용 → classDef 정의** 순으로 작성해야 스타일이 제대로 적용된다.

### 3-2. 속성 문법 (논리/물리)

Mermaid ER 다이어그램의 속성 순서는 고정이다:

```
type name [PK|FK|UK] ["comment"]
```

- 첫 번째: 타입 (필수)
- 두 번째: 속성명 (필수)
- 세 번째: 키 표기 — `PK`, `FK`, `UK`, 복합은 `PK, FK` (선택)
- 네 번째: 코멘트 — 큰따옴표로 감싼다 (선택)

코멘트가 없더라도 빈 문자열 `""`을 넣어 형식을 통일한다.

**예시 (논리):**
```
Long 직원ID PK ""
String 이름 "NN"
Enum 재직상태 "NN"
```

**예시 (물리):**
```
BIGINT employee_id PK "AUTO_INCREMENT"
VARCHAR(50) name "NN"
TIMESTAMP created_at "NN, DEFAULT NOW()"
```

**개념 ERD**에서는 엔티티 블록을 비워둔다:
```
직원 :::blue {

}
```

### 3-3. 관계 문법

```
엔티티A||--o{엔티티B:"관계동사"
```

| 카디널리티 | Mermaid 표기 |
|-----------|-------------|
| 1:1 | `\|\|--\|\|` |
| 1:N | `\|\|--o{` |
| N:1 | `}o--\|\|` |
| N:M | `}o--o{` |
| 0..1 | `\|\|--o\|` |

### 3-4. 다크 테마 색상 팔레트

엔티티별로 고유 색상을 부여한다. 아래 15색 팔레트를 기본으로 사용하고, 엔티티가 더 많으면 색상을 추가한다.

```
classDef blue stroke-width:1px,stroke-dasharray:none,stroke:#5b6ef5,fill:#1a2040,color:#a4b0ff
classDef teal stroke-width:1px,stroke-dasharray:none,stroke:#2dd4bf,fill:#0d2926,color:#7eecd8
classDef gold stroke-width:1px,stroke-dasharray:none,stroke:#f0c040,fill:#2a2408,color:#f5d87a
classDef green stroke-width:1px,stroke-dasharray:none,stroke:#4ade80,fill:#0f2518,color:#8aedb3
classDef orange stroke-width:1px,stroke-dasharray:none,stroke:#fb923c,fill:#2a1a0d,color:#fdb97a
classDef red stroke-width:1px,stroke-dasharray:none,stroke:#f87171,fill:#2a1414,color:#fba4a4
classDef purple stroke-width:1px,stroke-dasharray:none,stroke:#e879f9,fill:#1f0e2a,color:#f0a8fc
classDef lime stroke-width:1px,stroke-dasharray:none,stroke:#a3e635,fill:#1a2408,color:#c4ee7a
classDef slate stroke-width:1px,stroke-dasharray:none,stroke:#94a3b8,fill:#1a1e24,color:#b8c4d4
classDef cyan stroke-width:1px,stroke-dasharray:none,stroke:#67e8f9,fill:#0e2428,color:#9ef0fb
classDef amber stroke-width:1px,stroke-dasharray:none,stroke:#fbbf24,fill:#2a2208,color:#fcd76a
classDef pink stroke-width:1px,stroke-dasharray:none,stroke:#f472b6,fill:#2a1020,color:#f9a4d0
classDef indigo stroke-width:1px,stroke-dasharray:none,stroke:#818cf8,fill:#181a30,color:#b0b8fb
classDef violet stroke-width:1px,stroke-dasharray:none,stroke:#a78bfa,fill:#1e1630,color:#c8b4fc
classDef sky stroke-width:1px,stroke-dasharray:none,stroke:#38bdf8,fill:#0e1e2a,color:#7ed4fb
```

색상 구성 원칙:
- **fill**: 어두운 배경 (다크 테마에 녹아듦)
- **stroke**: 밝은 엔티티 대표색 (선이 눈에 띄게)
- **color**: 밝은 파스텔 텍스트 (가독성 확보)

---

## 4. 생성 → 리뷰 → 개선 워크플로우

### 4-1. 초안 생성

1. 입력을 분석하여 데이터 모델을 도출한다
2. 해당 수준의 레퍼런스를 읽고 구조를 맞춘다
3. `.mmd` 파일을 생성한다
   - 사용자가 경로를 지정하면 그곳에 생성한다
   - 지정하지 않으면 사용자에게 질문한다: "ERD 파일을 어디에 생성할까요? (예: `./design/`, `./docs/`, 현재 디렉토리)"
   - 폴더가 없으면 생성한다
4. **`viewer.html` 을 같은 디렉토리에 함께 생성한다** (아래 4-2 참조)
5. 사용자에게 두 가지를 안내한다:
   - VS Code에서 `.mmd` 파일 프리뷰
   - 또는 `viewer.html` 을 브라우저에서 더블클릭 (pan/zoom 지원)

### 4-2. viewer.html 생성

이 스킬 디렉토리의 `viewer.html` 템플릿을 출력 디렉토리로 복사한 뒤, 마커 영역만 교체한다:

```html
<pre class="mermaid-source" id="src">
<!-- MMD_CONTENT_START -->
%% 이 주석 사이를 erd.mmd 파일 내용으로 교체하세요.
%% (frontmatter `--- config: ... ---` 포함 전체 본문을 그대로 붙여넣습니다.)
<!-- MMD_CONTENT_END -->
  </pre>
```

마커(`<!-- MMD_CONTENT_START -->` / `<!-- MMD_CONTENT_END -->`) 사이의 모든 라인을 방금 만든 `.mmd` 파일의 **전체 본문**(frontmatter `--- config: ... ---` 포함)으로 교체한다.

**제약**:
- viewer.html은 단일 HTML 한 파일. fetch로 별도 .mmd 읽지 않음 — mmd 본문을 inline으로 삽입
- 마커 자체(`MMD_CONTENT_START/END`)는 보존. 다음 갱신 시 다시 사용
- viewer.html의 다른 코드(Mermaid 초기화, svg-pan-zoom 설정, CSS 등)는 절대 변경하지 않음

### 4-3. 리뷰 반영

사용자 피드백에 따라 수정한다 (`.mmd` 와 `viewer.html` 의 mmd 본문을 함께 갱신):
- 엔티티 추가/삭제/이름 변경
- 속성 추가/삭제/타입 변경
- 관계 추가/삭제/카디널리티 변경
- 색상 변경

### 4-4. 수준 전환

사용자가 수준 전환을 요청하면 기존 ERD를 기반으로 변환한다:
- **개념 → 논리**: 각 엔티티에 속성(한글명 + 추상 타입)을 추가
- **논리 → 물리**: 속성명을 영문 snake_case로, 타입을 DB 종속으로 변환, 인덱스/DEFAULT 추가
- **물리 → 논리**: 영문→한글, DB 타입→추상 타입으로 역변환
- **논리 → 개념**: 속성 블록을 비움

---

## 5. 출력 스펙

같은 디렉토리에 두 파일을 함께 출력한다.

| 파일 | 내용 |
|---|---|
| `{프로젝트명}-{수준}-erd.mmd` | 단일 Mermaid `erDiagram` 정의 (frontmatter `--- config: ... ---` 포함). VS Code Mermaid 프리뷰에서 바로 렌더링 |
| `viewer.html` | mmd 본문이 inline으로 박힌 단일 HTML. 더블클릭으로 브라우저에서 열림. Mermaid 런타임 렌더링 + svg-pan-zoom (Fit / Zoom +/- 버튼) |

**규칙**:
- `viewer.html` 은 단일 HTML 한 파일. 외부 `.mmd` 를 fetch하지 않음 (file:// CORS 회피)
- `.mmd` 와 `viewer.html` 의 mmd 본문은 항상 동기화 (수정 시 둘 다 갱신)
- 한 파일에 하나의 `erDiagram` 만 포함
