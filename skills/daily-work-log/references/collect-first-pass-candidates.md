# 1차 후보 수집 방법

1차 수집의 목적은 원시 Codex/Claude JSONL과 KB 원문을 LLM이 직접 먼저 읽지 않게 만드는 것이다. 스크립트가 deterministic parser, signal extractor, work-unit extractor, heuristic scorer 역할을 맡고, LLM과 사용자는 압축된 후보 카드 JSON만 본다.

이 스킬의 1차 산출물은 단순 세션 목록이 아니다. 사람이 바로 판단할 수 있도록 각 세션 후보 안에 `work_units`를 포함해야 한다.

## 저장 위치

1차 수집 결과물은 기본적으로 `~/.daily-work-log/YYYY/YYYY-MM-DD/` 아래에 저장한다. 같은 날짜의 2차 상세 탐색과 최종 정보 JSON도 이 디렉터리에 함께 둔다.

```text
~/.daily-work-log/
└── YYYY/
    └── YYYY-MM-DD/
        ├── codex-candidates.json
        ├── claude-candidates.json
        ├── kb-candidates.json
        ├── numbered-candidates.json
        ├── second-pass-digest.json
        └── final-info.json
```

`kb-candidates.json`은 optional이다. KB root가 설정되어 있지 않거나, KB를 찾을 수 없거나, 해당 날짜 후보가 없으면 파일을 만들지 않고 사용자에게도 언급하지 않는다.

이 디렉터리는 도구 상태와 low-level evidence 보관 위치다. 최종 Markdown 업무 기록은 사용자가 지정한 로그 루트 아래 `YYYY/MM/YYYY-MM-DD.md`로 작성한다. 사용자가 `/Users/.../work-log 여기로 해줘`처럼 특정 저장 폴더를 지정하면 `/Users/.../work-log/2026/07/2026-07-02.md`가 된다. 사용자가 `/Users/.../personal 이 아래에 만들어줘`처럼 상위 폴더만 지정하면 `/Users/.../personal/daily-work-log/2026/07/2026-07-02.md`가 된다. 두 해석이 모호하면 최종 Markdown을 쓰기 전에 사용자에게 확인한다.

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

## KB 1차 수집 Optional

KB는 세션 로그가 아니라 사용자가 직접 정리한 지식 문서이므로 optional evidence로만 다룬다. 설정되어 있을 때만 조용히 수집하고, 설정이 없거나 후보가 없으면 생략한다.

```bash
python3 <skill-base-dir>/scripts/collect_kb_first_pass_candidates.py --date YYYY-MM-DD
```

stdout으로 확인만 할 때:

```bash
python3 <skill-base-dir>/scripts/collect_kb_first_pass_candidates.py --date YYYY-MM-DD --stdout --emit-empty
```

스크립트가 수행하는 일:

- KB root를 `--kb-root`, `~/.config/kb/kb-config.json`, `~/.config/kb/path` 순서로 찾는다.
- root가 없거나 유효하지 않으면 아무 출력 없이 종료한다.
- KB의 `log.jsonl`에서 로컬 타임존 기준 대상 날짜 기록을 찾는다.
- Markdown frontmatter의 `created`, `updated`, `date`가 대상 날짜인 문서를 찾는다.
- 문서 제목, summary, path, log evidence를 같은 후보 카드 스키마로 압축한다.
- KB 후보는 `session_id`, `cwd`, `tool_names`처럼 세션 전용 값은 `null`, `[]`, `0`으로 둔다.
- KB 후보의 `work_units`는 문서 생성/수정 또는 log entry 단위로 만든다.

## 후보 카드 스키마

각 후보는 아래 필드를 목표로 한다. 값이 없으면 `null`, 빈 배열, 또는 낮은 confidence로 둔다.

