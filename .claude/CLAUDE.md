# agent-toolkit

> 개인용 Claude Code plugin. AI 에이전트를 일상적으로 쓰는 데 필요한 자산(초반은 skills 중심, 향후 hooks·agents·commands도 가능)을 한 곳에 모은다.

## 정체성

- **개인 큐레이션 베이스** — 직접 만든 것, 외부 OSS에서 가져와 다듬은 것, 실험 중인 것까지 자유롭게 담는다.
- **단일 plugin, 다중 자산** — Claude Code가 지원하는 자산 종류(`skills/`, `agents/`, `hooks/`, `commands/`)를 한 plugin 안에 섞어 담는다.
- **재배포 미고려** — 로컬 directory marketplace(`agent-toolkit-local`)로만 사용.
- **편한 게 우선** — 형식 강박 없음. 필요하면 추가하고, 안 맞으면 지운다.

## 디렉토리 구조

```
agent-toolkit/
├── .claude-plugin/
│   ├── plugin.json         # plugin 메타
│   └── marketplace.json    # 로컬 marketplace 메타
├── skills/                 # 독립 스킬 — 단일 목적, 다른 스킬에 의존 X
│   └── <name>/SKILL.md
├── skills-workflow/        # 워크플로우 스킬 — skills/의 것들을 조합/오케스트레이션
│   └── <name>/SKILL.md
├── skills-system/          # 메타·스캐폴딩 스킬 — project-setup, create-plugin 등
│   └── <name>/SKILL.md     #   "처음부터 구조를 세우는" 더 큰 작업
├── agents/                 # 필요해지면 추가
├── hooks/                  # 필요해지면 추가
├── commands/               # 필요해지면 추가
└── .claude/CLAUDE.md       # 이 파일
```

## 스킬 분류 기준

새 스킬을 추가할 때 어디에 놓을지 결정하는 기준:

| 디렉토리 | 성격 | 판단 질문 |
|---|---|---|
| `skills/` | **독립 스킬** | 다른 스킬을 호출하지 않고 단독으로 한 가지 일을 끝내는가? |
| `skills-workflow/` | **워크플로우** | `skills/`의 여러 스킬을 묶어 순차/병렬로 돌리는가? |
| `skills-system/` | **메타·스캐폴딩** | 빈 곳에 프로젝트·플러그인·디렉토리 구조 자체를 세우는가? |

> 분류가 애매하면 `skills/`에 둔다. 나중에 묶음·스캐폴딩 성격이 명확해지면 옮긴다.

`plugin.json`의 `skills` 배열에 세 디렉토리가 모두 등록되어 있어, Claude Code는 위치와 무관하게 모두 로드한다. 디렉토리 구분은 **사람이 관리하기 쉬우라고** 둔 것.

## 등록 상태

`~/.claude/settings.json`:
- `extraKnownMarketplaces.agent-toolkit-local` (directory source → 이 디렉토리)
- `enabledPlugins["agent-toolkit@agent-toolkit-local"]: true`
