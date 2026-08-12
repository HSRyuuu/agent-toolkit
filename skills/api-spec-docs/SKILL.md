---
name: api-spec-docs
description: >
  Use when producing a human-readable REST API specification document from
  backend source code (Spring Boot Java/Kotlin, FastAPI, NestJS, Express) to
  hand off to frontend developers, QA, or partners. Triggers: "API 명세서
  만들어줘", "API 문서 뽑아줘", "컨트롤러에서 API 스펙 정리", "FE에 전달할 API
  문서", "엔드포인트 명세 markdown", "api spec docs", "/api-spec-docs". Do NOT
  use for designing new API contracts (use `rest-api-design`), for screen-level
  UI specs (use `ui-feature-spec-docs`), or for running/searching Postman
  requests (use `postman-helper`).
---

# api-spec-docs — 사람이 읽는 API 명세서 생성 스킬

백엔드 소스(Controller/Router + DTO)를 읽어 **FE 개발자에게 그대로 전달 가능한 단일 markdown API 명세서**를 만든다. Postman 컬렉션 전달을 대체하는 것이 목적이므로, Postman이 못 주는 것 — **타입·필수 여부·제약·enum·에러 조건** — 을 채우는 데 집중한다.

## Overview

핵심 원칙:
- **입력은 백엔드 소스코드** — Controller/Router와 DTO/스키마가 단일 진실. OpenAPI 어노테이션이 있으면 보조로 쓰되, 없어도 동작한다.
- **단일 markdown 출력** — 엔드포인트가 몇 개든 하나의 `.md`. git diff로 API 변경 리뷰가 되는 게 이 포맷을 고른 이유다.
- **중첩 객체는 dot-path로 평탄화** — `data.items[].qty` 형태로 표 한 장에 담는다. 이 스킬의 핵심 산출 규칙.
- **신규는 전체, 수정은 변경분만** — 신규 엔드포인트는 응답 JSON 포함 full 명세, 기존 소폭 변경은 delta 블럭만. 단 breaking change면 소폭이어도 full 재발행 (Step 4).
- **예시는 전량이 아니라 전 분기** — full이어도 응답 JSON을 통째로 붙이지 않는다. 모든 분기가 한 번씩 드러나는 최소 예시 + 생략 마커 (Step 5 예시 규칙).
- **부재도 명세** — 무엇이 안 오는지, 무엇을 FE가 직접 만들어야 하는지를 명시한다. Postman이 못 주는 정보 중 enum 다음으로 값어치가 크다.
- **발명 금지** — 소스에 없는 필드·에러·설명을 추측해서 채우지 않는다. 모르면 `(TBD)`, 추론이면 `⚠️`.
- **시작 1회 입력 수집, 이후 무질문** — 모호한 건 결과물에 마커로 보존하고 사용자가 받아본 뒤 결정한다.

## When to Use

- 기존 백엔드 코드에서 FE 전달용 API 명세서를 역추출
- Postman 컬렉션 대신 문서로 API를 인계
- 외주·파트너에게 API 스펙 산출물 전달
- 스프린트 종료 시 변경된 엔드포인트만 문서 갱신

**사용하지 않을 때:**
- 신규 API 설계·컨트랙트 리뷰 → `rest-api-design`
- 화면 단위 기능 명세 → `ui-feature-spec-docs`
- Postman 요청 검색·실행 → `postman-helper`
- 기계 판독용 스펙(코드 생성·모킹)이 목적 → OpenAPI 생성기를 쓰는 게 맞다

## Step 0: 입력 수집 (시작 시 한 번)

**모든 질문은 여기서 한꺼번에 묻고, 이후 단계에서는 묻지 않는다.**

### 필수
- **소스 경로** — Controller/Router 디렉토리 또는 프로젝트 루트

### 선택 (안 주면 기본값·플레이스홀더)
- **범위** — 전체 / 특정 패키지·디렉토리 / 특정 엔드포인트 목록 (기본: 전체)
- **출력 경로** (기본 `./api-spec.md`)
- **base URL** — dev/prod (기본 `(TBD)`)
- **프로젝트명·작성자** (메타데이터용)
- **내부 API 포함 여부** — admin·batch·actuator 계열 (기본 제외, 제외한 목록은 부록에 남김)
- **출력 모드** — `full` / `delta` (기본: Step 4 규칙으로 자동 판정. 사용자가 지정하면 그 값이 우선)

