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

# api-spec-docs — API 명세서(규격) 생성 스킬

백엔드 소스(Controller/Router + DTO)를 읽어 **FE에게 전달하는 API 규격서 한 장**을 만든다. 기존에 전달하던 것은 Postman 응답 예시와 링크다. 이 문서는 그 자리를 대신하는 **규격서**이지, 작업 인수인계 문서나 설계 배경 문서가 아니다.

## Overview

핵심 원칙:
- **규격만 쓴다** — 요청 스펙 / 응답 스펙 / 에러. 배경, 설계 의도, 구현 히스토리, 검증 서사는 쓰지 않는다.
- **표가 본문, 산문은 예외** — 필드 정보는 전부 표의 컬럼에 들어간다. 표 밖 산문·인용 블럭은 `## 도메인 규칙`에만 둔다 (Step 3-B).
- **입력은 백엔드 소스코드** — Controller/Router와 DTO/스키마가 단일 진실. OpenAPI 어노테이션은 보조.
- **단일 markdown 출력** — 엔드포인트가 몇 개든 하나의 `.md`. git diff로 API 변경 리뷰가 되는 게 이 포맷을 고른 이유다.
- **중첩 객체는 dot-path로 평탄화** — `data.items[].qty` 형태로 표 한 장에 담는다.
- **독자는 FE** — 백엔드 내부 어휘(클래스·어노테이션·테이블·설정 키)는 FE가 보는 결과로 번역한다. 다음 섹션이 이 규칙 전체다.
- **예시는 전량이 아니라 전 분기** — 응답 JSON을 통째로 붙이지 않는다. 모든 분기가 한 번씩 드러나는 최소 예시 + 생략 마커.
- **발명 금지** — 소스에 없는 필드·에러·설명을 추측해서 채우지 않는다. 모르면 `(TBD)`, 추론이면 `⚠️`.
- **시작 1회 입력 수집, 이후 무질문** — 모호한 건 결과물에 마커로 보존하고 사용자가 받아본 뒤 결정한다.

**분량 상한** — 엔드포인트 하나는 `Request 표` + `Response 표` + `예시 JSON 1~3개` + `Errors 표`가 전부다. 여기에 안 들어가는 설명은 (a) 필드 `설명` 컬럼에 한 구절로 넣거나 (b) `## 도메인 규칙` 한 줄로 올리거나 (c) 지운다. 엔드포인트 블럭 안에서 표 밖 산문은 **합계 2줄까지**.

## 독자 기준 — 이 문서는 FE가 읽는다

명세서가 실패하는 가장 흔한 방식은 틀린 정보가 아니라 **백엔드 내부 사정으로 문서가 채워지는 것**이다. 소스를 읽으며 쓰기 때문에 자연히 그렇게 흐른다. **FE가 읽고 행동이 바뀌지 않는 정보는 빼거나 결과로 번역한다.**

| 쓰지 않는 것 | 대신 쓰는 것 |
|---|---|
| DTO·클래스·메서드명 (`OrderV3.OrderLine`, `Coupon.empty()`, `resolveLinePrice`) | 응답 JSON에 보이는 필드 경로와 관측 결과 |
| 어노테이션·프레임워크 설정 위치 (`@JsonInclude`가 클래스/필드 어디 붙었는지, `ObjectMapperConfig`, `SecurityConfig`) | "값이 없으면 키가 생략됩니다" / "비로그인도 호출 가능합니다" |
| DB 테이블·컬럼·SQL (`coupon_platform_map`, `use_yn=1 AND start_date <= NOW()`) | 그 필드가 언제 오는지를 FE가 볼 수 있는 말로 |
| 내부 설정 키·i18n 키 (`promo.target.channels`, `l00004`) | 지금 내려가는 값과 그 값의 안정성 (`type`으로 분기, `title`은 변할 수 있음) |
| 유틸·밸리데이터·리포지토리·배치 클래스명 | 입력 → 응답 판정 표 |
| 티켓 진행 상황, 기획 확인 대기, 리뷰 결과, 배포 순서 | (쓰지 않는다 — 규격이 아니다) |

