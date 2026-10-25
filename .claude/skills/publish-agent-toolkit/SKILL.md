---
name: publish-agent-toolkit
description: Use only when the user explicitly asks to publish or release this repository — "/publish-agent-toolkit", "배포해줘", "커밋하고 푸시하고 배포해줘", "publish", "릴리스해줘". Runs verify-secrets, commit, version bump, push (a per-plugin `[vX.Y.Z]` PR, optionally merged right away, when `plugins/` changed; direct push to main otherwise), and the plugin update commands in one order. Do NOT infer it from a plain "commit" or "push" request.
---

# Publish Workflow

이 저장소의 작업을 검증부터 배포까지 한 번에 돌린다.

두 호스트 모두 플러그인 `version`을 캐시 키로 쓴다. 그래서 **push만으로는 설치된
머신에 아무 변화가 없고, 버전 범프가 곧 릴리스다.** 배경과 캐시 경로는
[`docs/how-to-install.md`](../../../docs/how-to-install.md).

## PR 규칙

**`plugins/` 아래 스킬·manifest가 바뀐 경우에만** 아래 PR 경로를 쓴다. 그 밖의 변경(저장소 문서, 로컬 전용 스킬,
스크립트)은 버전 범프도 PR도 없이 5단계에서 `main`에 바로 push한다.

- **plugin 단위로 PR을 올린다.** PR 하나는 plugin 하나의 변경만 담는다. 여러 plugin을 바꿨으면
  plugin마다 브랜치·커밋·PR을 나눈다 (버전도 plugin별로 독립이다).
- **PR 제목 맨 앞에 `[v<새버전>]`을 붙인다.** 예: `[v1.2.3] fix(slack-helper): DM 조회 오류 수정`.
  버전은 4단계에서 올린 그 plugin의 새 버전이고, 괄호 뒤는 저장소의 커밋 메시지 스타일이다.
- **PR을 올리고 바로 main에 머지해도 된다.** 5단계에서 사용자가 고른다.

## 선행 조건

먼저 확인한다. 하나라도 어긋나면 멈추고 이유를 보고한다.

```bash
jq -r '.name' .claude-plugin/marketplace.json   # hsryuuu 여야 한다
git branch --show-current
git status --short
```

- push 대상은 `origin main` 또는 plugin PR 브랜치뿐이다. force push하지 않는다.
- 사용자가 명시적으로 요청하지 않는 한 브랜치 변경, stash, rebase, pull, 충돌
  해결을 하지 않는다.

## 1. 문서 동기화

스킬을 추가·이동·삭제했거나 `SKILL.md` frontmatter 또는 manifest를 바꿨으면 커밋
전에 로컬 `sync-docs`로 설명 문서(`README.md`, `HELP.md`, `docs/catalog.md`,
`AGENTS.md`, `.claude/CLAUDE.md`, `archived/README.md`)를 맞추고 `python3 .claude/skills/sync-docs/scripts/check_docs.py`가
`OK`인지 확인한다. 해당 없으면 건너뛴다.

## 2. verify-secrets

프로젝트 로컬 `verify-secrets` 스킬을 실행한다 (Claude Code는
`.claude/skills/verify-secrets/`). 이슈를 하나라도 보고하면 커밋하지 않는다.
수정하거나 사용자의 명시적 예외 승인을 받은 뒤 재검증한다.

## 3. 커밋

`git-actions`의 커밋 규칙을 따른다.

- `git status --short`, `git diff --stat`, 관련 diff를 먼저 본다.
- 현재 작업과 관련된 파일만 스테이징한다.
- 변경이 없으면 빈 커밋을 만들지 않는다. 브랜치에 `origin/main`보다 앞선 커밋이 있을
  때만 다음 단계로 간다.
- 저장소의 기존 커밋 메시지 스타일을 쓴다.
- `plugins/` 변경이고 `main`에 있으면 plugin 하나당 브랜치를 판다 (`feature/<plugin>-<요약>`).
  브랜치 생성은 5단계 승인에 포함한다.

## 4. 버전 범프

플러그인은 스킬(묶음)마다 따로 배포된다. 배포 대상 커밋이 `plugins/<name>/` 아래 파일을
바꿨고 아직 범프하지 않았다면, **바뀐 플러그인만** 범프한다.

