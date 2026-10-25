# agent-toolkit

> 개인용 Claude Code / Codex plugin marketplace(`hsryuuu`). AI 에이전트를 일상적으로 쓰는 데 필요한 자산(초반은 skills 중심, 향후 hooks·agents·commands도 가능)을 한 곳에 모으고, 플러그인 단위로 골라 설치한다.

## 정체성

- **개인 큐레이션 베이스** — 직접 만든 것, 외부 OSS에서 가져와 다듬은 것, 실험 중인 것까지 자유롭게 담는다.
- **스킬(묶음)당 plugin 하나** — 관련 스킬은 한 plugin에 묶어 함께 설치하고(`coding-convention`, `project-setup`, `html-tools`, `excel-docs`, `prompt-tools`, `writing-tools`), 개인 전용 스킬은 `personal-tools`에 모으며, 나머지는 스킬 하나가 plugin 하나다. 버전도 plugin별로 독립이다.
- **공통 plugin 트리** — Claude Code와 Codex 모두 이 저장소의 `plugins/<name>/`을 읽는다.
- **두 가지 설치 경로** — marketplace 이름은 `hsryuuu`. 개발 머신은 로컬 directory marketplace, 그 외 머신은 GitHub marketplace(`HSRyuuu/agent-toolkit`)로 설치한다. 한 머신에는 한 방식만 쓴다. plugin은 `/plugin install <plugin>@hsryuuu`로 개별 설치한다.
- **편한 게 우선** — 필요하면 추가하고, 안 맞으면 지운다. 단, 로더 구조는 단순하게 유지한다.

## 디렉토리 구조

```text
agent-toolkit/
├── .claude-plugin/marketplace.json   # Claude Code marketplace
├── .agents/plugins/marketplace.json  # Codex marketplace
├── .claude/skills/
│   ├── verify-secrets/     # 이 저장소 전용 로컬 검증 스킬
│   └── publish-agent-toolkit/   # 검증→커밋→푸시→배포 라우터
├── .codex/skills/          # 위 두 스킬의 Codex 사본
├── plugins/<plugin>/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   ├── skills/<skill>/SKILL.md
│   └── templates/          # 그 plugin 스킬이 쓰는 템플릿 (project-setup만)
├── scripts/bump-plugin.sh  # plugin 하나의 두 manifest 버전을 함께 올린다
├── templates/rules/        # 외부 가이드라인 사본
├── docs/
│   ├── catalog.md          # plugin·skill 카탈로그
│   └── how-to-install.md   # 설치·업데이트·배포·문제 해결
└── .claude/CLAUDE.md       # 이 파일
```

## 스킬 관리 기준

새 스킬은 `plugins/<plugin>/skills/<name>/SKILL.md`에 둔다. 독립 스킬이면 plugin을 새로 만들고(두 manifest + 두 marketplace 항목, 시작 버전 `1.0.0`), 기존 묶음에 속하면 그 plugin 안에 넣는다. 스킬은 자기 plugin 폴더 안에서 자급자족해야 한다. 다른 plugin이나 저장소 루트 파일을 참조하지 않는다.

`SKILL.md`가 없는 디렉토리는 공유 자산으로만 취급한다. 카탈로그와 inventory에는 넣지 않는다.

## 필수 로컬 검증

- 커밋, push, PR, release 전에는 반드시 프로젝트 로컬 `verify-secrets` 스킬을 실행한다.
- Claude Code는 `.claude/skills/verify-secrets/`, Codex는 `.codex/skills/verify-secrets/`를 사용한다.
- 이 스킬은 회사 식별자, secret, token, API key, private value, few-shot 예시의 민감값 유입을 막는 최종 게이트다.
- `verify-secrets`가 하나라도 이슈를 보고하면 커밋하지 않는다. 수정하거나 사용자의 명시적 예외 승인을 받은 뒤 재검증한다.
- 이 로컬 검증 스킬은 플러그인 배포용 `plugins/`로 옮기지 않는다. 로컬 검증 스킬의 회사/secret 예시는 `plugins/` 아래 어떤 파일에도 복사하지 않는다.

## 배포

검증부터 배포까지는 프로젝트 로컬 `publish-agent-toolkit` 스킬이 소유한다 — 문서 동기화 → verify-secrets → 커밋 → 바뀐 plugin의 두 manifest 버전 동시 범프(`scripts/bump-plugin.sh`) → push(`plugins/` 변경은 plugin 단위 PR, 제목 앞에 `[vX.Y.Z]`, 바로 머지해도 됨 / 그 밖은 `main`에 바로 push) → 설치 플러그인 업데이트. 어느 단계든 실패하면 멈춘다. 범프 기준은 repo 대격변 = major, 스킬 추가·삭제 = minor, 스킬 수정 = patch.

두 호스트 모두 plugin별 `version`을 캐시 키로 쓰므로 범프 없는 push는 설치된 머신에서 아무 변화가 없다. 호스트 CLI 명령, 캐시 경로, 문제 해결은 `docs/how-to-install.md`에 있다.

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
- `enabledPlugins["<plugin>@hsryuuu"]: true` — 쓰는 plugin마다 하나씩

다른 머신은 `/plugin marketplace add HSRyuuu/agent-toolkit` + `/plugin install <plugin>@hsryuuu`로 설치한다 (README 참고).

각 plugin의 Claude/Codex manifest는 같은 `version`을 가져야 한다 (버전이 캐시 키다). `marketplace.json`의 `plugins[]`에는 version을 두지 않는다.

## 문서 갱신

스킬을 추가·이동·삭제했거나 manifest를 바꿨으면 `update-project-docs` 스킬로 다음 파일을 함께 맞춘다.

- `README.md`
- `docs/catalog.md`
- `AGENTS.md`
- `.claude/CLAUDE.md`

카탈로그는 다음 inventory를 기준으로 생성한다.

```bash
find plugins -mindepth 4 -maxdepth 4 -path '*/skills/*' -name SKILL.md -print | sort
```
