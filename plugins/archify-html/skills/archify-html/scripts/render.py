#!/usr/bin/env python3
"""data.json 을 단일 HTML 로 만든다. 사실 수집은 하지 않는다.

data.json 의 최상위 "kind" 가 만들 화면 종류를 정한다 (생략하면 architecture).
  architecture  마우스오버 팝업이 있는 아키텍처 지도   (templates/architecture.html)
  data-model    테이블 스키마 + 처리 흐름 + 화면 노출 문서 (templates/data-model.html)
  tabs          위 문서 여러 개를 상단 고정 탭 하나로 묶는다 (templates/tabs.html)

사용: render.py <data.json> <out.html> [--ver YYYY-MM-DD] [--open] [--shot out.png [--size 1560,1000] [--hash n=<노드id>]]
"""
import argparse
import datetime
import html as htmllib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_KIND = "architecture"
TEMPLATES = {
    "architecture": os.path.join(HERE, "..", "templates", "architecture.html"),
    "data-model": os.path.join(HERE, "..", "templates", "data-model.html"),
    "tabs": os.path.join(HERE, "..", "templates", "tabs.html"),
}
START, END = "/*DATA_START*/", "/*DATA_END*/"
# 코드 줄번호(`Foo.java:41`, `Foo.java:41-52`)는 코드가 바뀌면 틀어지므로 쓰지 않는다
LINE_REF = re.compile(r"[\w.-]+\.(?:java|kt|kts|py|ts|tsx|js|jsx|go|rb|php|cs|xml|ya?ml|sql|properties):\d+")
CHROME = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chrome",
]


