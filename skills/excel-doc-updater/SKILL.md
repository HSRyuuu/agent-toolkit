---
name: excel-doc-updater
description: >
  Use when the user explicitly asks to update or regenerate an existing
  form-based .xlsx such as an interface spec, program list, or requirements form
  from markdown, JSON/YAML, DB/API output, or another workbook. Do NOT use for
  normal code edits, non-Excel docs, or forms with a project-specific updater
  skill.
---

# excel-doc-updater

양식이 정해진 xlsx 한 개를 데이터 소스의 최신 내용에 맞춰 **새 파일로** 다시 만든다. 매번 일회성 python 스크립트를 생성·실행한 뒤 원본과의 변경점을 결정론적 리포트로 보여준다.

## 절대 규칙 (위반 금지)

baseline 테스트(별도 agent에게 동일 작업을 시킨 RED 단계)에서 **실제로 관찰된 실패** 다섯 가지에 대응한다. 추측이 아니다.

### R-A. 사용자 승인 게이트
추론한 전략(row_append/sheet_clone/cell_update), 보호 영역, 셀 매핑, 신규 ID 패턴, 출력 경로 — 이 다섯 가지는 사용자에게 **한 번 보여주고 동의를 받은 뒤에만** 스크립트를 실행한다.

> baseline 관찰: agent는 매핑·덮어쓰기 결정을 묻지 않고 임의로 처리. 본인도 사후에 "사실은 물어봤어야 했다"고 자백.

### R-B. 결정론적 비교 리포트 의무
매 실행 끝에 `scripts/compare_excel.py`로 원본 vs 결과 diff를 만들고 **그대로** 사용자에게 보여준다. 자체 spot check(셀 카운트, 샘플 몇 개 확인)는 결과 보고용으로 사용 금지.

> baseline 관찰: agent의 자체 검증은 "보호 시트 셀 카운트 65개·63개 일치"만 봤다. 셀 카운트가 같아도 값이 다를 수 있음 — 결정론적 diff 없이는 진짜 무사한지 알 수 없다.

### R-C. ID 같음 ≠ 도메인 같음
기존 시트가 있는 ID에 신규 spec을 매핑하기 전, **그 시트의 실제 내용을 한 번 읽고** 도메인이 일치하는지 확인한다. 일치하지 않으면(예: 기존 시트가 다른 시스템의 API였음) **반드시 사용자에게 물어본다.**

> baseline 관찰: agent가 IF-AI-003-001~012 12개 시트(원래 Graphio 통계/온톨로지 API)를 명세서의 컬렉션·문서 관리 도메인으로 ID 일치만 보고 통째로 덮어씀.

### R-D. 발명 금지
spec에 없는 값(송신담당자, 수신담당자, 시스템명 등 메타데이터)을 임의로 채우지 않는다. 모르면 빈 값으로 두거나 사용자에게 묻는다.

> baseline 관찰: agent가 송신담당자="AI Data Manager", 수신담당자="Backend API"를 즉석에서 발명. 기존 시트의 실제 값과도 다름.

### R-E. spec 카운트 검증
spec list를 만든 직후 길이를 결정론적으로 세어 사용자에게 한 줄 보고한다 ("총 N건 처리합니다"). 사용자가 알려준 카운트와 다르면 그 시점에 합의한다.

> baseline 관찰: 프롬프트에 "47개 항목"으로 명시했는데 agent가 60개 전부 생성. spec 카운트와 작업 카운트의 불일치가 실행 전에 잡히지 않음.

## 안전 기본값 (대부분의 agent가 자연 준수, 위반 금지로 명시만)

- 입력 xlsx는 절대 덮어쓰지 않는다 (출력은 항상 새 파일).
- 보호 시트(표지, 개정이력, 무관한 prefix 시트 등)는 읽지도 쓰지도 않는다.
- 신규 시트·행은 `wb.copy_worksheet()` 또는 셀 단위 `_style` 복제로 만든다 (빈 시트에 스타일 흉내 금지).

자세한 보호 영역·스타일 처리 패턴은 `references/safety_rules.md`. 위반 시 회복 절차 포함.

## 입력

- **대상 xlsx**: 사용자가 지정한 파일 또는 패턴(예: `workspace/*.xlsx`).
- **데이터 소스**: 자유 형식 (markdown, JSON/YAML, DB/API 응답, 다른 xlsx).
- **사용자 의도**: 자연어 한두 줄.

**Out of scope**: 빈 상태에서 양식 자체를 처음 설계·생성하는 경우는 다루지 않는다. 본 스킬은 기존 양식 xlsx의 갱신·재생성 전용이다. 양식 자체를 처음부터 짜는 작업이 필요하면 `document-skills:xlsx` 사용을 고려할 것.

## 작업 절차

1. **입력 확인** — 경로·매칭·의도가 명확한지. 모호하면 묻고 대기.
2. **엑셀 프로파일링** — `python3 scripts/profile_excel.py --input <xlsx> --output /tmp/excel_profile.json`. 시트·헤더·ID prefix 클러스터·반복 단위 후보 추출. 출력 스키마: `references/profile_schema.md`.
3. **전략 추론 + 매핑 제시** — `row_append` / `sheet_clone` / `cell_update` 중 하나로 분류 (판단 기준: `references/strategy_patterns.md`). 보호 영역·셀 매핑·신규 ID 패턴을 사용자에게 보여주고 **R-A 승인 대기.**
4. **데이터 추출** — 데이터 소스를 파싱해 spec list 생성, `/tmp/excel_specs.json` 저장. **R-E 카운트 보고**, 기존 시트 있는 ID는 **R-C 도메인 일치 확인**, spec에 없는 값은 **R-D 빈 값 유지.**
5. **일회성 스크립트 생성 + 실행** — openpyxl 기반. `wb.copy_worksheet()` 사용. 새 파일로 저장. 스크립트는 `/tmp/excel_update_<timestamp>.py`에 둔다.
6. **결정론적 비교 리포트** — `python3 scripts/compare_excel.py --before <원본> --after <출력> --protected "<보호 시트 목록>"`. 출력을 그대로 사용자에게 표시. **R-B 의무.** 리포트 형식: `references/diff_report_schema.md`.
7. **사용자 최종 검토** — 승인 / 거절(출력 파일 삭제 여부 묻기) / 추가 수정 요청 분기.

## 자주 발생하는 실수 (baseline에서 관찰)

| 실수 | 위반 규칙 |
|---|---|
| 매핑·덮어쓰기를 사용자 승인 없이 결정 | R-A |
| 자체 spot check만 하고 "완료" 보고 | R-B |
| 같은 ID라는 이유로 다른 도메인 시트 덮어쓰기 | R-C |
| spec에 없는 메타데이터 값 발명 | R-D |
| spec 카운트와 작업 카운트 불일치를 사후 발견 | R-E |

## 프로젝트 specific 스킬과의 관계

해당 양식 전용 스킬이 별도 존재하면 (보호 영역·셀 매핑이 하드코딩되어 있어 안정적) 그쪽이 우선이다. 본 스킬은 신규·임시 양식이나 specific 스킬이 아직 없는 경우에 사용한다.
