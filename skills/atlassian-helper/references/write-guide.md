# Write Guide (생성 / 수정 / 삭제)

Use this file whenever the request changes something in Jira or Confluence.

## 작성자 판정

게이트 자체는 `SKILL.md`의 Safety Model에 있다. 여기서는 스크립트가 무엇을 보고
판정하는지만 다룬다.

- Jira 이슈: `creator` (없으면 `reporter`)
- Jira 코멘트: 코멘트 `author`
- Confluence 페이지: `authorId` (최초 작성자, 마지막 수정자가 아님)

남의 티켓/문서를 수정·삭제해야 하는 상황이면 실행하지 말고 이렇게 안내한다.

```text
이 티켓은 <작성자>님이 만든 거라 수정/삭제는 막혀 있어요.
대신 코멘트를 남기거나 작성자에게 요청하는 방법이 있습니다.
```

## 본문 작성 형식

`--body` / `--description`는 평문으로 넣는다. 스크립트가 Jira는 ADF로,
Confluence는 storage XHTML로 변환한다.

- 빈 줄 → 새 문단
- `- ` 또는 `* ` 로 시작하는 줄 → 글머리 목록
- `# ` / `## ` / `### ` → 제목
- 그 외에는 평문 그대로 (Jira 위키 마크업이나 HTML은 해석되지 않는다)

긴 본문은 `--body-file <path>` 또는 `--body-file -` (stdin)을 쓴다. 셸 인용
문제가 있는 한글/특수문자 본문은 파일 경로가 안전하다.

Confluence에서 표·매크로 같은 원본 XHTML을 그대로 넣어야 하면 `--storage`를
붙이고 storage 형식으로 직접 작성한다.

## Jira 쓰기

티켓 생성 (`--type` 기본값 `Task`):

```bash
python3 "<SKILL_DIR>/scripts/jira.py" create --project ABC --type Bug \
  --summary "결제 실패 시 에러 메시지 노출" \
  --description-file /tmp/desc.md --assignee-me --label backend --duedate 2026-08-20
```

코멘트 추가 (남의 티켓에도 가능 — 생성은 안전 작업):

```bash
python3 "<SKILL_DIR>/scripts/jira.py" comment ABC-123 --body "확인했습니다. 배포 후 재현 여부 다시 볼게요."
```

내가 만든 티켓 수정:

```bash
python3 "<SKILL_DIR>/scripts/jira.py" edit ABC-123 --summary "새 제목" --duedate 2026-08-25
```

`--label`은 라벨 전체를 지정한 값들로 **교체**한다. 기존 라벨을 유지하려면
`issue ABC-123`으로 현재 라벨을 먼저 확인하고 함께 넘긴다.

상태 변경 (전환 이름 / 도착 상태 이름 / 전환 id 모두 허용):

```bash
python3 "<SKILL_DIR>/scripts/jira.py" transitions ABC-123
python3 "<SKILL_DIR>/scripts/jira.py" transition ABC-123 --to "In Progress"
```

삭제 (되돌릴 수 없음):

```bash
python3 "<SKILL_DIR>/scripts/jira.py" delete ABC-123 --yes
```

내 코멘트 수정/삭제 (id는 `issue ABC-123 --comments 5` 출력의 `[id=...]`):

```bash
python3 "<SKILL_DIR>/scripts/jira.py" comment-edit ABC-123 --id 10021 --body "내용 정정"
python3 "<SKILL_DIR>/scripts/jira.py" comment-delete ABC-123 --id 10021 --yes
```

## Confluence 쓰기

페이지 생성 (`--space`는 스페이스 키, `--parent`는 상위 페이지 ID):

```bash
python3 "<SKILL_DIR>/scripts/confluence.py" create --space DEV \
  --title "결제 실패 원인 정리" --body-file /tmp/page.md --parent 1234567
```

내가 만든 페이지 수정 (버전은 자동으로 +1):

