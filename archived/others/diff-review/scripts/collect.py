#!/usr/bin/env python3
"""현재 브랜치의 diff 를 수집해 리뷰용 meta.json 과 파일별 patch 를 만든다.

- 파일별 상태(A/M/D/R), 추가/삭제 줄 수, 변경된 Java 메서드(시그니처 기준)
- 변경 메서드에서 호출자를 여러 단계 거슬러 올라가 영향받는 진입점(HTTP API, Kafka 등 리스너, 스케줄러)
- 규칙 기반 기본 위험도(H/M/L)

LLM 은 이 결과를 보고 요약과 최종 위험도만 summary.json 으로 쓴다.
"""
import argparse
import bisect
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import deque

ENDPOINT_ANNOTATIONS = {
    "GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT",
    "DeleteMapping": "DELETE", "PatchMapping": "PATCH", "RequestMapping": "ANY",
    "KafkaListener": "KAFKA", "RabbitListener": "RABBIT", "JmsListener": "JMS",
    "SqsListener": "SQS", "Scheduled": "SCHEDULED", "EventListener": "EVENT",
    "TransactionalEventListener": "EVENT",
}
KEYWORDS = {"if", "for", "while", "switch", "catch", "synchronized", "try", "return",
            "new", "else", "do", "throw", "case", "assert", "super", "this"}
SENSITIVE_HINTS = ("entity", "repository", "migration", "/db/", "config", "security")
MAX_DEPTH = 8
MAX_VISIT = 3000


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} 실패: {r.stderr.strip()}")
    return r.stdout


# ---------------------------------------------------------------- Java 파싱

def blank(src):
    """주석은 공백으로, 문자열/문자 리터럴 내용은 공백으로 바꾼 버전(code)과
    주석만 지운 버전(raw)을 같은 길이로 돌려준다. 줄바꿈은 유지한다."""
    code, raw = list(src), list(src)
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                code[k] = raw[k] = " "
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if src[k] != "\n":
                    code[k] = raw[k] = " "
            i = j
        elif src.startswith('"""', i):
            j = src.find('"""', i + 3)
            j = n if j < 0 else j + 3
            for k in range(i + 3, j - 3):
                if src[k] != "\n":
                    code[k] = " "
            i = j
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            for k in range(i + 1, min(j, n)):
                code[k] = " "
            i = j + 1
        else:
            i += 1
    return "".join(code), "".join(raw)


METHOD_RE = re.compile(r"(\w+)\s*\(((?:[^()]|\([^()]*\))*)\)\s*(?:throws\s+[\w.,\s<>]+)?$")
CLASS_RE = re.compile(r"\b(class|interface|enum|record)\s+(\w+)")
ANNOT_RE = re.compile(r"@([\w.]+)")


def param_types(params):
    params = re.sub(r"@[\w.]+(\s*\((?:[^()]|\([^()]*\))*\))?", " ", params)
    params = re.sub(r"\bfinal\b", " ", params)
    out, depth, cur = [], 0, ""
    for ch in params:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    types = []
    for p in out:
        p = " ".join(p.split())
        if p:
            types.append(p.rsplit(" ", 1)[0] if " " in p else p)
    return types


def annotation_args(raw_header, name):
    m = re.search(r"@(?:[\w.]+\.)?" + name + r"\b\s*\(", raw_header)
    if not m:
        return ""
    depth, i = 1, m.end()
    while i < len(raw_header) and depth:
        depth += {"(": 1, ")": -1}.get(raw_header[i], 0)
        i += 1
    return raw_header[m.end():i - 1]


def first_string(s):
    m = re.search(r'"([^"]*)"', s)
    return m.group(1) if m else ""