프레임워크 자동 감지가 실패할 것 같으면(`build.gradle`/`pom.xml`/`package.json`/`pyproject.toml`을 미리 확인) 이때 함께 묻는다.

**Step 0 끝 = 묻기 끝.**

## Step 1: 프레임워크 감지 + 엔드포인트 추출

### 1-A. 감지

| 신호 | 프레임워크 |
|---|---|
| `build.gradle(.kts)`/`pom.xml` + `spring-boot-starter-web` | Spring Boot (파일 확장자로 Java/Kotlin 구분) |
| `pyproject.toml`/`requirements.txt` + `fastapi` | FastAPI |
| `package.json` + `@nestjs/core` | NestJS |
| `package.json` + `express` | Express |

감지 실패 시 Step 0에서 받은 값을 쓰고, 그것도 없으면 라우팅 정의 패턴을 직접 grep해서 진행한다.

### 1-B. 엔드포인트 목록 추출

| 프레임워크 | 추출 위치 |
|---|---|
| Spring Boot | `@RestController`/`@Controller` 클래스의 `@RequestMapping` prefix + 메서드의 `@GetMapping`/`@PostMapping`/`@PutMapping`/`@PatchMapping`/`@DeleteMapping`/`@RequestMapping(method=)` |
| FastAPI | `APIRouter(prefix=)` + `@router.get/post/put/patch/delete`, `app.include_router(..., prefix=)`의 중첩 prefix |
| NestJS | `@Controller('path')` + `@Get/@Post/@Put/@Patch/@Delete` |
| Express | `app.<method>()` / `router.<method>()` + `app.use('/prefix', router)` |

클래스 prefix와 메서드 path를 **합쳐서 최종 full path**로 적는다. 라우터가 여러 겹 중첩되면 전부 펼친다.

### 1-C. 엔드포인트 메타

각 엔드포인트별로 수집:

| 항목 | 소스 |
|---|---|
| 설명 | 메서드 javadoc/kdoc/docstring, `@Operation(summary=)`, `summary=` 인자. 없으면 메서드명에서 유추하고 `⚠️` |
| 소스 위치 | `파일명#메서드명` 을 기본으로 쓰고, 라인번호는 병기만 한다 (`SearchController.java#getMain:50`). 라인번호는 다음 커밋에 썩는다 |
| 인증 | Spring: `@PreAuthorize`/`@Secured`/SecurityConfig의 matcher. FastAPI: `Depends(get_current_user)` 류. Nest: `@UseGuards`. 판단 못 하면 `(TBD)` |
| 권한 | `@PreAuthorize("hasRole('X')")`, `@Roles(...)`, 라우터 미들웨어 인자 |
| 상태 | `@Deprecated`, `TODO`/`FIXME` 주석, 미구현 스텁이면 각각 마커 |

## Step 2: 필드 추출과 평탄화 (이 스킬의 핵심)

### 2-A. 파라미터 위치별 수집

| 위치 | Spring | FastAPI | Nest/Express |
|---|---|---|---|
| path | `@PathVariable` | 함수 인자 중 path에 등장하는 이름 | `@Param` / `req.params` |
| query | `@RequestParam`, `@ModelAttribute` DTO | `Query(...)`, Pydantic `Depends()` 모델 | `@Query` / `req.query` |
| header | `@RequestHeader` | `Header(...)` | `@Headers` / `req.headers` |
| body | `@RequestBody` DTO | Pydantic 모델 인자 | `@Body` DTO / `req.body` |

### 2-B. dot-path 평탄화 규칙

DTO를 재귀 순회해 **필드 하나 = 표의 한 행**으로 편다.

- 중첩 객체: `user.address.zipCode`
- 배열/리스트: `items[].productId`
- 배열의 배열: `matrix[][]`
- Map/Dict: `attributes.{key}` 로 적고 값 타입을 설명에 씀
- **최대 depth 4** — 초과하면 그 지점에서 멈추고 타입명만 적은 뒤 `⛔ depth 제한` 마커
- **순환 참조**는 첫 재등장에서 멈추고 `⛔ 순환 참조` 마커

### 2-C. 타입·필수·제약 매핑

