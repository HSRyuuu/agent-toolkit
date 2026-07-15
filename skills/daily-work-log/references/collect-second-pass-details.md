# 2차 상세 탐색 방법

2차 상세 탐색의 목적은 사용자가 고른 1차 후보만 다시 확인해서 최종 업무 기록에 쓸 수 있는 안전한 정보 JSON을 만드는 것이다.

1차 후보의 `first_pass_summary`와 `work_units[].outcome`은 스크립트 기반 추정이다. 최종 Markdown에 바로 쓰지 말고, 선택된 후보의 세션 digest, KB 문서, 관련 파일 경로를 확인해 사실과 추정을 분리한다.

## 저장 위치

2차 산출물은 1차 후보와 같은 날짜 디렉터리에 저장한다.

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

`final-info.json`은 최종 Markdown 초안 작성의 직접 입력이다. 사용자가 고른 후보 목록은 별도 파일로 만들지 않고 `final-info.json`의 최상위 `selected_candidates` 배열에 함께 기록한다. 1차 응답의 상위 후보와 기타 후보는 모두 번호를 가지므로, 기타 후보를 선택한 경우에도 같은 배열에 기록한다.

## Impact 항목 확인

`build_second_pass_digest.py`를 실행하기 전에, 사용자에게 현재 등록된 `impact-items`를 안내하고 추가/수정/삭제 여부를 매번 확인한다. 변경 요청이 있으면 `config.json`을 먼저 갱신한 뒤 다음 단계로 진행한다. 안내 문구, 확인 시점을 여기에 두는 이유는 SKILL.md의 "Impact 항목 확인" 절을 따른다.

## 스크립트 기반 2차 흐름

사용자 선택 이후에는 먼저 선택 번호를 저장된 `numbered-candidates.json`에 대해 해석한다.

```bash
python3 <skill-base-dir>/scripts/build_second_pass_digest.py --date YYYY-MM-DD --selection 4,5,6
```

