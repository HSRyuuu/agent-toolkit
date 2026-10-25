---
name: sync-docs
description: Use after changing this repository's plugins, skills, manifests, marketplace files, scripts, or structure, and before committing or publishing, so every document that describes the repo matches the files. Also use for "문서 동기화", "문서 맞춰줘", "sync docs", "catalog 갱신", "HELP 갱신", "스킬 추가했어", "스킬 옮겼어". Do NOT use for editing a single skill's own body.
---

# Sync Docs

이 저장소(agent-toolkit)를 설명하는 문서가 실제 파일과 어긋나지 않게 맞춘다. 기준은 항상 **실제 파일**이다. 문서끼리 맞추지 않는다.

## 대상 문서

| 문서 | 독자 | 무엇을 맞추나 |
|---|---|---|
| `README.md` | 처음 여는 사람 | 소개, 설치 링크, 플러그인 묶음 표, 갱신 안내 |
| `HELP.md` | 스킬을 찾는 사람 | 의도별 표, 플러그인별 구성, 로컬 스킬, 보관 스킬 안내 |
| `docs/catalog.md` | 사람 + 검색 | 스킬 한 줄당 한 행, 개수, 링크 |
| `docs/how-to-install.md` | 설치·배포하는 사람 | 호스트 CLI 명령, 캐시 규칙 (명령이 바뀐 경우만) |
| `AGENTS.md` | Codex 등 공통 에이전트 | 구조 트리, WHERE TO LOOK, CODE MAP, 규칙 |
| `.claude/CLAUDE.md` | Claude Code | 정체성, 디렉토리 구조, 규칙 |
| `old/README.md` | 보관 스킬을 찾는 사람 | 폴더별 스킬 목록과 보관 사유 |
| manifest·marketplace | 호스트 | plugin 이름·version 일치, marketplace와 `plugins/` 1:1 |

`docs/kb-skill-improvement-plan.md` 같은 개별 계획 문서는 대상이 아니다.

## 워크플로우

### 1. 검사

repo 루트에서 읽기 전용 검사를 돌린다.

```bash
python3 .codex/skills/sync-docs/scripts/check_docs.py
```

출력은 `[분류] 설명` 한 줄씩이고, 문제가 없으면 `OK` 한 줄이다. 분류는 `marketplace` `manifest` `version` `skill` `catalog` `help` `path` `old` `local` `doc` `json`이다.

검사가 보지 못하는 것은 다음 단계에서 사람이 읽고 확인한다.

### 2. 문서별로 고친다

문제가 나온 문서만 열어 틀린 사실을 좁게 고친다. 의도적인 정책 변화가 없으면 문장 전체를 다시 쓰지 않는다.

- **`docs/catalog.md`**
  - 스킬마다 한 행: `플러그인 | 링크 | name | description 요약`. 정렬은 플러그인명, 스킬명 순이다.
  - description 요약은 frontmatter에서 "무엇을 하는지"만 뽑고 호출 문구는 줄인다.
  - 요약 표의 plugin·skill 개수와 `Last updated`를 맞춘다.
- **`HELP.md`**
  - 새 스킬은 "하려는 일로 찾기" 표와 "플러그인별 구성"에 둘 다 넣는다. 삭제·이동한 스킬은 두 곳에서 모두 뺀다.
  - 한 줄 설명은 SKILL.md `description`에 근거한다. 근거 없는 추천 문구를 지어내지 않는다.
  - 개수는 적지 않는다(catalog가 소유한다).
- **`README.md`**: "플러그인 묶음" 표는 여러 스킬을 가진 plugin만 적는다. 나머지는 이름이 같은 1:1 plugin이라고 한 줄로 둔다.
- **`AGENTS.md`, `.claude/CLAUDE.md`**: 두 파일은 같은 저장소 사실을 말한다. 구조 트리, 묶음 plugin 이름, 로컬 스킬 목록, CODE MAP의 스크립트 경로를 실제와 맞춘다. 생성 시각·커밋 해시 같은 금방 낡는 값은 적지 않는다.
- **`old/README.md`**: `old/` 아래 폴더마다 포함 스킬과 비고를 적는다. 스킬을 옮겼으면 폴더 표에 반영한다.
- **manifest·marketplace**: 범위 밖이면 고치지 않고 보고만 한다. plugin을 새로 만든 작업이면 두 manifest(같은 version, 시작 `1.0.0`)와 두 marketplace 항목을 추가한다. `.claude-plugin/marketplace.json`의 `plugins[]`에는 `version`을 두지 않는다.

### 3. 로컬 스킬 사본

`.codex/skills/<name>/`을 바꿨으면 `.claude/skills/<name>/`에 같은 내용을 반영한다. 호스트 이름과 경로가 나오는 문장만 다르다.

### 4. 재검사

```bash
python3 .codex/skills/sync-docs/scripts/check_docs.py
jq empty .claude-plugin/marketplace.json .agents/plugins/marketplace.json plugins/*/.claude-plugin/plugin.json plugins/*/.codex-plugin/plugin.json
```

`OK`가 나올 때까지 반복한다. 같은 항목이 두 번 연속 풀리지 않으면 멈추고 이유를 보고한다.

### 5. 보고

고친 문서와 이유를 한 줄씩, 검사 마지막 출력, 고치지 않고 남긴 항목을 보고한다.

## 새로운 종류의 어긋남을 만났을 때

사람이 읽다가 검사가 놓친 어긋남(문서가 사라진 기능을 설명하는 경우 등)을 발견하면 그 자리에서 고치고, 반복될 만하면 `scripts/check_docs.py`에 검사를 추가한다. 이 스킬이 시간이 갈수록 더 많이 잡게 하는 방법이다.

## 하지 말 것

- 문서를 보고 문서를 고치지 않는다. 항상 `plugins/`와 manifest의 실제 상태를 먼저 확인한다.
- `old/`의 스킬을 현재 plugin처럼 `README.md`, `HELP.md`, `docs/catalog.md`에 올리지 않는다.
- 이 스킬과 검사 스크립트를 `plugins/`로 옮기지 않는다. 로컬 전용이며 `docs/catalog.md`에도 올리지 않는다.
- 범위 밖 manifest를 임의로 바꾸지 않는다.
