---
name: kb-add
description: |
  Knowledge Base에 새 지식을 추가하는 **단일 input 통로**. URL·파일·텍스트 덤프를 받아 적절한 폴더에 마크다운 문서로 저장한다. 기본은 신규 파일, 명시 신호가 있으면 기존 문서에 섹션 append. 기존 본문 수정·삭제·git 커밋은 하지 않는다. Obsidian 볼트와 호환되며 위키링크·tags·created frontmatter를 자동 부여한다.
  트리거: "/kb-add {내용}", "KB에 추가해줘", "이거 정리해서 넣어줘", "지식 저장소에 추가"
---

# kb-add — KB 단일 input 통로

URL·파일·텍스트 덤프를 Obsidian 볼트에 마크다운 문서로 저장한다.

> **Obsidian 스킬 활용**
> - `obsidian-markdown` — 위키링크, 콜아웃, frontmatter 등 Obsidian Flavored Markdown 문법 참조.
> - `defuddle` — URL 입력 시 깨끗한 마크다운 추출.

---

## 핵심 원칙

1. **하나의 입구** — URL이든 파일이든 텍스트든 이 스킬 하나로 받는다.
2. **신규 우선, append는 신호 있을 때만** — 그래프 뷰의 노드 수를 늘리는 방향이 기본.
3. **수정은 사용자 명시 또는 LLM 제안 + 사용자 컨펌** — modify 모드는 (a) 입력에 "수정/변경/바꿔/업데이트/교체/rotate/갱신" 동사가 있거나, (b) LLM이 판단해 "이건 append보다 수정이 낫다"고 제안하고 **사용자가 명시적으로 동의**한 경우에만 실행. **어떤 경우에도 사용자 허가 없이 수정하지 않는다** — 허가 없으면 무조건 append/신규로 폴백. remove는 (a) 경로만 — LLM 자율 제안 금지.
4. **remove는 별도 문구 컨펌** — 단순 `Y` 답변으로는 제거 안 됨. "이 부분 제거한다" 같은 명시적 문구를 사용자가 직접 타이핑해야 진행.
5. **git에 손대지 않음** — 커밋·푸시·`git add`를 호출하지 않는다. 백업은 Obsidian Git 플러그인 등 사용자 환경에 위임.
6. **수정·제거 시 스냅샷 의무** — 쓰기 직전 `~/.kb-snapshots/{ts}-{filename}` 복사. 신규/append는 스냅샷 불필요.
7. **atomic write** — 모든 파일 쓰기는 `.tmp` → `mv` 패턴.

---

## Step 0. 볼트 경로 확인

`~/.config/kb/path` 파일을 읽어 볼트 절대 경로를 얻는다 (단일 줄).

```bash
test -f ~/.config/kb/path && cat ~/.config/kb/path
```

### 파일이 없거나 비어있는 경우

다음 안내 메시지를 출력하고 **사용자 응답을 기다린다** (자동 진행 금지):

```
⚠️  KB 볼트 경로가 설정되어 있지 않습니다.

볼트로 사용할 디렉토리의 **절대 경로**를 알려주세요.
  예: /Users/you/workspace/KnowledgeBase

조건:
  - 디렉토리가 미리 존재해야 합니다.
  - 응답하면 ~/.config/kb/path 에 저장되어 모든 kb-* 스킬에서 공유됩니다.

직접 설정하려면 (대신 셸에서):
  mkdir -p ~/.config/kb && echo "/your/vault/path" > ~/.config/kb/path

설정을 원치 않으면 "취소"라고 답하세요.
```

### 사용자 응답 처리

| 응답 | 동작 |
|---|---|
| 절대 경로 (`/`로 시작) | 디렉토리 존재 확인 → 존재하면 저장 후 진행, 없으면 "디렉토리가 존재하지 않습니다: {경로}" 출력 후 재질문 |
| 상대 경로 또는 `~/...` | "절대 경로(`/`로 시작)를 입력해주세요" 출력 후 재질문 |
| "취소" 또는 빈 응답 | 즉시 종료, 아무 동작 안 함 |