```bash
git diff --name-only origin/main..HEAD | grep '^plugins/' | cut -d/ -f2 | sort -u
scripts/bump-plugin.sh <plugin> [patch|minor|major]   # 두 plugin.json을 같은 값으로 올린다
```

- 올리는 단계는 변경 종류로 정한다. 새 버전은 사용자에게 확인받는다.

  | 변경 | 범프 | 자리 |
  | --- | --- | --- |
  | repo 대격변 (구조·이름·호출 방식이 바뀌어 쓰던 명령이 깨짐) | major | 맨 앞 |
  | 스킬 추가·삭제 | minor | 가운데 |
  | 스킬 수정 (문구·동작 변경 모두) | patch | 맨 뒤 |

  종류가 섞이면 가장 높은 단계를 따른다. 올리면 아래 자리는 0이 된다 (`1.2.3` → minor → `1.3.0`).
- `marketplace.json`의 `plugins[]`에는 version을 넣지 않는다.
- `chore: bump <plugin> version to X.Y.Z` 형식으로 커밋한다 (여럿이면 한 커밋에 묶고 제목에 나열).

`plugins/` 밖 변경(저장소 문서, 로컬 전용 파일)만 있으면 범프를 건너뛰고 보고에 그
이유를 적는다.

## 5. push · PR · 머지

**`plugins/` 밖 변경만 있으면** PR 없이 바로 push한다. 실패하면 멈추고, 플러그인 업데이트로 넘어가지 않는다.

```bash
git push origin main
```

**`plugins/` 변경이면** 아래로 간다. 브랜치 생성, push, PR 생성, 머지는 되돌리기 어렵다. 브랜치명, PR 제목, **PR만 올릴지 바로 머지할지**를
한 번에 보여주고 승인받은 뒤 실행한다. 사용자가 처음부터 "머지까지"라고 했으면 그것으로 갈음한다.

```bash
git push -u origin <branch>
gh pr create --base main --title "[v<새버전>] <type>(<plugin>): <요약>" --body "<변경 요약>"
```

바로 머지를 골랐으면:

```bash
gh pr merge --merge            # 기존 이력과 같은 merge commit
git checkout main
git pull origin main
```

push·PR·머지 중 하나라도 실패하면 멈춘다. force push하지 않고, 플러그인 업데이트로 넘어가지 않는다.
PR만 올린 경우 6단계는 머지된 뒤 `main`에서 한다 — 개발 머신의 로컬 directory marketplace는 지금 체크아웃된
브랜치를 읽기 때문이다.

## 6. 설치 플러그인 업데이트

서드파티 marketplace는 자동 업데이트되지 않으므로 push 성공 후 직접 실행한다.
한쪽 호스트 CLI가 없으면 그 호스트를 건너뛰었다고 보고하고 다른 쪽을 진행한다.

```bash
claude plugin marketplace update hsryuuu
claude plugin update <plugin>@hsryuuu      # 바뀐 플러그인마다, 설치돼 있는 것만
claude plugin details <plugin>@hsryuuu

codex plugin marketplace upgrade hsryuuu
codex plugin list
```

각 호스트가 보고하는 버전이 방금 push한 버전과 같은지 확인한다. **옛 버전 번호와
함께** "already at the latest version"이 나오면 범프 커밋이 `origin main`에 도달하지
못한 것이다. 캐시를 지우지 말고 push를 고친다.

이 흐름에서 캐시 디렉토리를 지우지 않는다. 버전 범프만으로 두 호스트가 새
스냅샷을 받는다.

## 보고

- verify-secrets 결과
- 커밋 해시와 메시지, 또는 커밋이 필요 없었다는 사실
- 플러그인별 버전 범프 `name old → new`, 또는 건너뛴 이유
- push 대상과 결과. PR을 올렸다면 번호·제목(`[vX.Y.Z]` 접두사 포함)과 머지 여부
- 호스트별 업데이트 결과와 각 호스트가 보고한 버전, 또는 건너뛴 이유
- 모든 머신에서 새 세션이 필요하고, 다른 머신은 업데이트 명령을 직접 실행해야
  한다는 안내
