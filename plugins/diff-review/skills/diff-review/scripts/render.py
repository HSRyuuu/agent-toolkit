#!/usr/bin/env python3
"""collect.py 결과(meta.json, files/*.patch)와 LLM 이 쓴 summary.json 을
고정 템플릿에 넣어 단일 index.html 을 만든다."""
import argparse
import json
import os
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "templates", "review.html")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out", help="collect.py 가 출력한 OUT 폴더")
    ap.add_argument("--open", action="store_true", help="생성 후 브라우저로 연다")
    a = ap.parse_args()

    meta = json.load(open(os.path.join(a.out, "meta.json")))
    sp = os.path.join(a.out, "summary.json")
    summary = json.load(open(sp)) if os.path.exists(sp) else {}
    for f in meta["files"]:
        s = summary.get(f["path"], {})
        f["summary"] = s.get("s", "")
        f["why"] = s.get("why", "")
        f["risk"] = s.get("r") or f["risk_base"]
        f["diff"] = open(os.path.join(a.out, f["patch"]), errors="replace").read()
    meta["files"].sort(key=lambda f: (-len(f["methods"]), -(f["add"] + f["del"])))

    data = json.dumps(meta, ensure_ascii=False).replace("</", "<\\/")
    html = open(TEMPLATE).read().replace("/*__DATA__*/null", data)
    path = os.path.join(a.out, "index.html")
    open(path, "w").write(html)
    print(path)
    if a.open:
        webbrowser.open("file://" + os.path.abspath(path))


if __name__ == "__main__":
    main()
