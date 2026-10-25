# skill:* — 프로젝트 로컬 스킬

`templates/skills/` 아래 스킬을 대상 프로젝트의 스킬 디렉토리에 설치하고, 프로젝트에 맞게 토큰을 채운 뒤 진입점에 등록한다. 스킬 디렉토리는 규약 §3을 따른다.

## 대상

| 스킬 | 원본 | 하는 일 | 동작에 필요한 것 |
| --- | --- | --- | --- |
| `sync-docs` | `templates/skills/sync-docs/` | 코드 변경 후 매핑된 문서를 맞춘다. 자동 호출된다 | 진입점 매핑 표에 문서 1개 이상, 진입점의 sync-docs 규칙 줄 |
| `manage-skills` | `templates/skills/manage-skills/` | 세션 변경을 보고 `verify-*` 스킬을 만들고 고친다. `/manage-skills`로 직접 실행 | `verify-implementation`, 진입점 매핑 표 |
| `verify-implementation` | `templates/skills/verify-implementation/` | 기본 검사와 모든 `verify-*`를 실행한다. `/verify-implementation`으로 직접 실행 | 기본 검사 명령 또는 `verify-*` 스킬 |

`manage-skills`와 `verify-implementation`은 짝으로 설치한다. 하나만 고르면 짝이 필요한 이유를 알리고 함께 설치할지 묻는다.

## 절차

1. 스킬마다 원본과 목적지를 보여 준다. 두 호스트를 쓰면 목적지가 두 곳이다.
2. 디렉토리를 통째로 복사한다.
3. 토큰을 채운다.

| 스킬 | 토큰 | 값 |
| --- | --- | --- |
| `manage-skills` | `{BASE_BRANCH}` | 프로필의 기본 브랜치. 모르면 `main`을 쓰고 보고한다 |
| `verify-implementation` | `{BASELINE_ROWS}` | `\| 테스트 \| \`./gradlew test\` \| \`backend/\` \|` 형식의 행. CI에서 실제로 돌리는 빌드·테스트·린트·타입체크 명령. 하나도 없으면 행 대신 `\| — \| (아직 없음) \| — \|` 한 줄을 둔다 |

4. 진입점 `### 프로젝트 스킬`에 설치한 스킬을 한 줄씩 등록한다.

| 스킬 | 용도 칸 문구 |
| --- | --- |
| `/sync-docs` | 코드 변경 후 아래 외부문서를 실제 상태와 맞춘다 |
| `/manage-skills` | 세션 변경을 분석해 `verify-*` 스킬을 만들고 고친다 |
| `/verify-implementation` | 기본 검사와 모든 `verify-*` 스킬을 실행한다 |

5. `sync-docs`를 설치했으면 진입점 `## 문서 매핑` 바로 아래에 다음 규칙 줄을 넣는다. 이 줄이 있어야 에이전트가 매번 문서를 맞춘다.

```markdown
- 아래 외부문서에 영향을 주는 변경(라우트·스키마·환경변수·배포·의존성·디렉토리 구조 등)을 마쳤으면, 완료를 보고하거나 커밋하기 전에 `sync-docs`로 문서를 맞춘다.
```

6. `verify-implementation`을 설치했으면 같은 위치에 다음 줄을 넣는다.

```markdown
- 기능 구현을 마치면 PR 전에 `/verify-implementation`을 실행한다.
```

## 충돌과 이전

- 목적지가 있으면 유지 / `.bak.<timestamp>` 백업 후 교체 / 다른 이름으로 설치 / 취소 중에서 묻는다. 스킬 디렉토리는 병합하지 않는다.
- 설치된 스킬이 원본과 다르면 프로젝트 맞춤일 수 있다. `diff -ru`로 차이를 보여 주고 갱신할지 묻는다.
- **구 이름 `update-project-docs`가 있으면** `sync-docs`로 교체를 권한다. 승인되면 `sync-docs`를 설치하고, `update-project-docs`는 백업 후 지우고, 매핑 표의 `/update-project-docs` 행을 `/sync-docs`로 바꾸고, 규칙 줄을 넣는다.
- 구 `verify-implementation`에 `## 실행 대상 스킬` 표가 있으면 새 버전은 디렉토리를 직접 찾는다는 점을 알리고, 갱신 시 표에 있던 스킬이 모두 `verify-*/`로 존재하는지 확인한다.
- 같은 이름의 전역·plugin 스킬이 있으면 로컬 스킬이 우선할 수 있다고 알린다.

## 검증

```bash
python3 <skill>/scripts/check_harness.py "$TARGET"
```

스킬 이름 불일치, 토큰 잔존, sync-docs 규칙·매핑 누락, 짝 누락이 없어야 한다.
