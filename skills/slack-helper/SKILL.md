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

Keep this file as the router. For any real task, first read `~/.config/slack-helper/MEMORY.md` if it exists and honor the user's recorded preferences; then read only the routed reference file(s) needed for that request, and call the Python scripts from this skill's `scripts/` directory. Always use the absolute path of the installed skill directory (`<SKILL_DIR>` in the reference files) — both when running scripts yourself and in any command shown to the user. Never use cwd-relative `skills/...` paths; the user's terminal and your working directory can be anywhere.

## Identity

이 스킬의 사용자는 비개발자일 수 있다. 아래 원칙은 모든 응답에 항상 적용한다.

- **모든 사용자 안내는 한글로 한다.** 에러 메시지 해석, 설정 안내, 결과 정리 전부 한글이다.
- **비개발자도 쓸 수 있게 한다.** 기술 용어는 꼭 필요할 때만 쓰고 바로 풀어서 설명한다. Python 명령이나 스크립트 실행법을 사용자에게 제품 사용법처럼 보여주지 않는다. 스크립트는 에이전트 내부 도구이고, 사용자에게는 자연어 요청 예시만 보여준다.
- **설정 확인을 별도 단계로 만들지 않는다.** "설정 상태부터 확인할게요" 같은 예고나 사전 점검 없이, 요청받은 작업의 스크립트를 바로 실행한다. 설정이 없으면 스크립트가 스스로 에러를 낸다 (`Missing config file: ~/.config/slack-helper/config.json`, "검색용 User token이 없습니다" 등). 그 에러가 나왔을 때 비로소 연결이 안 된 상태로 판단하고, `references/setup-guide.md`를 읽어 1단계부터 설정을 안내한다.
- **설정 안내는 매우 친절하고 가독성 좋게, 초등학생도 따라할 수 있을 정도로 한다.** 화면에서 무엇을 누르는지 버튼 이름 그대로, 번호 매긴 단계로, 한 단계에 한 동작씩 안내한다. "알아서 하세요"식 요약이나 링크만 던지는 안내는 하지 않는다.
- **설정은 step by step으로 진행한다.** `references/setup-guide.md`의 1~5단계를 순서대로, 한 응답에 한 단계씩 안내하고, 사용자의 완료 확인과 에이전트의 상태 검증을 거친 뒤에만 다음 단계로 넘어간다.

## Routing

| Request | Read First | Main Scripts |
| --- | --- | --- |
| First setup, OAuth, scopes, missing config, auth check | `references/setup-guide.md` | `slack_setup.py` |
| Mentions triage("내 멘션 정리"), incident timeline(장애 회고), weekly report("이번 주 내가 한 일"), daily review("데일리 리뷰", "어제/그날 내 슬랙 정리") | `references/workflows.md` | `slack_search.py`, `slack_read.py` |
| 집계·통계·대량 파싱 등 기본 스크립트 범위를 넘는 분석 ("전부 세줘", "종류별로 묶어줘") | `references/adhoc-scripts.md` | scratchpad 일회용 스크립트 → `slack_search.py`, `slack_read.py` |
| Project history, person/channel search, keyword monitoring, other combinations | `references/scripts-reference.md` | compose scripts as needed |

## Local Files

`~/.config/slack-helper/`에는 파일이 정확히 두 개만 있다.

- `config.json` — 앱 자격증명(`app`), 워크스페이스 토큰(`workspaces`), 내 identity(`workspaces.<name>.user_identity`)의 **단일 저장소**. 스크립트만 읽고 쓴다. identity를 다른 곳에 복사하지 않는다.
- `MEMORY.md` — 에이전트가 Read/Edit로 직접 관리하는 자유형 markdown. 워크플로우 선호와 채널 컨텍스트(별칭·ID·한 줄 요약)를 담는다.

구버전 3분할 config(`oauth-app.json`/`api-key.json`/`context.json`)가 남아 있으면 스크립트가 처음 실행될 때 자동으로 `config.json`+`MEMORY.md`로 합치고 옛 파일을 지운다.

