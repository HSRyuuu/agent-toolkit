---
name: update-project-docs
description: agent-toolkit 저장소의 개발용 문서(.claude/CLAUDE.md, README.md, docs/catalog.md)를 현재 디렉토리/플러그인 상태에 맞게 동기화한다. 새 스킬을 추가·이동·삭제했거나, plugin.json의 skills 배열을 변경했거나, 디렉토리 정책(skills/ vs skills-workflow/ vs skills-system/)을 바꿨을 때 사용한다. 트리거 - "프로젝트 문서 업데이트", "catalog 갱신", "툴킷 README 정리", "update project docs", "skills 카탈로그 다시 생성".
---

# Update Project Docs (agent-toolkit 전용)

이 스킬은 **이 저장소(agent-toolkit)** 의 세 가지 문서가 실제 디렉토리·플러그인 상태와 어긋나지 않도록 갱신한다.

대상 문서:
- `.claude/CLAUDE.md` — 저장소의 정체성·디렉토리 구조·스킬 분류 기준 (사람·에이전트가 처음 읽는 문서)
- `README.md` — 저장소를 처음 여는 사람을 위한 한 페이지짜리 진입점 + **하단 "구성" 섹션의 스킬·템플릿 표**
- `docs/catalog.md` — `skills/`, `skills-workflow/`, `skills-system/` 에 등록된 스킬 카탈로그

> 이 세 문서는 **서로 정합성**을 가져야 한다. CLAUDE.md가 말하는 디렉토리 구조와 catalog.md의 섹션, README.md의 요약이 동시에 같은 그림을 그려야 한다.

---

## 언제 트리거되는가

다음 중 하나라도 발생하면 갱신한다:

1. `skills/`, `skills-workflow/`, `skills-system/` 어딘가에 스킬을 **추가/삭제/이동** 했다.
2. 스킬의 `SKILL.md` frontmatter `description` 또는 `name`을 의미 있게 바꿨다.
3. `.claude-plugin/plugin.json`의 `skills` 배열 또는 plugin 메타(`name`, `description`, `version`)를 바꿨다.
4. 디렉토리 정책(어떤 종류의 스킬이 어디에 들어가는지)을 바꿨다.
5. `agents/`, `hooks/`, `commands/` 디렉토리를 새로 활성화했다(빈 placeholder 단계가 아니라 실제 자산이 들어왔을 때).

> 단순 오타·문구 다듬기는 트리거 대상이 아니다. **상태 변화**가 있을 때만 돈다.

---

## 워크플로우

### Step 1 — 현재 상태 스캔

다음을 **병렬로** 읽어 현재 상태를 파악한다:

```bash
# 디렉토리 구조와 스킬 목록
ls -1 skills/ skills-workflow/ skills-system/ 2>/dev/null

# plugin.json (등록된 skills 배열, 메타)
cat .claude-plugin/plugin.json

# 각 스킬의 frontmatter — name, description 추출용
# 한 번에 모으는 게 빠르다:
for d in skills skills-workflow skills-system; do
  for s in "$d"/*/SKILL.md; do
    [ -f "$s" ] || continue
    echo "=== $s ==="
    awk '/^---$/{c++; next} c==1' "$s"   # frontmatter 블록만
  done
done
```

추가로 확인할 것:
- `agents/`, `hooks/`, `commands/` 디렉토리에 실제 파일이 있는가? (있으면 README/CLAUDE.md에서 "필요해지면 추가" → "활성화됨"으로 톤 변경)
- 기존 세 문서를 읽어 **무엇이 바뀌어야 하는지** 차이를 식별한다.

### Step 2 — `docs/catalog.md` 갱신

이 문서는 가장 기계적으로 갱신할 수 있다. 형식:

```markdown
# Skill Catalog

> `agent-toolkit` plugin에 등록된 스킬 목록. 분류 기준은 [.claude/CLAUDE.md](../.claude/CLAUDE.md) 참고.
>
> Last updated: YYYY-MM-DD

## 요약

| 디렉토리 | 개수 |
|---|---|
| `skills/` (독립 스킬) | <N> |
| `skills-workflow/` (워크플로우) | <N> |
| `skills-system/` (메타·스캐폴딩) | <N> |
| **합계** | **<N>** |

---

## skills/ — 독립 스킬

단일 목적, 다른 스킬에 의존하지 않고 단독으로 동작.

| 이름 | 한 줄 설명 | 주요 트리거 |
|---|---|---|
| [<name>](../skills/<name>/SKILL.md) | <description 요약 — 실제 SKILL.md description에서 첫 의미 단위> | <트리거 어구 요약> |
...

---

## skills-workflow/ — 워크플로우 스킬

`skills/`의 여러 스킬을 묶어 순차/병렬로 돌리는 오케스트레이션 스킬.

_(현재 등록된 스킬 없음)_  ← 비어있을 때만 이렇게.

---

## skills-system/ — 메타·스캐폴딩 스킬

빈 곳에 프로젝트·플러그인·디렉토리 구조 자체를 세우는 더 큰 작업.

| 이름 | 한 줄 설명 | 주요 트리거 |
|---|---|---|
...

---

## 갱신 방법

이 문서는 `.claude/skills/update-project-docs` 스킬로 갱신한다.
```