예외는 하나다. **FE의 행동이 그 근거에 달려 있으면** 남긴다. `sort`가 `null`로 내려간다는 사실은 필요하지만, 그게 필드 레벨 `@JsonInclude(ALWAYS)`가 클래스 설정을 덮기 때문이라는 건 필요 없다.

번역 예:

| 소스에서 읽은 것 | 문서에 쓸 것 |
|---|---|
| `selectActiveCouponById`가 null 대신 `Coupon.empty()`를 반환하고 필터가 `items(emptyList())`로 채운다 | 대상이 없어도 `coupon`은 `{"items": []}`로 옵니다. 키 부재로 판정하면 안 됩니다 |
| `SourceUtil.isPartnerOnly`가 `^PARTNER(_.*)?$` strict 매칭 | `source`별 노출 판정 표 (`PARTNER_1` → 나옴 / `NOT_PARTNER` → 안 나옴) |
| `OrderQueryRepository`에 `@Transactional(readOnly)` 보정 | (쓰지 않는다 — 응답에 변화 없음) |

**소스 근거는 엔드포인트 표의 `소스` 컬럼 한 곳에만 둔다.** 본문 산문에 `파일:라인`을 흩뿌리지 않는다.

## When to Use

- 기존 백엔드 코드에서 FE 전달용 API 규격서를 역추출
- Postman 컬렉션·링크 대신 문서로 API를 인계
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
- **대상 티켓** (범위를 티켓으로 한정할 때)
- **내부 API 포함 여부** — admin·batch·actuator 계열 (기본 제외, 제외한 목록은 부록에 남김)

**메타 표에 빈 칸을 만들지 않는다.** base URL, 프론트 티켓, 담당자 같은 항목은 값을 모르면 아예 행을 만들지 않는다. `(TBD)`만 늘어선 표는 규격에 아무것도 더하지 않는다.

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

**헤더는 그 엔드포인트의 동작을 바꾸는 것만 적는다.** 누락 시 에러가 나는 헤더, 응답 내용을 가르는 헤더, 인증 헤더가 그것이다. 모든 요청에 붙는 관용 헤더(`Content-Type`, 추적용 헤더 등)는 적지 않는다.

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

**응답 표는 `필수` 대신 `존재` 컬럼을 쓴다.** 응답에서 `N`은 "요청에서 생략 가능" · "null일 수 있음" · "특정 조건에서만 존재"를 한 글자로 눌러버린다.

| 값 | 의미 |
|---|---|
| `항상` | 어떤 응답에서도 반드시 존재 |
| `조건부: {조건}` | 조건을 그 자리에 그대로 쓴다 |
| `없음` | 스키마에는 있으나 이 엔드포인트·이 타입에서는 절대 안 내려감 |

**부모가 조건부면 자식의 `존재`는 `조건부: {부모} 존재 시`로 적는다.** 부모가 조건부인데 자식만 `항상`으로 적으면 읽는 쪽이 null 체크를 뺀다.

```
| `lowest_price`      | object | 조건부: 최저가 판정 시        |
| `lowest_price.name` | string | 조건부: lowest_price 존재 시 |
```

응답 성격의 표는 **전부** 이 컬럼을 단다. 카드 표에만 달고 상위 래퍼 표에서 빠뜨리면 그 표의 필드는 항상 존재하는 것으로 읽힌다.

**응답 표에 `필수` 컬럼이 남아 있으면 그 표는 다시 쓴다.** 요청 표를 복사해 응답 표를 만들면 반드시 이 실수가 난다. 실제로 나온 오류 셋:

| 잘못 쓴 것 | 실제 | 올바른 표기 |
|---|---|---|
| `sort \| int \| 필수 Y` | 값은 항상 `null`이지만 키는 항상 온다 | `항상` + 설명에 "값은 항상 `null`" |
| `coupon \| object \| 필수 N` | 대상이 없어도 `{"items": []}`로 온다 | `항상` (안 오는 예외 조건을 설명에) |
| `owner_name \| string \| 필수 N` | 특정 타입 카드에만 실린다 | `조건부: type=PARTNER_PICK` |
| `text_color \| string \| 필수 N` | 이 화면의 타입들엔 정의가 없어 절대 안 온다 | `없음` |