## Scripts

- `slack_setup.py`: `setup-guide`, `init-oauth`, `oauth-start`, `oauth-finish`, `auth-test`, `team-info`, `read-sample`, `set-me`, `resolve-me`
- `slack_read.py`: `users`, `channels`, `channel-history`, `thread`
- `slack_search.py`: `search`
- `slack_common.py`: import-only shared implementation

## Rules

- **이 스킬은 조회 전용이다.** 메시지 전송·수정·삭제·리액션 기능을 제공하지 않으며, OAuth scope도 읽기 권한만 요청하므로 API 차원에서 불가능하다. 사용자가 전송류 작업을 요청하면 이 스킬의 범위 밖임을 안내한다.
- Never ask the user to paste Slack tokens or `Client Secret` into chat. `Client Secret` is accepted only through the interactive `slack_setup.py init-oauth` prompt.
- Config lives outside the repo at `~/.config/slack-helper`; files should be `600` and the directory `700`.
- 채널 작업 전에 `MEMORY.md`의 채널 목록을 먼저 참고한다. 거기 없으면 `slack_read.py channels`로 찾고, 자주 쓸 채널이면 MEMORY에 기록을 제안한다.
- Prefer compact output. Use `--raw` only when a workflow truly needs full Slack API JSON.
- For broad work, search compactly first, then read only selected threads with `slack_read.py thread`. 결과가 100건을 넘을 것 같으면 `--page` 수동 반복 대신 `slack_search.py search ... --limit N`을 쓴다.
- 집계·통계처럼 기본 스크립트 범위를 넘는 분석은 `references/adhoc-scripts.md`의 임시 스크립트 작성 규칙을 먼저 읽고, scratchpad에 일회용 스크립트를 만들어 처리한다.
- Slack search runs with the approved user token scope (`search:read`). Direct channel history/thread reads require bot access to that channel.

## Memory

- `~/.config/slack-helper/MEMORY.md`는 사용자별 **작업 선호·규칙과 채널 컨텍스트**를 담는 자유형 markdown이다. config 디렉토리(레포 밖)에 두며, 파일은 `600`으로 만든다. 스크립트가 파싱하지 않으므로 에이전트가 Read/Edit로 직접 관리한다.
- 기록 경로는 세 가지다.
  - **제안형**: 대화에서 기억해둘 만한 것(반복될 선호, 교정 피드백, 자주 찾는 채널·사람 등)이 보이면 저장할 한 줄을 보여주며 "이거 기억해둘까요?"라고 먼저 물어본다. 동의할 때만 기록하고, 같은 내용을 두 번 제안하지 않는다.
  - **명령형**: 사용자가 "기억해둬", "기억해", "저장해둬"라고 하면 묻지 않고 바로 기록한 뒤, 기록한 문장을 그대로 보여준다.
  - **탐지형**: 작업 요청 안에 **사용자가 알려주지 않으면 모르는 사실**(예: "X채널은 우리 팀 배포 알림 채널이야" 같은 채널·사람·조직 맥락)이 들어 있으면, 먼저 요청받은 작업을 끝낸 뒤 "이 내용을 MEMORY에 저장할까요? — <저장할 한 줄>"이라고 물어본다. 동의하면 기록한다. 채널이면 `slack_read.py channels`로 ID를 찾아 별칭·요약과 함께 `## 채널`에 적는다.
- 담는 것은 **워크플로우 선호·규칙과 채널/사람 식별자 + 한 줄 요약**까지다. token·secret·`Client Secret`·메시지 본문은 절대 기록하지 않는다.
- 사용자가 명시적으로 선호를 바꾸거나 취소하면 해당 줄을 수정·삭제한다.

```markdown
# slack-helper memory

## 워크플로우 선호
- (예) 멘션 정리는 주요 채널만 대상으로 한다

## 검색 습관
- (예) "이번 주" 기준은 월요일 시작

## 채널
- (예) backend — C0123456789 — 백엔드 팀 논의
```
