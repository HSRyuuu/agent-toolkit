---
name: kb-add
description: |
  Knowledge Base에 새 지식을 추가하는 LLM wiki ingest 통로. URL·파일·텍스트·_inbox 입력을 `sources -> wiki -> schema` 모델로 처리해 원본 source를 보존하고, canonical wiki와 daily log를 연결하며, 누적 주제는 facts-preserving merge-preview로 기존 문서 갱신을 제안한다. 기존 본문 수정·병합은 preview + 사용자 승인 후에만 수행하고, 삭제는 별도 안전 확인을 요구한다.
  트리거: "/kb-add {내용}", "KB에 추가해줘", "이거 정리해서 넣어줘", "지식 저장소에 추가", "온보딩 내용 저장", "회사생활 가이드에 반영"
---

# kb-add — LLM Wiki Ingest

입력을 개인 KB에 추가하되, 단순히 노드 수를 늘리는 것이 아니라
`sources -> wiki -> schema` 흐름에 맞춰 원본과 canonical wiki를 함께 유지한다.

공통 규칙과 양식:

- Schema: `skills/kb-common/references/llm-wiki-schema.md`
- Canonical template: `skills/kb-common/templates/canonical-wiki.md`
- Daily log template: `skills/kb-common/templates/daily-log.md`
- Helper: `skills/kb-common/scripts/validate_llm_wiki.py`

---

## 핵심 원칙

1. **LLM wiki 우선** — KB의 1순위 모델은 `sources -> wiki -> schema`다.
2. **source 보존** — URL, 파일, 원문 메모, daily log는 원본 맥락을 잃지 않게 보존한다.
3. **canonical wiki 우선** — 나중에 다시 찾을 지식은 날짜 없는 canonical wiki에 모은다.
4. **daily log 보존** — 날짜에 묶인 온보딩·회의·작업 메모는 daily log로 남길 수 있다.
5. **facts-preserving 병합** — 기존 canonical 문서 갱신은 사실을 해치지 않는 `merge-preview` 또는 `modify-preview`로 제안한다.
6. **승인 없는 수정 금지** — 기존 본문 수정·병합은 대상 영역, 변경 전후, 사실 보존 근거를 보여주고 사용자 승인 후에만 수행한다.
7. **삭제는 별도 안전 게이트** — remove/delete는 사용자 명시 + 별도 문구 확인 없이는 실행하지 않는다.
8. **git에 손대지 않음** — `git add`, `git commit`, `git push`를 호출하지 않는다.
9. **atomic write** — 모든 쓰기는 `.tmp` 작성 후 rename한다.

---

## Step 0. 볼트 경로 확인

`~/.config/kb/path` 파일을 읽어 볼트 절대 경로를 얻는다.

```bash
test -f ~/.config/kb/path && cat ~/.config/kb/path
```

파일이 없거나 비어 있으면 사용자에게 볼트 절대 경로를 묻고, 존재하는 디렉터리인지 확인한 뒤 저장한다.
상대 경로와 `~/...`는 받지 않는다. 사용자가 "취소"하거나 빈 응답이면 아무 작업도 하지 않는다.

---

## Step 1. 입력 타입 감지

| 입력 | 타입 | 처리 |
|---|---|---|
| `http(s)://...` | `url` | 원문 추출 후 `_raw/` source 저장 |
| 존재하는 파일 경로 | `file` | `_raw/` source로 복사 후 요약 |
| 그 외 구체적 사실·경험·결정사항 | `text` | source 없이 canonical/daily-log 후보 판단 |
| 인자 없음 | `inbox` | `_inbox/` 파일을 하나씩 정리 |

질문 형태("~란?", "~알려줘")이면 `/kb-search`를 안내하고 종료한다.
일반 지식 생성을 요구하지만 구체적인 내용이나 출처가 없으면 거부한다.

---

## Step 2. source 준비

### URL

1. `defuddle` 또는 WebFetch로 본문을 추출한다.
2. 추출 결과가 200KB를 초과하면 진행 여부를 1회 확인한다.
3. 원본을 `{kb_root}/_raw/{slug}.md`에 저장한다.
4. source link 후보를 `[[\_raw/{slug}]]` 형태로 준비한다.

