# Principles — 예측 가능한 스킬을 만드는 레버

[`writing-great-skill`](../SKILL.md)의 판정 어휘. A3·A4·B2·B4에서 읽는다.

## Contents

- Invocation · Writing the description
- Information hierarchy — the four rungs · Prose or script · **하드 제약**
- When to split · Pruning · Leading words · Failure modes

A skill exists to wrangle determinism out of a stochastic system. **Predictability** — the agent taking the same _process_ every run, not producing the same output — is the root virtue; every lever below serves it.

**Bold terms** are defined in [`GLOSSARY.md`](GLOSSARY.md); look them up there for the full meaning — 애매한 용어 하나만 찾아 읽고, 통독하지 않는다.

## Invocation

Two choices, trading different costs:

- A **model-invoked** skill keeps a **description**, so the agent can fire it autonomously _and_ other skills can reach it (you can still type its name too). It contributes to **context load** — the description sits in the window every turn. Mechanics: omit `disable-model-invocation`, and write a model-facing description with rich trigger phrasing ("Use when the user wants…, mentions…").
- A **user-invoked** skill strips the description from the agent's reach: only you, typing its name, can invoke it — and no other skill can. Zero context load, but it spends **cognitive load**: _you_ are the index that must remember it exists. Mechanics: set `disable-model-invocation: true`; the `description` becomes human-facing — a one-line summary, trigger lists stripped.

Pick model-invocation only when the agent must reach the skill on its own, or another skill must. If it only ever fires by hand, make it user-invoked and pay no context load.

When user-invoked skills multiply past what you can remember, that piled-up cognitive load is cured by a **router skill**: one user-invoked skill that names the others and when to reach for each.

## Writing the description

A model-invoked **description** does two jobs — state what the skill is, and list the **branches** that should trigger it. Every word increases **context load**, so a description earns even harder pruning than the body:

- **Front-load the skill's leading word** — the description is where it does its invocation work.
- **One trigger per branch.** Synonyms that rename a single branch are **duplication** — "build features using TDD … asks for test-first development" is one branch written twice. Collapse them; keep only genuinely distinct branches.
- **Cut identity that's already in the body.** Keep the description to triggers, plus any "when another skill needs…" reach clause.

## Information hierarchy

A skill is built from three content types — **steps**, **reference**, and **executable script** — that mix freely: a skill can be all steps, all reference, or any blend. The core decision is which to use and where each sits on the **information hierarchy**, a ladder ranked by how immediately the agent needs the material:

1. **In-skill step** — an ordered action in `SKILL.md`, the primary tier: what the agent does, in order. Each step ends on a **completion criterion**, the condition that tells the agent the work is done. Make it _checkable_ (can the agent tell done from not-done?) and, where it matters, _exhaustive_ ("every modified model accounted for", not "produce a change list") — a vague criterion invites **premature completion**.
2. **In-skill reference** — a definition, rule, or fact in `SKILL.md`, consulted on demand. Often a legitimately flat peer-set (every rule of a review on one rung) — a fine arrangement, not a smell. _This file is all reference, disclosed one rung down from its skill._
3. **External reference** — reference pushed out of `SKILL.md` into a separate file, reached by a **context pointer**, loaded only when the pointer fires. (Spans _disclosed_ reference — a sibling file like `GLOSSARY.md`, still part of the skill — through fully **external reference** that lives outside the skill system and any skill can point at.)
4. **Executable script** — a bundled `scripts/*.py|js|ts|sh` that is **run, not read**. Off the reading ladder entirely: only its _output_ enters context, so a 500-line script costs the tokens of its stdout. The only rung that delivers **predictability** outright rather than nudging toward it — the same input yields the same output, with no sampling in between.

A demanding completion criterion drives thorough **legwork** — the digging the agent does within the work — whether the skill has steps or not, since "every rule applied" binds flat reference just as "every step done" binds a sequence.

### Prose or script — degrees of freedom

