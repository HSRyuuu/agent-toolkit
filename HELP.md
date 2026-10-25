# agent-toolkit 도움말

이 저장소(`hsryuuu` marketplace)에서 **어떤 스킬이 있고, 지금 하려는 일에 무엇을 쓰면 되는지** 찾는 안내서다.
설치 방법은 [docs/how-to-install.md](docs/how-to-install.md), 스킬 전체 목록과 원문 description은 [docs/catalog.md](docs/catalog.md)를 본다.

스킬은 플러그인 단위로 설치한다.

```text
/plugin install <plugin>@hsryuuu
```

설치한 스킬의 호출 이름은 `<plugin>:<skill>`이다. 이름이 같으면 `kb:kb`처럼 쓴다. 스킬은 대부분 description에 맞는 말을 하면 자동으로 선택된다.

## 하려는 일로 찾기

| 하려는 일 | 쓸 스킬 (플러그인) |
|---|---|
| 지식을 저장소(KB)에 저장하거나 찾기 | `kb` |
| 오늘 한 일을 세션 기록에서 일일 업무 로그로 정리 | `daily-work-log` |
| 이 대화를 다른 에이전트가 이어받을 인계 문서로 압축 | `handoff` |
| 계획이나 결정을 집요하게 질문받으며 검증 | `grill-me` |
| 결과가 왜 그렇게 나왔는지 가설을 경쟁시켜 원인 추적 | `trace` |
| 커밋, 커밋 분리, PR, 충돌 해결, rebase | `git-actions` |
| 현재 브랜치 변경을 사람이 보기 쉬운 단일 HTML로 리뷰 | `diff-review` |
| 서비스·API·DB 구조를 마우스오버 팝업이 있는 HTML 지도로 | `archify-html` (`html-tools`) |
| DB 스키마(DBML·DDL)를 정적 HTML 뷰어로 | `html-db-schema-viewer-creator` (`html-tools`) |
| PRD·테이블 목록에서 Mermaid ERD(개념/논리/물리) | `create-mermaid-erd` |
| 백엔드 소스에서 프론트·QA 전달용 REST API 명세서 | `api-spec-docs` |
| 프론트 소스에서 화면별 기능 정의서 | `ui-feature-spec-docs` |
| 기능 정의서·시나리오로 브라우저 UI 점검 | `ui-test-runner` |
| 테스트 시나리오·결과를 단위테스트 산출물 Excel로 | `excel-ui-test-doc-creator` (`excel-docs`) |
| 양식 기반 기존 Excel(인터페이스 정의서 등) 갱신 | `excel-doc-updater` (`excel-docs`) |
| 한국 SI 프로젝트 산출물(요구사항·설계서 등) 원문 Markdown | `si-project-docs` (`project-setup`) |
| 남이 읽을 Markdown 문서(보고서·공지·정리) 쓰기 | `docs-writing` (`writing-tools`) |
| 웹 UI 문구(버튼·에러·빈 화면 메시지) 쓰기·리뷰 | `ux-writing` (`writing-tools`) |
| 내 블로그 말투로 글 쓰기 | `dev-blog-writing-hsryuuu` (`personal-tools`) |
| 코드 설명·개념 학습 (직접 `/dev-teacher`로만 호출) | `dev-teacher` |
| Slack 메시지 검색·요약·멘션 정리·메시지 전송 | `slack-helper` |
| Jira·Confluence 티켓 조회·문서 확인 | `atlassian-helper` |
| Datadog 로그·APM 조회 | `datadog-helper` |
| Postman 엔드포인트·컬렉션 조회 | `postman-helper` |
| 프롬프트 조각을 CLAUDE.md·AGENTS.md에 넣기 | `prompt-composer` (`prompt-tools`) |
| 낡은 프롬프트·CLAUDE.md를 최신 모델 기준으로 진단 | `prompt-modernizer` (`prompt-tools`) |
| 스킬을 새로 쓰거나 점검·다이어트 | `writing-great-skill` (`prompt-tools`) |
| 새 프로젝트에 에이전트 진입점·문서·로컬 스킬 세팅 | `setup-*` (`project-setup`) |
| 로컬 plugin·marketplace 만들기·등록·갱신 | `local-plugin-manager` |

## 플러그인별 구성

플러그인 이름과 스킬 이름이 같은 것은 스킬 하나짜리 플러그인이다.

### 묶음 플러그인

| 플러그인 | 스킬 |
|---|---|
| `project-setup` | `setup-agent-entrypoint`, `setup-codebase-context-map`, `setup-project-docs`, `setup-project-level-agent-skill`, `setup-project-setting-recommend`, `setup-self-improvement-loop`, `si-project-docs`, `update-project-docs` |
| `html-tools` | `archify-html`, `html-db-schema-viewer-creator` |
| `excel-docs` | `excel-doc-updater`, `excel-ui-test-doc-creator` |
| `prompt-tools` | `prompt-composer`, `prompt-modernizer`, `writing-great-skill` (+ `snippets/`) |
| `writing-tools` | `docs-writing`, `ux-writing` |
| `personal-tools` | `dev-blog-writing-hsryuuu` |

### 단독 플러그인

- **연동:** `slack-helper`, `atlassian-helper`, `datadog-helper`, `postman-helper`
- **작업 흐름:** `kb`, `daily-work-log`, `handoff`, `grill-me`, `trace`, `git-actions`, `dev-teacher`
- **시각화·문서 생성:** `diff-review`, `create-mermaid-erd`, `api-spec-docs`, `ui-feature-spec-docs`
- **검증·운영:** `ui-test-runner`, `local-plugin-manager`

## 설치 없이 이 저장소에서만 쓰는 스킬

`.claude/skills/`(Claude Code)와 `.codex/skills/`(Codex)에 있는 로컬 스킬이다. 플러그인이 아니어서 설치되지 않는다.

| 스킬 | 언제 |
|---|---|
| `verify-secrets` | 커밋·push·PR·릴리스 전에 회사 식별자와 secret이 섞였는지 검사 (필수) |
| `sync-docs` | 스킬·plugin·구조를 바꾼 뒤 README, HELP, catalog 등 설명 문서를 맞출 때 |
| `publish-agent-toolkit` | "배포해줘"처럼 명시적으로 요청할 때만. 검증→커밋→버전 범프→push→업데이트 |

## 보관된 스킬

더 이상 배포하지 않는 스킬은 `old/`에 있다. marketplace에 등록되어 있지 않아 설치되지 않는다. 목록은 [old/README.md](old/README.md)를 본다.

## 없는 스킬이 필요할 때

`writing-great-skill`로 새 스킬을 설계하고, `plugins/<plugin>/skills/<name>/SKILL.md`에 만든 뒤 `sync-docs`로 문서를 맞춘다. 배포 절차는 [docs/how-to-install.md](docs/how-to-install.md)를 본다.
