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

### 2-D. 응답 스키마

반환 타입(`ResponseEntity<T>`, `response_model=`, 함수 리턴 타입)을 같은 규칙으로 평탄화한다. 공통 응답 래퍼(`ApiResponse<T>`, `CommonResponse` 등)가 있으면 **Step 3 공통 규약에 한 번만 쓰고**, 엔드포인트별 표에는 `data.` 이하만 적는다.

### 2-E. 에러

- Spring: `@ExceptionHandler`/`@ControllerAdvice`, 던지는 커스텀 예외와 ErrorCode enum
- FastAPI: `raise HTTPException(status_code=, detail=)`, exception handler
- Nest/Express: `throw new XxxException()`, 에러 미들웨어

해당 메서드에서 **실제로 던지는 것**만 엔드포인트 표에 적고, 전역 공통 에러는 Step 3으로 뺀다.

## Step 3: 공통 규약 추출

엔드포인트마다 반복될 내용을 문서 앞쪽에 한 번만 정리한다.

- 공통 응답 래퍼 구조와 예시
- 전역 에러 코드 표 (ErrorCode enum / 에러 핸들러에서 추출)
- 페이지네이션 규칙 (`Pageable`, `page`/`size`/`sort` 기본값, 응답의 `totalElements` 등)
- 날짜·타임존 포맷 (`@JsonFormat`, ObjectMapper 설정, `application.yml`)
- 공통 헤더 (인증 헤더 이름, `Content-Type`)

## Step 4: 출력 모드 분기

엔드포인트마다 **full(전체 명세) / delta(변경 블럭만)** 중 하나를 고른다. 판정은 자동으로 하고 사용자에게 묻지 않는다.

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

## Step 5: markdown 출력

기본 경로 `./api-spec.md`. 엔드포인트는 **도메인(컨트롤러) 단위로 그룹**하고 목차를 단다.

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
| 필요 | MEMBER | 정상 | `OrderController.kt:42` |

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

| 필드 | 타입 | 설명 |
|---|---|---|
| data.orderId | string | 주문 번호 |
| data.status | enum | PENDING \| PAID \| CANCELED |
| data.items[].qty | int | 수량 |

```json
{ "code": "SUCCESS", "data": { "orderId": "ORD-001", "status": "PENDING", "items": [{ "qty": 2 }] } }
```

#### Errors

| HTTP | code | 조건 |
|---|---|---|
| 400 | INVALID_QTY | qty가 1~99 범위 밖 |
| 409 | OUT_OF_STOCK | 재고 부족 |
```

### delta 블럭 (기존 엔드포인트 소폭 변경)

full 섹션을 다시 쓰지 않고, **바뀐 것만** 적는다. 기존 문서의 해당 엔드포인트 섹션은 실제 값으로 갱신하되, 전달용으로는 이 블럭을 뽑아준다.

```markdown
### 🔧 [변경] POST /api/v1/orders — 주문 생성

> 2026-08-11 · delta · Breaking: 없음 · 소스 `OrderController.kt:42`

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

### full 재발행 (기존 엔드포인트 대폭 변경)

Step 4에서 full로 판정되면 **엔드포인트 섹션 전체를 다시 발행**한다. 머리에 사유를 명시한다.

```markdown
### ⚠️ [전면 개정] POST /api/v1/orders — 주문 생성

> 2026-08-11 · full 재발행 · **Breaking** · 사유: `data`가 객체→배열, `legacyFlag` 삭제
> 이전 버전 기준 코드는 동작하지 않습니다. 아래 명세로 다시 맞춰주세요.
```

이후는 신규 엔드포인트와 동일한 full 템플릿(Request 표 / Response 표 / 예시 JSON / Errors)을 그대로 쓴다. 이 경우 응답 예시 JSON은 **생략 없이 전체**를 싣는다.

### 전달용 요약 헤더

기존 문서 갱신이면 문서 최상단 메타 표 아래에 이번 회차 요약을 붙인다.

```markdown
## 이번 변경 (2026-08-11)

| 엔드포인트 | 모드 | Breaking |
|---|---|---|
| POST /api/v1/orders | ⚠️ full 재발행 | Y |
| GET /api/v1/orders | 🔧 delta | N |
| POST /api/v1/payments | 🆕 신규 | - |
```

문서 끝에는 두 섹션을 붙인다.

- `## 변경 이력` — 날짜 / 변경 내용 / 영향받는 FE 화면 (첫 생성 시 최초 행만)
- `## 부록 — 제외된 엔드포인트` — Step 0에서 제외한 admin/batch/actuator 목록 (있을 때만)

### 예시 JSON 생성 규칙

- 표의 타입·제약과 **모순되지 않는 값**만 쓴다
- enum은 첫 번째 값
- 실제 운영 데이터·사번·회사 식별자·토큰은 절대 넣지 않는다. 전부 `P-001`, `ORD-001` 같은 중립 더미
- 필수 아닌 필드는 `null`로 남겨 필수/선택 구분이 예시에서도 드러나게 한다

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

- 목차의 앵커가 실제 섹션과 전부 맞는가
- 표에 있는 필드가 예시 JSON과 서로 모순되지 않는가
- enum 값을 나열하지 않고 `enum`으로만 둔 행이 없는가
- 소스에 없는 필드를 만들어 넣지 않았는가
- 실제 토큰·회사 식별자·운영 데이터가 예시에 섞이지 않았는가

갱신 모드일 때 추가로:

- delta 판정한 엔드포인트에 breaking 신호가 실제로 하나도 없는가 (있으면 full로 올린다)
- delta 표에 **안 바뀐 행**이 섞이지 않았는가
- `## 이번 변경` 표의 모드가 각 블럭 머리의 표기와 일치하는가
- 변경 없는 엔드포인트 섹션이 불필요하게 다시 쓰이지 않았는가 (git diff로 확인)
