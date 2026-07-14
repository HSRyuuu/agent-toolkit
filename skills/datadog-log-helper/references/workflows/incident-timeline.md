# Incident Timeline Workflow

Use this workflow for outage reconstruction, 장애 회고, or "언제부터 무슨 일이 있었는지" requests.

## Steps

1. Read `MEMORY.md`.
2. Start with a bounded timeline query:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" timeline "<query>" --from now-2h --limit 100
```

3. If the query is broad, ask for confirmation before widening time range or limit.
4. Build a concise timeline with:
   - first observed error
   - spikes or pattern changes
   - deploy/version/host changes if visible
   - representative trace/event IDs
5. Avoid copying long log bodies. Quote only the smallest useful fragments.

## Follow-Up Queries

- Narrow by `status:error`.
- Add `@http.status_code:[500 TO 599]` for HTTP incidents.
- Add `@trace_id:<id>` to inspect related events.
- Add `@version:<version>` when deploy metadata appears.
