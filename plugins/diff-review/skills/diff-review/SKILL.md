---
name: diff-review
description: 현재 브랜치의 변경사항을 사람이 리뷰하기 쉬운 단일 HTML로 만든다. 파일별 요약, 위험도(High/Mid/Low), 변경 메서드 수 정렬, 영향받는 진입점(HTTP API·메시지 리스너·스케줄러), 추가/삭제 파일, side-by-side diff를 한 페이지에 보여준다. Java 프로젝트 전용. Triggers - "diff 리뷰 html", "리뷰용 html 만들어줘", "변경사항 리뷰 페이지", "코드리뷰 보기 좋게", "/diff-review".
---

# diff-review

변경사항 파싱, 메서드 집계, 진입점 추적, HTML 생성은 스크립트가 맡는다.
너는 **파일별 요약과 위험도만** 판단한다. 토큰을 아끼는 것이 이 스킬의 목적이다.

## 1. 수집

```bash
python3 <skill>/scripts/collect.py [--repo .] [--base <ref>]
```

- 기본 비교 대상은 기본 브랜치(`origin/HEAD` → `main` → `master`)와의 merge-base부터 지금 작업 트리까지다. 커밋, staged, unstaged, untracked 변경이 모두 들어간다.
- 출력 첫 줄 `OUT=<폴더>`가 이후 단계의 작업 폴더다.
- 표의 `risk`는 규칙으로 정한 기본값이다(메서드 수, 줄 수, entity/repository/config 같은 경로, 메서드 삭제, 진입점 영향).

## 2. 요약 (네가 하는 일)

- 표에서 `(trivial)` 표시가 없는 파일만 `<OUT>/files/NNN.patch`를 읽는다. 표시가 있는 파일은 읽지 않는다.
- 테스트 파일은 patch를 읽지 말고, `<OUT>/meta.json`의 메서드 목록만 보고 한 줄로 요약한다.
- 진입점은 `meta.json`의 `endpoints`에 이미 들어 있다. 다시 추적하지 않는다.
- `<OUT>/summary.json`을 쓴다. 키는 meta의 `path`다.

```json
{"src/main/java/.../FooService.java": {"s": "무엇이 왜 바뀌었는지 한 문장", "r": "H", "why": "기본값과 다를 때만 근거 한 줄"}}
```

- `r`은 기본값과 다르게 판단할 때만 넣는다. 트랜잭션 경계 변경, 쿼리 조건 변경, 외부 연동 변경, 데이터 삭제 경로는 H 쪽으로 올리고, 이름 변경이나 로그만 바뀐 경우는 L 쪽으로 내린다.

## 3. 생성

```bash
python3 <skill>/scripts/render.py <OUT> --open
```

생성된 `index.html` 경로를 사용자에게 알려준다. 채팅에는 High 파일 목록과 진입점 수만 짧게 적는다.

## 한계

- 진입점 추적은 메서드 이름과 타입 참조를 기준으로 호출자를 거슬러 올라가는 추정이다. 같은 이름의 오버로드, 리플렉션, 프록시 호출은 놓치거나 과하게 잡을 수 있다. 정확한 확인이 필요한 경로만 LSP(call hierarchy)로 따로 확인한다.
- Java 파일만 메서드를 분석한다. 다른 파일은 줄 수와 상태만 보여준다.
