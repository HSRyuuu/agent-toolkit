---
name: trace
description: >
  Use when you need to explain WHY an observed result happened — ambiguous,
  causal, evidence-heavy problems where jumping straight to a fix is premature.
  Runs competing hypotheses in parallel lanes, ranks them by evidence strength,
  runs a rebuttal round, and recommends the next probe that collapses uncertainty
  fastest. Triggers: "왜 이런 결과가 나왔지", "원인 추적", "이 출력 역추적해줘",
  "regression 원인", "trace the cause", "root cause 분석", "premortem", "postmortem",
  "/trace". Do NOT use for a straightforward fix with a known cause — use ordinary
  debugging.
argument-hint: "<observation to trace>"
metadata:
  origin: oh-my-claudecode
---

# Trace Skill

Use this skill for ambiguous, causal, evidence-heavy questions where the goal is to explain **why** an observed result happened, not to jump directly into fixing or rewriting code.

This is an orchestration layer that runs disciplined **tracer lanes**: restate the observation, generate competing explanations, gather evidence in parallel, rank the explanations, and propose the next probe that would collapse uncertainty fastest. The per-lane tracer agent prompt lives in [references/tracer-agents.md](references/tracer-agents.md); read it before running lanes, and use it as the spawned agent's instructions (Claude Code team mode) or as your own lane role (single-agent harnesses such as Codex).

## Good entry cases

Use `/trace` when the problem is:

- ambiguous
- causal
- evidence-heavy
- best answered by exploring competing explanations in parallel

Examples:
- runtime bugs and regressions
- performance / latency / resource behavior
- architecture / premortem / postmortem analysis
- scientific or experimental result tracing
- config / routing / orchestration behavior explanation
- “given this output, trace back the likely causes”

## Core tracing contract

Always preserve these distinctions:

1. **Observation** -- what was actually observed
2. **Hypotheses** -- competing explanations
3. **Evidence For** -- what supports each explanation
4. **Evidence Against / Gaps** -- what contradicts it or is still missing
5. **Current Best Explanation** -- the leading explanation right now
6. **Critical Unknown** -- the missing fact keeping the top explanations apart
7. **Discriminating Probe** -- the highest-value next step to collapse uncertainty

Do **not** collapse into:
- a generic fix-it coding loop
- a generic debugger summary
- a raw dump of worker output
- fake certainty when evidence is incomplete

## Evidence strength hierarchy

Treat evidence as ranked, not flat.

From strongest to weakest:

1. **Controlled reproductions / direct experiments / uniquely discriminating artifacts**
2. **Primary source artifacts with tight provenance** (trace events, logs, metrics, benchmark outputs, configs, git history, file:line behavior)
3. **Multiple independent sources converging on the same explanation**
4. **Single-source code-path or behavioral inference**
5. **Weak circumstantial clues** (timing, naming, stack order, resemblance to prior bugs)
6. **Intuition / analogy / speculation**

Explicitly down-rank hypotheses that depend mostly on lower tiers when stronger contradictory evidence exists.

## Strong falsification / disconfirmation rules

Every serious `/trace` run must try to falsify its own favorite explanation.

For each top hypothesis:

- collect evidence **for** it
- collect evidence **against** it
- state what distinctive prediction it makes
- state what observation would be hard to reconcile with it
- identify the cheapest probe that would discriminate it from the next-best alternative

Down-rank a hypothesis when:

- direct evidence contradicts it
- it survives only by adding new unverified assumptions
- it makes no distinctive prediction compared with rivals
- a stronger alternative explains the same facts with fewer assumptions
- its support is mostly circumstantial while the rival has stronger evidence tiers

## Execution model

`/trace` runs multiple **tracer lanes** that pursue deliberately different explanations. Pick the mechanism by harness:

- **Claude Code**: use built-in team mode / subagent spawning (Task tool). Spawn one tracer worker per hypothesis lane and run them concurrently, passing the agent prompt from [references/tracer-agents.md](references/tracer-agents.md) as each worker's instructions. Suggested model tier for workers: `sonnet`.
- **Codex or other harnesses with parallel subagents**: spawn one lane per hypothesis the same way, using the same reference prompt.
- **Single-agent fallback**: run the lanes sequentially in one context, adopting the reference prompt's role for one lane at a time, keeping each hypothesis explicitly separate and never letting a favored lane contaminate the others.

Either way the lead should:

1. Restate the observed result or “why” question precisely
2. Extract the tracing target
3. Generate multiple deliberately different candidate hypotheses
4. Run **3 tracer lanes by default**
5. Assign one lane owner per hypothesis
6. Instruct each lane owner to gather evidence **for** and **against** its lane
7. Run a **rebuttal round** between the leading hypothesis and the strongest remaining alternative
8. Detect whether the top lanes genuinely differ or actually converge on the same root cause
9. Merge findings into a ranked synthesis with an explicit critical unknown and discriminating probe

Important: lanes should pursue deliberately different explanations, not the same explanation in parallel.

## Default hypothesis lanes

Unless the prompt strongly suggests a better partition, use these 3 default lanes:

1. **Code-path / implementation cause**
2. **Config / environment / orchestration cause**
3. **Measurement / artifact / assumption mismatch cause** — covers verification-method defects, not just system defects. Examples: the verification query reuses a single dimensional key across distinct entities, tenants, streams, or groups; the comparison filter shape does not match the schema grain; or the catalog or column name was assumed portable across runtimes without enumeration. This includes multi-entity premise/key-assumption mismatches.

