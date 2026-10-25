# {PROJECT_NAME} Overview

> 이 문서는 프로젝트의 **정체성·맥락·현재 상태**를 한 곳에 정리한다.
> 신규 합류자, 외부 협업자, 그리고 Claude가 "이 프로젝트가 무엇인지"를 빠르게 파악할 수 있도록 한다.
>
> **작성 원칙**
> - "왜 이 프로젝트가 존재하는가"와 "지금 어떤 상태인가"만 적는다.
> - 코드·인프라·DB의 **상세**는 적지 않는다 — 그건 `SOURCE_MAP.md`, `DEPLOY.md`, `DB_SCHEMA.md`의 영역이다.
> - 정보가 바뀌면 즉시 갱신한다. 외부에 보여주는 첫 인상이다.

---

## 한 줄 정의

> **{PROJECT_NAME}** — <한 줄로 무엇을 위한 프로젝트인지>

선택: 슬로건이나 짧은 캐치프레이즈를 함께 적어도 된다.

> "<슬로건이 있으면 여기>"

---

## 문제 정의 (Why)

이 프로젝트가 풀려는 문제는 무엇인가? 누가 어떤 상황에서 어려움을 겪는가?

- <문제 1 — 한두 줄 설명>
- <문제 2 — 한두 줄 설명>

> 비즈니스/제품 가설을 적는 곳이지, 기능을 나열하는 곳이 아니다. 기능 목록은 README에.

---

## 사용자

- **주 사용자**: <역할/직군 — 예: "주니어~중급 개발자, 데스크톱 환경에서 작업">
- **부 사용자**: <있으면>
- **사용 환경**: <예: "데스크톱 브라우저 우선, 모바일은 깨지지 않는 수준">

---

## 기술 스택

### Frontend

| 항목 | 값 |
|---|---|
| 언어 | <TypeScript / JavaScript> |
| 프레임워크 | <Next.js 16 (App Router) / Vite + React / SvelteKit / ...> |
| UI | <Tailwind CSS v4 / shadcn/ui / ...> |
| 상태 관리 | <Zustand / Jotai / React Context / ...> |
| 폰트 / 디자인 시스템 | <Pretendard / 자체 디자인 시스템> |
| 빌드 / 패키지 매니저 | <pnpm / npm / yarn / bun> |

### Backend

| 항목 | 값 |
|---|---|
| 언어 | <Kotlin 1.9 / Java 21 / Python 3.12 / Node 20 / ...> |
| 프레임워크 | <Spring Boot 3.2 / FastAPI / NestJS / ...> |
| ORM / 데이터 액세스 | <JPA + QueryDSL / Prisma / SQLAlchemy / ...> |
| 인증 | <JWT / OAuth / Clerk / Supabase Auth> |
| 빌드 도구 | <Gradle / Maven / Poetry / ...> |

### 데이터 / 인프라

| 항목 | 값 |
|---|---|
| 데이터베이스 | <PostgreSQL 16 / MySQL / MongoDB / ...> |
| 캐시 | <Redis / Memcached / 없음> |
| 객체 스토리지 | <S3 / GCS / Supabase Storage / 없음> |
| 큐 / 이벤트 | <SQS / Kafka / 없음> |
| 검색 | <Elasticsearch / pg_trgm / Algolia / 없음> |

### 배포 / 호스팅

| 항목 | 값 |
|---|---|
| Frontend | <Vercel / Netlify / Cloudflare Pages> |
| Backend | <GCP Cloud Run / AWS ECS / Fly.io> |
| DB | <Supabase / RDS / Cloud SQL> |
| CI/CD | <GitHub Actions / GitLab CI> |

> 상세 배포 설정·환경변수는 [`DEPLOY.md`](./DEPLOY.md) 참조.

---

## 디자인 / UX 토큰

핵심 비주얼 아이덴티티만 적는다. 컴포넌트별 상세 규칙·색상 팔레트·타이포그래피는 [`DESIGN.md`](./DESIGN.md)에 둔다.

| 항목 | 값 |
|---|---|
| Primary 컬러 | `<#3451B2>` |
| Accent 컬러 | `<#F06449>` |
| 배경 톤 | `<#F7F8FB>` (쿨톤 / 웜톤 / 뉴트럴) |
| 테마 | <단일 / 다크모드 지원> |
| 톤 & 매너 | <한 줄 — 예: "신뢰감 있는 사파이어 + 따뜻한 코랄 액센트"> |

---

## 현재 단계

- **상태**: <prototype / MVP / production / maintenance>
- **시작일**: YYYY-MM-DD
- **첫 배포일**: YYYY-MM-DD (또는 "미배포")
- **현재 사이클 / 스프린트**: <ex. "Sprint 6 — 키워드 허브 개선">

---

## 마일스톤

지나간 큰 사건과 다가올 큰 사건만 한 줄씩 적는다. 일일 작업 이력이 별도로 있다면 그 위치를 한 줄로 명기한다 (없으면 이 문장 삭제).

| 날짜 | 마일스톤 |
|---|---|
| YYYY-MM-DD | 프로젝트 시작 |
| YYYY-MM-DD | <MVP 완성 / 첫 배포 / 도메인 연결> |
| YYYY-MM-DD (예정) | <다가올 마일스톤> |

---

## 핵심 링크

| 항목 | URL |
|---|---|
| 프로덕션 | `<https://...>` |
| 스테이징 | `<https://...>` (있으면) |
| 코드 저장소 | `<github.com/.../...>` |
| 이슈 트래커 | `<github.com/.../issues / Linear / Jira>` |
| 디자인 | `<Figma 링크>` |
| 문서 / 노션 | `<Notion / Confluence>` |
| 모니터링 / 로그 | `<Sentry / Grafana>` |

---

## 팀 / 책임

| 역할 | 담당 | 비고 |
|---|---|---|
| <Owner / PM> | <이름> | <연락처/슬랙> |
| <Frontend> | <이름> | |
| <Backend> | <이름> | |
| <Design> | <이름> | |
| <Ops / DevOps> | <이름> | |

> 1인 프로젝트면 단순히 "Owner: <이름>" 한 줄로 충분.

---

## 비고 / 의도적 제약

이 프로젝트에서 **하지 않기로 결정한 것**을 적는다. 코드 결정의 배경이 된다.

- <예: "네이티브 모바일 앱은 만들지 않는다 — 데스크톱 웹 우선">
- <예: "다크모드는 지원하지 않는다 — 단일 라이트 테마로 일관성 유지">
- <예: "다국어 지원 없음 — 한국어 사용자만 대상">
