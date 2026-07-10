# KB Skills Guide

개인 Markdown Knowledge Base 스킬을 처음 사용하는 사람을 위한
시작점이다. 에이전트 실행 규칙은 `SKILL.md`와
`references/` 문서가 기준이다.

## 스킬 구성

| 스킬 | 용도 |
|---|---|
| `kb-manage` | 최초 설정, KB 루트 등록, 규칙, index/log 관리, 마이그레이션 |
| `kb-write` | 문서 생성, 추가, 병합, 정리 |
| `kb-search` | 읽기 전용 검색과 질의응답 |
| `kb-lint` | metadata, 링크, index/log, 보안 후보 점검 |

## 처음 사용할 때

현재 agent host가 네 KB 스킬을 이름으로 제공하는지 확인한 뒤 다음처럼
요청한다.

```text
kb-skills를 처음 설정해줘. 설정이 비어 있으면 ~/KnowledgeBase를 먼저 제안해줘.
Python과 python-frontmatter 사전 준비부터 smoke test까지 확인해줘.
```

최초 설정은 다음 흐름으로 진행한다.

1. Python 3.10+와 전용 `~/.venvs/agent-toolkit-kb` 확인
2. 사용자 확인 후 bundled requirements로 고정된 Python runtime 설치
3. `~/.config/kb/kb-config.json`에 KB 루트를 먼저 등록
4. 기본 제안은 `~/KnowledgeBase`; 사용자가 다른 절대 경로를 선택할 수 있음
5. `AGENTS.md`, `index.md`, `log.jsonl` 초기화
6. 루트 해석, index, 구조화 검색, lint smoke test

YAML frontmatter는 Markdown 맨 위의 `---` metadata 블록이다.
`python-frontmatter`는 이 블록을 읽는 Python 패키지이며, 설치명은
`python-frontmatter`, import 이름은 `frontmatter`다. 내부 YAML 파서는
`PyYAML`(import 이름 `yaml`)이며 두 패키지는 `scripts/requirements.txt`에
정확한 버전으로 함께 고정한다.

Homebrew/system Python에는 직접 설치하지 않는다. 모든 KB helper는 기본적으로
`~/.venvs/agent-toolkit-kb/bin/python`으로 실행한다.

전체 최초 설정 절차는
[`references/getting-started.md`](./references/getting-started.md)를 본다.

## 모든 설치는 확인 후 수행

패키지, runtime, virtual environment, skill 등록, clone,
download, `npx`, skill copy/symlink, enable, update, reinstall, remove는 모두
정확한 출처·명령·대상 경로·영향을 먼저 보여준 뒤 사용자 확인을 받아야
한다. 확인하지 않은 추가 의존성을 자동으로 설치하지 않는다.

## Obsidian 연동은 선택 사항

일반 KB 작업에는 Obsidian 스킬이 필요하지 않다. Obsidian Markdown,
Bases, JSON Canvas, Obsidian CLI 기능이 필요할 때만
[`kepano/obsidian-skills`](https://github.com/kepano/obsidian-skills)를
검토한다.

설치 전에 필요한 스킬이 현재 세션에 이미 있는지 확인한다. Claude Code
marketplace, `npx skills add`, Codex/Claude 수동 설치 방법과 별도 runtime
의존성은
[`references/obsidian-skills.md`](./references/obsidian-skills.md)를 본다.

## 상세 문서

- [`SKILL.md`](./SKILL.md) — 에이전트용 `kb-manage` 실행 규칙
- [`references/getting-started.md`](./references/getting-started.md) — 최초 설정과 검증
- [`references/conventions.md`](./references/conventions.md) — 네 KB 스킬의 공통 규칙
- [`references/obsidian-skills.md`](./references/obsidian-skills.md) — 선택적 Obsidian 설치와 사용 경계
