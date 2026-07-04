# kb 스킬 비판적 분석 및 개선 계획

> 대상: `skills/kb-manage`, `skills/kb-write`, `skills/kb-search`, `skills/kb-lint` (2026-07-04 기준)
>
> 목표 대비 평가 기준: "Karpathy LLM wiki에서 영감만 받고, **사람이 지속적으로 관리**하면서 **사람이 읽기 쉽고**, **검색 가능한** 구조"

## 1. 총평

설계 방향 자체는 목표와 잘 맞는다. maintained document를 유일한 진실 표면으로 삼고, `_raw/`·canonical·daily-log 스키마를 거부한 것은 "사람이 관리 가능한 KB"라는 목표에 정확히 부합한다. `agent_edit_mode` 3단계와 git 기반 guard는 다른 KB 스킬에서 보기 힘든 독창적이고 실용적인 장치다. 보안 게이트, 불확실성 마커, Obsidian을 선택 의존성으로 격리한 것도 잘 되어 있다.

문제는 세 갈래다.

1. **규칙끼리 충돌한다** — 문서가 시키는 절차가 guard 스크립트에 걸리고, 스킬마다 마커·규칙 목록이 미묘하게 다르다.
2. **프롬프트 무게가 목표와 상충한다** — "편한 게 우선"인데, 메모 한 줄 추가에 kb-manage(381줄)+kb-write(313줄) 낭독, 보안 리뷰 2회, guard 실행, index/log 갱신이 전부 요구된다.
3. **구조적 중복** — 같은 규칙(frontmatter, edit mode, 금지사항)이 3~4곳에 복사되어 있어 drift가 이미 발생했다.

## 2. 상충·버그 (검증됨)

### 2.1 [버그] 아카이브 절차가 guard와 항상 충돌

- `kb-manage:208-212`는 아카이브 절차로 "① `_archived/`로 이동 ② `agent_edit_mode: read_only` 설정 ③ index/log 갱신"을 규정한다.
- `check_agent_edit_mode.py:196-206`은 old/new **어느 쪽이든** `read_only`면 모든 변경을 위반으로 판정한다. 따라서 editable 문서를 절차대로 아카이브하면 **항상 exit 1** → 에이전트는 매번 "사람이 의도한 변경이 맞나요?"를 물어야 한다. 사용자가 방금 아카이브를 지시했는데도.
- 같은 이유로 **새 read_only 문서 생성**도 항상 위반 판정된다 (재현 테스트로 확인).
- **수정안**: guard에서 (a) `old_mode`가 None 또는 editable이고 `new_mode`가 read_only인 전환(신규 생성·아카이브 전환)은 위반이 아니라 정보성 알림으로 강등, 또는 (b) `--allow-transition` 플래그 추가 + 스킬 문서에 아카이브 시 사용 명시. (a)가 단순해서 권장. 보호의 본질은 "이미 read_only였던 내용의 변경 금지"이므로 `old_mode == read_only`일 때만 위반으로 보면 된다.

### 2.2 [상충] append_only 규칙 vs kb-lint 검사

- `kb-manage:299` / `kb-write:158`: append_only 문서는 `updated` 프론트매터를 바꾸면 안 된다.
- `kb-lint:39`: "`updated` older than a meaningful body change indicated by git history"를 결함으로 검사한다.
- 즉 **append_only 문서에 규칙대로 추가할수록 lint 결함이 쌓인다**. 규칙 준수가 lint 위반을 생산하는 구조.
- **수정안**: kb-lint의 해당 검사에 "append_only 문서는 제외(또는 별도 정보성 카테고리)" 예외를 명시. 장기적으로는 append_only에서도 `updated` 갱신만은 허용하는 게 더 깔끔하다(guard의 subsequence 검사에 `updated` 라인 교체 허용 예외 추가).

### 2.3 [상충] 불확실성 마커 집합이 스킬마다 다름

