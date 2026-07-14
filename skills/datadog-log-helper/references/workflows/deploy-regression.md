# Deploy Regression Workflow

Use this workflow when the user suspects a deploy, release, version, or rollout caused new errors.

## Steps

1. Read `MEMORY.md` for service/env/version tag conventions.
2. Search errors after the deployment time:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" errors --service <service> --env <env> --from <deploy-time> --limit 100
```

3. If a version tag is known, compare old/new versions:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" search "service:<service> env:<env> status:error @version:<version>" --from <time> --limit 100
```

Compare exact error counts before/after with `count` instead of comparing sample sizes:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" count --service <service> --status error --from <deploy-time>
python3 "<SKILL_DIR>/scripts/datadog_logs.py" count --service <service> --status error --from <before-window> --to <deploy-time>
```

4. Look for:
   - new error message shapes
   - version/build tags
   - specific hosts/pods
   - upstream timeout or dependency failures
   - HTTP status shifts

## Output

Summarize whether the logs support the regression hypothesis, what changed after
the deploy, and the strongest event IDs/trace IDs to inspect next.
