---
name: datadog-helper
description: >
  Use when the user asks to set up Datadog API keys, search Datadog logs,
  count or aggregate logs (top paths, status distribution, 자주 발생하는 에러),
  inspect service errors or stack traces, build incident timelines, investigate
  deploy regressions, query APM traces or spans, check API latency (p95/p99,
  느린 API), inspect a trace by trace_id, remember frequently used Datadog
  queries, or manage local Datadog access context. Triggers: "Datadog 로그",
  "datadog api", "서비스 에러 로그", "로그 집계", "몇 건이야", "장애 타임라인",
  "배포 후 에러", "APM", "트레이스", "trace_id", "스팬", "느린 API", "레이턴시",
  and in Datadog context: "기억해", "기억해줘", "memory", "MEMORY".
---

# Datadog Helper

This skill explores Datadog logs and APM spans through the Datadog API, avoiding
MCP and returning compact, pre-trimmed output. It is read-only toward Datadog:
use it for local API key setup, log searches, error investigation, timeline
reconstruction, trace/latency inspection, and maintaining the user's Datadog
access memory.

Keep this file as the router. For any real task, first read
`~/.config/datadog-helper/MEMORY.md` if it exists and honor saved service,
environment, index, and query preferences. Then read only the routed reference
file(s), and call the Python scripts from this skill's `scripts/` directory.
Always use the absolute installed skill directory when running scripts or showing
commands to the user.

## Identity

- 모든 사용자 안내는 한글로 한다.
- Datadog API key, application key, `.env` 값, config 내용을 채팅에 붙여넣으라고 요구하지 않는다.
- 설정 확인을 별도 사전 단계로 만들지 않는다. 요청받은 작업의 스크립트를 바로 실행하고, 설정 파일/권한 오류가 나왔을 때 `references/setup-guide.md`를 읽어 안내한다.
- 설정 안내는 한 응답에 한 단계만 진행한다. 사용자의 완료 확인과 에이전트 검증 뒤 다음 단계로 넘어간다.

## Routing

| Request | Read First | Main Scripts |
| --- | --- | --- |
| First setup, missing config, API key/app key, auth or permission error | `references/setup-guide.md` | `datadog_setup.py` |
| General log search, service/env/status filters, raw script combinations | `references/scripts-reference.md`, `references/query-patterns.md` | `datadog_logs.py` |
| Counts, distributions, top-N (경로/코드/로거별 몇 건) | `references/scripts-reference.md` | `datadog_logs.py count`, `agg` |
| 시간대별 추이, 스파이크 시점, 배포 전후 비교 | `references/scripts-reference.md` | `datadog_logs.py timeseries` |
| 특정 시각/이벤트 전후 컨텍스트 (그 직전에 무슨 일이) | `references/scripts-reference.md` | `datadog_logs.py around` |
| 에러 메시지 유형 분포 (어떤 에러가 많은지) | `references/scripts-reference.md` | `datadog_logs.py patterns` |
| Unknown log schema, which facets exist | `references/scripts-reference.md` | `datadog_logs.py fields` |
| Stack trace analysis, which app code throws | `references/scripts-reference.md` | `datadog_logs.py frames` |
| APM 스팬 검색, 에러 스팬, trace_id로 트레이스 보기 | `references/scripts-reference.md`, `references/query-patterns.md` | `datadog_apm.py search`, `trace` |
| 느린 API, latency p95/p99, 리소스별 응답시간 | `references/scripts-reference.md` | `datadog_apm.py latency`, `agg` |
| APM 서비스 목록, 스팬 건수/추이 | `references/scripts-reference.md` | `datadog_apm.py services`, `count`, `timeseries` |
| Service errors, exception bursts, recent failures | `references/workflows/error-investigation.md` | `datadog_logs.py` |
| Incident timeline, outage reconstruction | `references/workflows/incident-timeline.md` | `datadog_logs.py` |
| Deploy regression, release-related errors | `references/workflows/deploy-regression.md` | `datadog_logs.py` |

## Local Files

`~/.config/datadog-helper/` contains two local files (setups created under the
old name keep working from `~/.config/datadog-log-helper/`):

- `config.json` - Datadog profiles and credentials. Scripts only read/write it.
- `MEMORY.md` - Agent-managed Markdown for frequently used logs, access paths,
  service/env/index aliases, query patterns, and workflow preferences.

The config directory should be `700`; `config.json` and `MEMORY.md` should be
`600`. Never store API keys, application keys, full log bodies, customer data, or
secrets in `MEMORY.md`.

## Scripts

- `datadog_setup.py`: `init-keys`, `auth-test`, `logs-test`, `apm-test`, `profiles`
- `datadog_logs.py`: `search`, `errors`, `timeline`, `around`, `count`, `agg`,
  `timeseries`, `fields`, `frames`, `patterns`
- `datadog_apm.py`: `search`, `trace`, `count`, `agg`, `latency`, `timeseries`,
  `services`, `fields`
- `datadog_common.py`: import-only shared implementation

