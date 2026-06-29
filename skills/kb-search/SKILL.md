---
name: kb-search
description: |
  Knowledge Base에 축적된 LLM wiki를 자연어 질문으로 검색·답변한다. canonical wiki를 우선 검색하고, daily log와 _raw source는 보조 근거로 사용한다. 답변의 사실 주장은 위키링크 출처를 붙이며, KB에 정보가 부족하면 일반 지식으로 채우지 않고 정보 부족을 말한다. **읽기 전용** — 어떤 파일도 수정·생성하지 않는다.
  트리거: "/kb-search {질문}", "KB에서 찾아줘", "위키에서 검색", "지식저장소에서 알려줘"
---

# kb-search — LLM Wiki 검색·질의응답

KB의 `sources -> wiki -> schema` 모델 중 `wiki` 계층, 특히 canonical wiki를 우선 읽어 답한다.

참조 규칙:

- Schema: `skills/kb-common/references/llm-wiki-schema.md`
- Helper: `skills/kb-common/scripts/validate_llm_wiki.py`

---

## 핵심 원칙

1. **읽기 전용** — 파일 생성·수정·삭제·git 호출 없음.
2. **canonical wiki 우선** — 답변의 주요 근거는 `kind: canonical` 문서 또는 날짜 없는 canonical 주제 문서다.
3. **source/log는 보조 근거** — daily log와 `_raw` source는 맥락 확인용이며, canonical과 충돌하면 갱신 필요성을 안내한다.
4. **출처 명시** — 사실 주장은 본문 또는 말미에 `[[경로/문서명]]`으로 인용한다.
5. **정보 부족 인정** — KB에 정보 부족이면 LLM 일반 지식으로 채우지 않는다.

---

## Step 0. 볼트 경로 확인

`~/.config/kb/path`를 읽어 볼트 절대 경로를 얻는다.

```bash
test -f ~/.config/kb/path && cat ~/.config/kb/path
```

없거나 비어 있으면 검색 대상이 없음을 알리고, 절대 경로 설정을 요청한다.

---

## Step 1. 키워드 추출

질문에서 다음을 추출한다.

- 고유명사: 프로젝트명, 회사명, 라이브러리명, 인명
- 핵심 명사·동사
- 한/영 혼용 키워드
- 날짜성 힌트: "첫날", "2026-06-29", "어제 온보딩"

---

## Step 2. canonical-first 검색

### 계층 1 — canonical wiki

우선 `kind: canonical` frontmatter 또는 날짜 suffix가 없는 주제 문서를 찾는다.

```bash
grep -rli "{keyword}" "{kb_root}" --include="*.md" \
  --exclude-dir=_raw --exclude-dir=_inbox --exclude-dir=_archive \
  --exclude-dir=.obsidian --exclude-dir=.claude
```

우선 점수:

1. `kind: canonical`
2. 제목/파일명이 질문 주제와 일치
3. tags가 질문 키워드와 일치
4. canonical 문서의 related/source link가 질문과 맞음

### 계층 2 — daily log

canonical 문서가 부족하거나 날짜성 질문이면 `kind: daily-log` 또는 ISO date suffix 문서를 찾는다.

daily log는 그날 맥락을 설명할 때 사용하되, 답변에서 가능한 canonical wiki도 함께 인용한다.

### 계층 3 — source/raw

`_raw/` source는 canonical이나 daily log가 링크한 경우에만 보조 근거로 읽는다.
정리되지 않은 `_raw`만 발견되면 정보 부족 또는 정리 필요로 안내한다.

### 계층 4 — 위키링크 1-hop

상위 후보 문서의 `[[...]]` 링크를 1-hop만 따라간다.
깊이 2 이상은 무한 탐색과 노이즈를 막기 위해 가지 않는다.

---

## Step 3. 후보 선별

- 최종 본문을 읽을 문서는 최대 7개로 제한한다.
- canonical wiki를 우선하고, daily log/source는 보조로 붙인다.
- `_inbox/` 문서는 답변 출처로 쓰지 않는다.
- `_archive/` 문서는 질문이 과거 자료를 요구할 때만 보조로 쓴다.

---

## Step 4. 답변 합성

1. canonical wiki에서 현재 지식과 절차를 추출한다.
2. 필요한 경우 daily log로 날짜별 맥락을 보강한다.
3. 필요한 경우 source link로 원문 근거를 확인한다.
4. 모든 사실 주장에 위키링크 출처를 붙인다.
5. canonical과 daily log가 충돌하거나 canonical이 오래된 것 같으면 "갱신 필요"를 상단 부가 설명에 짧게 안내한다.

출력은 답변과 참조 문서가 화면 하단에 보이도록 구성한다.

```markdown
(선택) 검색 맥락: canonical N개, daily log N개, source N개 확인.

---

## 답변

{핵심 답변. 인라인 [[위키링크]] 인용 포함.}

**참조 문서**
- [[canonical 문서]] — 핵심 근거
- [[daily log]] — 날짜별 맥락
- [[_raw/source]] — 원문 보조 근거
```

### 정보 부족 시

```markdown
---

## 답변

KB에는 이 주제에 대한 정보가 부족합니다.

**가장 가까운 문서**
- [[문서A]] — 일부 관련

추가 자료가 있으면 `/kb-add`로 source 또는 canonical wiki에 반영할 수 있습니다.
```

LLM 일반 지식으로 빈칸을 채우지 않는다.

---

## 하지 않는 일

- 파일 쓰기.
- git 호출.
- frontmatter 갱신.
- 일반 지식으로 답변 보충.
- `_raw`나 daily log만 보고 canonical wiki가 있는 것처럼 답변하기.