For lane 3, cross-entity discrepancies need a premise audit before escalation: enumerate entity dimensions and check whether a zero-row or mismatch result came from applying one key across multiple entities rather than from a system defect; the result may be a verification-methodology defect.

These defaults are intentionally broad so the first slice works across bug, performance, architecture, and experiment tracing.

## Mandatory cross-check lenses

After the initial evidence pass, pressure-test the leaders with these lenses when relevant:

- **Systems lens** -- queues, retries, backpressure, feedback loops, upstream/downstream dependencies, boundary failures, coordination effects
- **Premortem lens** -- assume the current best explanation is incomplete or wrong; what failure mode would embarrass the trace later?
- **Science lens** -- controls, confounders, measurement bias, alternative variables, falsifiable predictions

These lenses are not filler. Use them when they can surface a missed explanation, hidden dependency, or weak inference.

## Worker contract

Each lane owner adopts the **tracer agent role** defined in [references/tracer-agents.md](references/tracer-agents.md), not a generic executor role.

Each lane owner must:

- own exactly one hypothesis lane
- restate its lane hypothesis explicitly
- gather evidence **for** the lane
- gather evidence **against** the lane
- rank the evidence strength behind its case
- call out missing evidence, failed predictions, and remaining uncertainty
- name the **critical unknown** for the lane
- recommend the best lane-specific **discriminating probe**
- avoid collapsing into implementation unless explicitly told to do so

Useful evidence sources include:

- relevant code, tests, configs, docs, logs, outputs, and benchmark artifacts
- any existing trace / replay / session artifacts your harness exposes
- git history and file:line behavior

Recommended lane return structure:

1. **Lane**
2. **Hypothesis**
3. **Evidence For**
4. **Evidence Against / Gaps**
5. **Evidence Strength**
6. **Critical Unknown**
7. **Best Discriminating Probe**
8. **Confidence**

## Leader synthesis contract

The final `/trace` answer should synthesize, not just concatenate.

Return:

1. **Observed Result**
2. **Ranked Hypotheses**
3. **Evidence Summary by Hypothesis**
4. **Evidence Against / Missing Evidence**
5. **Rebuttal Round**
6. **Convergence / Separation Notes**
7. **Most Likely Explanation**
8. **Critical Unknown**
9. **Recommended Discriminating Probe**
10. **Additional Trace Lanes** (optional, only if uncertainty remains high)

Preserve a ranked shortlist even if one explanation is currently dominant.

## Rebuttal round and convergence detection

Before closing the trace:

- let the strongest non-leading lane present its best rebuttal to the current leader
- force the leader to answer the rebuttal with evidence, not assertion
- if the rebuttal materially weakens the leader, re-rank the table
- if two “different” hypotheses reduce to the same underlying mechanism, merge them and say so explicitly
- if two hypotheses still imply different next probes, keep them separate even if they sound similar

Do not claim convergence just because multiple lanes use similar language. Convergence requires either:

- the same root causal mechanism, or
- independent evidence streams pointing to the same explanation

## Explicit down-ranking guidance

The lead should explicitly say why a hypothesis moved down:

- contradicted by stronger evidence
- lacks the observation it predicted
- requires extra ad hoc assumptions
- explains fewer facts than the leader
- lost the rebuttal round
- converged into a stronger parent explanation

This is important because `/trace` should teach the reader **why** one explanation outranks another, not just present a final table.

## Suggested lead prompt skeleton

Use an orchestration prompt along these lines:

1. “Restate the observation exactly.”
2. “Generate 3 deliberately different hypotheses.”
3. “Create one tracer lane per hypothesis — Claude Code team mode / Task subagents with the prompt from references/tracer-agents.md, or sequential lanes in one context if the harness has no subagents.”
4. “For each lane, gather evidence for and against, rank evidence strength, and name the critical unknown plus best discriminating probe.”
5. “Apply systems, premortem, and science lenses to the leaders if useful.”
6. “Run a rebuttal round between the top two explanations.”
7. “Return a ranked explanation table, convergence notes, the critical unknown, and the single best discriminating probe.”

## Output quality bar

Good `/trace` output is:

- evidence-backed
- concise but rigorous
- skeptical of premature certainty
- explicit about missing evidence
- practical about the next action
- explicit about why weaker explanations were down-ranked

## Example final synthesis shape

### Observed Result
[What happened]

### Ranked Hypotheses
| Rank | Hypothesis | Confidence | Evidence Strength | Why it leads |
|------|------------|------------|-------------------|--------------|
| 1 | ... | High / Medium / Low | Strong / Moderate / Weak | ... |

### Evidence Summary by Hypothesis
- Hypothesis 1: ...
- Hypothesis 2: ...
- Hypothesis 3: ...

### Evidence Against / Missing Evidence
- Hypothesis 1: ...
- Hypothesis 2: ...
- Hypothesis 3: ...

### Rebuttal Round
- Best rebuttal to leader: ...
- Why leader held / failed: ...

### Convergence / Separation Notes
- ...

### Most Likely Explanation
[Current best explanation]

### Critical Unknown
[Single missing fact keeping uncertainty open]

### Recommended Discriminating Probe
[Single next probe]

### Additional Trace Lanes
[Only if uncertainty remains high]