| 소스 | 문서 표기 |
|---|---|
| `String`/`str` | string |
| `int`/`Long`/`Integer` | int |
| `BigDecimal`/`Double`/`float` | number |
| `LocalDateTime`/`datetime` | string (ISO-8601, 예시 포함) |
| enum 타입 | `enum` + 값 전부 나열 (`PENDING \| PAID \| CANCELED`) |
| Kotlin non-null / `@NotNull`/`@NotBlank`/`required=true` / Pydantic 필수 필드 | 필수 `Y` |
| Kotlin nullable(`?`) / `Optional<T>` / `= None` / `required=false` | 필수 `N` |
| 기본값이 선언돼 있으면 | 기본값 컬럼에 그대로 |
| `@Size`/`@Min`/`@Max`/`@Pattern`/`Field(ge=, le=, max_length=)` | 설명 컬럼에 제약 병기 (`1~99`, `최대 50자`) |

**enum은 반드시 값을 전부 펼친다.** FE가 Postman에서 못 얻던 정보 1순위다.

위 `필수 Y/N`은 **요청 표에서만** 쓴다. 응답에는 2-D의 `존재` 컬럼을 쓴다.

### 2-D. 응답 스키마

반환 타입(`ResponseEntity<T>`, `response_model=`, 함수 리턴 타입)을 같은 규칙으로 평탄화한다.

**응답 표는 `필수` 대신 `존재` 컬럼을 쓴다.** 응답에서 `N`은 "요청에서 생략 가능" · "null일 수 있음" · "특정 조건에서만 존재"를 한 글자로 눌러버린다. 사람은 산문으로 보정해 읽지만, 표만 파싱하는 쪽은 전부 optional로 읽는다.

| 값 | 의미 |
|---|---|
| `항상` | 어떤 응답에서도 반드시 존재 |
| `조건부: {조건}` | 조건을 그 자리에 그대로 쓴다 (`조건부: type=AMBASSADOR_PICK`, `조건부: 최저가 판정 시`, `조건부: 앱 전용`) |
| `없음` | 스키마에는 있으나 이 엔드포인트·이 타입에서는 절대 안 내려감 |

**부모가 조건부면 자식의 `존재`는 `조건부: {부모} 존재 시`로 적는다.** 부모가 조건부인데 자식만 `항상`으로 적으면 읽는 쪽이 null 체크를 뺀다.

```
| `lowest_price`      | object | 조건부: 최저가 판정 시        |
| `lowest_price.name` | string | 조건부: lowest_price 존재 시 |
```

응답 성격의 표는 **전부** 이 컬럼을 단다. 카드 표에만 달고 상위 배너·래퍼 표에서 빠뜨리면 그 표의 필드는 항상 존재하는 것으로 읽힌다.

### 2-D-2. 공유 스키마 hoisting

**2개 이상 엔드포인트가 같은 DTO를 반환하면 Step 3 공통 규약으로 올린다.** 엔드포인트 섹션에는 **차이나는 것만** 쓴다 ("앱과 동일한 구조이며 랜딩 필드만 다릅니다" 식).

공통 응답 래퍼(`ApiResponse<T>`, `CommonResponse` 등)도 같은 규칙이다. 래퍼가 있으면 공통 규약에 한 번만 쓰고, 엔드포인트별 표에는 `data.` 이하만 적는다.

### 2-E. 에러

- Spring: `@ExceptionHandler`/`@ControllerAdvice`, 던지는 커스텀 예외와 ErrorCode enum
- FastAPI: `raise HTTPException(status_code=, detail=)`, exception handler
- Nest/Express: `throw new XxxException()`, 에러 미들웨어

해당 메서드에서 **실제로 던지는 것**만 엔드포인트 표에 적고, 전역 공통 에러는 Step 3으로 뺀다.

## Step 3: 공통 규약 추출

엔드포인트마다 반복될 내용을 문서 앞쪽에 한 번만 정리한다.