기본 출력:

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/second-pass-digest.json
```

`second-pass-digest.json`은 선택된 후보가 가리키는 work unit, 세션 파일, KB 문서, 관련 파일 경로, 명령/test/git 근거만 압축한다. 이 파일은 LLM이 원시 JSONL 전체를 다시 읽지 않게 하기 위한 중간 자료다.

그 다음 final-info skeleton을 만든다.

```bash
python3 <skill-base-dir>/scripts/build_final_info_skeleton.py --date YYYY-MM-DD
```

기본 출력:

```text
~/.daily-work-log/YYYY/YYYY-MM-DD/final-info.json
```

이 skeleton은 초안이다. 스크립트는 `category`를 중립 기본값 `work-item`으로 두고, `technical_context.modules`, `technical_context.systems`, `technical_context.tech_stack`, `technical_context.context_links`, `markdown_hints.include_keywords`를 비워 둔다. LLM은 `second-pass-digest.json`과 필요한 최소 근거만 확인해 이 빈 슬롯과 `summary`, `why_it_mattered`, `decisions`, `learnings`, `troubleshooting`, `follow_ups`, `uncertainties`를 보강한다.

## 선택 후보 기록

사용자가 "4,5,6"처럼 후보를 고르면, 선택 내용을 후보 묶음 단위로 `final-info.json` 안에 기록한다.

```json
{
  "selected_candidates": [
    {
      "group_id": "4",
      "title": "API 응답 정책 정리",
      "list_section": "top",
      "selection_note": "사용자가 오늘 일지에 포함하도록 선택함",
      "candidate_refs": [
        {
          "source": "codex",
          "session_id": "...",
          "file": "/absolute/path/session.jsonl",
          "work_unit_ids": ["codex:...:1"]
        }
      ],
      "kb_paths": ["dev/concepts/api-response-policy.md"]
    }
  ]
}
```

후보 번호는 사용자에게 보여준 목록의 번호다. 번호만 저장하지 말고 제목, 세션 파일, `work_unit_ids`, 관련 KB 경로를 함께 남긴다. `list_section`은 `top` 또는 `other`를 사용한다. 이 배열은 "왜 이 항목들을 2차 상세 탐색했는가"를 설명하는 선택 이력이다.

## 상세 탐색 입력

선택된 후보별로 아래 자료만 깊게 본다.

- 저장된 `numbered-candidates.json`
- 선택 번호로 만든 `second-pass-digest.json`
- 선택 후보가 가리키는 Codex/Claude 세션 파일
- 선택 후보의 `work_unit_ids`
- 1차 후보에 나온 `mentioned_paths`, `changed_paths`
- 선택 후보와 직접 연결된 KB 문서
- 사용자가 명시한 회의 메모, 계획서, 트러블슈팅 문서

선택되지 않은 후보는 최종 문서에 쓰지 않는다. 단, 선택 후보의 이해에 필요한 supporting evidence로만 짧게 참조할 수 있다.

## 최종 정보 JSON

`final-info.json`은 아래 구조를 사용한다.

```json
{
  "schema_version": "daily-work-log.final-info.v1",
  "date": "2026-07-02",
  "generated_at": "...",
  "markdown_generation_policy": {
    "purpose": "사용자가 하루 뒤/몇 주 뒤에 읽어도 어떤 일을 했는지 기억할 수 있는 일일 업무 기록을 만든다.",
    "include": [
      "업무를 식별할 수 있는 프로젝트, repo, 모듈, 시스템, 기술 스택",
      "조사/판단/문서화/트러블슈팅의 높은 수준 요약",
      "다시 찾아볼 수 있는 근거 파일 경로와 링크"
    ],
    "exclude": [
      "구체적인 회사 소스코드",
      "긴 원문 로그",
      "고객 식별자",
      "인증 정보와 secret 원문",
      "운영 데이터 원문"
    ]
  },
  "source_files": {
    "first_pass": [
      "~/.daily-work-log/2026/2026-07-02/codex-candidates.json",
      "~/.daily-work-log/2026/2026-07-02/claude-candidates.json",
      "~/.daily-work-log/2026/2026-07-02/kb-candidates.json"
    ]
  },
  "impact": {
    "impact_items": ["Jira Ticket", "PR/MR 기록", "최종 개발 결정 사항"],
    "findings": {
      "Jira Ticket": [],
      "PR/MR 기록": [],
      "최종 개발 결정 사항": []
    }
  },
  "selected_candidates": [
    {
      "group_id": "4",
      "title": "API 응답 정책 정리",
      "list_section": "top",
      "selection_note": "사용자가 오늘 일지에 포함하도록 선택함",
      "candidate_refs": [
        {
          "source": "codex",
          "session_id": "...",
          "file": "/absolute/path/session.jsonl",
          "work_unit_ids": ["codex:...:1"]
        }
      ],
      "kb_paths": ["dev/concepts/spring-cloud-config-server.md"]
    }
  ],
  "selected_items": [
    {
      "item_id": "config-server-structure",
      "selected_group_id": "4",
      "title": "API 응답 정책 정리",
      "category": "work-item",
      "summary": "무엇을 했는지 한두 문장으로 정리한다.",
      "memory_cue": "나중에 읽었을 때 사용자가 이 일을 떠올릴 수 있는 짧은 회상 단서이다.",
      "what_i_did": [],
      "why_it_mattered": "",
      "technical_context": {
        "repo_names": [],
        "codebase_paths": [],
        "modules": [],
        "systems": [],
        "tech_stack": [],
        "context_links": []
      },
      "decisions": [],
      "learnings": [],
      "troubleshooting": [],
      "follow_ups": [],
      "uncertainties": [],
      "markdown_hints": {
        "detail_level": "normal",
        "include_keywords": [],
        "avoid_details": []
      },
      "evidence_paths": {
        "session_files": [],
        "kb_documents": [],
        "project_files": [],
        "notes": []
      },
      "safe_evidence_summary": [],
      "confidence": "high"
    }
  ]
}
```

`memory_cue`는 최종 Markdown에 그대로 쓰기 위한 문장이 아니라, 초안 작성자가 "이 항목이 무슨 일이었는지" 빠르게 이해하는 회상 단서다. `technical_context`에는 Confluence 링크, repo 이름, 코드베이스 경로, 모듈명, 기술 스택처럼 업무 식별에 도움이 되지만 민감 구현 세부는 아닌 정보를 넣는다.

`impact`는 `~/.daily-work-log/config.json`의 `impact-items`가 설정된 경우에만 skeleton에 존재한다(비어있으면 이 키 자체가 없다). LLM은 각 `selected_items`의 `decisions`, `learnings` 등을 채우는 것과 같은 패스에서 선택 후보 원문(second-pass digest, 필요하면 원본 세션 work unit)을 함께 확인해 `impact.findings`의 각 라벨에 해당하는 근거를 찾아 채운다. 하루치 항목 전체를 가로지르는 day-level 요약이므로 특정 `selected_items` 하나에 종속시키지 않는다. 근거를 찾지 못한 라벨은 빈 배열로 남기고 지어내지 않는다.

## 최종 Markdown 근거 방식

최종 Markdown에는 긴 원문 발췌보다 참조 모음을 우선 남긴다.

`impact.impact_items`가 존재하고 `impact.findings`에 하나 이상 값이 있으면, frontmatter와 `# YYYY-MM-DD 업무 기록` 제목 다음·`## 한눈에 보기`보다 위에 `## Impact`를 먼저 둔다. 근거가 없는 라벨은 생략하고, 모든 라벨이 비면 `## Impact` 자체를 생략한다. repo에 종속된 근거(PR/MR 기록, branch 등)는 repo별로 묶어서 표기한다. 상세 규칙과 예시는 `SKILL.md`의 "Impact 섹션 (opt-in)"을 따른다.

