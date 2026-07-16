---
name: help-agent-toolkit
description: >
  Use when the user asks what agent-toolkit skills exist or which agent-toolkit
  skill fits a task. Triggers: "agent-toolkit 스킬 목록", "어떤 스킬 있어?",
  "툴킷에 뭐 있어?", "/help-agent-toolkit", "이거 할 때 쓸 스킬 추천",
  "xxx 하려면 어떤 스킬?". Read-only. Do NOT use for non-agent-toolkit skills
  or performing the chosen task.
---

# Help Agent Toolkit — 스킬 카탈로그 & 의도 매칭

`agent-toolkit` 플러그인에 등록된 스킬 중 사용자가 지금 필요한 것을 찾을 수 있게 돕는다. 사용자의 입력 의도에 따라 두 가지 모드 중 하나로 동작한다.

## 두 가지 모드

| 모드 | 트리거 예시 | 동작 |
|---|---|---|
| **A. 목록** | "스킬 목록", "뭐 있어?", "전체 보여줘", "/help-agent-toolkit" (인수 없이) | 모든 스킬을 카테고리별 마크다운 테이블로 출력 |
| **B. 추천** | "ERD 그리고 싶어", "FastAPI 코드 리뷰 받고 싶어", "프로젝트 셋업 도와줘", "xxx 하려면 어떤 스킬?" | 사용자 의도를 분석하고 frontmatter 매칭 → 관련도 높은 순으로 추천 테이블 |

> 모호하면 모드 A부터 실행해 사용자가 직접 고르게 한다.

## 대전제

1. **read-only 스킬이다.** 파일을 만들거나 수정하지 않는다. 정보 제공만 한다.
2. **출처는 SKILL.md frontmatter다.** `docs/catalog.md`는 보조 참고로만 쓴다 — 자동 갱신되지 않으므로 옛 정보가 있을 수 있음. **단일 진실의 원천은 각 SKILL.md의 `description` 필드**.
3. **agent-toolkit 스킬만 다룬다.** 이 플러그인의 `skills/` 디렉토리만 스캔한다. 외부 플러그인이나 사용자 글로벌 스킬은 대상이 아니다.
4. **임의 추천 금지.** 사용자 의도와 명확히 맞물리는 스킬만 추천하고, 매칭이 없으면 "해당 스킬 없음"이라고 명시한다.

## 사전 조건

- **플러그인 루트**: 현재 `SKILL.md`의 위치를 기준으로 찾는다. 이 파일은 `<plugin-root>/skills/help-agent-toolkit/SKILL.md`에 있으므로, 이 파일의 두 단계 상위 디렉토리가 플러그인 루트다. Codex/omo에서 `${PLUGIN_ROOT}`가 있거나 Claude Code에서 `${CLAUDE_PLUGIN_ROOT}`가 있으면 그 값을 우선 사용해도 된다.
- 카탈로그가 비어 있다면 (모든 디렉토리에 SKILL.md가 0개) — 즉시 종료하고 "스킬 없음"이라고 알린다.

## 워크플로우

### Step 0 — 모드 판정

사용자 입력을 보고 모드를 정한다.

- 입력에 **구체적 의도 키워드**(동사 + 대상)가 있으면 → **모드 B (추천)**
  - 예: "ERD 그리고 싶어", "코드 리뷰 받고 싶어", "PR 만들어줘", "스프링부트 코드 표준 알고 싶어"
- 입력이 **목록을 요청**하거나 **인수가 비어 있으면** → **모드 A (목록)**
  - 예: "스킬 목록", "어떤 스킬 있어?", "/help-agent-toolkit"
- 애매하면 → **모드 A**로 시작하고 보고서 끝에 "특정 작업이 있으면 알려주세요. 의도 기반 추천도 가능합니다."를 덧붙인다.

### Step 1 — 카탈로그 수집

`skills/` 아래의 모든 `SKILL.md`에서 frontmatter를 읽는다. 먼저 플러그인 루트를 다음 우선순위로 결정한다:

1. `${PLUGIN_ROOT}` 또는 `${CLAUDE_PLUGIN_ROOT}`가 있고 그 아래에 `skills/`가 있으면 사용한다.
2. Codex/Claude가 로드한 이 `SKILL.md`의 실제 파일 경로에서 `../..`로 올라간다.
3. 현재 작업 디렉토리가 이 저장소 루트이고 `skills/`가 있으면 현재 작업 디렉토리를 사용한다.

```bash
ROOT="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
[ -n "$ROOT" ] && [ -d "$ROOT/skills" ] || ROOT="<plugin-root>"

find "$ROOT/skills" -mindepth 2 -maxdepth 2 -name SKILL.md 2>/dev/null
```

