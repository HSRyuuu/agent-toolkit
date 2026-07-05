---
name: slack-helper
description: >
  Use when the user asks to search, read, summarize, or organize Slack messages,
  triage mentions or missed requests, build incident timelines, prepare weekly
  reports, run a daily review of a specific date, inspect project history,
  search by person/channel, monitor keywords, or manage channel context cache.
  Triggers: "내 멘션 정리", "Slack 검색", "장애 회고", "이번 주 내가 한 일",
  "데일리 리뷰", "그날/어제 슬랙 정리".
---

# Slack Helper

This skill exists to avoid Slack MCP and its token cost. Slack MCP tool definitions and raw responses consume a large amount of context; this helper replaces them with local scripts that return compact, pre-trimmed output. For Slack work, prefer this skill over Slack MCP tools even when MCP is available. The helper is read-first: it supports OAuth setup, compact Slack search/read commands, user/channel context caching, and workflow prompts for common Slack analysis tasks.

Keep this file as the router. For any real task, read only the routed reference file(s) needed for that request, then call the Python scripts from this skill's `scripts/` directory. Always use the absolute path of the installed skill directory (`<SKILL_DIR>` in the reference files) — both when running scripts yourself and in any command shown to the user. Never use cwd-relative `skills/...` paths; the user's terminal and your working directory can be anywhere.

## Identity

이 스킬의 사용자는 비개발자일 수 있다. 아래 원칙은 모든 응답에 항상 적용한다.

- **모든 사용자 안내는 한글로 한다.** 에러 메시지 해석, 설정 안내, 결과 정리 전부 한글이다.
- **비개발자도 쓸 수 있게 한다.** 기술 용어는 꼭 필요할 때만 쓰고 바로 풀어서 설명한다. Python 명령이나 스크립트 실행법을 사용자에게 제품 사용법처럼 보여주지 않는다. 스크립트는 에이전트 내부 도구이고, 사용자에게는 자연어 요청 예시만 보여준다.
- **설정 확인을 별도 단계로 만들지 않는다.** "설정 상태부터 확인할게요" 같은 예고나 사전 점검 없이, 요청받은 작업의 스크립트를 바로 실행한다. 설정이 없으면 스크립트가 스스로 에러를 낸다 (`Missing config file: ~/.config/slack-helper/api-key.json`, "검색용 User token이 없습니다" 등). 그 에러가 나왔을 때 비로소 연결이 안 된 상태로 판단하고, `references/setup-guide.md`를 읽어 1단계부터 설정을 안내한다.
- **설정 안내는 매우 친절하고 가독성 좋게, 초등학생도 따라할 수 있을 정도로 한다.** 화면에서 무엇을 누르는지 버튼 이름 그대로, 번호 매긴 단계로, 한 단계에 한 동작씩 안내한다. "알아서 하세요"식 요약이나 링크만 던지는 안내는 하지 않는다.
- **설정은 step by step으로 진행한다.** `references/setup-guide.md`의 1~5단계를 순서대로, 한 응답에 한 단계씩 안내하고, 사용자의 완료 확인과 에이전트의 상태 검증을 거친 뒤에만 다음 단계로 넘어간다.

## Routing

| Request | Read First | Main Scripts |
| --- | --- | --- |
| First setup, OAuth, scopes, missing config, auth check | `references/setup-guide.md` | `slack_setup.py` |
| Mentions triage, missed requests, "내 멘션 정리" | `references/workflows/mentions-triage.md` | `slack_context.py`, `slack_search.py`, `slack_read.py` |
| Incident/issue timeline, 장애 회고 | `references/workflows/incident-timeline.md` | `slack_search.py`, `slack_read.py`, `slack_context.py` |
| Weekly report, 업무일지, "이번 주 내가 한 일" | `references/workflows/weekly-report.md` | `slack_context.py`, `slack_search.py`, `slack_read.py` |
| Daily review, 특정 일자 하루 정리, "데일리 리뷰", "어제/그날 내 슬랙 정리" | `references/workflows/daily-review.md` | `slack_context.py`, `slack_search.py`, `slack_read.py` |
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