- `kb-manage:35`: `확인 필요`, `미정`, `추정`, **`unknown`, `past information`**
- `kb-write:17,182` / `kb-search:19`: `확인 필요`, `미정`, `추정`, **`과거 정보`**
- `kb-lint:61,98`(grep 패턴): 한국어 4종만. → kb-manage가 허용한 `unknown`/`past information`으로 표기된 항목은 **lint에 영원히 안 걸린다**.
- **수정안**: 마커 canonical 집합을 한 곳(공유 conventions)에서 딱 한 번 정의하고 전 스킬이 참조. 한국어 4종으로 통일 권장(사용자 언어), 영어 별칭을 허용할 거면 lint grep에도 반드시 포함.

### 2.4 [상충] kb-search의 log.jsonl 이중 메시지

- `kb-search:10` Overview: "Do not depend on ... `log.jsonl`".
- `kb-search:61-67`: log.jsonl을 검색하라며 `tail`/`rg`/`jq` 커맨드 제공.
- 의도는 "진실 소스로 쓰지 말고 포인터로만 써라"겠지만, 문장 그대로 읽으면 모순. **수정안**: Overview 문구를 "log.jsonl을 사실의 근거로 인용하지 말 것(파일 위치·git 이력 탐색용으로만)"으로 교체.

### 2.5 [상충] 루트 해석 규칙 vs AGENTS.md 템플릿

- `kb-manage:81`: cwd, `index.md`, guidance 파일 등에서 루트를 **추론 금지**. 오직 사용자 절대경로 또는 전역 config.
- `templates/AGENTS.md:9`: "이 파일을 읽는 에이전트는 이 KB 루트를 해석해서 이 파일을 읽어라" — 그런데 AGENTS.md의 위치 자체는 루트 증거로 못 쓴다. 사용자가 KB 디렉토리 안에서 작업 중이고 AGENTS.md가 스스로 KB라고 선언해도, config가 없으면 무조건 되물어야 한다.
- 오탐 방지(아무 저장소나 KB로 오인) 목적은 정당하나, 단일 전역 config는 **KB가 2개 이상이면 파손**된다(개인 KB + 회사 KB가 실제 시나리오). 현재 config는 경로 1개만 지원.
- **수정안**: config를 다중 루트로 확장 — `{"kbs": {"personal": "...", "work": "..."}, "default": "personal"}` (기존 `path` 키는 하위호환 유지). cwd가 등록된 루트 중 하나의 하위면 그 루트를 자동 선택. 등록 안 된 디렉토리는 지금처럼 물어본다. 이러면 엄격함은 유지하면서 "내 KB 안에서는 그냥 동작"하게 된다.

### 2.6 [불일치] 문서 배치 오류

- `kb-manage:160` "Normal KB documents should include `agent_edit_mode: editable` ..."이 `### index.md Default Shape` 절 아래에 들어가 있다. index.md 얘기가 아니라 일반 문서 frontmatter 규칙이므로 Frontmatter Default 절로 이동.

### 2.7 [설계 결함] append_only "아무 데나 삽입 허용"의 의미 왜곡 위험

- guard는 라인 subsequence만 검사하므로, 기존 문단 **한가운데** 줄을 끼워 넣어도 통과한다. "원문 보존"이 지켜져도 부정문 사이에 문장을 끼우면 의미가 뒤집힐 수 있다.
- **수정안**: 규칙 문구를 "섹션 경계 또는 기존 블록 뒤에 추가, 추가분은 `> [agent YYYY-MM-DD]` 같은 출처 표기 권장"으로 좁힌다. guard는 그대로 두되(기계 검증은 subsequence가 한계) 프롬프트 규범으로 보완.

## 3. 프롬프트 개선

### 3.1 트리거 표면(description) 강화 — 우선순위 높음

CLAUDE.md 스스로 "description이 실제 trigger surface"라고 규정하는데, 네 스킬 어디에도 **"KB"라는 토큰과 사용자가 실제로 말할 법한 한국어 문구가 없다**. 사용자는 "kb에 저장해줘", "지식베이스에서 찾아줘"라고 말한다.

개선 예 (kb-write):

