#!/usr/bin/env python3
"""data.json 을 hover 팝업이 있는 단일 HTML 로 만든다. 사실 수집은 하지 않는다.

사용: render.py <data.json> <out.html> [--ver YYYY-MM-DD] [--open] [--shot out.png [--hash n=<노드id>]]
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
TEMPLATE = os.path.join(HERE, "..", "templates", "architecture.html")
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


def validate(data):
    """깨진 데이터를 렌더 전에 막는다. 오류 문자열 목록과 경고 목록을 돌려준다."""
    errors, warns = [], []
    groups = data.get("groups") or []
    if not groups:
        errors.append("groups 가 비어 있다")
    for path, text in strings(data):
        m = LINE_REF.search(text)
        if m:
            errors.append(f"줄번호는 쓰지 않는다 (파일명·클래스·메서드명까지만): {path} → {m.group(0)}")
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


def agent_text(data):
    """지도를 에이전트가 그대로 읽을 평문으로 옮긴다. 데이터에 있는 것만 쓰고 foot 는 넣지 않는다."""
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


def build(data, ver=None):
    meta = data.setdefault("meta", {})
    meta["ver"] = ver or meta.get("ver") or datetime.date.today().isoformat()
    with open(TEMPLATE, encoding="utf-8") as f:
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
    ap.add_argument("--hash", help="예: n=<노드id> 로 팝업을 연 채 스크린샷")
    a = ap.parse_args()
    with open(a.data, encoding="utf-8") as f:
        data = json.load(f)
    errors, warns = validate(data)
    for w in warns:
        print("WARN:", w, file=sys.stderr)
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        sys.exit(1)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(build(data, a.ver))
    print("OK", os.path.abspath(a.out))
    if a.shot and screenshot(a.out, a.shot, a.hash):
        print("SHOT", os.path.abspath(a.shot))
    if a.open:
        subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", a.out], check=False)


if __name__ == "__main__":
    main()
