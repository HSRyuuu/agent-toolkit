---
name: excel-ui-test-doc-creator
description: 테스트 시나리오 또는 테스트 수행 결과(JSON/markdown)를 입력받아 단위테스트 산출물 Excel(.xlsx) 파일을 작성할 때 사용한다. 사용자가 제공한 템플릿 xlsx가 있으면 그 양식의 컬럼 구조·스타일을 우선 따르고(한↔영 컬럼명 자동 매칭), 없으면 기본 양식(단위테스트 ID/명/데이터/절차/기대 결과/화면 URL/실제 결과)으로 신규 생성한다. openpyxl로 처리하며 긴 텍스트는 자동 wrap_text, pass/fail 행 색상 차등을 적용한다. 트리거 - "테스트 결과 엑셀로 정리해줘", "단위테스트 산출물 만들어줘", "테스트 시나리오 xlsx로", "QA 테스트 결과서 엑셀", "/excel-ui-test-doc-creator". 사용하지 않을 때 - 기존 양식 xlsx 갱신(`excel-doc-updater`가 우선), PDF/docx 테스트 보고서, 코드 테스트 실행 자체.
---

# excel-ui-test-doc-creator

테스트 시나리오/수행 결과를 받아 단위테스트 산출물 `.xlsx` 한 파일을 만든다. 사용자 템플릿이 있으면 그 양식을 그대로 따르고, 없으면 기본 양식으로 신규 생성한다.

핵심은 **LLM이 추론한 매핑을 절대 그대로 작성하지 않는다**는 점이다. 항상 결정론적 프로파일링 스크립트로 매핑 후보를 산출하고, 사용자 승인을 받은 뒤에만 작성하며, 작성 후엔 다시 결정론적 검증 리포트로 행·셀 단위 일치를 확인한다.

## 절대 규칙 (위반 금지)

### R-A. 사용자 승인 게이트
템플릿이 제공된 경우, **반드시 `profile_template.py`를 먼저 실행**해 (1) 헤더 행, (2) 헤더 ↔ 표준 키 자동 매칭 결과, (3) 미매핑 컬럼, (4) spec 키 중 양식에 없는 항목을 표로 사용자에게 보여주고 **승인을 받은 뒤에만** `create_test_doc.py`를 호출한다. 매핑은 LLM이 머릿속으로 추론하지 않는다.

> 막는 실패 모드: 비슷한 단어(예: "결과"가 두 컬럼에 있을 때)를 LLM이 임의로 한쪽에 붙여 작성. 사용자가 발견하면 전 행을 다시 작성.

### R-B. 결정론적 비교 리포트 의무
작성 직후 `verify_test_doc.py`로 spec ↔ 출력 xlsx를 행·셀 단위로 비교한 리포트를 만들고 **그대로** 사용자에게 보여준다. "샘플 몇 행 확인" 식 spot check를 보고용으로 쓰지 않는다.

> 막는 실패 모드: 매핑이 한 칸씩 밀려도 LLM의 자체 확인은 "TC ID·이름이 보이네"에서 끝남. 결정론적 셀 비교 없이는 잡지 못한다.

### R-C. spec에 없는 값 발명 금지
spec에 "tester", "date" 같은 키가 없는데 양식 컬럼에 해당하는 자리가 있다면 **빈 값으로 둔다.** 그 자리 채우려고 "QA", "2025-01-01" 등 임의 값 생성 금지. 누가 채워야 하는지 사용자에게 묻거나 빈 채로 인도.

> 막는 실패 모드: agent가 친절하게 "테스터=Claude" 등을 채워 넣어 실제 테스터와 불일치.

### R-D. spec 카운트 보고
spec 파싱 직후 **"총 N건 처리합니다"** 한 줄을 사용자에게 보고한다. 사용자가 알려준 카운트와 다르면 그 시점에 합의한다. 작성 후 합계 카운트(pass/fail/block/na/empty)도 별도로 보고.

> 막는 실패 모드: 입력 JSON에 47건이 의도였는데 노이즈로 60건이 섞여 있고 agent가 60건을 그대로 생성. 사후 발견.

### R-E. 출력 파일 충돌 시 묻기
출력 경로에 이미 파일이 있으면 덮어쓰기 전에 한 번 묻는다. 입력 템플릿 자체는 **절대 덮어쓰지 않는다** (출력은 항상 별도 파일).

> 막는 실패 모드: agent가 `./test-results.xlsx`로 무심결에 덮어써서 이전 검수본을 잃음.

## 안전 기본값

- 라이브러리: **openpyxl만 사용**. xlrd/xlsxwriter/pandas 금지.
- `.xls`(구버전 BIFF) 입력 템플릿은 처리하지 않는다 — 사용자에게 `.xlsx`로 저장 후 다시 요청하라고 안내(자동 변환 X).
- 긴 텍스트(40자 초과 또는 줄바꿈 포함)는 `wrap_text=True` 자동 적용.
- 사용자 템플릿이 있으면 헤더·기존 스타일을 **수정하지 않는다.** 데이터 행만 추가.

