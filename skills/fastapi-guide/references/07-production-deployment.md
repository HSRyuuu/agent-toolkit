# 프로덕션 배포 & 운영

## 1. Gunicorn + Uvicorn 워커

```bash
# ❌ 개발 전용
uvicorn main:app --reload

# ✅ 프로덕션
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

**워커 수 공식:** `2 * CPU 코어 수 + 1`

## 2. 헬스체크 엔드포인트

```python
from sqlalchemy import text
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse

@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db), request: Request = None):
    try:
        await db.execute(text("SELECT 1"))
        await request.app.state.redis.ping()
        return {
            "status": "healthy",
            "database": "ok",
            "redis": "ok",
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy"},
        )
```

## 3. 구조화 로깅

```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    log = logger.bind(user_id=user_id, endpoint="get_user")
    log.info("fetching_user")
    user = get_user_from_db(user_id)
    log.info("user_found", username=user.name)
    return user

# 출력:
# {"event": "fetching_user", "user_id": 123, "timestamp": "2024-01-01T10:00:00", "level": "info"}
```

## 4. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 비루트 사용자로 실행 (보안)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120"]
```

## 5. 테스트 & 린팅

### 비동기 테스트 클라이언트
프로젝트 초기부터 비동기 테스트 클라이언트를 설정하라 (이벤트 루프 충돌 방지):
```python
# conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

# test_users.py
@pytest.mark.asyncio
async def test_get_user(client):
    response = await client.get("/users/1")
    assert response.status_code == 200
```

### Ruff 린터 (black + isort + autoflake 대체)
```bash
# 설치
pip install ruff

# 실행
ruff check --fix src && ruff format src
```

`pyproject.toml`:
```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]
```

pre-commit hook에 통합하면 자동으로 검사된다.
