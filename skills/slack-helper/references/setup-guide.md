# Slack Helper Setup Guide

Use this file when config is missing, OAuth is incomplete, scopes are unclear, or the user asks how to set up Slack search.

## Tone

설정 안내를 받는 사용자는 비개발자라고 가정한다.

- 모든 안내는 한글로 한다.
- 매우 친절하고 가독성 좋게, 초등학생도 따라할 수 있을 정도로 쓴다. 번호 매긴 단계, 한 단계에 한 동작, 화면에 보이는 버튼 이름 그대로.
- "OAuth", "scope", "token" 같은 용어가 나오면 한 줄로 풀어서 설명한다. (예: "scope는 이 앱이 Slack에서 무엇을 읽을 수 있는지 정하는 권한 목록이에요.")
- 터미널 명령은 사용자가 그대로 복사해서 붙여넣기만 하면 되도록 완성된 형태로 준다. 각 명령이 무엇을 하는지 한 줄로 설명을 붙인다.

## Paths

이 문서의 모든 `python3` 명령에 있는 `<SKILL_DIR>`은 **이 스킬이 실제 설치된 디렉토리의 절대 경로**다 (이 문서가 `<SKILL_DIR>/references/setup-guide.md`에 있으므로 여기서 역산하면 된다). 안내하거나 실행하기 전에 반드시 절대 경로로 치환한다. 사용자는 어느 디렉토리에서 터미널을 열지 알 수 없으므로, 사용자에게 보여주는 명령에 상대 경로를 절대 쓰지 않는다.

## 진행 방식 (Step Gating)

설정은 아래 1~5단계를 순서대로 진행한다. **한 응답에는 한 단계만 안내한다.**

- 다음 단계 내용을 미리 보여주지 않는다. "완료되면 알려주세요"로 각 단계를 끝맺는다.
- 사용자가 완료했다고 하면, 각 단계에 적힌 확인 방법으로 실제 상태를 검증한 뒤 다음 단계로 넘어간다. 확인이 실패하면 어디까지 됐는지 물어보고 그 지점부터 다시 안내한다.
- 이미 끝난 단계가 확인되면(예: `~/.config/slack-helper/config.json`에 `app` 설정 존재) 그 단계는 건너뛰고 다음 단계부터 시작한다.

## 1단계: Slack 앱 만들기 (브라우저에서)

아래 안내를 그대로 보낸다 (이 말투를 유지한다):

```text
1단계: Slack 앱 만들기 (브라우저에서)

1. 브라우저에서 아래 주소를 열어주세요.
   👉 https://api.slack.com/apps
2. 오른쪽에 있는 초록색 Create New App 버튼을 눌러요.
3. 두 가지 중에 고르라고 나오면 From scratch (맨 위)를 눌러요.
4. 칸을 채워요.
   - App Name: slack-helper-local 이라고 적어요.
   - Pick a workspace: 메시지를 검색하고 싶은 Slack 워크스페이스를 골라요.
5. Create App 버튼을 눌러요.

💡 여기서 만드는 "앱"은 제가 회원님 Slack을 대신 읽을 수 있게 해주는 열쇠 같은 거예요.
   회원님 계정 안에서만 쓰이고, 외부로 나가지 않아요.

앱이 만들어지면 Basic Information 화면이 나와요.
그 화면을 아래로 내려서 App Credentials가 보이면 정상적으로 완료한 거예요.
완료하면 다음으로 넘어갈게요. "완료"라고 말씀해주세요!
```

**에이전트 확인:** 브라우저 작업이라 로컬에서 검증할 수 없다. 사용자가 완료했다고 하면 2단계로 넘어간다.

## 2단계: Client ID / Client Secret 등록 (터미널에서)

아래 안내를 그대로 보낸다 (이 말투를 유지한다):

