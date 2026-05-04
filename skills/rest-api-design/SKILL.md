---
name: rest-api-design
description: 새 REST API 엔드포인트를 설계하거나 기존 API 규약(URL 구조·상태 코드·응답 형식·페이지네이션·필터링·버전 관리)을 검토할 때 사용한다. 공개/파트너용 API를 설계할 때도 사용. 트리거 - "API 설계", "REST API 만들어줘", "엔드포인트 설계", "페이지네이션 패턴", "버전 관리 전략", "에러 응답 표준", "API 컨트랙트 리뷰".
---

# API 설계 패턴 (API Design Patterns)

일관성 있고 개발자 친화적인 REST API 설계를 위한 관례와 모범 사례입니다.

## 적용 시점

- 새로운 API 엔드포인트 설계 시
- 기존 API 규약(contract) 검토 시
- 페이지네이션, 필터링 또는 정렬 기능 추가 시
- API 에러 핸들링 구현 시
- API 버전 관리 전략 수립 시
- 공개 또는 파트너용 API 빌드 시

## 리소스 설계

### URL 구조

```
# 리소스는 명사, 복수형, 소문자, kebab-case를 사용합니다.
GET    /api/v1/users
GET    /api/v1/users/:id
POST   /api/v1/users
PUT    /api/v1/users/:id
PATCH  /api/v1/users/:id
DELETE /api/v1/users/:id

# 관계를 위한 하위 리소스
GET    /api/v1/users/:id/orders
POST   /api/v1/users/:id/orders

# CRUD로 매핑되지 않는 동작 (동사는 절제해서 사용)
POST   /api/v1/orders/:id/cancel
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
```

### 네이밍 규칙

```
# 올바른 예 (GOOD)
/api/v1/team-members          # 여러 단어로 된 리소스에는 kebab-case 사용
/api/v1/orders?status=active  # 필터링을 위해 쿼리 파라미터 사용
/api/v1/users/123/orders      # 소유권을 나타내기 위해 중첩 리소스 사용

# 잘못된 예 (BAD)
/api/v1/getUsers              # URL에 동사 포함
/api/v1/user                  # 단수형 사용 (복수형 권장)
/api/v1/team_members          # URL에 snake_case 사용
/api/v1/users/123/getOrders   # 중첩 리소스에 동사 포함
```

## HTTP 메서드 및 상태 코드

### 메서드 의미론

| 메서드 | 멱등성 (Idempotent) | 안전함 (Safe) | 용도 |
|--------|-----------|------|---------|
| GET | 예 | 예 | 리소스 조회 |
| POST | 아니요 | 아니요 | 리소스 생성, 동작 트리거 |
| PUT | 예 | 아니요 | 리소스 전체 교체 |
| PATCH | 아니요* | 아니요 | 리소스 일부 수정 |
| DELETE | 예 | 아니요 | 리소스 삭제 |

*PATCH는 적절한 구현을 통해 멱등성을 가질 수 있습니다.

### 상태 코드 참조

```
# 성공 (Success)
200 OK                    — GET, PUT, PATCH (응답 본체 포함 시)
201 Created               — POST (Location 헤더 포함)
204 No Content            — DELETE, PUT (응답 본체 없을 시)

# 클라이언트 에러 (Client Errors)
400 Bad Request           — 유효성 검사 실패, 잘못된 형식의 JSON
401 Unauthorized          — 인증 누락 또는 고유하지 않은 인증
403 Forbidden             — 인증은 되었으나 권한이 없음
404 Not Found             — 리소스가 존재하지 않음
409 Conflict              — 중복 항목, 상태 충돌
422 Unprocessable Entity  — 의미론적으로 유효하지 않음 (JSON은 유효하나 데이터가 잘못됨)
429 Too Many Requests     — 속도 제한 초과

# 서버 에러 (Server Errors)
500 Internal Server Error — 예상치 못한 실패 (상세 내용 노출 금지)
502 Bad Gateway           — 상위 서비스 실패
503 Service Unavailable   — 일시적인 과부하, Retry-After 포함 권장
```

### 흔한 실수

```
# 나쁜 예 (BAD): 모든 응답에 200 사용
{ "status": 200, "success": false, "error": "Not found" }

# 좋은 예 (GOOD): HTTP 상태 코드를 의미에 맞게 사용
HTTP/1.1 404 Not Found
{ "error": { "code": "not_found", "message": "User not found" } }

# 나쁜 예 (BAD): 유효성 검사 에러에 500 사용
# 좋은 예 (GOOD): 필드 레벨 상세 내용과 함께 400 또는 422 사용

# 나쁜 예 (BAD): 리소스 생성 시 200 사용
# 좋은 예 (GOOD): Location 헤더와 함께 201 사용
HTTP/1.1 201 Created
Location: /api/v1/users/abc-123
```

## 응답 형식

### 성공 응답

```json
{
  "data": {
    "id": "abc-123",
    "email": "alice@example.com",
    "name": "Alice",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

### 컬렉션 응답 (페이지네이션 포함)

```json
{
  "data": [
    { "id": "abc-123", "name": "Alice" },
    { "id": "def-456", "name": "Bob" }
  ],
  "meta": {
    "total": 142,
    "page": 1,
    "per_page": 20,
    "total_pages": 8
  },
  "links": {
    "self": "/api/v1/users?page=1&per_page=20",
    "next": "/api/v1/users?page=2&per_page=20",
    "last": "/api/v1/users?page=8&per_page=20"
  }
}
```

### 에러 응답

```json
{
  "error": {
    "code": "validation_error",
    "message": "요청 유효성 검사 실패",
    "details": [
      {
        "field": "email",
        "message": "유효한 이메일 주소여야 합니다",
        "code": "invalid_format"
      },
      {
        "field": "age",
        "message": "0에서 150 사이여야 합니다",
        "code": "out_of_range"
      }
    ]
  }
}
```

## 페이지네이션 (Pagination)

### 오프셋 기반 (Offset-Based, 단순형)

```
GET /api/v1/users?page=2&per_page=20