- 공통 응답 래퍼 구조와 예시
- 여러 엔드포인트가 공유하는 DTO (2-D-2)
- **직렬화 규칙** — 네이밍 전략(`SNAKE_CASE` 등)과 **null 필드 처리**. `@JsonInclude(NON_NULL)`/`exclude_none=True`면 "null 필드는 응답에서 생략됨"을 반드시 못 박는다. 이 한 줄이 모든 optional 필드의 소비 방식을 바꾼다
- 전역 에러 코드 표 (ErrorCode enum / 에러 핸들러에서 추출)
- 페이지네이션 규칙 (`Pageable`, `page`/`size`/`sort` 기본값, 응답의 `totalElements` 등)
- 날짜·타임존 포맷 (`@JsonFormat`, ObjectMapper 설정, `application.yml`)
- 공통 헤더 (인증 헤더 이름, `Content-Type`)

## Step 4: 출력 모드 분기

**full(전체 명세) / delta(변경 블럭만)** 중 하나를 고른다. 판정은 자동으로 하고 사용자에게 묻지 않는다.

### 판정 단위

기본 단위는 엔드포인트다. 단 **여러 엔드포인트가 공유하는 DTO 하나가 바뀐 경우, 판정과 delta 블럭은 스키마 단위로 1회만** 발행한다. 같은 변경 표를 엔드포인트 수만큼 복사하지 않는다.

이때 `## 이번 변경` 표에는 영향받는 엔드포인트를 전부 나열하되, 변경 표 본문은 공유 블럭 하나를 가리키게 한다.

### 판정 규칙

기존 문서(출력 경로의 `.md`)에 그 엔드포인트가 **없으면 신규**, 있으면 기존 문서와 소스를 비교한다.

| 조건 | 모드 |
|---|---|
| 신규 엔드포인트 | **full** |
| 기존 문서가 아예 없음 (첫 생성) | **full** (전건) |
| 아래 breaking 신호가 **하나라도** 있음 | **full** |
| 변경된 필드가 해당 엔드포인트 전체 필드의 **30% 초과** | **full** |
| 그 외 (non-breaking 소폭 변경) | **delta** |

**breaking 신호** — 하나만 걸려도 full:
- 응답 최상위 구조 변경 (래퍼 교체, `data`가 객체↔배열)
- 기존 필드 **삭제** 또는 **이름 변경**
- 타입 변경 (`int` → `string` 등)
- 선택 → 필수 승격
- enum 값 **삭제** (추가는 breaking 아님)
- path·method 변경, 인증/권한 요구 강화

**delta로 남는 대표 케이스**: 선택 필드 추가, enum 값 추가, 설명·예시 보강, 제약 완화, 에러 코드 추가.

판정 결과는 각 블럭 머리에 그대로 적어 FE가 "왜 전체가 왔는지"를 알 수 있게 한다.

### Breaking은 두 컬럼으로 쪼갠다

`Breaking` 하나로 적으면 "Y로 쓰면 과장, N으로 쓰면 거짓"인 상황에서 매번 흔들리고, 결국 문서 안에서 자기모순이 난다 (삭제 필드가 표에 있는데 `Breaking: N`).

| 컬럼 | 판정 근거 |
|---|---|
| `Breaking(스펙)` | 위 breaking 신호 목록에 기계적으로 걸리면 무조건 `Y`. FE가 그 필드를 실제로 썼는지는 여기서 따지지 않는다 |
| `실무 영향` | 무시해도 안전한지 사람이 읽을 한 줄. `없음 (미사용 필드)`, `분기 추가 필요` 등 |

출력 모드는 **`Breaking(스펙)` 쪽으로만** 판정한다. "안 쓰던 필드니까 괜찮다"는 full 재발행을 면제하는 근거가 아니다.

### 모드 마커는 이 셋뿐

| 마커 | 뜻 |
|---|---|
| `🆕 신규` | 기존 문서에 없던 엔드포인트 |
| `🔧 delta` | 기존 엔드포인트 소폭 변경 |
| `⚠️ full 재발행` | 기존 엔드포인트 대폭·breaking 변경 |

이 셋 밖의 표기를 만들지 않는다. `🆕 변경 (full)` 처럼 섞으면 `## 이번 변경` 표와 블럭 머리가 어긋난다.

## Step 5: markdown 출력

기본 경로 `./api-spec.md`. 엔드포인트는 **도메인(컨트롤러) 단위로 그룹**하고 목차를 단다.

**헤딩은 평문으로 쓴다.** 백틱·괄호를 넣으면 앵커가 `#list_cs-카드-itemsitems`처럼 깨져 목차가 어긋난다. 코드 표기는 헤딩 아래 본문에서 한다.

