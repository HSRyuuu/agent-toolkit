# 엑셀 프로파일 JSON 스키마

`scripts/profile_excel.py`의 출력 형식. LLM이 전략 추론 단계에서 이 JSON을 읽어 매핑/전략을 결정한다.

## 최상위 구조

```json
{
  "input_path": "workspace/EVAX_설계_AI_인터페이스설계서_v1.0_20260101.xlsx",
  "input_size_bytes": 123456,
  "input_mtime": "2026-04-12T11:32:01",
  "sheet_count": 12,
  "sheets": [ /* SheetProfile[] */ ],
  "cross_sheet_signals": {
    "sheet_name_prefix_clusters": [ /* PrefixCluster[] */ ],
    "duplicate_header_signature_groups": [ /* string[][] */ ]
  }
}
```

## SheetProfile

```json
{
  "name": "IF-AI-003-001",
  "index": 5,
  "max_row": 28,
  "max_col": 8,
  "dimensions": "A1:H28",
  "header_row_candidates": [
    {"row": 10, "filled_ratio": 1.0, "values": ["No.", "필드명 (한글)", "필드명 (영문)", "데이터타입", "길이", "필수여부", "테스트값", "비고"]}
  ],
  "merged_ranges": ["A1:H1", "B2:C2", "D2:H2"],
  "column_widths": {"A": 6.0, "B": 18.5, "C": 18.5, "D": 12.0},
  "row_heights": {"1": 28.0, "2": 22.0},
  "id_columns": [
    {
      "column": "C",
      "prefix": "PG-AI-003-",
      "match_count": 60,
      "rows": [3, 4, 5, "..."],
      "sample_values": ["PG-AI-003-001", "PG-AI-003-002"]
    }
  ],
  "cell_style_fingerprint": {
    "row_11_template": {
      "A": {"font": "맑은 고딕/10/regular", "fill": "FFFFFF", "border": "thin/all", "align": "center/middle"},
      "B": {"font": "맑은 고딕/10/regular", "fill": "FFFFFF", "border": "thin/all", "align": "left/middle"}
    }
  },
  "cross_sheet_formula_count": 0,
  "has_images": false,
  "has_charts": false,
  "has_data_validation": false,
  "has_conditional_formatting": false
}
```

## PrefixCluster

같은 prefix를 공유하는 시트들의 묶음. `sheet_clone` 전략 후보 식별에 사용.

```json
{
  "prefix": "IF-AI-003-",
  "sheet_names": ["IF-AI-003-001", "IF-AI-003-002", "IF-AI-003-003"],
  "count": 3,
  "master_candidate": "IF-AI-003-001",
  "header_signature_match_ratio": 1.0
}
```

## 필드 의미

### `header_row_candidates`
- 1~12행 중 텍스트 셀 비율이 0.6 이상인 행을 후보로 잡는다.
- LLM이 그 중 어느 행이 진짜 헤더인지 사용자 의도와 함께 결정.

### `id_columns`
- 각 컬럼에서 `^[A-Z]+(-[A-Z0-9]+){2,}$` 같은 ID 패턴이 3회 이상 반복되면 후보.
- `match_count >= 3` 이고 같은 prefix가 80% 이상이면 row_append 후보 컬럼.

### `cell_style_fingerprint`
- 신규 행/셀을 만들 때 어느 행을 템플릿으로 복제할지 결정하기 위함.
- 헤더 다음 행(첫 데이터 행)을 기본 템플릿으로 잡는다.
- 행 단위 결과만 담고, 모든 셀의 스타일을 다 담지 않는다 (용량 절약).

### `cross_sheet_formula_count`
- 다른 시트를 참조하는 수식의 개수. 0이 아니면 행 삽입·삭제 시 주의.

### `cross_sheet_signals.sheet_name_prefix_clusters`
- 시트 이름을 정규식으로 분리해 prefix가 같은 묶음을 만든다 (count >= 2).
- count가 가장 큰 묶음이 sheet_clone 후보 1순위.

### `cross_sheet_signals.duplicate_header_signature_groups`
- 시트의 헤더 행 값들이 동일한 시트들의 묶음.
- 시트 이름은 다르지만 내부 양식이 같은 경우(예: 표지 양식이 여럿)를 식별.

## 스키마 안정성

- 필드 추가는 가능하나 기존 필드 이름·의미 변경은 없음.
- LLM이 누락 키에 대해 안전하게 동작하도록, 필수 키는 다음으로 한정한다: `input_path`, `sheets[].name`, `sheets[].max_row`, `sheets[].max_col`.
