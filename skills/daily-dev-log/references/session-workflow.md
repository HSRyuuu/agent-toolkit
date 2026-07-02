# Session Workflow

Use the required seven-step workflow: detect source availability, collect candidates, build a first-pass intermediate artifact, extract details, analyze, ask the user, then write Markdown.

## Step 1: Source Availability

Run `scripts/detect_sources.py --date YYYY-MM-DD` before collection.

Record:

- whether Codex session files exist for the date
- whether Claude session files likely exist for the date
- whether a configured KB root exists
- which sources are unavailable

Unavailable sources are not failures. Continue with the remaining sources and mention the gap when presenting candidates.

## Step 2: Candidate Collection

Collect lightweight evidence from available sources:

- session id
- source: `codex`, `claude`, `kb`, `manual`, or `git`
- start time and date
- cwd or project path
- human-origin marker such as Codex `thread_source == "user"`
- first clean user request snippets
- assistant final snippets when cheap to extract
- tool call counts and names
- likely file paths mentioned by tool calls or outputs
- confidence: `high`, `medium`, or `low`

Do not parse full logs into the final journal at this stage.

## Step 3: First-Pass Filtering Intermediate

Build a structured intermediate artifact before any detailed extraction.

Run source-specific filtering scripts:

```bash
python3 scripts/filter_codex_candidates.py codex-collection.json > codex-filtered.json
python3 scripts/filter_claude_candidates.py claude-collection.json > claude-filtered.json
```

Add KB search results under `kb_candidates` using the schema in `output-schema.md`. KB candidates come from read-only `kb-search` or KB helper scripts, not from raw session parsing.

Then combine them:

```bash
python3 scripts/build_first_pass_artifact.py \
  --date YYYY-MM-DD \
  --sources source-availability.json \
  --codex codex-filtered.json \
  --claude claude-filtered.json \
  --kb kb-candidates.json
```

The intermediate artifact should contain:

- `source_availability`
- `codex_candidates`
- `claude_candidates`
- `kb_candidates`
- `rejected_or_supporting`
- `notes`

Show or summarize this artifact to the user before detailed exploration.

## Step 4: Second-Pass Extraction

For selected or promising session candidates:

1. Extract full session digest using the relevant script.
2. Keep raw logs outside the journal.
3. Preserve session ids, file paths, tool names, safe excerpts, mentioned paths, and error snippets.

## Step 5: Agent Analysis

Analyze the extracted evidence into candidate work units:

- actual work outcome
- troubleshooting narrative
- decisions made
- lessons learned
- follow-up work
- confidence and missing context

Do not treat the first user prompt as sufficient proof of completed work. Prefer final answers, tool outputs, changed-file evidence, and user confirmations.

## Step 6: User Detail Question

Show the user a short numbered list:

```markdown
# YYYY-MM-DD Work Candidates

## 1. Short candidate title
- Source: Codex session `019f...`
- Evidence:
  - User asked: "..."
  - Tools: `exec_command`, `memory_sessions`
  - Project: `/path/to/project`
- Confidence: high

## 2. Short candidate title
- Source: Claude session `<id-or-file>`
- Evidence:
  - ...
- Confidence: medium
```

Then ask:

```text
오늘 회고에 중요하게 남길 항목을 골라주세요.
번호로 답해도 되고, 새로 추가해도 됩니다.
예: 1, 2 / 1은 자세히, 3은 한 줄만 / 회의에서 논의한 API 정책도 추가
```

Ask before doing additional deep exploration if the candidate list is large. If the user selects only a few items, deepen those and keep other items as brief mentions or omit them.

## Step 7: Markdown Writing

Write the final daily work log only after the user identifies important items or approves the candidate scope.

Use the daily template and include only safe summaries, session ids, and evidence references.

## Classification

Classify selected items into:

- `work-item`: implemented, reviewed, designed, researched, or documented work
- `troubleshooting`: debugging, incident response, investigation, flaky tests, broken tools
- `decision`: architecture, workflow, convention, or scope decision
- `learning`: reusable lesson or skill growth
- `follow-up`: unfinished task or next action

## Drafting Standard

Final writing should answer:

- What did I do?
- Why did it matter?
- What evidence supports it?
- What was hard or uncertain?
- What did I learn?
- What should I do next?
