---
name: git-actions
description: git 관련 요청이나 git 작업이 필요할 때 쓰는 단일 진입 스킬. 커밋·푸시·PR/MR 생성·pull(머지)·충돌 해결·rebase/브랜치 정리·이력(history) 조회를 한 곳에서 라우팅한다. 인자/의도가 분명하면 바로 해당 작업으로, 모호하거나 인자가 없으면 메뉴로 무엇을 할지 고르게 한다. 트리거 - "커밋해줘", "atomic commit", "커밋 분리", "PR 만들어줘", "MR 생성", "이 브랜치 PR로", "푸시하고 PR", "main pull 해줘", "최신 main 가져와서 충돌 해결", "develop 머지", "브랜치 동기화", "merge conflict 해결", "rebase", "브랜치 정리", "git history", "이 변경 누가 언제 추가했어?", "git log 분석", "/git-actions", "/git-actions main pull", "/git-actions --file".
---

# Git Actions

git 관련 요청이 들어오면 이 스킬이 받아서, **무슨 작업인지 판단해 해당 프롬프트 파일(`references/*.md`)을 읽고 그대로 따른다.** 이 `SKILL.md`는 얇은 라우터다 — 실제 git 절차는 전부 `references/`에 있다.

## 1. 작업 라우팅

들어온 인자/자연어에서 의도를 읽어 아래로 분기한다. **의도가 분명하면 메뉴를 건너뛰고 곧장 해당 작업으로 간다.**

| 의도 신호 | 작업 | 읽을 파일 |
|---|---|---|
| "커밋해줘", "atomic commit", "커밋 분리", dirty 변경 정리 | **commit** | `references/commit.md` |
| 위 + "푸시", "push" | **commit + push** | `references/commit.md` (+ 끝에 push) |
| "PR 만들어줘", "MR", "이 브랜치 PR로", "리뷰 요청" | **PR 생성** | `references/pr.md` |
| 위 + `--file` 인자 또는 "파일로" | **PR 파일 모드** | `references/pr.md` (파일 모드) |
| "pull 해줘", "main 가져와", "develop 머지", "브랜치 동기화", `<branch> pull` | **pull (머지)** | `references/pull.md` |
| "merge conflict 해결", "충돌 해결" | **충돌 해결** | `references/resolve-conflict.md` |
| "rebase", "브랜치 정리", "커밋 정리" | **rebase** | `references/rebase.md` |
| "누가 언제 짰어?", "언제 추가됐어?", "git log 분석", blame/bisect | **history 조회** | `references/history.md` |

인자 예:
- `/git-actions main pull` → 대상 브랜치 `main`으로 **pull** 작업. 충돌 나면 `resolve-conflict.md`를 탄다.
- `/git-actions --file` → **PR 파일 모드**.
- `/git-actions --base develop` → PR 베이스를 `develop`으로.

## 2. 인자 없거나 모호하면 메뉴

`/git-actions`만 호출됐거나 의도가 갈리면, **`AskUserQuestion`으로 터미널 옵션 메뉴**를 띄운다:

```
무엇을 할까요?
─────────────────────────────
1) commit          변경을 atomic 단위로 나눠 커밋        → references/commit.md
2) commit + push   커밋 후 origin에 푸시                 → references/commit.md (+push)
3) PR 만들기        베이스 최신화 → PR 자동 생성(gh)        → references/pr.md
4) PR 파일로         PR/MR 본문을 markdown 파일로          → references/pr.md (파일 모드)
5) pull 최신화       대상 브랜치 머지 + 충돌 해결            → references/pull.md
```

> rebase·history는 메뉴에 넣지 않는다 — 보통 자연어/인자로 직접 들어오는 정리·조회 작업이라 1번 라우팅에서 바로 분기한다. 사용자가 메뉴에서 그 외 작업을 원한다고 하면 해당 파일로 안내한다.

선택이 정해지면 해당 `references/*.md`를 읽고 그 절차를 그대로 수행한다.

## 3. 프롬프트 공유 관계

작업끼리 겹치는 로직은 한 파일에만 둔다. 다른 작업은 그 파일을 참조한다.

- **`resolve-conflict.md`** — 충돌 분류(SAFE/ESCALATE)와 해결. **pull**(`pull.md`)과 **PR 생성 전 베이스 머지**(`pr.md`)가 공통으로 참조한다.
- **`commit.md`** — atomic 커밋 설계와 커밋 스타일 감지. **commit**과 **PR 본문 제목 스타일**이 공유한다.

## 4. 공통 안전 규칙 (모든 작업 공통)

각 `references/*.md`에 상세가 있지만, 어떤 작업이든 아래는 절대 어기지 않는다:

- **모호한 충돌은 추측 금지** — SAFE라고 1초라도 망설여지면 ESCALATE. `AskUserQuestion`으로 사용자 결정을 받는다.
- **force push 자동 실행 금지** — `--force`, `--force-with-lease` 모두 사용자가 명시 요청할 때만.
- **main/master 직접 rebase 금지.**
- **dirty 워킹트리를 임의로 stash·commit·reset 하지 않는다** — 사용자에게 묻는다.
- **충돌 마커(`<<<<<<<`, `=======`, `>>>>>>>`)가 남은 채 커밋·푸시하지 않는다** — `git diff --check`로 확인.
- **막히면 밀어붙이지 말고** `git merge --abort` / `git rebase --abort`로 되돌린 뒤 상황을 보고한다.
- **끝나면 무엇을 어떻게 했는지 간단히 보고한다.**
