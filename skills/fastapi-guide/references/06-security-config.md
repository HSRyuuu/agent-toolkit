# 보안 & 설정 관리

## 1. API 문서 프로덕션 비공개

```python
import os
from fastapi import FastAPI

app = FastAPI(
    docs_url="/docs" if os.getenv("ENV") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENV") == "development" else None,
    openapi_url="/openapi.json" if os.getenv("ENV") == "development" else None
)
```

## 2. 시크릿 관리 — pydantic-settings

### ❌ 절대 하지 말 것
```python
DATABASE_URL = "postgresql://admin:password123@localhost/db"
SECRET_KEY = "super-secret-key"
```

### ✅ 도메인별 Settings 분리
```python
from pydantic_settings import BaseSettings

class AuthConfig(BaseSettings):
    JWT_ALG: str = "HS256"
    JWT_SECRET: str
    JWT_EXP: int = 5  # minutes
    ACCESS_TOKEN_EXP: int = 30

    class Config:
        env_file = ".env"

class DatabaseConfig(BaseSettings):
    DB_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    class Config:
        env_file = ".env"

auth_config = AuthConfig()
db_config = DatabaseConfig()
```

`.env` 파일:
```
JWT_SECRET=your-256-bit-secret
DB_URL=postgresql+asyncpg://user:pass@localhost/db
```

## 3. 커스텀 예외 처리

### 도메인 예외 클래스 정의
```python
# src/posts/exceptions.py
from fastapi import HTTPException

class PostNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Post not found")

class NotAuthorized(HTTPException):
    def __init__(self):
        super().__init__(status_code=403, detail="Not authorized")
```

### 전역 예외 핸들러 (main.py에 등록)
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

# ⚠️ 예외 핸들러는 APIRouter가 아닌 FastAPI 인스턴스에만 등록 가능
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation failed", "details": exc.errors()}
    )
```

**중요:** 예외 핸들러는 `APIRouter`가 아닌 `FastAPI` 앱 인스턴스에만 등록할 수 있다.

## 4. 미들웨어 패턴

```python
import time
from fastapi import Request

# 요청 처리 시간 로깅
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 레이트 리미팅 — slowapi (토큰 버킷 알고리즘 + Redis 백엔드)
# pip install slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",  # 멀티워커 환경에서도 동작
)
app.state.limiter = limiter

@app.get("/api/resource")
@limiter.limit("100/minute")
async def get_resource(request: Request):
    return {"data": "ok"}
```

**미들웨어 사용 시나리오:**
- 요청/응답 로깅
- CORS 헤더 추가
- 요청 처리 시간 측정
- 레이트 리미팅
- 공통 인증 (단, 라우터 레벨 `Depends`가 더 선호됨)

## 5. CORS 설정

```python
from fastapi.middleware.cors import CORSMiddleware

# ❌ 절대 금지 — 모든 출처 허용
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# ✅ 화이트리스트 방식
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com", "https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**규칙:**
- `allow_origins=["*"]`는 개발 환경에서만 허용, 프로덕션에서는 반드시 도메인 화이트리스트 사용
- `allow_credentials=True` 사용 시 `allow_origins=["*"]`는 불가 (브라우저가 거부)
- 필요한 메서드와 헤더만 명시적으로 허용
