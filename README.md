# agent-toolkit

> 이 저장소는 [https://github.com/HSRyuuu/AI-Practice-Archive](https://github.com/HSRyuuu/AI-Practice-Archive)를 플러그인 형태로 변경한 것입니다.
> 더 이상 기존 저장소는 유지보수되지 않고 이 저장소로 마이그레이션 되었습니다.

## 설치

이 저장소를 **로컬 directory marketplace**로 등록해서 사용한다.

```bash
git clone https://github.com/HSRyuuu/agent-toolkit.git
cd agent-toolkit
pwd # ~/your-dir/agent-toolkit
```

Claude Code 안에서:

```
/plugin marketplace add ~/your-dir/agent-toolkit
/plugin install agent-toolkit@agent-toolkit-local
```

새 세션을 띄우면 `skills/`, `skills-workflow/`, `skills-system/`의 모든 스킬이 자동 로드된다. 디렉토리를 그대로 편집하면 다음 세션부터 반영 — 빌드·배포 단계 없음.

## 무엇이 들어 있나

- `skills/` — 독립 스킬
- `skills-workflow/` — 워크플로우 스킬
- `skills-system/` — 메타·스캐폴딩 스킬
- `templates/` — 다른 스킬이 골격 원본으로 쓰는 템플릿 모음

전체 목록과 트리거는 [docs/catalog.md](docs/catalog.md). 디렉토리 분류 기준은 [.claude/CLAUDE.md](.claude/CLAUDE.md).

## 갱신

스킬을 추가/이동/삭제했으면 `update-project-docs` 스킬로 문서를 동기화한다.

---

## 구성

### skills/

단일 목적, 다른 스킬에 의존하지 않고 단독으로 동작.

| 이름                                                                           | 설명                                                                                            |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| [agent-harness-construction](skills/agent-harness-construction/SKILL.md)       | AI 에이전트의 action space·tool 정의·observation 포맷·context 예산 설계·최적화                  |
| [agent-introspection-debugging](skills/agent-introspection-debugging/SKILL.md) | 반복 실패·루프·토큰 소진 중인 에이전트 런을 캡처·진단·격리하고 자기진단 보고서 작성             |
| [create-mermaid-erd](skills/create-mermaid-erd/SKILL.md)                       | PRD·도메인 설명을 받아 Mermaid `.mmd` ERD + 단일 `viewer.html` (개념·논리·물리 3종)             |
| [excel-doc-updater](skills/excel-doc-updater/SKILL.md)                         | form 기반 xlsx(인터페이스 정의서·요구사항 양식)를 별도 데이터 소스로 갱신·재생성                |
| [excel-ui-test-doc-creator](skills/excel-ui-test-doc-creator/SKILL.md)         | 테스트 시나리오·결과(JSON·markdown)를 단위테스트 산출물 xlsx로 생성                             |
| [fastapi-guide](skills/fastapi-guide/SKILL.md)                                 | FastAPI 프로덕션 API 모범 사례 — async/sync, Pydantic, DI, 배포                                 |
| [git-master](skills/git-master/SKILL.md)                                       | 원자적 커밋·rebase·히스토리 관리 (저장소 커밋 스타일 자동 감지)                                 |
| [hsryuuu-writing](skills/hsryuuu-writing/SKILL.md)                             | hsryuuu(innovation123.tistory.com) 톤·어조·언어 습관 가이드                                     |
| [html-cheat-sheet-creator](skills/html-cheat-sheet-creator/SKILL.md)           | 모바일 우선 단일 HTML 치트 시트·학습 카드·레퍼런스 시트 (2~6 탭 + 사이드바)                     |
| [html-db-schema-viewer-creator](skills/html-db-schema-viewer-creator/SKILL.md) | DBML·DDL·MCP 결과를 다중 페이지 정적 HTML DB 사이트로 (ERD + 테이블 상세 + DBML 뷰어)           |
| [html-docs-creator](skills/html-docs-creator/SKILL.md)                         | 임의의 input을 외부 CDN 의존 없는 단일 자기완결 HTML 문서로 (노션 톤)                           |
| [html-erd-viewer-creator](skills/html-erd-viewer-creator/SKILL.md)             | DDL·mmd·schema 명세서를 단일 self-contained 인터랙티브 ERD HTML 파일로                          |
| [kb-add](skills/kb-add/SKILL.md)                                               | KB 단일 input 통로 — URL/파일/텍스트/Inbox, 신규/append/modify/remove 모드, 수정·제거 시 스냅샷 |
| [kb-lint](skills/kb-lint/SKILL.md)                                             | KB 건강 점검 + 위키링크 보강 — 깨진 링크·고아·tags 누락·_inbox 방치·_raw 고아·진부·폴더 컨벤션 검사, `--boost-links`로 양방향 보강 |
| [kb-search](skills/kb-search/SKILL.md)                                         | KB 읽기 전용 질의응답 — 4계층 검색(tags/title/body/wikilink) + 출처 인용                        |
| [node-backend-patterns](skills/node-backend-patterns/SKILL.md)                 | Node·Express·Next.js API 라우트(또는 NestJS) 백엔드 아키텍처·DB·캐싱 패턴                       |
| [pr](skills/pr/SKILL.md)                                                       | GitHub은 `gh pr create`로 자동 생성, 그 외에는 PR/MR draft markdown 파일 생성                   |
| [prompt-master](skills/prompt-master/SKILL.md)                                 | LLM 프롬프트 엔지니어링 — 작성·리뷰·평가, 멀티에이전트 오케스트레이션                           |
| [rest-api-design](skills/rest-api-design/SKILL.md)                             | REST API 설계 — 리소스 네이밍, 상태 코드, 페이지네이션, 에러 응답, 버전 관리                    |
| [si-project-docs](skills/si-project-docs/SKILL.md)                             | 한국 SI 업계 IT 프로젝트 산출물(설계서·명세서·계획서 등) 작성·업데이트                          |
| [springboot-java-standards](skills/springboot-java-standards/SKILL.md)         | Java 17+ 코딩 표준 + Spring Boot 가이드 (JPA/QueryDSL reference 별도)                           |
| [springboot-kotlin-standards](skills/springboot-kotlin-standards/SKILL.md)     | Kotlin + Spring Boot 코딩 표준 — null safety, data class, 확장 함수                             |
| [test-sync-verifier](skills/test-sync-verifier/SKILL.md)                       | 코드 변경 후 테스트 검증 — 테스트 코드만 수정, 프로덕션은 리포트만                              |
| [ui-feature-spec-docs](skills/ui-feature-spec-docs/SKILL.md)                   | 프론트엔드 소스(±화면정의서)에서 화면별 기능 정의서를 단일 markdown으로 (옵션: Playwright 검증) |
| [ui-test-runner](skills/ui-test-runner/SKILL.md)                               | Playwright MCP로 dev 서버 UI 테스트, mutation 요청은 인터셉트해 실제 백엔드 보호                |
| [writing-skills](skills/writing-skills/SKILL.md)                               | 새 스킬 작성·기존 스킬 편집·배포 전 검증                                                        |

### skills-system/

빈 곳에 프로젝트·플러그인·디렉토리 구조 자체를 세우는 메타·스캐폴딩 작업.

| 이름                                                                          | 설명                                                                   |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| [create-claude-plugin](skills-system/create-claude-plugin/SKILL.md)           | 새 로컬 Claude Code 플러그인 스캐폴딩 + marketplace 등록·로드 검증     |
| [help-agent-toolkit](skills-system/help-agent-toolkit/SKILL.md)               | agent-toolkit 스킬 카탈로그 안내 — 전체 목록 또는 의도 기반 추천       |
| [project-setup](skills-system/project-setup/SKILL.md)                         | 대상 프로젝트에 검증 스킬·작업 문서 골격을 메뉴 선택형으로 설치        |
| [recommend-project-setting](skills-system/recommend-project-setting/SKILL.md) | 진행 중 프로젝트의 누락 자산을 read-only로 추천, 명시 요청 시에만 설치 |

### skills-workflow/

`skills/`의 여러 스킬을 묶어 순차/병렬로 돌리는 오케스트레이션 스킬.

_(현재 등록된 스킬 없음)_

### templates/

다른 스킬이 골격 원본으로 사용하는 템플릿 모음. 직접 로드되지 않는다.

| 이름                                       | 설명                                                                                                                                                                                      |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [project-setup/](templates/project-setup/) | `project-setup` 스킬이 설치하는 작업 문서 8종(CLAUDE·PROJECT_OVERVIEW·SOURCE_MAP·DB_SCHEMA·DEPLOY·DESIGN·ADR·LESSONS) + 스킬 3종(manage-skills·verify-implementation·update-project-docs) |
| [rules/](templates/rules/)                 | 외부 가이드라인 사본 (Boris Cherny CLAUDE.md 패턴, Karpathy guidelines)                                                                                                                   |
