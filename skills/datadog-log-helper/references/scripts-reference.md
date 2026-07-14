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
| `datadog_logs.py` | Datadog Logs API reads | `search`, `errors`, `timeline`, `around`, `count`, `agg`, `timeseries`, `fields`, `frames`, `patterns` |
| `datadog_common.py` | Shared implementation | import-only; do not call as CLI |

## Command Selection

| Need | Command |
| --- | --- |
| "몇 건이야?" — exact hit count | `count` |
| top paths / status code distribution / top loggers | `agg --by <facet>` |
| "언제부터 늘었나" — 시간대별 추이, 스파이크 시점 | `timeseries` (선택: `--by @version`) |
| read actual log lines | `search` / `errors` / `timeline` |
| 특정 시각 전후에 무슨 일이 있었나 (컨텍스트) | `around --time <ts> --window <m>` |
| 어떤 에러 메시지 유형이 많은지 (모양별 클러스터) | `patterns` |
| which attributes exist on this log type | `fields` |
| which app code appears in stack traces | `frames --prefix <package>` |
| compact 출력에 커스텀 필드 한두 개 추가 | `search --show @<facet>` (`--raw` 대신) |

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

Time-bucketed counts — find when errors spiked, or compare versions after a deploy:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" timeseries --service payments-api --status error --from now-6h --interval 15m
python3 "<SKILL_DIR>/scripts/datadog_logs.py" timeseries --service payments-api --status error --from now-6h --by @version
```

Context around a moment (±5 minutes, ascending, center marked):

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" around --service payments-api --time "2026-07-14T10:03:21+09:00" --window 5
```

Cluster error messages by shape (numbers/uuids/hex normalized; samples up to 200 events):

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" patterns --service payments-api --status error --from now-2h
```

Show one custom field inline instead of dumping `--raw`:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" search "service:payments-api status:error" --show @error.kind --show @http.status_code
```

Recent service errors (`--minutes`와 `--from` 중 하나만; 둘 다 없으면 최근 30분):

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" errors --service payments-api --env prod --minutes 30
python3 "<SKILL_DIR>/scripts/datadog_logs.py" errors --service payments-api --env prod --from now-24h
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
`timeseries` prints one `time  count  bar` row per interval bucket. `patterns`
prints `count  normalized-message` rows. When a search is truncated, the output
ends with `(more results available; rerun with --cursor <after>)` — page with
`--cursor`, do not widen `--limit`. The scripts mask credentials in error
messages and never print configured keys.

## Limits

- Default time range: `now-15m`
- Default limit: 20 (search family); `patterns` defaults to 200 samples.
  Hard limit: 1000; `--allow-wide` needed over 500 (profile `default_limit` is
  also capped at 500).
- `--raw` needs `--limit 5` or less (raw is ~1k tokens/event); over 5 requires
  `--allow-wide`. If you wanted counts or distributions, use `count`/`agg` instead.
- `errors`: `--from`과 `--minutes`는 함께 쓸 수 없다. 둘 다 없으면 최근 30분.
- `agg --top`: 1–100. `fields --sample`: 1–20 (`fields`는 `--limit` 대신 `--sample`).
- `timeseries --interval`: `1m`/`5m`/`1h`처럼 숫자+단위(s/m/h/d).
- `around --window`: 1–120분. `--time`은 ISO8601(타임존 없으면 `--tz` 기준) 또는 epoch 초/밀리초.
- `count`/`agg`/`timeseries` are exact server-side aggregates regardless of event
  volume — prefer them over wide raw reads. `patterns` counts only its sample.
- Confirm with the user before broad `*` or multi-day searches.