```json
{
  "session_id": "...",
  "source": "codex",
  "file": "/absolute/path/session.jsonl",
  "started_at": "...",
  "last_seen_at": "...",
  "cwd": "...",
  "title_hint": "...",
  "user_intent_snippets": ["..."],
  "result_snippets": ["..."],
  "tool_names": ["exec_command", "apply_patch"],
  "tool_call_count": 42,
  "mentioned_paths": ["src/...", "README.md"],
  "has_edit_signal": true,
  "has_git_signal": true,
  "has_test_signal": true,
  "has_error_signal": false,
  "classification_hints": ["work-item", "verification"],
  "importance_score": 84,
  "first_pass_summary": "작업공간 A에서 '기능 A 정리' 관련 작업으로 보임. 도구: exec_command, apply_patch. 신호: 수정, 테스트.",
  "confidence": "high",
  "work_units": [
    {
      "work_unit_id": "codex:019f...:1",
      "title": "작업공간 A - 기능 A 정리",
      "user_request": "기능 A의 동작 규칙을 정리하고 싶다",
      "outcome": "기능 A의 데이터 구조와 표시 정책을 정리한 것으로 보임",
      "changed_paths": ["src/..."],
      "mentioned_paths": ["src/...", "README.md"],
      "commands": ["pnpm test", "git commit ..."],
      "git_evidence": ["git commit ...", "commit:b3f865b"],
      "test_evidence": ["pnpm test"],
      "tool_names": ["exec_command", "apply_patch"],
      "result_snippets": ["..."],
      "final_answer": "...",
      "classification_hints": ["work-item", "verification"],
      "confidence": "high"
    }
  ]
}
```

Codex, Claude, KB output 파일은 모두 같은 top-level 구조를 사용한다.

```json
{
  "schema_version": "daily-work-log.first-pass.v1",
  "date": "2026-07-02",
  "source": "codex",
  "stage": "first-pass-collection",
  "generated_at": "...",
  "candidates": [],
  "supporting": [],
  "rejected": []
}
```

없는 값은 타입별로 일관되게 비운다.

- 문자열인데 모름 또는 해당 없음: `null`
- 배열인데 없음: `[]`
- 실제 개수 값이 0개: `0`
- 측정할 수 없는 숫자: `null`
- boolean 신호가 감지되지 않음: `false`
- 객체인데 없음: `{}`

`work_units`가 비어 있으면 사람이 판단하기 어렵다. 그런 후보는 `first_pass_summary`만으로 일지에 쓰지 말고, 원시 세션을 추가 추출하거나 사용자에게 확인한다.

## 점수화 기준

스크립트는 LLM 없이 아래 기준으로 `importance_score`를 계산한다.

`importance_score`는 100점 만점이 아니다. 신호가 많은 후보는 100을 넘을 수 있으며, 후보 간 정렬을 위한 가산형 점수로 사용한다.

- 깨끗한 사용자 요청 있음: `+30`
- 도구 호출 있음: `+15`
- 수정 신호 있음: `+20`
- git/commit/push 신호 있음: `+15`
- 테스트 실행 신호 있음: `+10`
- 에러/트러블슈팅 신호 있음: `+20`
- assistant 결과 힌트 있음: `+15`
- subagent/sidechain: `-25`
- 스킬 본문 로딩만 있음: `-20`
- interrupted 후 결과 없음: `-15`

에러/트러블슈팅 신호는 회고와 검색 가치가 높기 때문에 도구 호출보다 강하게 본다. 다만 단순히 문서 안의 `error handling` 같은 표현까지 과대평가될 수 있으므로, 최종 일지 작성 전에는 `work_units[].outcome`과 사용자 요청을 함께 확인한다.

`cwd`는 점수에 반영하지 않는다. 작업공간 경로는 중요도 신호가 아니라 표시, 묶기, 중복 제거에 쓰는 메타데이터로만 사용한다.

분류:

- `80+`: 사용자가 보면 바로 기억할 가능성이 높은 후보
- `50-79`: 보여줄 만한 후보
- `25-49`: supporting 후보
- `<25`: rejected 후보

## LLM 처리 규칙

- 원시 JSONL을 먼저 읽지 않는다.
- 먼저 `~/.daily-work-log/YYYY/YYYY-MM-DD/*-candidates.json`만 읽는다.
- 사용자에게는 `candidates[].work_units`를 우선 보여주고, 필요할 때만 세션 단위 요약과 `supporting`을 참고한다.
- `rejected`는 사용자가 요청하거나 후보가 부족할 때만 확인한다.
- `first_pass_summary`는 확정 사실이 아니라 스크립트 기반 추정이다. 최종 일지에 쓰기 전 `work_units`, 사용자 선택, 추가 근거로 확인한다.
- KB 후보 파일이 없으면 KB가 없었다고 말하지 않는다. 해당 날짜에 쓸 만한 KB 후보가 있을 때만 Codex/Claude 후보와 함께 보여준다.
- 사용자가 후보를 선택하면 `references/collect-second-pass-details.md`를 읽고 선택된 후보만 2차 상세 탐색한다.

