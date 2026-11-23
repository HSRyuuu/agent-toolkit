# Daily Work Log 사용자 설정

사용자가 바꿀 수 있는 값과 그 값을 에이전트가 적용하는 방법을 정리한다. 설정은 `~/.daily-work-log/config.json`과 템플릿 파일 두 곳에 둔다.

## 설정 항목

| 항목 | 설명 | 예시 값 |
|---|---|---|
| `impact-items` | 문서 맨 위 `## Impact`에 모을 라벨과 각 라벨이 찾을 근거 | `[{"name": "TODO", "description": "완결되지 않은 것으로 보이는 것"}]` |
| 본문 템플릿 | `~/.daily-work-log/daily-work-log-template.md`. `###` 항목의 부가 슬롯과 자유 형식 영역을 바꿀 수 있다 | `- 관련 링크` 슬롯 삭제 |
| 수집·검색 한도 | 상위 후보 수, 기타 후보 수, subagent/sidechain 세션 포함 여부, 검색 결과 수 | `"top-limit": 40`, `"other-limit": 10`, `"include-supporting": false`, `"search-limit": 20` |
| `log_root` | 최종 Markdown을 저장하는 로그 루트 | `"/Users/me/work-log"` |

표시 후보는 세션 단위이고 모두 기록에 들어간다. `top-limit`과 `other-limit`을 더한 값이 하루에 보는 세션 수의 상한이다. 한도에 걸려 숨는 것은 점수가 낮은 짧은 세션이라, 기본값은 넉넉하게 잡혀 있다. 숨긴 후보가 있으면 `evidence.md` 맨 위에 개수가 나온다.

본문 템플릿에서 frontmatter 4개 필드, `# YYYY-MM-DD 업무 기록` 제목, `## 한눈에 보기`와 표, `###` 항목의 `요약:`, `<!-- 이 아래는 자유 형식 -->` 마커는 바꿀 수 없다. 상세 규칙은 `references/how-to-set-template.md`를 따른다.

## config.json 예시

```json
{
  "log_root": "/Users/me/work-log",
  "impact-items": [
    {"name": "Jira Ticket", "description": "Jira 이슈 키(예: PROJ-1234)가 언급된 것"},
    {"name": "PR/MR 기록", "description": "생성/머지/리뷰한 PR 또는 MR"}
  ],
  "top-limit": 40,
  "other-limit": 10,
  "include-supporting": false,
  "search-limit": 20
}
```

모든 키는 선택이다. 한도 키(`top-limit`, `other-limit`, `include-supporting`, `search-limit`)가 없으면 위 예시 값이 기본값이다. `impact-items`가 없으면 `## Impact`를 만들지 않는다. `log_root`는 기본값이 없어서, 없으면 SKILL.md "출력 위치" 규칙대로 묻는다.

## 에이전트가 적용하는 방법

| 키 | 적용 방법 |
|---|---|
| `top-limit`, `other-limit`, `include-supporting`, `impact-items` | `build_day_evidence.py`가 `config.json`에서 직접 읽는다. 에이전트가 옵션으로 넘기지 않는다 |
| `search-limit` | 에이전트가 읽어 `search_work_logs.py --limit`으로 넘긴다. 사용자가 이번 검색에서 건수를 말하면 그 값이 우선 |
| `log_root` | 에이전트가 읽어 저장 위치로 쓴다. `search_work_logs.py`는 직접 읽는다 |

## 설정을 바꾸는 방법

사용자는 `config.json`을 직접 고치거나 대화로 요청할 수 있다. 대화로 요청하면 에이전트가 해당 키만 바꾸고 다른 키는 유지한 뒤, 바뀐 값을 한 줄로 알린다. `~/.daily-work-log/` 아래 쓰기는 사전 승인된 것으로 본다. 템플릿 변경은 `references/how-to-set-template.md`의 승인 규칙을 따른다.
