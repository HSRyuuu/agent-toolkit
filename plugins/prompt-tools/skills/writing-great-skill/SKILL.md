---
name: writing-great-skill
description: >
  Use when creating a new Claude/Codex skill, writing a SKILL.md from scratch,
  or editing, reviewing, diagnosing, or pruning an existing skill. Triggers:
  "create a skill", "new skill", "make this a skill", "skill test", "스킬
  만들어줘", "이 스킬 리뷰해줘", "스킬 개선해줘", "SKILL.md 고쳐줘", "스킬이 안
  불려", "스킬 너무 길어", "/writing-great-skill". Do NOT use for one-off
  project docs or repository conventions that belong in AGENTS.md/CLAUDE.md,
  for plugin/marketplace registration (use `local-plugin-manager`), or for
  re-tuning an existing prompt to a newer model generation (use
  `prompt-modernizer`).
---

# Writing a Great Skill

스킬을 만드는 것은 **프로세스 문서에 적용한 TDD**다. Iron Law도 같다 — **실패하는 테스트 없이 스킬 없다.** 스킬 없이 에이전트가 실패하는 걸 직접 보지 않았다면, 그 스킬이 옳은 것을 가르치는지 알 수 없다. **신규 생성과 편집 모두에 적용된다.**

이 저장소에서 plugin 스킬은 `./skills/<name>/SKILL.md`에 산다 — Claude Code와 Codex가 공유하는 루트다.

## 레퍼런스

각 파일은 **언제 읽는지**가 조건이다. 조건에 안 걸리면 열지 않는다.

| 파일 | 읽는 시점 |
|---|---|
| [`references/principles.md`](references/principles.md) | **A3·A4·B2·B4 진입 전 항상.** invocation 선택, description 작성, 정보 계층, progressive disclosure, leading word, 실패모드 — 이 스킬의 판정 어휘 전부 |
| [`references/GLOSSARY.md`](references/GLOSSARY.md) | principles의 굵은 용어 하나가 애매할 때만. 전량 통독하지 않는다 |
| [`references/testing-skills-with-subagents.md`](references/testing-skills-with-subagents.md) | A2·B3에서 시나리오를 **실제로 작성할 때**. 압박 유형, 시나리오 문안, 메타 테스트 |
| [`references/persuasion-principles.md`](references/persuasion-principles.md) | discipline 스킬의 압박 시나리오를 설계할 때만 |
| [`references/examples/CLAUDE_MD_TESTING.md`](references/examples/CLAUDE_MD_TESTING.md) | 테스트 캠페인 전체가 어떻게 굴러가는지 실제 사례가 필요할 때 |

참조는 **전부 여기서 직접 링크한다** — 참조 파일이 또 다른 파일을 가리키면 에이전트가 부분만 읽고 지나간다.

## 두 갈래

| 요청 | 경로 |
|---|---|
| 새 스킬을 만든다 | **A. 신규 생성** |
| 기존 스킬을 고친다 · 리뷰한다 · "왜 안 불리지" · "너무 길다" | **B. 수정·리뷰** |

둘 다 아니면(플러그인 등록, 캐시, 로드 실패) `local-plugin-manager`다.

---

## A. 신규 생성

### A1. 존재해야 하는지 결정

직관적으로 자명하지 않았고, 프로젝트를 넘나들며 반복되고, 넓게 적용되는 기법에만 스킬을 만든다. 나머지는 다른 곳으로 보낸다 — 프로젝트 고유 관례는 CLAUDE.md/AGENTS.md로, 스크립트나 regex로 강제할 수 있는 것은 자동화로. 문서는 **판단이 필요한 것**에 남긴다.

**완료 기준:** 그 스킬이 어떤 반복 상황을 위한 것인지 한 문장으로 말할 수 있다.

### A2. RED — 기준선 기록

스킬 **없이** 서브에이전트로 압박 시나리오를 돌린다 (discipline 스킬이면 압박 3종 이상 조합 — 시간, 매몰비용, 권위, 피로). 에이전트가 무엇을 선택했고 어떤 합리화를 했는지 **원문 그대로** 기록한다. 이 실패 기록이 스킬이 충족해야 할 명세다.