`필수 N`은 이 넷을 전부 같은 글자로 눌러버린다. FE는 `N`을 "가끔 없음"으로 읽고, 넷 중 어느 것도 그 뜻이 아니다.

### 2-D-2. 조건은 FE가 관찰할 수 있는 말로 쓴다

`조건부: {조건}`의 조건을 백엔드 판정 로직으로 적으면 FE는 분기 시점을 알 수 없다. "실제 대상자가 있을 때만"은 FE가 확인할 방법이 없는 조건이다.

| 조건의 성격 | 표기 |
|---|---|
| FE가 요청으로 제어 (파라미터·헤더·인증·플랫폼) | 어떤 값일 때 오는지 그대로 — `조건부: source가 PARTNER 계열일 때` |
| 응답의 다른 필드로 판별 가능 | 그 필드를 가리킨다 — `조건부: type=PARTNER_PICK` |
| 서버 내부 판정으로 FE가 예측 불가 | `조건부: 서버 판정 — 키 존재 여부로만 분기` |

요청 값으로 갈리는 조건이 2개 이상이면 **입력 → 응답 판정 표**를 따로 만든다. 산문 세 줄보다 표 한 장이 정확하다.

| `source` | `partner_label` |
|---|---|
| `PARTNER`, `PARTNER_1` | `PARTNER_PICK` |
| `DIRECT`, `NOT_PARTNER` | 없음 |

### 2-D-3. 공유 스키마 hoisting

**2개 이상 엔드포인트가 같은 객체를 반환하면 Step 3 공통 스키마로 올린다.** 엔드포인트 섹션에는 **차이나는 것만** 쓴다.

공통 응답 래퍼(`ApiResponse<T>`, `CommonResponse` 등)도 같은 규칙이다. 래퍼가 있으면 공통 스키마에 한 번만 쓰고, 엔드포인트별 표에는 `data.` 이하만 적는다.

### 2-E. 에러

- Spring: `@ExceptionHandler`/`@ControllerAdvice`, 던지는 커스텀 예외와 ErrorCode enum
- FastAPI: `raise HTTPException(status_code=, detail=)`, exception handler
- Nest/Express: `throw new XxxException()`, 에러 미들웨어

해당 메서드에서 **실제로 던지는 것**만 엔드포인트 표에 적고, 전역 공통 에러는 Step 3으로 뺀다.

## Step 3: 공통 스키마 추출

엔드포인트마다 반복될 **스키마**를 문서 앞쪽에 한 번만 정리한다. 여기 올라가는 것은 다음뿐이다.

- 공통 응답 래퍼 구조와 예시
- 2곳 이상에서 쓰이는 객체의 필드 표 (2-D-3)
- 2개 이상 엔드포인트가 공유하고 **동작을 바꾸는** 헤더 표 (2-A). 한 엔드포인트만 읽는 헤더는 그 엔드포인트 Request 표에 둔다
- 전역 에러 코드 표
- 페이지네이션 규칙 (`page`/`size`/`sort` 기본값, 응답의 총건수 필드)
- 날짜·타임존 포맷

**직렬화 규칙 섹션은 만들지 않는다.** 네이밍 전략은 표의 필드명이 이미 보여주고, null 필드 생략은 `존재` 컬럼과 예시 JSON이 보여준다. 대신 `null`이면 키가 빠지는 API라면 `존재` 컬럼이 `조건부`인 행의 판정을 **키 부재 기준으로 쓴다** (2-D).

## Step 3-B: 도메인 규칙 추출

필드 표로는 표현되지 않지만 FE가 지켜야 하는 규칙을 **한 섹션에 모은다.** 엔드포인트마다 흩뿌리거나 "FE 영향"·"프론트 계약"·"주의"·"구성 규칙" 같은 이름으로 쪼개지 말고, `## 도메인 규칙` 하나에 번호를 매겨 넣는다.

여기에 들어가는 것:

| 종류 | 예 |
|---|---|
| 분기 기준 | 라벨은 `type`으로 분기한다. `title`은 번역값이라 바뀐다 |
| 서버가 계산하지 않는 값 | 카드 최저가는 `rooms[].rates[].price`의 min을 FE가 구한다 |
| 서버가 정하지 않는 것 | 두 라벨이 함께 올 때 표시 순서는 FE가 정한다 |
| 목록의 순서·구성 | `rooms[]`는 `items[]`와 같은 순서. 등록 요금제 ∩ 조회 결과만 남는다 |
| 값의 산출 기준 | 웹은 세금 미포함가, 앱은 세금 포함가 |
| 노출·부재 조건 | 등록 시 웹 노출로 체크된 건만 웹 응답에 나온다. `source`가 `TCELEB*`면 응답이 30초 캐시된다 |
| FE가 만들어야 하는 것 | 스타일·아이콘 에셋, 상태별 표시 문구 |

규칙 하나는 **제목 한 줄 + 본문 최대 2줄**이다. 근거·배경·검증 이야기는 쓰지 않는다. 관련 필드는 백틱으로 가리키고, 필드 표의 `설명`으로 충분한 내용은 규칙으로 올리지 않는다.

## Step 4: 출력 범위 판정 (내부 판단)

엔드포인트별로 **full(전체 명세) / delta(변경분만)** 을 정한다. **이건 작성 분량을 정하는 내부 판단이고, 문서에 "모드"로 표기하지 않는다.** 판정은 자동으로 하고 사용자에게 묻지 않는다.

| 조건 | 범위 |
|---|---|
| 기존 문서가 없음 (첫 생성) | **full** |
| 기존 문서에 없던 엔드포인트 | **full** |
| breaking 신호가 **하나라도** 있음 | **full** |
| 변경된 필드가 그 엔드포인트 전체 필드의 **30% 초과** | **full** |
| 그 외 (non-breaking 소폭 변경) | **delta** |

**breaking 신호** — 하나만 걸려도 full이고 `## 이번 변경` 표의 `Breaking`은 `Y`다:
- 응답 최상위 구조 변경 (래퍼 교체, `data`가 객체↔배열)
- 기존 필드 **삭제** 또는 **이름 변경**
- 타입 변경 (`int` → `string` 등)
- 선택 → 필수 승격
- enum 값 **삭제** (추가는 breaking 아님)
- path·method 변경, 인증/권한 요구 강화

`Breaking`은 이 목록에 **기계적으로** 걸리는지로만 판정한다. "FE가 그 필드를 안 썼으니 괜찮다"는 판단을 섞지 않는다 — 섞으면 삭제 행이 표에 있는데 `Breaking: N`인 자기모순이 난다.

**delta로 남는 대표 케이스**: 선택 필드 추가, enum 값 추가, 설명·예시 보강, 제약 완화, 에러 코드 추가.

**판정 단위**는 엔드포인트다. 단 여러 엔드포인트가 공유하는 객체 하나가 바뀐 경우, 변경 표는 **스키마 단위로 1회만** 쓰고 영향 엔드포인트를 나열한다. 같은 표를 엔드포인트 수만큼 복사하지 않는다.

## Step 5: markdown 출력

기본 경로 `./api-spec.md`. 엔드포인트는 **도메인(컨트롤러) 단위로 그룹**하고 목차를 단다.

**헤딩은 평문으로 쓴다.** 백틱·괄호를 넣으면 앵커가 깨져 목차가 어긋난다. 코드 표기는 헤딩 아래 본문에서 한다.

### 섹션 순서

1. 메타 표 (+ 범위 밖이 있으면 한 줄)
2. `## 이번 변경` (갱신·티켓 한정 문서일 때만)
3. 목차 → `## 도메인 규칙` → `## 공통 스키마` → `## 엔드포인트`
4. `## 변경 이력` / 부록

**문서 관리 사정은 4번에만 쓴다.** 재발행 사유, 판정 근거, "이전 발행분은 그대로입니다", "기능 변경이 아니라 문서 정정입니다" 같은 문장은 상단에 두지 않는다.