```text
2단계: Client ID / Client Secret 등록

앱을 만들면 바로 Basic Information 화면이 나와요. 거기서 두 가지 값을 등록할 거예요.

- 그 화면을 아래로 내리면 App Credentials 부분에 Client ID와 Client Secret이 있어요.
  - Client ID는 그냥 보여요.
  - Client Secret은 옆의 Show 버튼을 눌러야 보여요.
- 이제 터미널에 아래 명령을 복사해서 붙여넣고 실행해주세요.
  이 명령을 실행하면 Client ID와 Client Secret을 순서대로 물어봐요.

python3 "<SKILL_DIR>/scripts/slack_setup.py" init-oauth

입력할 때 참고하세요:
- Client Secret은 안전하게 보호되어서, 입력할 때 화면에 글자가 안 보여요.
  (정상이에요! 그냥 붙여넣고 Enter를 누르면 돼요.)
- 잘 끝나면 터미널에 ✅ Client ID / Client Secret 등록에 성공했어요! 라고 나와요.

🔒 Client Secret은 채팅창에 붙여넣지 마세요! 오직 위 터미널 명령을 통해서만 안전하게 입력돼요.

등록하고 나서 "완료"라고 말씀해주세요.
```

`init-oauth`는 Client ID와 Client Secret 두 가지만 입력받는다. Redirect URI와 범위(scope)는 묻지 않고 기본값으로 저장되며, 다음 단계에서 사용자가 Slack 웹 화면에 직접 등록한다. Slack 이름/@핸들도 여기서는 묻지 않는다 — 5단계의 연결 테스트 후에 물어본다.

`Client Secret`은 채팅·명령 인자·파일로 절대 받지 않는다. `init-oauth`의 대화형 프롬프트가 유일한 입력 경로다.

**에이전트 확인:** 사용자가 완료를 알리면 `~/.config/slack-helper/config.json`이 생겼는지 확인한다 (`test -f ~/.config/slack-helper/config.json`). 있으면 "등록 확인했어요!" 하고 3단계로. 없으면 어느 지점에서 막혔는지 물어보고 다시 안내한다.

## 3단계: 권한 설정 (브라우저에서)

Slack 앱 화면의 왼쪽 메뉴에서 **OAuth & Permissions**를 누르게 한 뒤, 두 가지를 순서대로 안내한다.

1. **Redirect URLs** — 앱이 승인 결과를 돌려받을 주소 등록:
   - `Add New Redirect URL`을 누르고 아래 주소를 그대로 붙여넣는다.
   - `http://localhost:8765/slack-helper/callback`
   - `Add` → `Save URLs`를 차례로 누른다.
2. 같은 화면을 아래로 내려 **Scopes(범위)** — 이 앱이 Slack에서 무엇을 읽을 수 있는지 정하는 권한 목록:
   - **봇 토큰 범위(Bot Token Scopes)**의 `Add an OAuth Scope`에서 아래 4개를 하나씩 추가한다.
     - `team:read` — 워크스페이스 기본 정보 읽기
     - `users:read` — 사용자 목록 읽기
     - `channels:read` — 공개 채널 목록 읽기
     - `channels:history` — 공개 채널 대화 읽기
   - **사용자 토큰 범위(User Token Scopes)**의 `Add an OAuth Scope`에서 아래 1개를 추가한다.
     - `search:read` — 메시지 검색 (검색은 이 사용자 범위가 꼭 필요하다. 봇 범위만으로는 검색이 안 된다.)

안내는 "여기까지 다 됐으면 완료됐다고 말해주세요."로 끝맺는다.

**에이전트 확인:** 이 단계는 Slack 웹 화면 작업이라 로컬에서 검증할 수 없다. 사용자가 완료했다고 하면 4단계로 넘어간다 (실수는 4단계 승인 과정에서 에러로 드러나므로 그때 되짚는다).

## 4단계: Slack 연결 승인 (브라우저 + 붙여넣기)

1. 에이전트가 승인 화면을 브라우저로 연다:

```bash
python3 "<SKILL_DIR>/scripts/slack_setup.py" oauth-start --open
```

2. 사용자에게 안내한다:
   - 브라우저에 Slack 허용(Allow) 화면이 뜨면 **허용** 버튼을 눌러 주세요.
   - 허용을 누르면 화면이 이동하는데, **"사이트에 연결할 수 없음" 같은 오류 페이지가 떠도 정상이에요.** 걱정하지 마세요.
   - 그 상태에서 **브라우저 맨 위 주소창의 주소를 전체 복사해서 여기에 그대로 붙여넣어 주세요.** (주소 안에 `code=...`가 들어 있어요.)
3. 사용자가 주소를 붙여넣으면 에이전트가 토큰으로 교환한다:

```bash
python3 "<SKILL_DIR>/scripts/slack_setup.py" oauth-finish --url "붙여넣은_주소_전체" --workspace default
```

