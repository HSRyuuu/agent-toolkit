#!/usr/bin/env python3
"""
mysql_to_dbml.py — MySQL/MariaDB INFORMATION_SCHEMA dump (JSON) → schema.dbml

Input JSON (see tools/README.md for the canonical shape):
    {
      "server":  { "version": "...", "database": "...", "now": "..." },
      "tables":  [{ "TABLE_NAME": "...", "TABLE_COMMENT": "..." }, ...],
      "columns": [{ "TABLE_NAME", "COLUMN_NAME", "COLUMN_TYPE", "COLUMN_KEY",
                    "IS_NULLABLE", "EXTRA", "COLUMN_DEFAULT", "COLUMN_COMMENT" }, ...],
      "indexes": [{ "TABLE_NAME", "INDEX_NAME", "COLUMN_NAME",
                    "SEQ_IN_INDEX", "NON_UNIQUE" }, ...],
      "fks":     [{ "TABLE_NAME", "CONSTRAINT_NAME", "COLUMN_NAME",
                    "ORDINAL_POSITION",
                    "REFERENCED_TABLE_NAME", "REFERENCED_COLUMN_NAME" }, ...]
    }

The output respects pydbml's quoting rules (see SKILL.md → "pydbml Quoting Rules"):
  - identifiers and types are plain or "..." (NEVER backtick)
  - non-ASCII inside a type → wrap the whole type in "..."
  - default expressions may use backtick (raw expression, not an identifier)

Usage:
    python mysql_to_dbml.py --in raw.json --out schema.dbml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


# Identifiers that are safe to emit plain (alnum/underscore, not reserved).
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# pydbml reserved words. Case-insensitive — names matching any of these must
# be double-quoted even if otherwise plain-safe.
DBML_RESERVED = {
    "table", "ref", "project", "enum", "indexes", "note", "default",
    "pk", "unique", "increment", "not", "null", "as", "type",
}

# Types like "varchar(100)", "enum('a','b')", "int". Anything else (spaces,
# special chars, non-ASCII) must be double-quoted.
TYPE_PLAIN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\([^()]*\))?$")


def qtbl(name: str) -> str:
    """Quote a table name when not a plain DBML identifier."""
    if IDENT.match(name) and name.lower() not in DBML_RESERVED:
        return name
    return '"' + name.replace('"', '\\"') + '"'


def qcol(name: str) -> str:
    """Quote a column name when not a plain DBML identifier."""
    if IDENT.match(name) and name.lower() not in DBML_RESERVED:
        return name
    return '"' + name.replace('"', '\\"') + '"'


def qtype(t: str) -> str:
    """Quote a column type when it has parens beyond simple, single quotes, or non-ASCII."""
    if TYPE_PLAIN.match(t) and t.isascii() and "'" not in t:
        return t
    return '"' + t.replace('"', '\\"') + '"'


def esc_note(s: str) -> str:
    """Escape a note string (single-quoted in DBML)."""
    return (
        s.replace("\\", "\\\\")
         .replace("'", "\\'")
         .replace("\n", " ")
         .replace("\r", "")
    )


def fmt_default(v):
    """Format a column default into the DBML attribute form.

    Returns None when no default attribute should be emitted.
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return f"`{v}`"
    sv = str(v)
    # MariaDB INFORMATION_SCHEMA sometimes wraps string defaults with outer
    # single quotes already (e.g. "'0000-00-00'"). Strip them once.
    if len(sv) >= 2 and sv[0] == sv[-1] == "'":
        sv = sv[1:-1].replace("''", "'")
    if sv.lower() in ("current_timestamp()", "current_timestamp"):
        return "`CURRENT_TIMESTAMP`"
    if re.fullmatch(r"-?\d+(\.\d+)?", sv):
        return f"`{sv}`"
    if sv.upper() == "NULL":
        return None
    sv_clean = sv.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{sv_clean}'"


