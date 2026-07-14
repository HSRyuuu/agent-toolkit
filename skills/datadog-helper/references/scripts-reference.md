# Datadog Helper Scripts Reference

Use this file for general Datadog log/APM reads or when combining scripts freely.

## Common Pattern

1. Read `~/.config/datadog-helper/MEMORY.md` first if it exists.
2. Counts and distributions → `count`/`agg` first. Do NOT download raw events and
   count them client-side; the aggregate API is exact and cheaper.
3. Search compactly with a short window; narrow by `service`, `env`, `status`,
   `host`, `trace_id`, `version`, or `index`.
4. Unknown schema → `fields` (never dump `--raw` just to discover keys).
5. Java stack traces → `frames` to rank app frames.
6. Use `--raw` only when the compact output hides a field you truly need.
7. 로그 ↔ APM 연결: 로그에서 `trace_id`를 찾으면 `datadog_apm.py trace`, 스팬에서
   로그가 필요하면 `datadog_logs.py search --trace-id`.
8. Update `MEMORY.md` when an investigation confirms a reusable access pattern.

## Scripts

| Script | Use For | Key Commands |
| --- | --- | --- |
| `datadog_setup.py` | API key/app key setup and checks | `init-keys`, `auth-test`, `logs-test`, `apm-test`, `profiles` |
| `datadog_logs.py` | Datadog Logs API reads | `search`, `errors`, `timeline`, `around`, `count`, `agg`, `timeseries`, `fields`, `frames`, `patterns` |
| `datadog_apm.py` | Datadog APM Spans API reads (read-only) | `search`, `trace`, `count`, `agg`, `latency`, `timeseries`, `services`, `fields` |
| `datadog_common.py` | Shared implementation | import-only; do not call as CLI |

## Command Selection — Logs

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

## Command Selection — APM

| Need | Command |
| --- | --- |
| 스팬 검색, 에러 스팬 보기 | `search` (선택: `--errors-only`) |
| trace_id로 트레이스 전체 스팬 (오프셋 포함) | `trace --trace-id <id>` |
| 스팬 몇 건인지 (에러율 분모/분자) | `count` |
| 리소스/서비스별 건수·측정값 top-N | `agg --by <facet>` (선택: `--agg pc95 --measure @duration`) |
| 느린 API — count + p50/p95/p99 | `latency --by resource_name` |
| 스팬 건수 추이, 스파이크 시점 | `timeseries` (선택: `--by version`) |
| 이 기간에 어떤 서비스가 있나 | `services` |
| 스팬에 어떤 속성이 있나 | `fields` |

APM 주요 facet: `service`, `env`, `resource_name`, `operation_name`, `status`
(ok/error), `version`, `@duration`(ns 단위 measure), `@http.status_code`.

## Examples — Logs

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

## Examples — APM

Slowest resources by p95 (count + p50/p95/p99 per resource):

```bash
python3 "<SKILL_DIR>/scripts/datadog_apm.py" latency --service payments-api --env prod \
  --by resource_name --from now-1h
```

Recent error spans, with HTTP status inline:

```bash
python3 "<SKILL_DIR>/scripts/datadog_apm.py" search --service payments-api --env prod \
  --errors-only --show @http.status_code --from now-30m
```

Whole trace by trace_id (ascending, offsets from the first span):

```bash
python3 "<SKILL_DIR>/scripts/datadog_apm.py" trace --trace-id <trace-id> --from now-1h
```

Error span count and top failing resources:

```bash
python3 "<SKILL_DIR>/scripts/datadog_apm.py" count --service payments-api --errors-only --from now-1h
python3 "<SKILL_DIR>/scripts/datadog_apm.py" agg --service payments-api --errors-only \
  --by resource_name --from now-1h --top 10
```

p95 duration per resource via generic agg (single measure):

```bash
python3 "<SKILL_DIR>/scripts/datadog_apm.py" agg --service payments-api \
  --by resource_name --agg pc95 --measure @duration --from now-1h
```

Span volume over time, split by version after a deploy:

```bash
python3 "<SKILL_DIR>/scripts/datadog_apm.py" timeseries --service payments-api --errors-only \
  --from now-6h --interval 15m --by version
```

Which services are active / what attributes exist on spans:

```bash
python3 "<SKILL_DIR>/scripts/datadog_apm.py" services --env prod --from now-1h
python3 "<SKILL_DIR>/scripts/datadog_apm.py" fields --service payments-api --from now-15m --sample 3
```

## Output

Compact log `search` output is one event per block:

```text
[2026-07-08 14:03:21 KST] status=error service=payments-api env=prod host=ip-...
message...
id=... trace_id=...
```

Compact span output is one span per block:

```text
[2026-07-08 14:03:21 KST] status=error service=payments-api env=prod duration=241.7ms
resource=POST /orders operation=servlet.request type=web
trace_id=... span_id=... parent_id=...
```

`agg` prints `count  facet=value` rows sorted by count. `count` prints one number.
`latency` prints a `count p50 p95 p99` table per group. `timeseries` prints one
`time  count  bar` row per interval bucket. `patterns` prints
`count  normalized-message` rows. When a search is truncated, the output ends
with `(more results available; rerun with --cursor <after>)` — page with
`--cursor`, do not widen `--limit`. The scripts mask credentials in error
messages and never print configured keys.

## Limits

- Default time range: `now-15m`
- Default limit: 20 (search family); `patterns` defaults to 200 samples;
  `apm trace` defaults to 100 spans. Hard limit: 1000; `--allow-wide` needed
  over 500 (profile `default_limit` is also capped at 500).
- `--raw` needs `--limit 5` or less (raw is ~1k tokens/event); over 5 requires
  `--allow-wide`. If you wanted counts or distributions, use `count`/`agg` instead.
- `errors`: `--from`과 `--minutes`는 함께 쓸 수 없다. 둘 다 없으면 최근 30분.
- `agg --top`: 1–100. `fields --sample`: 1–20 (`fields`는 `--limit` 대신 `--sample`).
- `timeseries --interval`: `1m`/`5m`/`1h`처럼 숫자+단위(s/m/h/d).
- `around --window`: 1–120분. `--time`은 ISO8601(타임존 없으면 `--tz` 기준) 또는 epoch 초/밀리초.
- `count`/`agg`/`latency`/`timeseries` are exact server-side aggregates regardless
  of event volume — prefer them over wide raw reads. `patterns` counts only its sample.
- APM은 **인덱싱된 스팬**만 조회한다 (retention filter 통과분, 보존 기간 제한).
  스팬이 비어 보이면 기간·retention 문제를 먼저 의심한다. `@duration`은 ns 단위이며
  출력에서 자동으로 ms/s로 변환된다.
- Confirm with the user before broad `*` or multi-day searches.
