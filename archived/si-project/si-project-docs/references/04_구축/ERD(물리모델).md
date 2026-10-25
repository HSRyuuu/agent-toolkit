# ERD(물리모델) 작성 가이드

## 목적

논리 데이터 모델을 실제 DBMS에 배포 가능한 물리 테이블 구조로 확정하고, DDL 스크립트와 인덱스 정의를 문서화하여 DB 구축·변경 이력 관리의 기준 산출물로 삼는다.

## 작성 시점

구축 단계 초기(논리 ERD 확정 직후)에 초안을 작성하고, 테이블 구조 변경(컬럼 추가·삭제, 인덱스 변경 등)이 발생할 때마다 버전을 올려 갱신한다.

## 메타데이터 헤더

| 항목 | 내용 |
|------|------|
| 문서명 | ERD(물리모델) |
| 프로젝트명 | {프로젝트명} |
| 버전 | {v1.0} |
| 작성일 | {YYYY-MM-DD} |
| 작성자 | {이름 (역할)} |
| 승인자 | {이름 (역할)} |

> **참고:** 본 문서는 최종 확정된 물리 테이블 ERD 정의서입니다.
> 실제 ERD 다이어그램 파일(`{ERD 파일명}`)을 함께 참조하십시오.

## 필수 섹션 구조

### 1. 물리 ERD 다이어그램 (텍스트 표현)
ERD 다이어그램 도구(ERDCloud, draw.io 등)로 작성한 ERD를 텍스트 아스키 아트로 표현한다. 각 테이블 박스에는 PK, FK, 주요 컬럼과 데이터 타입을 포함하고, 테이블 간 관계선(1:N, N:M 등)을 화살표로 표현한다. 코드 블록(`\`\`\``)으로 감싸 고정폭 폰트로 렌더링되게 한다. 실제 ERD 파일 경로나 도구 링크를 본문에 함께 안내한다.

### 2. DDL (물리 테이블 생성 스크립트)
실제 DBMS에 실행 가능한 전체 DDL을 sql 코드 블록으로 수록한다. 각 CREATE TABLE 앞에 테이블명을 주석으로 표기한다. PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL, DEFAULT 등 모든 제약 조건을 명시한다. 확장 기능(extension)이 필요한 경우 상단에 `CREATE EXTENSION` 구문을 포함한다.

### 3. 인덱스 목록
DDL에 포함된 모든 인덱스를 표로 정리한다. 테이블명, 인덱스명, 대상 컬럼, 인덱스 유형(BTREE/UNIQUE/Partial/IVFFlat 등), 생성 목적을 포함한다.

### 변경 이력
버전별 변경 내용을 추적한다.

## 주요 표 템플릿

### 물리 ERD 다이어그램 (텍스트 표현 예시)
```
┌──────────────────────────┐    ┌──────────────────────────┐
│  TB_{테이블A}             │    │  TB_{테이블B}             │
├──────────────────────────┤    ├──────────────────────────┤
│ PK {pk_컬럼} UUID        │    │ PK {pk_컬럼} UUID        │
│    {컬럼명} {데이터타입}  │    │ FK {fk_컬럼} UUID        │
│    {컬럼명} {데이터타입}  │    │    {컬럼명} {데이터타입}  │
│    created_at            │    │    created_at            │
│    updated_at            │    │    updated_at            │
│    deleted_at            │    │    deleted_at            │
└────────────┬─────────────┘    └──────────────────────────┘
             │ 1
             │ N
             ▼
       TB_{관계테이블}
```

### DDL 스크립트 (sql 코드 블록)
```sql
-- TB_{테이블명}
CREATE TABLE tb_{테이블명} (
    {pk_컬럼}    UUID         NOT NULL DEFAULT gen_random_uuid(),
    {컬럼명}     {데이터타입} NOT NULL,
    {fk_컬럼}    UUID         NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at   TIMESTAMPTZ,
    CONSTRAINT pk_{테이블명} PRIMARY KEY ({pk_컬럼}),
    CONSTRAINT fk_{테이블명}_{참조테이블} FOREIGN KEY ({fk_컬럼}) REFERENCES tb_{참조테이블}({참조pk_컬럼})
);
CREATE INDEX idx_{테이블명}_{컬럼} ON tb_{테이블명}({컬럼명}) WHERE deleted_at IS NULL;
```

### 인덱스 목록
| 테이블 | 인덱스명 | 컬럼 | 유형 | 목적 |
|--------|---------|------|------|------|
| {TB_테이블명} | {idx_인덱스명} | {컬럼명} | {BTREE / UNIQUE / Partial 등} | {인덱스 생성 목적} |

### 변경 이력
| 버전 | 변경일 | 변경 내용 | 작성자 | 승인자 |
|------|--------|----------|--------|--------|
| {v0.1} | {YYYY-MM-DD} | {변경 내용} | {작성자} | {승인자} |

## 작성 팁

- **Soft Delete 패턴 일관성**: `deleted_at TIMESTAMPTZ` 컬럼을 사용한 Soft Delete를 채택한 경우, 해당 컬럼이 있는 테이블의 UNIQUE 인덱스는 모두 `WHERE deleted_at IS NULL` 조건을 붙인 Partial Index로 생성해야 논리 삭제된 레코드와의 중복 문제를 방지할 수 있다.
- **DDL과 마이그레이션 도구 동기화**: 문서의 DDL은 Alembic, Flyway 등 마이그레이션 도구의 실제 스크립트와 항상 동일하게 유지한다. 마이그레이션 파일과 본 문서가 불일치하면 실제 DB 스키마의 근거가 불명확해지므로, 변경 시 반드시 함께 갱신한다.
- **텍스트 ERD 한계 명시**: 텍스트 표현은 가독성을 위한 요약이므로, 모든 컬럼과 제약 조건의 완전한 정의는 DDL 섹션이 기준임을 문서 첫머리에 안내한다.