**작성 규칙:**

- **`Last updated`** — 오늘 날짜로 갱신. 시스템 컨텍스트의 `currentDate`를 사용한다.
- **한 줄 설명** — 각 스킬의 `description` 첫 의미 단위(보통 첫 번째 마침표·대시·줄임표 앞)를 간결히. 트리거 예시("~~ 시 사용", "~~ 요청 시")는 잘라내고 **무엇을 하는지**만 남긴다.
- **주요 트리거** — `description`에서 추출한 호출 시점·사용 동사 1~2개. 한 칸에 30자 이내로.
- **이름 정렬** — 알파벳 오름차순.
- **빈 섹션** — `_(현재 등록된 스킬 없음)_` 마커를 유지. 섹션 자체를 지우지 않는다.
- **링크 경로** — 항상 `../<dir>/<name>/SKILL.md` (catalog.md 기준 상대경로).

### Step 3 — `.claude/CLAUDE.md` 갱신

이 문서는 정책 변화가 있을 때만 손댄다. 다음 항목을 현재 상태와 대조:

- **디렉토리 구조 트리** — `agents/`, `hooks/`, `commands/`가 활성화되면 "필요해지면 추가" 주석을 실제 설명으로 바꾼다. `.claude/skills/` 같은 project-local 위치가 새로 쓰이기 시작하면 트리에 추가한다.
- **스킬 분류 기준 표** — 디렉토리가 추가/제거되었으면 행을 더하거나 뺀다.
- **등록 상태** — `~/.claude/settings.json` 키 이름이 바뀌었거나 marketplace 이름이 바뀌었으면 갱신.
- **정체성 블록** — 의도적으로 바꾼 게 아니면 건드리지 않는다.

> 이 문서는 **에이전트가 첫 컨텍스트로 읽는 문서**다. 길이를 늘리지 말고, 사실 관계만 정확히 유지한다.

### Step 4 — `README.md` 갱신

저장소 루트에 처음 들어온 사람이 30초 안에 "이게 뭔지" 파악할 수 있게 만든다.

README는 **두 부분**으로 나뉜다:

1. **상단(소개·설치·갱신)** — 한 화면짜리 진입점. 정책 변화가 없으면 거의 손대지 않는다.
2. **하단 "구성" 섹션** — `skills/`, `skills-system/`, `skills-workflow/`, `templates/` 네 디렉토리의 표. **상태가 바뀔 때마다 반드시 갱신한다.**

#### 상단 권장 구성

```markdown
# agent-toolkit

> 개인용 Claude Code plugin. 일상 워크플로우에 쓰는 스킬을 한 곳에 모은다.

## 설치
... (clone + /plugin marketplace add + /plugin install)

## 무엇이 들어 있나
- `skills/` — 독립 스킬
- `skills-workflow/` — 워크플로우 스킬
- `skills-system/` — 메타·스캐폴딩 스킬
- `templates/` — 다른 스킬이 골격 원본으로 쓰는 템플릿 모음

전체 목록과 트리거는 [docs/catalog.md](docs/catalog.md). 디렉토리 분류 기준은 [.claude/CLAUDE.md](.claude/CLAUDE.md).

## 갱신
스킬을 추가/이동/삭제했으면 `update-project-docs` 스킬로 문서를 동기화한다.
```

#### 하단 "구성" 섹션 — 4개 표 (필수)

`---` 가로줄 아래에 `## 구성` 단일 H2로 시작하고, 그 안에 4개 H3 섹션을 둔다. **순서·헤더 고정**.

```markdown
---

## 구성

### skills/

단일 목적, 다른 스킬에 의존하지 않고 단독으로 동작.

| 이름 | 설명 |
|---|---|
| [<name>](skills/<name>/SKILL.md) | <한 줄 설명> |
...

### skills-system/

빈 곳에 프로젝트·플러그인·디렉토리 구조 자체를 세우는 메타·스캐폴딩 작업.

| 이름 | 설명 |
|---|---|
| [<name>](skills-system/<name>/SKILL.md) | <한 줄 설명> |
...

### skills-workflow/

`skills/`의 여러 스킬을 묶어 순차/병렬로 돌리는 오케스트레이션 스킬.

_(현재 등록된 스킬 없음)_   ← 비어 있을 때만. 스킬이 생기면 표로 교체.

### templates/

다른 스킬이 골격 원본으로 사용하는 템플릿 모음. 직접 로드되지 않는다.

| 이름 | 설명 |
|---|---|
| [<dir>/](templates/<dir>/) | <한 줄 설명 — 어떤 스킬이 무슨 용도로 쓰는지> |
...
```

**작성 규칙 (하단 구성 섹션):**

