---
name: kb-lint
description: |
  Knowledge Base 전체 건강 점검과 LLM wiki schema/template 검증을 수행한다. 깨진 링크, 고아 페이지, tags 누락, _inbox 방치, _raw 고아 원본, 폴더 컨벤션뿐 아니라 canonical wiki 없는 daily log 누적, daily-log-without-canonical-link, raw-source-unlinked 등을 보고한다. `--boost-links`는 명시 옵션 + 사용자 컨펌 후에만 링크를 추가한다.
  트리거: "/kb-lint", "KB 점검", "위키 건강 체크", "그래프 보강해줘", "위키링크 추가", "LLM wiki 검증"
---

# kb-lint — LLM Wiki 건강 점검

볼트 전체를 스캔해 Obsidian 링크 건강과 `sources -> wiki -> schema` 일관성을 보고한다.

참조 규칙:

- Schema: `skills/kb-common/references/llm-wiki-schema.md`
- Helper: `skills/kb-common/scripts/validate_llm_wiki.py`

---

## 핵심 원칙

1. **기본은 읽기 전용 보고** — 자동 수정 없음.
2. **schema/template 점검** — document kind, frontmatter, source/canonical/log 연결을 확인한다.
3. **canonical-log 관계 우선** — daily log만 쌓이고 canonical wiki가 없는 주제를 보고한다.
4. **추가만, 수정 없음** — `--boost-links`도 `## 관련` 같은 관련 섹션에 링크를 추가할 뿐 기존 문장을 고치지 않는다.
5. **일괄 컨펌** — 쓰기가 필요한 보강은 대상 목록을 보여주고 사용자 승인 후 진행한다.
6. **git에 손대지 않음**.

---

## Step 0. 볼트 경로 확인

`~/.config/kb/path`를 읽어 볼트 절대 경로를 얻는다.

```bash
test -f ~/.config/kb/path && cat ~/.config/kb/path
```

없거나 비어 있으면 점검 대상이 없음을 알리고 절대 경로 설정을 요청한다.

---

## Step 1. 모드 분기

| 입력 | 모드 |
|---|---|
| `/kb-lint` | report — 읽기 전용 전체 점검 |
| `/kb-lint --llm-wiki` | helper — `validate_llm_wiki.py` 중심 schema 점검 |
| `/kb-lint --boost-links` | boost — 최근 문서 위키링크 보강 |
| `/kb-lint --boost-links {파일}` | boost — 특정 문서 링크 보강 |
| `/kb-lint --folder {경로}` | report 또는 boost 대상 제한 |

---

## Step 2. 전체 파일 스캔

수집 정보:

- 파일 경로
- frontmatter: `kind`, `tags`, `created`, `updated`, `source`, `canonical`, `related`
- 문서 kind: `source`, `inbox`, `archive`, `daily-log`, `canonical`, `unknown`
- 위키링크 목록
- 인바운드/아웃바운드 링크 그래프
- daily log와 canonical wiki 연결 관계
- raw source 참조 관계

`_raw/`, `_inbox/`, `_archive/`는 특수 폴더로 별도 점검한다.

---

## Step 3. 점검 항목

### 기존 Obsidian 건강 점검

- 깨진 위키링크
- 고아 페이지
- tags 누락
- 중복 의심 문서
- `_inbox/` 방치
- `_raw/` 고아 원본
- 진부한 정보
- 빈약한 문서
- 폴더 컨벤션 위반
- 위키링크 보강 제안

### LLM wiki schema/template 점검

`validate_llm_wiki.py` 또는 동일한 규칙으로 다음 issue code를 보고한다.

| Issue code | 의미 |
|---|---|
| `missing-required-frontmatter` | kind별 필수 frontmatter가 없음 |
| `raw-source-unlinked` | `_raw` source가 어떤 canonical/daily-log에서도 참조되지 않음 |
| `daily-log-without-canonical-link` | daily log가 canonical wiki를 가리키지 않음 |
| `canonical-missing-related-section` | canonical wiki에 관련 문서/로그 섹션이 없음 |
| `unknown-kind` | 문서 kind를 판정할 수 없음 |

추가 보고:

- 같은 주제의 날짜별 daily log가 2개 이상 있지만 canonical wiki가 없는 경우
- canonical wiki와 daily log가 서로 링크하지 않는 경우
- 깊은 폴더 구조가 canonical/wiki link 대신 분류를 과도하게 담당하는 경우

---

## Step 4. helper 실행

가능하면 read-only helper를 실행한다.

```bash
python3 skills/kb-common/scripts/validate_llm_wiki.py --root "{kb_root}"
```

JSON이 필요하면:

```bash
python3 skills/kb-common/scripts/validate_llm_wiki.py --root "{kb_root}" --json
```

helper 실패는 report에 포함하되, 자동 수정하지 않는다.

---

## Step 5. 보고서 출력

```text
===== KB Lint Report =====

볼트: {kb_root}
총 문서 수: N (_raw 제외)

Obsidian health:
- 깨진 위키링크: N
- tags 누락: N
- _inbox 방치: N

LLM wiki schema/template:
- missing-required-frontmatter: N
- raw-source-unlinked: N
- daily-log-without-canonical-link: N
- canonical 없는 daily log 주제: N

다음 액션:
- /kb-add                 ← _inbox 정리 또는 canonical 반영
- /kb-lint --boost-links  ← 승인 후 링크 보강
```

상세 내역은 파일 경로와 issue code를 함께 출력한다.

---

## Step 6. `--boost-links`

링크 보강은 명시 옵션과 사용자 승인 후에만 수행한다.

- A -> B 링크 추가 시 B -> A도 제안한다.
- canonical wiki와 daily log 사이의 링크를 우선 보강한다.
- 기존 본문 문장은 수정하지 않는다.
- 관련 섹션이 없으면 파일 끝에 새 관련 섹션을 추가한다.
- atomic write를 사용한다.

---

## 하지 않는 일

- report 모드에서 파일 수정.
- 깨진 링크 자동 수정.
- tags 자동 추론 채움.
- 중복 문서 자동 병합.
- `_raw` 고아 원본 자동 삭제.
- 실제 사용자 KB 볼트 자동 마이그레이션.
- git 호출.

