# lessons — 자기개선 루프

사용자의 교정을 기록해 이후 에이전트가 같은 실수를 반복하지 않게 하는 프로젝트 로컬 루프를 둔다.

## 대상

| 자산 | 위치 | 원본 |
| --- | --- | --- |
| `LESSONS.md` | `.claude/LESSONS.md` | `templates/LESSONS.md` |
| 자기개선 규칙 | 기존 `AGENTS.md` 또는 `CLAUDE.md` | 아래 문구 |

`LESSONS.md`는 에이전트 운영 기록이지 프로젝트 문서가 아니다. `docs/`에 두지 않고, `sync-docs` 매핑 대상에도 넣지 않는다.

## 절차

1. `.claude/LESSONS.md`가 있는지 본다.
2. 진입점(`AGENTS.md`, `.claude/CLAUDE.md`, `CLAUDE.md` 순)에 `LESSONS` / `Self-Improvement` 규칙이 있는지 본다. `templates/CLAUDE.md`로 진입점을 새로 만들면 이 규칙이 이미 들어 있다.
3. 필요한 최소 작업만 한다: 없으면 `LESSONS.md` 복사, 규칙이 없으면 규칙 추가, 둘 다 있으면 아무것도 하지 않음.
4. `templates/LESSONS.md`에서만 복사한다. 대체 템플릿을 지어내지 않는다.

## 진입점 문구

```markdown
## Self-Improvement Loop

- 세션을 시작할 때 `.claude/LESSONS.md`가 있으면 읽는다.
- 사용자가 에이전트의 행동을 교정하면 그 파일 형식대로 즉시 기록한다.
- 같은 실수가 반복되면 새 항목을 더하지 말고 기존 교훈을 강화한다.
```

비슷한 섹션이 이미 있으면 사용자 문구를 보존하고 빠진 규칙만 더한다.

## 검증

```bash
test -f "$TARGET/.claude/LESSONS.md"
rg -n "LESSONS|Self-Improvement" "$TARGET/AGENTS.md" "$TARGET/.claude/CLAUDE.md" "$TARGET/CLAUDE.md" 2>/dev/null
```
