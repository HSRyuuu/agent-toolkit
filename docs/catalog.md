# Skill Catalog

> `agent-toolkit` plugin에 등록된 스킬 목록. 분류 기준은 [.claude/CLAUDE.md](../.claude/CLAUDE.md) 참고.
>
> Last updated: 2026-05-22

## 요약

| 디렉토리 | 개수 |
|---|---|
| `skills/` (독립 스킬) | 26 |
| `skills-workflow/` (워크플로우) | 0 |
| `skills-system/` (메타·스캐폴딩) | 4 |
| **합계** | **30** |

---

## skills/ — 독립 스킬

단일 목적, 다른 스킬에 의존하지 않고 단독으로 동작.

| 이름 | 한 줄 설명 | 주요 트리거 |
|---|---|---|
| [agent-harness-construction](../skills/agent-harness-construction/SKILL.md) | AI 에이전트의 action space·tool 정의·observation 포맷·context 예산 설계·최적화 | "agent design review", "harness construction", "tool 정의 정리" |
| [agent-introspection-debugging](../skills/agent-introspection-debugging/SKILL.md) | 반복 실패·루프·토큰 소진 중인 에이전트 런을 진단하고 자기진단 보고서 작성 | "agent stuck", "agent looping", "self-debug", "introspection report" |
| [create-mermaid-erd](../skills/create-mermaid-erd/SKILL.md) | PRD·도메인 설명을 받아 Mermaid `.mmd` ERD + 단일 `viewer.html`을 함께 출력 (개념·논리·물리 3종) | "ERD 만들어줘", "테이블 관계도", "데이터 모델링", "mmd 뷰어" |
| [excel-doc-updater](../skills/excel-doc-updater/SKILL.md) | form 기반 xlsx(인터페이스 정의서·요구사항 양식 등)를 별도 데이터 소스(markdown/JSON/DB) 기준으로 갱신 | xlsx 양식 갱신·재생성 요청 (코드 편집·일반 문서 갱신 제외) |
| [excel-ui-test-doc-creator](../skills/excel-ui-test-doc-creator/SKILL.md) | 테스트 시나리오/결과(JSON·markdown)를 단위테스트 산출물 xlsx로 생성 (사용자 템플릿 우선, 없으면 기본 양식) | "테스트 결과 엑셀로", "단위테스트 산출물", "QA 테스트 결과서" |
| [fastapi-guide](../skills/fastapi-guide/SKILL.md) | FastAPI 프로덕션 API 작성·리뷰·리팩토링 — async/sync, Pydantic, DI, 배포 | FastAPI 코드 작성·리뷰·리팩토링, async/sync 선택 |
| [git-master](../skills/git-master/SKILL.md) | 원자적 커밋·rebase·히스토리 관리·blame 추적 (스타일 자동 감지) | "커밋해줘", "atomic commit", "rebase", "git history" |
| [hsryuuu-writing](../skills/hsryuuu-writing/SKILL.md) | hsryuuu(innovation123.tistory.com) 톤·어조·언어 습관 가이드 — 글의 어휘·문장에만 관여 | "hsryuuu처럼 써줘", "내 블로그 말투로", "tistory 톤" |
| [html-cheat-sheet-creator](../skills/html-cheat-sheet-creator/SKILL.md) | 모바일 우선 단일 HTML 치트 시트·학습 카드·레퍼런스 시트 (2~6 탭, 사이드바, 스크롤 스파이) | "cheat sheet 만들어줘", "치트시트 HTML", "학습 카드 HTML" |
| [html-db-schema-viewer-creator](../skills/html-db-schema-viewer-creator/SKILL.md) | DBML·DDL·MCP 결과를 다중 페이지 정적 HTML DB 사이트로 변환 (ERD + 테이블 상세 + DBML 뷰어) | "ERD 사이트 만들어줘", "DB 뷰어 정적 사이트", "schema.dbml viewer" |
| [html-docs-creator](../skills/html-docs-creator/SKILL.md) | 임의의 input을 외부 CDN 의존 없는 단일 자기완결 HTML 문서로 (노션 톤, 스크롤 스파이, copy 버튼) | "이 내용 HTML로", "보고서·계획서 HTML로", "단일 파일 HTML 문서" |
| [html-erd-viewer-creator](../skills/html-erd-viewer-creator/SKILL.md) | DDL·mmd·schema 명세서를 단일 self-contained 인터랙티브 ERD HTML 파일로 | "ERD HTML 만들어줘", "인터랙티브 ERD", "mmd to HTML" |
| [kb-add](../skills/kb-add/SKILL.md) | KB 단일 input 통로 — URL/파일/텍스트/Inbox, 신규·append·modify·remove 모드, 수정·제거 시 ~/.kb-snapshots/ 스냅샷 | "/kb-add", "KB에 추가", "지식 저장소에 추가", "이거 정리해서 넣어줘" |
| [kb-link](../skills/kb-link/SKILL.md) | KB 위키링크 양방향 보강 — 4종 변형(`[[x]]`·alias·anchor·embed) 인식, Obsidian 그래프 뷰 엣지 추가 | "/kb-link", "그래프 보강해줘", "위키링크 추가해줘" |
| [kb-search](../skills/kb-search/SKILL.md) | KB 읽기 전용 질의응답 — 4계층 검색(tags/title/body/wikilink) + 출처 [[wikilink]] 인용 | "/kb-search", "KB에서 찾아줘", "위키에서 검색" |
| [node-backend-patterns](../skills/node-backend-patterns/SKILL.md) | Node·Express·Next.js API 라우트(또는 NestJS) 백엔드 아키텍처·DB·캐싱 패턴 | "Node 백엔드", "Express 라우트", "NestJS", "N+1 쿼리" |
| [pr](../skills/pr/SKILL.md) | GitHub일 때는 `gh pr create`로 자동 생성, 그 외에는 PR/MR draft markdown 파일 생성 | "PR 만들어줘", "MR 생성", "/pr", "리뷰 요청" |
| [prompt-master](../skills/prompt-master/SKILL.md) | LLM 프롬프트(시스템·에이전트·1회성·파이프라인) 작성·리뷰·평가, 멀티에이전트 오케스트레이션 | "프롬프트 만들어줘", "prompt 개선", "시스템 프롬프트" |
| [rest-api-design](../skills/rest-api-design/SKILL.md) | REST API 설계·검토 — 리소스 네이밍, 상태 코드, 페이지네이션, 필터링, 버전 관리 | "API 설계", "엔드포인트 설계", "페이지네이션 패턴" |
| [si-project-docs](../skills/si-project-docs/SKILL.md) | 한국 SI 업계 IT 프로젝트 산출물(설계서·명세서·계획서 등) 작성·업데이트 | "설계서 만들어줘", "API명세서 업데이트", "DB설계서 작성" |
| [springboot-java-standards](../skills/springboot-java-standards/SKILL.md) | Java 17+ 코딩 표준 + Spring Boot 가이드 (JPA/QueryDSL reference 별도) | Java 코드 작성·리뷰, Spring Boot 표준 |
| [springboot-kotlin-standards](../skills/springboot-kotlin-standards/SKILL.md) | Kotlin + Spring Boot 코딩 표준 — null safety, data class, 확장 함수, JPA/QueryDSL | Kotlin 코드 작성·리뷰, Spring Boot 표준 |
| [test-sync-verifier](../skills/test-sync-verifier/SKILL.md) | 코드 변경 후 테스트만 안전하게 동기화, 프로덕션 코드는 리포트만 | "테스트 확인해줘", "변경 검증해줘", "verify changes" |
| [ui-feature-spec-docs](../skills/ui-feature-spec-docs/SKILL.md) | 프론트엔드 소스(±화면정의서)에서 화면별 기능 정의서를 단일 markdown으로 (옵션: Playwright 라이브 검증) | "화면별 기능 정의서", "라우터 기반 기능 명세서", "/ui-feature-spec-docs" |
| [ui-test-runner](../skills/ui-test-runner/SKILL.md) | Playwright MCP로 dev 서버 UI 테스트, mutation 요청은 인터셉트해 실제 백엔드 보호 | "UI 테스트 돌려줘", "Playwright로 검증", "smoke test" |
| [writing-skills](../skills/writing-skills/SKILL.md) | 새 스킬 작성·기존 스킬 편집·배포 전 검증 | 새 스킬 생성, SKILL.md 수정, 스킬 검증 |

