# lessons — 자기개선 루프

사용자의 교정을 기록해 이후 에이전트가 같은 실수를 반복하지 않게 한다. 파일과 진입점 규칙이 **둘 다** 있어야 동작한다.

## 대상

| 자산 | 위치 | 원본 |
| --- | --- | --- |
| `LESSONS.md` | `.claude/LESSONS.md` | `templates/LESSONS.md` |
| 자기개선 규칙 | 정본 진입점 `## Workflows` | 아래 문구 |

`LESSONS.md`는 에이전트 운영 기록이다. `docs/`에 두지 않는다. 진입점 `### 외부문서`에는 등록하되(`sync-docs`는 이 파일을 건너뛴다), 용도 칸에 "자기개선 기록"이라고 적는다.

## 절차

1. `templates/LESSONS.md`를 복사하고 `{PROJECT_NAME}`을 채운다. 대체 템플릿을 지어내지 않는다.
2. 진입점에 규칙을 넣는다. `## Workflows`가 있으면 그 안에 다음 번호로, 없으면 `## Self-Improvement Loop` 섹션으로 넣는다.

```markdown
### Self-Improvement Loop

- 세션을 시작할 때 `.claude/LESSONS.md`를 읽고, 현재 작업 영역에 해당하는 lesson을 적용한다.
- 사용자가 에이전트의 행동을 교정하면 그 파일의 형식대로 즉시 기록한다.
- 같은 실수가 반복되면 새 항목을 더하지 말고 기존 lesson을 강화한다.
- 반복 횟수가 3에 이르면 `.claude/rules/<area>.md`로 옮길지 사용자에게 제안한다.
```

3. 비슷한 규칙이 이미 있으면 사용자 문구를 보존하고 빠진 줄만 더한다.
4. Codex만 쓰는 프로젝트도 경로는 `.claude/LESSONS.md`를 그대로 쓴다. 진입점 규칙이 경로를 가리키므로 호스트와 무관하게 동작한다.

## 검증

```bash
python3 <skill>/scripts/check_harness.py "$TARGET"
```

"LESSONS.md가 있지만 진입점에 규칙이 없다" ERROR가 없어야 한다.
