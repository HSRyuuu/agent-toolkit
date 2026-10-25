---
name: excel-ui-test-doc-creator
description: >
  Use when the user wants test scenarios or test execution results turned into a
  unit-test or QA deliverable Excel .xlsx, with or without a provided template.
  Triggers: "테스트 결과 엑셀로 정리해줘", "단위테스트 산출물 만들어줘",
  "테스트 시나리오 xlsx로", "QA 테스트 결과서 엑셀", "/excel-ui-test-doc-creator".
  Do NOT use for running tests, PDF/docx reports, or updating an existing form
  workbook.
---

# excel-ui-test-doc-creator

테스트 시나리오·수행 결과로 단위테스트 산출물 `.xlsx` 한 파일을 만든다. 사용자 템플릿이 있으면 그 양식을 그대로 따르고, 없으면 기본 양식으로 새로 만든다.

핵심은 **LLM이 추론한 매핑을 그대로 작성하지 않는다**는 점이다. 결정론적 스크립트로 매핑 후보를 만들고, 사용자 승인을 받은 뒤에만 쓰고, 쓴 뒤에는 결정론적 리포트로 행·셀 단위 일치를 확인한다. 아래 규칙은 실제로 관찰된 실패에서 나왔다.

## 절대 규칙

- **R-A. 승인 게이트.** 템플릿이 있으면 `profile_template.py`를 먼저 실행해 (1) 헤더 행, (2) 헤더↔표준 키 매칭 결과, (3) 미매핑 컬럼, (4) spec 키 중 양식에 없는 항목을 표로 보여 주고 **승인을 받은 뒤에만** `create_test_doc.py`를 호출한다. 같은 표준 키에 두 컬럼이 매칭되면(예: "결과"와 "수행 결과") 반드시 묻는다(`duplicate_standard_keys`). 실패 사례: 두 컬럼 중 한쪽에 임의로 붙여 전 행을 다시 작성함.
- **R-B. 결정론적 비교 리포트.** 작성 직후 `verify_test_doc.py`의 출력을 **그대로** 사용자에게 보여 준다. 샘플 몇 행을 눈으로 확인하는 spot check를 보고에 쓰지 않는다(매핑이 한 칸 밀려도 놓친다). 종료 코드가 1이면 완료를 보고하지 않고 어긋난 셀을 보여 준 뒤 수정한다.
- **R-C. 발명 금지.** spec에 `tester`, `date` 같은 값이 없으면 양식에 자리가 있어도 **빈 값**으로 둔다. "QA", "Claude" 같은 값을 채우지 않는다.
- **R-D. 건수 보고.** spec 파싱 직후 "총 N건 처리합니다"를 한 줄 보고하고, 사용자가 말한 숫자와 다르면 그 자리에서 합의한다(47건이 의도인데 노이즈가 섞여 60건이 만들어진 사례). 작성 후에는 pass/fail/block/na/empty 합계도 보고한다.
- **R-E. 덮어쓰기.** 출력 경로에 파일이 있으면 덮어쓰기 전에 한 번 묻는다. 입력 템플릿은 절대 덮어쓰지 않고 출력은 항상 별도 파일이다.

## 안전 기본값

- `openpyxl`만 쓴다(xlrd, xlsxwriter, pandas 금지). `.xls` 입력은 처리하지 않고 `.xlsx`로 저장해 다시 요청하게 안내한다.
- 사용자 템플릿이 있으면 헤더와 기존 스타일을 수정하지 않고 **데이터 행만 추가**한다. 템플릿이 항상 우선이며 기본 양식이 더 풍부해 보여도 깎지 않는다.
- 긴 텍스트(40자 초과 또는 줄바꿈 포함)는 `wrap_text=True`.

## 입력

- 테스트 데이터(필수): 수행 결과가 있는 JSON, 또는 시나리오만 적힌 JSON/markdown.
- 사용자 템플릿(선택): 헤더 행이 있는 빈 `.xlsx`.
- 출력 경로(선택): 기본 `./test-results.xlsx`.

```json
{
  "title": "회원가입 단위테스트",
  "tests": [
    {
      "id": "TC-001",
      "name": "이메일 형식 검증 - 정상",
      "data": "email=user@example.com",
      "steps": ["1. 회원가입 페이지 진입", "2. 이메일 입력", "3. 다음 버튼 클릭"],
      "expected": "다음 단계로 이동",
      "url": "https://app.example.com/signup",
      "actual": "다음 단계로 이동함",
      "status": "pass"
    }
  ]
}
```

`steps`는 배열 또는 줄바꿈 문자열이고 셀에는 줄바꿈으로 풀어 넣는다. 수행 결과가 없으면 `actual`, `status`를 생략한다. `status`는 `pass`/`fail`/`block`/`na`/빈 값.

표준 키는 `id`, `name`, `data`, `steps`, `expected`, `url`, `actual`, `status`, `note`, `tester`, `date` 11개이고, 양식 헤더와의 한↔영 매칭은 `profile_template.py`의 alias 사전이 결정한다. 이 문서의 표나 LLM 추론으로 매핑을 단정하지 않는다.

## 절차 (순서를 깨지 않는다)

1. **입력 점검과 건수 보고(R-D).** 입력이 명확한지, 출력 경로가 정해졌는지, 템플릿이 `.xlsx`인지 본다.
2. **(템플릿 모드) 프로파일링과 승인(R-A).**
   ```bash
   python3 scripts/profile_template.py --template <user.xlsx> --output /tmp/excel_test_profile.json
   ```
   산출 JSON을 `컬럼 | 헤더 텍스트 | 표준 키 매칭` 표로 보여 주고, 양식에 컬럼이 없어 **누락될** spec 키와 spec에 데이터가 없어 **빈 값으로 남을** 키를 함께 보고한다. 승인 또는 수정 지시가 있을 때까지 넘어가지 않는다. 수정 지시는 `--mapping` JSON으로 만들어 다음 단계에 넘긴다. 템플릿이 없으면 기본 양식 7컬럼을 보여 주고 진행 의사만 가볍게 확인한다.
3. **작성.**
   ```bash
   python3 scripts/create_test_doc.py --input <spec.json> [--template <user.xlsx>] [--mapping <map.json>] --output <out.xlsx>
   ```
4. **검증 리포트(R-B).**
   ```bash
   python3 scripts/verify_test_doc.py --input <spec.json> --output <out.xlsx> [--mapping <map.json>]
   ```
   리포트에는 spec 건수 대 행수, 최종 매핑 표, 누락 키, 셀 단위 비교(`✓name ✓data ✗expected`), 의도적 빈 셀, status별 카운트, 행 색상 검증이 들어 있다.
5. **최종 보고.** 절대 경로와 `pass: X / fail: Y / block: Z / na: W / empty: V` 한 줄, 검증 리포트를 그대로 첨부하고 검토 의사를 묻는다.

## 기본 양식 (템플릿이 없을 때)

단위테스트 ID, 단위테스트명, 테스트 데이터, 테스트 절차, 기대 결과, 화면 URL, 실제 결과 — 7컬럼. 헤더는 굵게, 배경 `#D9E1F2`, 가운데 정렬, freeze `A2`. 본문은 세로 정렬 top, 절차 배열은 `\n`으로 join.

status별 데이터 행 배경: pass `#E2EFDA`, fail `#FCE4D6`, block `#FFF2CC`, na `#F2F2F2`, 빈 값은 색 없음(헤더 행은 별도).