---

## skills-workflow/ — 워크플로우 스킬

`skills/`의 여러 스킬을 묶어 순차/병렬로 돌리는 오케스트레이션 스킬.

_(현재 등록된 스킬 없음)_

---

## skills-system/ — 메타·스캐폴딩 스킬

빈 곳에 프로젝트·플러그인·디렉토리 구조 자체를 세우는 더 큰 작업.

| 이름 | 한 줄 설명 | 주요 트리거 |
|---|---|---|
| [create-claude-plugin](../skills-system/create-claude-plugin/SKILL.md) | 로컬 Claude Code plugin 스캐폴딩 — 디렉토리·plugin.json·marketplace.json·settings.json 등록·로드 검증 | "플러그인 만들기", "plugin scaffold", "로컬 marketplace 등록" |
| [help-agent-toolkit](../skills-system/help-agent-toolkit/SKILL.md) | agent-toolkit 스킬 카탈로그 안내 — 전체 목록 출력 또는 의도 기반 매칭 추천 | "어떤 스킬 있어?", "툴킷에 뭐 있어?", "/help-agent-toolkit" |
| [project-setup](../skills-system/project-setup/SKILL.md) | 대상 프로젝트에 검증 스킬·작업 문서 골격 설치 (스킬은 `.claude/skills/`, 문서는 `docs/`, LESSONS.md는 `.claude/`) | "프로젝트 셋업", "프로젝트 초기화", "/project-setup" |
| [recommend-project-setting](../skills-system/recommend-project-setting/SKILL.md) | 진행 중 프로젝트의 누락 자산·갭을 read-only로 추천, 명시 요청 시에만 설치 | "프로젝트 세팅 추천", ".claude 보강", "/recommend-project-setting" |

---

## 갱신 방법

이 문서는 `update-project-docs` 스킬로 갱신한다.