Match specificity to the task's _fragility_ and _variability_, not to how often it recurs.

| 자유도 | 형태 | 조건 |
|---|---|---|
| **High** | 산문 지시 | 유효한 접근이 여럿 · 맥락이 판단을 가름 · 휴리스틱이 이끔 |
| **Medium** | 파라미터 있는 스크립트, 의사코드 | 선호 패턴이 있음 · 약간의 변형 허용 · 설정이 동작을 바꿈 |
| **Low** | 파라미터 거의 없는 특정 스크립트 | 취약하고 오류 나기 쉬움 · 일관성이 critical · 정해진 순서를 지켜야 함 |

절벽 사이 좁은 다리에는 난간을 놓고, 탁 트인 들판에서는 방향만 준다. **_Prefer scripts for deterministic operations_** — 검증 로직을 매번 생성시키지 말고 `validate_*.py`를 쓴다. 반복되지 않는 일회성이라도 **일괄 변경·파괴적 작업·고위험 작업**은 스크립트로 고정한다. 반대로 맥락이 최선의 경로를 정하는 일(코드 리뷰 등)을 스크립트로 굳히면 스킬이 재사용성을 잃는다.

번들할 때:

- **실행형인지 참조형인지 명시한다** — `"Run analyze_form.py to extract fields"` (실행, 기본값) 대 `"See analyze_form.py for the extraction algorithm"` (참조). 대부분 실행이 맞다
- 스크립트가 **문제를 풀고, 에이전트에게 떠넘기지 않는다** — 에러 처리를 스크립트 안에서 한다
- **정당화되지 않은 상수 금지** — 값의 근거를 주석으로 남긴다. 작성자가 모르는 값을 에이전트가 알 리 없다
- 고위험 작업은 **계획 → 검증 → 실행** — 에이전트가 구조화된 계획 파일을 쓰고, 스크립트가 그것을 기계 검증한 뒤 실행한다

(근거: Anthropic [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills))

Push too little down and the top bloats; push too much and you hide material the agent actually needs. That tension is the whole decision.

**Progressive disclosure** is the move down the ladder — out of `SKILL.md` into a linked file — so the top stays legible. Mechanics: a linked `.md` file in the skill folder, named for what it holds (this skill discloses its full definitions to `GLOSSARY.md`). Some skills are used in more than one way, and each distinct way is a **branch** — different runs taking different paths through the skill. Branching is the cleanest disclosure test: inline what every branch needs, and push behind a pointer what only some branches reach. A **context pointer**'s _wording_, not its target, decides when and how reliably the agent reaches the material.

### 하드 제약 — 벤더가 수치로 못 박은 것

위 논의는 판단이지만, 아래는 숫자다. 3단계 로딩 모델이 그 근거다:

| Level | 로드 시점 | 비용 | 내용 |
|---|---|---|---|
| 1 Metadata | 항상 (startup) | **~100 tokens/skill** | frontmatter의 `name` + `description` |
| 2 Instructions | 트리거될 때 | **under 5k tokens** | `SKILL.md` 본문 |
| 3+ Resources | 필요할 때 | **접근 전까지 0** | 번들 파일. 참조는 읽을 때 로드, 스크립트는 **출력만** |

- **`SKILL.md` 본문 500행 이하.** 넘으면 파일을 쪼갠다
- **참조는 `SKILL.md`에서 1단계 깊이.** 참조된 파일이 또 다른 파일을 가리키면 에이전트가 `head -100` 류로 **부분만 읽어** 정보가 빠진다. 모든 참조 파일은 `SKILL.md`에서 직접 링크한다
- **100행 넘는 참조 파일에는 목차를 단다.** 부분 읽기를 당해도 전체 범위가 보이게
- **번들 자체에는 실질적 상한이 없다** — 안 읽으면 0토큰이므로 완전한 API 문서·대용량 예시를 넣어도 된다. 짧아야 하는 것은 `SKILL.md`뿐이다

