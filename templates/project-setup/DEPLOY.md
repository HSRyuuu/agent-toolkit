# {PROJECT_NAME} 배포 정보

> 최초 배포: YYYY-MM-DD
>
> **작성 원칙**
> - 운영 환경에 영향을 주는 **현재 상태**를 기록한다. 인시던트 대응 시 가장 먼저 열리는 문서다.
> - 비밀 값은 절대 적지 않는다. **변수명만** 적고, 값은 시크릿 매니저/콘솔 위치를 가리킨다.
> - 변경하면 즉시 갱신한다. 오래된 정보는 잘못된 정보보다 위험하다.

---

## 아키텍처 개요

```
[사용자]
   │
   ├─── <frontend-domain> ──────────► [<Vercel/Cloudflare/...>] <Frontend stack>
   │
   └─── <api-domain> ──────────────► [<GCP Cloud Run / AWS / ...>] <Backend stack>
                                                │
                                          [<Supabase / RDS / ...>]
                                          <Database>
```

> 캐시·큐·외부 서비스가 있으면 위 블록 옆에 추가한다 (예: Redis 사이드카, S3, Mixpanel).

---

## 도메인 설정

### 구성 흐름
1. **<도메인 등록기관>**에서 `<root-domain>` 구매
2. **DNS 위임 / 네임서버 설정**: <위임 대상>
3. **Frontend 도메인 연결**: `<root-domain>`, `www.<root-domain>` → <Frontend 플랫폼>
4. **Backend 도메인 연결**: `<api-subdomain>` → <Backend 플랫폼>
5. **TXT/CNAME 레코드 추가**: <도메인 소유권 인증, SSL, etc.>

### 최종 도메인
| 도메인 | 연결 대상 |
|--------|-----------|
| `<root-domain>` | <Frontend> |
| `www.<root-domain>` | <Frontend> |
| `<api-subdomain>` | <Backend> |

---

## Frontend — <플랫폼명>

| 항목 | 값 |
|------|----|
| 플랫폼 | <Vercel / Netlify / Cloudflare Pages> |
| 레포 / 루트 디렉토리 | `<owner>/<repo>` / `<frontend/>` |
| 프레임워크 | <Next.js / Vite / etc.> |
| 리전 | <region-id> |
| 도메인 | `<...>` |

### 환경변수
시크릿 자체는 적지 않는다. **변수명·역할·관리 위치**만 기록한다.

| 변수명 | 설명 | 비고 |
|--------|------|------|
| `<VAR_NAME>` | <설명> | <Vercel 콘솔에서 관리 / .env.production / etc.> |

### 배포 트리거
- <main 브랜치 push 시 자동 배포 / 수동 / GitHub Actions / etc.>

---

## Backend — <플랫폼명>

| 항목 | 값 |
|------|----|
| 플랫폼 | <Cloud Run / EKS / Fly.io> |
| 프로젝트 ID | `<...>` |
| 서비스명 | `<...>` |
| 리전 | `<region-id>` |
| 서비스 URL | `<https://...>` |
| 커스텀 도메인 | `<https://...>` |
| 컨테이너 이미지 | `<registry/path:tag>` |
| CPU / 메모리 | `<...>` |
| 동시성 | `<...>` |
| 최소 / 최대 인스턴스 | `<min>` / `<max>` |
| 런타임 프로필 | `<prod / staging>` |

### 사이드카 / 의존 컨테이너
| 컨테이너 | 이미지 | 용도 |
|---------|--------|------|
| `<name>` | `<image:tag>` | <Redis / sidecar / etc.> |

### 서비스 계정
| 계정 | 역할 |
|------|------|
| `<deploy-sa>` | CI/CD 배포용 |
| `<runner-sa>` | 런타임 실행용 |

### Artifact Registry / Container Registry
| 항목 | 값 |
|------|-----|
| 리전 | `<...>` |
| 저장소 | `<...>` |
| 이미지 경로 | `<...>` |

### 환경변수 (평문)
| 변수명 | 설명 |
|--------|------|
| `<VAR_NAME>` | <설명> |

### 환경변수 (시크릿)
**값은 적지 않는다.** 어디에 있는지만 적는다.

| 변수명 | 관리 위치 |
|--------|----------|
| `<SECRET_NAME>` | <GCP Secret Manager / AWS SSM / Vault / ...> |

---

## 데이터베이스

| 항목 | 값 |
|------|----|
| 플랫폼 | <Supabase / RDS / Cloud SQL> |
| 엔진 / 버전 | `<PostgreSQL 16>` |
| 리전 | `<...>` |
| 접속 호스트 | `<host>` |
| 백업 정책 | <자동 일일 백업 / PITR / etc.> |
| 마이그레이션 도구 | <Flyway / Liquibase / Prisma> |

스키마 정의는 [`DB_SCHEMA.md`](./DB_SCHEMA.md)를 참조.

---

## CI/CD

| 단계 | 도구 / 설정 파일 | 트리거 |
|------|-----------------|--------|
| 빌드 | <GitHub Actions: `.github/workflows/<file>`> | <push to main> |
| 테스트 | <...> | <PR> |
| 배포 | <...> | <release tag / push> |

### 배포 정의 파일
| 파일 | 설명 |
|------|------|
| `<path>` | <Cloud Run 서비스 정의 / Helm chart / Terraform 모듈> |

---

## 모니터링 / 로깅

| 항목 | 위치 |
|------|------|
| 애플리케이션 로그 | <Cloud Logging / CloudWatch / Loki> |
| 알람 | <콘솔 / Slack 채널> |
| 메트릭 | <Cloud Monitoring / Datadog / etc.> |
| 에러 트래킹 | <Sentry / etc.> |

---

## 롤백 절차

1. <롤백 트리거 명령 / 콘솔에서 이전 리비전 트래픽 100% 전환>
2. <검증할 헬스체크 엔드포인트>
3. <DB 마이그레이션 롤백이 필요한 경우의 절차>

> 롤백은 **상황 인지 → 결정 → 실행** 순서가 중요하다. 누가 결정하는지, 누가 실행하는지를 명확히 적어둔다.