저장 명령:

```bash
mkdir -p ~/.config/kb
echo "{검증 통과한 절대 경로}" > ~/.config/kb/path
```

이후 모든 경로는 `{kb_root}`로 표기.

---

## Step 1. 입력 타입 감지

| 입력 | 타입 | 처리 |
|---|---|---|
| `http(s)://...` | `url` | → Step 2A |
| 존재하는 파일 경로 (`.pdf`, `.pptx`, `.docx`, `.md`, 이미지 등) | `file` | → Step 2B |
| 그 외 텍스트 | `text` | → Step 2C |
| **인자 없음** | `inbox` | → Step 2D |

질문 형태("~란?", "~알려줘")로 보이면 **`/kb-search`를 안내**하고 종료한다.

---

## Step 2. 내용 준비

### 2A. URL

1. `defuddle` 또는 WebFetch로 본문 추출.
2. 사이즈 sanity check — 추출 결과가 200KB를 초과하면 사용자에게 "원문이 큽니다. 진행할까요?" 1회 확인.
3. 원본을 `{kb_root}/_raw/{slug}.md`에 저장. slug는 영숫자·하이픈만 허용 (path traversal 방지).
4. 추출 본문을 1~3문단으로 정리.

### 2B. 외부 파일

1. 파일명을 slug화 (영숫자·하이픈·언더스코어·점). `..` 거부.
2. `{kb_root}/_raw/{slug}.{ext}`로 복사.
3. 텍스트 추출:
   - PDF/PPTX/DOCX → 텍스트 추출
   - 이미지 → LLM이 보고 설명 생성
4. 추출 본문을 1~3문단으로 정리.

### 2C. 텍스트 덤프

1. 입력에 **구체적 사실·경험·결정사항**이 있는지 판단.
2. "Python REST API 사용법" 같이 LLM이 일반 지식을 생성해야 하는 요청은 거부:
   > "구체적인 내용이나 출처를 제공해주세요. 일반 지식 생성은 이 KB의 정책이 아닙니다."
3. 사용자에게 1회 선택:
   > "정리해서 저장할까요, 원문 그대로 저장할까요? [정리/원문]"
4. 응답에 맞춰 본문 준비.

### 2D. Inbox 정리 (인자 없음)

1. `{kb_root}/_inbox/`의 파일 목록을 스캔.
2. 비어있으면 안내 후 종료:
   > "_inbox/가 비어있습니다. 정리할 항목이 없습니다."
3. 파일 1개씩 다음을 수행:
   a. 파일 내용을 읽고 1~3문단으로 요약 추출.
   b. 파일 타입 따라 Step 2A/2B/2C와 동일하게 처리하되, **_raw/ 복사는 건너뜀** (이미 볼트 안에 있음).
   c. Step 3·4·5·6·7을 그대로 진행.
   d. 컨펌 시 추가 옵션 `s/skip` 제공 — 이 파일은 _inbox에 그대로 남김.
   e. 승인 후 쓰기 완료되면 **원본 _inbox 파일은 삭제** (다른 곳에 이미 정리되었으므로).
4. 모든 파일 처리 후 한 줄 요약: "Inbox {N}개 처리: 정리 {n}, 건너뜀 {s}".

---

## Step 3. 동작 모드 판단

입력에서 **수정·제거 동사**가 있는지 먼저 확인하고, 없으면 신규/append 흐름으로 간다.

### Step 3-0. 수정·제거 의도 감지

modify 모드는 두 경로로, remove 모드는 한 경로로만 진입한다.

