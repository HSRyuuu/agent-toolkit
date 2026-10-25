# Codesight Install

Use this only when the project owner asks to install, persist, or wire Codesight into a project. If they only want a one-time map refresh, prefer `npx -y codesight --wiki` and avoid changing project files.

Source checked: https://github.com/Houseofmvps/codesight

## Requirements

- Node.js 18 or newer.
- Run commands from the target project root unless scanning a specific path.
- Codesight needs no API keys and no config for the default scan.

## One-Time Use

```bash
npx -y codesight
npx -y codesight --wiki
```

Expected outputs include `.codesight/CODESIGHT.md` and, with `--wiki`, `.codesight/wiki/index.md`.

## Persisted CLI Options

Choose one. Ask before adding dependencies or global tools.

```bash
# Project dev dependency
npm install --save-dev codesight
npx codesight --wiki

# Global install, useful for faster MCP startup
npm install -g codesight
codesight --wiki
```

For pnpm or yarn projects, use the matching package manager if the repo already standardizes on it.

## Common Commands

```bash
npx -y codesight --wiki                 # Generate .codesight/wiki/
npx -y codesight --init                 # Generate AI tool instruction files
npx -y codesight --open                 # Open interactive HTML report
npx -y codesight --blast src/lib/db.ts  # Show blast radius for a file
npx -y codesight --profile codex        # Generate Codex-oriented config
npx -y codesight --watch --wiki         # Keep wiki refreshed while coding
npx -y codesight --hook                 # Install git hook that refreshes context
```

Use `--init`, `--profile`, `--watch`, or `--hook` only after user confirmation because they may create or alter project files or long-running behavior.

## Codex MCP

For Codex CLI, Codesight documents this MCP shape:

```toml
[mcp_servers.codesight]
command = "npx"
args = ["codesight", "--mcp"]
startup_timeout_sec = 60
```

If startup is slow on first `npx` resolution, install globally and use:

```toml
[mcp_servers.codesight]
command = "codesight"
args = ["--mcp"]
startup_timeout_sec = 60
```

## CI Refresh

Use CI only when the team wants `.codesight/` artifacts refreshed or uploaded consistently.

```yaml
name: codesight
on: [push]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm install -g codesight && codesight --wiki
      - uses: actions/upload-artifact@v4
        with:
          name: codesight
          path: .codesight/
```

## Safety Checks

- Do not overwrite existing `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, or `codex.md` with `--init` or `--profile` without reviewing diffs.
- Do not commit `.codesight/` until the project decides generated context belongs in version control.
- After generation, run the local context map generator and validator so `docs/SOURCE_MAP.md` points agents at the chosen Codesight entrypoints.