def parse_java(src):
    """클래스와 메서드 목록을 돌려준다.
    method: {cls, name, key, sig, start, end, body, annots, endpoint}"""
    code, raw = blank(src)
    nl = [i for i, ch in enumerate(code) if ch == "\n"]
    line = lambda pos: bisect.bisect_left(nl, pos) + 1
    classes, methods, stack = [], [], []
    seg, paren = 0, 0

    def header_at(end):
        h = code[seg:end]
        lead = len(h) - len(h.lstrip())
        return seg + lead, h.strip(), raw[seg + lead:end].strip()

    def method_from(start, h, rh, end_pos, body):
        flat = re.sub(r"\s+", " ", h)
        m = METHOD_RE.search(flat)
        if not m or m.group(1) in KEYWORDS:
            return None
        if "=" in re.sub(r"\((?:[^()]|\([^()]*\))*\)", "", flat) or "->" in flat:
            return None
        name = m.group(1)
        types = param_types(re.sub(r"\s+", " ", raw_sig_params(rh, name)))
        cls = stack[-1]
        annots = set(a.split(".")[-1] for a in ANNOT_RE.findall(rh))
        ep = endpoint_of(annots, rh, cls)
        return {"cls": cls["name"], "name": name, "key": f"{name}({', '.join(types)})",
                "start": line(start), "end": line(end_pos), "body": body,
                "annots": sorted(annots), "endpoint": ep}

    for i, ch in enumerate(code):
        if ch == "(":
            paren += 1
        elif ch == ")":
            paren -= 1
        elif paren:
            continue
        elif ch == ";":
            if stack and stack[-1]["kind"] == "class":
                start, h, rh = header_at(i)
                m = method_from(start, h, rh, i, "") if h else None
                if m:
                    methods.append(m)
            seg = i + 1
        elif ch == "{":
            start, h, rh = header_at(i)
            flat = re.sub(r"\s+", " ", h)
            cm = CLASS_RE.search(flat)
            entry = {"kind": "other", "open": i}
            pre = re.sub(r"\((?:[^()]|\([^()]*\))*\)", "", flat.split(cm.group(0))[0]) if cm else ""
            if cm and "=" not in pre and "new " not in pre and "->" not in pre:
                outer = next((s["name"] for s in reversed(stack) if s["kind"] == "class"), None)
                tail = flat[cm.end():]
                supers = re.findall(r"(?:extends|implements)\s+([\w.<>,\s?]+?)(?=\s+(?:extends|implements|permits)\b|$)", tail)
                names = set()
                for grp in supers:
                    for t in re.sub(r"<[^<>]*>", "", re.sub(r"<[^<>]*>", "", grp)).split(","):
                        if t.strip():
                            names.add(t.strip().split(".")[-1])
                rmap = annotation_args(rh, "RequestMapping")
                entry = {"kind": "class", "name": f"{outer}.{cm.group(2)}" if outer else cm.group(2),
                         "simple": cm.group(2), "supers": sorted(names),
                         "prefix": first_string(rmap), "open": i}
                classes.append(entry)
            elif stack and stack[-1]["kind"] == "class" and h:
                entry = {"kind": "method", "open": i, "start": start, "h": h, "rh": rh}
            stack.append(entry)
            seg = i + 1
        elif ch == "}":
            if stack:
                e = stack.pop()
                if e["kind"] == "method":
                    m = method_from(e["start"], e["h"], e["rh"], i, code[e["open"]:i + 1])
                    if m:
                        methods.append(m)
            seg = i + 1
    return classes, methods


def raw_sig_params(rh, name):
    flat = re.sub(r"\s+", " ", rh)
    m = re.search(r"\b" + re.escape(name) + r"\s*\(", flat)
    if not m:
        return ""
    depth, i = 1, m.end()
    while i < len(flat) and depth:
        depth += {"(": 1, ")": -1}.get(flat[i], 0)
        i += 1
    return re.sub(r'"[^"]*"', '""', flat[m.end():i - 1])


def endpoint_of(annots, rh, cls):
    for a in annots:
        kind = ENDPOINT_ANNOTATIONS.get(a)
        if not kind:
            continue
        args = annotation_args(rh, a)
        if kind in ("GET", "POST", "PUT", "DELETE", "PATCH", "ANY"):
            if kind == "ANY":
                mm = re.search(r"RequestMethod\.(\w+)", args)
                kind = mm.group(1) if mm else "ANY"
            path = (cls.get("prefix", "") + "/" + first_string(args)).replace("//", "/").rstrip("/") or "/"
            return {"kind": "API", "label": f"{kind} {path}"}
        detail = " ".join(args.split())
        if len(detail) > 120:
            detail = detail[:117] + "..."
        return {"kind": kind, "label": f"@{a}({detail})" if detail else f"@{a}"}
    return None


