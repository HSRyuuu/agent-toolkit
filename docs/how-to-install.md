# 설치 · 업데이트 · 배포

`agent-toolkit` 플러그인을 머신에 올리고, 바꾼 내용을 다른 머신까지 전달하는 방법.

대상 범위: Claude Code / Codex · marketplace `hsryuuu` · plugin `agent-toolkit`

## 설치

설치 방식은 두 가지이며 **한 머신에는 하나만** 쓴다. 둘 다 설치하면 스킬이 중복
로드된다.

### 방식 1 — GitHub에서 설치 (일반 사용)

클론이 필요 없다. 두 도구 모두 저장소를 자체 캐시에 복사한다.

Claude Code — 채팅창에 입력한다.

```text
/plugin marketplace add HSRyuuu/agent-toolkit
/plugin install agent-toolkit@hsryuuu
```

Codex — 터미널에서 실행한다.

```bash
codex plugin marketplace add HSRyuuu/agent-toolkit
codex plugin add agent-toolkit@hsryuuu
```

### 방식 2 — 로컬 디렉토리로 설치 (개발 머신)

스킬을 직접 편집하는 머신에서는 클론을 directory marketplace로 등록한다. 파일을
고치면 다음 세션부터 바로 반영되고, 버전 범프나 push가 필요 없다.

```bash
git clone https://github.com/HSRyuuu/agent-toolkit.git
cd agent-toolkit
pwd # ~/your-dir/agent-toolkit
```

Claude Code — 채팅창에 입력한다.

```text
/plugin marketplace add ~/your-dir/agent-toolkit
/plugin install agent-toolkit@hsryuuu
```

Codex — 터미널에서 실행한다.

```bash
codex plugin marketplace add ~/your-dir/agent-toolkit
codex plugin add agent-toolkit@hsryuuu
codex plugin list --available --json
```

Claude Code는 `.claude-plugin/plugin.json`, Codex는 `.agents/plugins/marketplace.json`과
`.codex-plugin/plugin.json`을 사용한다. 두 도구 모두 활성 스킬 루트는 `skills/`
하나이며, 모든 플러그인 스킬은 `skills/<name>/SKILL.md` 형태로 둔다.

## 업데이트 (GitHub 설치 시)

서드파티 marketplace는 자동 업데이트가 기본으로 꺼져 있으므로 직접 실행한다.

```bash
# Claude Code — 카탈로그 갱신 후 플러그인 업데이트
claude plugin marketplace update hsryuuu
claude plugin update agent-toolkit@hsryuuu
claude plugin details agent-toolkit@hsryuuu

# Codex — 마켓플레이스 스냅샷 갱신
codex plugin marketplace upgrade hsryuuu
codex plugin list
```

`details` / `list`가 보고하는 버전이 방금 배포한 버전과 같아야 한다.

로컬 디렉토리 설치는 버전 범프 없이 다음 세션부터 편집 내용이 반영된다.

## 버전이 캐시 키다

두 도구 모두 플러그인 `version`을 캐시 키로 쓴다.

```text
~/.claude/plugins/cache/hsryuuu/agent-toolkit/<version>/
~/.codex/plugins/cache/hsryuuu/agent-toolkit/<version>/
```

그래서 **push만으로는 설치된 머신에 아무 변화가 없다. 버전 범프가 곧 릴리스다.**

- `.claude-plugin/plugin.json`과 `.codex-plugin/plugin.json`의 `version`을 **같은
  값으로** 올린다. 기본은 patch, 기능 단위 릴리스면 minor.
- `marketplace.json`의 `plugins[]`에는 version을 넣지 않는다. 넣으면 `plugin.json`
  값이 경고 없이 이기고 캐시 디버깅이 꼬인다.

## 배포

이 저장소의 변경을 다른 머신까지 전달하는 절차는 프로젝트 로컬
`publish-workflow` 스킬이 소유한다. 순서는 verify-secrets → 커밋 → 버전 범프 →
`git push origin main` → 위 업데이트 명령.

다른 머신은 이 루프에서 닿지 않는다. 각 머신에서 업데이트 명령을 직접 실행해야
한다.

## 문제 해결

증상은 대부분 **소스 / 설치 스냅샷 / 실행 중인 세션** 세 곳이 어긋난 것이다.

| 증상 | 원인 | 대응 |
| --- | --- | --- |
| 업데이트가 "already at the latest version"인데 버전 번호가 옛것 | 범프 커밋이 `origin main`에 안 갔다 | push를 고친다. 캐시를 지우지 않는다 |
| `plugin details`엔 새 스킬이 보이는데 실제 호출은 옛 내용 | `details`는 소스를 직접 읽고, 실행은 버전 스냅샷에서 나온다 | 버전을 범프한다 |
| 스냅샷은 최신인데 세션에 안 보임 | 실행 중인 세션은 재로드하지 않는다 | 새 세션을 연다 |
| 한쪽 도구만 최신 | 두 도구는 캐시와 등록 파일이 별개다 | 각 도구에서 따로 업데이트한다 |

전체 캐시 트리를 지우지 않는다. 지워야 한다면 `<marketplace>/<plugin>/<version>`
경로까지만 지운다.

플러그인이 아예 로드되지 않거나 다른 로컬 플러그인에서 같은 증상이 나면
`local-plugin-manager` 스킬을 쓴다.