건수·분포·top-N이 필요하면 raw 이벤트를 내려받아 세지 말고 `count`/`agg`를 먼저
쓴다 (서버사이드 집계라 정확하고 싸다). "언제부터 늘었나"는 `count` 반복이 아니라
`timeseries` 한 번으로 본다. 스키마를 모르면 `--raw` 덤프 대신 `fields`를
쓰고, 특정 필드 한두 개만 더 보고 싶으면 `--raw` 대신 `search --show @facet`을
쓴다. 로그에서 `trace_id`를 발견하면 `datadog_apm.py trace`로 트레이스를 이어서
본다 (반대 방향은 `datadog_logs.py search --trace-id`).

## Memory

`MEMORY.md` is important for this skill. It stores durable Datadog access
knowledge so the next session does not rediscover it:

- **서비스 별칭**: 사용자가 부르는 이름 ↔ 실제 `service:` 이름 ↔ 소스코드 repo
  (예: "svc" → `<env>-some-service`, repo `some-service-repo`)
- **로그 접근**: canonical `service:`/`env:`/`index:` 조합과 용도
- **로그 스키마**: 서비스별 `source:` 구분, 주요 facet, 로그 레벨 검색 패턴
  (예: access 로그는 `@status`, 서버 로그는 `"ERROR 1 ---"` 문자열 매칭)
- **APM 접근**: 서비스별 주요 `resource_name`/`operation_name` 패턴, 트레이스
  조사에 유효했던 스팬 쿼리
- **자주 쓰는 쿼리**: 재사용 가능한 쿼리 조각
- **선호**: 기본 조회 범위 등

Update triggers — do not wait passively:

1. **명시 트리거**: 사용자 메시지에 "기억", "기억해", "기억해줘", "저장해둬",
   "memory", "MEMORY", "MEMORY.md" 같은 단어가 나오면 메모리 요청으로 간주하고
   사용자의 의도를 파악한다.
   - **저장 대상이 명확한 경우** (직전 대화에서 확인된 사실을 가리키거나, 저장할
     내용을 직접 말한 경우): 묻지 말고 바로 `MEMORY.md`의 알맞은 섹션에 추가하고,
     추가/변경된 라인을 그대로 보고한다.
   - **모호한 경우** (무엇을 저장할지 여러 해석이 가능한 경우): 후보를 1~3개
     제시하고 어떤 것을 저장할지 한 번만 묻는다.
   - 이미 같은 내용이 있으면 중복 추가하지 않고 기존 라인을 갱신하거나 "이미
     저장되어 있다"고 알린다.
2. **탐색이 끝났을 때**: 조사 과정에서 새로 확인된 서비스명, 별칭, `source:` 구분,
   유효했던 쿼리 패턴이 있으면 마지막 응답에서 저장할지 한 문장으로 제안한다.
   ("이번에 확인된 `prd-some-service` 접근 패턴을 MEMORY.md에 저장할까요?")
3. 같은 사실을 두 번째 세션에서 다시 발견했다면 그것은 저장했어야 할 사실이다.
   즉시 저장을 제안한다.

저장할 때는 내용 성격에 맞는 섹션(서비스 별칭 / 로그 접근 / 로그 스키마 / APM
접근 / 자주 쓰는 쿼리 / 선호)을 고른다. 로그·스팬 원문, 고객 데이터, 키/secret은
어떤 경우에도 저장하지 않는다.

Keep entries short and operational. Recommended shape:

```markdown
# datadog-helper memory

## 서비스 별칭
- svc — <env>-some-service (prd-some-service, ...) — 소스코드: `some-service-repo` repo

## 로그 접근
- payments-api — service:payments-api env:prod — 결제 API 운영 로그

## 로그 스키마
- prd-some-service: access 로그는 @request_uri/@status facet, 서버 stdout은 source:console-logs

## APM 접근
- payments-api — 주요 리소스는 `POST /orders`; 결제 지연 조사는 latency --by resource_name

## 자주 쓰는 쿼리
- 배포 회귀 — service:<service> env:prod @version:<version> status:error

## 선호
- 기본 조회 범위는 최근 30분으로 본다
```

## Rules

- Default to recent, bounded reads: `now-15m`, limit 20.
- Confirm before broad reads such as query `*` over more than a short window,
  limit over 500, or multi-day searches.
- Prefer compact output. Use `--raw` only when a workflow truly needs full API
  JSON, and keep it to a few events (limit 5 초과는 `--allow-wide` 필요).
- Search compactly first, then run narrower follow-up queries by service, env,
  status, trace id, host, index, or version.
- If a search prints a `--cursor` hint, results were truncated; page through with
  the cursor instead of widening the limit.
- APM 조회는 인덱싱된 스팬만 대상이다 (retention filter 통과분, 보존 기간 제한).
  결과가 비면 기간·retention을 의심하고, 장기 추세는 로그/다른 수단을 검토한다.
- Treat API errors as setup signals. On missing config, invalid key, forbidden, or
  scope/permission errors, route to `references/setup-guide.md`.
- Do not write log or span contents into repo files. Only write durable
  user-approved access hints to `MEMORY.md`.
