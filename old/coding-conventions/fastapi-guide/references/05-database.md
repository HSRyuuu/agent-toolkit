# 데이터베이스 패턴

## 1. 커넥션 풀링 + 의존성 주입

### ❌ 잘못된 예 — 매 요청마다 새 커넥션
```python
@app.get("/users")
async def get_users():
    db = SessionLocal()  # 매번 새 커넥션 생성!
    users = db.query(User).all()
    db.close()
    return users
```

### ✅ 올바른 예 — 동기 풀 + yield 패턴
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine(
    DATABASE_URL,
    pool_size=10,        # 유지할 커넥션 수
    max_overflow=20,     # 추가 허용 커넥션
    pool_pre_ping=True,  # 사용 전 연결 상태 확인
    pool_recycle=3600    # 1시간마다 재활용
)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # 풀에 반환 (실제 연결 종료 아님)

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

### ✅ 비동기 풀 + yield 패턴 (권장)
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

async_engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

## 2. Lifespan 리소스 관리

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import redis.asyncio as redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 초기화
    app.state.redis = await redis.from_url("redis://localhost")
    app.state.db_engine = create_async_engine(DATABASE_URL)

    yield  # 앱 실행

    # 종료 시 정리
    await app.state.redis.close()
    await app.state.db_engine.dispose()

app = FastAPI(lifespan=lifespan)

@app.get("/cached/{key}")
async def get_cached(key: str, request: Request):
    value = await request.app.state.redis.get(key)
    return {"value": value}
```

## 3. DB 네이밍 컨벤션

```python
# SQLAlchemy 네이밍 컨벤션 설정
from sqlalchemy import MetaData

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_%(referred_table_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)
```

**명명 규칙:**
- 테이블명: `lower_snake_case`, 단수형 (`user`, `post`, `payment_account`)
- 모듈 접두사로 그룹화: `payment_account`, `payment_bill`
- datetime 컬럼: `_at` 접미사 (`created_at`, `updated_at`)
- date 컬럼: `_date` 접미사 (`published_date`)

## 4. Alembic 마이그레이션

```python
# 마이그레이션은 정적이고 가역적이어야 한다
# 파일명: {날짜}_{설명}.py
# 예: 2024-03-15_add_user_avatar_url.py

def upgrade():
    op.add_column('user', sa.Column('avatar_url', sa.String(), nullable=True))
    op.create_index('avatar_url_idx', 'user', ['avatar_url'])

def downgrade():
    op.drop_index('avatar_url_idx', 'user')
    op.drop_column('user', 'avatar_url')
```

**규칙:**
- 마이그레이션은 항상 `downgrade()`를 구현하라
- 데이터 마이그레이션과 스키마 마이그레이션을 분리하라
- 날짜 기반 파일명 사용: `2024-03-15_post_content_idx.py`

## 5. SQL 우선 철학

복잡한 집계, JOIN, JSON 구성은 Python 대신 SQL에서 처리하라:
```python
# ❌ Python에서 처리 — 느림
users = db.query(User).all()
result = [{"name": u.name, "post_count": len(u.posts)} for u in users]

# ✅ SQL에서 처리 — 빠름 (반드시 text() + 바인드 파라미터 사용)
from sqlalchemy import text

result = db.execute(text("""
    SELECT u.name, COUNT(p.id) as post_count
    FROM "user" u
    LEFT JOIN post p ON p.user_id = u.id
    WHERE u.status = :status
    GROUP BY u.id
"""), {"status": "active"}).all()

# ❌ 절대 금지 — SQL Injection 위험
# db.execute(f"SELECT * FROM user WHERE id = {user_id}")
# db.execute("SELECT * FROM user WHERE id = %s" % user_id)
```