```yaml
description: Use when the user asks to save, note, or file knowledge into their
  personal Markdown Knowledge Base (KB) — e.g. "kb에 저장/추가/정리해줘", "이거
  메모해둬", meeting notes, decisions, procedures, onboarding docs, or URLs to
  keep. Covers create/merge/append/reorganize. Not for answering questions from
  the KB (use kb-search) or KB setup/migration (use kb-manage).
```

네 스킬 모두 동일 원칙 적용: ① "KB/kb" 리터럴 포함 ② 한국어 트리거 문구 예시 ③ 스킬 간 제외 조건 상호 명시(현재는 kb-write만 kb-search를 언급).

### 3.2 무게 줄이기 — 빠른 경로(fast path) 신설

현재 kb-write는 입력이 한 줄 메모여도 Required First Reads 7단계 + Security Gate 2회 + Washing Protocol + Multi-document 라우팅 + guard + index/log 갱신을 모두 요구한다. "지속적으로 사람이 관리"하려면 에이전트 경유 비용이 낮아야 하는데, 지금은 매 write가 의식(ritual)이다.

**수정안**: kb-write 상단에 분기 명시 —

- **Fast path** (기본): 입력이 단일 주제·민감정보 무해·대상 문서가 명백 → root 해석, 대상 문서 읽기, 보안 스캔 1회, 쓰기, index 갱신만. 라우팅 테이블·washing 프롬프트 낭독 생략.
- **Full path**: 다중 주제, 보안 후보 감지, 대규모 재구성, 병합 충돌 시에만 현재의 전체 절차.

### 3.3 "무엇이 아닌가" 반복 제거

`_raw/` 금지, canonical/daily-log 거부, `sources -> wiki -> schema` 거부가 4개 스킬에 걸쳐 8회 이상 반복된다. 이건 구모델에서 넘어온 마이그레이션 잔재이고, 새로 읽는 에이전트에게는 존재하지 않는 개념에 대한 부정 지식이다. **kb-manage의 "Migration From Old KB Model" 절에만 남기고 나머지 전부 삭제**. Overview들은 "maintained documents are the single source of truth" 한 문장이면 충분하다.

### 3.4 보안 스캔 패턴의 신호/잡음 개선

`kb-lint:104-105`의 grep은 `host|internal|prod|staging|session|계정`까지 잡는다. 기술 문서 KB에서는 거의 모든 파일이 걸려서 리포트가 잡음으로 채워지고, 결국 이 카테고리를 무시하게 된다(늑대소년 효과).

**수정안**: 2단계로 분리 —

- **High-confidence 패턴** (자동 플래그): `AKIA[0-9A-Z]{16}`, `-----BEGIN .*PRIVATE KEY`, `ghp_[A-Za-z0-9]{36}`, `xox[bp]-`, `eyJ[A-Za-z0-9_-]{10,}\.` (JWT), `password\s*[:=]\s*\S`, `Bearer\s+[A-Za-z0-9._-]{20,}` 등 값 형태 매칭.
- **Contextual 키워드** (LLM이 문맥 판단 후 보고): 현재 키워드 목록. 리포트에서 두 등급을 구분 표기.

### 3.5 답변 언어 정책 명시

스킬 본문은 영어, 사용자 대면 프롬프트·마커는 한국어로 섞여 있는데 정책이 없다. 공유 conventions에 한 줄 추가: "사용자 대면 출력(질문, 리포트, 답변)은 사용자의 언어를 따른다. 불확실성 마커는 canonical 한국어 마커를 쓴다."

### 3.6 `aliases` 필수 완화

필수 필드라서 자연스러운 별칭이 없는 문서에도 에이전트가 억지 별칭을 만들어 넣게 된다(검색 잡음). "필수, 단 빈 리스트 허용(`aliases: []`)"으로 명시하고, kb-lint의 "missing likely aliases"는 제안 등급 유지.

## 4. 구조 개선

### 4.1 공유 규약을 단일 파일로 추출 — 가장 중요

현재 frontmatter 스키마는 kb-manage와 kb-write에 통째로 복사, edit-mode 표는 kb-manage/kb-write/templates·AGENTS.md 3곳에 존재한다. 2.2·2.3의 drift는 이 복사 구조의 필연적 결과다.

**수정안**:

```text
skills/kb-manage/
├── SKILL.md                      # setup, migration, 템플릿 사용법만 (얇게)
├── references/
│   ├── conventions.md            # ★ 신설: 루트 해석, KB identity, frontmatter 스키마,
│   │                             #   agent_edit_mode 정의, 불확실성 마커, index/log 규칙,
│   │                             #   보안 원칙, Do-Not 목록 — 단일 원본
│   └── obsidian-skills.md
```

- kb-write/search/lint의 "Required orientation"을 "read `kb-manage/references/conventions.md`"로 교체. kb-manage SKILL.md 381줄 전체가 아니라 규약만 읽게 되어 컨텍스트 비용도 준다.
- kb-write의 frontmatter 블록·edit-mode 표 복사본은 삭제하고 참조로 대체(각 스킬에는 1줄 요약만).
- `templates/AGENTS.md`는 어차피 KB에 복사되는 파일이라 중복이 불가피 — "이 파일이 스킬 규약과 어긋나면 KB 로컬 규칙(이 파일)이 우선"임을 파일 안에 명시해 drift를 사양으로 흡수.

### 4.2 스크립트 경로: `/path/to/agent-toolkit` 플레이스홀더 제거

문서 전반의 `python3 /path/to/agent-toolkit/skills/...`는 에이전트가 경로를 추측하게 만든다. Claude Code 플러그인에서는 `${CLAUDE_PLUGIN_ROOT}`가 주입되므로:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kb-manage/scripts/check_agent_edit_mode.py"
```

Codex 겸용을 위해 각주 한 줄: "변수가 없으면 이 SKILL.md 파일 위치 기준 상대 경로로 해석."

### 4.3 index.md를 frontmatter에서 생성 가능하게

index의 summary/tags/updated는 frontmatter의 사본이라 구조적으로 drift한다(kb-lint의 Index 검사 5종이 그 증거). 이미 `python-frontmatter` 기반 스크립트가 kb-search에 있으므로, `kb_build_index.py` 하나 추가:

- frontmatter를 스캔해 Documents 테이블을 재생성. `_inbox/`/`_archived/`는 별도 섹션.
- 사람이 쓰는 상단 서문·Start Here 섹션은 마커 주석(`<!-- generated:start -->`)으로 보호해 수동 편집 보존.
- kb-lint `--fix-index`와 kb-write의 index 갱신이 이 스크립트를 호출 → "index drift" 검사 카테고리가 통째로 사라진다.

이건 "사람이 읽기 쉬운 카탈로그" 목표를 해치지 않는다 — 사람이 읽는 건 그대로고, 사람이 **유지보수**할 필요만 없어진다.

### 4.4 log.jsonl을 opt-in으로 강등

- 선언된 존재 이유가 "git history를 찾기 쉽게 하는 포인터"뿐인데, git-backed KB에서는 `git log --oneline --name-only`가 같은 정보를 무비용으로 준다.
- 유지 비용은 실재한다: 모든 write마다 append, timezone 규칙, kb-lint 검사 4종, 스킬 문서 곳곳의 "when present" 분기.
- **수정안**: setup 기본 생성 목록에서 제외하고 "non-git KB이거나 사용자가 작업 이력 파일을 원할 때만" 생성. 이미 있는 KB는 그대로 유지(기존 규칙 유효). 이렇게 하면 git-backed KB의 write 절차가 한 단계 줄고, 대신 커밋 메시지 규약("kb: add/update/merge <doc> — <summary>")을 conventions에 한 줄 추가해 git log 검색성을 보강.

### 4.5 kb-lint에 결정적 검사 스크립트 추가

현재 lint는 전부 LLM 수작업이라 실행마다 결과가 다르고 토큰이 비싸다. `--fix-index` 같은 CLI 플래그 표기는 실체 없는 스크립트를 암시하는 오해 유발 표기이기도 하다.

**수정안**: `kb_lint.py` 신설 — 기계 판정 가능한 것만: frontmatter 필수 필드/`agent_edit_mode` 유효값/날짜 형식, `_archived/` 깊이·read_only 여부, index 링크 대상 존재, 깨진 상대 링크, log.jsonl JSON 유효성, high-confidence 보안 패턴(3.4). SKILL.md는 "스크립트 결과 + LLM 판단 검사(중복 주제, 충돌 주장, 분할 필요)"의 2부 구성으로 재편. 가짜 CLI 플래그 표기는 "fix modes"라는 일반 명칭으로 변경.

### 4.6 guard 스크립트에 파일 스코프 옵션

guard는 HEAD 대비 **모든** 변경 md를 검사하므로, 사람이 직접 고쳐둔 미커밋 protected 파일이 있으면 에이전트가 무관한 작업 후에도 매번 경고를 만난다. `--files a.md b.md` 인자를 추가해 kb-write가 "이번에 자기가 만진 파일만" 검사할 수 있게 한다(인자 없으면 현행 전체 검사 = lint용).

### 4.7 4-스킬 분할 자체는 유지

단일 `kb` 스킬로 합치는 대안도 검토했으나, description 트리거가 작업 의도별로 분리되는 현재 구조가 CLAUDE.md의 스킬 관리 기준과 더 잘 맞는다. 4.1의 공유 conventions 추출만 되면 분할 비용(중복)이 사라지므로 분할 유지가 낫다.

## 5. 추가 권고 (선택)

- **git 이력 속 비밀값**: "Git history is the durable audit trail"과 "Security overrides preservation"이 충돌하는 지점이 하나 있다 — 비밀값이 일단 커밋되면 문서에서 지워도 이력에 남는다. conventions에 "커밋된 비밀값 발견 시: 값 회전(rotation)을 우선 권고, 이력 재작성은 사용자 결정" 한 단락 추가.
- **index 스케일링**: 문서 200개가 되면 단일 테이블은 못 읽는다. index.md에 폴더/카테고리별 섹션 가이드를 미리 넣어두면 나중에 재구조화 비용이 준다(4.3 생성 스크립트가 폴더별 섹션을 만들면 자동 해결).
- **사람 리뷰 루프**: "사람이 관리하는 KB"를 실질화하려면 kb-lint 리포트 끝에 "지난 lint 이후 에이전트가 변경한 문서 목록"(git log 기반)을 넣어 사람이 훑어볼 리뷰 큐로 쓰는 방안을 권장.

## 6. 실행 계획

### P0 — 버그·모순 해소 (동작 정확성)

1. `check_agent_edit_mode.py`: editable/신규 → read_only 전환을 위반에서 제외 (§2.1) + 테스트 케이스.
2. kb-lint: append_only 문서의 `updated` drift 검사 예외 (§2.2).
3. 불확실성 마커 canonical 집합 통일, kb-lint grep 동기화 (§2.3).
4. kb-search Overview의 log.jsonl 문구 수정 (§2.4).
5. kb-manage:160 배치 오류 이동 (§2.6).

### P1 — 구조 정리 (drift 원천 제거)

6. `kb-manage/references/conventions.md` 신설, 3개 스킬의 orientation 교체, 중복 블록 삭제 (§4.1).
7. `${CLAUDE_PLUGIN_ROOT}` 경로로 교체 (§4.2).
8. "무엇이 아닌가" 반복 제거 → Migration 절로 일원화 (§3.3).
9. 4개 스킬 description 재작성 (§3.1) 후 `update-project-docs`로 카탈로그 동기화.

### P2 — 사용성·자동화

10. kb-write fast path 분기 (§3.2).
11. `kb_build_index.py` + index 생성 마커 (§4.3).
12. `kb_lint.py` 결정적 검사 + 보안 패턴 2단계화 (§4.5, §3.4).
13. log.jsonl opt-in 전환 + 커밋 메시지 규약 (§4.4).
14. guard `--files` 스코프 옵션 (§4.6).
15. 다중 KB config (§2.5) — config 스키마 확장 + `resolve_kb_root.py` 갱신.

P0는 서로 독립적이라 한 번에 진행 가능. P1의 6번(공유 conventions)이 나머지 항목의 diff를 줄여주므로 P1 중 가장 먼저 하는 것이 좋다.
