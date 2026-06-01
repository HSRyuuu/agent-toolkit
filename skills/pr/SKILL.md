---
name: pr
description: 현재 작업 브랜치의 변경사항을 main(또는 master)에 머지하기 위해 GitHub Pull Request를 만들거나, GitHub이 아닌 환경(GitLab·Bitbucket·자체 호스트 등)에서 PR/MR 본문 markdown을 만들어야 할 때 사용한다. GitHub일 때는 `gh pr create`로 자동 생성, 그 외에는 `PR-DRAFT-yyyy-MM-dd-hh-mm-ss.md` 파일을 만들어 사용자가 직접 붙여넣게 한다. `--file` 인자를 주면 GitHub이라도 자동 생성을 건너뛰고 파일만 만든다. 트리거 - "PR 만들어줘", "MR 생성", "/pr", "/pr --file", "merge request 올려", "이 브랜치 PR로", "푸시하고 PR", "리뷰 요청".
---

# PR Creation Skill

현재 브랜치의 변경사항을 묶어서 PR/MR 본문을 만든다. **GitHub이면 자동 생성, 그 외에는 markdown 파일로 떨궈서 수동 생성**.

## 핵심 원칙

- **자동 생성은 GitHub만** — `gh pr create` 한 가지 경로만 자동화한다. GitLab(`glab`)이나 다른 호스트는 분기하지 않고 일괄적으로 파일 모드로 보낸다 (스킬 단순화 목적).
- **베이스 브랜치 자동 결정** — `main` 우선, 없으면 `master`. `git symbolic-ref refs/remotes/origin/HEAD`도 보조로 본다.
- **현재 브랜치를 그대로 사용** — 새 브랜치를 만들지 않는다. main/master 위에서 호출됐으면 거부.
- **PR 전에 베이스 최신화** — PR을 만들기 전에 베이스 브랜치를 머지해 충돌을 먼저 해소한다. 자명한 충돌은 직접 해결하고, 모호한 충돌은 사용자에게 처리 방법을 묻는다.
- **사용자 확인 후 행동** — 제목/본문 초안과 푸시 여부는 항상 사용자에게 보여주고 진행.

## 인자

| 인자 | 동작 |
|---|---|
| `--file` | 호스트와 무관하게 자동 생성을 건너뛰고 **무조건 파일 모드**로 동작. |
| `--draft` | GitHub 자동 생성 시 `gh pr create --draft` 사용. |
| `--base <branch>` | 자동 감지 대신 명시한 베이스 브랜치 사용. |

## 모드 결정

```
호스트가 GitHub인가? (remote URL에 github.com 포함)
├── YES + `--file` 없음 → 자동 생성 모드 (gh)
└── 그 외 (GitLab / Bitbucket / 자체 호스트 / `--file` 지정) → 파일 모드
```

호스트 판정:
```bash
git remote get-url origin | grep -q 'github\.com'
```

GitHub인데 `gh`가 없거나 인증 안 됐으면 → 파일 모드로 폴백.

## 실행 순서

### 1. 사전 점검

```bash
git status --short
git rev-parse --abbrev-ref HEAD
git remote get-url origin
git fetch origin --quiet
```

- 현재 브랜치가 `main`/`master`/`develop`이면 **중단** — "feature 브랜치에서 호출하세요".
- 워킹 트리 dirty면 사용자에게 알리고 커밋 여부 확인 (`git-master` 스킬 권유).

### 2. 베이스 브랜치 결정

```bash
git show-ref --verify --quiet refs/remotes/origin/main && echo main || echo master
```

결과를 `BASE`로 사용. `--base` 인자가 들어왔으면 그 값 우선.

### 3. 베이스 브랜치 최신화 & 충돌 해결

PR을 만들기 전에 최신 베이스를 현재 브랜치로 머지해 충돌을 미리 해소한다. 그래야 PR이 깔끔하게 머지되고, diff/본문도 머지된 상태를 반영한다.

**먼저 충돌 여부만 확인** (워킹 트리를 건드리지 않음):
```bash
git fetch origin "$BASE" --quiet
git merge-tree --write-tree HEAD "origin/$BASE" >/dev/null 2>&1; echo $?
```
- 종료 코드 `0` → 충돌 없음. 이 단계를 건너뛰고 **3-A(클린 머지)**로.
- 종료 코드 `1` → 충돌 있음. **3-B(충돌 해결)**로.
  (`git merge-tree`가 없는 구버전 git이면 곧바로 3-A의 머지를 시도하고 충돌 시 3-B로 분기.)

