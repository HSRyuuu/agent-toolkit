# Skill Catalog

> `agent-toolkit` plugin에 등록된 스킬 목록. 분류 기준은 [.claude/CLAUDE.md](../.claude/CLAUDE.md) 참고.
>
> Last updated: 2026-04-29

## 요약

| 디렉토리 | 개수 |
|---|---|
| `skills/` (독립 스킬) | 8 |
| `skills-workflow/` (워크플로우) | 0 |
| `skills-system/` (메타·스캐폴딩) | 3 |
| **합계** | **11** |

---

## skills/ — 독립 스킬

단일 목적, 다른 스킬에 의존하지 않고 단독으로 동작.

| 이름 | 한 줄 설명 | 주요 트리거 |
|---|---|---|
| [fastapi-guide](../skills/fastapi-guide/SKILL.md) | FastAPI 프로덕션 API 개발 모범 사례 — async/sync, Pydantic, DI, 배포 | FastAPI 코드 작성·리뷰·리팩토링 |
| [git-master](../skills/git-master/SKILL.md) | 원자적 커밋·rebase·히스토리 관리 전문가 (스타일 자동 감지) | 커밋 분리, rebase, 히스토리 추적 |
| [node-backend-patterns](../skills/node-backend-patterns/SKILL.md) | Node.js·Express·Next.js API 라우트 백엔드 아키텍처 패턴 (NestJS 별도 reference) | 백엔드 API·DB·캐싱 설계 |
| [prompt-master](../skills/prompt-master/SKILL.md) | LLM 프롬프트 엔지니어링 — 전략 선택 + 작성 기법, 서브에이전트 오케스트레이션 reference 포함 | 프롬프트 작성·개선·리뷰 |
| [rest-api-design](../skills/rest-api-design/SKILL.md) | REST API 설계 패턴 — 리소스 네이밍, 상태 코드, 페이지네이션, 에러 응답, 버전 관리 | API 엔드포인트 설계·리뷰 |
| [springboot-java-standards](../skills/springboot-java-standards/SKILL.md) | Java 17+ 코딩 표준 + Spring Boot 가이드 (JPA/QueryDSL reference 별도) | Java 코드 작성·리뷰 |
| [springboot-kotlin-standards](../skills/springboot-kotlin-standards/SKILL.md) | Kotlin + Spring Boot 코딩 표준 — null safety, data class, 확장 함수 | Kotlin 코드 작성·리뷰 |
| [test-sync-verifier](../skills/test-sync-verifier/SKILL.md) | 코드 변경 후 테스트 검증 — 테스트 코드만 수정, 프로덕션은 리포트만 | "테스트 확인해줘", "verify changes" |

---

## skills-workflow/ — 워크플로우 스킬

`skills/`의 여러 스킬을 묶어 순차/병렬로 돌리는 오케스트레이션 스킬.

_(현재 등록된 스킬 없음)_

---

## skills-system/ — 메타·스캐폴딩 스킬

빈 곳에 프로젝트·플러그인·디렉토리 구조 자체를 세우는 더 큰 작업.

| 이름 | 한 줄 설명 | 주요 트리거 |
|---|---|---|
| [create-claude-plugin](../skills-system/create-claude-plugin/SKILL.md) | 로컬 Claude Code plugin 스캐폴딩 — 디렉토리, plugin.json, marketplace.json, settings.json 등록, 로드 검증 | "플러그인 만들기", "plugin scaffold", "로컬 marketplace 등록" |
| [project-setup](../skills-system/project-setup/SKILL.md) | 대상 프로젝트에 검증 스킬·작업 문서 골격 설치 (스킬은 `.claude/skills/`, 작업 문서 5종은 기본 `docs/`·사용자 지정 가능, LESSONS.md는 `.claude/` 고정). 메뉴 선택형, 설치 전 PATHS 공지 단계 포함 | "프로젝트 셋업", "프로젝트 초기화", "/project-setup" |
| [recommend-project-setting](../skills-system/recommend-project-setting/SKILL.md) | 진행 중 프로젝트의 현재 세팅(`.claude/`·`docs/` 양쪽)을 스캔하고 누락 자산·부분 갭(CLAUDE.md 핵심 섹션 등)을 추천. 기본 read-only, 사용자 명시 요청 시 PATHS 공지 후 선택 설치 | "프로젝트 세팅 추천", ".claude 보강", "/recommend-project-setting" |

---

## 갱신 방법

새 스킬을 추가하거나 옮긴 뒤 이 문서를 직접 갱신한다. 추후 자동 생성 스크립트가 필요해지면 `skills-workflow/` 또는 `skills-system/`에 별도 스킬을 추가할 것.
