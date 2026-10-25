# agent-toolkit

> 이 저장소는 [https://github.com/HSRyuuu/AI-Practice-Archive](https://github.com/HSRyuuu/AI-Practice-Archive)를 플러그인 형태로 변경한 것입니다.
> 더 이상 기존 저장소는 유지보수되지 않고 이 저장소로 마이그레이션 되었습니다.
>
> Claude Code와 Codex 양쪽에서 로컬 플러그인으로 등록해 쓰는 개인용 agent toolkit입니다.

## 설치

marketplace 이름은 `hsryuuu`이고, **플러그인 단위로 골라 설치한다.** 관련 스킬은 한 플러그인에 묶여 함께 설치된다 (예: `coding-convention` = Java + Kotlin 컨벤션).

```text
/plugin marketplace add HSRyuuu/agent-toolkit
/plugin install kb@hsryuuu
```

설치 방식(GitHub / 로컬 디렉토리), 업데이트, 버전 범프 규칙, 문제 해결은 [docs/how-to-install.md](docs/how-to-install.md)를 본다.

## 무엇이 들어 있나

- `plugins/<name>/` - 플러그인 하나. `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `skills/<skill>/SKILL.md`를 가진다
- `docs/catalog.md` - 플러그인·스킬 카탈로그 (`plugins/*/skills/*/SKILL.md` frontmatter에서 생성)
- `docs/how-to-install.md` - 설치, 업데이트, 버전 범프, 배포, 문제 해결
- `scripts/bump-plugin.sh` - 플러그인 한 개의 두 manifest 버전을 같은 값으로 올린다
- `templates/rules/` - 외부 가이드라인 사본
- `.claude-plugin/marketplace.json` - Claude Code marketplace
- `.agents/plugins/marketplace.json` - Codex marketplace

전체 목록과 트리거는 [docs/catalog.md](docs/catalog.md)를 본다.

KB 스킬의 최초 설정과 선택적 Obsidian 연동은
[`plugins/kb/skills/kb/README.md`](plugins/kb/skills/kb/README.md)를 본다.

## 갱신

플러그인이나 스킬을 추가·이동·삭제했거나 manifest를 바꿨으면 `update-project-docs` 스킬로 문서를 동기화한다.

기본 점검 명령:

```bash
find plugins -mindepth 4 -maxdepth 4 -path '*/skills/*' -name SKILL.md -print | sort | wc -l
grep -oE '\(\.\./plugins/[^)]+/SKILL\.md\)' docs/catalog.md | tr -d '()' | sed 's#^../##' | while read p; do test -f "$p" || echo "MISSING: $p"; done
jq empty .claude-plugin/marketplace.json .agents/plugins/marketplace.json plugins/*/.claude-plugin/plugin.json plugins/*/.codex-plugin/plugin.json
```

## 플러그인 묶음

| 플러그인 | 포함 스킬 |
|---|---|
| `coding-convention` | springboot-java-convention, springboot-kotlin-standards |
| `project-setup` | setup-* 6개, si-project-docs, update-project-docs (+ `templates/`) |
| `html-tools` | html-cheat-sheet-creator, html-db-schema-viewer-creator, html-docs-creator |
| `excel-docs` | excel-doc-updater, excel-ui-test-doc-creator |
| `prompt-tools` | prompt-master, prompt-modernizer, writing-great-skill |
| `writing-tools` | docs-writing, ux-writing |
| `personal-tools` | dev-blog-writing-hsryuuu (개인 전용 스킬 모음) |

나머지는 스킬 이름 = 플러그인 이름인 1:1 플러그인이다.
