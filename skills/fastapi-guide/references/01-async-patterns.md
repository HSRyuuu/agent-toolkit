# Async 패턴 & 백그라운드 태스크

## 1. Async/Sync 선택 규칙

| 코드 유형 | 사용 상황 | 성능 |
|---|---|---|
| `async def` + `await` | 비동기 I/O (DB, 외부 API 호출) | 최고 |
| `def` (동기) | 블로킹 I/O, CPU 집약 작업 | 양호 |
| `async def` + 블로킹 코드 | **절대 금지** — 이벤트 루프 전체 정지 | 최악 |

FastAPI는 `def` 함수를 자동으로 스레드 풀에서 실행한다. 블로킹 작업엔 `def`를 사용하라.

### ❌ 잘못된 예
```python
@app.get("/bad")
async def bad_endpoint():
    time.sleep(5)  # 이벤트 루프 전체가 5초 동안 정지!
    return {"message": "done"}
```

### ✅ 올바른 예
```python
@app.get("/good")
def good_endpoint():
    time.sleep(5)  # FastAPI가 스레드 풀에서 실행 — 이벤트 루프는 자유
    return {"message": "done"}

@app.get("/async-good")
async def async_good():
    await asyncio.sleep(5)  # 논블로킹
    return {"message": "done"}
```

### 블로킹 → 논블로킹 대체 목록
```python
# ❌ 블로킹 (def 사용)          # ✅ 논블로킹 (async def + await)
time.sleep()              →    await asyncio.sleep()
requests.get()            →    await httpx_client.get()
open().read()             →    await aiofiles.open()
psycopg2                  →    asyncpg
SQLAlchemy Session        →    AsyncSession
```

## 2. 동기 SDK를 async 라우트에서 사용할 때

서드파티 SDK가 동기 전용인 경우 `run_in_threadpool`로 감싸라:
```python
from fastapi.concurrency import run_in_threadpool

@app.get("/sync-sdk")
async def use_sync_sdk():
    result = await run_in_threadpool(sync_client.make_request, data=my_data)
    return result
```

## 3. CPU 집약 작업

GIL로 인해 `def` 스레드 풀이어도 CPU 작업은 다른 요청을 차단한다.

### ✅ Celery 워커로 오프로드
```python
from celery import Celery

celery_app = Celery('tasks', broker='redis://localhost')

@celery_app.task
def process_heavy_work(data):
    return complex_calculation(data)

@app.post("/compute")
async def compute(data: dict):
    task = process_heavy_work.delay(data)
    return {"task_id": task.id, "status": "processing"}  # 즉시 응답
```

## 4. 백그라운드 태스크

사용자 응답과 무관한 작업(이메일, 알림, 통계)은 `BackgroundTasks`로 처리하라.

### ❌ 잘못된 예
```python
@app.post("/register")
async def register(user: UserCreate):
    create_user(user)
    send_welcome_email(user.email)   # 2초
    generate_avatar(user.id)         # 2초
    update_analytics(user)           # 1초
    return {"message": "created"}    # 5초 후 응답
```

### ✅ 올바른 예
```python
from fastapi import BackgroundTasks

@app.post("/register")
async def register(user: UserCreate, background_tasks: BackgroundTasks):
    create_user(user)
    background_tasks.add_task(send_welcome_email, user.email)
    background_tasks.add_task(generate_avatar, user.id)
    background_tasks.add_task(update_analytics, user)
    return {"message": "created"}  # 즉시 응답
```

**규칙:**
- 가벼운 비동기 작업 → `BackgroundTasks`
- 무거운 CPU/장시간 작업 → **Celery + Redis**
