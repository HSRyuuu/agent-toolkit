---
name: kb-setup
description: |
  개인 Knowledge Base를 처음 초기화하거나 공유 볼트 경로를 바꿀 때 사용한다. `~/.config/kb/path`를 설정하고 `_raw/`, `_inbox/`, `_archive/` 기본 폴더를 준비하며, KB가 `sources -> wiki -> schema` LLM wiki 모델로 운영된다는 점과 `skills/kb-common` schema/template/helper 자산을 안내한다.
  트리거: "/kb-setup", "KB 최초 세팅", "KB 설치", "kb 기본 세팅", "볼트 경로 설정", "Knowledge Base 초기화"
---

# kb-setup — LLM Wiki KB 최초 세팅

개인 KB 볼트 경로를 설정하고, 모든 `kb-*` 스킬이 공유하는 기본 디렉터리와 운영 모델을 안내한다.

---

## 핵심 원칙

1. **단일 설정 파일** — 모든 KB 스킬은 `~/.config/kb/path` 한 줄을 공유한다.
2. **LLM wiki 모델 안내** — KB는 `sources -> wiki -> schema`로 운영된다.
3. **기본 특수 폴더 생성** — `_raw`, `_inbox`, `_archive`만 만든다.
4. **기존 볼트 보존** — 기존 경로나 문서를 사용자 확인 없이 바꾸지 않는다.
5. **자동 마이그레이션 없음** — 기존 KB 파일을 이동·삭제·재작성하지 않는다.
6. **git에 손대지 않음**.

---

## Step 0. 현재 설정 확인

```bash
test -f ~/.config/kb/path && cat ~/.config/kb/path
```

이미 설정되어 있고 디렉터리가 존재하면 현재 볼트를 보여주고 종료한다.
사용자가 재설정을 명시한 경우에만 새 경로 흐름으로 간다.

---

## Step 1. 볼트 경로 받기

사용자가 경로를 주지 않았다면 기본값을 제안한다.

```text
KB 볼트로 사용할 디렉터리의 절대 경로를 알려주세요.

추천 기본값:
  {HOME}/KnowledgeBase

조건:
  - 절대 경로여야 합니다.
  - 존재하지 않으면 생성 여부를 먼저 확인합니다.
  - 이 경로는 ~/.config/kb/path 에 저장되어 kb-add, kb-search, kb-lint가 공유합니다.
```

상대 경로와 `~/...`는 받지 않는다. 취소하면 아무 작업도 하지 않는다.

---

## Step 2. 디렉터리 생성 확인

입력 경로가 존재하지 않으면 생성 여부를 묻는다.

```text
디렉터리가 없습니다: {kb_root}

생성할까요? [Y/n]
```

승인 시에만 `mkdir -p "{kb_root}"`를 실행한다.

---

## Step 3. 기본 특수 폴더 생성

```bash
mkdir -p "{kb_root}/_raw" "{kb_root}/_inbox" "{kb_root}/_archive"
```

| 폴더 | LLM wiki 역할 |
|---|---|
| `_raw/` | source 계층. URL 원문, 외부 파일, 추출 원문 보관 |
| `_inbox/` | 정리 전 입력. `/kb-add` inbox 모드의 처리 대상 |
| `_archive/` | active wiki 흐름에서 빠진 오래된 보관 문서 |

주제 폴더는 `_` prefix 없이 얕게 만든다. 예: `Tripbtoz/`, `LLM/`, `Projects/`.

---

## Step 4. 공유 설정 저장

기존 `~/.config/kb/path` 값이 있고 새 경로와 다르면 변경 계획을 보여주고 확인을 받는다.

```text
KB 볼트 경로를 변경합니다.

기존: {old_root}
신규: {kb_root}

진행할까요? [Y/n]
```

승인 후 저장한다.

```bash
mkdir -p ~/.config/kb
printf '%s\n' "{kb_root}" > ~/.config/kb/path
```

---

## Step 5. LLM wiki 운영 안내

설정 완료 후 다음을 안내한다.

```text
KB 기본 세팅 완료.

운영 모델:
  sources -> wiki -> schema

특수 폴더:
  _raw/      source 원본
  _inbox/    정리 대기 입력
  _archive/  오래된 보관 문서

공통 자산:
  skills/kb-common/references/llm-wiki-schema.md
  skills/kb-common/templates/canonical-wiki.md
  skills/kb-common/templates/daily-log.md
  skills/kb-common/scripts/validate_llm_wiki.py

다음 명령:
  /kb-add {내용}
  /kb-search {질문}
  /kb-lint
```

---

## Step 6. 검증

```bash
test -d "{kb_root}"
test -d "{kb_root}/_raw"
test -d "{kb_root}/_inbox"
test -d "{kb_root}/_archive"
test "$(cat ~/.config/kb/path)" = "{kb_root}"
```

---

## 하지 않는 일

- 지식 문서 생성은 하지 않는다.
- 기존 KB 파일을 이동·삭제·재작성하지 않는다.
- 기존 볼트를 `sources -> wiki -> schema`로 자동 마이그레이션하지 않는다.
- Obsidian 앱 설정, 플러그인 설치, git 설정은 하지 않는다.
- 검색이나 답변은 하지 않는다. 검색은 `/kb-search`가 담당한다.
- 건강 점검은 하지 않는다. 점검은 `/kb-lint`가 담당한다.

