# old — 보관 스킬

더 이상 배포하지 않는 스킬을 모아 둔다. marketplace(`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`)에 등록되어 있지 않고 `plugins/` 밖에 있어서 설치되지 않는다. 필요하면 `SKILL.md` 디렉토리를 `plugins/<plugin>/skills/` 아래로 되돌리고 manifest와 marketplace 항목을 다시 만든다.

보관 사유는 대체로 같다. 모델이 좋아져서 지침 없이도 같은 결과를 내거나, 범용 지식이라 가치가 줄었다. 기억해 둘 만한 규칙만 남기고 줄여서 보관한 것도 있다.

| 폴더 | 스킬 | 비고 |
|---|---|---|
| `coding-conventions/` | `springboot-java-convention`, `springboot-kotlin-standards`, `fastapi-guide`, `node-backend-patterns`, `rest-api-design` | 범용 예제와 `references/`를 걷어내고 고유 규칙만 남겼다 |
| `html-tools/` | `html-docs-creator`, `html-cheat-sheet-creator` | 고정 디자인 템플릿(`base.html`)이 자산이다 |
| `agent-harness/` | `agent-harness-construction`, `agent-introspection-debugging` | harness-as-usual이 같은 규칙을 이미 갖고 있다 |
| `prompt-tools/` | `prompt-master` | 최신 모델 비적용 게이트만 걷어내고 작성 기법과 `references/`는 그대로 보존했다 |
