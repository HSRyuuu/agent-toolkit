# 프로젝트 구조 & APIRouter

## 1. 도메인 기반 구조 (권장)

파일 유형(crud, routers, models)이 아닌 **도메인/기능** 단위로 구성하라.

### ✅ 권장 구조
```
src/
├── main.py
├── auth/
│   ├── router.py       # 라우트 정의
│   ├── schemas.py      # Pydantic 모델
│   ├── models.py       # DB 모델
│   ├── service.py      # 비즈니스 로직
│   ├── dependencies.py # 의존성
│   ├── constants.py
│   ├── exceptions.py   # 도메인 예외
│   └── utils.py
├── posts/
│   ├── router.py
│   ├── schemas.py
│   └── ...
└── users/
    └── ...
```

### ❌ 피해야 할 구조
```
# 파일 유형 기반 — 규모 커지면 관리 어려움
routers/
models/
schemas/
crud/
```

**크로스 패키지 임포트는 명시적 모듈명 사용:**
```python
from src.auth import constants as auth_constants  # ✅
from ..auth.constants import ...                   # ❌ 상대경로 지양
```

## 2. APIRouter 패턴

`APIRouter`로 라우트를 도메인별로 분리하라.

### router.py (각 도메인)
```python
from fastapi import APIRouter, Depends
from . import schemas, service
from .dependencies import get_current_user

router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
    dependencies=[Depends(get_current_user)],  # 라우터 전체에 인증 적용
)

@router.get("/", response_model=list[schemas.PostResponse])
async def list_posts():
    return await service.get_all()

@router.post("/", response_model=schemas.PostResponse, status_code=201)
async def create_post(data: schemas.PostCreate):
    return await service.create(data)
```

### main.py
```python
from fastapi import FastAPI
from src.posts.router import router as posts_router
from src.auth.router import router as auth_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(posts_router)
```

### 보호된 라우터 vs 공개 라우터 분리
```python
# 인증 필요한 라우터
protected_router = APIRouter(dependencies=[Depends(verify_token)])

# 공개 라우터
public_router = APIRouter()

app.include_router(protected_router, prefix="/api/v1")
app.include_router(public_router)
```

## 3. API 버저닝

```python
from fastapi import FastAPI
from src.v1 import router as v1_router
from src.v2 import router as v2_router

app = FastAPI()
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")
```

**또는 별도 앱 마운트:**
```python
from fastapi import FastAPI
from fastapi.routing import APIRouter

app = FastAPI()
v1 = FastAPI(title="API v1")
v2 = FastAPI(title="API v2")

app.mount("/api/v1", v1)
app.mount("/api/v2", v2)
```

## 4. 엔드포인트 문서화

라우트에 메타데이터를 항상 추가하라:
```python
@router.get(
    "/{post_id}",
    response_model=schemas.PostResponse,
    status_code=200,
    summary="Get a post by ID",
    description="Retrieve a single post. Returns 404 if not found.",
    responses={
        404: {"description": "Post not found"},
        403: {"description": "Not authorized"},
    },
    tags=["Posts"],
)
async def get_post(post: Post = Depends(get_post_or_404)):
    return post
```
