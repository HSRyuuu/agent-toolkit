# Memory

Use this file when saving to or reorganizing
`~/.config/atlassian-helper/MEMORY.md`.

## 무엇을 남기나

- **프로젝트/스페이스 별칭**: 사용자가 부르는 이름 ↔ 키 (예: "백엔드" → `ABC`)
- **팀/사람**: 자주 검색하는 동료의 표시 이름/이메일
- **자주 쓰는 JQL/CQL**: 재사용 가능한 조각과 용도
- **선호**: 기본 조회 범위, 기본 프로젝트/스페이스, 기본 이슈 타입, "이번 주"
  기준, 사이트마다 다른 상태 이름 등

API token, 이슈/문서 본문 원문, 고객 데이터는 어떤 경우에도 저장하지 않는다.

## 언제 쓰나 — 수동적으로 기다리지 않는다

1. **명시 트리거**: 사용자 메시지에 "기억", "기억해", "기억해줘", "저장해둬",
   "memory", "MEMORY" 같은 단어가 나오면 메모리 요청으로 간주한다. 저장 대상이
   명확하면 묻지 말고 바로 알맞은 섹션에 추가하고 추가된 라인을 그대로
   보고한다. 모호하면 후보 1~3개를 제시하고 한 번만 묻는다. 이미 있으면 기존
   라인을 갱신하거나 "이미 저장되어 있다"고 알린다.
2. **탐색이 끝났을 때**: 조사 과정에서 새로 확인된 프로젝트 키, 스페이스 키,
   별칭, 유효했던 JQL/CQL 패턴이 있으면 마지막 응답에서 저장할지 한 문장으로
   제안한다.
3. 같은 사실을 두 번째 세션에서 다시 발견했다면 즉시 저장을 제안한다.

## 형식

```markdown
# atlassian-helper memory

## 프로젝트/스페이스 별칭
- 백엔드 — ABC — 백엔드 팀 메인 보드
- 개발 위키 — DEV — Confluence 스페이스

## 팀/사람
- 길동 — 홍길동 (hong@example.com)

## 자주 쓰는 JQL
- 스프린트 리뷰 — project = ABC AND sprint in openSprints() AND assignee = currentUser()

## 자주 쓰는 CQL
- 내 최근 문서 — type = page AND creator = currentUser()

## 선호
- 기본 조회 프로젝트는 ABC
```

한 줄에 한 사실, `이름 — 값 — 용도` 순서를 지킨다. 섹션이 없으면 만들고, 파일이
아예 없으면 `atlassian_setup.py init-keys`가 만든 템플릿을 기준으로 채운다.
