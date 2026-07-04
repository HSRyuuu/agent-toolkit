---
name: slack-helper
description: Use when accessing Slack through the Slack Web API with a local curl-based helper instead of Slack MCP, especially for OAuth token setup, channel/user/team reads, and local Slack API troubleshooting.
---

# Slack Helper

## Purpose

Use the bundled script when Slack data should be read through Slack Web API calls instead of an MCP connector. The script keeps credentials in `~/.config/slack-helper`, performs OAuth token exchange, and wraps `curl` for deterministic local calls.

## Config Files

Create `~/.config/slack-helper/oauth-app.json` before OAuth:

```json
{
  "client_id": "123456789.123456789",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uri": "https://your-registered-redirect.example/slack/callback",
  "scopes": ["team:read", "users:read", "channels:read"]
}
```

`redirect_uri` must match a Redirect URL configured in Slack App Management under OAuth & Permissions. Slack redirects there with `?code=...`; copying that `code` is enough for the manual OAuth flow.

The script writes tokens to `~/.config/slack-helper/api-key.json` and reads optional channel aliases from `~/.config/slack-helper/channel-info.json`:

```json
{
  "channels": {
    "general": "C0123456789"
  }
}
```

## OAuth Flow

Run from the repository root:

```bash
python3 skills/slack-helper/scripts/slack_api.py oauth-start --open
```

The browser opens Slack's approval page. After approval, copy the `code` query parameter from the redirected URL:

```bash
python3 skills/slack-helper/scripts/slack_api.py oauth-finish --code CODE_FROM_REDIRECT --workspace default
```

Then verify by reading one Slack datum:

```bash
python3 skills/slack-helper/scripts/slack_api.py read-sample --workspace default
```

`read-sample` calls `team.info` first, then falls back to `auth.test` if the token lacks `team:read`.

## Common Reads

```bash
python3 skills/slack-helper/scripts/slack_api.py auth-test
python3 skills/slack-helper/scripts/slack_api.py team-info
python3 skills/slack-helper/scripts/slack_api.py users --limit 20
python3 skills/slack-helper/scripts/slack_api.py channels --limit 20
python3 skills/slack-helper/scripts/slack_api.py channel-history --channel general --limit 10
```

Use channel IDs directly, or aliases from `channel-info.json`.

## Safety Rules

- Never print or paste Slack tokens into chat.
- Keep `api-key.json` and `oauth-app.json` outside the repo; the script sets file mode `600` when it writes token files.
- In Codex, opening a browser or calling Slack may require user approval because it uses GUI/network access.
- For writes such as `chat.postMessage`, add a separate explicit command later; this helper is intentionally read-first.
