---
name: node-backend-patterns
description: >
  Use when writing, reviewing, or refactoring Node.js backend code in Express,
  Next.js API routes, or NestJS. Do NOT use for REST contract design alone.
---

# Node 백엔드 규칙

일반 패턴(Repository, 캐싱, JWT, 재시도 등)은 모델이 이미 안다. 아래는 고정해 둔 선택과 자주 틀리는 지점만 적는다. 프로젝트 규칙과 기존 코드 관례가 다르면 프로젝트 쪽을 따른다.

## 공통

- 레이어를 나눈다: Controller(HTTP 변환만) → Service(비즈니스 로직) → Repository(데이터 접근). 컨트롤러에 비즈니스 로직을, 서비스에 ORM 호출을 두지 않는다.
- 쿼리는 필요한 컬럼만 고른다(`select *` 금지). 루프 안에서 쿼리하지 말고 배치 조회한다(N+1).
- 여러 엔티티를 바꾸는 작업은 트랜잭션으로 묶는다.
- 목록 조회는 항상 페이지네이션한다. `findAll()` 전체 조회 금지.
- 5xx 응답에 내부 에러 메시지·스택을 노출하지 않는다. 에러 형태는 전역 핸들러/필터 한 곳에서 만든다.
- 포트·시크릿을 하드코딩하지 않는다. `as any`로 타입을 우회하지 않는다.
- 로그는 JSON 구조화 로그로 쓰고, 요청마다 `requestId`를 싣는다.

## NestJS

- 모듈 단위로 관련 파일(controller, service, repository, dto, entity, test)을 함께 둔다.
- 입력은 `class-validator` + `ValidationPipe`로 검증하고 Swagger 데코레이터를 함께 선언한다.
- 환경 변수는 `ConfigModule` + `Joi` 스키마로 관리한다.
- 인증·인가는 Guard + 커스텀 데코레이터로 처리한다. 컨트롤러·서비스에 넣지 않는다.
- 내장 예외와 전역 Exception Filter로 응답 포맷을 통일한다.
- `enableCors()`를 인자 없이 호출하지 않는다. origin whitelist를 지정한다.