숫자가 노리는 것은 토큰 절약만이 아니다. 위쪽 사다리가 길어지면 에이전트가 행동하기 전에 헤매고 주의가 묽어진다.

(근거: Anthropic [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices))

Where the ladder decides _how far down_ a piece sits, **co-location** decides _what sits beside it_ once there: keep a concept's definition, rules, and caveats under one heading rather than scattered, so reading one part brings its neighbours with it.

## When to split

**Granularity** is how finely you divide skills, and each cut spends one of the two loads, so split only when the cut earns it. Two cuts:

- **By invocation** — split off a **model-invoked** skill when you have a distinct **leading word** that should trigger it on its own, or another skill must reach it. You pay **context load** for the new always-loaded **description**, so that independent reach has to be worth it.
- **By sequence** — split a run of **steps** when the steps still ahead (a step's **post-completion steps**) tempt the agent to rush the one in front of it (**premature completion**). Keeping them out of view encourages the agent to do more **legwork** on the current task.

## Pruning

Keep each meaning in a **single source of truth**: one authoritative place, so changing the behaviour is a one-place edit.

Check every line for **relevance**: does it still bear on what the skill does?

Then hunt **no-ops** sentence by sentence, not just line by line: run the no-op test on each sentence in isolation, and when one fails, delete the whole sentence rather than trim words from it. Be aggressive — most prose that fails should go, not be rewritten.

## Leading words

A **leading word** is a compact concept already living in the model's pretraining that the agent thinks with while running the skill (e.g. _lesson_, _fog of war_, _tracer bullets_). Repeated throughout the text (though not necessarily - a strong leading word might only be needed once), it accumulates a distributed definition and anchors a whole region of behaviour in the fewest tokens, by recruiting priors the model already holds.

It serves predictability twice. In the body it anchors _execution_: the agent reaches for the same behaviour every time the word appears. In the description it anchors _invocation_: when the same word lives in your prompts, docs, and code, the agent links that shared language to the skill and fires it more reliably.

Hunt for opportunities to refactor skills to use leading words. A triad spelled out at three sites (**duplication**), a description spending a sentence to gesture at one idea — each is a passage begging to **collapse** into a single token. Examples include:

- "fast, deterministic, low-overhead" -> _tight_ — one quality restated across a phase — into a single pretrained word (a _tight_ loop).
- "a loop you believe in" -> _red_ — converts a fuzzy gate into a binary observable state (the loop goes _red_ on the bug, or it doesn't).

You win twice over: fewer tokens, _and_ a sharper hook for the agent to hang its thinking on. Assume every skill is carrying restatements that leading words retire — go find them.

## Failure modes

Use these to diagnose issues the user may be having with the skill.

- **Premature completion** — ending a step before it's genuinely done, attention slipping to _being done_. Defence, in order: sharpen the completion criterion first (cheap, local); only if it is irreducibly fuzzy _and_ you observe the rush, hide the post-completion steps by splitting (the sequence cut).
- **Duplication** — the same meaning in more than one place. Costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank.
- **Sediment** — stale layers that settle because adding feels safe and removing feels risky. The default fate of any skill without a pruning discipline.
- **Sprawl** — a skill simply too long, even when every line is live and unique. Hurts readability and maintainability and wastes tokens. The cure is the ladder: disclose **reference** behind pointers, and split by **branch** or sequence so each path carries only what it needs.
- **No-op** — a line the model already obeys by default, so you pay load to say nothing. The test: does it change behaviour versus the default? A weak leading word (_be thorough_ when the agent is already thorough-ish) is a no-op; the fix is a stronger word (_relentless_), not a different technique.
- **Negation** — steering by prohibition backfires: _don't think of an elephant_ names the elephant and makes it more available, not less. Prompt the **positive** — state the target behaviour so the banned one is never spoken; keep a prohibition only as a hard guardrail you can't phrase positively, and even then pair it with what to do instead.
