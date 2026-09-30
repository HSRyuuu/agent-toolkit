# Deploy Regression Workflow

Use this workflow when the user suspects a deploy, release, version, or rollout caused new errors.

## Steps

2~4번은 서로 의존하지 않는다. `normal`·`fast` 모드에서는 추이 비교 / 배포 후 에러 /
버전 한정 조회를 subagent 셋으로 동시에 돌린다 (SKILL.md `## Parallel Investigation`).
배포 시각과 버전 태그는 위임 전에 확정해서 각 프롬프트에 값으로 넣는다.

1. Read `MEMORY.md` for service/env/version tag conventions.
2. See the error-rate shift around the deploy in one call — a timeseries spanning
   before and after the deploy time:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" timeseries --service <service> --env <env> --status error --from <before-window> --interval 15m
# 버전 태그가 있으면 버전별로 분리해서 비교
python3 "<SKILL_DIR>/scripts/datadog_logs.py" timeseries --service <service> --env <env> --status error --from <before-window> --by @version
```

3. Read the actual errors after the deployment time:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" errors --service <service> --env <env> --from <deploy-time> --limit 100
```

4. If a version tag is known, narrow to the new version:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" search "service:<service> env:<env> status:error @version:<version>" --from <time> --limit 100
```

Back the comparison with exact counts when the timeseries is ambiguous:

```bash
python3 "<SKILL_DIR>/scripts/datadog_logs.py" count --service <service> --status error --from <deploy-time>
python3 "<SKILL_DIR>/scripts/datadog_logs.py" count --service <service> --status error --from <before-window> --to <deploy-time>
```

5. Look for:
   - new error message shapes (`patterns`로 배포 전/후 유형 분포를 비교하면 빠르다)
   - version/build tags
   - specific hosts/pods
   - upstream timeout or dependency failures
   - HTTP status shifts

## Output

Summarize whether the logs support the regression hypothesis, what changed after
the deploy, and the strongest event IDs/trace IDs to inspect next.