## 1차 수집 후 응답 형식

1차 수집을 실행한 뒤 사용자에게는 상위 몇 개만 보여주지 않는다. 기본 응답은 아래 순서를 따른다.

1. 결과 파일 경로를 먼저 보여준다.
2. Codex/Claude 각각의 `candidates`, `supporting`, `rejected`, 전체 `work_units` 수를 보여준다.
3. 그룹핑·번호·제목은 `numbered-candidates.json`의 `displayed_candidates`를 유일한 source of truth로 삼고, LLM은 사용자에게 보여줄 요약 문구만 다듬는다.
4. 상위 후보 목록에 들어가지 않았지만 쓸만한 후보가 있으면 “기타 후보 목록”에 최대 3개까지만 제안한다.
5. 상위 후보와 기타 후보를 합친 전체 표시 후보에 하나의 연속 번호를 부여한다. 기타 후보도 사용자가 번호로 선택할 수 있어야 한다.
6. 마지막에는 사용자가 고를 수 있게 “어떤 번호를 오늘 일지에 포함할까요?”라고 묻는다.

예시:

```markdown
2026-07-02 1차 수집 완료.

결과 파일:
- Codex: `~/.daily-work-log/2026/2026-07-02/codex-candidates.json`
- Claude: `~/.daily-work-log/2026/2026-07-02/claude-candidates.json`
- KB: `~/.daily-work-log/2026/2026-07-02/kb-candidates.json`

수집량:
- Codex: candidates 16, work units 94
- Claude: candidates 9, supporting 1, work units 26
- KB: candidates 7, work units 7

상위 후보 목록:
Codex
1. user-module - 사용자 도메인 구조와 레이어 책임 정리, 문서/수정 신호
2. event-worker - Kafka 연동 문제 원인 확인과 재처리 흐름 점검, 에러/테스트 신호
3. admin-ui - 목록 필터 동작 규칙 개선, 수정/git/테스트 신호
4. local-dev - 패키지 매니저 버전과 로컬 실행 방법 정리, 설정/검증 신호

Claude
5. docs-vault - 업무 문서 분류 기준 정리, 문서 수정 신호
6. support-note - 회의 메모와 후속 요청사항 정리, 업무 기록 신호
7. auth-flow - 로그인 흐름 질문 정리와 참고 자료 확인, 조사 신호

기타 후보 목록:
8. batch-job - 배치 실행 조건 확인, 낮은 confidence
9. onboarding-note - 참고 자료 위치 확인, supporting 후보
```

KB 파일이 생성되지 않았거나 비어 있으면 예시의 KB 결과 파일과 수집량 줄은 표시하지 않는다.

`기타 후보 목록`에는 상위 후보와 중복된 항목을 넣지 않는다. 기타 후보도 전역 번호를 유지한다. `<turn_aborted>`만 남은 후보, `local-command-*` 로그인/훅 확인 노이즈, `Continue from where you left off` 같은 단독 재개 신호는 기본적으로 숨긴다.

## 번호 후보 JSON 생성

사용자에게 후보 목록을 보여주기 전에는 Codex/Claude/KB 1차 수집 결과를 합쳐 번호가 부여된 `numbered-candidates.json`을 만든다.

```bash
python3 <skill-base-dir>/scripts/build_numbered_candidates.py --date YYYY-MM-DD
```

기본 출력:

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/numbered-candidates.json
```

이 파일의 `displayed_candidates`가 사용자에게 보여줄 후보 목록의 source of truth다. 응답에서 후보 번호, 제목, `list_section`, 근거 요약은 이 파일에서 가져온다. 사용자가 나중에 "4,5,6"처럼 번호로 선택하면 반드시 같은 `numbered-candidates.json`의 번호를 기준으로 2차 상세 탐색을 시작한다.

`numbered-candidates.json`은 상위 후보와 기타 후보 모두에 연속 번호를 부여한다. 따라서 사용자가 기타 후보를 고르더라도 별도 `extra_items`나 `selected-candidates.json` 없이, 최종 `final-info.json`의 `selected_candidates` 배열에 같은 방식으로 기록할 수 있다.

그룹핑은 세션 단위(Codex/Claude)와 KB 문서 단위만 사용한다. 한 업무 주제가 여러 세션에 걸치면 그룹이 나뉠 수 있으며, 이 경우에도 번호와 그룹 자체는 `displayed_candidates`를 그대로 따른다.