# ---------------------------------------------------------------- diff 파싱

def split_patch(text):
    files, cur = [], None
    for ln in text.splitlines(keepends=True):
        if ln.startswith("diff --git "):
            cur = {"lines": [ln]}
            files.append(cur)
        elif cur is not None:
            cur["lines"].append(ln)
    return ["".join(f["lines"]) for f in files]


def analyze_patch(patch):
    old = new = None
    status = "M"
    add = dele = 0
    old_lines, new_lines = set(), set()
    binary = False
    o = n = 0
    for ln in patch.splitlines():
        if ln.startswith("--- "):
            old = None if ln[4:] == "/dev/null" else ln[6:]
        elif ln.startswith("+++ "):
            new = None if ln[4:] == "/dev/null" else ln[6:]
        elif ln.startswith("rename from "):
            old, status = ln[12:], "R"
        elif ln.startswith("rename to "):
            new = ln[10:]
        elif ln.startswith("new file mode"):
            status = "A"
        elif ln.startswith("deleted file mode"):
            status = "D"
        elif ln.startswith("Binary files"):
            binary = True
        elif ln.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)", ln)
            o, n = int(m.group(1)), int(m.group(2))
        elif ln.startswith("+") and not ln.startswith("+++"):
            new_lines.add(n)
            n += 1
            add += 1
        elif ln.startswith("-") and not ln.startswith("---"):
            old_lines.add(o)
            o += 1
            dele += 1
        elif ln.startswith(" "):
            o += 1
            n += 1
    if old is None and new is None:
        m = re.match(r"diff --git a/(.+) b/(.+)", patch.splitlines()[0])
        old, new = m.group(1), m.group(2)
    if status == "A":
        old = None
    if status == "D":
        new = None
    return {"old": old, "new": new, "status": status, "add": add, "del": dele,
            "old_lines": old_lines, "new_lines": new_lines, "binary": binary}


def first_changed_line(methods, key, lines):
    """key 메서드 범위 안에서 가장 앞선 변경 줄 번호(없으면 None)."""
    m = next((m for m in methods if (m["cls"], m["key"]) == key), None)
    return min((l for l in lines if m and m["start"] <= l <= m["end"]), default=None)


def changed_methods(methods, lines):
    hit, outside = {}, 0
    for ln in lines:
        inner = None
        for m in methods:
            if m["start"] <= ln <= m["end"] and (inner is None or m["start"] >= inner["start"]):
                inner = m
        if inner is None:
            outside += 1
        else:
            hit[(inner["cls"], inner["key"])] = hit.get((inner["cls"], inner["key"]), 0) + 1
    return hit, outside