```markdown
# {프로젝트명} API 명세서

| 항목 | 내용 |
|---|---|
| 작성일 | {YYYY-MM-DD} |
| 작성자 | {작성자} |
| 대상 티켓 | {티켓} |
| 엔드포인트 수 | {N} |

> **범위** — {무엇만 다루는지 / 무엇이 범위 밖인지} 한 줄.

## 이번 변경

| 엔드포인트 | 변경 | Breaking |
|---|---|---|
| `POST /api/v1/orders` | `memo` 추가, `status`에 `CANCELED` 추가 | N |
| `GET /api/v1/orders` | `legacyFlag` 삭제 | Y |

| 구분 | 위치 | 필드 | 변경 전 | 변경 후 |
|---|---|---|---|---|
| 추가 | body | `memo` | - | string / 선택 / 최대 200자 |
| 변경 | response | `data.status` | `PENDING \| PAID` | `PENDING \| PAID \| CANCELED` |
| 삭제 | response | `data.legacyFlag` | boolean | **없음** |

## 목차
- [도메인 규칙](#도메인-규칙)
- [공통 스키마](#공통-스키마)
- [주문](#주문)
  - [POST /api/v1/orders — 주문 생성](#post-apiv1orders--주문-생성)

## 도메인 규칙

**① 주문 상태 분기는 `status`로 합니다**
`statusText`는 로케일에 따라 바뀝니다. 상태별 표시 문구는 서버가 내려주지 않으므로 FE가 매핑합니다.

**② 쿠폰 적용 여부는 `coupon.items`가 비었는지로 판정합니다**
대상이 없어도 `coupon` 키는 옵니다. 키 존재로 판정하면 모든 주문이 쿠폰 주문이 됩니다.

## 공통 스키마

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

주문을 생성하고 결제 대기 상태로 만듭니다.

| 인증 | 권한 | 상태 | 소스 |
|---|---|---|---|
| 필요 | MEMBER | 정상 | `OrderController.kt#create:42` |

#### Request

| 위치 | 필드 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| query | `dry_run` | boolean | N | false | 검증만 수행 |
| body | `items[].product_id` | string | Y | - | 상품 ID |
| body | `items[].qty` | int | Y | - | 1~99 |
| body | `memo` | string | N | - | 최대 200자 |
| header | `Accept-Language` | string | Y | - | 없으면 400 |

```json
{ "items": [{ "product_id": "P-001", "qty": 2 }], "memo": null }
```

```bash
curl -X POST '{base}/api/v1/orders' \
  -H 'Content-Type: application/json' -H 'Accept-Language: ko' \
  -d '{"items":[{"product_id":"P-001","qty":2}]}'
```

#### Response 200

| 필드 | 타입 | 존재 | 설명 |
|---|---|---|---|
| `data.order_id` | string | 항상 | 주문 번호 |
| `data.status` | enum | 항상 | `PENDING` \| `PAID` \| `CANCELED` |
| `data.items[].qty` | int | 항상 | 수량 |
| `data.coupon` | object | 항상 | 대상이 없으면 `{"items": []}` |
| `data.coupon.items[].code` | string | 조건부: `coupon.items` 원소가 있을 때 | 쿠폰 코드 |
| `data.status_text` | string | 없음 | 서버가 내려주지 않습니다 |

```json
{ "code": "SUCCESS", "data": { "order_id": "ORD-001", "status": "PENDING", "items": [{ "qty": 2 }], "coupon": { "items": [] } } }
```

#### Errors

| HTTP | code | 조건 |
|---|---|---|
| 400 | INVALID_QTY | `qty`가 1~99 범위 밖 |
| 409 | OUT_OF_STOCK | 재고 부족 |
```

필수 헤더가 2개 이상이거나 누락 시 에러가 나면 Request 표 아래에 `curl` 한 줄을 붙인다. 표만 보고 헤더를 빼면 FE는 그 에러가 자기 실수인지 서버 문제인지 모른다.

### delta 블럭 (소폭 변경)

full 섹션을 다시 쓰지 않고 **바뀐 것만** 적는다. 기존 문서의 해당 엔드포인트 섹션은 실제 값으로 갱신하고, 전달용으로는 이 블럭을 뽑아준다.

```markdown
### POST /api/v1/orders 주문 생성 — 변경분

| 구분 | 위치 | 필드 | 변경 전 | 변경 후 |
|---|---|---|---|---|
| 추가 | body | `memo` | - | string / 선택 / 최대 200자 |
| 변경 | response | `data.status` | `PENDING \| PAID` | `PENDING \| PAID \| CANCELED` |
| 추가 | error | 409 OUT_OF_STOCK | - | 재고 부족 시 |

