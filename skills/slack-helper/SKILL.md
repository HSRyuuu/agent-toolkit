---
name: slack-helper
description: Use when Slack MCP 대신 Slack Web API와 로컬 curl helper로 Slack 메시지를 검색·읽기·정리해야 할 때. Slack App/OAuth 설정, 멘션 정리, 놓친 요청, 장애 회고, 프로젝트 히스토리, 사람/채널 중심 검색, 키워드 모니터링, 주간보고 보조, context.json 채널 캐시 관리에 사용한다.
---

# Slack Helper

Use this skill when Slack MCP is unavailable or when a local curl-based Slack Web API helper is preferred. The helper is read-first: it supports OAuth setup, compact Slack search/read commands, user/channel context caching, and workflow prompts for common Slack analysis tasks.

Keep this file as the router. For any real task, read only the routed reference file(s) needed for that request, then call the Python scripts from `skills/slack-helper/scripts/`.

## Routing

| Request | Read First | Main Scripts |
| --- | --- | --- |
| First setup, OAuth, scopes, missing config, auth check | `references/setup-guide.md` | `slack_setup.py` |
| Mentions triage, missed requests, "내 멘션 정리" | `references/workflows/mentions-triage.md` | `slack_context.py`, `slack_search.py`, `slack_read.py` |
| Incident/issue timeline, 장애 회고 | `references/workflows/incident-timeline.md` | `slack_search.py`, `slack_read.py`, `slack_context.py` |
| Weekly report, 업무일지, "이번 주 내가 한 일" | `references/workflows/weekly-report.md` | `slack_context.py`, `slack_search.py`, `slack_read.py` |
| Project history, person/channel search, keyword monitoring, other combinations | `references/scripts-reference.md` | compose scripts as needed |
| Context cache setup or channel summary cache | `references/scripts-reference.md` | `slack_context.py` |

## Scripts

- `slack_setup.py`: `setup-guide`, `init-oauth`, `oauth-start`, `oauth-finish`, `auth-test`, `team-info`, `read-sample`, `set-me`, `resolve-me`
- `slack_context.py`: `show`, `add-channel`, `remove-channel`, `draft-summaries`
- `slack_read.py`: `users`, `channels`, `channel-history`, `thread`
- `slack_search.py`: `search`
- `slack_common.py`: import-only shared implementation

## Rules

- Never ask the user to paste Slack tokens or `Client Secret` into chat. `Client Secret` is accepted only through the interactive `slack_setup.py init-oauth` prompt.
- Config lives outside the repo at `~/.config/slack-helper`; files should be `600` and the directory `700`.
- Prefer `context.json` before broad channel listing. Store only user/channel identifiers and one-line summaries, not message bodies or tokens.
- Prefer compact output. Use `--raw` only when a workflow truly needs full Slack API JSON.
- For broad work, search compactly first, then read only selected threads with `slack_read.py thread`.
- Slack search runs with the approved user token scope (`search:read`). Direct channel history/thread reads require bot access to that channel.
