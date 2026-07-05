---
name: node-backend-patterns
description: >
  Use when writing, reviewing, or refactoring Node.js backend code in Express,
  Next.js API routes, or NestJS. Triggers: "Node 백엔드", "Express 라우트",
  "Next.js API", "NestJS", "Repository 패턴", "N+1 쿼리", "캐싱 전략",
  "JWT middleware", "structured logging". Do NOT use for REST contract design
  alone; use rest-api-design.
---

# 백엔드 개발 패턴 (Backend Development Patterns)

확장 가능한 서버측 애플리케이션을 위한 백엔드 아키텍처 패턴 및 모범 사례입니다.

## 적용 시점

- REST 또는 GraphQL API 엔드포인트 설계 시
- Repository, Service 또는 Controller 레이어 구현 시
- 데이터베이스 쿼리 최적화(N+1 문제, 인덱싱, 커넥션 풀링) 시
- 캐싱 추가(Redis, 인메모리, HTTP 캐시 헤더) 시
- 백그라운드 작업 또는 비동기 처리 설정 시
- API 에러 핸들링 및 유효성 검사 구조 잡을 때
- 미들웨어(인증, 로깅, 속도 제한) 구축 시

## API 설계 패턴

### RESTful API 구조

```typescript
// ✅ 리소스 기반 URL
GET    /api/markets                 # 리소스 목록 조회
GET    /api/markets/:id             # 단일 리소스 조회
POST   /api/markets                 # 리소스 생성
PUT    /api/markets/:id             # 리소스 전체 교체
PATCH  /api/markets/:id             # 리소스 일부 수정
DELETE /api/markets/:id             # 리소스 삭제

// ✅ 필터링, 정렬, 페이지네이션을 위한 쿼리 파라미터
GET /api/markets?status=active&sort=volume&limit=20&offset=0
```

### Repository 패턴

```typescript
// 데이터 접근 로직 추상화
interface MarketRepository {
  findAll(filters?: MarketFilters): Promise<Market[]>
  findById(id: string): Promise<Market | null>
  create(data: CreateMarketDto): Promise<Market>
  update(id: string, data: UpdateMarketDto): Promise<Market>
  delete(id: string): Promise<void>
}

class SupabaseMarketRepository implements MarketRepository {
  async findAll(filters?: MarketFilters): Promise<Market[]> {
    let query = supabase.from('markets').select('*')

    if (filters?.status) {
      query = query.eq('status', filters.status)
    }

    if (filters?.limit) {
      query = query.limit(filters.limit)
    }

    const { data, error } = await query

    if (error) throw new Error(error.message)
    return data
  }

  // 기타 메서드들...
}
```

### Service 레이어 패턴

```typescript
// 비즈니스 로직을 데이터 접근 로직과 분리
class MarketService {
  constructor(private marketRepo: MarketRepository) {}

  async searchMarkets(query: string, limit: number = 10): Promise<Market[]> {
    // 비즈니스 로직
    const embedding = await generateEmbedding(query)
    const results = await this.vectorSearch(embedding, limit)

    // 전체 데이터 조회
    const markets = await this.marketRepo.findByIds(results.map(r => r.id))

    // 유사도에 따라 정렬
    return markets.sort((a, b) => {
      const scoreA = results.find(r => r.id === a.id)?.score || 0
      const scoreB = results.find(r => r.id === b.id)?.score || 0
      return scoreA - scoreB
    })
  }

  private async vectorSearch(embedding: number[], limit: number) {
    // 벡터 검색 구현
  }
}
```

### 미들웨어 패턴

```typescript
// 요청/응답 처리 파이프라인
export function withAuth(handler: NextApiHandler): NextApiHandler {
  return async (req, res) => {
    const token = req.headers.authorization?.replace('Bearer ', '')

    if (!token) {
      return res.status(401).json({ error: 'Unauthorized' })
    }

    try {
      const user = await verifyToken(token)
      req.user = user
      return handler(req, res)
    } catch (error) {
      return res.status(401).json({ error: 'Invalid token' })
    }
  }
}

// 사용 예시
export default withAuth(async (req, res) => {
  // 핸들러에서 req.user에 접근 가능
})
```

## 데이터베이스 패턴

### 쿼리 최적화

```typescript
// ✅ 좋은 예: 필요한 컬럼만 선택
const { data } = await supabase
  .from('markets')
  .select('id, name, status, volume')
  .eq('status', 'active')
  .order('volume', { ascending: false })
  .limit(10)

// ❌ 나쁜 예: 모든 컬럼 선택
const { data } = await supabase
  .from('markets')
  .select('*')
```

### N+1 쿼리 방지