def strings(x, path=""):
    """데이터 안의 모든 문자열을 (경로, 값)으로 돌려준다."""
    if isinstance(x, dict):
        for k, v in x.items():
            yield from strings(v, f"{path}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from strings(v, f"{path}[{i}]")
    elif isinstance(x, str):
        yield path, x


def strip_lines(text):
    """`Foo.java:41-52`, `(호출 :159)`, `, :118-125` 같은 줄번호 표기를 지운다."""
    ext = r"(?:java|kt|kts|py|ts|tsx|js|jsx|go|rb|php|cs|xml|ya?ml|sql|properties)"
    text = re.sub(rf"(\.{ext}):\d+(?:[-,]\d+)*", r"\1", text)
    text = re.sub(r"\s*\([^()]*?\s:\d+(?:[-,]\d+)*\)", "", text)
    return re.sub(r",\s*:\d+(?:[-,]\d+)*", "", text)


def kind_of(data):
    k = data.get("kind", DEFAULT_KIND)
    if k not in TEMPLATES:
        raise ValueError(f"kind 는 {' | '.join(TEMPLATES)} 중 하나다 ({k!r})")
    return k


def line_ref_errors(data):
    """모든 종류가 공유하는 규칙: 코드 줄번호는 쓰지 않는다."""
    return [f"줄번호는 쓰지 않는다 (파일명·클래스·메서드명까지만): {path} → {m.group(0)}"
            for path, text in strings(data) for m in [LINE_REF.search(text)] if m]


def validate(data, base_dir=None):
    """깨진 데이터를 렌더 전에 막는다. 오류 문자열 목록과 경고 목록을 돌려준다. kind 별로 검사한다.
    base_dir 은 tabs 의 file 경로를 푸는 기준 폴더이다(생략하면 현재 폴더)."""
    try:
        kind = kind_of(data)
    except ValueError as e:
        return [str(e)], []
    if kind == "tabs":
        return validate_tabs(data, base_dir)
    errors, warns = (validate_data_model if kind == "data-model" else validate_architecture)(data)
    return line_ref_errors(data) + errors, warns


def validate_architecture(data):
    errors, warns = [], []
    groups = data.get("groups") or []
    if not groups:
        errors.append("groups 가 비어 있다")
    ids = {}
    for g in groups:
        if not g.get("title"):
            errors.append(f"group {g.get('id')!r}: title 이 없다")
        if g.get("col") is None and g.get("x") is None:
            errors.append(f"group {g.get('title')!r}: col 또는 x 가 필요하다")
        if not g.get("nodes"):
            errors.append(f"group {g.get('title')!r}: nodes 가 비어 있다")
        for n in g.get("nodes", []):
            nid = n.get("id")
            if not nid:
                errors.append(f"group {g.get('title')!r}: id 없는 node 가 있다")
            elif nid in ids:
                errors.append(f"node id 중복: {nid}")
            ids[nid] = n
            if n.get("row") is None and n.get("y") is None:
                errors.append(f"node {nid}: row 또는 y 가 필요하다")
            for r in n.get("db", []):
                if not r.get("s") or not r.get("op"):
                    errors.append(f"node {nid}: db 항목에 s/op 가 필요하다 {r}")
                elif set(r["op"]) - set("RWUD"):
                    errors.append(f"node {nid}: op 는 R W U D 만 쓴다 ({r['op']})")
    for e in data.get("edges", []):
        for k in ("from", "to"):
            if e.get(k) not in ids:
                errors.append(f"edge {e.get('n')!r}: {k}={e.get(k)!r} 인 node 가 없다")
        if e.get("kind", "ok") not in ("ok", "unk"):
            errors.append(f"edge {e.get('n')!r}: kind 는 ok 또는 unk")
    # 같은 col 의 그룹이 세로로 겹치면 경고 (row 를 조정하면 된다)
    by_col = {}
    for g in groups:
        if g.get("col") is not None and g.get("y") is None and g.get("nodes"):
            rows = [n["row"] for n in g["nodes"] if n.get("row") is not None]
            if rows:
                by_col.setdefault(g["col"], []).append((min(rows), max(rows), g.get("title")))
    for col, spans in by_col.items():
        spans.sort()
        for (a0, a1, at), (b0, b1, bt) in zip(spans, spans[1:]):
            if b0 - a1 < 1.5:  # 그룹 머리말(약 0.5행)과 여백이 들어갈 간격
                warns.append(f"col {col}: '{at}' 와 '{bt}' 가 너무 붙어 있다 (row 간격 1.5 이상 권장)")
    return errors, warns


KIND = {"focus": "강조", "ext": "외부", "queue": "메시지"}
OP = {"R": "읽기", "W": "INSERT", "U": "UPDATE", "D": "DELETE"}


def agent_text(data, base_dir=None):
    """화면을 에이전트가 그대로 읽을 평문으로 옮긴다. 데이터에 있는 것만 쓰고 foot 는 넣지 않는다."""
    kind = kind_of(data)
    if kind == "tabs":
        return agent_text_tabs(data, base_dir)
    return (agent_text_data_model if kind == "data-model" else agent_text_architecture)(data)


def agent_text_architecture(data):
    meta = data.get("meta", {})
    lv = {1: meta.get("confirmedLabel", "확인"), 0: meta.get("estimatedLabel", "추정")}
    ref = {}
    for g in data["groups"]:
        for n in g["nodes"]:
            ref[n["id"]] = f"{g['title']} · {n['label']}"
    out = [f"# {meta.get('title', 'Architecture')}" + (f"  (ver. {meta['ver']})" if meta.get("ver") else ""), "",
           "위 지도를 글로 옮긴 것이다. 구성 요소, 호출 관계, 경로별 저장소 접근이 들어 있다.",
           "- 저장소 접근 표기: R=읽기, W=INSERT, U=UPDATE, D=DELETE. 둘 이상이면 조합(예: RU).",
           f"- 근거 표기: [{lv[1]}]=확인된 항목, [{lv[0]}]=추정. 표기가 없으면 근거 수준 미표시.",
           "- 호출 관계의 화살표는 호출 방향이다. [확정]=확인된 호출, [미확인]=호출자·발행자 등 정확히 못 찾은 연결.",
           "", "## 구성 요소"]
    unknown = []
    for g in data["groups"]:
        kind = KIND.get(g.get("kind"))
        out += ["", f"### {g['title']}" + (f" — {g['sub']}" if g.get("sub") else "") + (f" ({kind})" if kind else "")]
        for n in g["nodes"]:
            out.append(f"- {n['label']}" + ("  [미확인 주체]" if n.get("stub") else ""))
            if n.get("stub"):
                unknown.append(ref[n["id"]])
            line = ((n.get("method") or "") + " " + (n.get("path") or "")).strip()
            if line:
                out.append(f"    호출 지점: {line}")
            if n.get("desc"):
                out.append(f"    설명: {n['desc']}")
            if n.get("db"):
                out.append("    저장소 접근:")
                for r in n["db"]:
                    ops = "".join(r["op"])
                    mark = f" [{lv[r['c']]}]" if r.get("c") in (0, 1) else ""
                    tail = "".join(f" ({x})" if k == "e" else f" — {x}" for k, x in (("n", r.get("n")), ("e", r.get("e"))) if x)
                    out.append(f"      - {ops} {r['s']}{mark}{tail}")
            if n.get("ext"):
                out.append("    외부 호출:")
                for x in n["ext"]:
                    out.append(f"      - {x['t']}" + (f" — {x['n']}" if x.get("n") else "") + (f" ({x['e']})" if x.get("e") else ""))
            if n.get("note"):
                out.append(f"    비고: {n['note']}")
    out += ["", "## 호출 관계"]
    for e in data.get("edges", []):
        unk = e.get("kind") == "unk"
        tag = f"[{e['n']}] " if e.get("n") is not None else ""
        out.append(f"- {tag}{ref[e['from']]} → {ref[e['to']]}  [{'미확인' if unk else '확정'}]" + (f" : {e['note']}" if e.get("note") else ""))
        if unk:
            unknown.append(f"{ref[e['from']]} → {ref[e['to']]}")
    if unknown:
        out += ["", "## 확인하지 못한 연결·주체"] + [f"- {u}" for u in dict.fromkeys(unknown)]
    return "\n".join(out) + "\n"


TONES = ("a", "b", "c", "d")
TAGS = ("real", "ex", "new")
OPS = ("ins", "upd", "same")
TAG_KO = {"real": "실제", "ex": "예시", "new": "신규"}
OP_KO = {"ins": "INSERT", "upd": "UPDATE", "same": "변경 없음"}


def validate_data_model(data):
    """data-model 종류의 데이터 검사. 표의 열 수가 어긋나면 화면이 깨지므로 오류로 막는다."""
    errors, warns = [], []
    tables = data.get("tables") or []
    if not tables:
        errors.append("tables 가 비어 있다")
    tid = {}
    for t in tables:
        i = t.get("id")
        if not i:
            errors.append(f"id 없는 table 이 있다 ({t.get('name')!r})")
        elif i in tid:
            errors.append(f"table id 중복: {i}")
        tid[i] = t
        for k in ("name", "role"):
            if not t.get(k):
                errors.append(f"table {i!r}: {k} 가 필요하다")
        if t.get("tone", "a") not in TONES:
            errors.append(f"table {i!r}: tone 은 {'/'.join(TONES)} 중 하나")
        if not t.get("columns"):
            errors.append(f"table {i!r}: columns 가 비어 있다")
        for c in t.get("columns", []):
            if not c.get("n") or not c.get("t") or not c.get("d"):
                errors.append(f"table {i!r}: column 에 n/t/d 가 필요하다 {c.get('n')!r}")
    for r in data.get("relations", []):
        for k in ("from", "to"):
            if r.get(k) not in tid:
                errors.append(f"relation: {k}={r.get(k)!r} 인 table 이 없다")
        if r.get("card") and r["card"].count(":") != 1:
            errors.append(f"relation card 는 '1:N' 처럼 쓴다 ({r['card']!r})")
    fids = set()
    for f in data.get("flows", []):
        i = f.get("id")
        if not i or not f.get("label"):
            errors.append(f"flow 에 id/label 이 필요하다 ({i!r})")
        elif i in fids:
            errors.append(f"flow id 중복: {i}")
        fids.add(i)
        if f.get("tag") and f["tag"] not in TAGS:
            errors.append(f"flow {i!r}: tag 는 {'/'.join(TAGS)} 중 하나")
        for ft in f.get("tables", []):
            if ft.get("ref") not in tid:
                errors.append(f"flow {i!r}: ref={ft.get('ref')!r} 인 table 이 없다")
            cols = ft.get("cols") or []
            for row in ft.get("rows", []):
                if row.get("op") not in OPS:
                    errors.append(f"flow {i!r}: row op 는 {'/'.join(OPS)} 중 하나 ({row.get('op')!r})")
                if len(row.get("c", [])) != len(cols):
                    errors.append(f"flow {i!r}: row 의 칸 수({len(row.get('c', []))})가 cols({len(cols)})와 다르다")
    views = data.get("views") or {}
    vids = set()
    src = views.get("source")
    if src:
        for row in src.get("rows", []):
            if len(row.get("c", [])) != len(src.get("cols", [])):
                errors.append("views.source: row 의 칸 수가 cols 와 다르다")
            if row.get("tag", "real") not in TAGS:
                errors.append(f"views.source: tag 는 {'/'.join(TAGS)} 중 하나")
    for tab in views.get("tabs", []):
        i = tab.get("id")
        if not i or not tab.get("label"):
            errors.append(f"views.tabs 에 id/label 이 필요하다 ({i!r})")
        elif i in vids:
            errors.append(f"views.tabs id 중복: {i}")
        vids.add(i)
        for row in tab.get("rows", []):
            if len(row.get("c", [])) != len(tab.get("cols", [])):
                errors.append(f"views.tabs {i!r}: row 의 칸 수가 cols 와 다르다")
            if row.get("tag", "real") not in TAGS:
                errors.append(f"views.tabs {i!r}: tag 는 {'/'.join(TAGS)} 중 하나")
    for c in data.get("callouts", []):
        if not c.get("title") or not c.get("body"):
            errors.append("callouts 항목에 title/body 가 필요하다")
    if data.get("relations") and len(tables) > 6:
        warns.append("테이블이 7개 이상이면 관계도가 넓어진다. 필요하면 table.pos 로 격자 위치를 지정한다")
    return errors, warns


def plain_all(raw_json):
    """JSON 문자열 안의 값에서 강조 기호를 걷어낸다(키와 구조는 그대로)."""
    obj = json.loads(raw_json)

    def walk(x):
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        if isinstance(x, list):
            return [walk(v) for v in x]
        return plain(x) if isinstance(x, str) else x

    return json.dumps(walk(obj), ensure_ascii=False)


def plain(s):
    """화면용 강조(`코드`, **굵게**)를 걷어낸 평문."""
    return re.sub(r"\*\*([^*]+)\*\*", r"\1", re.sub(r"`([^`]+)`", r"\1", str(s)))


def agent_text_data_model(data):
    """data-model 문서를 평문으로 옮긴다. foot 는 넣지 않고, 근거(basis)와 경고(callouts)는 넣는다."""
    data = json.loads(plain_all(json.dumps(data, ensure_ascii=False)))
    meta = data.get("meta", {})
    T = {t["id"]: t for t in data.get("tables", [])}
    out = [f"# {meta.get('heading') or meta.get('title', 'Data model')}" + (f"  (ver. {meta['ver']})" if meta.get("ver") else ""), ""]
    if meta.get("lead"):
        out += [meta["lead"], ""]
    ov = data.get("overview") or {}
    if ov.get("formula"):
        out += [f"공식: {ov['formula']}"]
    if ov.get("note"):
        out += [ov["note"]]
    out += ["", "## 테이블"]
    for t in data.get("tables", []):
        out += ["", f"### {t['role']} — {t['name']}" + (f" ({t['where']})" if t.get("where") else "")]
        if t.get("summary"):
            out.append(f"설명: {t['summary']}")
        if t.get("indexes"):
            out.append(f"{t['indexes']}")
        out.append("컬럼:")
        for c in t["columns"]:
            out.append(f"  - {c['n']} ({c['t']}){' [핵심]' if c.get('key') else ''} — {c['d']}")
    if data.get("relations"):
        out += ["", "## 관계"]
        for r in data["relations"]:
            out.append(f"- {T[r['from']]['name']} → {T[r['to']]['name']}  [{r.get('card', '1:N')}]" + (f" : {r['label']}" if r.get("label") else ""))
    if data.get("flows"):
        out += ["", "## 처리 흐름별 테이블 변화"]
    for f in data.get("flows", []):
        tag = f" [{f.get('tagLabel') or TAG_KO.get(f['tag'], f['tag'])}]" if f.get("tag") else ""
        out += ["", f"### {f['label']}{tag}"]
        if f.get("who"):
            out.append(f["who"])
        for ft in f.get("tables", []):
            t = T[ft["ref"]]
            out.append(f"- {t['name']} ({t['role']})")
            if not ft.get("rows"):
                out.append("    추가되거나 변경되는 행 없음")
            for row in ft.get("rows", []):
                out.append(f"    {OP_KO[row['op']]}: " + ", ".join(f"{c}={v}" for c, v in zip(ft["cols"], row["c"])))
        for n in f.get("notes", []):
            out.append(f"  * {n}")
    views = data.get("views") or {}
    if views.get("tabs"):
        out += ["", "## 화면 노출 로직"]
        if views.get("lead"):
            out.append(views["lead"])
        src = views.get("source")
        if src:
            out += ["", f"### {src.get('title', '원본')}"]
            for row in src["rows"]:
                out.append(f"- [{TAG_KO[row.get('tag', 'real')]}] " + ", ".join(f"{c}={v}" for c, v in zip(src["cols"], row["c"])))
        for tab in views["tabs"]:
            out += ["", f"### {tab['label']}"]
            for row in tab["rows"]:
                out.append(f"- [{TAG_KO[row.get('tag', 'real')]}] " + ", ".join(f"{c}={v}" for c, v in zip(tab["cols"], row["c"])))
            if tab.get("note"):
                out.append(f"비고: {tab['note']}")
            if tab.get("rules"):
                out.append(f"{tab.get('rulesTitle', tab['label'])}:")
                out += [f"  - {r}" for r in tab["rules"]]
    if data.get("callouts"):
        out += ["", "## 주의"]
        for c in data["callouts"]:
            out += [f"- {c['title']}: {c['body']}"]
    if meta.get("basis"):
        out += ["", f"근거: {meta['basis']}"]
    return "\n".join(out) + "\n"


TAB_ID = re.compile(r"^[A-Za-z][\w-]*$")


def load_tabs(data, base_dir=None):
    """tabs 의 각 탭을 (id, label, 자식 데이터) 로 푼다. file 은 base_dir 기준 상대 경로이다."""
    base = base_dir or os.getcwd()
    out = []
    for i, tab in enumerate(data.get("tabs") or []):
        if tab.get("file"):
            with open(os.path.join(base, tab["file"]), encoding="utf-8") as f:
                child = json.load(f)
        else:
            child = tab.get("data") or {}
        out.append({"id": tab.get("id") or f"tab{i + 1}", "label": tab.get("label", ""), "data": child})
    return out


def validate_tabs(data, base_dir=None):
    errors = line_ref_errors({k: v for k, v in data.items() if k != "tabs"})
    warns = []
    tabs = data.get("tabs") or []
    if not tabs:
        return errors + ["tabs 가 비어 있다"], warns
    if len(tabs) < 2:
        warns.append("탭이 하나뿐이다. 탭으로 묶을 이유가 없으면 해당 종류의 문서를 그대로 만든다")
    base = base_dir or os.getcwd()
    seen = set()
    for i, tab in enumerate(tabs):
        who = tab.get("label") or f"tabs[{i}]"
        if not tab.get("label"):
            errors.append(f"{who}: label 이 필요하다")
        if bool(tab.get("file")) == bool(tab.get("data")):
            errors.append(f"{who}: file 또는 data 중 하나만 쓴다")
            continue
        tid = tab.get("id") or f"tab{i + 1}"
        if not TAB_ID.match(tid):
            errors.append(f"{who}: id 는 영문으로 시작하는 영문·숫자·-·_ 이다 ({tid!r})")
        if tid in seen:
            errors.append(f"탭 id 중복: {tid}")
        seen.add(tid)
        try:
            child = load_tabs({"tabs": [tab]}, base)[0]["data"]
        except (OSError, ValueError) as e:
            errors.append(f"{who}: 파일을 읽지 못했다 ({tab.get('file')!r}): {e}")
            continue
        if child.get("kind") == "tabs":
            errors.append(f"{who}: 탭 안에 tabs 를 넣을 수 없다")
            continue
        ce, cw = validate(child, base)
        errors += [f"[{who}] {m}" for m in ce]
        warns += [f"[{who}] {m}" for m in cw]
    return errors, warns


def agent_text_tabs(data, base_dir=None):
    meta = data.get("meta", {})
    tabs = load_tabs(data, base_dir)
    out = [f"# {meta.get('title', 'Documents')}" + (f"  (ver. {meta['ver']})" if meta.get("ver") else ""), "",
           f"탭 {len(tabs)}개: " + ", ".join(t["label"] for t in tabs)]
    for t in tabs:
        out += ["", "=" * 60, f"탭: {t['label']}", "=" * 60, "", agent_text(t["data"], base_dir).rstrip()]
    return "\n".join(out) + "\n"


def split_document(html):
    """완성된 문서 HTML 을 (css, 본문 마크업, 스크립트) 로 나눈다. 템플릿은 <style> 하나, 본문 뒤 <script> 하나를 가진다."""
    css = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    body = re.search(r"<body[^>]*>(.*)</body>", html, re.S).group(1)
    i = body.index("<script>")
    script = re.search(r"<script>(.*?)</script>", body[i:], re.S).group(1)
    assert "</script>" not in script
    return css, body[:i].strip(), script


def to_shadow_css(css):
    """문서 전체용 CSS 를 Shadow DOM 패널용으로 바꾼다. :root 는 호스트로, body 는 패널 래퍼(.pg)로 옮긴다.
    data-theme 는 탭 페이지가 호스트 속성으로 미러링한다."""
    css = css.replace(':root:not([data-theme="light"])', ':host(:not([data-theme="light"]))')
    css = css.replace(':root[data-theme="dark"]', ':host([data-theme="dark"])')
    css = re.sub(r"(?m)^(\s*):root\s*\{", r"\1:host {", css)
    css = re.sub(r"(?m)^(\s*)body\s*\{", r"\1.pg {", css)
    return (":host { display: block; }\n[hidden] { display: none !important; }\n"
            ".pg { min-height: calc(100vh - 56px); }\n" + css)  # 56px = 탭 막대 높이


def build_tabs(data, ver=None, base_dir=None):
    meta = data.setdefault("meta", {})
    meta["ver"] = ver or meta.get("ver") or datetime.date.today().isoformat()
    tabs = load_tabs(data, base_dir)
    buttons, hosts, templates, scripts = [], [], [], []
    for tab in tabs:
        key, label = tab["id"], htmllib.escape(tab["label"])
        css, markup, script = split_document(build(tab["data"], meta["ver"], base_dir))
        buttons.append(f'<button type="button" role="tab" id="tab-{key}" aria-controls="host-{key}" aria-selected="false" tabindex="-1">{label}</button>')
        hosts.append(f'<div class="host" id="host-{key}" role="tabpanel" aria-labelledby="tab-{key}"></div>')
        templates.append(f'<template id="tpl-{key}"><style>{to_shadow_css(css)}</style><div class="pg">{markup}</div></template>')
        scripts.append(f"<script>\n(function (document) {{\n{script}\n}})(scopedDocument(ROOTS[{json.dumps(key)}]));\n</script>")
    with open(TEMPLATES["tabs"], encoding="utf-8") as f:
        html = f.read()
    html = html.replace("<!--TITLE-->", htmllib.escape(meta.get("title", "Documents")), 1)
    html = html.replace("<!--TAB_BUTTONS-->", "".join(buttons), 1)
    html = html.replace("<!--TAB_HOSTS-->", "\n".join(hosts), 1)
    html = html.replace("<!--TAB_TEMPLATES-->", "\n".join(templates), 1)
    html = html.replace("<!--TAB_SCRIPTS-->", "\n".join(scripts), 1)
    i, j = html.index("/*KEYS_START*/"), html.index("/*KEYS_END*/") + len("/*KEYS_END*/")
    return html[:i] + "/*KEYS_START*/" + json.dumps([t["id"] for t in tabs]) + "/*KEYS_END*/" + html[j:]


def build(data, ver=None, base_dir=None):
    if kind_of(data) == "tabs":
        return build_tabs(data, ver, base_dir)
    meta = data.setdefault("meta", {})
    meta["ver"] = ver or meta.get("ver") or datetime.date.today().isoformat()
    with open(TEMPLATES[kind_of(data)], encoding="utf-8") as f:
        html = f.read()
    i, j = html.index(START), html.index(END) + len(END)
    # </script> 가 데이터에 들어 있어도 HTML 이 깨지지 않게 한다
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = html[:i] + START + payload + END + html[j:]
    return html.replace("<!--AGENT_TEXT-->", htmllib.escape(agent_text(data)), 1)


def screenshot(html_path, png_path, hash_=None, size="1560,1000"):
    chrome = next((c for c in CHROME if os.path.exists(c) or shutil.which(c)), None)
    if not chrome:
        print("Chrome 을 찾지 못해 스크린샷은 건너뛴다", file=sys.stderr)
        return False
    url = "file://" + os.path.abspath(html_path) + ("#" + hash_ if hash_ else "")
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={size}", f"--screenshot={png_path}", url],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return os.path.exists(png_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("out")
    ap.add_argument("--ver")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--shot")
    ap.add_argument("--hash", help="예: n=<노드id> 로 팝업을 연 채 스크린샷(architecture), 또는 <탭id> 로 그 탭을 연 채 스크린샷(tabs)")
    ap.add_argument("--size", default="1560,1000", help="스크린샷 창 크기 '가로,세로'. 긴 문서는 세로를 키운다 (예: 1100,4400)")
    a = ap.parse_args()
    with open(a.data, encoding="utf-8") as f:
        data = json.load(f)
    base_dir = os.path.dirname(os.path.abspath(a.data))
    errors, warns = validate(data, base_dir)
    for w in warns:
        print("WARN:", w, file=sys.stderr)
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        sys.exit(1)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(build(data, a.ver, base_dir))
    print("OK", os.path.abspath(a.out))
    if a.shot and screenshot(a.out, a.shot, a.hash, a.size):
        print("SHOT", os.path.abspath(a.shot))
    if a.open:
        subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", a.out], check=False)


if __name__ == "__main__":
    main()