# 구현 예시
SELECT * FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 20;
```

**장점:** 구현이 쉽고, "n페이지로 이동" 기능을 지원함
**단점:** 큰 오프셋(예: OFFSET 100000)에서 느려짐, 데이터가 빈번히 추가될 때 중복 노출 가능성 있음

### 커서 기반 (Cursor-Based, 확장형)

```
GET /api/v1/users?cursor=eyJpZCI6MTIzfQ&limit=20

# 구현 예시
SELECT * FROM users
WHERE id > :cursor_id
ORDER BY id ASC
LIMIT 21;  -- has_next 여부를 확인하기 위해 하나 더 가져옴
```

**장점:** 데이터 양에 관계없이 일관된 성능, 실시간 데이터 추가 시에도 안정적임
**단점:** 임의의 페이지로 건너뛸 수 없음, 커서 값이 불투명함(opaque)

### 사용 기준

| 유스케이스 | 페이지네이션 유형 |
|----------|----------------|
| 관리자 대시보드, 소규모 데이터셋 (<10K) | 오프셋 (Offset) |
| 무한 스크롤, 피드, 대규모 데이터셋 | 커서 (Cursor) |
| 공개용 API | 커서(기본) 및 오프셋(선택사항) |
| 검색 결과 | 오프셋 (사용자가 페이지 번호를 기대함) |

## 필터링, 정렬 및 검색

### 필터링 (Filtering)

```
# 단순 일치
GET /api/v1/orders?status=active&customer_id=abc-123

# 비교 연산자 (대괄호 표기법 사용)
GET /api/v1/products?price[gte]=10&price[lte]=100
GET /api/v1/orders?created_at[after]=2025-01-01

# 다중 값 (쉼표로 구분)
GET /api/v1/products?category=electronics,clothing

# 중첩 필드 (점 표기법 사용)
GET /api/v1/orders?customer.country=US
```

### 정렬 (Sorting)

```
# 단일 필드 (내림차순은 - 접두사 사용)
GET /api/v1/products?sort=-created_at

# 다중 필드 (쉼표로 구분)
GET /api/v1/products?sort=-featured,price,-created_at
```
ㅁ
### 전문 검색 (Full-Text Search)

```
# 검색 쿼리 파라미터
GET /api/v1/products?q=wireless+headphones

# 필드 지정 검색
GET /api/v1/users?email=alice
```

## 인증 및 인가 (Authentication and Authorization)

### 토큰 기반 인증

```
# Authorization 헤더에 Bearer 토큰 포함
GET /api/v1/users
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

# API 키 (서버 간 통신용)
GET /api/v1/data
X-API-Key: sk_live_abc123
```

## 버전 관리 (Versioning)

### URL 경로 버전 관리 (권장)

```
/api/v1/users
/api/v2/users
```

**장점:** 명확함, 라우팅이 쉬움, 캐싱 가능
**단점:** 버전에 따라 URL이 변경됨

### 버전 관리 전략

```
1. /api/v1/으로 시작 — 필요하기 전까지는 버전을 올리지 마십시오
2. 최대 2개의 활성 버전(현재 + 이전)만 유지하십시오
3. 지원 중단(Deprecation) 일정:
   - 지원 중단 예고 (공개 API의 경우 6개월 전 공지)
   - Sunset 헤더 추가: Sunset: Sat, 01 Jan 2026 00:00:00 GMT
   - 일몰 날짜 이후 410 Gone 반환
4. 파괴적이지 않은 변경(Non-breaking)은 버전을 올릴 필요가 없습니다:
   - 응답에 새로운 필드 추가
   - 새로운 선택적 쿼리 파라미터 추가
   - 새로운 엔드포인트 추가
5. 파괴적인 변경(Breaking)은 새로운 버전이 필요합니다:
   - 필드 삭제 또는 이름 변경
   - 필드 타입 변경
   - URL 구조 변경
   - 인증 방식 변경
```

## API 설계 체크리스트

새로운 엔드포인트를 배포하기 전에 확인하십시오:

- [ ] 리소스 URL이 명명 규칙을 따르는가 (복수형, kebab-case, 동사 없음)
- [ ] 올바른 HTTP 메서드를 사용하고 있는가 (조회는 GET, 생성은 POST 등)
- [ ] 적절한 상태 코드를 반환하는가 (모두 200을 반환하지 않음)
- [ ] 스키마(Zod, Pydantic 등)를 통해 입력을 검증하는가
- [ ] 에러 응답이 표준 형식(코드 및 메시지)을 따르는가
- [ ] 목록 엔드포인트에 페이지네이션이 구현되어 있는가
- [ ] 인증이 필요한가 (또는 명시적으로 공개로 표시되었는가)
- [ ] 인가가 확인되었는가 (유저가 자신의 리소스에만 접근 가능한가)
- [ ] 속도 제한(Rate limiting)이 구성되어 있는가
- [ ] 응답에 내부 정보(스택 트레이스, SQL 에러)가 유출되지 않는가
- [ ] OpenAPI/Swagger 스펙이 업데이트되었는가