워킹 트리가 dirty면 머지 전에 멈추고 사용자에게 알린다 (커밋/stash는 임의로 하지 않는다 — 1단계 정책과 동일).

#### 3-A. 클린 머지

```bash
git merge --no-edit "origin/$BASE"
```
충돌 없이 끝나면 이후 단계로 진행. (이미 베이스를 포함하고 있어 "Already up to date"면 아무 일도 일어나지 않음.)

#### 3-B. 충돌 해결

충돌 파일 목록을 확인한다:
```bash
git merge --no-edit "origin/$BASE"   # 충돌로 중단됨
git diff --name-only --diff-filter=U
```

충돌을 **자명한 것**과 **모호한 것**으로 분류한다:

- **자명한 충돌 → 직접 해결**
  - import/의존성 정렬, lockfile(`package-lock.json`, `uv.lock` 등) 재생성, changelog·버전 범프처럼 양쪽 의도가 명확하고 합치면 되는 경우.
  - 한쪽이 단순 포매팅/공백만 바꾼 경우.
  - 명백히 양쪽 변경을 모두 살리면 되는 경우(서로 다른 함수/줄 추가).
  - 해결 후 `git add <file>`.

- **모호한 충돌 → 사용자에게 질문**
  - 같은 로직을 양쪽이 다르게 고친 경우, 어느 쪽 동작이 맞는지 코드만으로 판단 불가한 경우, 머지가 의미를 바꿀 위험이 있는 경우.
  - **추측해서 한쪽을 고르지 않는다.** 충돌 파일 경로, 충돌 구간(both-modified)의 양쪽 내용 요약, 가능한 처리안을 제시하고 사용자에게 어떻게 할지 묻는다.
  - 모호한 충돌이 하나라도 남아 있으면 PR 생성을 진행하지 않고 대기한다.

모든 충돌 해결 후 머지를 커밋한다:
```bash
git diff --check          # 충돌 마커(<<<<<<< 등) 잔류 확인
git commit --no-edit      # 머지 커밋 생성
```

머지를 중단해야 하면 `git merge --abort`로 원상복귀하고 사용자에게 보고한다 (절대 변경을 임의로 버리지 않는다).

> 머지 커밋이 생겼으므로 5단계 푸시 시 upstream에 반영해야 PR에 포함된다.

### 4. 변경사항 수집

```bash
git log --oneline "origin/$BASE..HEAD"
git diff --stat "origin/$BASE...HEAD"
git diff "origin/$BASE...HEAD"
```

`...`(three-dot)으로 베이스 분기점 이후 차이만 본다.

### 5. 제목·본문 생성

**제목 규칙**:
- 커밋이 1개면 그 커밋 제목 그대로.
- 여러 개면 공통 주제를 한 줄로 (70자 이내).
- 기존 커밋 스타일을 따른다 (`git log -30 --oneline`로 한국어/영어, semantic prefix 여부 감지).

**본문 템플릿**:

```markdown
## Summary
- <변경 요점>

## Changes
- <파일/모듈 단위 주요 변경>

## Test plan
- [ ] <검증 항목>
```

레포에 `.github/PULL_REQUEST_TEMPLATE.md`가 있으면 우선 사용.

### 6. 푸시 (필요 시)

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null
```

upstream 없거나 로컬이 앞서 있으면 사용자에게 묻고:
```bash
git push -u origin HEAD
```

force push는 사용자가 명시 요청하지 않는 한 절대 사용하지 않는다.

### 7. 모드별 출력

#### 7-A. 자동 생성 모드 (GitHub + `--file` 없음 + gh 사용 가능)

```bash
gh pr create --base "$BASE" --title "<제목>" --body "$(cat <<'EOF'
<본문>
EOF
)"
```

생성된 PR URL을 사용자에게 보여준다.

#### 7-B. 파일 모드 (그 외 모든 경우)

본문 앞에 메타 헤더를 붙인 markdown 본문을 만든다:

```markdown
# <제목>

