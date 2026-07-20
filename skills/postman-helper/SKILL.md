---
name: postman-helper
description: >
  Use when the user asks to find or search Postman API endpoints, look up a
  request's query/path parameters, headers, body, or auth, list Postman
  workspaces or collections, inspect an exported collection JSON file, or run
  (send/execute/호출) a saved Postman request. Triggers: "Postman 엔드포인트 찾아줘",
  "이 API 파라미터 뭐야", "요청 파라미터 조회", "컬렉션에서 검색", "Postman 컬렉션",
  "이 요청 실행해줘/보내줘/호출해줘", "collection.json", "workspace 목록".
  Prefer this over Postman MCP for read and guarded-run tasks.
---

# Postman Helper

This skill searches Postman collections and inspects request definitions from
two sources — the Postman cloud API (`X-Api-Key`) or a local exported collection
JSON file — and can execute saved requests through a hard safety gate. It returns
compact, secret-redacted output and avoids Postman MCP's context cost.

Keep this file as the router. For any real task, first read
`~/.config/postman-helper/MEMORY.md` if it exists and honor saved workspace,
collection, file-path, and local base-URL preferences. Then read only the routed
reference file(s), and call the Python scripts from this skill's `scripts/`
directory. Always use the absolute installed skill directory (`<SKILL_DIR>`) when
running scripts or showing commands — never cwd-relative `skills/...` paths.

## Identity

- 모든 사용자 안내는 한글로 한다.
- 설정 확인을 별도 사전 단계로 만들지 않는다. 요청받은 작업의 스크립트를 바로
  실행하고, `Missing config file` 같은 오류가 났을 때 비로소 `references/setup-guide.md`를
  읽어 한 응답에 한 단계씩 안내한다.
- Postman API key를 채팅에 붙여넣으라고 요구하지 않는다. 대화형 입력으로만 받는다.
- 로컬 파일 소스(`--file`)는 API key 없이 동작한다. 컬렉션 파일 경로만 있으면 된다.

## The execution gate (실행 안전 규칙)

실행 여부 판단은 프롬프트가 아니라 `postman_run.py`에 코드로 박혀 있다. 이 규칙을
우회하려 하지 말고 그대로 따른다.

- **전송은 `--send`가 있을 때만 일어난다.** `--send` 없는 `run`은 항상 미리보기다
  (헤더·바디를 보여주고 아무것도 전송하지 않는다, exit 2).
- **`--send`는 사용자가 이번 대화에서 실행을 명시적으로 요청했을 때만 붙인다**
  ("실행해줘/보내줘/호출해줘"). "찾아줘/파라미터 뭐야/확인해줘"는 실행 요청이 아니다.
  과거 턴의 실행 요청을 다른 요청에 재사용하지 않는다.
- **메서드 분류**: GET/HEAD/OPTIONS = safe · POST = confirm · **PUT/PATCH/DELETE = blocked**
  (blocked는 `--send --confirm`을 줘도 절대 실행되지 않는다).
- **환경 분류**: host가 localhost·127.x·`*.local`·`*.test`이거나 **첫 라벨**이
  `dev`/`local`(예: `dev.example.com`)이면 local, 미해결 `{{변수}}` → unknown,
  그 외 → remote. `api.dev.example.com`처럼 중간 라벨은 local로 치지 않는다.
  리다이렉트(3xx)는 따라가지 않는다 — 게이트 판정 후 다른 host로 넘어가는 것을 막기 위함.
- **`--send`만으로 전송되는 것은 `safe method + local/dev env`뿐.** 그 외는 추가로
  `--confirm`이 필요하다.
  - POST는 local이어도 사용자에게 먼저 질의하고, 동의하면 `--send --confirm`으로 재실행한다.
  - safe 메서드라도 remote/unknown 환경이면 먼저 질의한다.
  - PUT/PATCH/DELETE 요청은 실행하지 않는다. 검색·조회만 제공한다고 안내한다.
- 실행 요청이라도 내용이 확실치 않으면 먼저 `--send` 없이 미리보기를 보여주고 진행한다.
- 스크립트는 전송 불가 상황에서 판정/사유만 출력한다 (blocked→exit 0,
  확인 필요/미리보기→exit 2). 이때 사용자에게 사유를 그대로 전하고 진행 여부를 묻는다.

## Routing

| Request | Read First | Main Command |
| --- | --- | --- |
| First setup, missing config, API key, auth error | `references/setup-guide.md` | `postman_setup.py init-key`, `auth-test` |
| 워크스페이스/컬렉션 목록 (클라우드) | `references/scripts-reference.md` | `postman_collections.py workspaces`, `collections` |
| 엔드포인트 검색, 메서드/키워드 필터 | `references/scripts-reference.md` | `postman_collections.py endpoints` |
| 특정 요청의 파라미터/헤더/바디/auth 조회 | `references/scripts-reference.md` | `postman_collections.py request` |
| 저장된 요청 실행 (안전 게이트) | `references/scripts-reference.md` | `postman_run.py run` |

