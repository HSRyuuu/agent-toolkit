---
name: update-project-docs
description: >
  Use when the agent-toolkit repo's plugin docs or manifests may be out of sync
  after adding, moving, deleting, or renaming skills, changing SKILL.md
  frontmatter, changing .codex-plugin/.claude-plugin skill settings, or updating
  plugin loading structure. Triggers: "catalog 갱신", "문서 동기화", "스킬 추가했어",
  "plugin manifest 바꿨어". Do NOT use for unrelated project docs.
---

# Update Project Docs (agent-toolkit 전용)

이 스킬은 **이 저장소(agent-toolkit)** 의 개발용 문서와 플러그인 표면이 실제 파일 상태와 어긋나지 않도록 갱신한다. 스킬은 플러그인(`plugins/<name>/skills/<skill>/`) 단위로 나뉘어 배포되며, Claude Code와 Codex가 같은 `plugins/` 구조를 쓴다는 전제를 유지한다.

대상 파일:
- `AGENTS.md` - Codex와 공통 에이전트가 읽는 저장소 구조, 규칙, 작업 지침
- `.claude/CLAUDE.md` - Claude Code가 읽는 저장소 구조, 규칙, 작업 지침
- `README.md` - 저장소를 처음 여는 사람이 보는 소개, 설치, 구성 요약
- `docs/catalog.md` - `plugins/*/skills/`에 있는 plugin·skill 카탈로그
- `plugins/<name>/.codex-plugin/plugin.json` - Codex plugin manifest
- `plugins/<name>/.claude-plugin/plugin.json` - Claude Code plugin manifest
- `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` - 플러그인 목록

위 파일들은 같은 사실을 말해야 한다. `AGENTS.md`와 `.claude/CLAUDE.md`의 구조 설명, `README.md`의 구성 요약, `docs/catalog.md`의 목록, marketplace 두 파일의 플러그인 목록이 동시에 `plugins/` 기준으로 맞아야 한다.

## 트리거

다음 중 하나라도 발생하면 갱신한다:

1. `plugins/` 아래에 plugin이나 skill을 추가, 삭제, 이동했다.
2. `plugins/<plugin>/skills/<name>/SKILL.md` frontmatter의 `name` 또는 `description`을 의미 있게 바꿨다.
3. plugin manifest나 marketplace 파일의 `skills`, `name`, `description`, `version`을 바꿨다.
4. plugin skill 로딩 방식이나 저장소 구조 설명을 바꿨다.
5. `agents/`, `hooks/`, `commands/`, `templates/` 같은 보조 자산의 활성 상태가 문서와 달라졌다.

단순 오타나 문장 다듬기는 트리거가 아니다. 실제 파일 상태, plugin manifest, 또는 로딩 정책이 바뀐 경우에만 실행한다.

## 워크플로우

### Step 1 - 현재 상태 스캔

plugin skill inventory는 **오직 `plugins/*/skills/`만** 스캔한다.

```bash
# plugin skill 목록
find plugins -mindepth 4 -maxdepth 4 -path '*/skills/*' -name SKILL.md -print | sort

# plugin manifest 상태
jq -r '.plugins[].name' .claude-plugin/marketplace.json .agents/plugins/marketplace.json
for m in plugins/*/.claude-plugin/plugin.json plugins/*/.codex-plugin/plugin.json; do jq -c '[.name,.version]' "$m"; done

# 각 plugin skill의 frontmatter
for s in plugins/*/skills/*/SKILL.md; do
  [ -f "$s" ] || continue
  echo "=== $s ==="
  awk '/^---$/{c++; next} c==1' "$s"
done
```

추가로 확인할 것:
- `AGENTS.md`, `.claude/CLAUDE.md`, `README.md`, `docs/catalog.md`가 같은 skill 목록과 루트 정책을 설명하는가?
- 각 플러그인의 두 manifest가 같은 `name`/`version`이고, marketplace 두 파일이 `plugins/` 아래 실제 디렉토리와 1:1인가?
- `templates/`는 템플릿으로만 설명되어 있는가? 빈 디렉토리나 임시 구조를 plugin skill로 승격하지 않는다.

### Step 2 - `docs/catalog.md` 갱신

`docs/catalog.md`는 `plugins/*/skills/*/SKILL.md` frontmatter에서 생성한 plugin·skill 카탈로그로 유지한다.

작성 규칙:
- `Last updated`는 현재 날짜로 갱신한다.
- 목록은 `plugins/*/skills/` 아래 실제 `SKILL.md`가 있는 디렉토리만 포함한다.
- 플러그인 이름, 스킬 디렉토리명 순으로 정렬한다.
- 링크 경로는 catalog 기준 상대경로인 `../plugins/<plugin>/skills/<name>/SKILL.md`를 사용한다.
- 한 줄 설명은 frontmatter `description`에서 "무엇을 하는지"만 추출하고, 호출 문구나 장황한 사용 조건은 줄인다.
- 빈 디렉토리, 임시 폴더, 템플릿 폴더는 카탈로그에 올리지 않는다.