> Branch: `<현재 브랜치>` → `<BASE>`
> Commits: <N>개 / Files: <M>개

## Summary
- <변경 요점>

## Changes
- <파일/모듈 단위 주요 변경>

## Commits
- <sha> <commit subject>

## Test plan
- [ ] <검증 항목>

---
<!-- 이 파일은 PR/MR 본문 임시 초안입니다. 내용을 복사한 뒤 반드시 삭제하세요. -->
```

**파일 저장**:
- 경로: 프로젝트 루트(`git rev-parse --show-toplevel`)에 `PR-DRAFT-yyyy-MM-dd-hh-mm-ss.md`
- 타임스탬프: `date +"%Y-%m-%d-%H-%M-%S"` (콜론은 파일시스템 호환성 문제로 하이픈)

**출력 형식 예**:

```
[모드] 파일 모드 (사유: GitLab 호스트 / `--file` 지정 / gh 미설치 등)

📄 임시 파일: /Users/me/proj/PR-DRAFT-2026-05-04-13-42-07.md
🔗 새 PR/MR URL: <호스트별 compare URL>

⚠️  파일 내용을 복사한 뒤 반드시 삭제하세요:
    rm "/Users/me/proj/PR-DRAFT-2026-05-04-13-42-07.md"
```

**호스트별 새 PR/MR 생성 웹 URL** (가능하면 함께 출력):
- GitHub: `https://github.com/<owner>/<repo>/compare/<BASE>...<branch>?expand=1`
- GitLab: `https://<host>/<group>/<repo>/-/merge_requests/new?merge_request[source_branch]=<branch>&merge_request[target_branch]=<BASE>`
- Bitbucket: `https://bitbucket.org/<workspace>/<repo>/pull-requests/new?source=<branch>&dest=<BASE>`

**규칙**:
- "복사 후 삭제하세요" 문구는 어떤 경우에도 누락하지 않는다.
- 파일이 git에 tracked 되지 않는지 `git status`로 확인. tracked면 즉시 삭제 후 보고.

## 사용자 확인 포인트

다음은 **반드시 사용자에게 보여주고 진행 여부를 묻는다**:
1. push가 필요한 경우 → 진행 여부
2. 제목·본문 초안 → 그대로 진행 / 수정
3. 베이스 브랜치 자동 감지 결과가 의심스러운 경우
4. 베이스 머지 중 **모호한 충돌** → 처리 방법 (어느 쪽 채택 / 양쪽 병합 / 직접 지시)

## 자주 만나는 케이스

| 상황 | 대응 |
|---|---|
| Fork에서 upstream으로 PR | `gh pr create --repo <upstream>` 사용자에게 확인 |
| 이미 PR 존재 | `gh pr view`로 확인 후 새로 만들지/갱신할지 사용자에게 묻기 |
| 빈 커밋(베이스와 차이 없음) | 중단하고 안내 |
| 베이스가 `main`도 `master`도 아닌 레포 | `git symbolic-ref refs/remotes/origin/HEAD` 결과 사용, 없으면 사용자에게 질문 |
| 베이스 머지 시 자명한 충돌(lockfile/import/포매팅) | 직접 해결 후 `git add` → 머지 커밋 |
| 베이스 머지 시 모호한 충돌(같은 로직 양쪽 수정) | 추측 금지 — 양쪽 내용 요약해 사용자에게 처리 방법 질문 |

## 하지 말 것

- 커밋되지 않은 변경을 임의로 커밋·stash 하지 않는다.
- 모호한 충돌을 추측으로 한쪽만 채택해 해결하지 않는다 — 반드시 사용자에게 묻는다.
- 충돌 마커(`<<<<<<<`, `=======`, `>>>>>>>`)가 남은 채 커밋·푸시하지 않는다 (`git diff --check`로 확인).
- `--force-with-lease` 포함 어떤 force push도 자동 실행하지 않는다.
- main/master로 직접 PR을 만드는 동작을 사용자가 명시하지 않은 채 수행하지 않는다.
- 본문에 의미 없는 boilerplate("This PR ...")만 채우지 않는다 — 실제 diff 기반 요약을 쓴다.
- GitLab `glab` 명령을 자동 실행하지 않는다 — GitLab은 무조건 파일 모드.
