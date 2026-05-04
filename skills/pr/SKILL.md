---
name: pr
description: 현재 작업 브랜치의 변경사항을 main(또는 master)에 머지하기 위해 GitHub Pull Request 또는 GitLab Merge Request를 만들어야 할 때 사용한다. GitHub/GitLab 외 호스트(Bitbucket·Gitea 등)나 PR CLI가 없는 환경에서도 사용 가능하다. 트리거 - "PR 만들어줘", "MR 생성", "/pr", "merge request 올려", "이 브랜치 PR로", "푸시하고 PR", "리뷰 요청".
---

# PR / MR Creation Skill

현재 브랜치의 변경사항 전체를 묶어서 GitHub PR 또는 GitLab MR을 만든다.

## 핵심 원칙

- **베이스 브랜치는 자동 결정**: `main` 우선, 없으면 `master`. `git symbolic-ref refs/remotes/origin/HEAD`도 보조로 본다.
- **호스트는 remote URL로 감지**: `github.com` → `gh`, `gitlab` → `glab`. self-hosted GitLab도 `glab`로 처리.
- **현재 브랜치를 그대로 사용**: 새 브랜치를 만들지 않는다. main/master 위에서 호출됐으면 거부하고 사용자에게 알린다.
- **PR 생성은 사용자 확인 후**: 제목/본문 초안을 보여주고, 사용자가 승인하면 `gh`/`glab` 실행.

## 실행 순서

### 1. 사전 점검 (병렬 실행)

```bash
git status --short
git rev-parse --abbrev-ref HEAD
git remote get-url origin
git fetch origin --quiet
```

판정:
- 현재 브랜치가 `main`/`master`/`develop`이면 **중단**하고 "PR은 feature 브랜치에서 만드세요" 안내.
- 워킹 트리에 커밋 안 된 변경이 있으면 사용자에게 알리고 커밋부터 할지 물어본다(필요하면 `git-master` 스킬 호출 권유).

### 2. 베이스 브랜치 결정

```bash
git show-ref --verify --quiet refs/remotes/origin/main && echo main || echo master
```

위에서 결정한 베이스를 `BASE`로 사용.

### 3. 호스트 감지

`git remote get-url origin` 결과로 분기:

| URL 패턴 | 도구 | 명령 |
|---|---|---|
| `github.com` | `gh` | `gh pr create` |
| `gitlab.com` 또는 GitLab self-hosted (`gitlab.*`, `*/gitlab/*`) | `glab` | `glab mr create` |
| 그 외 | 사용자에게 어떤 호스트인지 묻고 도구 지정 |

도구가 설치돼 있는지 미리 확인:
```bash
command -v gh   # GitHub
command -v glab # GitLab
```

없으면 설치 가이드 안내:
- macOS: `brew install gh` / `brew install glab`
- 인증: `gh auth login` / `glab auth login`

### 4. 변경사항 수집 (병렬 실행)

```bash
git log --oneline "origin/$BASE..HEAD"
git diff --stat "origin/$BASE...HEAD"
git diff "origin/$BASE...HEAD"
```

`...` (three-dot)을 사용해야 베이스 분기점 이후 차이만 본다.

### 5. 제목·본문 생성

**제목 규칙**:
- 커밋이 1개면 그 커밋 제목 그대로.
- 커밋이 여러 개면 변경의 공통 주제를 한 줄로 (70자 이내).
- 기존 커밋 스타일을 따른다 (한국어/영어, semantic prefix 여부 — `git log -30 --oneline`로 감지).

**본문 템플릿**:

```markdown
## Summary
- <변경 요점 1>
- <변경 요점 2>

## Changes
- <파일/모듈 단위 주요 변경>

## Test plan
- [ ] <검증 항목 1>
- [ ] <검증 항목 2>
```

레포에 `.github/PULL_REQUEST_TEMPLATE.md` 또는 `.gitlab/merge_request_templates/`가 있으면 그 템플릿을 우선 사용.