각 파일에 대해:

```bash
# frontmatter 영역만 추출 (--- 와 --- 사이)
awk '/^---$/{c++; if(c==2)exit; next} c==1' "$file"
```

다음 필드를 메모리에 보관한다:
- `category` — frontmatter나 description에서 도출한 용도 라벨. 확실하지 않으면 "일반"으로 둔다.
- `name` — frontmatter의 `name:` 값
- `description` — frontmatter의 `description:` 값 (전체. 모드 B 매칭에 사용)
- `path` — SKILL.md 상대 경로

> `description`이 누락된 SKILL.md는 한 줄로 한 번만 경고 출력하고 카탈로그에서 제외한다. 스킬이 깨진 신호다.

### Step 2 — 모드별 출력

#### 모드 A — 전체 목록

카테고리별로 분리한 표를 출력한다. **description은 너무 길면 첫 문장 또는 80자로 자른다** (전체는 SKILL.md를 클릭해서 보라고 안내).

```markdown
## agent-toolkit 스킬 카탈로그

**플러그인 루트:** `<ROOT 절대경로>`
**총 개수:** N개

### skills/

| 스킬 | 경로 | 한 줄 설명 |
|---|---|---|
| `name` | `skills/<dir>/SKILL.md` | description 첫 문장 또는 80자 컷 |
| ... | ... |

---

**다음 행동:**
- 특정 스킬을 자세히 보려면 SKILL.md 파일을 열어보세요.
- "ERD 만들고 싶어" 처럼 구체적 의도를 알려주시면 관련 스킬만 골라 추천드립니다 (모드 B).
```

#### 모드 B — 의도 기반 추천

사용자 의도를 분석하고, 각 스킬의 `description` 전체와 비교해 매칭한다.

**매칭 기준 (위에서 아래 순으로 강함):**

1. **직접 키워드 매칭** — 사용자 메시지의 핵심 단어가 description의 트리거 예시·키워드에 직접 등장 (예: "ERD" ↔ `create-mermaid-erd` description의 "ERD")
2. **동의어 / 영-한 매칭** — "스키마 뷰어" ↔ "schema viewer", "치트시트" ↔ "cheat sheet", "프로젝트 세팅" ↔ "project setup"
3. **목적 의미 매칭** — 사용자의 목적과 스킬의 "사용 시점"이 같은 종류 (예: "코드 리뷰 받고 싶어" ↔ Java/Kotlin/FastAPI 표준 스킬들 중 언어와 매칭되는 것)

**관련도 등급:**

- 🟢 **강력 추천** — 직접 키워드 매칭 + 목적 일치
- 🟡 **참고** — 동의어 매칭 또는 부분 키워드 매칭
- ⚪ **약한 관련** — 같은 영역이지만 정확히 그 작업은 아님 (예: 사용자가 "ERD 그리기"인데 `html-db-schema-viewer-creator`는 ERD가 아니라 스키마 뷰어)

**출력 형식:**

상단에 **요약 테이블**(스킬명 + 한 줄 사용 시점)을 먼저 두고, 그 아래에 **상세 추천 테이블**(관련도순)을 둔다. 사용자가 위쪽 요약만 보고도 빠르게 후보를 훑을 수 있어야 한다.

