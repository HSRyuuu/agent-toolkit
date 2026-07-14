# Incident Timeline Workflow

Use this workflow for outage reconstruction, 장애 회고, or "언제부터 무슨 일이 있었는지" requests.

## Steps

1. Read `MEMORY.md`.
2. Find when it started with a server-side timeseries first — cheaper and more
   precise than reading events:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" timeseries "<query>" --from now-6h --interval 10m
```

3. Read events around the spike: a bounded ascending window, or `around` on the
   spike time:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" timeline "<query>" --from now-2h --limit 100
python3 "<SKILL_DIR>/scripts/datadog_logs.py" around "<query>" --time "<spike-time>" --window 10
```

4. If the query is broad, ask for confirmation before widening time range or limit.
5. Build a concise timeline with:
   - first observed error
   - spikes or pattern changes
   - deploy/version/host changes if visible
   - representative trace/event IDs
6. Avoid copying long log bodies. Quote only the smallest useful fragments.

## Follow-Up Queries

- Narrow by `status:error`.
- Add `@http.status_code:[500 TO 599]` for HTTP incidents.
- Add `@trace_id:<id>` to inspect related events.
- Add `@version:<version>` when deploy metadata appears.