- **링크 경로** — README는 저장소 루트 기준 상대경로(`skills/<name>/SKILL.md`). catalog.md(`../skills/...`)와 다르다는 점 주의.
- **한 줄 설명** — 각 스킬의 `description` frontmatter에서 **무엇을 하는지**만 추출. 트리거 어구(`"~ 시 사용"`, 따옴표로 둘러싼 호출 문구), 부속 reference 안내, 사용 시점 나열은 잘라낸다. 표 한 칸에 한 줄로 끝나도록 압축.
- **이름 정렬** — 알파벳 오름차순.
- **빈 섹션** — `_(현재 등록된 스킬 없음)_` 마커를 유지. 섹션 자체를 지우지 않는다.
- **templates/** — 디렉토리 단위로 한 행. 그 디렉토리가 어떤 스킬에 의해 어떤 용도로 소비되는지 한 줄로 적는다 (예: "`project-setup` 스킬이 설치하는 작업 문서 골격").
- **개수 카운트는 적지 않는다** — 표 자체가 카운트를 보여준다. 상단 "무엇이 들어 있나"에도 개수 숫자를 박지 않는다 (변동 시 누락 위험).

**작성 규칙 (상단):**

- 길지 않게 — 한 화면 안에서 끝낸다.
- 외부에 공개·재배포하는 저장소가 아니므로 배지·CI·라이선스 섹션은 추가하지 않는다.
- 이미 README.md가 비어 있다면 위 템플릿으로 **새로 쓴다** (Write 사용). 내용이 있으면 부분 수정(Edit).

### Step 5 — 정합성 검증

세 문서를 모두 갱신한 뒤 다음을 확인:

1. **개수 정합성** — `docs/catalog.md`의 요약 표와 `README.md`의 "무엇이 들어 있나" 개수가 동일한가?
2. **디렉토리 정합성** — `.claude/CLAUDE.md`의 트리에 나오는 디렉토리가 `plugin.json`의 `skills` 배열과 일치하는가?
3. **링크 유효성** — catalog.md에 적힌 `../skills/<name>/SKILL.md` 파일들이 실제로 존재하는가?
4. **분류 정합성** — `skills/`에 들어 있는 스킬이 다른 스킬을 호출하지 않는지(워크플로우라면 `skills-workflow/`로 옮겨야 한다는 것을 사용자에게 알린다).

검증 명령 예시:

```bash
# 카탈로그에 적힌 모든 SKILL.md 경로가 실존하는지
grep -oE '\(\.\./[a-z-]+/[a-z0-9-]+/SKILL\.md\)' docs/catalog.md \
  | tr -d '()' \
  | sed 's|^\.\./||' \
  | while read p; do [ -f "$p" ] || echo "MISSING: $p"; done
```

`MISSING:`이 한 줄도 나오지 않아야 한다.

### Step 6 — 사용자에게 보고

다음 형식의 짧은 요약을 출력한다:

- 갱신된 파일과 변경 요지(추가된 스킬, 분류 변경 등)
- 정합성 검증 결과 (OK / 불일치 항목)
- 사용자 확인이 필요한 모호한 분류 결정이 있으면 **묻기**

---

## 자주 만나는 케이스

**케이스 1 — 새 스킬 추가**
1. 해당 디렉토리에 SKILL.md가 있는지 확인
2. catalog.md의 해당 섹션에 행 추가, 요약 표의 개수 +1, 합계 +1
3. README.md 개수 동기화
4. CLAUDE.md는 보통 손대지 않음 (분류 정책이 바뀌지 않았다면)

**케이스 2 — 스킬을 `skills/`에서 `skills-workflow/`로 이동**
1. catalog.md에서 행을 옮기고, 두 섹션의 개수 갱신
2. README.md 개수 갱신
3. CLAUDE.md는 변경 없음

**케이스 3 — 새 디렉토리(`agents/`)에 첫 자산 추가**
1. CLAUDE.md 트리의 `# 필요해지면 추가` 주석을 실제 설명으로 교체
2. README.md "무엇이 들어 있나"에 항목 추가
3. catalog.md는 스킬 카탈로그이므로 손대지 않음 (필요하면 별도 `docs/agents.md` 신설을 사용자에게 제안)

**케이스 4 — 스킬의 description만 바뀜**
1. catalog.md의 해당 행 "한 줄 설명"·"주요 트리거" 갱신
2. 개수 변화 없으므로 다른 문서는 손대지 않음

---

## 하지 말 것

- 스킬의 `SKILL.md` 자체를 이 스킬에서 수정하지 않는다 — 이 스킬은 **저장소 메타 문서**만 다룬다.
- `plugin.json`을 임의로 바꾸지 않는다 — 새 디렉토리가 생겨 `skills` 배열을 늘려야 한다면 사용자에게 확인을 받는다.
- 갱신 중에 발견한 분류 오류(예: `skills/`에 들어간 워크플로우)를 자동으로 옮기지 않는다 — **리포트만** 하고 사용자 결정을 기다린다.
- `Last updated` 외에 변동 사유, 작업자, 변경 로그 같은 메타데이터를 늘리지 않는다 — git history가 그 역할을 한다.
