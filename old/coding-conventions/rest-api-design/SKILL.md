---
name: rest-api-design
description: >
  Use when designing or reviewing REST API contracts: endpoint URLs, methods,
  status codes, error shapes, pagination, filtering, versioning. Do NOT use for
  backend implementation patterns alone.
---

# REST API 설계 규칙

HTTP 메서드·상태 코드의 일반 의미는 모델이 이미 안다. 아래는 고정해 둔 선택만 적는다. 프로젝트에 이미 정해진 API 관례가 있으면 그것을 따른다.

## URL

- 리소스는 명사·복수형·소문자 kebab-case다(`/api/v1/team-members`). URL에 동사를 넣지 않는다.
- CRUD에 안 맞는 동작만 하위 동사를 허용한다(`POST /orders/:id/cancel`).
- 필터는 쿼리 파라미터, 소유 관계는 중첩 경로(`/users/:id/orders`).

## 응답

- HTTP 상태 코드를 의미에 맞게 쓴다. 모든 응답을 200으로 내려 본문에 `success: false`를 싣지 않는다.
- 생성은 `201` + `Location` 헤더. 본문 없는 성공은 `204`. 검증 실패는 필드 단위 상세와 함께 `400`/`422`.
- 성공은 `{ "data": ... }`, 목록은 `meta`(페이지 정보)·`links`를 더한다.
- 에러는 `{ "error": { "code", "message", "details": [{ "field", "message", "code" }] } }`. `code`는 기계가 읽는 값이다.

## 페이지네이션·정렬

- 소규모·관리자·검색 결과는 오프셋(`page`, `per_page`), 피드·대용량·공개 API는 커서가 기본이다. 커서는 불투명 값이고 `limit+1`건을 읽어 다음 페이지 여부를 판단한다.
- 정렬은 `sort=-created_at,price`(`-`는 내림차순). 범위 필터는 `price[gte]=10`.

## 버전

- 경로 버전(`/api/v1`)을 쓰고, 필요해지기 전에는 올리지 않는다. 활성 버전은 최대 2개.
- 필드·엔드포인트 추가는 non-breaking이다. 필드 삭제·이름/타입 변경·URL 구조·인증 방식 변경은 새 버전이 필요하다.
- 폐기는 예고 → `Sunset` 헤더 → 일몰 후 `410 Gone` 순서로 한다.

## 배포 전 확인

- 입력을 스키마로 검증하는가, 인증과 소유권 인가를 확인했는가, 속도 제한이 있는가
- 응답에 스택 트레이스·SQL 에러가 새지 않는가, OpenAPI 스펙을 갱신했는가
