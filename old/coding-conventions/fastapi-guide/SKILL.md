---
name: fastapi-guide
description: >
  Use when writing, reviewing, or refactoring FastAPI code, APIs, routers,
  Pydantic models, dependencies, auth, DB sessions, async/sync behavior,
  middleware, exceptions, BackgroundTasks, deployment, or project structure.
  Triggers: "FastAPI 코드 리뷰", "APIRouter", "async vs sync", "Pydantic 모델",
  "FastAPI 엔드포인트", "FastAPI 프로젝트 구조".
---

# FastAPI Best Practices

프로덕션 수준의 FastAPI 애플리케이션 작성을 위한 핵심 규칙 모음.

## References 가이드 (주제별 상세 예제)

| 파일 | 내용 |
|---|---|
| [01-async-patterns.md](references/01-async-patterns.md) | async/sync 선택, 블로킹 대체 목록, BackgroundTasks, Celery, run_in_threadpool |
| [02-project-structure.md](references/02-project-structure.md) | 도메인 기반 구조, APIRouter, prefix/tags, API 버저닝, 엔드포인트 문서화 |
| [03-dependency-injection.md](references/03-dependency-injection.md) | Depends() 패턴, get_or_404, 체이닝, 캐싱, 도메인별 Settings |
| [04-pydantic-models.md](references/04-pydantic-models.md) | CustomBase, response_model, Field/validator, Input/Output 분리 |
| [05-database.md](references/05-database.md) | 커넥션 풀링, lifespan, DB 네이밍, Alembic, SQL 우선 철학 |
| [06-security-config.md](references/06-security-config.md) | API 문서 비공개, pydantic-settings, 예외 핸들러, 미들웨어 |
| [07-production-deployment.md](references/07-production-deployment.md) | Gunicorn, 헬스체크, structlog, Dockerfile, 비동기 테스트, Ruff |

## 핵심 규칙 요약

### Async 사용 규칙 (가장 중요)

| 코드 유형 | 사용 상황 | 성능 |
|---|---|---|
| `async def` + `await` | 비동기 I/O (DB, 외부 API 호출) | 최고 |
| `def` (동기) | 블로킹 I/O, CPU 집약 작업 | 양호 |
| `async def` + 블로킹 코드 | **절대 금지** — 이벤트 루프 전체 정지 | 최악 |

블로킹 → 논블로킹: `time.sleep()→asyncio.sleep()`, `requests→httpx`, `psycopg2→asyncpg`, `Session→AsyncSession`

### 프로젝트 구조
- **도메인 기반** 구성: `src/auth/`, `src/posts/` (파일 유형 기반 금지)
- 각 도메인에 `router.py`, `schemas.py`, `service.py`, `dependencies.py`, `exceptions.py`
- `APIRouter(prefix="/posts", tags=["Posts"])`로 라우트 분리

### 의존성 주입
- 반복 로직은 `Depends()`로 추출 — 인증, DB 세션, 리소스 존재 검증
- `get_or_404` 패턴으로 엔드포인트 간 검증 재사용
- 의존성은 `async def` 선호 (sync는 불필요한 스레드 사용)

### Pydantic
- `CustomBase(BaseModel)`로 공통 설정 중앙화
- `response_model` 파라미터 항상 지정
- Input/Output 스키마 분리 (`UserCreate` vs `UserResponse`)
- 직접 if 검증 금지 → `Field()`, `field_validator`, `EmailStr` 사용

### DB
- 엔드포인트에서 `SessionLocal()` 직접 생성 금지 → `Depends(get_db)` + `yield`
- 비동기 DB: `AsyncSession` + `create_async_engine` 사용 권장
- `pool_size=10, max_overflow=20, pool_pre_ping=True` 설정
- `lifespan`으로 앱 시작/종료 시 리소스 관리

### 보안
- 프로덕션: `docs_url=None`, `redoc_url=None`, `openapi_url=None`
- 시크릿 하드코딩 금지 → `pydantic_settings.BaseSettings` + `.env`
- 예외 핸들러는 `APIRouter`가 아닌 `FastAPI` 인스턴스에 등록

### 배포
```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
- `/health` 헬스체크 엔드포인트 필수
- `structlog`으로 JSON 구조화 로깅
- Docker: 비루트 사용자(`appuser`) 실행
- 테스트: `httpx + ASGITransport` 비동기 클라이언트 사용
