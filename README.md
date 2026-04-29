# hsryuuu-toolkit

> 개인용 Claude Code plugin. 스킬·에이전트·훅·커맨드를 한 곳에 모아 일상 워크플로우에 쓴다.

## 로컬 세팅

아직 공용 marketplace에 올리지 않은 상태라, 이 디렉토리를 **로컬 directory marketplace**로 등록해서 사용한다.

### 1. 저장소 가져오기

원하는 위치에 clone 한다. (예시 경로는 본인 환경에 맞게)

```bash
git clone https://github.com/happyhsryu/hsryuuu-toolkit.git ~/dev/personal/hsryuuu-toolkit
```

### 2. Claude Code에 marketplace 등록

Claude Code 안에서 슬래시 커맨드로 등록한다.

```
/plugin marketplace add ~/dev/personal/hsryuuu-toolkit
/plugin install hsryuuu-toolkit@hsryuuu-toolkit-local
```

또는 `~/.claude/settings.json`을 직접 편집해도 된다.

```json
{
  "extraKnownMarketplaces": {
    "hsryuuu-toolkit-local": {
      "type": "directory",
      "path": "/Users/<you>/dev/personal/hsryuuu-toolkit"
    }
  },
  "enabledPlugins": {
    "hsryuuu-toolkit@hsryuuu-toolkit-local": true
  }
}
```

### 3. 확인

새 Claude Code 세션을 띄우면 `skills/`, `skills-workflow/`, `skills-system/`에 있는 모든 스킬이 자동 로드된다. `/plugin` 으로 활성 상태를 확인할 수 있다.

> 디렉토리를 그대로 편집하면 다음 세션부터 반영된다 — 별도 빌드/배포 단계 없음.

## 무엇이 들어 있나

- **skills/** — 독립 스킬 (현재 8개)
- **skills-workflow/** — 워크플로우 스킬 (현재 0개)
- **skills-system/** — 메타·스캐폴딩 스킬 (현재 3개)

전체 스킬 목록과 트리거는 [docs/catalog.md](docs/catalog.md) 참고.

## 어떻게 로드되나

로컬 directory marketplace(`hsryuuu-toolkit-local`)로 등록되어 있어,
이 디렉토리를 그대로 편집하면 다음 Claude Code 세션부터 반영된다.

자세한 정책·디렉토리 분류 기준은 [.claude/CLAUDE.md](.claude/CLAUDE.md) 참고.

## 저장소 갱신

스킬을 추가/이동/삭제했으면 `update-project-docs` 스킬로 문서를 동기화한다.