| 진입 경로 | 조건 | 분기 |
|---|---|---|
| **modify (A) 사용자 명시** | 입력에 "수정/변경/바꿔/업데이트/교체/rotate/갱신" 동사 + 대상 파일 지정 | → Step 3-M |
| **modify (B) LLM 제안** | LLM이 입력을 보고 "신규/append보다 기존 영역 수정이 더 정확하다"고 판단 (예: 기존 표의 한 셀이 갱신된 값임이 명백, 기존 코드블록의 키-값이 새 값으로 바뀐 게 명백) | → Step 3-M (단, 진입 시 사용자 컨펌 필수 — 거부하면 신규/append로 폴백) |
| **remove** | 입력에 "삭제/제거/지워/빼줘" 동사 + 대상 파일 지정. **LLM 자율 제안 금지** | → Step 3-R |
| (없음) | 그 외 | → Step 3-1 (신규/append) |

**중요 안전 규칙:**
- **사용자 허가 없이는 어떤 경우에도 수정·제거를 실행하지 않는다.** (B) 경로에서 사용자가 거부하면 자동으로 신규/append로 폴백.
- (B) LLM 제안 시 *왜* 수정이 낫다고 판단했는지 **한 줄 근거를 diff preview에 함께 출력**한다.
- remove는 LLM이 자율 제안하지 않는다 (위험도 큼). 사용자 명시 동사 + 별도 문구 컨펌 필수.

대상 파일이 모호하면 사용자에게 1회 질문:
> "어느 파일을 수정할까요? (예: `[[credentials]]`)"

대상 미지정 상태로는 진행하지 않는다.

### Step 3-1. 신규 vs append 판단 (기본 흐름)

기본은 **신규 파일**. 다음 신호 중 하나라도 있으면 **append**도 옵션으로 함께 제시한다.

| 신호 | 예시 |
|---|---|
| 사용자가 명시 | "이거 [[RAG-개념]]에 추가해줘" |
| 입력이 짧고 (3문단 이하) 기존 문서의 한 섹션 보강 | 기존 `[[RAG-개념]]`에 "## 단점" 섹션이 없는데 단점 정보를 받음 |
| 시간 기록형 폴더 | `01_Projects/EVAX/회의록/` → 항상 신규 (날짜별) |

### Step 3-2. 후보 탐색 (신규/append용)

볼트에서 입력 키워드와 매칭되는 기존 문서를 최대 3개 찾는다 (제목·tags grep).

```bash
grep -rl "tags:.*{키워드}" {kb_root} --include="*.md" 2>/dev/null | head -3
```

### Step 3-M. Modify 모드

진입 경로:
- **(A) 사용자 명시** — Step 3-0의 명시 동사로 진입. 바로 진행.
- **(B) LLM 제안** — LLM이 modify가 더 정확하다고 판단해 진입. diff preview에 **제안 근거**를 1줄 함께 출력하고, 사용자가 명시적으로 동의(`Y`)해야만 적용.

1. 대상 파일을 읽는다.
2. LLM이 **수정할 정확한 위치**를 식별한다:
   - 표(table) 셀
   - 리스트 항목
   - 코드블록(YAML/JSON/env) 안의 키-값
   - 산문 한 문장 (가능하면 피하고 사용자에게 재확인)
3. **diff preview**를 출력:
   ```
   === 수정 계획: credentials.md ===
   [LLM 제안 근거] (B 경로일 때만)  사용자 입력이 기존 표의 prod-db row의 password 셀을 갱신하는 형태로 보입니다.
   대상 영역: 표 (prod-db 행, password 셀)

   - | prod   | db.prod:5432 | old-secret-xxx |
   + | prod   | db.prod:5432 | new-secret-yyy |

   [Y] 수정 진행  /  [n] 취소  /  [a] append로 폴백 (B 경로일 때만 표시)
   ```
4. **응답별 처리:**
   - **`Y`** → 진행:
     a. 스냅샷: `mkdir -p ~/.kb-snapshots && cp {파일} ~/.kb-snapshots/{YYYY-MM-DD-HHMMSS}-{basename}`
     b. atomic write로 수정 적용
     c. 파일 끝에 변경 로그 한 줄 추가:
        ```
        <!-- updated 2026-05-22: prod-db password rotated -->
        ```
   - **`n` / 취소 / 빈 응답** → 즉시 종료, 어떤 변경도 안 함.
   - **`a` (B 경로 한정)** → Step 3-1로 폴백해 신규/append 흐름으로 재진입. 새로 폴더·모드 선택 후 진행.