```typescript
// ❌ 나쁜 예: N+1 쿼리 문제 발생
const markets = await getMarkets()
for (const market of markets) {
  market.creator = await getUser(market.creator_id)  // N번의 쿼리 실행
}

// ✅ 좋은 예: 배치 조회(Batch Fetch)
const markets = await getMarkets()
const creatorIds = markets.map(m => m.creator_id)
const creators = await getUsers(creatorIds)  // 1번의 쿼리 실행
const creatorMap = new Map(creators.map(c => [c.id, c]))

markets.forEach(market => {
  market.creator = creatorMap.get(market.creator_id)
})
```

### 트랜잭션 패턴

```typescript
async function createMarketWithPosition(
  marketData: CreateMarketDto,
  positionData: CreatePositionDto
) {
  // Supabase RPC 사용
  const { data, error } = await supabase.rpc('create_market_with_position', {
    market_data: marketData,
    position_data: positionData
  })

  if (error) throw new Error('Transaction failed')
  return data
}

// Supabase의 SQL 함수 예시
CREATE OR REPLACE FUNCTION create_market_with_position(
  market_data jsonb,
  position_data jsonb
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
BEGIN
  -- 트랜잭션 자동 시작
  INSERT INTO markets VALUES (market_data);
  INSERT INTO positions VALUES (position_data);
  RETURN jsonb_build_object('success', true);
EXCEPTION
  WHEN OTHERS THEN
    -- 자동 롤백 발생
    RETURN jsonb_build_object('success', false, 'error', SQLERRM);
END;
$$;
```

## 캐싱 전략

### Redis 캐싱 레이어

```typescript
class CachedMarketRepository implements MarketRepository {
  constructor(
    private baseRepo: MarketRepository,
    private redis: RedisClient
  ) {}

  async findById(id: string): Promise<Market | null> {
    // 캐시 먼저 확인
    const cached = await this.redis.get(`market:${id}`)

    if (cached) {
      return JSON.parse(cached)
    }

    // 캐시 미스 - 데이터베이스에서 조회
    const market = await this.baseRepo.findById(id)

    if (market) {
      // 5분 동안 캐싱
      await this.redis.setex(`market:${id}`, 300, JSON.stringify(market))
    }

    return market
  }

  async invalidateCache(id: string): Promise<void> {
    await this.redis.del(`market:${id}`)
  }
}
```

### Cache-Aside 패턴

```typescript
async function getMarketWithCache(id: string): Promise<Market> {
  const cacheKey = `market:${id}`

  // 캐시 시도
  const cached = await redis.get(cacheKey)
  if (cached) return JSON.parse(cached)

  // 캐시 미스 - DB에서 조회
  const market = await db.markets.findUnique({ where: { id } })

  if (!market) throw new Error('Market not found')

  // 캐시 업데이트
  await redis.setex(cacheKey, 300, JSON.stringify(market))

  return market
}
```

## 에러 핸들링 패턴

### 중앙 집중식 에러 핸들러

```typescript
class ApiError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public isOperational = true
  ) {
    super(message)
    Object.setPrototypeOf(this, ApiError.prototype)
  }
}

export function errorHandler(error: unknown, req: Request): Response {
  if (error instanceof ApiError) {
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: error.statusCode })
  }

  if (error instanceof z.ZodError) {
    return NextResponse.json({
      success: false,
      error: 'Validation failed',
      details: error.errors
    }, { status: 400 })
  }

  // 예상치 못한 에러 로깅
  console.error('Unexpected error:', error)

  return NextResponse.json({
    success: false,
    error: 'Internal server error'
  }, { status: 500 })
}

// 사용 예시
export async function GET(request: Request) {
  try {
    const data = await fetchData()
    return NextResponse.json({ success: true, data })
  } catch (error) {
    return errorHandler(error, request)
  }
}
```

### 지수 백오프를 이용한 재시도 (Retry with Exponential Backoff)

```typescript
async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  let lastError: Error

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error

      if (i < maxRetries - 1) {
        // 지수 백오프: 1초, 2초, 4초
        const delay = Math.pow(2, i) * 1000
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
  }

  throw lastError!
}

// 사용 예시
const data = await fetchWithRetry(() => fetchFromAPI())
```

## 인증 및 인가 (Authentication & Authorization)

### JWT 토큰 검증

```typescript
import jwt from 'jsonwebtoken'

interface JWTPayload {
  userId: string
  email: string
  role: 'admin' | 'user'
}

export function verifyToken(token: string): JWTPayload {
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as JWTPayload
    return payload
  } catch (error) {
    throw new ApiError(401, 'Invalid token')
  }
}

export async function requireAuth(request: Request) {
  const token = request.headers.get('authorization')?.replace('Bearer ', '')

  if (!token) {
    throw new ApiError(401, 'Missing authorization token')
  }

  return verifyToken(token)
}

// API 라우트에서의 사용 예시
export async function GET(request: Request) {
  const user = await requireAuth(request)

  const data = await getDataForUser(user.userId)

  return NextResponse.json({ success: true, data })
}
```

### 역할 기반 접근 제어 (Role-Based Access Control)

