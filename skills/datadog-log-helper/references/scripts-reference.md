# Datadog Log Helper Scripts Reference

Use this file for general Datadog log searches or when combining scripts freely.

## Common Pattern

1. Read `~/.config/datadog-log-helper/MEMORY.md` first if it exists.
2. Counts and distributions → `count`/`agg` first. Do NOT download raw events and
   count them client-side; the aggregate API is exact and cheaper.
3. Search compactly with a short window; narrow by `service`, `env`, `status`,
   `host`, `trace_id`, `version`, or `index`.
4. Unknown log schema → `fields` (never dump `--raw` just to discover keys).
5. Java stack traces → `frames` to rank app frames.
6. Use `--raw` only when the compact output hides a field you truly need.
7. Update `MEMORY.md` when an investigation confirms a reusable access pattern.

## Scripts

| Script | Use For | Key Commands |
| --- | --- | --- |
| `datadog_setup.py` | API key/app key setup and checks | `init-keys`, `auth-test`, `logs-test`, `profiles` |
| `datadog_logs.py` | Datadog Logs API reads | `search`, `errors`, `timeline`, `count`, `agg`, `fields`, `frames` |
| `datadog_common.py` | Shared implementation | import-only; do not call as CLI |

## Command Selection

| Need | Command |
| --- | --- |
| "몇 건이야?" — exact hit count | `count` |
| top paths / status code distribution / top loggers | `agg --by <facet>` |
| read actual log lines | `search` / `errors` / `timeline` |
| which attributes exist on this log type | `fields` |
| which app code appears in stack traces | `frames --prefix <package>` |

## Examples

Exact count (server-side; no sampling bias):

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" count --service prd-some-service '"ERROR 1 ---"' --from now-24h
```

Top request paths and status codes among HTTP errors:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" agg --service prd-some-service "@status:>=400" \
  --by @request_uri --by @status --from now-24h --top 10
```

Discover attribute schema (sensitive keys like authorization/cookie are redacted):

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" fields --service prd-some-service --from now-15m --sample 3
```

Rank app stack frames in error logs:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" frames --service prd-some-service '"ERROR 1 ---"' \
  --prefix com.example --from now-24h --limit 200
```

Recent service errors:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" errors --service payments-api --env prod --minutes 30
```

General query / timeline / index:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" search "service:payments-api env:prod @http.status_code:500" --from now-30m --limit 50
python3 "<SKILL_DIR>/scripts/datadog_logs.py" timeline "service:payments-api env:prod status:error" --from now-2h --limit 100
python3 "<SKILL_DIR>/scripts/datadog_logs.py" search "service:payments-api env:prod" --index main --limit 50
```

## Output

Compact `search` output is one log event per block:

```text
[2026-07-08 14:03:21 KST] status=error service=payments-api env=prod host=ip-...
message...
id=... trace_id=...
```

`agg` prints `count  facet=value` rows sorted by count. `count` prints one number.
The scripts mask credentials in error messages and never print configured keys.

## Limits

- Default time range: `now-15m`
- Default limit: 20 (search family). Hard limit: 1000; `--allow-wide` needed over 500.
- `--raw` needs `--limit 5` or less (raw is ~1k tokens/event); over 5 requires
  `--allow-wide`. If you wanted counts or distributions, use `count`/`agg` instead.
- `agg --top`: 1–100. `fields --sample`: 1–20.
- `count`/`agg` are exact regardless of event volume — prefer them over wide raw reads.
- Confirm with the user before broad `*` or multi-day searches.