**중요:** `Y`가 아닌 모든 응답은 "허가 안 함"으로 간주 — 절대 silent modify 안 함. 애매하면 `n`으로 처리.

산문 수정은 정보 손실 위험이 크므로 diff 위에 다음 경고를 추가:
> "⚠️ 산문 영역 수정입니다. 원문 의미가 바뀌지 않는지 확인하세요."

### Step 3-R. Remove 모드

1. 대상 파일을 읽고 **제거할 영역**을 식별한다.
2. 제거 계획을 빨간색 마킹으로 출력:
   ```
   === 제거 계획: 03_Resources/credentials.md ===

   다음을 제거합니다:

   ─────────────────────────────────────
   | deprecated-db | db.old:5432 | old-pass |
   ─────────────────────────────────────

   ⚠️ 제거는 되돌리기 어렵습니다 (스냅샷은 ~/.kb-snapshots/에 보관).

   진행하려면 **"이 부분 제거한다"** 라고 정확히 입력해주세요.
   취소하려면 다른 어떤 답이든 됩니다.
   ```
3. **사용자 응답 검사:**
   - 정확히 `"이 부분 제거한다"` 문자열만 → 진행
   - 그 외 모든 응답 (`Y`, `yes`, `확인`, 빈 응답 등) → **취소**, 아무 변경 안 함

   이 게이트는 단순 `Y` 오타·반사적 confirm을 막기 위함이다.
4. 진행 시:
   a. 스냅샷: `mkdir -p ~/.kb-snapshots && cp {파일} ~/.kb-snapshots/{YYYY-MM-DD-HHMMSS}-{basename}`
   b. atomic write로 해당 영역 삭제
   c. 파일 끝에 변경 로그 한 줄 추가:
      ```
      <!-- removed 2026-05-22: deprecated-db row -->
      ```

**여러 영역 제거가 필요하면 각각 별도 확인을 받는다** (한 번에 일괄 제거 금지).

---

## Step 4. 폴더 선정

신규 파일 모드인 경우:

1. `{kb_root}` 하위 폴더 트리를 `ls -R`로 스캔 (`_raw/`, `_inbox/`, `_archive/`, `.obsidian/`, `.claude/` 제외).
2. 입력 내용 키워드와 폴더명 매칭 → 후보 1~2개 선정.
3. 매칭되는 폴더가 없으면 다음 3가지를 제안:
   - 루트에 `{새 카테고리}/` 신규 폴더 생성 (주제 폴더이므로 prefix 없음)
   - `_inbox/`에 임시 보관 (분류 보류)
   - 사용자가 경로 직접 지정

### 폴더 컨벤션

| 종류 | 규칙 | 예 |
|---|---|---|
| **주제 폴더** | prefix 없음 | `RAG/`, `Python/`, `EVAX/` |
| **특수 폴더** | **`_` prefix 필수** | `_archive/`, `_inbox/`, `_raw/` |

- 새 주제 폴더를 만들 때 절대 `_` prefix를 붙이지 않는다.
- 새 특수 폴더가 필요하면 (예: `_secrets/`, `_scratch/` 등) 반드시 `_` prefix.
- 스킬은 **기존 특수 폴더(`_*`)에 새 콘텐츠를 자동 배치하지 않는다** — 사용자가 명시적으로 지정한 경우에만.

---

## Step 5. 관련 문서 발굴 (그래프 뷰 보강)

새 문서에 위키링크를 자동 삽입하기 위해, 관련 기존 문서를 최대 5개 찾는다.

1. 입력 본문에서 키워드·고유명사 추출.
2. tags frontmatter grep + 제목 grep.
3. 관련도 상위 3~5개 선정.

이 목록은 새 문서 하단 `## 관련` 섹션에 위키링크로 들어간다.

