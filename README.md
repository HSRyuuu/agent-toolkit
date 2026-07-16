# agent-toolkit

> 이 저장소는 [https://github.com/HSRyuuu/AI-Practice-Archive](https://github.com/HSRyuuu/AI-Practice-Archive)를 플러그인 형태로 변경한 것입니다.
> 더 이상 기존 저장소는 유지보수되지 않고 이 저장소로 마이그레이션 되었습니다.
>
> Claude Code와 Codex 양쪽에서 로컬 플러그인으로 등록해 쓰는 개인용 agent toolkit입니다.

## 설치

marketplace 이름은 `hsryuuu`, 플러그인 이름은 `agent-toolkit`이다. 설치 방식은 두 가지이며 **한 머신에는 하나만** 쓴다 (둘 다 설치하면 스킬이 중복 로드된다).

### 방식 1 — GitHub에서 설치 (일반 사용)

클론이 필요 없다. 두 도구 모두 저장소를 자체 캐시에 복사한다.

**Claude Code** — 채팅창에 입력한다.

```text
/plugin marketplace add HSRyuuu/agent-toolkit
/plugin install agent-toolkit@hsryuuu
```

**Codex** — 터미널에서 실행한다.

```bash
codex plugin marketplace add HSRyuuu/agent-toolkit
codex plugin add agent-toolkit@hsryuuu
```

### 방식 2 — 로컬 디렉토리로 설치 (개발 머신)

스킬을 직접 편집하는 머신에서는 클론을 directory marketplace로 등록한다. 파일을 고치면 다음 세션부터 바로 반영되고, 버전 범프나 push가 필요 없다.

```bash
git clone https://github.com/HSRyuuu/agent-toolkit.git
cd agent-toolkit
pwd # ~/your-dir/agent-toolkit
```

**Claude Code** — 채팅창에 입력한다.

```text
/plugin marketplace add ~/your-dir/agent-toolkit
/plugin install agent-toolkit@hsryuuu
```

**Codex** — 터미널에서 실행한다.

```bash
codex plugin marketplace add ~/your-dir/agent-toolkit
codex plugin add agent-toolkit@hsryuuu
codex plugin list --available --json
```

Claude Code는 `.claude-plugin/plugin.json`, Codex는 `.agents/plugins/marketplace.json`과 `.codex-plugin/plugin.json`을 사용한다. 두 도구 모두 활성 스킬 루트는 `skills/` 하나이며, 모든 플러그인 스킬은 `skills/<name>/SKILL.md` 형태로 둔다.

### 업데이트 (GitHub 설치 시)

서드파티 marketplace는 자동 업데이트가 기본으로 꺼져 있으므로 직접 실행한다.

```bash
# Claude Code — 카탈로그 갱신 후 플러그인 업데이트. 적용에는 재시작이 필요하다.
claude plugin marketplace update hsryuuu
claude plugin update agent-toolkit@hsryuuu

# Codex — 마켓플레이스 스냅샷 갱신
codex plugin marketplace upgrade hsryuuu
```

두 도구 모두 **플러그인 version을 캐시 키**로 쓴다 (`~/.claude/plugins/cache/…/<version>/`, `~/.codex/plugins/cache/…/<version>/`). 변경사항을 GitHub 설치 사용자에게 전달하려면 `.claude-plugin/plugin.json`과 `.codex-plugin/plugin.json`의 `version`을 **같은 값으로 반드시 올려야** 한다. 버전이 그대로면 새 커밋을 push해도 캐시된 사본이 유지된다. 단, `marketplace.json`의 `plugins[]` 항목에는 version을 넣지 않는다 — 넣으면 `plugin.json` 값이 경고 없이 이긴다.

로컬 디렉토리 설치는 버전 범프 없이 다음 세션부터 편집 내용이 반영된다.

## 무엇이 들어 있나

- `skills/` - Claude Code와 Codex가 함께 읽는 단일 플러그인 스킬 루트
- `templates/` - 스킬이 대상 프로젝트에 복사하거나 참고하는 템플릿
- `docs/catalog.md` - 현재 `skills/*/SKILL.md` frontmatter에서 생성한 사람용 카탈로그
- `.claude-plugin/` - Claude Code 플러그인 메타데이터
- `.codex-plugin/` - Codex 플러그인 메타데이터
- `.agents/plugins/` - Codex 로컬 marketplace 메타데이터

전체 스킬 목록과 트리거는 [docs/catalog.md](docs/catalog.md)를 본다. 스킬의 카테고리는 문서상의 메타데이터일 뿐이며, 로더 구조를 나누는 디렉토리 기준이 아니다.

KB 스킬의 최초 설정과 선택적 Obsidian 연동은
[`skills/kb/README.md`](skills/kb/README.md)를 본다.

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