스킬 유형별 테스트 설계:

| 유형 | 테스트 방식 | 통과 조건 |
|---|---|---|
| Discipline (규칙) | 압박 시나리오, 압박 조합 | 최대 압박에서도 준수 |
| Technique (방법) | 적용 + 엣지케이스 시나리오 | 새 상황에 적용해낸다 |
| Pattern (사고 모델) | 인식 + 반례 시나리오 | 적용될 때와 안 될 때를 가른다 |
| Reference (문서·API) | 검색 + 공백 시나리오 | 자료를 찾아 올바로 적용한다 |

**완료 기준:** 모든 시나리오의 기준선 행동이 원문으로 기록됐다.

### A3. GREEN — 최소한으로 쓴다

`skills/<name>/SKILL.md`를 쓴다. **기록된 실패만** 겨냥하고 가정된 것은 쓰지 않는다. frontmatter, invocation 선택, 구조는 `references/principles.md`를 따른다. 잘 만든 실행 가능 예시 하나가 어중간한 여러 개를 이긴다.

**산문으로 쓰기 전에 스크립트인지 먼저 판정한다.** 절차 중 **결정적인 부분**(같은 입력 → 같은 출력: 검증, 파싱, 집계, 포맷 변환)이나 **취약한 부분**(일괄 변경, 파괴적 작업, 순서를 지켜야 하는 것)이 있으면 `scripts/`로 뺀다. 반복 횟수가 아니라 **취약성과 가변성**이 기준이다 — 한 번만 도는 마이그레이션도 스크립트가 맞다. 맥락이 최선의 경로를 정하는 일(리뷰, 설계 판단)은 산문으로 둔다.

스크립트를 번들하면 **실행형인지 참조형인지 SKILL.md에 명시한다** — `` `python scripts/x.py` 를 실행한다`` (기본) 대 `` `scripts/x.py` 의 알고리즘을 참조한다``. 판정 근거와 작성 규칙은 `references/principles.md`의 *Prose or script* 절에 있다.

**description 함정 (테스트로 확인됨):** description에는 **트리거만** 쓰고 스킬의 프로세스를 요약하지 않는다. 프로세스를 요약한 description은 지름길이 되어, 에이전트가 description만 읽고 본문을 건너뛴다. `"code review between tasks"`라고 쓴 description이 리뷰를 **한 번**만 시켰다 — 본문 플로우차트는 두 번을 요구했는데. 순수 트리거 조건으로 고쳐 쓰자 해결됐다.

같은 시나리오를 스킬을 **넣고** 다시 돌린다.

**완료 기준:** 모든 기준선 시나리오가 이제 통과한다.

### A4. REFACTOR — 빠져나갈 구멍을 막는다

에이전트가 새로 찾아낸 합리화마다 명시적 반박을 스킬에 넣는다. discipline 스킬이면 합리화 표(`변명 | 실제`)와 red-flag 자가점검 목록으로 누적하고, **규칙의 문자를 어기는 것이 곧 정신을 어기는 것**임을 앞부분에 못 박는다.

그 다음 `references/principles.md`의 실패모드로 쳐낸다 — no-op, duplication, sediment, sprawl, negation.

**완료 기준:** 테스트 한 바퀴를 다 돌려도 새 합리화가 안 나온다.

### A5. 배포

다음 스킬을 시작하기 전에 이 스킬을 테스트한다 — 테스트 안 된 스킬을 쌓아두는 것은 테스트 안 된 코드를 배포하는 것이다. `sync-docs`로 저장소 문서를 맞추고, 커밋한다 (저장소 정책상 `verify-secrets` 먼저).

**완료 기준:** 스킬이 커밋됐고 catalog/문서가 그것을 반영한다.

---

## B. 수정·리뷰

기존 스킬을 고치는 것도 TDD다. **어떤 실패를 고치는지 모르면 고치지 않는다.**

### B1. 정체성 확정

먼저 한 줄로 답한다 — **이 스킬이 없으면 에이전트가 무엇을 다르게 하는가.** 여러 주제가 섞인 스킬이면 섹션당 한 줄, 최대 7줄.