```typescript
type Permission = 'read' | 'write' | 'delete' | 'admin'

interface User {
  id: string
  role: 'admin' | 'moderator' | 'user'
}

const rolePermissions: Record<User['role'], Permission[]> = {
  admin: ['read', 'write', 'delete', 'admin'],
  moderator: ['read', 'write', 'delete'],
  user: ['read', 'write']
}

export function hasPermission(user: User, permission: Permission): boolean {
  return rolePermissions[user.role].includes(permission)
}

export function requirePermission(permission: Permission) {
  return (handler: (request: Request, user: User) => Promise<Response>) => {
    return async (request: Request) => {
      const user = await requireAuth(request)

      if (!hasPermission(user, permission)) {
        throw new ApiError(403, 'Insufficient permissions')
      }

      return handler(request, user)
    }
  }
}

// 사용 예시 - HOF가 핸들러를 감쌈
export const DELETE = requirePermission('delete')(
  async (request: Request, user: User) => {
    // 핸들러는 권한이 확인된 인증된 사용자를 인자로 받음
    return new Response('Deleted', { status: 200 })
  }
)
```

## 속도 제한 (Rate Limiting)

### 단순 인메모리 속도 제한기

```typescript
class RateLimiter {
  private requests = new Map<string, number[]>()

  async checkLimit(
    identifier: string,
    maxRequests: number,
    windowMs: number
  ): Promise<boolean> {
    const now = Date.now()
    const requests = this.requests.get(identifier) || []

    // 윈도우 밖의 오래된 요청 제거
    const recentRequests = requests.filter(time => now - time < windowMs)

    if (recentRequests.length >= maxRequests) {
      return false  // 속도 제한 초과
    }

    // 현재 요청 추가
    recentRequests.push(now)
    this.requests.set(identifier, recentRequests)

    return true
  }
}

const limiter = new RateLimiter()

export async function GET(request: Request) {
  const ip = request.headers.get('x-forwarded-for') || 'unknown'

  const allowed = await limiter.checkLimit(ip, 100, 60000)  // 분당 100회 요청

  if (!allowed) {
    return NextResponse.json({
      error: 'Rate limit exceeded'
    }, { status: 429 })
  }

  // 요청 처리 계속 진행
}
```

## 백그라운드 작업 및 큐 (Background Jobs & Queues)

### 단순 큐 패턴

```typescript
class JobQueue<T> {
  private queue: T[] = []
  private processing = false

  async add(job: T): Promise<void> {
    this.queue.push(job)

    if (!this.processing) {
      this.process()
    }
  }

  private async process(): Promise<void> {
    this.processing = true

    while (this.queue.length > 0) {
      const job = this.queue.shift()!

      try {
        await this.execute(job)
      } catch (error) {
        console.error('Job failed:', error)
      }
    }

    this.processing = false
  }

  private async execute(job: T): Promise<void> {
    // 작업 실행 로직
  }
}

// 마켓 인덱싱을 위한 사용 예시
interface IndexJob {
  marketId: string
}

const indexQueue = new JobQueue<IndexJob>()

export async function POST(request: Request) {
  const { marketId } = await request.json()

  // 블로킹하지 않고 큐에 추가
  await indexQueue.add({ marketId })

  return NextResponse.json({ success: true, message: 'Job queued' })
}
```

## 로깅 및 모니터링

### 구조화된 로깅 (Structured Logging)

```typescript
interface LogContext {
  userId?: string
  requestId?: string
  method?: string
  path?: string
  [key: string]: unknown
}

class Logger {
  log(level: 'info' | 'warn' | 'error', message: string, context?: LogContext) {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      ...context
    }

    console.log(JSON.stringify(entry))
  }

  info(message: string, context?: LogContext) {
    this.log('info', message, context)
  }

  warn(message: string, context?: LogContext) {
    this.log('warn', message, context)
  }

  error(message: string, error: Error, context?: LogContext) {
    this.log('error', message, {
      ...context,
      error: error.message,
      stack: error.stack
    })
  }
}

const logger = new Logger()

// 사용 예시
export async function GET(request: Request) {
  const requestId = crypto.randomUUID()

  logger.info('Fetching markets', {
    requestId,
    method: 'GET',
    path: '/api/markets'
  })

  try {
    const markets = await fetchMarkets()
    return NextResponse.json({ success: true, data: markets })
  } catch (error) {
    logger.error('Failed to fetch markets', error as Error, { requestId })
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
```

## 상세 참조

- **NestJS 모듈/컨트롤러/서비스/DTO/Common 패턴**: `references/nestjs-patterns.md`
  - NestJS 프로젝트 구조, 데코레이터 기반 DI, class-validator, Exception Filter, Interceptor 작성 시

**핵심**: 백엔드 패턴은 확장 가능하고 유지보수하기 쉬운 서버측 애플리케이션을 가능하게 합니다. 프로젝트의 복잡도 수준에 맞는 패턴을 선택하십시오.