---

## Step 6. 일괄 컨펌

신규 + append 둘 다 가능한 경우 한 번의 컨펌으로 분기:

```
=== KB Add 계획 ===

[모드 A — 신규 (추천)]
  파일: 03_Resources/RAG/rag-단점.md
  tags: [rag, llm, 단점]
  관련 링크: [[RAG-개념]], [[벡터DB-비교]], [[Karpathy-wiki-design]]

[모드 B — append]
  대상: 03_Resources/RAG/RAG-개념.md
  추가 섹션: ## 단점  <!-- appended 2026-05-22 -->

어느 쪽? [A/B/취소]
```

신규만 가능하면 단순 컨펌:

```
→ 03_Resources/RAG/rag-단점.md 에 신규 생성합니다. OK? [Y/n]
```

---

## Step 7. 쓰기

### 7-1. 신규 파일

```markdown
---
tags: [{키워드 3~5개}]
created: 2026-05-22
source: "[[_raw/{원본 slug}]]"   # url/file 타입일 때만
---

# {제목}

{본문}

## 관련

- [[관련 문서 1]]
- [[관련 문서 2]]
- [[관련 문서 3]]

---
원본: [[_raw/{원본 slug}]]   <!-- url/file 타입일 때만, frontmatter source와 중복이지만 본문에서도 클릭 가능하게 -->
```

### 7-2. append

대상 파일의 끝에 새 섹션을 추가:

```markdown

## {섹션 제목}  <!-- appended 2026-05-22 -->

{본문}

관련: [[연결 문서]]
```

- **append 모드에서는 기존 섹션을 수정하지 않는다.** 항상 파일 끝에 새 `## `로 append. (기존 본문을 바꾸려면 Step 3-M의 modify 모드를 명시적으로 호출해야 함)
- append 본문 안에도 최소 1개의 위키링크를 포함시켜 그래프 엣지를 늘린다.

### 7-3. atomic write

모든 쓰기는 다음 패턴:

```bash
tmpfile=$(mktemp "{대상파일}.XXXXXX.tmp")
cat > "$tmpfile" <<'EOF'
{내용}
EOF
mv "$tmpfile" "{대상파일}"
```

append의 경우도 전체 새 내용을 tmp에 쓰고 rename. (부분 append는 원자성 보장 안 됨)

### 7-4. qmd 인덱스 리빌드 (best-effort)

쓰기가 끝나면 검색 인덱스를 갱신한다. 실패는 무시 — qmd 없거나 인덱스 미사용 환경에서도 스킬은 동작해야 함.

```bash
qmd index rebuild 2>/dev/null || true
```

Inbox 정리 모드(2D)에서는 **모든 파일 처리 후 1회만** 실행 (반복 호출 비용 회피).

---

## 하지 않는 일

- ❌ `git add` / `git commit` / `git push` — 어떤 git 명령도 호출하지 않는다.
- ❌ 사용자 컨펌 없이 **기존 본문을 한 줄도 수정·삭제하지 않는다.** (modify는 사용자 명시 또는 LLM 제안 → 사용자 `Y` 컨펌 시에만 / remove는 사용자 명시 동사 + 별도 문구 컨펌 시에만)
- ❌ Remove 모드에서 단순 `Y` 답변으로 진행하지 않는다 — 반드시 `"이 부분 제거한다"` 정확한 문구.
- ❌ 한 번에 여러 영역을 일괄 제거하지 않는다 — 각 영역마다 개별 확인.
- ❌ 파일 자체 삭제·이동·이름변경 — Obsidian에서 직접.
- ❌ frontmatter 수정 — 별도 작업, 본문 수정 모드에 포함하지 않음.
- ❌ 폴더별 인덱스 파일(`00_index_*.md`) 생성·유지 — 폴더 트리·Obsidian 그래프 뷰·qmd 검색으로 충분.
- ❌ SCHEMA.md 레지스트리 — 폴더 그 자체가 스키마.
- ❌ 5개 문서 자동 cascade append — 그건 `/kb-lint --boost-links`의 책임.