```bash
python3 "<SKILL_DIR>/scripts/confluence.py" update 1234567890 \
  --body-file /tmp/page.md --message "표 추가"
```

`--body`를 생략하면 본문은 그대로 두고 `--title`만 바꾼다.

페이지 코멘트 (안전 작업):

```bash
python3 "<SKILL_DIR>/scripts/confluence.py" comment 1234567890 --body "표 하나 추가했습니다."
```

페이지 삭제 (휴지통으로 이동):

```bash
python3 "<SKILL_DIR>/scripts/confluence.py" delete 1234567890 --yes
```

## 이미지 / 첨부 파일 업로드

현재 첨부 목록부터 확인한다 (파일명·버전·크기):

```bash
python3 "<SKILL_DIR>/scripts/confluence.py" attachments 1234567890
```

새 파일 올리기 (생성 = 안전 작업):

```bash
python3 "<SKILL_DIR>/scripts/confluence.py" attach 1234567890 \
  --file ~/Desktop/flow.png --comment "발송 플로우 다이어그램"
```

같은 이름이 이미 있으면 실행을 멈춘다. 의도적으로 갈아끼우는 경우에만
`--replace`를 붙인다 (수정 = 작성자 확인, 첨부 버전이 +1 된다):

```bash
python3 "<SKILL_DIR>/scripts/confluence.py" attach 1234567890 \
  --file /tmp/flow-v2.png --replace
```

`--replace`는 본문의 `ri:version-at-save`도 새 버전으로 맞춰준다. Confluence는
본문에 박힌 버전을 렌더하므로 이 갱신이 없으면 파일만 바뀌고 화면은 옛 이미지가
그대로 보인다. 다른 이름으로 올리고 싶으면 `--name new-name.png`을 쓴다.

새로 올린 이미지는 첨부만 된 상태다. 본문에 노출하려면 출력에 나온 조각을
`update --storage`로 원하는 위치에 넣는다:

```xml
<ac:image ac:align="center" ac:custom-width="true" ac:width="900" ac:alt="발송 플로우"><ri:attachment ri:filename="flow.png" ri:version-at-save="1" /></ac:image>
```

Jira 이슈 첨부 (생성 = 안전 작업, 남의 티켓에도 가능):

```bash
python3 "<SKILL_DIR>/scripts/jira.py" attach ABC-123 --file ~/Desktop/error.png
```

빈 파일·없는 경로·디렉터리·경로 구분자가 섞인 `--name`은 업로드 전에 거절한다.
상한은 100MB이고, 그보다 작은 실제 상한은 사이트 설정을 따른다 (Jira는 보통 10MB).

## 실행 전 체크리스트

1. 대상이 맞는가 — 프로젝트 키/스페이스 키, 이슈 키/페이지 ID를 조회로 먼저 확인.
2. 이슈 타입·상태 이름이 실제로 존재하는가 (`statuses --project ABC`,
   `transitions ABC-123`).
3. 수정/삭제라면 작성자가 본인인가 — 아니면 시도하지 말고 안내한다.
4. 사용자에게 "무엇을 / 어디에 / 어떻게" 한 줄 요약을 보여주고 진행한다.
5. 실행 후 출력된 키/ID와 URL을 사용자에게 그대로 전달한다.

## Errors

- `400` — 필드 이름/값 문제 (없는 이슈 타입, 필수 필드 누락, 잘못된 상태 전환).
  에러 본문 메시지를 읽고 이름을 교정한다. 설정 문제(401/403)와 혼동하지 않는다.
- `403` — 계정에 해당 프로젝트/스페이스 쓰기 권한이 없다. 설정이 아니라 권한
  문제임을 안내한다.
- `404` on update — 페이지 ID가 틀렸거나 이미 삭제됐다.
- Confluence `update` 충돌 — 다른 사람이 그사이 저장하면 버전 번호가 어긋난다.
  `page <id>`로 다시 읽고 재시도한다.