검증:

```bash
grep -oE '\(\.\./plugins/[^)]+/SKILL\.md\)' docs/catalog.md \
  | tr -d '()' \
  | sed 's|^\.\./||' \
  | while read p; do [ -f "$p" ] || echo "MISSING: $p"; done
```

`MISSING:`이 한 줄도 나오지 않아야 한다.

### Step 3 - `AGENTS.md`와 `.claude/CLAUDE.md` 갱신

두 에이전트 지침 파일은 같은 저장소 사실을 공유하되, 각 도구 표면에 필요한 문구만 다르게 둔다.

확인 항목:
- 저장소 구조 트리가 `plugins/<name>/skills/<skill>` 구조를 설명하는가?
- 플러그인별 두 manifest와 marketplace 두 파일의 역할이 정확히 설명되는가?
- `README.md`와 `docs/catalog.md`를 갱신 대상으로 안내하는가?
- 사용하지 않는 로더 루트, 중복 local skill copy, 빈 placeholder를 현재 구조처럼 설명하지 않는가?
- `.claude/CLAUDE.md`는 Claude Code 전용 지침을 담되, plugin skill inventory 자체는 `plugins/` 기준으로 설명하는가?

의도적인 정책 변화가 없으면 문장 전체를 다시 쓰지 말고, 틀린 사실만 좁게 고친다.

### Step 4 - `README.md` 갱신

README는 처음 보는 사람이 저장소 목적과 현재 plugin 구성을 빠르게 파악하게 한다.

작성 규칙:
- 상단 소개, 설치, 갱신 안내는 짧게 유지한다.
- `plugins/`는 실제 plugin 루트로 설명한다.
- `templates/`는 다른 스킬이 사용하는 원본 자산으로 설명하고 plugin skill 목록에 섞지 않는다.
- 전체 skill 목록과 트리거는 `docs/catalog.md`로 연결한다.
- 디렉토리 개수나 수동 카운트는 꼭 필요할 때만 쓰고, 쓰는 경우 현재 `plugins/` inventory와 일치시킨다.

### Step 5 - manifest 정합성 확인

```bash
jq -r '.plugins[].name' .claude-plugin/marketplace.json | sort > /tmp/mk-claude.txt
jq -r '.plugins[].name' .agents/plugins/marketplace.json | sort > /tmp/mk-codex.txt
ls plugins | sort | diff - /tmp/mk-claude.txt && diff /tmp/mk-claude.txt /tmp/mk-codex.txt
for d in plugins/*/; do n=$(basename $d); [ "$(jq -r .version $d.claude-plugin/plugin.json)" = "$(jq -r .version $d.codex-plugin/plugin.json)" ] || echo "VERSION MISMATCH: $n"; done
```

기대값: diff와 `VERSION MISMATCH`가 한 줄도 나오지 않는다. marketplace `plugins[]`에는 version을 두지 않는다.

manifest를 임의로 바꾸지 않는다. manifest 변경이 작업 범위에 포함되어 있는 경우에만 수정한다.

### Step 6 - 최종 검증

최소 검증:

```bash
test -f plugins/project-setup/skills/update-project-docs/SKILL.md
rg -n 'AGENTS.md|\.claude/CLAUDE.md|marketplace.json|docs/catalog.md|README.md' plugins/project-setup/skills/update-project-docs/SKILL.md
```

문서 갱신 작업까지 수행했다면 추가로 확인한다:

```bash
find plugins -mindepth 4 -maxdepth 4 -path '*/skills/*' -name SKILL.md -print | sort
rg -n '\(\.\./plugins/[^)]+/SKILL\.md\)' docs/catalog.md
jq empty .claude-plugin/marketplace.json .agents/plugins/marketplace.json plugins/*/.claude-plugin/plugin.json plugins/*/.codex-plugin/plugin.json
```

검증 출력에는 실행한 명령과 stdout/stderr를 남긴다. 기존 evidence, report, log는 신뢰하지 말고 현재 작업 후 직접 실행한 결과만 사용한다.

## 보고 형식

작업을 끝내면 다음을 짧게 보고한다:

- 변경된 파일
- 실행한 정확한 명령
- evidence artifact 경로
- cleanup 결과
- 남은 risk 또는 scope 밖이라 건드리지 않은 항목

## 하지 말 것

- `plugins/*/skills/` 밖의 plugin-local `SKILL.md`를 현재 활성 skill로 문서화하지 않는다.
- 빈 `architecture-html-dashboard` 디렉토리를 plugin skill로 승격하지 않는다.
- `templates/`를 plugin skill 목록에 포함하지 않는다.
- `plugin.json`을 범위 밖 작업으로 임의 수정하지 않는다.
- 스캔 대상을 넓혀 중복 skill copy를 다시 정식 루트처럼 취급하지 않는다.