**에이전트 확인:** `oauth-finish`가 `"ok": true`를 출력하면 5단계로 바로 이어간다. 실패하면 에러 내용(`invalid_scope`, `bad_redirect_uri` 등)을 한글로 풀어 설명하고 3단계의 해당 항목으로 되돌아간다.

## 5단계: 연결 확인 + 첫 결과 보여주기

이 단계는 사용자에게 시키는 일 없이 에이전트가 이어서 실행한다.

1. 연결 확인:

```bash
python3 "<SKILL_DIR>/scripts/slack_setup.py" read-sample --workspace default
```

2. 성공하면 사용자에게 **"성공했습니다! 🎉 Slack 연결이 모두 끝났어요."**라고 알린다.
3. 내 계정 식별자 확정. 연결 성공 안내에 바로 이어서 이렇게 물어본다:

```text
마지막으로 하나만요 — 당신은 누구신가요? 🙂
Slack 표시 이름, @핸들, member ID(U로 시작) 중 아무거나 알려주세요.
회원님을 부른 멘션을 찾을 때 써요.
```

   사용자가 답하면 `set-me`로 저장하고 `resolve-me`로 실제 Slack 계정과 맞는지 확인한다:

```bash
python3 "<SKILL_DIR>/scripts/slack_setup.py" set-me --slack-user "슬랙_이름" --workspace default
python3 "<SKILL_DIR>/scripts/slack_setup.py" resolve-me --workspace default
```

   - **저장된 이름이 실제 Slack 사용자와 정확히 일치하지 않으면** `resolve-me`가 실패하면서 비슷한 사용자 후보(`U... / @handle / 표시 이름`)를 함께 보여준다. 후보가 안 나오면 사용자 목록에서 직접 찾는다:

```bash
python3 "<SKILL_DIR>/scripts/slack_read.py" users --limit 100
```

   - 후보를 사용자에게 보여주고 "혹시 이 중에 회원님이 있나요?"라고 확인한 뒤, 맞는 후보의 `U...` ID로 다시 저장하고 재확인한다:

```bash
python3 "<SKILL_DIR>/scripts/slack_setup.py" set-me --slack-user-id U0123ABCD --workspace default
python3 "<SKILL_DIR>/scripts/slack_setup.py" resolve-me --workspace default
```

4. 최근 멘션 3개를 찾아서 보여준다:

```bash
python3 "<SKILL_DIR>/scripts/slack_search.py" search --to-me --days 30 --count 3
```

   - 결과는 한글로 정리한다: 채널, 보낸 사람, 한 줄 요약.
   - 멘션이 없으면 "최근 30일 동안 저를 부른 멘션은 없었어요."라고 알린다.

5. 마무리 메시지. Python 명령은 보여주지 않고 자연어 예시만 보여준다:

```text
설정이 끝났어요. 이제 이런 식으로 물어보시면 제가 Slack에서 찾아서 정리해드릴게요.

- 내 최근 멘션 뭐 있어?
- 이번 주에 나를 멘션한 메시지 정리해줘
- 어제 장애 관련해서 나온 이야기 찾아줘
- 특정 채널에서 온보딩 관련 논의 요약해줘
- OO 프로젝트 관련 최근 결정사항 찾아줘
```

## Optional: 자주 쓰는 채널 기억하기

자주 쓰는 채널이 있으면 `~/.config/slack-helper/MEMORY.md`의 `## 채널` 섹션에 기록해두자고 제안할 수 있다 (설정 흐름의 필수 단계는 아니다). 채널 ID는 아래로 찾는다.

```bash
python3 "<SKILL_DIR>/scripts/slack_read.py" channels --limit 100
```

기록 형식은 `- 별칭 — C채널ID — 한 줄 요약`이며, 에이전트가 Read/Edit로 직접 관리한다 (SKILL.md의 Memory 규칙을 따른다). 사용자가 확인한 내용만 저장한다.

## Avoid

- 한 응답에 여러 단계를 몰아서 안내하기.
- Running arbitrary test searches such as `배포`. (5단계의 `--to-me` 멘션 검색만 예외)
- Asking for a search keyword before identity is saved.
- Printing tokens, client secrets, or `.env` values.
- Presenting `python3 ...` commands as the user-facing product flow after setup.