def build_dbml(data: dict) -> str:
    tables = data["tables"]
    columns = data["columns"]
    indexes = data.get("indexes", [])
    fks = data.get("fks", [])
    server = data.get("server", {}) or {}

    cols_by_tbl = defaultdict(list)
    for c in columns:
        cols_by_tbl[c["TABLE_NAME"]].append(c)

    idx_by_tbl = defaultdict(lambda: defaultdict(list))
    idx_meta: dict[tuple[str, str], dict] = {}
    for i in indexes:
        if i.get("INDEX_NAME") == "PRIMARY":
            continue
        t, idx = i["TABLE_NAME"], i["INDEX_NAME"]
        idx_by_tbl[t][idx].append(i)
        idx_meta[(t, idx)] = {"non_unique": i.get("NON_UNIQUE", 1)}

    fks_by_tbl = defaultdict(lambda: defaultdict(list))
    for f in fks:
        fks_by_tbl[f["TABLE_NAME"]][f["CONSTRAINT_NAME"]].append(f)

    lines: list[str] = []
    if server:
        ver = server.get("version", "")
        when = server.get("now", "")
        db = server.get("database", "")
        if ver or when or db:
            lines.append(
                "// Auto-generated from INFORMATION_SCHEMA"
                + (f" ({db})" if db else "")
            )
            lines.append(f"// Generated at {when} from {ver}".rstrip())
            lines.append("")

    lines += [
        "Project schema {",
        f"  database_type: '{server.get('flavor', 'MariaDB')}'",
        f"  Note: '{len(tables)} tables, {len(columns)} columns'",
        "}",
        "",
    ]

    for t in sorted(tables, key=lambda x: x["TABLE_NAME"]):
        name = t["TABLE_NAME"]
        lines.append(f"Table {qtbl(name)} {{")
        cols = cols_by_tbl.get(name, [])

        pk_cols = [c["COLUMN_NAME"] for c in cols if c.get("COLUMN_KEY") == "PRI"]
        composite_pk = len(pk_cols) > 1

        for c in cols:
            col_attrs: list[str] = []
            if c.get("COLUMN_KEY") == "PRI" and not composite_pk:
                col_attrs.append("pk")
            if c.get("COLUMN_KEY") == "UNI":
                col_attrs.append("unique")
            if c.get("IS_NULLABLE") == "NO":
                col_attrs.append("not null")
            if (c.get("EXTRA") or "").lower() == "auto_increment":
                col_attrs.append("increment")
            d = fmt_default(c.get("COLUMN_DEFAULT"))
            if d is not None:
                col_attrs.append(f"default: {d}")
            note_parts: list[str] = []
            if c.get("COLUMN_COMMENT"):
                note_parts.append(c["COLUMN_COMMENT"])
            extra = (c.get("EXTRA") or "").strip()
            if extra and extra.lower() != "auto_increment":
                note_parts.append(f"extra: {extra}")
            if note_parts:
                col_attrs.append(f"note: '{esc_note(' / '.join(note_parts))}'")

            type_str = qtype(c["COLUMN_TYPE"])
            attr_str = f" [{', '.join(col_attrs)}]" if col_attrs else ""
            lines.append(f"  {qcol(c['COLUMN_NAME'])} {type_str}{attr_str}")

        idxs = idx_by_tbl.get(name, {})
        if composite_pk or idxs:
            lines.append("")
            lines.append("  indexes {")
            if composite_pk:
                cols_in_pk = ", ".join(qcol(c) for c in pk_cols)
                lines.append(f"    ({cols_in_pk}) [pk, name: 'PRIMARY']")
            for idx_name, parts in idxs.items():
                parts_sorted = sorted(parts, key=lambda r: r["SEQ_IN_INDEX"])
                cols_str = ", ".join(qcol(p["COLUMN_NAME"]) for p in parts_sorted)
                unique = "unique, " if str(idx_meta[(name, idx_name)]["non_unique"]) == "0" else ""
                lines.append(f"    ({cols_str}) [{unique}name: '{esc_note(idx_name)}']")
            lines.append("  }")

        if t.get("TABLE_COMMENT"):
            lines.append(f"  Note: '{esc_note(t['TABLE_COMMENT'])}'")
        lines.append("}")
        lines.append("")

    for tbl, fk_groups in fks_by_tbl.items():
        for fk_name, rows in fk_groups.items():
            rows_sorted = sorted(rows, key=lambda r: r["ORDINAL_POSITION"])
            cols = ", ".join(qcol(r["COLUMN_NAME"]) for r in rows_sorted)
            ref_tbl = rows_sorted[0]["REFERENCED_TABLE_NAME"]
            ref_cols = ", ".join(qcol(r["REFERENCED_COLUMN_NAME"]) for r in rows_sorted)
            lines.append(f"Ref: {qtbl(tbl)}.({cols}) > {qtbl(ref_tbl)}.({ref_cols})")

    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in",  dest="inp", required=True,
                    help="Input JSON (MySQL/MariaDB INFORMATION_SCHEMA dump)")
    ap.add_argument("--out", dest="out", required=True,
                    help="Output DBML file path")
    args = ap.parse_args()

    in_path = Path(args.inp)
    out_path = Path(args.out)

    if not in_path.exists():
        sys.stderr.write(f"ERROR: {in_path} not found.\n")
        sys.exit(1)

    data = json.loads(in_path.read_text(encoding="utf-8"))
    dbml = build_dbml(data)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(dbml, encoding="utf-8")

    print(
        f"wrote {out_path}\n"
        f"  tables={len(data.get('tables', []))}"
        f"  columns={len(data.get('columns', []))}"
        f"  fks={len(data.get('fks', []))}"
        f"  bytes={len(out_path.read_bytes())}"
    )


if __name__ == "__main__":
    main()
