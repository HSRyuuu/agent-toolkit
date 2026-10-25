# skill:* — 프로젝트 로컬 스킬 설치

`templates/skills/` 아래 스킬을 대상 프로젝트의 `.claude/skills/`에 복사한다. 설치된 스킬은 그 프로젝트에서만 로드된다.

## 대상

| 스킬 | 위치 | 원본 | 권할 때 |
| --- | --- | --- | --- |
| `sync-docs` | `.claude/skills/sync-docs/` | `templates/skills/sync-docs/` | 진입점 매핑 표에 문서가 하나라도 있을 때 |
| `manage-skills` | `.claude/skills/manage-skills/` | `templates/skills/manage-skills/` | 프로젝트 전용 `verify-*` 스킬을 쌓아 가고 싶을 때 |
| `verify-implementation` | `.claude/skills/verify-implementation/` | `templates/skills/verify-implementation/` | `manage-skills`와 함께 |

Codex를 쓰는 프로젝트면 같은 스킬을 그 프로젝트가 이미 쓰는 Codex 스킬 경로(`.codex/skills/` 또는 `.agents/skills/`)에도 둘지 묻는다.

## 절차

1. 원본이 디스크에 있는 스킬만 대상으로 한다.
2. 스킬마다 원본과 목적지를 보여 준다.
3. 목적지가 있으면 유지 / `.bak.<timestamp>` 백업 후 교체 / 다른 이름으로 설치 / 취소 중에서 묻는다. 스킬 디렉토리는 병합하지 않는다.
4. 같은 이름의 전역·plugin 스킬이 있으면 로컬 스킬이 우선할 수 있다고 알린다.
5. 승인된 디렉토리만 복사한다. 사용자가 프로젝트 맞춤을 요청하지 않으면 복사한 `SKILL.md`를 고치지 않는다.
6. 진입점 매핑 표의 `프로젝트 스킬`에 설치한 스킬을 추가한다. `sync-docs`를 설치했으면 `entrypoint.md`의 sync-docs 규칙도 진입점에 넣는다.

## 검증

```bash
find "$TARGET/.claude/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort
```
