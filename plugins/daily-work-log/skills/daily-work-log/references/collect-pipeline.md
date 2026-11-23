# 수집 파이프라인

`scripts/build_day_evidence.py`가 아래 스크립트를 순서대로 돌리고 `evidence.md`를 만든다. 이 문서는 스크립트를 고치거나 결과가 이상할 때 보는 문서다. 업무 기록을 쓸 때는 읽지 않아도 된다.

```bash
python3 <skill-base-dir>/scripts/build_day_evidence.py --date YYYY-MM-DD
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--top-limit`, `--other-limit` | `config.json` 값, 없으면 40과 10 | 표시 후보 수 |
| `--include-supporting` | `config.json` 값, 없으면 끔 | subagent·sidechain 세션도 후보로 본다 |
| `--render-only` | 끔 | 수집을 다시 돌리지 않고 저장된 digest로 `evidence.md`만 다시 만든다 |
| `--state-root` | `~/.daily-work-log` | 중간 산출물과 `config.json` 위치 |

## 단계

| 순서 | 스크립트 | 출력 | 하는 일 |
|---|---|---|---|
| 1 | `collect_codex_first_pass_candidates.py` | `codex-candidates.json` | Codex 세션을 작업 단위로 나눈다 |
| 2 | `collect_claude_first_pass_candidates.py` | `claude-candidates.json` | Claude 세션을 작업 단위로 나눈다 |
| 3 | `build_numbered_candidates.py` | `numbered-candidates.json` | 세션을 점수순으로 줄 세우고 번호를 붙인다 |
| 4 | `build_second_pass_digest.py` | `second-pass-digest.json` | 표시 후보의 작업 단위를 모으고, 포크 복사본을 거르고, 시간순으로 둔다 |
| 5 | `build_day_evidence.py` | `evidence.md` | 에이전트가 읽을 근거 파일을 쓴다 |

## 수집 규칙

- Codex는 대상 날짜의 전날, 당일, 다음날 `~/.codex/sessions/YYYY/MM/DD/*.jsonl`에서 로컬 타임존 기준 대상 날짜 row가 있는 파일만 쓴다. `thread_source`가 `user`가 아니면 supporting이다.
- Claude는 `~/.claude/projects/**/*.jsonl`을 훑는다. `isSidechain == true`이거나 경로에 `/subagents/`가 있으면 supporting이다.
- 작업 단위는 사용자 요청 한 번과 그 뒤 응답·도구 호출 묶음이다. 대상 날짜에 시작한 단위만 남긴다.
- `tool_result`가 user message처럼 저장된 row는 사용자 요청으로 보지 않는다. 하네스가 사용자 메시지 자리에 넣는 블록(`<system-reminder>`, `<local-command-caveat>`, `<task-notification>`, `[Image: ...]` 등)과 포크·Orca 워커 지시문, 컨텍스트 요약문, 다른 세션이 보낸 메시지, `[Request interrupted by user]`는 `clean_user_text`가 지운다. 그 뒤 응답과 도구 호출은 앞 작업 단위에 붙는다.
- 점수(`importance_score`)가 50 이상인 세션만 후보다. `<turn_aborted>`, `local-command-*`, 단독 재개 신호만 남은 단위는 `build_numbered_candidates.py`가 숨긴다.
- 그룹핑은 세션 단위다. 한 주제가 여러 세션에 걸치면 후보가 나뉘고, 합치는 일은 작성 단계에서 한다.

## 텍스트 한도

한도는 `first_pass_candidate_utils.py`의 상수로만 정한다. 뒤 단계는 다시 자르지 않는다.

| 상수 | 값 | 대상 |
|---|---|---|
| `REQUEST_LIMIT` | 260자 | 사용자 요청 |
| `OUTCOME_LIMIT` | 260자 | 작업 단위의 마지막 응답 |
| `OUTCOME_LONG_LIMIT` | 1,200자 | 세션의 마지막 단위와 커밋·푸시·PR 단위의 마지막 응답 |

한도를 올리면 `evidence.md`가 그만큼 커진다. 1자가 약 0.9토큰이다. 바꾼 뒤에는 바쁜 날짜 하나로 `build_day_evidence.py`를 돌려 출력의 `chars`를 확인한다.

## 근거 필드

작업 단위마다 도구 호출 입력에서 아래 값을 뽑는다. `evidence.md`의 후보 머리에 모아 출력한다.

| 필드 | 출처 |
|---|---|
| `edited_files` | Claude는 `Edit`·`Write`·`MultiEdit`·`NotebookEdit`의 `file_path`, Codex는 `apply_patch`의 `*** Update File:` 줄. `function_call`과 `custom_tool_call`(`exec`) row를 모두 읽는다 |
| `delivery_commands` | 셸 명령 중 `git commit`·`git push`·`git merge`, `gh pr create`·`merge`, `glab mr create`·`merge` |
| `links` | 응답 텍스트에 나온 URL |

`mentioned_paths`, `changed_paths`, `git_evidence`는 세션 텍스트 전체에 정규식을 돌린 값이라 잡음이 많다. 점수 계산에만 쓰고 `evidence.md`에는 내지 않는다.
