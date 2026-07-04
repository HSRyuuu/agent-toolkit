---
name: verify-secrets
description: Use before any git commit, push, pull request, or release when changed files may contain company identifiers, credentials, tokens, API keys, private values, or generated few-shot examples.
---

# Verify Secrets

## Rule

Run this skill before every commit. Do not commit until the scan passes or the user explicitly confirms each remaining finding is intentional.

This project is allowed to mention the target company identifiers only inside this local verify skill. Those identifiers must not appear under the plugin skill root at `skills/`.

## What to Catch

Block these categories in staged, modified, untracked, generated, and documentation files:

- Company identifiers: `tripbtoz`, `tbz`
- API keys and tokens: OpenAI, Anthropic, GitHub, Slack, AWS, Google, NPM, generic bearer tokens
- Credential assignments: password, passwd, secret, token, api_key, private_key, client_secret, access_key
- Private key material: PEM headers, SSH keys, certificates
- Environment values: committed `.env*` files, connection strings, database URLs, webhook URLs
- Few-shot examples that accidentally contain real company names or realistic secret-looking values

## Workflow

1. Check the repo state.

```bash
git status --short
git diff --name-only
git diff --cached --name-only
```

2. Scan company identifiers everywhere except this local skill and git internals.

```bash
rg -n -i --hidden --glob '!.git/**' --glob '!.claude/skills/verify-secrets/**' --glob '!.codex/skills/verify-secrets/**' '\b(tripbtoz|tbz)\b|tripbtoz'
```

3. Scan the plugin skill root with zero exceptions. Any company identifier under `skills/` is a hard failure.

```bash
rg -n -i '\b(tripbtoz|tbz)\b|tripbtoz' skills
```

4. Scan likely secret patterns.

```bash
rg -n --hidden --glob '!.git/**' --glob '!.claude/skills/verify-secrets/**' --glob '!.codex/skills/verify-secrets/**' '(AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,}|npm_[A-Za-z0-9]{20,}|-----BEGIN (RSA |EC |OPENSSH |DSA |)?PRIVATE KEY-----|mongodb(\+srv)?://|postgres(ql)?://|mysql://|redis://|Bearer [A-Za-z0-9._~+/=-]{20,})'
```

5. Scan credential-looking assignments.

```bash
rg -n -i --hidden --glob '!.git/**' --glob '!.claude/skills/verify-secrets/**' --glob '!.codex/skills/verify-secrets/**' '(^|[^A-Za-z0-9_])(password|passwd|secret|token|api[_-]?key|private[_-]?key|client[_-]?secret|access[_-]?key|webhook)([^A-Za-z0-9_]|$).{0,40}[:=][[:space:]]*[^[:space:]]{8,}'
```

6. Inspect staged content before committing.

```bash
git diff --cached --stat
git diff --cached --check
git diff --cached
```

## PASS Criteria

- No company identifier appears outside `.claude/skills/verify-secrets/` and `.codex/skills/verify-secrets/`.
- No company identifier appears anywhere under `skills/`.
- No real credential, token, key, private URL, or realistic fake secret remains in the files to be committed.
- Staged diff has been inspected after automated scans.

## Exceptions

These may be marked as false positives after inspection:

- Placeholder values such as `<REDACTED>`, `<TOKEN>`, `YOUR_CLIENT_SECRET`, `example.com`, or `example-project`
- Local-only sample URLs such as `redis://localhost`, `postgresql://...@localhost/...`, or `mysql://localhost/...`
- Obviously abbreviated tokens containing ellipses, such as `Bearer eyJ...`
- Test-only values such as `password123` or `encodedPassword` when they appear in test fixtures or teaching examples

Do not exempt company identifiers under `skills/`.

## FAIL Criteria

- Any hit under `skills/` for the company identifiers.
- Any secret-like value that could plausibly work outside a toy example.
- Any `.env`, credentials file, key file, or generated few-shot file that contains private values.
- Any finding the agent cannot confidently classify as a false positive.

## Few-Shot Checks

Treat these as failures:

```text
company_name: "tripbtoz"
tenant: "tbz"
OPENAI_API_KEY=sk-real-looking-value
Authorization: Bearer real-looking-token
client_secret = "long-real-looking-secret"
```

Safe replacements:

```text
company_name: "<COMPANY>"
tenant: "<TENANT>"
OPENAI_API_KEY="<REDACTED>"
Authorization: Bearer <REDACTED>
client_secret = "<REDACTED>"
```

## Reporting

Report findings with file path, line number, category, and recommended fix. If nothing is found, explicitly say:

```text
verify-secrets passed: no company identifiers or secret-looking values found in commit scope.
```

Never silently ignore a hit. If it is intentional, state why it is exempt and ask the user before committing.
