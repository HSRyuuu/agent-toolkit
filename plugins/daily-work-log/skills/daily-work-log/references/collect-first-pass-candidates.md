# 1차 후보 수집 방법

1차 수집의 목적은 원시 Codex/Claude JSONL을 LLM이 직접 먼저 읽지 않게 만드는 것이다. 스크립트가 deterministic parser, signal extractor, work-unit extractor, heuristic scorer 역할을 맡고, LLM은 압축된 후보 카드 JSON만 본다.

이 스킬의 1차 산출물은 단순 세션 목록이 아니다. LLM이 원시 세션 없이 업무 단위를 판단할 수 있도록 각 세션 후보 안에 `work_units`를 포함해야 한다.

## 저장 위치

저장 위치와 파일 구성은 SKILL.md "1차 후보 수집"을 따른다. 최종 Markdown 저장 위치는 SKILL.md "출력 위치"를 따른다.

## Codex 1차 수집

Codex 세션은 비교적 구조가 일정하므로 `session_meta`, `response_item.message`, `function_call`, `function_call_output`, `event_msg`를 파싱한다.

```bash
python3 <skill-base-dir>/scripts/collect_codex_first_pass_candidates.py --date YYYY-MM-DD
```

stdout으로 확인만 할 때:

```bash
python3 <skill-base-dir>/scripts/collect_codex_first_pass_candidates.py --date YYYY-MM-DD --stdout
```

스크립트가 수행하는 일:

- 대상 날짜의 전날, 당일, 다음날 `~/.codex/sessions/YYYY/MM/DD/*.jsonl`을 찾고 로컬 타임존 기준 대상 날짜 row가 있는 파일만 쓴다.
- `thread_source == "user"`를 primary 후보로 본다.
- 사용자 요청, assistant 결과 힌트, 도구 이름, 도구 호출 수를 추출한다.
- `apply_patch`, git 명령, test 명령, error 키워드, 파일 경로를 신호로 추출한다.
- 사용자 요청 turn을 기준으로 세션 안의 업무 단위 후보인 `work_units`를 만든다.
- `importance_score`, `classification_hints`, `first_pass_summary`, `confidence`를 계산한다.

## Claude 1차 수집

Claude 세션은 포맷이 더 느슨하므로 tolerant parser를 사용한다.

```bash
python3 <skill-base-dir>/scripts/collect_claude_first_pass_candidates.py --date YYYY-MM-DD
```

stdout으로 확인만 할 때:

```bash
python3 <skill-base-dir>/scripts/collect_claude_first_pass_candidates.py --date YYYY-MM-DD --stdout
```

스크립트가 수행하는 일:

- `~/.claude/projects/**/*.jsonl`을 우선 찾고, 없으면 `~/.claude/**/*.jsonl`을 찾는다.
- 파일 전체를 훑어 로컬 타임존 기준 대상 날짜 row가 있는지 판정하고, 대상 날짜의 `work_units`만 남긴다.
- `message.role`, top-level `type`, `queue-operation`, `ai-title`을 tolerant하게 해석한다.
- `tool_use` block에서 `Read`, `Bash`, `Edit`, `Write`, `MultiEdit`, `Skill`, `Agent` 같은 도구 이름을 추출한다.
- `isSidechain == true` 또는 경로에 `/subagents/`가 있으면 supporting 후보로 낮춘다.
- attachment, mode, last-prompt는 보조 신호로만 사용한다.
- `tool_result`가 user message처럼 저장된 경우 사용자 요청으로 취급하지 않고 근거 신호로만 사용한다.
- 사용자 요청 turn을 기준으로 세션 안의 업무 단위 후보인 `work_units`를 만든다.

## 후보 카드

후보 카드의 필드는 수집 스크립트 출력이 정본이다. 2차 탐색에서는 카드 JSON을 직접 읽지 않고 digest와 `print_digest_group.py`로 본다.

`work_units`가 비어 있으면 사람이 판단하기 어렵다. 그런 후보는 `first_pass_summary`만으로 일지에 쓰지 말고, 원시 세션을 추가 추출해 보강한다. 보강해도 무슨 일인지 알 수 없으면 기록에 넣되 요약에 근거가 약하다고 적고, 완료 보고에서 사용자가 뺄 수 있게 한다.

## 1차 수집 후 진행

1차 수집 결과는 중간에 사용자에게 보여주지 않는다. 기록 목록은 최종 Markdown을 저장한 뒤 SKILL.md의 "완료 보고"에서 한 번만 보여준다.

`numbered-candidates.json`이 표시 후보를 고른다. 상위 후보 다음에 상위 후보에 들지 못했지만 쓸 만한 기타 후보를 기본 5개까지 두고(상위 후보는 기본 15개), 둘을 합친 전체에 하나의 연속 번호를 붙인다. 기타 후보에는 상위 후보와 중복된 항목을 넣지 않는다. `<turn_aborted>`만 남은 후보, `local-command-*` 로그인/훅 확인 노이즈, `Continue from where you left off` 같은 단독 재개 신호는 기본적으로 숨긴다. 하네스가 사용자 메시지 자리에 넣는 블록(`<system-reminder>`, `<local-command-caveat>`, `<recommended_plugins>`, `<task-notification>`, `<fork-source>`, `[Image: ...]`)과 포크·Orca 워커 지시문은 수집 단계의 `clean_user_text`가 사용자 요청에서 지운다.

## 번호 후보 JSON 생성

2차 상세 탐색 전에는 Codex/Claude 1차 수집 결과를 합쳐 번호가 부여된 `numbered-candidates.json`을 만든다.

```bash
python3 <skill-base-dir>/scripts/build_numbered_candidates.py --date YYYY-MM-DD
```

기본 출력:

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/numbered-candidates.json
```

이 파일의 `displayed_candidates`가 기록 대상 목록의 source of truth다. 완료 보고의 번호, 제목, `list_section`은 이 파일에서 가져온다. 사용자가 완료 보고를 보고 "4,5"(날짜가 여럿이면 "10-01 4번")처럼 뺄 번호를 말하면 반드시 같은 `numbered-candidates.json`의 번호로 해석한다.

`numbered-candidates.json`은 상위 후보와 기타 후보 모두에 연속 번호를 부여한다. 따라서 기타 후보도 별도 `extra_items`나 `selected-candidates.json` 없이, 최종 `final-info.json`의 `selected_candidates` 배열에 같은 방식으로 기록할 수 있다.

그룹핑은 세션 단위(Codex/Claude)만 사용한다. 한 업무 주제가 여러 세션에 걸치면 그룹이 나뉠 수 있으며, 이 경우에도 번호와 그룹 자체는 `displayed_candidates`를 그대로 따른다.
