# agent-toolkit

> 개인용 Claude Code / Codex plugin. AI 에이전트를 일상적으로 쓰는 데 필요한 자산(초반은 skills 중심, 향후 hooks·agents·commands도 가능)을 한 곳에 모은다.

## 정체성

- **개인 큐레이션 베이스** — 직접 만든 것, 외부 OSS에서 가져와 다듬은 것, 실험 중인 것까지 자유롭게 담는다.
- **단일 plugin, 다중 런타임** — Claude Code와 Codex가 각각 읽는 manifest를 함께 유지한다.
- **다중 자산** — `skills/`, `agents/`, `hooks/`, `commands/` 같은 agent 자산을 한 저장소에 모은다.
- **재배포 미고려** — 로컬 directory marketplace(`agent-toolkit-local`) 또는 개인 Codex marketplace로만 사용.
- **편한 게 우선** — 형식 강박 없음. 필요하면 추가하고, 안 맞으면 지운다.

## 디렉토리 구조

```
agent-toolkit/
├── .claude-plugin/
│   ├── plugin.json         # Claude Code plugin 메타
│   └── marketplace.json    # Claude Code 로컬 marketplace 메타
├── .codex-plugin/
│   └── plugin.json         # Codex plugin 메타
├── .agents/
│   └── plugins/
│       └── marketplace.json # Codex 로컬 marketplace 메타
├── plugins/
│   └── agent-toolkit -> ..  # Codex marketplace 표준 source path용 symlink
├── skills/                 # 독립 스킬 — 단일 목적, 다른 스킬에 의존 X
│   └── <name>/SKILL.md
│   └── <alias> -> ../skills-system|../forks/taste-skill/... # Codex 단일 루트 호환
├── skills-workflow/        # 워크플로우 스킬 — skills/의 것들을 조합/오케스트레이션
│   └── <name>/SKILL.md
├── skills-system/          # 메타·스캐폴딩 스킬 — project-setup, create-plugin 등
│   └── <name>/SKILL.md     #   "처음부터 구조를 세우는" 더 큰 작업
├── agents/                 # 필요해지면 추가
├── hooks/                  # 필요해지면 추가
├── commands/               # 필요해지면 추가
├── AGENTS.md               # Codex/agent 공통 작업 지침
└── .claude/CLAUDE.md       # Claude Code 작업 지침
```

## 스킬 분류 기준

새 스킬을 추가할 때 어디에 놓을지 결정하는 기준:

| 디렉토리 | 성격 | 판단 질문 |
|---|---|---|
| `skills/` | **독립 스킬** | 다른 스킬을 호출하지 않고 단독으로 한 가지 일을 끝내는가? |
| `skills-workflow/` | **워크플로우** | `skills/`의 여러 스킬을 묶어 순차/병렬로 돌리는가? |
| `skills-system/` | **메타·스캐폴딩** | 빈 곳에 프로젝트·플러그인·디렉토리 구조 자체를 세우는가? |

> 분류가 애매하면 `skills/`에 둔다. 나중에 묶음·스캐폴딩 성격이 명확해지면 옮긴다.

Claude Code manifest(`.claude-plugin/plugin.json`)는 `skills/`, `skills-workflow/`, `skills-system/`, `forks/taste-skill/`을 스킬 루트로 등록한다.

Codex manifest(`.codex-plugin/plugin.json`)는 단일 스킬 루트인 `skills/`를 등록한다. Codex에서 `skills-system/`과 `forks/taste-skill/`도 함께 보이도록 `skills/` 아래에 symlink alias를 둔다. 원본 디렉토리 구조는 사람의 분류 기준과 Claude Code manifest를 위해 유지한다.

## 등록 상태

Claude Code:
- `.claude-plugin/marketplace.json`의 `agent-toolkit-local` marketplace를 등록한다.
- `agent-toolkit@agent-toolkit-local`을 설치한다.

Codex:
- `.agents/plugins/marketplace.json`의 `agent-toolkit-local` marketplace를 `codex plugin marketplace add <repo-root>`로 등록할 수 있다.
- `agent-toolkit@agent-toolkit-local`을 `codex plugin add agent-toolkit@agent-toolkit-local`로 설치할 수 있다.
- 개인 Codex marketplace(`~/.agents/plugins/marketplace.json`)에서 `~/plugins/agent-toolkit` symlink를 가리키는 경우 `agent-toolkit@personal`로도 설치할 수 있다.
