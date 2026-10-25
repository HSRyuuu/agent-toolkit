# 의존성 주입 (Depends) 패턴

## 1. 기본 패턴: 중복 제거

### ❌ 잘못된 예 — 중복 인증
```python
@app.get("/users/{user_id}")
async def get_user(user_id: int, token: str):
    if not validate_token(token):
        raise HTTPException(401, "Invalid token")
    ...

@app.get("/posts/{post_id}")
async def get_post(post_id: int, token: str):
    if not validate_token(token):  # 중복!
        raise HTTPException(401, "Invalid token")
    ...
```

### ✅ 올바른 예 — Depends()로 추출
```python
from fastapi import Depends, Header, HTTPException

async def verify_token(token: str = Header(...)):
    if not validate_token(token):
        raise HTTPException(401, "Invalid token")
    return token

@app.get("/users/{user_id}")
async def get_user(user_id: int, token: str = Depends(verify_token)):
    return get_user_from_db(user_id)
```

## 2. DB 검증 의존성 패턴 (get_or_404)

리소스 존재 검증을 의존성으로 만들어 재사용하라:
```python
from uuid import UUID

async def get_post_or_404(
    post_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Post:
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    return post

@app.get("/posts/{post_id}")
async def get_post(post: Post = Depends(get_post_or_404)):
    return post  # 이미 검증 완료

@app.put("/posts/{post_id}")
async def update_post(
    post: Post = Depends(get_post_or_404),
    data: PostUpdate = ...,
):
    return await update(post, data)  # 중복 검증 불필요
```

## 3. 의존성 체이닝

의존성이 다른 의존성에 의존할 수 있다:
```python
async def valid_profile_id(profile_id: UUID) -> Profile:
    profile = await service.get_profile(profile_id)
    if not profile:
        raise ProfileNotFound()
    return profile

async def valid_creator_id(
    profile: Profile = Depends(valid_profile_id)
) -> Profile:
    if not profile.is_creator:
        raise NotACreator()
    return profile

# 체이닝 사용
@app.get("/creator/{profile_id}/posts")
async def creator_posts(creator: Profile = Depends(valid_creator_id)):
    return await service.get_creator_posts(creator.id)
```

## 4. 의존성 캐싱

FastAPI는 **같은 요청 스코프 내**에서 동일 의존성 결과를 캐시한다. 여러 엔드포인트에서 같은 의존성을 호출해도 한 번만 실행된다.

```python
# get_current_user가 한 요청에서 여러 번 호출돼도 DB 쿼리는 1번만
@app.get("/profile")
async def get_profile(
    user: User = Depends(get_current_user),
    permissions: list = Depends(get_user_permissions),  # 내부에서도 get_current_user 사용
):
    ...
```

**설계 원칙:** 작고 집중된 의존성을 만들어 재사용하라.

## 5. async 의존성 선호

가벼운 의존성도 `async def`로 작성하라. `def` 의존성은 스레드 풀에서 실행되므로, I/O가 없는 경량 작업에서는 불필요한 컨텍스트 스위칭이 발생한다:
```python
# ✅ 권장 — 이벤트 루프에서 직접 실행 (await 없는 경량 작업도 async 선호)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    return decode_token(token)  # 동기 함수 호출이지만 async def 안에서 즉시 반환

# ⚠️ def → threadpool 경유 (컨텍스트 스위칭 오버헤드)
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    return decode_token(token)
```

**핵심:** `async def` 안에서 `await`가 없어도 괜찮다. FastAPI는 `async def`를 이벤트 루프에서 직접 실행하고, `def`는 스레드 풀로 보낸다. 블로킹 I/O가 없는 경량 작업이라면 `async def`가 더 효율적이다.

## 6. 도메인별 Settings 분리

단일 거대 설정 클래스 대신 도메인별로 분리하라:
```python
# ❌ 하나의 거대한 Settings
class Settings(BaseSettings):
    db_url: str
    jwt_secret: str
    redis_url: str
    smtp_host: str
    ...

# ✅ 도메인별 분리
class AuthConfig(BaseSettings):
    JWT_ALG: str = "HS256"
    JWT_SECRET: str
    JWT_EXP: int = 5  # minutes

    class Config:
        env_file = ".env"

class DatabaseConfig(BaseSettings):
    DB_URL: str
    DB_POOL_SIZE: int = 10

auth_config = AuthConfig()
db_config = DatabaseConfig()
```