```json
{ "memo": "선물포장", "items": [{ "product_id": "P-001", "qty": 99 }] }
```
```

규칙:
- 표에는 **바뀐 행만** 넣는다. 안 바뀐 필드는 쓰지 않는다.
- `변경 전` 값은 기존 문서에서 읽는다. 확인 불가면 `(TBD)`.
- 예시 JSON은 **변경된 필드가 드러나는 부분만**. 전체 payload를 다시 붙이지 않는다.
- FE가 코드를 고쳐야 하는 변경이면 그 규칙을 `## 도메인 규칙`에 넣고, 여기서는 표만 남긴다.

### full 재발행

Step 4에서 full로 판정되면 엔드포인트 섹션 전체를 다시 발행한다. 신규와 같은 템플릿(Request 표 / 예시 / Response 표 / 예시 / Errors)을 그대로 쓴다. 사유는 `## 변경 이력` 행에만 적는다.

### 문서 끝

- `## 변경 이력` — 날짜 / 변경 내용 / 영향받는 FE 화면 (첫 생성 시 최초 행만)
- `## 부록 — 제외된 엔드포인트` — Step 0에서 제외한 목록 (있을 때만)

### 예시 JSON 생성 규칙

- 표의 타입·제약과 **모순되지 않는 값**만 쓴다
- enum은 첫 번째 값
- 실제 운영 데이터·사번·회사 식별자·토큰은 절대 넣지 않는다. 전부 `P-001`, `ORD-001` 같은 중립 더미
- **실제 상호·상품명·사람 이름·닉네임·운영 ID를 그대로 복사하지 않는다.** 로컬에서 실측한 응답을 붙일 때 가장 새기 쉽다
- 실측 비교표가 필요하면 **숫자는 남기고 식별자만 더미로 바꾼다** (`상품 90114327` → `상품 P-001`)

#### null / 생략

- `null`이면 키가 빠지는 API면 선택 필드를 **키째 뺀다**. `null`을 적으면 실제로 오지 않는 모양의 예시가 된다
- 그렇지 않으면 선택 필드를 `null`로 남겨 구분이 예시에서도 드러나게 한다
- 어느 쪽이든 진짜 근거는 표의 `존재` 컬럼이다. 예시는 보조다

#### 분량 — 전량이 아니라 전 분기

응답이 수백~수천 행이 될 수 있으므로 통째로 붙이지 않는다. **모든 분기가 한 번씩 드러나는 최소 예시**를 만든다.

- 배열은 **대표 원소 2개까지** — 서로 다른 분기를 보여주는 것으로 고른다. 같은 모양을 두 번 넣지 않는다
- 나머지는 `// ... 동일 구조 N건 생략` 마커. **생략했다는 사실을 반드시 남긴다**
- 반복 없이 필드가 많아 긴 경우엔 최상위 + 대표 서브트리 1개만 펼치고 나머지는 표에만 둔다
- 빈 상태(`items: []`)처럼 구조가 달라지는 케이스는 **별도 짧은 예시**로 붙인다
- 엔드포인트 하나당 예시는 **3개까지**. 그 이상 필요하다고 느끼면 분기를 표로 옮긴다

## 마커 표기 규칙

작업 중 사용자에게 묻지 않고, 애매한 케이스를 결과물에 보존한다.

| 마커 | 의미 |
|---|---|
| `(TBD)` | 소스에 정보가 없음. 사용자가 채워야 함 |
| `⚠️ 추론` | 소스에서 직접 못 읽고 이름·관례로 유추한 값 |
| `🚧 미구현` | 스텁·TODO·FIXME가 달린 엔드포인트 |
| `⛔ depth 제한` | 평탄화 depth 4 초과로 중단 |
| `⛔ 순환 참조` | DTO 순환 참조로 중단 |
| `🗑 deprecated` | `@Deprecated` 표시된 엔드포인트 |

## 갱신 모드

출력 경로에 이미 문서가 있으면 **문서 전체를 재생성하지 않는다.**