범위를 티켓·기능으로 한정한 문서면 메타 표에 `대상 티켓`·`브랜치`를 추가하고, **무엇이 범위 밖인지**(무변경 항목)를 메타 표 바로 아래 한 줄로 못 박는다.

```markdown
# {프로젝트명} API 명세서

| 항목 | 내용 |
|---|---|
| 작성일 | {YYYY-MM-DD} |
| 작성자 | {작성자} |
| Base URL (dev) | {url} |
| Base URL (prod) | {url} |
| 인증 방식 | Bearer Token (`Authorization: Bearer {token}`) |
| 엔드포인트 수 | {N} |

## 목차
- [공통 규약](#공통-규약)
- [주문](#주문)
  - [POST /api/v1/orders — 주문 생성](#post-apiv1orders--주문-생성)

## 공통 규약

### 직렬화 규칙
전역 `SNAKE_CASE`. **`null` 필드는 응답에서 생략됩니다** (`@JsonInclude(NON_NULL)`).

### 공통 응답 래퍼
```json
{ "code": "SUCCESS", "message": null, "data": { } }
```

### 전역 에러 코드
| HTTP | code | 설명 |
|---|---|---|
| 401 | UNAUTHORIZED | 토큰 없음/만료 |

### 페이지네이션
| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| page | int | 0 | 0-based |

---

## 주문

### POST /api/v1/orders — 주문 생성

주문을 생성하고 결제 대기 상태로 만든다.

| 인증 | 권한 | 상태 | 소스 |
|---|---|---|---|
| 필요 | MEMBER | 정상 | `OrderController.kt#create:42` |

#### Request

| 위치 | 필드 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| query | dryRun | boolean | N | false | 검증만 수행 |
| body | items[].productId | string | Y | - | 상품 ID |
| body | items[].qty | int | Y | - | 1~99 |
| body | memo | string | N | - | 최대 200자 |

```json
{ "items": [{ "productId": "P-001", "qty": 2 }], "memo": null }
```

#### Response 200

| 필드 | 타입 | 존재 | 설명 |
|---|---|---|---|
| data.orderId | string | 항상 | 주문 번호 |
| data.status | enum | 항상 | PENDING \| PAID \| CANCELED |
| data.items[].qty | int | 항상 | 수량 |
| data.coupon | object | 조건부: 쿠폰 적용 시 | 적용 쿠폰 |
| data.coupon.code | string | 조건부: coupon 존재 시 | 쿠폰 코드 |

```json
{ "code": "SUCCESS", "data": { "orderId": "ORD-001", "status": "PENDING", "items": [{ "qty": 2 }] } }
```

#### 내려주지 않는 것

- `status` 별 표시 문구 — 서버는 코드만 주고 문구는 FE가 매핑
- 쿠폰 미적용이면 `coupon` 키 자체가 없음 (null 아님)

#### Errors

| HTTP | code | 조건 |
|---|---|---|
| 400 | INVALID_QTY | qty가 1~99 범위 밖 |
| 409 | OUT_OF_STOCK | 재고 부족 |
```

**`#### 내려주지 않는 것`은 full 블럭의 필수 섹션이다.** 서버가 안 주는 값, FE가 하드코딩해야 하는 것(스타일·에셋·문구), 스키마엔 있으나 이 엔드포인트에선 안 실리는 필드를 적는다. 쓸 게 없으면 `- 없음`.

### delta 블럭 (기존 엔드포인트 소폭 변경)

full 섹션을 다시 쓰지 않고, **바뀐 것만** 적는다. 기존 문서의 해당 엔드포인트 섹션은 실제 값으로 갱신하되, 전달용으로는 이 블럭을 뽑아준다.

```markdown
### 🔧 delta — POST /api/v1/orders 주문 생성

> 2026-08-11 · Breaking(스펙): N · 실무 영향: 없음 (하위 호환) · 소스 `OrderController.kt#create:42`

| 구분 | 위치 | 필드 | 변경 전 | 변경 후 |
|---|---|---|---|---|
| 추가 | body | memo | - | string / 선택 / 최대 200자 |
| 변경 | response | data.status | PENDING \| PAID | PENDING \| PAID \| CANCELED |
| 변경 | body | items[].qty | 1~50 | 1~99 |
| 추가 | error | 409 OUT_OF_STOCK | - | 재고 부족 시 |

