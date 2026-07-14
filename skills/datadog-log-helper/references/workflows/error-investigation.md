# Error Investigation Workflow

Use this workflow for recent service errors, exception bursts, or "왜 에러가 났는지 봐줘" requests.

## Steps

1. Read `MEMORY.md` for service aliases, env defaults, and known index names.
2. Search recent errors first:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" errors --service <service> --env <env> --minutes 30 --limit 50
```

3. Rank the clusters server-side instead of eyeballing raw events:

```bash
# 어떤 경로/코드에 몰렸는지
python3 "<SKILL_DIR>/scripts/datadog_logs.py" agg --service <service> "<error query>" --by @request_uri --by @status --from now-24h
# 정확한 총 건수
python3 "<SKILL_DIR>/scripts/datadog_logs.py" count --service <service> "<error query>" --from now-24h
```

4. For Java services, rank app stack frames to locate the throwing code:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" frames --service <service> "<error query>" --prefix <package> --from now-24h --limit 200
```

5. Run narrower follow-up searches for the strongest cluster.
6. Summarize:
   - time window
   - dominant error pattern with exact counts
   - affected service/env
   - example event IDs or trace IDs
   - likely next query or owner

## Memory Update

If the investigation confirmed a service name, alias, `source:` split, or query
pattern that was not in `MEMORY.md`, propose saving it in your final answer. If
the user says this is the normal way to inspect the service, update
`~/.config/datadog-log-helper/MEMORY.md` with the service/env/index/query hint.
