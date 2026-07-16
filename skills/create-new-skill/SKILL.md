---
name: create-new-skill
description: >
  Use when creating a new Claude/Codex skill, writing a SKILL.md from scratch,
  or testing a skill before deployment. Triggers: "create a skill", "new
  skill", "make this a skill", "skill test". Also fires for editing or
  reviewing an existing skill — the body routes those to the
  writing-great-skills reference. Do NOT use for one-off project docs or
  repository conventions that belong in AGENTS.md/CLAUDE.md.
---

# Create New Skill

Creating a skill IS Test-Driven Development applied to process documentation.
The Iron Law is the same: **no skill without a failing test first** — if you
didn't watch an agent fail without the skill, you don't know whether the skill
teaches the right thing. This applies to new skills AND to edits.

**Design reference:** the vocabulary and principles of a well-built skill —
invocation choice, description writing, information hierarchy, progressive
disclosure, leading words, pruning, failure modes — live in
[`../writing-great-skills/SKILL.md`](../writing-great-skills/SKILL.md).
Read it before writing the skill, and go straight to it when the task is
editing or reviewing an existing skill rather than creating one.

In this repository, plugin skills live under `./skills/<name>/SKILL.md` — the
shared root Claude Code and Codex both load.

## Steps

### 1. Decide it should exist

Create a skill for a technique that wasn't intuitively obvious, recurs across
projects, and applies broadly. Route the alternatives elsewhere:
project-specific conventions go to CLAUDE.md/AGENTS.md; anything enforceable
with a script or regex gets automated instead — save documentation for
judgment calls.

Done when: you can name the recurring situation the skill serves in one
sentence.

### 2. RED — record the baseline

Run pressure scenarios with a subagent WITHOUT the skill (discipline skills:
3+ combined pressures — time, sunk cost, authority, exhaustion). Record what
the agent chose and every rationalization it used, verbatim. These recorded
failures are the spec the skill must address.

Test design per skill type:

| Type | Test with | Passes when |
|------|-----------|-------------|
| Discipline (rules) | pressure scenarios, combined pressures | complies under maximum pressure |
| Technique (how-to) | application + edge-case scenarios | applies it to a new scenario |
| Pattern (mental model) | recognition + counter-example scenarios | knows when it applies and when not |
| Reference (docs/API) | retrieval + gap scenarios | finds and correctly applies the material |

Full methodology (scenario writing, pressure types, meta-testing):
[`testing-skills-with-subagents.md`](testing-skills-with-subagents.md).

Done when: every scenario's baseline behavior is documented verbatim.

### 3. GREEN — write the minimal skill

Write `skills/<name>/SKILL.md` addressing the recorded baseline failures and
nothing hypothetical. Follow writing-great-skills for frontmatter, invocation
choice, and structure. One excellent runnable example beats many mediocre
ones — you're good at porting.

**Description trap (tested):** the description states triggers only, never a
summary of the skill's process. A description that summarizes the workflow
becomes a shortcut — the agent follows the description and skips the body. A
description saying "code review between tasks" produced ONE review when the
body's flowchart required two; rewording it to pure triggering conditions
fixed it.

Re-run the same scenarios WITH the skill.

Done when: every baseline scenario now passes.

### 4. REFACTOR — close loopholes

Each new rationalization the agent finds gets an explicit counter in the
skill. For discipline skills, accumulate them into a rationalization table
("Excuse | Reality") and a red-flags self-check list, and state early that
violating the letter of the rules is violating their spirit. Then prune with
the writing-great-skills failure modes (no-op, duplication, sediment, sprawl,
negation).

Done when: a full test round surfaces no new rationalizations.

### 5. Deploy

Test each skill before starting the next — batching untested skills is
deploying untested code. Sync repo docs with the `update-project-docs` skill,
then commit (run `verify-secrets` first, per repo policy).

Done when: the skill is committed and the catalog/docs reflect it.

## Official guidance

Anthropic's skill-authoring best practices:
[`anthropic-best-practices.md`](anthropic-best-practices.md).