**FE 영향**
- `data.status` 에 `CANCELED` 분기 추가 필요
- `memo`는 선택 필드 — 기존 요청 그대로 보내도 동작

**변경분 예시**
```json
{ "memo": "선물포장", "items": [{ "productId": "P-001", "qty": 99 }] }
```
```

규칙:
- 표에는 **바뀐 행만** 넣는다. 안 바뀐 필드는 쓰지 않는다.
- `변경 전` 값은 기존 문서에서 읽는다. 기존 문서에 없어 확인 불가면 `(TBD)`.
- **FE 영향**은 필수 섹션. 쓸 게 없으면 `- 없음 (하위 호환)`.
- 예시 JSON은 **변경된 필드가 드러나는 부분만**. 전체 payload를 다시 붙이지 않는다.
- 여러 엔드포인트가 공유하는 DTO 변경이면 이 블럭을 **한 번만** 쓰고 영향 엔드포인트를 머리에 나열한다 (Step 4 판정 단위).

### full 재발행 (기존 엔드포인트 대폭 변경)

Step 4에서 full로 판정되면 **엔드포인트 섹션 전체를 다시 발행**한다. 머리에 사유를 명시한다.

```markdown
### ⚠️ full 재발행 — POST /api/v1/orders 주문 생성

> 2026-08-11 · Breaking(스펙): Y · 실무 영향: 기존 파싱 코드 동작 불가
> 사유: `data`가 객체→배열, `legacyFlag` 삭제. 아래 명세로 다시 맞춰주세요.
```

이후는 신규 엔드포인트와 동일한 full 템플릿(Request 표 / Response 표 / 예시 JSON / 내려주지 않는 것 / Errors)을 그대로 쓴다.

### 전달용 요약 헤더

기존 문서 갱신이면 문서 최상단 메타 표 아래에 이번 회차 요약을 붙인다.

```markdown
## 이번 변경 (2026-08-11)

| 엔드포인트 | 모드 | Breaking(스펙) | 실무 영향 |
|---|---|---|---|
| POST /api/v1/orders | ⚠️ full 재발행 | Y | 기존 파싱 코드 동작 불가 |
| GET /api/v1/orders | 🔧 delta | N | 없음 (하위 호환) |
| POST /api/v1/payments | 🆕 신규 | - | 신규 연동 |
```

`모드` 값은 Step 4의 세 마커만 쓰고, 각 블럭 머리의 표기와 글자까지 일치시킨다.

문서 끝에는 두 섹션을 붙인다.

- `## 변경 이력` — 날짜 / 변경 내용 / 영향받는 FE 화면 (첫 생성 시 최초 행만)
- `## 부록 — 제외된 엔드포인트` — Step 0에서 제외한 admin/batch/actuator 목록 (있을 때만)

### 예시 JSON 생성 규칙

- 표의 타입·제약과 **모순되지 않는 값**만 쓴다
- enum은 첫 번째 값
- 실제 운영 데이터·사번·회사 식별자·토큰은 절대 넣지 않는다. 전부 `P-001`, `ORD-001` 같은 중립 더미

#### null / 생략

**직렬화 설정을 먼저 확인한다** (Step 3).

- 생략형(`@JsonInclude(NON_NULL)`, `exclude_none=True`)이면 선택 필드를 **키째 뺀다**. `null`을 적으면 실제로 오지 않는 모양의 예시가 된다
- 그렇지 않으면 선택 필드를 `null`로 남겨 필수/선택 구분이 예시에서도 드러나게 한다
- 어느 쪽이든 필수/선택의 진짜 근거는 표의 `존재` 컬럼이다. 예시는 보조다

#### 분량 — 전량이 아니라 전 분기

응답이 수백~수천 행이 될 수 있으므로, full이어도 통째로 붙이지 않는다. **모든 분기가 한 번씩 드러나는 최소 예시**를 만든다.

