---
name: agent-harness-construction
description: >
  Use when designing or reviewing AI agent harnesses, tool contracts,
  action/observation schemas, subagent delegation, completion evidence, error
  recovery, adversarial verification, or context budgeting. Triggers: "agent
  design review", "completion evidence", "adversarial verify", "receipt-only",
  "harness construction". Do NOT use for ordinary app code review.
metadata:
  origin: ECC
---

# Agent Harness Construction

Use this skill when you are improving how an agent plans, calls tools, recovers from errors, and converges on completion.

## Core Model

Agent output quality is constrained by:
1. Action space quality
2. Observation quality
3. Subagent delegation quality
4. Completion evidence quality
5. Recovery quality
6. Context budget quality

## Action Space Design

1. Use stable, explicit tool names.
2. Keep inputs schema-first and narrow.
3. Return deterministic output shapes.
4. Avoid catch-all tools unless isolation is impossible.

## Granularity Rules

- Use micro-tools for high-risk operations (deploy, migration, permissions).
- Use medium tools for common edit/read/search loops.
- Use macro-tools only when round-trip overhead is the dominant cost.

## Observation Design

Every tool response should include:
- `status`: success|warning|error
- `summary`: one-line result
- `next_actions`: actionable follow-ups
- `artifacts`: file paths / IDs

## Subagent Delegation Contract

Use this contract when the harness can spawn child agents:

1. Require receipt-only returns: child outputs are persisted to disk; parent receives only `path + verdict (+ hash)`. Never paste the full body into the response.
2. Use closed-vocabulary verdicts such as `OKAY|ITERATE|REJECT` so loop exits are machine-checkable.
3. Disable re-delegation by default. Delegation prompts should say: "Do the work yourself. Do not spawn agents unless explicitly authorized."
4. Treat child output as a CLAIM until the parent verifies it.
5. Reuse a planner when its accumulated context is an asset; spawn fresh reviewers when prior context would anchor the review.
6. For prompt wording details, use `prompt-master`.

## Completion & Evidence Contract

Completion is a typed claim plus independent verification:

1. Type evidence by surface: CLI = rerunnable command + output, UI = screenshot, API = actual request/response log.
2. Tests alone never prove done; they are necessary evidence, not sufficient evidence.
3. Separate `DoneClaim` from verification. Verify from an independent context that tries to disprove the claim.
4. Use three-state verdicts: `PASS|FAIL|INCONCLUSIVE`. Timeout, silence, or ambiguity is `INCONCLUSIVE`, never `PASS`.
5. End evidence-producing flows with machine-parsable markers such as `EVIDENCE_RECORDED: <path>`.

## Error Recovery Contract

For every error path, include:
- root cause hint
- safe retry instruction
- explicit stop condition
- blocker classification: `resolvable` vs `human_blocked`

`resolvable` means keep investigating with smaller goals, tools, or delegation. `human_blocked` is only for credentials, external approval, physical steps, or choices the agent cannot infer.

Turn-level stop conditions:
- one bounded unit of work completed
- same failure repeated three times
- safety or permission boundary reached

For self-diagnosis loops, use `agent-introspection-debugging`.

## Context Budgeting

1. Keep system prompt minimal and invariant.
2. Move large guidance into skills loaded on demand.
3. Prefer references to files over inlining long documents.
4. Compact at phase boundaries, not arbitrary token thresholds.
5. Before compaction, try the ladder: prune tool output, escalate model/context capacity, then hand off with a durable state file.
6. Put state that must survive compaction in files, not chat. Include approval waits as explicit file state such as `status: awaiting-approval`.
7. After context-loss symptoms, reread the work file and resume from it. Do not re-plan from memory.

## Architecture Pattern Guidance

- ReAct: best for exploratory tasks with uncertain path.
- Function-calling: best for structured deterministic flows.
- Hybrid (recommended): ReAct planning + typed tool execution.

## Benchmarking

Track:
- completion rate
- retries per task
- pass@1 and pass@3
- cost per successful task

## Enforcement Layers

Rules become enforceable only when the layers agree:

1. Documentation: policy and rationale.
2. Declaration: config, frontmatter, schema, or manifest.
3. Prompt: model-facing instruction.
4. Runtime: code or tool rejection.

Prompt-only requests are guidance, not a harness contract.

## Anti-Patterns

- Too many tools with overlapping semantics.
- Opaque tool output with no recovery hints.
- Error-only output without next steps.
- Context overloading with irrelevant references.
- Child agents returning full reports instead of receipts.
- Completion claims without typed evidence and independent verification.
