---
name: fastapi-guide
description: >
  Use when writing, reviewing, or refactoring FastAPI code: routers, Pydantic
  models, dependencies, DB sessions, async/sync behavior, middleware, deployment.
---

# FastAPI 규칙

FastAPI의 일반 사용법은 모델이 이미 안다. 아래는 실수하기 쉬운 지점과 고정해 둔 선택만 적는다. 프로젝트 규칙과 기존 코드 관례가 이 문서와 다르면 프로젝트 쪽을 따른다.

## Async

- `async def` 안에서 블로킹 호출을 하지 않는다. 이벤트 루프 전체가 멈춘다. 블로킹이 필요하면 `def`로 선언하거나 `run_in_threadpool`을 쓴다.
- 대체: `time.sleep`→`asyncio.sleep`, `requests`→`httpx`, `psycopg2`→`asyncpg`, `Session`→`AsyncSession`.
- 의존성은 `async def`를 선호한다. sync 의존성은 불필요하게 스레드를 쓴다.

## 구조

- 파일 유형별이 아니라 **도메인별**로 나눈다(`src/auth/`, `src/posts/`). 도메인마다 `router.py`·`schemas.py`·`service.py`·`dependencies.py`·`exceptions.py`.

## 의존성·Pydantic

- 반복되는 인증·DB 세션·리소스 존재 검증은 `Depends()`로 뽑는다(`get_or_404`).
- `response_model`을 항상 지정한다. Input/Output 스키마를 분리한다(`UserCreate` / `UserResponse`).
- 직접 `if`로 검증하지 않고 `Field()`·`field_validator`·`EmailStr`을 쓴다. 공통 설정은 `CustomBase(BaseModel)`에 모은다.

## DB

- 엔드포인트에서 `SessionLocal()`을 직접 만들지 않는다. `Depends(get_db)` + `yield`.
- 시작/종료 리소스는 `lifespan`으로 관리한다.

## 보안·배포

- 프로덕션은 `docs_url`·`redoc_url`·`openapi_url`을 `None`으로 둔다.
- 시크릿은 코드에 두지 않고 `pydantic_settings.BaseSettings` + `.env`로 읽는다.
- 예외 핸들러는 `APIRouter`가 아니라 `FastAPI` 인스턴스에 등록한다.
- `/health` 엔드포인트를 둔다. 컨테이너는 비루트 사용자로 실행한다.
- 비동기 테스트는 `httpx` + `ASGITransport`.