- 배열은 **대표 원소 2개까지** — 서로 다른 분기를 보여주는 것으로 고른다 (예: 매진 카드 1 + 정상 카드 1). 같은 모양을 두 번 넣지 않는다
- 나머지는 `// ... 동일 구조 N건 생략` 마커. **생략했다는 사실을 반드시 남긴다**
- 반복 없이 순수하게 필드가 많아 긴 경우엔 최상위 + 대표 서브트리 1개만 펼치고, 나머지 서브트리는 표에만 둔다
- 빈 상태(`items: []`)처럼 구조가 달라지는 케이스는 **별도 짧은 예시**로 따로 붙인다
- 예시에 안 나온 분기가 있으면 예시 바로 아래 한 줄로 무엇이 생략됐는지 적는다

## 마커 표기 규칙

작업 중 사용자에게 묻지 않고, 애매한 케이스를 결과물에 보존한다.

| 마커 | 의미 |
|---|---|
| `(TBD)` | 소스에 정보가 없음. 사용자가 채워야 함 |
| `⚠️ 추론` | 소스에서 직접 못 읽고 이름·관례로 유추한 값 (설명, 인증 여부 등) |
| `🚧 미구현` | 스텁·TODO·FIXME가 달린 엔드포인트 |
| `⛔ depth 제한` | 평탄화 depth 4 초과로 중단 |
| `⛔ 순환 참조` | DTO 순환 참조로 중단 |
| `🗑 deprecated` | `@Deprecated` 표시된 엔드포인트 |

## 갱신 모드

출력 경로에 이미 문서가 있으면 **문서 전체를 재생성하지 않는다.**

1. 기존 문서의 엔드포인트 목록과 소스 추출 목록을 비교
2. 엔드포인트별로 Step 4 규칙에 따라 신규 / delta / full 재발행을 판정
3. **변경 없는 엔드포인트는 손대지 않는다** — 문장을 다시 쓰지도 않는다
4. 사람이 손으로 채운 내용(`(TBD)`를 채운 설명, 비고)은 **덮어쓰지 않는다**
5. 소스에서 사라진 엔드포인트는 지우지 말고 `🗑 deprecated` + 삭제 예정 표기로 남긴다
6. `## 이번 변경` 표를 새로 쓰고 `## 변경 이력`에 행을 추가

## 검증

문서를 쓴 뒤 스스로 확인한다.

- 목차의 앵커가 실제 섹션과 전부 맞는가 (헤딩에 백틱·괄호를 넣지 않았는가)
- 표에 있는 필드가 예시 JSON과 서로 모순되지 않는가
- enum 값을 나열하지 않고 `enum`으로만 둔 행이 없는가
- 소스에 없는 필드를 만들어 넣지 않았는가
- 실제 토큰·회사 식별자·운영 데이터가 예시에 섞이지 않았는가

`존재` 컬럼:

- **응답 성격의 표에 `존재` 컬럼이 빠진 것이 없는가** — 하위 카드 표에만 달고 상위 래퍼·배너 표에서 빠뜨리기 쉽다
- `조건부`인데 조건을 안 적고 `조건부`로만 둔 행이 없는가
- 부모가 `조건부`인데 자식이 `항상`으로 적힌 행이 없는가
- 산문에만 있고 표에는 안 들어간 존재 조건이 없는가 (표만 읽어도 같은 결론이 나와야 한다)

예시 JSON:

- 직렬화가 생략형인데 예시에 `null`을 적지 않았는가 (반대도 마찬가지)
- 배열을 통째로 붙이지 않았는가. 생략한 곳에 생략 마커가 있는가
- 표에 있는 분기 중 예시에 한 번도 안 나온 것이 있으면, 그 사실이 문서에 적혀 있는가

갱신 모드일 때 추가로:

- delta 판정한 엔드포인트에 breaking 신호가 실제로 하나도 없는가 (있으면 full로 올린다)
- **변경 표에 `삭제` 행이 있는데 `Breaking(스펙): N`으로 적히지 않았는가** — 삭제는 무조건 Y다
- delta 표에 **안 바뀐 행**이 섞이지 않았는가
- `## 이번 변경` 표의 모드가 각 블럭 머리의 표기와 글자까지 일치하는가. Step 4의 세 마커 밖의 값이 없는가
- 공유 DTO 변경인데 같은 변경 표를 엔드포인트마다 복사하지 않았는가
- 변경 없는 엔드포인트 섹션이 불필요하게 다시 쓰이지 않았는가 (git diff로 확인)