### 외부 파일

1. 파일명을 slug화한다. `..`와 path traversal은 거부한다.
2. `{kb_root}/_raw/{slug}.{ext}`로 복사한다.
3. PDF/PPTX/DOCX는 텍스트 추출, 이미지는 LLM 설명 생성으로 요약한다.
4. source link 후보를 준비한다.

### 텍스트

1. 입력에 구체적 사실·경험·결정사항이 있는지 확인한다.
2. 정리 저장 또는 원문 저장 여부를 사용자에게 묻는다.
3. 입력이 날짜성 메모인지, 누적 가이드 지식인지 판단한다.

### Inbox

1. `{kb_root}/_inbox/`의 파일 목록을 읽는다.
2. 각 파일을 source로 간주하되 `_raw/` 복사는 건너뛴다.
3. 정리 완료 후 원본 `_inbox` 파일은 삭제할 수 있지만, 사용자 승인 없이는 처리하지 않는다.
4. skip 선택 시 `_inbox`에 그대로 둔다.

---

## Step 3. 문서 kind 판단

`skills/kb-common/references/llm-wiki-schema.md`의 Document Kind Classification을 따른다.

| 신호 | kind | 예 |
|---|---|---|
| `_raw/` 원본 | `source` | `_raw/onboarding.md` |
| `_inbox/` 입력 | `inbox` | `_inbox/todo.md` |
| `_archive/` 보관 | `archive` | `_archive/old-note.md` |
| 날짜가 핵심인 입력 | `daily-log` | `tripbtoz-onboarding-2026-06-29.md` |
| 계속 갱신될 주제 | `canonical` | `tripbtoz-onboarding.md` |

온보딩, 회사생활, 프로젝트 가이드, 개발환경, 업무규칙처럼 앞으로 누적될 가능성이 높은 주제는
canonical wiki를 우선 후보로 제안한다.

---

## Step 4. 기존 canonical 후보 찾기

볼트에서 제목, 파일명, tags, 주요 키워드로 관련 canonical wiki를 최대 5개 찾는다.

```bash
grep -rli "{keyword}" "{kb_root}" --include="*.md" \
  --exclude-dir=_raw --exclude-dir=_inbox --exclude-dir=_archive \
  --exclude-dir=.obsidian --exclude-dir=.claude
```

우선순위:

1. frontmatter `kind: canonical`
2. 날짜 suffix가 없는 같은 주제 파일명
3. 제목과 tags가 입력 주제와 일치
4. 기존 daily log가 이미 연결한 canonical

---

## Step 5. 동작 모드 선택

첫 번째로 매칭되는 행을 적용한다.

| Priority | Condition | Mode | Required behavior |
|---|---|---|---|
| 1 | User explicitly asks remove/delete | `remove` | 별도 문구 확인 없이는 삭제하지 않는다. |
| 2 | User explicitly asks modify/change/merge | `modify-preview` | 대상 영역, 변경 전후, facts-preserving 근거를 보여주고 승인 후 적용한다. |
| 3 | New input is cumulative guide content and canonical exists | `merge-preview` | 기존 canonical 문서의 적절한 섹션 병합을 제안한다. |
| 4 | New input is date-bound log content | `daily-log + canonical-link` | 날짜별 로그를 보존하고 canonical 문서 연결 또는 갱신을 제안한다. |
| 5 | New topic with no canonical candidate | `new-canonical` | 얕은 주제 폴더에 canonical 문서 생성을 제안한다. |

### `merge-preview` / `modify-preview`

기존 본문을 바꿀 수 있는 모든 흐름은 다음 preview를 출력한다.

```text
=== KB merge-preview ===
대상 canonical: Tripbtoz/tripbtoz-onboarding.md
대상 섹션: ## Procedures And Rules
근거: 새 입력은 온보딩 절차 설명이며 기존 섹션의 중복 bullet을 보강합니다.

- 기존 bullet
+ 병합 후 bullet

facts-preserving 근거:
- 기존 사실을 삭제하지 않음
- source/daily-log 링크를 유지함
- 불확실한 내용을 확정 사실로 바꾸지 않음

[Y] 적용 / [n] 취소 / [l] daily log만 저장
```

