---
name: daily-dev-log
description: Use when creating or preparing a personal daily development work log from Codex sessions, Claude sessions, KB notes, git context, troubleshooting notes, or the user's end-of-day recap. Trigger for requests like "오늘 뭐 했는지 정리해줘", "퇴근 전 회고 써줘", "daily dev log", "오늘 작업 기록 만들어줘", or "트러블슈팅 기록 남겨줘".
---

# Daily Dev Log

## Overview

Prepare a personal Markdown daily development log owned by the user. The log records work done, troubleshooting, decisions, follow-ups, and lessons without copying sensitive company source text or raw private logs.

## Workflow

### Preflight

Resolve the journal root and target date before evidence collection.

- Use a user-provided absolute journal path when given.
- Otherwise run `scripts/resolve_daily_dev_log_root.py`.
- If no valid root is configured, ask the user for an absolute path or ask them to create `~/.config/daily-dev-log/path`.
- Default the target date to the user's current local date when the user says "today".
- Use exact dates in filenames and prose.

### Required Work Sequence

1. Check whether Codex, Claude, and KB evidence exists for the target date.
   - Run `scripts/detect_sources.py --date YYYY-MM-DD`.
   - Continue gracefully when one source is unavailable.
2. Collect Codex, Claude, and KB session/note candidates.
   - Read `references/codex-sessions.md`, then run `scripts/collect_codex_sessions.py`.
   - Read `references/claude-sessions.md`, then run `scripts/collect_claude_sessions.py`.
   - Read `references/kb-integration.md`, then run read-only KB lookup when `kb-search` or KB scripts are available.
3. Build the first-pass filtering intermediate artifact.
   - Run `scripts/filter_codex_candidates.py` on Codex collection output.
   - Run `scripts/filter_claude_candidates.py` on Claude collection output.
   - Add KB search results as `kb_candidates` using the shape in `references/output-schema.md`.
   - Run `scripts/build_first_pass_artifact.py` to combine the detected sources and filtered candidates.
   - Save or present this intermediate JSON before doing any deep extraction.
4. Perform second-pass extraction for selected or promising candidates.
   - Use `scripts/extract_codex_session.py` and `scripts/extract_claude_session.py` on selected session files.
   - Include KB note paths and excerpts as supporting evidence only.
5. Analyze the extracted evidence.
   - Identify actual work outcomes, troubleshooting, decisions, learnings, and follow-ups.
   - Do not treat raw prompt text as the final truth when tool results or final answers contradict it.
6. Ask the user which candidates deserve detailed exploration or inclusion.
   - Read `references/session-workflow.md` for the candidate question format.
   - Ask: "이 중 오늘 회고에 중요하게 남길 항목은 무엇인가요?"
   - Accept numbers, priorities, omissions, or newly added offline work.
7. Write the daily work log Markdown.
   - Use `assets/daily-work-log.md` as the main template.
   - Use `assets/troubleshooting-record.md` when a selected item deserves a standalone troubleshooting note.
   - Save only after the user approves the selected scope or draft location.
   - Default daily path: `<journal-root>/daily/YYYY/MM/YYYY-MM-DD.md`.
   - Default troubleshooting path: `<journal-root>/troubleshooting/YYYY/YYYY-MM-DD-<slug>.md`.
   - Do not write into company repositories by default.

## Safety Rules

- Store personal experience, reasoning, decisions, lessons, and summarized work evidence.
- Do not copy company source code, internal URLs, credentials, raw logs, customer identifiers, or session JSONL bodies into the journal.
- Prefer aliases for company systems and project names when exact names are not needed.
- Keep raw Codex/Claude session files as external evidence; record session ids and safe summaries instead of copying raw logs.
- If the user says a detail is personal and safe to keep, preserve it; otherwise redact conservatively.

## Resources

- `references/root-resolution.md`: journal root config and initialization guidance.
- `references/session-workflow.md`: candidate presentation, user selection, and deep-dive rules.
- `references/codex-sessions.md`: Codex session locations and JSONL parsing model.
- `references/claude-sessions.md`: Claude session locations and tolerant JSONL parsing model.
- `references/kb-integration.md`: read-only same-day KB lookup.
- `references/output-schema.md`: intermediate JSON shapes and final document conventions.
- `scripts/resolve_daily_dev_log_root.py`: resolve `~/.config/daily-dev-log/path`.
- `scripts/detect_sources.py`: check Codex, Claude, and KB evidence availability for a date.
- `scripts/collect_codex_sessions.py`: collect date-based Codex session candidates.
- `scripts/filter_codex_candidates.py`: produce first-pass filtered Codex candidates.
- `scripts/extract_codex_session.py`: extract a Codex session digest.
- `scripts/collect_claude_sessions.py`: collect date-based Claude session candidates.
- `scripts/filter_claude_candidates.py`: produce first-pass filtered Claude candidates.
- `scripts/extract_claude_session.py`: extract a Claude session digest.
- `scripts/build_first_pass_artifact.py`: combine source availability, source filters, and KB candidates.
- `assets/daily-work-log.md`: daily log Markdown template.
- `assets/troubleshooting-record.md`: standalone troubleshooting record template.
