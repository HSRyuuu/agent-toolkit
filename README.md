# agent-toolkit

> 개인용 Claude Code plugin. 일상 워크플로우에 쓰는 스킬을 한 곳에 모은다.

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

| 이름 | 설명 |
|---|---|
| [agent-harness-construction](skills/agent-harness-construction/SKILL.md) | AI 에이전트의 action space·tool 정의·observation 포맷을 완료율 기준으로 설계·최적화 |
| [agent-introspection-debugging](skills/agent-introspection-debugging/SKILL.md) | 반복 실패하는 에이전트 런을 캡처·진단·격리 복구하고 자기진단 보고서 작성 |
| [fastapi-guide](skills/fastapi-guide/SKILL.md) | FastAPI 프로덕션 API 모범 사례 — async/sync, Pydantic, DI, 배포 |
| [git-master](skills/git-master/SKILL.md) | 원자적 커밋·rebase·히스토리 관리 (저장소 커밋 스타일 자동 감지) |
| [node-backend-patterns](skills/node-backend-patterns/SKILL.md) | Node·Express·Next.js API 라우트 백엔드 아키텍처·DB·캐싱 패턴 |
| [prompt-master](skills/prompt-master/SKILL.md) | LLM 프롬프트 엔지니어링 — 전략 선택 + 작성 기법, 서브에이전트 오케스트레이션 |
| [rest-api-design](skills/rest-api-design/SKILL.md) | REST API 설계 — 리소스 네이밍, 상태 코드, 페이지네이션, 에러 응답, 버전 관리 |
| [springboot-java-standards](skills/springboot-java-standards/SKILL.md) | Java 17+ 코딩 표준 + Spring Boot 가이드 (JPA/QueryDSL reference 별도) |
| [springboot-kotlin-standards](skills/springboot-kotlin-standards/SKILL.md) | Kotlin + Spring Boot 코딩 표준 — null safety, data class, 확장 함수 |
| [test-sync-verifier](skills/test-sync-verifier/SKILL.md) | 코드 변경 후 테스트 검증 — 테스트 코드만 수정, 프로덕션은 리포트만 |

### skills-system/

빈 곳에 프로젝트·플러그인·디렉토리 구조 자체를 세우는 메타·스캐폴딩 작업.

| 이름 | 설명 |
|---|---|
| [create-claude-plugin](skills-system/create-claude-plugin/SKILL.md) | 새 로컬 Claude Code 플러그인 스캐폴딩 + marketplace 등록·로드 검증 |
| [project-setup](skills-system/project-setup/SKILL.md) | 대상 프로젝트에 검증 스킬·작업 문서 골격을 메뉴 선택형으로 설치 |
| [recommend-project-setting](skills-system/recommend-project-setting/SKILL.md) | 진행 중 프로젝트의 누락 자산을 read-only로 추천, 명시 요청 시에만 설치 |

### skills-workflow/

`skills/`의 여러 스킬을 묶어 순차/병렬로 돌리는 오케스트레이션 스킬.

_(현재 등록된 스킬 없음)_

### templates/

다른 스킬이 골격 원본으로 사용하는 템플릿 모음. 직접 로드되지 않는다.

| 이름 | 설명 |
|---|---|
| [project-setup/](templates/project-setup/) | `project-setup` 스킬이 설치하는 작업 문서 7종(CLAUDE·PROJECT_OVERVIEW·SOURCE_MAP·DB_SCHEMA·DEPLOY·DESIGN·LESSONS) + 스킬 3종(manage-skills·verify-implementation·update-project-docs) |
| [rules/](templates/rules/) | 외부 가이드라인 사본 (Boris Cherny CLAUDE.md 패턴, Karpathy guidelines) |