---

## 출력

완료 시 한 줄 요약:

```
KB Add 완료.
- 모드: 신규
- 경로: 03_Resources/RAG/rag-단점.md
- tags: [rag, llm, 단점]
- 추가 위키링크: 3개
```

append 모드:

```
KB Add 완료.
- 모드: append
- 대상: 03_Resources/RAG/RAG-개념.md
- 추가 섹션: ## 단점
```

modify 모드:

```
KB Add 완료.
- 모드: modify
- 대상: 03_Resources/credentials.md (prod-db 행, password 셀)
- 스냅샷: ~/.kb-snapshots/2026-05-22-153012-credentials.md
- 변경 로그: <!-- updated 2026-05-22: prod-db password rotated -->
```

remove 모드:

```
KB Add 완료.
- 모드: remove
- 대상: 03_Resources/credentials.md (deprecated-db 행)
- 스냅샷: ~/.kb-snapshots/2026-05-22-153012-credentials.md
- 변경 로그: <!-- removed 2026-05-22: deprecated-db row -->
```

inbox 정리 모드:

```
Inbox 정리 완료.
- 처리: 5개 (정리 4, 건너뜀 1)
- 새 문서: 3개, append: 1개
```

---

## 예시

```
# 웹 링크
/kb-add https://example.com/rag-tutorial
  → _raw/rag-tutorial.md 저장
  → "→ 03_Resources/RAG/rag-tutorial-정리.md 신규 생성. OK?"
  → 신규 파일 작성 (위키링크 3개 포함)

# 기존 문서 보강
/kb-add 이거 [[RAG-개념]]에 추가해줘
  RAG는 cache-augmented 방식 대비 latency가 높다.
  → "→ RAG-개념.md 끝에 '## cache-augmented 비교' 섹션 append. OK?"
  → append 실행

# 거부
/kb-add Docker 사용법
  → "구체적인 내용이나 출처를 제공해주세요."

# Modify 모드 — (A) 사용자 명시
/kb-add [[credentials]]의 prod-db password를 new-secret-yyy 로 변경해줘
  → Step 3-0: "변경" 동사 감지 → modify 모드 (A 경로)
  → credentials.md 읽고 prod-db 행, password 셀 식별
  → diff preview 출력
  → "Y" 응답
  → ~/.kb-snapshots/2026-05-22-153012-credentials.md 스냅샷
  → atomic write + <!-- updated 2026-05-22 ... --> 로그

# Modify 모드 — (B) LLM 제안
/kb-add [[credentials]] prod-db 새 password: new-secret-yyy
  → Step 3-0: 명시 동사 없지만, 입력이 기존 표 셀 갱신 패턴
  → LLM이 modify 모드 제안 (B 경로)
  → diff preview + 제안 근거 1줄 출력:
       [LLM 제안 근거] 입력이 기존 표의 prod-db row password 셀을 갱신하는 형태
       [Y] 수정 / [n] 취소 / [a] append로 폴백
  → "Y" 응답 → 수정 진행
  → "a" 응답 → Step 3-1로 폴백 → 신규/append 흐름 재진입
  → "n" 응답 → 즉시 종료, 어떤 변경도 없음

# Remove 모드 (deprecated 행 제거)
/kb-add [[credentials]]에서 deprecated-db 행 제거해줘
  → Step 3-0: "제거" 동사 감지 → remove 모드
  → 제거 대상 영역 출력
  → "이 부분 제거한다"라고 정확히 입력 요청
  → 사용자: "이 부분 제거한다"  ← Y 아님
  → 스냅샷 + 제거 + <!-- removed 2026-05-22 ... --> 로그

# Remove 거부 (단순 Y는 차단)
/kb-add [[credentials]]에서 staging-db 행 삭제
  → 제거 계획 출력
  → 사용자: "Y"
  → 취소됨. 어떤 변경도 없음.
```
