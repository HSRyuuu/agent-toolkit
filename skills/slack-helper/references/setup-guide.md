# Slack Helper Setup Guide

Use this file when config is missing, OAuth is incomplete, scopes are unclear, or the user asks how to set up Slack search.

## First Response

Give the user the Slack App Management link, app creation steps, where to find `Client ID` and `Client Secret`, and the exact `init-oauth` terminal command in one response. Do not stop with "앱을 다 만들었으면 알려주세요" or "브라우저를 대신 열까요?".

```text
https://api.slack.com/apps
Create New App > From scratch
App Name: slack-helper-local
Workspace: 읽고 싶은 Slack workspace
```

Run this in a real terminal:

```bash
python3 "skills/slack-helper/scripts/slack_setup.py" init-oauth
```

`Client Secret` must be typed into the interactive prompt only. Do not accept it in chat, command arguments, logs, examples, or files under this repo.

## OAuth App Steps

1. Open `OAuth & Permissions`.
2. Add Redirect URL: `http://localhost:8765/callback`
3. Add Bot Token Scopes:
   - `team:read`
   - `users:read`
   - `channels:read`
   - `channels:history`
4. Add User Token Scopes:
   - `search:read`

`search.messages` needs the user token scope `search:read`. Bot scopes alone are not enough for search.

## Local OAuth Flow

```bash
python3 "skills/slack-helper/scripts/slack_setup.py" oauth-start --open
python3 "skills/slack-helper/scripts/slack_setup.py" oauth-finish --code CODE_FROM_REDIRECT --workspace default
python3 "skills/slack-helper/scripts/slack_setup.py" read-sample --workspace default
```

The localhost callback page does not need to load. If the browser address contains `code=...`, copy only that code value.

## Save My Slack Identity

After connection works, do not run a random keyword search. Ask for the user's Slack display name, `@handle`, or `U...` member ID, then store and resolve it:

```bash
python3 "skills/slack-helper/scripts/slack_setup.py" set-me --slack-user "your-slack-name" --workspace default
python3 "skills/slack-helper/scripts/slack_setup.py" resolve-me --workspace default
```

This writes identity to local config and mirrors `me` into `~/.config/slack-helper/context.json`.

## Optional Context Cache

Use context cache to avoid broad channel discovery every time:

```bash
python3 "skills/slack-helper/scripts/slack_context.py" draft-summaries --workspace default
python3 "skills/slack-helper/scripts/slack_context.py" add-channel --alias backend --id C0123456789 --name backend --summary "backend team discussions"
python3 "skills/slack-helper/scripts/slack_context.py" show
```

`draft-summaries` prints summary drafts only. Save a summary only after the user confirms or edits it.

## Completion Message

Do not show Python commands as normal usage after setup. Show natural-language examples instead:

```text
설정이 끝났어요. 이제 이런 식으로 물어보시면 제가 Slack에서 찾아서 정리해드릴게요.

- 내 최근 멘션 뭐 있어?
- 이번 주에 나를 멘션한 메시지 정리해줘
- 어제 장애 관련해서 나온 이야기 찾아줘
- 특정 채널에서 온보딩 관련 논의 요약해줘
- OO 프로젝트 관련 최근 결정사항 찾아줘
```

## Avoid

- Running arbitrary test searches such as `배포`.
- Asking for a search keyword before identity is saved.
- Printing tokens, client secrets, or `.env` values.
- Presenting `python3 ...` commands as the user-facing product flow after setup.
