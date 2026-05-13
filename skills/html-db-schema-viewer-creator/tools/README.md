# tools/ — DB metadata → DBML converters

LLM이 INFORMATION_SCHEMA dump 같은 JSON 메타데이터를 받아 매번 DBML 직렬화를 새로 구현하지 않도록 모은 변환기들. 모두 출력 DBML이 **pydbml의 quoting 규칙을 자동으로 지킨다** (SKILL.md → "pydbml Quoting Rules" 참조).

## 변환기 목록

| 파일 | 입력 | 출력 |
|---|---|---|
| `mysql_to_dbml.py` | MySQL / MariaDB INFORMATION_SCHEMA dump (아래 형식의 JSON) | `schema.dbml` |
| `pg_to_dbml.py`    | (TODO) Postgres `pg_catalog` dump | `schema.dbml` |
| `mssql_to_dbml.py` | (TODO) SQL Server `sys.*` dump | `schema.dbml` |

다른 DB 변환기가 필요하면 `mysql_to_dbml.py`를 복제해서 `build_dbml()`의 입력 필드 매핑만 바꾸면 된다. `qtbl()` / `qcol()` / `qtype()` / `fmt_default()` 헬퍼는 공통 quoting 규칙이라 그대로 재사용.

## 입력 JSON 표준 형식

```json
{
  "server": {
    "version":  "10.6.16-MariaDB",
    "database": "myapp_prod",
    "flavor":   "MariaDB",
    "now":      "2026-05-12T13:00:00+09:00"
  },
  "tables": [
    { "TABLE_NAME": "users", "TABLE_COMMENT": "사용자" }
  ],
  "columns": [
    {
      "TABLE_NAME":      "users",
      "COLUMN_NAME":     "id",
      "COLUMN_TYPE":     "bigint(20) unsigned",
      "COLUMN_KEY":      "PRI",
      "IS_NULLABLE":     "NO",
      "EXTRA":           "auto_increment",
      "COLUMN_DEFAULT":  null,
      "COLUMN_COMMENT":  "사용자 ID"
    }
  ],
  "indexes": [
    {
      "TABLE_NAME":   "users",
      "INDEX_NAME":   "idx_users_email",
      "COLUMN_NAME":  "email",
      "SEQ_IN_INDEX": 1,
      "NON_UNIQUE":   0
    }
  ],
  "fks": [
    {
      "TABLE_NAME":             "posts",
      "CONSTRAINT_NAME":        "fk_posts_user",
      "COLUMN_NAME":            "user_id",
      "ORDINAL_POSITION":       1,
      "REFERENCED_TABLE_NAME":  "users",
      "REFERENCED_COLUMN_NAME": "id"
    }
  ]
}
```

키 이름은 INFORMATION_SCHEMA 컬럼명을 그대로 따른다. 새 DB 변환기를 만들 때도 입력 JSON을 이 모양으로 정규화해두면 출력은 `mysql_to_dbml.py`의 로직이 그대로 동작한다.

## 사용 예

### MySQL/MariaDB에서 직접

```bash
# 1) INFORMATION_SCHEMA를 JSON으로 dump (예시 — 환경에 맞게 조정)
mysql -h "$HOST" -u "$USER" -p"$PASS" -B -N -e "
  SELECT JSON_OBJECT(
    'server',  JSON_OBJECT('version', VERSION(), 'database', '$DB',
                          'flavor', 'MariaDB', 'now', NOW()),
    'tables',  (SELECT JSON_ARRAYAGG(JSON_OBJECT('TABLE_NAME', TABLE_NAME, 'TABLE_COMMENT', TABLE_COMMENT))
                  FROM information_schema.tables WHERE TABLE_SCHEMA = '$DB' AND TABLE_TYPE = 'BASE TABLE'),
    'columns', (SELECT JSON_ARRAYAGG(JSON_OBJECT(
                  'TABLE_NAME',TABLE_NAME, 'COLUMN_NAME',COLUMN_NAME,
                  'COLUMN_TYPE',COLUMN_TYPE, 'COLUMN_KEY',COLUMN_KEY,
                  'IS_NULLABLE',IS_NULLABLE, 'EXTRA',EXTRA,
                  'COLUMN_DEFAULT',COLUMN_DEFAULT, 'COLUMN_COMMENT',COLUMN_COMMENT))
                  FROM information_schema.columns WHERE TABLE_SCHEMA = '$DB'),
    'indexes', (SELECT JSON_ARRAYAGG(JSON_OBJECT(
                  'TABLE_NAME',TABLE_NAME, 'INDEX_NAME',INDEX_NAME,
                  'COLUMN_NAME',COLUMN_NAME, 'SEQ_IN_INDEX',SEQ_IN_INDEX,
                  'NON_UNIQUE',NON_UNIQUE))
                  FROM information_schema.statistics WHERE TABLE_SCHEMA = '$DB'),
    'fks',     (SELECT JSON_ARRAYAGG(JSON_OBJECT(
                  'TABLE_NAME',TABLE_NAME, 'CONSTRAINT_NAME',CONSTRAINT_NAME,
                  'COLUMN_NAME',COLUMN_NAME, 'ORDINAL_POSITION',ORDINAL_POSITION,
                  'REFERENCED_TABLE_NAME',REFERENCED_TABLE_NAME,
                  'REFERENCED_COLUMN_NAME',REFERENCED_COLUMN_NAME))
                  FROM information_schema.key_column_usage
                  WHERE TABLE_SCHEMA = '$DB' AND REFERENCED_TABLE_NAME IS NOT NULL)
  );
" > raw.json

# 2) DBML로 변환
python mysql_to_dbml.py --in raw.json --out schema.dbml

# 3) build.py로 정적 사이트 생성
python build.py --in schema.dbml --out .
```

### LLM이 MCP로 메타데이터를 받은 경우

LLM이 Supabase MCP / 자체 SQL 호출로 받은 결과를 위 JSON 형식으로 정규화 → `mysql_to_dbml.py`에 넘기면 동일.

## 새 변환기 추가 가이드

1. `mysql_to_dbml.py`를 복제해서 `<dialect>_to_dbml.py`로 저장
2. `build_dbml(data)` 안의 INFORMATION_SCHEMA 키(`COLUMN_TYPE`, `COLUMN_KEY` 등)를 해당 DB의 필드명으로 교체
3. `qtbl()` / `qcol()` / `qtype()` / `fmt_default()`는 공용이라 손대지 말 것 (pydbml quoting 규칙이 코드로 박혀 있음)
4. 표준 JSON 형식으로 입력을 정규화하면 출력 DBML은 자동으로 pydbml-safe

## 왜 backtick 안 쓰나?

dbdiagram.io 본가 DBML은 backtick 식별자(`` `name` ``)를 허용하지만 **pydbml은 backtick을 받지 않는다**. 식별자/타입은 plain 또는 `"..."`만 가능. 이 변환기들은 그 차이를 코드로 강제한다.
