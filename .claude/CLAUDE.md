# agent-toolkit

> 개인용 Claude Code plugin. AI 에이전트를 일상적으로 쓰는 데 필요한 자산(초반은 skills 중심, 향후 hooks·agents·commands도 가능)을 한 곳에 모은다.

## 정체성

- **개인 큐레이션 베이스** — 직접 만든 것, 외부 OSS에서 가져와 다듬은 것, 실험 중인 것까지 자유롭게 담는다.
- **단일 plugin, 다중 자산** — Claude Code가 지원하는 자산 종류(`skills/`, `agents/`, `hooks/`, `commands/`)를 한 plugin 안에 섞어 담는다.
- **공통 스킬 루트** — Claude Code와 Codex 모두 이 저장소의 `skills/`만 플러그인 스킬 루트로 읽는다.
- **두 가지 설치 경로** — marketplace 이름은 `hsryuuu`. 개발 머신은 로컬 directory marketplace, 그 외 머신은 GitHub marketplace(`HSRyuuu/agent-toolkit`)로 설치한다. 한 머신에는 한 방식만 쓴다.
- **편한 게 우선** — 필요하면 추가하고, 안 맞으면 지운다. 단, 로더 구조는 단순하게 유지한다.

## 디렉토리 구조

```text
agent-toolkit/
├── .claude-plugin/
│   ├── plugin.json         # Claude Code plugin 메타
│   └── marketplace.json    # 로컬 marketplace 메타
├── .claude/skills/
│   └── verify-secrets/     # 이 저장소 전용 로컬 검증 스킬
├── .codex-plugin/
│   └── plugin.json         # Codex plugin 메타
├── .codex/skills/
│   └── verify-secrets/     # 이 저장소 전용 로컬 검증 스킬
├── .agents/plugins/
│   └── marketplace.json    # Codex 로컬 marketplace 메타
├── skills/                 # 단일 활성 plugin skill root
│   └── <name>/SKILL.md
├── templates/              # 스킬이 대상 프로젝트에 복사하거나 참고하는 템플릿
├── docs/
│   └── catalog.md          # skills inventory에서 생성한 사람용 카탈로그
└── .claude/CLAUDE.md       # 이 파일
```

## 스킬 관리 기준

새 스킬을 추가할 때는 `skills/<name>/SKILL.md`에 둔다. 스킬이 워크플로우형인지, 스캐폴딩형인지, 디자인형인지는 문서와 frontmatter 설명으로 표현한다. 디렉토리는 플러그인 로딩 경계가 아니라 개별 스킬의 물리 위치다.

`SKILL.md`가 없는 디렉토리는 공유 자산으로만 취급한다. 카탈로그와 inventory에는 넣지 않는다.

## 필수 로컬 검증

- 커밋, push, PR, release 전에는 반드시 프로젝트 로컬 `verify-secrets` 스킬을 실행한다.
- Claude Code는 `.claude/skills/verify-secrets/`, Codex는 `.codex/skills/verify-secrets/`를 사용한다.
- 이 스킬은 회사 식별자, secret, token, API key, private value, few-shot 예시의 민감값 유입을 막는 최종 게이트다.
- `verify-secrets`가 하나라도 이슈를 보고하면 커밋하지 않는다. 수정하거나 사용자의 명시적 예외 승인을 받은 뒤 재검증한다.
- 이 로컬 검증 스킬은 플러그인 배포용 `skills/`로 옮기지 않는다. 로컬 검증 스킬의 회사/secret 예시는 `skills/` 아래 어떤 파일에도 복사하지 않는다.

필수 frontmatter:

```yaml
---
name: skill-name
description: 언제 이 스킬을 써야 하는지 검색 가능한 문장으로 설명
---
```

`description`이 실제 trigger surface다. 사용자가 말할 법한 문구, 제외 조건, 우선순위를 이 필드에 구체적으로 넣는다.

## 등록 상태

`~/.claude/settings.json` (개발 머신 기준):

- `extraKnownMarketplaces.hsryuuu` (directory source → 이 디렉토리)
- `enabledPlugins["agent-toolkit@hsryuuu"]: true`

다른 머신은 `/plugin marketplace add HSRyuuu/agent-toolkit` + `/plugin install agent-toolkit@hsryuuu`로 설치한다 (README 참고).

Claude Code의 plugin manifest와 Codex의 plugin manifest는 모두 `skills/`를 스킬 루트로 가리켜야 한다. GitHub 설치 사용자에게 변경을 전달하려면 두 plugin manifest의 `version`을 같은 값으로 올려야 한다 (버전이 캐시 키다). `marketplace.json`의 `plugins[]`에는 version을 두지 않는다.

## 문서 갱신

스킬을 추가·이동·삭제했거나 manifest를 바꿨으면 `update-project-docs` 스킬로 다음 파일을 함께 맞춘다.

- `README.md`
- `docs/catalog.md`
- `AGENTS.md`
- `.claude/CLAUDE.md`

카탈로그는 다음 inventory를 기준으로 생성한다.

```bash
find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort
```
