# 테스트 시나리오 포맷

ui-test-runner 는 다음 3가지 입력 중 하나를 받는다.

## A) Markdown 시나리오 (사람이 쓰기 편한 형식, **권장**)

```markdown
# 시나리오: 사용자 관리 화면

baseUrl: http://localhost:5173
auth: none   # none | preloaded (사용자 직접 로그인) | manual

## TC-001 사용자 목록 조회
url: /users
steps:
  - goto
  - 화면에 "사용자 목록" 텍스트가 보이는지 확인
  - 테이블 row가 1개 이상 렌더링 되었는지 확인
expected: 사용자 목록 테이블이 비어있지 않다

## TC-002 사용자 생성 (mutation, 백엔드 호출은 차단됨)
url: /users
steps:
  - goto
  - "신규 등록" 버튼 클릭
  - 모달이 열리는지 확인
  - 이름 input에 "홍길동" 입력
  - 이메일 input에 "hong@example.com" 입력
  - "저장" 버튼 클릭
expected:
  - 모달이 닫힌다
  - 토스트 "저장되었습니다"가 표시된다
  - POST /api/users 가 mockedRequests 에 1건 기록되어 있다

## TC-003 에러 응답 시 토스트 노출
url: /users
mockOverrides:
  - urlPattern: "/api/users$"
    method: POST
    response:
      status: 500
      body:
        error: "internal_error"
steps:
  - goto
  - "신규 등록" 클릭
  - 이름 "x" 입력 → "저장" 클릭
expected:
  - 에러 토스트가 보인다
  - 모달은 여전히 열려있다
```

## B) JSON 시나리오 (자동화/스크립트에서 생성하기 좋은 형식)

```json
{
  "baseUrl": "http://localhost:5173",
  "auth": "none",
  "cases": [
    {
      "id": "TC-001",
      "name": "사용자 목록 조회",
      "url": "/users",
      "steps": ["goto", "assert text '사용자 목록'", "assert row count > 0"],
      "expected": "사용자 목록 테이블이 비어있지 않다",
      "mockOverrides": []
    },
    {
      "id": "TC-002",
      "name": "사용자 생성",
      "url": "/users",
      "data": { "name": "홍길동", "email": "hong@example.com" },
      "steps": [
        "goto",
        "click '신규 등록'",
        "fill '이름' '홍길동'",
        "fill '이메일' 'hong@example.com'",
        "click '저장'"
      ],
      "expected": [
        "모달이 닫힌다",
        "토스트 '저장되었습니다'",
        "mockedRequests 에 POST /api/users 가 있다"
      ]
    }
  ]
}
```

## C) URL 목록 (smoke test 만 수행)

```text
http://localhost:5173/
http://localhost:5173/users
http://localhost:5173/settings
```

이 경우 각 URL에 대해 자동으로 다음 smoke 체크만 수행:
- `goto` 성공 (HTTP 200, no navigation error)
- `document.title` 이 비어있지 않음
- console 에 error 레벨 로그가 0건
- 페이지에 보이는 visible text가 일정 길이 이상

## 화면 기능 명세에서 시나리오 도출

명세 markdown(예: PRD, 화면 설계서)이 주어지면 다음 휴리스틱으로 시나리오를 만든다.

| 명세에 등장하는 표현 | 도출되는 케이스 |
|---|---|
| "~~ 목록을 보여준다" | 해당 url 진입 + 리스트 렌더 확인 |
| "~~ 등록/생성 버튼" | 버튼 클릭 → 모달/폼 노출 → 저장 → 토스트 |
| "~~ 수정" | 행 선택 → 수정 모드 → 변경 → 저장 |
| "~~ 삭제" | 삭제 버튼 → 확인 모달 → 확인 → 토스트 |
| "검색/필터 가능" | 검색어 입력 → 결과 변화 확인 |
| "권한 없는 사용자는 ~~" (인증 분리) | 사전 로그인 상태에서만 수행, 케이스 분리 |

명세에서 케이스를 만들 때는 사용자에게 한 번 확인 후 진행한다:
> "명세에서 N개의 테스트 케이스를 도출했습니다. 진행할까요? (목록 출력)"