def only_imports(patch):
    body = [l[1:].strip() for l in patch.splitlines()
            if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    body = [l for l in body if l]
    return bool(body) and all(l.startswith(("import ", "package ")) for l in body)


# ---------------------------------------------------------------- 호출 그래프

class Index:
    def __init__(self, repo, java_files):
        self.methods = []          # 전체 메서드
        self.file_idents = {}      # file -> set(identifier)
        self.supers = {}           # simple class -> set(super simple)
        for f in java_files:
            if "/src/test/" in f or not f.endswith(".java"):
                continue
            try:
                src = open(os.path.join(repo, f), encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            classes, methods = parse_java(src)
            self.file_idents[f] = set(re.findall(r"\w+", blank(src)[0]))
            for c in classes:
                self.supers.setdefault(c["simple"], set()).update(c["supers"])
            for m in methods:
                m["file"] = f
                m["id"] = f"{m['cls']}#{m['key']}"
                m["simple"] = m["cls"].split(".")[-1]
                self.methods.append(m)
        self.memo = {}
        self.by_file = {}
        for m in self.methods:
            self.by_file.setdefault(m["file"], []).append(m)

    def type_names(self, simple):
        seen, todo = set(), [simple]
        while todo:
            t = todo.pop()
            if t not in seen:
                seen.add(t)
                todo.extend(self.supers.get(t, ()))
        return seen

    def callers(self, target):
        """target 메서드를 부를 가능성이 있는 메서드들. 이름 + 타입 참조로 추정한다."""
        if target["id"] in self.memo:
            return self.memo[target["id"]]
        pat = re.compile(r"(?:\b" + re.escape(target["name"]) + r"\s*\(|::\s*" + re.escape(target["name"]) + r"\b)")
        types = self.type_names(target["simple"])
        out = []
        for f, idents in self.file_idents.items():
            if f != target["file"] and not (types & idents):
                continue
            for m in self.by_file.get(f, ()):
                if m is not target and m["body"] and pat.search(m["body"]):
                    out.append(m)
        self.memo[target["id"]] = out
        return out


def trace_endpoints(index, seeds):
    """seeds(변경 메서드)에서 호출자를 BFS 로 거슬러 진입점을 찾는다."""
    found = {}
    for seed in seeds:
        q = deque([(seed, [seed["id"]])])
        seen = {seed["id"]}
        visits = 0
        while q and visits < MAX_VISIT:
            m, path = q.popleft()
            visits += 1
            if m.get("endpoint"):
                ep = found.setdefault(m["id"], {
                    "kind": m["endpoint"]["kind"], "label": m["endpoint"]["label"],
                    "handler": m["id"], "file": m["file"], "line": m["start"], "via": []})
                if len(ep["via"]) < 5:
                    ep["via"].append({"from": seed["id"], "path": list(reversed(path))})
                if m is not seed:
                    continue
            if len(path) > MAX_DEPTH:
                continue
            for c in index.callers(m):
                if c["id"] not in seen:
                    seen.add(c["id"])
                    q.append((c, path + [c["id"]]))
    return sorted(found.values(), key=lambda e: (e["kind"] != "API", e["label"]))


# ---------------------------------------------------------------- 위험도

def base_risk(f):
    if f["binary"]:
        return "L"
    if f["kind"] == "test" or f["trivial"]:
        return "L"
    score = len(f["methods"]) * 2 + (f["add"] + f["del"]) / 20
    if any(h in f["path"].lower() for h in SENSITIVE_HINTS) or f["path"].endswith((".sql", ".yml", ".yaml", ".properties")):
        score += 3
    if any(m["change"] == "D" for m in f["methods"]):
        score += 2
    if f["endpoints"]:
        score += 3
    return "H" if score >= 10 else "M" if score >= 4 else "L"


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", help="비교 기준 ref. 생략하면 기본 브랜치와의 merge-base")
    ap.add_argument("--out", help="출력 폴더. 생략하면 임시 폴더 아래 diff-review/<repo>-<branch>")
    ap.add_argument("--no-trace", action="store_true", help="진입점 추적을 건너뛴다")
    a = ap.parse_args()

    repo = git(a.repo, "rev-parse", "--show-toplevel").strip()
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if a.base:
        base_ref = a.base
    else:
        head = git(repo, "rev-parse", "--abbrev-ref", "origin/HEAD", check=False).strip()
        base_ref = head if head and head != "origin/HEAD" else next(
            (b for b in ("main", "master") if git(repo, "rev-parse", "--verify", "-q", b, check=False).strip()), None)
        if not base_ref:
            sys.exit("기본 브랜치를 찾지 못했다. --base 로 지정한다.")
    base = git(repo, "merge-base", "HEAD", base_ref).strip()

    safe_branch = re.sub(r"[^\w.-]", "_", branch)
    out = a.out or os.path.join(tempfile.gettempdir(), "diff-review", f"{os.path.basename(repo)}-{safe_branch}")
    shutil.rmtree(os.path.join(out, "files"), ignore_errors=True)
    os.makedirs(os.path.join(out, "files"), exist_ok=True)

    # 커밋된 변경 + 작업 트리 변경(staged/unstaged) + untracked 파일
    patch_text = git(repo, "diff", "-M", "--no-color", "--no-ext-diff", base)
    untracked = [u for u in git(repo, "ls-files", "--others", "--exclude-standard").splitlines() if u]
    for u in untracked:
        r = subprocess.run(["git", "-C", repo, "diff", "--no-color", "--no-index", "--", "/dev/null", u],
                           capture_output=True, text=True)
        patch_text += r.stdout
    open(os.path.join(out, "diff.patch"), "w").write(patch_text)

    tracked_java = [f for f in git(repo, "ls-files", "*.java").splitlines()]
    index = None if a.no_trace else Index(repo, tracked_java + [u for u in untracked if u.endswith(".java")])

    files, seeds_by_file = [], {}
    for i, patch in enumerate(split_patch(patch_text)):
        p = analyze_patch(patch)
        path = p["new"] or p["old"]
        pf = f"files/{i:03d}.patch"
        open(os.path.join(out, pf), "w").write(patch)
        f = {"path": path, "old_path": p["old"] if p["status"] == "R" else None, "status": p["status"],
             "add": p["add"], "del": p["del"], "binary": p["binary"], "patch": pf,
             "kind": "test" if "/src/test/" in path or "/test/" in path else "main",
             "methods": [], "class_level_lines": 0, "endpoints": []}
        if path.endswith(".java") and not p["binary"]:
            new_src = old_src = ""
            if p["new"]:
                try:
                    new_src = open(os.path.join(repo, p["new"]), encoding="utf-8", errors="replace").read()
                except OSError:
                    pass
            if p["old"]:
                old_src = git(repo, "show", f"{base}:{p['old']}", check=False)
            _, new_m = parse_java(new_src)
            _, old_m = parse_java(old_src)
            new_keys = {(m["cls"], m["key"]) for m in new_m}
            old_keys = {(m["cls"], m["key"]) for m in old_m}
            hit_new, out_new = changed_methods(new_m, p["new_lines"])
            hit_old, out_old = changed_methods(old_m, p["old_lines"])
            f["class_level_lines"] = out_new + out_old
            for k in sorted(set(hit_new) | set(hit_old), key=lambda k: -(hit_new.get(k, 0) + hit_old.get(k, 0))):
                change = "A" if k not in old_keys else "D" if k not in new_keys else "M"
                src_m = next(m for m in (new_m if change != "D" else old_m) if (m["cls"], m["key"]) == k)
                f["methods"].append({"sig": f"{k[0]}#{k[1]}", "change": change,
                                     "lines": hit_new.get(k, 0) + hit_old.get(k, 0), "line": src_m["start"],
                                     "new_at": first_changed_line(new_m, k, p["new_lines"]),
                                     "old_at": first_changed_line(old_m, k, p["old_lines"]),
                                     "endpoint": (src_m["endpoint"] or {}).get("label")})
            if index and f["kind"] == "main":
                ids = {m["sig"] for m in f["methods"] if m["change"] != "D"}
                seeds_by_file[path] = [m for m in index.methods if m["file"] == path and m["id"] in ids]
        f["trivial"] = f["status"] == "D" or (f["add"] + f["del"]) <= 4 or only_imports(patch)
        files.append(f)

    endpoints = []
    if index:
        all_seeds = [s for ss in seeds_by_file.values() for s in ss]
        endpoints = trace_endpoints(index, all_seeds)
        for f in files:
            ids = {s["id"] for s in seeds_by_file.get(f["path"], [])}
            f["endpoints"] = sorted({e["label"] for e in endpoints if any(v["from"] in ids for v in e["via"])})
    for f in files:
        f["risk_base"] = base_risk(f)

    meta = {"repo": os.path.basename(repo), "branch": branch, "base_ref": base_ref, "base": base[:12],
            "files": files, "endpoints": endpoints,
            "added": [f["path"] for f in files if f["status"] == "A"],
            "deleted": [f["path"] for f in files if f["status"] == "D"],
            "renamed": [[f["old_path"], f["path"]] for f in files if f["status"] == "R"]}
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)

    # LLM 이 읽을 최소 요약만 출력한다
    print(f"OUT={out}")
    print(f"{meta['repo']} {branch} vs {base_ref}@{meta['base']} | files={len(files)} endpoints={len(endpoints)}")
    print("patch | risk | st | +/- | methods | path")
    for f in sorted(files, key=lambda f: (-len(f["methods"]), -(f["add"] + f["del"]))):
        mark = " (trivial)" if f["trivial"] else ""
        print(f"{f['patch']} | {f['risk_base']} | {f['status']} | +{f['add']}/-{f['del']} | "
              f"{len(f['methods'])} | {f['path']}{mark}")


if __name__ == "__main__":
    main()