## 입력

| 종류 | 필수 | 형태 |
|---|---|---|
| 테스트 데이터 | 필수 | (a) 수행 결과 포함 JSON, 또는 (b) 시나리오만 적힌 JSON/markdown |
| 사용자 템플릿 | 선택 | 빈 양식 `.xlsx` (헤더 행 포함) |
| 출력 경로 | 선택 | 미지정 시 `./test-results.xlsx` |

### JSON 스키마 (권장 입력 포맷)

```json
{
  "title": "회원가입 단위테스트",
  "tests": [
    {
      "id": "TC-001",
      "name": "이메일 형식 검증 - 정상",
      "data": "email=user@example.com",
      "steps": [
        "1. 회원가입 페이지 진입",
        "2. 이메일 필드에 user@example.com 입력",
        "3. 다음 버튼 클릭"
      ],
      "expected": "다음 단계로 이동",
      "url": "https://app.example.com/signup",
      "actual": "다음 단계로 이동함",
      "status": "pass"
    }
  ]
}
```

- `steps`는 배열 또는 줄바꿈 문자열 모두 허용. 셀에는 항상 줄바꿈으로 풀어 넣는다.
- 수행 결과가 없는 시나리오에서는 `actual`, `status` 생략 가능.
- `status`는 `pass` / `fail` / `block` / `na` / 빈 값 중 하나.

## 표준 키

`id`, `name`, `data`, `steps`, `expected`, `url`, `actual`, `status`, `note`, `tester`, `date` — 이 11개가 spec과 양식 사이를 잇는 표준 키. 양식 헤더는 이 키 중 하나로 매핑된다. 매핑은 결정론적이며 `scripts/profile_template.py` 안의 alias 사전에 정의되어 있다.

## 작업 절차 (이 순서를 깨지 않는다)

### 0. 입력 점검
- 입력 JSON 또는 markdown이 명확한가?
- 출력 경로가 정해졌는가? (없으면 `./test-results.xlsx` 안내)
- 템플릿 경로가 주어졌는가? `.xls`이면 사용자에게 `.xlsx` 변환 요청 후 대기.

### 1. spec 파싱 및 카운트 보고 (R-D)
```bash
# 농담이 아니라 결정론적으로 jq 또는 python으로 카운트
python3 -c "import json; d=json.load(open('spec.json')); print(len(d['tests']))"
```
→ "총 N건 처리합니다" 한 줄 보고. 사용자가 알려준 숫자와 어긋나면 그 시점에서 합의.

### 2. (템플릿 모드) 프로파일링 + 사용자 승인 (R-A)
```bash
python3 scripts/profile_template.py --template <user.xlsx> --output /tmp/excel_test_profile.json
```
산출 JSON을 다음 표로 정리해 사용자에게 제시:

| 컬럼 | 헤더 텍스트 | 표준 키 매칭 |
|---|---|---|
| A | TC ID | id |
| B | 테스트 케이스 | name |
| ... | ... | ... |
| I | 특이사항 | **미매핑** (의도? 빈 값으로 둠?) |

추가로 보고:
- spec 키 중 양식에 컬럼이 없어서 **누락될** 키
- 양식에 있지만 spec에 데이터가 없어서 **빈 값으로 남을** 키
- 두 컬럼이 같은 표준 키에 매칭된 경우 (예: "결과", "수행 결과")

사용자가 매핑을 승인하거나 수정 지시할 때까지 **다음 단계로 가지 않는다.** 사용자가 수정 지시를 하면 `--mapping` JSON을 만들어 그대로 다음 단계에 전달.

(템플릿이 없을 때는 기본 양식 컬럼 7개를 그대로 보여주고 진행 의사만 가볍게 확인 — 매핑 분쟁 여지가 없으므로.)

### 3. 작성 실행
```bash
python3 scripts/create_test_doc.py \
  --input <spec.json> \
  [--template <user.xlsx>] \
  [--mapping <map.json>] \
  --output <out.xlsx>
```
출력 경로에 파일이 이미 있으면 **반드시 한 번 묻고** 진행 (R-E).