```markdown
## agent-toolkit 스킬 추천

**사용자 의도:** "<사용자 원본 메시지>"
**탐지된 키워드:** `<키워드1>`, `<키워드2>`, ...

### 요약 (관련도순)

| 스킬 | 경로 | 어떨 때 쓰는지 |
|---|---|---|
| `name` | `skills/<dir>/SKILL.md` | description의 "사용 시점" 또는 트리거 예시를 한 줄로 압축 (60~80자) |
| `name` | `skills/<dir>/SKILL.md` | ... |
| `name` | `skills/<dir>/SKILL.md` | ... |

### 상세 매칭

| 관련도 | 스킬 | 경로 | 카테고리 | 매칭 이유 | 트리거 / 사용 시점 |
|---|---|---|---|---|---|
| 🟢 | `name` | `skills/<dir>/SKILL.md` | 독립 | "ERD" 키워드 직접 일치, "DB 설계 시각화" 목적 일치 | description의 트리거 예시 발췌 |
| 🟡 | `name` | `skills/<dir>/SKILL.md` | 메타 | "스키마" 동의어 매칭 | ... |
| ⚪ | `name` | `skills/<dir>/SKILL.md` | 독립 | 같은 DB 영역이지만 ERD가 아닌 스키마 탐색기 | ... |

### 매칭 없음 (해당하는 경우)

위 의도에 정확히 맞는 스킬이 없습니다. 가까운 영역의 스킬은 다음과 같습니다:
- (있으면 약한 관련만 나열)
- 아무것도 없으면 "agent-toolkit에 해당 스킬이 없습니다. 새 스킬을 만들려면 `create-new-skill`를 참고하거나 `skills/<이름>/SKILL.md`를 작성하세요."

### 외부 스킬 (agent-toolkit 밖)

같은 의도에 쓸 만한 **agent-toolkit이 아닌** 스킬을 매우 간단하게(이름·짧은 설명만) 한 표로 덧붙인다. 관련도 표기·매칭 이유·카테고리·경로는 적지 않는다 — 어디까지나 보조 정보다.

> **외부 스킬 후보의 출처** — 현재 세션 system prompt의 "available skills" 목록 중 `agent-toolkit:` 접두어가 **없는** 모든 스킬. 다른 플러그인(`oh-my-claudecode:`, `document-skills:`, `codex:` 등)과 글로벌 스킬(`kb-*`, `defuddle`, `python-starter` 등)이 여기에 해당한다. 파일을 스캔하지 않고 세션에 이미 노출된 목록만 사용한다.

| 스킬 | 짧은 설명 |
|---|---|
| `<name>` | description을 50자 내외로 압축 |
| ... | ... |

> 후보가 한 개도 없으면 이 섹션 자체를 생략한다. (억지 추천 금지 — 대전제 4)

### 다음 행동

- 추천된 스킬을 사용하려면 해당 슬래시 커맨드를 호출하세요. 예: `/<skill-name>`
- 더 좁히려면 추가 컨텍스트를 주세요 (사용 중인 언어, 프로젝트 단계 등).
```

> **매칭 이유는 반드시 구체적으로**: "관련됨" / "유용함" 같은 모호한 표현 금지. description의 어떤 단어/문구와 매칭됐는지를 짧게 인용한다.

### Step 3 — 후속 안내

- 모드 A 후 사용자가 의도를 추가로 말하면 즉시 모드 B로 전환한다.
- 모드 B 후 사용자가 "전체도 보여줘" 같이 말하면 모드 A로 전환한다.
- 그 외 후속 작업은 이 스킬의 책임이 아니다 — 사용자가 추천된 스킬을 실제로 호출하도록 유도만 한다.

## 카탈로그가 비어있을 때

`skills/`에 SKILL.md가 0개라면:

```markdown
## agent-toolkit 스킬 없음

**플러그인 루트:** `<ROOT>`

이 플러그인에 등록된 스킬이 없습니다. 새 스킬을 추가하려면:
- `create-new-skill` 참고 (새 스킬을 만들 때)
- 직접 `skills/<이름>/SKILL.md` 작성 후 새 세션 시작
```

## docs/catalog.md 와의 관계

`docs/catalog.md`는 사람이 손으로 관리하는 README 보조 문서다. 이 스킬은 **그 파일을 신뢰하지 않는다**:

- catalog.md가 옛 정보를 가질 수 있음 (예: 8개 스킬로 표기되어 있지만 실제로는 20개)
- 모든 출력은 SKILL.md frontmatter 실시간 스캔 결과를 기준으로 한다
- catalog.md를 갱신하는 것은 별도 작업이며 이 스킬의 책임이 아니다 (필요하면 `update-project-docs` 영역)

## 예외 사항

다음은 **문제가 아니다**:

1. **카탈로그 일부 누락** — frontmatter가 깨진 SKILL.md가 있어도 한 줄 경고만 출력하고 나머지를 정상 처리한다.
2. **매칭 결과 0개** — 모드 B에서 정확한 매칭이 없으면 솔직하게 보고한다. 억지로 끼워 맞춘 추천을 만들지 않는다 (대전제 4).
3. **사용자가 카테고리 한 종류만 보고 싶어함** — "독립 스킬만 보여줘" 같은 요청이면 해당 디렉토리만 출력한다.

## Related Files

| File | Purpose |
|------|---------|
| `<plugin-root>/skills/*/SKILL.md` | 플러그인 스킬 카탈로그 원천 |
| `<plugin-root>/docs/catalog.md` | 사람이 쓰는 보조 카탈로그 (이 스킬은 신뢰하지 않음) |
| `<plugin-root>/.codex-plugin/plugin.json` | Codex가 읽는 플러그인 manifest와 `skills` 루트 확인용 |
| `<plugin-root>/.claude-plugin/plugin.json` | Claude Code가 읽는 플러그인 manifest와 `skills` 루트 확인용 |