`## Impact` 다음(또는 `impact`가 없으면 제목 바로 다음)에 `## 한눈에 보기`를 둔다. `## 한눈에 보기`에는 선택된 작업 목록을 `| 구분 | 제목 | 요약 |` 표로 요약한다. 별도의 `## 작업 요약` 섹션은 만들지 않고, 표 바로 아래에 각 선택 항목을 `### 항목 제목`으로 작성한다.

각 `###` 항목은 요약이 중심이다. `###` 제목 바로 아래에 `요약:`을 필수로 두고, 그 아래에 `- 구분:`과 참조 목록(`코드 경로`, `관련 파일`, `관련 링크`)을 필요한 것만 둔다. 맥락, 진행/확인, 판단/배운 점, 결론, 남은 일 같은 상세 소제목은 `###` 항목 안에 고정 슬롯으로 넣지 않는다. 참조 목록은 2-depth list까지 허용하고, 그 외 본문은 불필요하게 깊은 중첩 목록을 만들지 않는다.

Markdown 초안 작성 중에는 `<!-- 이 아래는 자유 형식 -->` 주석 마커를 사용해 요약 영역과 자유 형식 상세 영역을 구분할 수 있다. 마커 위쪽 `###` 항목들은 최대한 요약으로 유지하고, 각 항목의 상세 내용(맥락, 진행 과정, 판단 근거, 배운 점, 남은 일 등)은 에이전트가 이 마커 아래에 자유 형식으로 작성한다. 사용자가 남기고 싶은 메모, 추가 회고, 임시 생각도 이 아래에 둔다. 단, 최종 Markdown 저장본에서는 `<!-- 이 아래는 자유 형식 -->` 주석 라인을 제거하고, 그 아래에 작성한 상세 내용만 일반 본문으로 남긴다.

참조 표기 상세 규칙은 SKILL.md의 "참조 표기 규칙"을 따른다. 이 문서에서는 최종 Markdown에 남길 수 있는 근거의 종류만 요약한다.

권장 근거:

- KB 문서 경로
- 사용자가 직접 작성한 계획/회의/트러블슈팅 문서 경로 (로컬 전용이면 full path)
- 확인한 코드 파일 (repo 이름 + 파일명)
- 커밋 hash 또는 테스트 명령은 필요한 경우 짧게

피해야 할 근거:

- Claude/Codex 세션 파일 경로 (`~/.claude/projects/...`, `~/.codex/sessions/...`) — 캐시성 파일이라 언제든 삭제될 수 있으므로 최종 Markdown에는 넣지 않는다. `final-info.json` 같은 중간 산출물까지만 유지한다.
- git repo 관리 파일의 full path — repo 이름 + 파일명으로 충분하다.
- 원시 JSONL 본문 복사
- 회사 소스코드 긴 인용
- 인증 정보, 고객 식별자, 내부 URL의 불필요한 원문 노출
- Slack/DM 원문 전문

## 항목 분류

각 선택 항목은 하나 이상의 성격을 가질 수 있지만, `category`에는 대표 성격 하나를 둔다.

- `work-item`: 구현, 문서화, 조사, 리뷰 등 일반 업무
- `troubleshooting`: 장애, 에러, 원인 분석, 운영 확인
- `decision`: 아키텍처, 운영 방식, 문서 구조, 전환 방향 결정
- `learning`: 재사용 가능한 개념 이해 또는 학습
- `follow-up`: 후속 작업 중심 항목

## 사용자 확인

2차 상세 탐색 후에는 최종 Markdown을 바로 저장하지 말고, `final-info.json` 요약을 보여준 뒤 확인한다.

확인할 것:

- 선택 항목이 사용자의 의도와 맞는지
- 확정 사실과 추정이 분리됐는지
- 회사명, 시스템명, 내부 경로를 어느 정도까지 남길지
- 각 항목을 자세히 쓸지, 한 줄로 쓸지

사용자가 승인하면 템플릿을 적용해 최종 Markdown 초안을 작성한다. 최종 저장 경로는 사용자가 지정한 로그 루트 아래 `YYYY/MM/YYYY-MM-DD.md`다.

최종 Markdown의 frontmatter 상세 규칙은 SKILL.md의 "필수 Frontmatter"를 따른다. 이 단계에서 작성하는 일일 업무 기록의 `type`은 항상 `daily-work-log`로 둔다.

```text
<log-root>/YYYY/MM/YYYY-MM-DD.md
```

경로 해석 상세 규칙과 `~/.daily-work-log/config.json` 재사용 순서는 SKILL.md의 "출력 위치"를 따른다.
