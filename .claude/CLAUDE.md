# agent-toolkit

> 개인용 Claude Code plugin. AI 에이전트를 일상적으로 쓰는 데 필요한 자산(초반은 skills 중심, 향후 hooks·agents·commands도 가능)을 한 곳에 모은다.

## 정체성

- **개인 큐레이션 베이스** — 직접 만든 것, 외부 OSS에서 가져와 다듬은 것, 실험 중인 것까지 자유롭게 담는다.
- **단일 plugin, 다중 자산** — Claude Code가 지원하는 자산 종류(`skills/`, `agents/`, `hooks/`, `commands/`)를 한 plugin 안에 섞어 담는다.
- **공통 스킬 루트** — Claude Code와 Codex 모두 이 저장소의 `skills/`만 플러그인 스킬 루트로 읽는다.
- **재배포 미고려** — 로컬 directory marketplace(`agent-toolkit-local`)로만 사용.
- **편한 게 우선** — 필요하면 추가하고, 안 맞으면 지운다. 단, 로더 구조는 단순하게 유지한다.

## 디렉토리 구조

```text
agent-toolkit/
├── .claude-plugin/
│   ├── plugin.json         # Claude Code plugin 메타
│   └── marketplace.json    # 로컬 marketplace 메타
├── .codex-plugin/
│   └── plugin.json         # Codex plugin 메타
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

필수 frontmatter:

```yaml
---
name: skill-name
description: 언제 이 스킬을 써야 하는지 검색 가능한 문장으로 설명
---
```

`description`이 실제 trigger surface다. 사용자가 말할 법한 문구, 제외 조건, 우선순위를 이 필드에 구체적으로 넣는다.

## 등록 상태

`~/.claude/settings.json`:

- `extraKnownMarketplaces.agent-toolkit-local` (directory source → 이 디렉토리)
- `enabledPlugins["agent-toolkit@agent-toolkit-local"]: true`

Claude Code의 plugin manifest와 Codex의 plugin manifest는 모두 `skills/`를 스킬 루트로 가리켜야 한다.

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