### 4. 결정론적 검증 리포트 (R-B)
```bash
python3 scripts/verify_test_doc.py \
  --input <spec.json> \
  --output <out.xlsx> \
  [--mapping <map.json>]
```
출력을 **그대로** 사용자에게 표시. 다음을 포함:
- 헤더 행, 데이터 행 범위, spec 건수 vs xlsx 행수 일치
- 헤더 ↔ 표준 키 최종 매핑 표
- spec에 있는데 양식에 없어 누락된 키
- 각 행을 셀 단위로 결정론적 비교 (`✓name ✓data ✗expected` 등)
- 의도적으로 빈 셀 (spec에 값 없음) 목록
- status별 카운트
- 행 색상 적용 검증 (pass=#E2EFDA 등)

`verify_test_doc.py`의 종료 코드가 1이면 **완료 보고를 보내지 않는다.** 어긋난 셀을 사용자에게 보여주고 수정 분기로 들어간다.

### 5. 사용자 최종 검토
검증 통과 후, 최종 절대 경로 + status 합계 한 줄을 보고하고 검토 의사 묻기.

## 양식 결정 로직 (보조 설명)

```
사용자 템플릿 제공?
├─ 예 → [템플릿 모드] profile → 매핑 사용자 승인 → 스타일 유지하며 데이터 채움
└─ 아니오 → [기본 모드] 기본 7컬럼으로 신규 생성
```

**사용자 템플릿이 있으면 무조건 그 양식이 우선이다.** 기본 양식의 컬럼이 더 풍부해 보여도 사용자 양식을 깎지 않는다.

### 한↔영 컬럼명 매칭 (참고)

| 표준 키 | 매칭되는 헤더 예시 |
|---|---|
| `id` | `단위테스트 ID`, `테스트 ID`, `TC ID`, `TC No`, `No`, `번호`, `id`, `ID` |
| `name` | `단위테스트명`, `테스트명`, `시나리오명`, `테스트 케이스`, `name`, `case` |
| `data` | `테스트 데이터`, `입력 데이터`, `입력값`, `input`, `data` |
| `steps` | `테스트 절차`, `절차`, `수행 절차`, `수행 단계`, `steps`, `procedure` |
| `expected` | `기대 결과`, `예상 결과`, `expected`, `예상` |
| `url` | `화면 URL`, `URL`, `화면`, `url`, `screen` |
| `actual` | `실제 결과`, `수행 결과`, `결과`, `actual`, `result` |
| `status` | `상태`, `합격여부`, `Pass/Fail`, `결과 상태`, `status` |
| `note` | `비고`, `메모`, `note`, `remarks` |
| `tester` | `테스터`, `수행자`, `담당자`, `tester` |
| `date` | `수행일`, `테스트일`, `date`, `tested at` |

> 이 표는 어디까지나 참고용 문서. **실제 매칭은 `profile_template.py`가 결정한다.** 이 표만 보고 LLM이 매핑을 단정하지 말 것.

### 기본 양식 (템플릿이 없을 때)

| # | 컬럼 |
|---|---|
| 1 | 단위테스트 ID |
| 2 | 단위테스트명 |
| 3 | 테스트 데이터 |
| 4 | 테스트 절차 |
| 5 | 기대 결과 |
| 6 | 화면 URL |
| 7 | 실제 결과 |

- 헤더 행: 굵게 + 배경색(`#D9E1F2`), 가운데 정렬, freeze A2.
- 본문 셀: `wrap_text=True` (40자 초과 또는 줄바꿈 포함 시), 세로 정렬 top.
- 절차 셀: 배열을 `\n`으로 join.

## status별 행 색상 (적용 표준)

| status | 배경색 hex |
|---|---|
| pass | `#E2EFDA` (연두) |
| fail | `#FCE4D6` (연빨) |
| block | `#FFF2CC` (연노랑) |
| na | `#F2F2F2` (회색) |
| (빈 값) | 색 없음 |

데이터 셀에만 적용 (헤더 행은 별도 배경색 유지).

## 자주 발생하는 실수

| 실수 | 위반 규칙 |
|---|---|
| 템플릿을 받고도 `profile_template.py` 없이 LLM이 직접 매핑 결정 | R-A |
| 셀 몇 개만 spot check하고 "완료" 보고 | R-B |
| spec에 없는 "테스터=Claude" 같은 메타데이터 임의 생성 | R-C |
| spec 카운트를 작성 후에야 보고 | R-D |
| 기존 `./test-results.xlsx`를 묻지 않고 덮어씀 | R-E |
| 절차 배열을 `['1...', '2...']`처럼 stringify해 단일 셀에 그대로 | (스크립트가 막아주지만 직접 수정 시 주의) |
| `.xls` 파일을 받고 묵묵히 실패 | Step 0에서 확장자 검사 |
| 두 컬럼이 같은 표준 키로 자동 매칭됐는데 사용자에게 안 물음 | R-A (duplicate_standard_keys 필드 확인) |

## 산출물

- `.xlsx` 한 파일 (기본 `./test-results.xlsx`, `--output`으로 변경 가능)
- 작성 완료 후 절대 경로 + `pass: X / fail: Y / block: Z / na: W / empty: V` 한 줄 요약
- 검증 리포트 (`verify_test_doc.py` stdout)는 결과 노출 시 그대로 첨부

## 스크립트 한눈에

| 스크립트 | 역할 | 시점 |
|---|---|---|
| `scripts/profile_template.py` | 템플릿 헤더 분석, 자동 매핑 후보 산출 (JSON) | 작성 전 (R-A) |
| `scripts/create_test_doc.py` | 실제 xlsx 작성 (템플릿 또는 기본 양식) | 매핑 승인 후 |
| `scripts/verify_test_doc.py` | spec ↔ 출력 xlsx 셀 단위 결정론적 diff | 작성 직후 (R-B) |