## Data sources

모든 조회·실행 명령은 두 소스 중 하나를 받는다.

- `--collection <uid>` — Postman 클라우드 API에서 컬렉션을 가져온다 (API key 필요).
  uid는 `collections`로 먼저 찾는다.
- `--file <path>` — 로컬에 export한 컬렉션 JSON을 읽는다 (API key 불필요).

`workspaces`/`collections`는 클라우드 전용이다.

## Local Files

`~/.config/postman-helper/`에 파일 두 개만 둔다. 디렉토리는 `700`, 파일은 `600`.

- `config.json` — API key 프로필(`profiles`, `default_profile`)의 단일 저장소.
  스크립트만 읽고 쓴다.
- `MEMORY.md` — 에이전트가 Read/Edit로 관리하는 자유형 markdown. 워크스페이스·컬렉션
  별칭, 로컬 컬렉션 파일 경로, 자주 찾는 엔드포인트, local/dev base URL, 선호를 담는다.
  **API key·토큰·요청 바디·응답 본문은 절대 기록하지 않는다.**

## Scripts

- `postman_setup.py`: `init-key`, `auth-test`, `profiles`
- `postman_collections.py`: `workspaces`, `collections`, `endpoints`, `request`
- `postman_run.py`: `run` (기본 미리보기; 전송은 `--send`, 비자동 케이스는 `--send --confirm`, `--var k=v`)
- `postman_common.py`: import-only 공유 구현 (파서·게이트·redaction)

## Rules

- **기본은 조회다.** 사용자가 실행을 명시적으로 요청하지 않았다면 `--send`를 절대
  붙이지 않는다. "찾아줘/파라미터 뭐야"류는 절대 실행으로 넘어가지 않는다 —
  요청 내용이 궁금하면 `request` 조회나 `--send` 없는 미리보기로 답한다.
- 넓게 찾을 때는 `endpoints`로 먼저 검색하고, 특정 요청만 `request`로 상세 조회한다.
- 헤더·변수의 민감값(Authorization/token/secret/api key 등)은 조회 출력에서 자동
  redact된다. 실제 값은 실행 시에만 쓰이고 화면에 노출하지 않는다.
- `request`/`run`은 이름·경로가 여러 건에 걸리면 목록만 보여주고 멈춘다. 사용자가
  좁히거나 `--first`를 줄 때만 단건으로 진행한다.
- `{{변수}}`가 host에 남아 환경 판정이 unknown이면 자동 실행하지 않는다. `--var
  base_url=...`로 채워 판정을 확정한 뒤 진행한다.
- API 오류(missing config, 401/403)는 설정 신호로 보고 `references/setup-guide.md`로 라우팅한다.
- 로그·응답 본문을 레포 파일에 쓰지 않는다. MEMORY에는 사용자 승인한 접근 힌트만 남긴다.

## Memory

`MEMORY.md`는 다음 세션이 다시 찾지 않도록 접근 지식을 담는다.

- **워크스페이스/컬렉션**: 사용자가 부르는 이름 ↔ 실제 uid/이름
- **로컬 컬렉션 파일 경로**: 자주 여는 export JSON 경로
- **자주 찾는 엔드포인트**: 컬렉션 + 요청 이름/경로 조합
- **실행 환경**: local/dev base URL (예: `base_url=http://localhost:8080`)
- **선호**: 기본 소스(cloud/file), 기본 워크스페이스 등

기록 트리거:

1. **명시형**: 사용자가 "기억해/저장해둬/memory"라고 하면, 대상이 명확하면 바로
   알맞은 섹션에 추가하고 추가한 줄을 그대로 보여준다. 모호하면 후보를 제시하고 한 번 묻는다.
2. **탐지형**: 요청 안에 사용자가 알려주지 않으면 모를 사실(컬렉션 uid, 로컬 파일
   경로, local base URL 등)이 있으면 작업을 끝낸 뒤 "이 내용을 MEMORY에 저장할까요? —
   <저장할 한 줄>"로 묻는다.

API key·토큰·요청/응답 본문은 어떤 경우에도 저장하지 않는다.

```markdown
# postman-helper memory

## 워크스페이스 / 컬렉션
- (예) orders — uid 12345-abcd... — 주문 API 컬렉션

## 로컬 컬렉션 파일 경로
- (예) orders-api — ~/exports/orders.postman_collection.json

## 자주 찾는 엔드포인트
- (예) 주문 생성 — orders 컬렉션 / POST /orders

## 실행 환경 (local/dev base URL)
- (예) local — base_url=http://localhost:8080

## 선호
- (예) 기본 소스는 로컬 파일
```