1. 기존 문서의 엔드포인트 목록과 소스 추출 목록을 비교
2. 엔드포인트별로 Step 4 규칙에 따라 full / delta를 판정
3. **변경 없는 엔드포인트는 손대지 않는다** — 문장을 다시 쓰지도 않는다
4. 사람이 손으로 채운 내용(`(TBD)`를 채운 설명, 비고)은 **덮어쓰지 않는다**
5. 소스에서 사라진 엔드포인트는 지우지 말고 `🗑 deprecated` + 삭제 예정 표기로 남긴다
6. `## 이번 변경` 표를 새로 쓰고 `## 변경 이력`에 행을 추가

## 검증

문서를 쓴 뒤 스스로 확인한다.

분량 (먼저 본다):

- 엔드포인트 블럭에 `Request 표` / 예시 / `Response 표` / 예시 / `Errors` 밖의 섹션이 붙어 있지 않은가
- 엔드포인트 블럭의 표 밖 산문이 2줄을 넘지 않는가. 인용 블럭(`>`)이 늘어서 있지 않은가
- FE가 지켜야 할 규칙이 `## 도메인 규칙` 한 곳에 모여 있는가. "FE 영향"·"주의"·"계약"·"구성 규칙" 같은 이름으로 흩어져 있지 않은가
- 메타 표에 값 없는 행(`(TBD)`만 있는 행)이 있지 않은가
- 직렬화 규칙 섹션을 만들지 않았는가
- 문서에 "모드"·"신규"·"full 재발행" 같은 발행 상태 표기가 남아 있지 않은가

FE 관점:

- **응답 성격의 표에 `필수` 컬럼이 남아 있지 않은가** — 하나라도 있으면 그 표는 다시 쓴다 (2-D)
- 클래스·메서드·어노테이션·테이블·SQL·설정 키·i18n 키가 본문에 남아 있지 않은가. 남겼다면 그것 때문에 **FE의 행동이 바뀌는가** (아니면 지운다)
- 티켓 진행 상황·기획 확인 대기·검증 서사가 섞여 있지 않은가
- `조건부`의 조건이 FE가 관찰할 수 없는 백엔드 판정 서술("실제 X가 있을 때만")로 적혀 있지 않은가
- `파일:라인`이 엔드포인트 표의 `소스` 컬럼 밖에 흩어져 있지 않은가
- 그 엔드포인트가 읽지 않는 헤더를 Request 표에 적지 않았는가
- 예시에 실제 상호·상품명·사람 이름·닉네임·운영 ID가 남아 있지 않은가

정확성:

- 목차의 앵커가 실제 섹션과 전부 맞는가 (헤딩에 백틱·괄호를 넣지 않았는가)
- 표에 있는 필드가 예시 JSON과 서로 모순되지 않는가
- enum 값을 나열하지 않고 `enum`으로만 둔 행이 없는가
- 소스에 없는 필드를 만들어 넣지 않았는가

`존재` 컬럼:

- **응답 성격의 표에 `존재` 컬럼이 빠진 것이 없는가** — 하위 표에만 달고 상위 래퍼 표에서 빠뜨리기 쉽다
- `조건부`인데 조건을 안 적고 `조건부`로만 둔 행이 없는가
- 부모가 `조건부`인데 자식이 `항상`으로 적힌 행이 없는가
- 산문에만 있고 표에는 안 들어간 존재 조건이 없는가 (표만 읽어도 같은 결론이 나와야 한다)

예시 JSON:

- 키 생략형 API인데 예시에 `null`을 적지 않았는가 (반대도 마찬가지)
- 배열을 통째로 붙이지 않았는가. 생략한 곳에 생략 마커가 있는가
- 엔드포인트당 예시가 3개를 넘지 않는가

갱신 모드일 때 추가로:

- delta 판정한 엔드포인트에 breaking 신호가 실제로 하나도 없는가 (있으면 full로 올린다)
- **변경 표에 `삭제` 행이 있는데 `Breaking: N`으로 적히지 않았는가** — 삭제는 무조건 Y다
- delta 표에 **안 바뀐 행**이 섞이지 않았는가
- 공유 객체 변경인데 같은 변경 표를 엔드포인트마다 복사하지 않았는가
- 변경 없는 엔드포인트 섹션이 불필요하게 다시 쓰이지 않았는가 (git diff로 확인)
