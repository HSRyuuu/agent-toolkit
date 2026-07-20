# Postman Helper Scripts Reference

Use this file for endpoint search, request inspection, and guarded execution.
All commands run from `<SKILL_DIR>/scripts/`.

## Common Pattern

1. Read `~/.config/postman-helper/MEMORY.md` first if it exists.
2. Pick a source: `--file <path>` (local, no key) or `--collection <uid>` (cloud).
   Cloud uid는 `collections`로 먼저 찾는다.
3. Search broad with `endpoints`, then inspect one with `request`.
4. Execute only when the user asks AND the safety gate allows — via `run`.
5. Update `MEMORY.md` when a collection uid, local file path, or local base URL
   proves reusable.

## Scripts

| Script | Use For | Commands |
| --- | --- | --- |
| `postman_setup.py` | API key setup/checks | `init-key`, `auth-test`, `profiles` |
| `postman_collections.py` | Read collections | `workspaces`, `collections`, `endpoints`, `request` |
| `postman_run.py` | Guarded execution | `run` |
| `postman_common.py` | Shared impl | import-only; do not call as CLI |

## Command Selection

| Need | Command |
| --- | --- |
| 어떤 워크스페이스가 있나 (클라우드) | `workspaces` |
| 워크스페이스 안의 컬렉션 + uid (클라우드) | `collections [--workspace <id>]` |
| 엔드포인트 목록/검색 | `endpoints --query <text> [--method GET]` |
| 특정 요청의 파라미터/헤더/바디 | `request "<name or path>"` |
| 저장된 요청 실행 | `run "<name or path>"` (게이트 통과 시) |

## endpoints — 검색

```bash
# 로컬 파일에서 'order' 관련 GET 엔드포인트
python3 postman_collections.py endpoints --file ~/exports/orders.json --query order --method GET

# 클라우드 컬렉션 전체 엔드포인트 (기본 50건)
python3 postman_collections.py endpoints --collection <uid> --limit 200
```

출력: `[METHOD] /path — 요청이름  (폴더 경로)`. `--query`는 이름/경로/메서드/URL을
부분 문자열로 매칭한다.

## request — 파라미터/헤더/바디 조회

```bash
python3 postman_collections.py request --file ~/exports/orders.json "List orders"
python3 postman_collections.py request --collection <uid> "/orders" --first
```

- path variables, query params(설명 포함), headers, body(mode별 요약), auth type를 보여준다.
- Authorization·token·secret·api key 같은 민감 헤더/변수 값은 `***redacted***`로 나온다.
- 여러 건이 걸리면 목록만 보여주고 멈춘다. `--first`로 첫 건을 강제한다.

## run — 안전 게이트 실행

**`--send`가 없으면 아무것도 전송되지 않는다.** `--send`는 사용자가 이번 대화에서
실행을 명시적으로 요청했을 때만 붙인다.

```bash
# 미리보기(기본): 판정 + 헤더/바디를 보여주고 전송하지 않는다
python3 postman_run.py run --file ~/exports/orders.json "List orders" --var base_url=http://localhost:8080

# 사용자가 실행을 요청한 경우: safe(GET) + local host → --send 만으로 전송
python3 postman_run.py run --file ~/exports/orders.json "List orders" --var base_url=http://localhost:8080 --send

# POST 또는 remote GET → 사용자 동의까지 받은 뒤 --send --confirm
python3 postman_run.py run --file ~/exports/orders.json "Create order" --var base_url=http://localhost:8080 --send --confirm
```

동작:

1. 요청을 찾고 변수(`--var k=v` + 컬렉션 변수)를 치환해 URL을 확정한다.
2. 메서드/환경을 분류하고 게이트를 적용한다 (SKILL.md의 규칙과 동일).
3. 게이트 통과 + `--send`면 curl로 전송하고 `HTTP <status> (<time>s)` + 헤더(민감값
   redact) + 본문(기본 2000자로 절단)을 출력한다. 리다이렉트(3xx)는 따라가지 않고
   상태와 Location 헤더만 보여준다. URL 쿼리의 민감 파라미터 값도 출력에서 redact된다.
4. 전송하지 않는 경우 판정/사유만 출력한다.
   - blocked(PUT/PATCH/DELETE) → exit 0, 실행 불가 안내.
   - `--send` 없음(미리보기) 또는 확인 필요(POST, remote/unknown GET) → exit 2.
     사용자에게 사유를 전하고 동의를 받은 뒤에만 필요한 플래그를 붙여 재실행한다.

옵션: `--send`, `--confirm`, `--var key=value`(반복 가능), `--first`, `--max-body <n>`.

## body 실행 지원 범위

`run`은 body가 없거나 `raw`(json/text) 또는 `urlencoded`인 요청만 전송한다.
`formdata`/`file` 등은 자동 실행을 지원하지 않으므로 오류로 멈춘다 — 조회는 그대로 된다.