이게 없으면 이후 판정이 "모델이 이미 이걸 하나?"로 좁혀지고, **모델의 기본 성향을 거스르는 것이 목적인 스킬은 전부 삭제 판정**이 난다. 정체성 문장이 있으면 질문이 *"이걸 지우면 저 줄이 약해지나?"*로 바뀐다.

**완료 기준:** 정체성 문장이 사용자에게 확정받은 상태다.

### B2. 진단

`references/principles.md`를 읽고 아래를 훑는다. 각 항목은 **파일·행 근거를 달아** 보고한다.

| 점검 | 증상 | 처방 |
|---|---|---|
| **no-op** | 모델이 기본으로 이미 하는 지시 | 삭제. 약한 leading word면 더 센 단어로 교체 |
| **duplication** | 같은 의미가 두 곳에 | 한 곳으로 모은다 (single source of truth) |
| **sediment** | 낡아서 안 맞는 층 | 삭제 |
| **sprawl** | 살아있고 안 겹치는데도 길다 | reference를 pointer 뒤로 내리거나 branch로 쪼갠다 |
| **negation** | 스타일 지시를 금지형으로 | 긍정형 목표로. 단 **경계 정의(`Do NOT use for X`)와 하드 가드레일은 그대로 둔다** — 그건 금지형이 더 정확하다 |
| **산문으로 쓴 결정적 절차** | 매번 같은 결과여야 하는 검증·파싱·집계를 산문이 지시한다 | `scripts/`로 이관. 취약·파괴적 작업도 포함 |
| **약한 context pointer** | 링크는 있는데 *언제* 읽는지가 없다 | 발화 조건을 pointer 문구에 넣는다. 대상이 크면 "해당 절만" |
| **참조가 2단계 이상** | 참조 파일이 또 다른 파일을 가리킨다 | 전부 `SKILL.md`에서 직접 링크. 안 그러면 부분 읽기로 정보가 빠진다 |
| **100행 넘는데 목차 없음** | 부분 읽기 시 전체 범위가 안 보인다 | 파일 상단에 `## Contents` |
| **`SKILL.md`가 500행 초과** | 행동 전 읽을 게 너무 많다 | reference로 쪼갠다. 번들 파일 크기는 제약이 아니다 |
| **트리거 충돌** | 다른 스킬 description과 겹쳐 오발화 | 겹치는 쪽에 `Do NOT use for ...` 배타 조항 |
| **description이 프로세스를 요약** | 본문을 건너뛰게 만든다 | 순수 트리거로 (A3의 함정) |
| **자기모순** | 스킬이 자기 규칙을 어긴다 | 규칙과 본문 중 어느 쪽이 틀렸는지 정하고 한쪽을 고친다 |

**완료 기준:** 각 발견에 파일·행과 처방이 붙었고, B1의 정체성 문장을 깨는 처방이 없다.

### B3. RED — 편집도 테스트가 먼저

고치려는 것이 **행동**이면 (안 불린다, 단계를 건너뛴다, 압박에 무너진다) 그 실패를 서브에이전트로 재현하고 원문을 기록한다. 재현되지 않으면 그 편집은 근거가 없다 — 보고만 하고 고치지 않는다.

고치려는 것이 **순수 정리**면 (오타, 중복 병합, 죽은 링크) 이 단계를 건너뛴다.

**완료 기준:** 행동 수정 항목마다 재현된 실패가 기록됐거나, 순수 정리로 분류됐다.

### B4. 최소 편집 + 재검증

기록된 실패만 겨냥해 고친다. 편집 후 **B1의 정체성 문장을 줄 단위로** 다시 확인한다 — 한 줄이라도 안 지켜지면 삭제한 것 중 무엇을 되돌려야 하는지 지목한다.

B3에서 재현한 실패는 같은 시나리오로 다시 돌려 통과를 확인한다.

**완료 기준:** 재현 실패가 통과로 바뀌었고, 정체성 문장이 전부 유지된다.

### B5. 배포

A5와 같다. description이나 파일 구성을 바꿨으면 `sync-docs`가 필수다.

**완료 기준:** A5와 동일.
