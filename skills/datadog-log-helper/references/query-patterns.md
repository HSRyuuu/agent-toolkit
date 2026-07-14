# Datadog Log Query Patterns

Use this file when composing Datadog log search queries.

## Core Filters

| Need | Query Fragment |
| --- | --- |
| Service | `service:<service-name>` |
| Environment | `env:<env-name>` |
| Error logs (log level) | `status:error` |
| Log pipeline / source | `source:<source-name>` (예: `source:console-logs`) |
| HTTP 5xx | `@http.status_code:[500 TO 599]` |
| HTTP status | `@http.status_code:500` |
| Host | `host:<host-name>` |
| Trace ID | `@trace_id:<trace-id>` or `trace_id:<trace-id>` depending on parsing |
| Version | `@version:<version>` |
| Kubernetes namespace | `kube_namespace:<namespace>` or `@kube.namespace:<namespace>` |

## Reserved Attributes vs Custom Facets

- `status:` (no `@`) is the **log level** (error/warn/info) — a reserved attribute.
- `@status:` is a **custom facet**; on access logs it is often the HTTP status code.
  `@status:>=400` and `status:error` match completely different things.
- Custom fields always need `@`: `@request_uri:/play/element`, `@processing_time:>1000`.
- Escape `/` inside facet values when needed: `@request_uri:\/play\/element`.

## Negation

- Prefix `-` excludes a term: `"ERROR 1 ---" -NonUniqueResultException`
- `NOT` also works: `"ERROR 1 ---" AND NOT intValue`
- Verify with a `count` comparison when unsure whether negation applied.

## Text Search Heuristics

- Quoted phrases match exact text: `"connection refused"`, `"Caused by"`.
- Framework log-line patterns make good level filters when `status:` is not parsed,
  e.g. Spring Boot console logs: `"ERROR 1 ---"`, `"WARN 1 ---"`.
- Java stack traces: search `"at com.<company>"` or `"Caused by"`, then use the
  `frames` command to rank app frames.
- Services often split logs by `source:` (access logs vs server stdout vs browser
  logs). If error-level results look empty, check other sources before concluding
  "no errors" — run `fields` on a sample to see which schema you are looking at.

## Search Heuristics

- Start with `service:<name> env:<env> status:error`.
- If results are noisy, add one of: `@http.status_code`, `@error.kind`,
  `@trace_id`, `host`, `@version`, an `index`, or a `source:`.
- Counting or ranking anything → `count`/`agg`, not a wide `search --raw`.
- "언제부터/얼마나 늘었나" → `timeseries` (스파이크 시점을 한 번에). 배포 비교는
  `timeseries --by @version`.
- "어떤 에러가 많은지" 메시지 유형 분포 → `patterns` (facet이 없어도 동작).
- 특정 필드 한두 개만 더 필요하면 `search --show @facet` (`--raw` 금지 사유가 됨).
- For deploy checks, include version/build/deployment tags when known.
- For incident timelines, sort ascending with `timeline`; 특정 시각 전후는 `around`.

## Memory Candidates

When an investigation confirms a pattern, save only the access hint:

```markdown
- checkout-api — service:checkout-api env:prod index:main — 결제 체크아웃 운영 로그
- checkout 5xx — service:checkout-api env:prod @http.status_code:[500 TO 599]
- svc 서버 에러 — service:prd-some-service "ERROR 1 ---" (source:console-logs)
```

Do not save full log messages or private customer/request data.
