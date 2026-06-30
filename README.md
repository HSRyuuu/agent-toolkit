# agent-toolkit

> 이 저장소는 [https://github.com/HSRyuuu/AI-Practice-Archive](https://github.com/HSRyuuu/AI-Practice-Archive)를 플러그인 형태로 변경한 것입니다.
> 더 이상 기존 저장소는 유지보수되지 않고 이 저장소로 마이그레이션 되었습니다.
>
> Claude Code와 Codex 양쪽에서 로컬 플러그인으로 등록해 쓰는 개인용 agent toolkit입니다.

## 설치

먼저 원하는 위치에 저장소를 둔다.

```bash
git clone https://github.com/HSRyuuu/agent-toolkit.git
cd agent-toolkit
pwd # ~/your-dir/agent-toolkit
```

### Claude Code

```text
/plugin marketplace add ~/your-dir/agent-toolkit
/plugin install agent-toolkit@agent-toolkit-local
```

Claude Code는 `.claude-plugin/plugin.json`을 사용한다. 이 플러그인의 활성 스킬 루트는 `skills/` 하나이며, 모든 플러그인 스킬은 `skills/<name>/SKILL.md` 형태로 둔다.

### Codex

```bash
codex plugin marketplace add ~/your-dir/agent-toolkit
codex plugin add agent-toolkit@agent-toolkit-local
codex plugin list --available --json
```

Codex는 `.agents/plugins/marketplace.json`과 `.codex-plugin/plugin.json`을 사용한다. Codex도 같은 `skills/` 루트를 읽는다.

새 세션을 띄우면 설치된 플러그인 스킬이 자동 로드된다. 디렉토리를 그대로 편집하면 다음 세션부터 반영되며 별도 빌드·배포 단계는 없다.

## 무엇이 들어 있나

- `skills/` - Claude Code와 Codex가 함께 읽는 단일 플러그인 스킬 루트
- `templates/` - 스킬이 대상 프로젝트에 복사하거나 참고하는 템플릿
- `docs/catalog.md` - 현재 `skills/*/SKILL.md` frontmatter에서 생성한 사람용 카탈로그
- `.claude-plugin/` - Claude Code 플러그인 메타데이터
- `.codex-plugin/` - Codex 플러그인 메타데이터
- `.agents/plugins/` - Codex 로컬 marketplace 메타데이터

전체 스킬 목록과 트리거는 [docs/catalog.md](docs/catalog.md)를 본다. 스킬의 카테고리는 문서상의 메타데이터일 뿐이며, 로더 구조를 나누는 디렉토리 기준이 아니다.

## 갱신

스킬을 추가·이동·삭제했거나 manifest의 스킬 루트를 바꿨으면 `update-project-docs` 스킬로 문서를 동기화한다.

기본 점검 명령:

```bash
find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort | wc -l
grep -oE '\(\.\./skills/[^)]+/SKILL\.md\)' docs/catalog.md | tr -d '()' | sed 's#^../##' | while read p; do test -f "$p" || echo "MISSING: $p"; done
python3 /Users/happyhsryu/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py /Users/happyhsryu/dev/personal/agent-toolkit
```

## 구성

### skills/

모든 플러그인 스킬의 실제 위치다. 현재 inventory는 `skills/*/SKILL.md`만 스캔해서 계산한다.
`SKILL.md` 없는 보조 디렉토리는 공유 자산으로만 취급하고 inventory에 포함하지 않는다.

```bash
find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort
```

### templates/

다른 스킬이 골격 원본으로 사용하는 템플릿 모음. 직접 플러그인 스킬로 로드되지 않는다.

| 이름 | 설명 |
|---|---|
| [project-setup/](templates/project-setup/) | `setup-*` 계열 스킬이 대상 프로젝트에 설치하거나 참고하는 작업 문서와 보조 스킬 템플릿 |
| [rules/](templates/rules/) | 외부 가이드라인 사본 |
