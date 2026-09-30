# Pull — 대상 브랜치 병합으로 최신화

> `git-actions`의 **pull (머지)** 작업이 따르는 프롬프트.
> 현재 작업 브랜치에 **대상 브랜치를 병합(pull)**하고, 충돌이 나면 `resolve-conflict.md`를 따른다.

## 핵심 원칙

- **현재 브랜치는 그대로** — 작업 중인 현재 브랜치를 유지한 채 대상 브랜치를 끌어와 병합한다(`git merge`). 브랜치를 전환하지 않는다.
- **merge 방식** — `git merge`로 병합 커밋을 만든다. rebase는 `--rebase` 인자를 줄 때만 사용한다.
- **되돌릴 수 있게 시작** — 병합 중 막히면 `git merge --abort`로 원상복구. 작업 트리가 더러우면 먼저 정리(또는 stash)한 뒤 시작한다.
- **항상 보고** — 끝나면 무엇을 병합했고, 어떤 충돌을 어떻게 처리했는지 간단히 정리해 보고한다.

## 인자

| 인자 | 동작 |
|---|---|
| `<branch>` | 병합할 대상 브랜치를 명시 (예: `/git-actions main pull`). 생략하면 후보 목록을 제시하고 컨펌받는다. |
| `--rebase` | merge 대신 `git rebase origin/<branch>` 사용. 충돌이 커밋 단위로 반복될 수 있음을 사용자에게 알린다. |
| `--no-fetch` | `git fetch`를 건너뛰고 로컬에 있는 브랜치 상태로 병합 (오프라인 / 의도적 구버전 병합 시). |

## 실행 순서

### 1. 사전 점검

```bash
git rev-parse --is-inside-work-tree   # 저장소인지
git status --porcelain                # 작업 트리 상태
git branch --show-current             # 현재 브랜치
```

- 저장소가 아니면 중단하고 알린다.
- **작업 트리가 더럽다면** (커밋 안 된 변경) 그대로 병합하면 위험하다. 사용자에게 알리고 선택을 받는다: 커밋하기 / `git stash`로 치워두기(병합 후 복원) / 중단. 임의로 stash·commit하지 않는다.
- 현재 브랜치가 곧 대상 브랜치면(예: main에서 main을 당기려는 경우) 단순 `git pull`로 충분함을 알리고 확인받는다.

### 2. 대상 브랜치 결정

인자로 브랜치가 주어졌으면 그대로 사용한다. **없으면** 후보를 모아 사용자에게 제시하고 컨펌받는다(`AskUserQuestion` 권장).

후보 수집:
```bash
git remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p'   # 원격 기본 브랜치
git branch -a --format='%(refname:short)'                            # 전체 브랜치
```

- 흔한 베이스 브랜치(`main`, `master`, `develop`, `release/*`)와 원격 기본 브랜치를 우선 노출한다.
- 현재 브랜치 자신은 후보에서 제외한다.
- 후보가 하나로 자명해도(예: `main`만 존재) **한 번은 확인**받는다 — 잘못된 브랜치 병합은 되돌리기 번거롭다.

### 3. 최신화 후 병합

```bash
git fetch origin                      # --no-fetch면 생략
git merge origin/<branch>             # 원격 추적 브랜치 기준으로 병합
# 원격에 없는 로컬 전용 브랜치면: git merge <branch>
# --rebase면: git rebase origin/<branch>
```

- 병합이 **깨끗하게 끝나면**(충돌 없음) 바로 4번(검증·보고)으로 간다. fast-forward인지 병합 커밋이 생겼는지 구분해 보고한다.
- 충돌이 나면 → **`resolve-conflict.md`의 분류·해결 절차를 따른다.** 해결이 끝나면 4번으로.

### 4. 검증 후 보고

- 남은 충돌 마커가 없는지, 병합 커밋이 만들어졌는지 확인한다.
- 가능하면 가벼운 sanity check(타입체크·린트·빌드 중 프로젝트에 맞는 것)를 제안한다. 단, 시키지 않은 무거운 작업은 임의로 돌리지 않는다.

**보고 형식** (간단히):

```
## 병합 결과
- 대상: origin/main → 현재 브랜치 (feature/x)
- 가져온 커밋: 7개  /  fast-forward 여부
- 충돌: 3개 파일

### 자동 해결 (2)
- src/api.ts — 양쪽 import 추가, 둘 다 보존
- uv.lock — 재생성

### 사용자 결정 반영 (1)
- src/auth.ts — 토큰 만료 로직 충돌 → '대상(theirs) 채택' 선택 반영

상태: 병합 완료 (커밋 abc1234)
```

충돌이 없었으면 한 줄로: "origin/main을 fast-forward로 최신화했습니다(충돌 없음)."

## 안전 규칙

- **절대** `--force` push 하지 않는다. 이 작업은 병합·충돌 해결까지만 한다. push는 사용자가 결정한다.
- 병합 전 작업 트리가 더러우면 사용자 동의 없이 stash·commit·reset 하지 않는다.
- main/master 위에서 호출됐는데 거기에 다른 브랜치를 병합하려는 경우, 의도가 맞는지 한 번 더 확인한다.
- 막히거나 예상과 다르면 밀어붙이지 말고 `--abort`로 되돌린 뒤 상황을 설명한다.