### 6. 푸시 (필요 시)

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null
```

upstream이 없거나 로컬이 앞서 있으면:
```bash
git push -u origin HEAD
```

`--force`/`--force-with-lease`는 사용자가 명시적으로 요청하지 않는 한 사용하지 않는다.

### 7. PR/MR 생성

**GitHub**:
```bash
gh pr create --base "$BASE" --title "<제목>" --body "$(cat <<'EOF'
<본문>
EOF
)"
```

**GitLab**:
```bash
glab mr create --target-branch "$BASE" --title "<제목>" --description "$(cat <<'EOF'
<본문>
EOF
)" --remove-source-branch --squash-before-merge=false
```

`--remove-source-branch`, `--squash` 같은 옵션은 사용자가 요청하거나 프로젝트 컨벤션에 명시된 경우에만 추가.

### 8. 결과 출력

생성된 PR/MR URL을 사용자에게 보여준다. `gh pr view --web` / `glab mr view --web` 안내는 사용자가 요청 시에만.

## Fallback: 자동 생성 불가 시 markdown 출력

다음 중 하나라도 해당되면 **자동 생성을 시도하지 말고 fallback 모드로 전환**한다:

| 상황 | 감지 방법 |
|---|---|
| `gh`/`glab` 미설치 | `command -v gh` / `command -v glab` 실패 |
| CLI 인증 안 됨 | `gh auth status` / `glab auth status` 실패 |
| 미지원 호스트 (Bitbucket, Gitea, Gerrit, 자체 Git 서버 등) | remote URL이 GitHub/GitLab 패턴에 매칭 안 됨 |
| 권한 부족으로 push/생성 실패 | `gh pr create` / `glab mr create` 또는 `git push`가 403/permission denied로 실패 |
| 사용자가 "markdown만 줘", "복사할 수 있게만" 등 명시적으로 요청 | 사용자 발화 |

### Fallback 동작

1. **표준 markdown 본문을 만든다** — 자동 생성 모드와 동일한 제목·본문 + 메타 정보 헤더를 추가:

   ````markdown
   # <제목>

   > Branch: `<현재 브랜치>` → `<BASE>`
   > Commits: <N>개 / Files: <M>개

   ## Summary
   - <변경 요점>

   ## Changes
   - <파일/모듈 단위 주요 변경>

   ## Commits
   - <sha> <commit subject>
   - ...

   ## Test plan
   - [ ] <검증 항목>
   ````

2. **임시 파일로 저장** — 사용자가 터미널에서 markdown 본문을 통째로 긁기 어려우므로 파일로 떨어뜨린다:

   - 경로: 프로젝트 루트(`git rev-parse --show-toplevel`)에 `PR-DRAFT-yyyy-MM-dd-hh-mm-ss.md`
   - 타임스탬프 포맷: `date +"%Y-%m-%d-%H-%M-%S"` (콜론은 파일시스템 호환성 문제로 하이픈 사용)
   - 파일 끝에 다음 푸터를 항상 붙인다:

     ```markdown
     ---
     <!-- 이 파일은 PR/MR 본문 임시 초안입니다. 내용을 복사한 뒤 반드시 삭제하세요. -->
     ```

3. **사용자에게 명확히 안내** — 출력에서 다음 두 가지를 강조한다:
   - 임시 파일 경로 (절대 경로로)
   - **"복사 후 삭제하세요"** 문구 (생략 금지)

   삭제 명령도 함께 제시:
   ```bash
   rm "<임시 파일 경로>"
   ```

4. **호스트별 PR/MR 생성 URL 안내** (가능한 경우):
   - GitHub: `https://github.com/<owner>/<repo>/compare/<BASE>...<branch>?expand=1`
   - GitLab: `https://<host>/<group>/<repo>/-/merge_requests/new?merge_request[source_branch]=<branch>&merge_request[target_branch]=<BASE>`
   - Bitbucket: `https://bitbucket.org/<workspace>/<repo>/pull-requests/new?source=<branch>&dest=<BASE>`

   remote URL을 파싱해서 위 패턴으로 만든 뒤 사용자에게 함께 보여준다. 클릭만 하면 본문 붙여넣기로 바로 생성 가능.

5. **푸시는 fallback에서도 동일 규칙** — upstream 없거나 로컬이 앞서 있으면 사용자에게 묻고 `git push -u origin HEAD` 진행. 푸시 자체가 실패하면 그 사실도 출력에 포함한다.

### Fallback 출력 형식 예

```
[자동 생성 불가] 사유: glab CLI 미설치

📄 임시 파일 생성: /Users/me/proj/PR-DRAFT-2026-05-04-13-42-07.md
🔗 새 MR URL: https://gitlab.com/foo/bar/-/merge_requests/new?merge_request[source_branch]=feat/x&merge_request[target_branch]=main

⚠️  파일 내용을 복사한 뒤 반드시 삭제하세요:
    rm "/Users/me/proj/PR-DRAFT-2026-05-04-13-42-07.md"
```

- "복사 후 삭제하세요" 문구는 어떤 경우에도 누락하지 않는다.
- 임시 파일은 절대 자동 commit/stage 되면 안 된다 — 생성 직후 `git status`로 추적되지 않는지 확인하고, tracked 상태면 즉시 삭제 후 사용자에게 보고.
- 설치 안내(`brew install glab` 등)는 출력 끝에 한 줄로만 덧붙인다.

## 사용자 확인 포인트

다음 단계에서는 **반드시 사용자에게 보여주고 진행 여부를 묻는다**:
1. 푸시되지 않은 커밋이 있어 push가 필요한 경우 → push 진행 여부
2. PR/MR 제목·본문 초안 → 그대로 만들지, 수정할지
3. 베이스 브랜치가 자동 감지와 다르게 필요한 경우 → 사용자가 지정

## 자주 만나는 케이스

| 상황 | 대응 |
|---|---|
| Fork에서 upstream으로 PR | `gh pr create --repo <upstream>` 형태로 사용자에게 확인 |
| Draft로 만들고 싶음 | `gh pr create --draft` / `glab mr create --draft` |
| 이미 PR이 있음 | `gh pr view` / `glab mr view`로 확인 후 새로 만들지 갱신할지 사용자에게 묻기 |
| 빈 커밋(베이스와 차이 없음) | 중단하고 안내 |
| 베이스가 `main`도 `master`도 아닌 레포 | `git symbolic-ref refs/remotes/origin/HEAD` 결과 사용, 없으면 사용자에게 질문 |

## 하지 말 것

- 커밋되지 않은 변경을 임의로 커밋하거나 stash하지 않는다.
- `--force-with-lease` 포함 어떤 force push도 자동 실행하지 않는다.
- main/master로 직접 PR을 만드는 동작을 사용자가 명시적으로 요청하지 않은 채 수행하지 않는다.
- 본문에 의미 없는 boilerplate("This PR ...")만 채우지 않는다 — 실제 diff 기반 요약을 쓴다.