`Y`가 아니면 기존 본문은 수정하지 않는다.

### `daily-log + canonical-link`

날짜성 입력은 daily log를 만들고, canonical wiki 연결을 제안한다.

```text
[모드 A] daily log + canonical 반영
  log: Tripbtoz/tripbtoz-onboarding-2026-06-29.md
  canonical: Tripbtoz/tripbtoz-onboarding.md

[모드 B] daily log만 저장
[모드 C] 취소
```

### `new-canonical`

새 주제면 얕은 주제 폴더에 canonical wiki 생성을 제안한다.

```text
→ Tripbtoz/tripbtoz-onboarding.md canonical wiki를 생성합니다. OK? [Y/n]
```

---

## Step 6. 폴더 선정

얕은 주제 폴더를 우선한다.

| 종류 | 규칙 | 예 |
|---|---|---|
| 주제 폴더 | `_` prefix 없음 | `Tripbtoz/`, `LLM/`, `Projects/` |
| 특수 폴더 | `_` prefix 필수 | `_raw/`, `_inbox/`, `_archive/` |

깊은 폴더보다 제목, tags, source link, wiki link로 관계를 표현한다.
새 특수 폴더는 사용자가 명시하지 않으면 만들지 않는다.

---

## Step 7. 쓰기 형식

### Canonical wiki

`skills/kb-common/templates/canonical-wiki.md`를 따른다.

필수:

- `kind: canonical`
- `tags`
- `created`
- source links
- related logs
- related documents

### Daily log

`skills/kb-common/templates/daily-log.md`를 따른다.

필수:

- `kind: daily-log`
- `tags`
- `created`
- `canonical`
- raw context 또는 source link
- canonical update candidates

### Source

`_raw/` 아래에 원본을 저장하고, canonical 또는 daily log가 이 source를 링크하게 한다.

---

## Step 8. atomic write

모든 쓰기는 전체 파일 내용을 임시 파일에 쓴 뒤 rename한다.

```bash
tmpfile=$(mktemp "{target}.XXXXXX.tmp")
# tmpfile에 전체 새 내용 작성
mv "$tmpfile" "{target}"
```

append도 부분 append를 직접 하지 않고 전체 파일을 다시 쓴다.

---

## Step 9. helper 검증

쓰기 후 best-effort로 helper를 실행해 schema 위반 후보를 확인한다.
실패해도 사용자에게 보고만 하고, 이미 승인된 쓰기를 자동으로 되돌리지 않는다.

```bash
python3 skills/kb-common/scripts/validate_llm_wiki.py --root "{kb_root}"
```

---

## 하지 않는 일

- 사용자 승인 없이 기존 본문을 수정·병합하지 않는다.
- remove/delete를 단순 `Y`로 처리하지 않는다.
- source link를 삭제하지 않는다.
- 날짜별 맥락을 조용히 canonical 문서로만 흡수하지 않는다.
- 실제 사용자 KB 볼트를 자동 마이그레이션하지 않는다.
- git 명령을 호출하지 않는다.
- `kb-search`처럼 질문에 답하지 않는다.

---

## 예시

### 1일차 온보딩

```text
/kb-add Tripbtoz 1일차 온보딩 내용...
→ Tripbtoz/tripbtoz-onboarding-2026-06-29.md daily log 생성 제안
→ Tripbtoz/tripbtoz-onboarding.md canonical wiki 생성 또는 merge-preview 제안
→ 두 문서 상호 wiki link
```

### 다음날 온보딩 추가

```text
/kb-add 오늘 온보딩에서 배운 추가 내용...
→ 기존 Tripbtoz/tripbtoz-onboarding.md 발견
→ 새 daily log 저장
→ canonical의 적절한 섹션에 facts-preserving merge-preview
```

### 기존 문서 명시 수정

```text
/kb-add [[tripbtoz-onboarding]]의 배포 절차 섹션에 이 내용을 병합해줘
→ modify-preview 출력
→ 사용자 Y 승인 시 스냅샷 + atomic write
```

### 삭제 요청

```text
/kb-add [[credentials]]에서 deprecated row 삭제해줘
→ remove 계획 출력
→ "이 부분 제거한다" 정확한 문구 없으면 취소
```

