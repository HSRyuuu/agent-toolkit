# KB Skill Guide

개인 또는 업무용 Markdown Knowledge Base 스킬을 처음 사용하는 사람을 위한
시작점이다. 에이전트 실행 규칙은 `SKILL.md`와
`references/` 문서가 기준이다.

## 모드 구성

| 모드 | 용도 |
|---|---|
| manage | 최초 설정, KB 루트 등록, 규칙, index/log 관리, 마이그레이션 |
| write | 문서 생성, 추가, 병합, 정리 |
| search | 읽기 전용 검색과 질의응답 |
| lint | metadata, 링크, index/log, 보안 후보 점검 |

## 처음 사용할 때

현재 agent host가 `kb` 스킬을 제공하는지 확인한 뒤 다음처럼
요청한다.

```text
kb를 처음 설정해줘. 설정이 비어 있으면 ~/KnowledgeBase를 먼저 제안해줘.
Python과 python-frontmatter 사전 준비부터 smoke test까지 확인해줘.
```

최초 설정은 다음 흐름으로 진행한다.

1. Python 3.10+와 전용 `~/.venvs/agent-toolkit-kb` 확인
2. 사용자 확인 후 bundled requirements로 고정된 Python runtime 설치
3. `~/.config/kb/kb-config.json`에 KB 루트를 먼저 등록
4. 기본 제안은 `~/KnowledgeBase`; 사용자가 다른 절대 경로를 선택할 수 있음
5. `AGENTS.md`, `index.md` 초기화 (`log.jsonl`은 non-git KB에서만 기본 생성)
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

- [`SKILL.md`](./SKILL.md) — 에이전트용 `kb` 모드 라우터
- [`references/getting-started.md`](./references/getting-started.md) — 최초 설정과 검증
- [`references/conventions.md`](./references/conventions.md) — 네 모드의 공통 규칙
- [`references/obsidian-skills.md`](./references/obsidian-skills.md) — 선택적 Obsidian 설치와 사용 경계

## 검색과 품질 확인

메타데이터 검색은 `scripts/kb_meta_search.py <root> --query <terms>`로 실행한다.
본문 식별자나 빠진 근거는 `--content`로 찾고, 초안·과거 기록은 `--scope all`로
추가한다. 기본 검색은 maintained/unspecified 문서이며 개인·gitignore·숨김
영역과 운영 안내문을 제외한다. 운영 규칙은 `--include-guidance`로 조회한다.

선택 필드 `status`는 maintained/draft/historical이다. 없는 문서는 unspecified로
표시한다. 상태를 필수로 정한 KB는 `kb_lint.py <root> --require-status`를 사용한다.
변경 파일 검사는 `--files <paths>`로 범위를 좁힌다. 이동·삭제 후에는 전체 검사와
유입 링크 확인을 수행한다. Inbox·archive는 최소 메타데이터·상태·링크를 점검한다.

검색 중 파싱 실패는 유효한 결과와 함께 경로만 보고하고 exit 2를 반환한다.
인덱스 생성은 파싱 실패 시 쓰기를 중단한다. 문서 저장 후 실제 질문 두 개로
검색을 확인한다. `scripts/test_kb_quality.py`가 이 동작을 회귀 검증한다.
