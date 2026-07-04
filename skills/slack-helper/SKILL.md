---
name: slack-helper
description: Use when Slack MCP 대신 Slack Web API와 로컬 curl helper로 Slack 메시지를 검색하거나 데이터를 읽어야 할 때. 비개발자용 Slack App/OAuth 설정, Bot/User scope 등록, search:read 검색, team/user/channel 읽기 문제 확인에 사용한다.
---

# Slack Helper

## 목적

Slack MCP 없이 Slack Web API를 직접 호출할 때 사용한다. 주 목적은 Slack 메시지 검색이다. 설정 파일은 `~/.config/slack-helper` 아래에 두고, 스크립트는 OAuth 승인, 토큰 저장, 검색, 간단한 Slack 데이터 읽기를 맡는다.

사용자가 처음 설정하는 중이면 앱 생성이 첫 단계다. 첫 안내에서는 `https://api.slack.com/apps` 링크, 앱 생성 순서, 앱 생성 직후 `Basic Information`에서 `Client ID`와 `Client Secret`을 확인하는 방법, 그리고 바로 실행할 `init-oauth` 터미널 명령까지 한 응답 안에 안내한다. “앱을 다 만들었으면 알려주세요”, “브라우저를 대신 열까요?”처럼 중간에서 멈추는 질문은 하지 않는다.

그 다음 응답부터 Redirect URL, scope, OAuth 승인 순서로 하나씩 이어간다.

`init-oauth`는 항상 대화형으로 실행한다. `Client ID`를 묻고, `Client Secret`은 화면에 보이지 않게(그리고 셸 히스토리에 남지 않게) 입력받는다. Redirect URI(`http://localhost:8765/callback`), Bot scope(`team:read, users:read, channels:read, channels:history`), User scope(`search:read`)는 프롬프트에서 Enter만 누르면 기본값으로 저장된다. Slack 이름/핸들은 마지막 프롬프트에서 입력하거나, 나중에 사용자가 알려주면 에이전트가 `set-me`로 저장한다.

`Client Secret`은 명령 인자로 받지 않는다. 대화형 입력만 지원하므로 secret이 셸 히스토리나 프로세스 목록에 남지 않는다.

설정 확인 후에는 임의 키워드로 검색 테스트하지 않는다. 특히 `배포` 같은 일반 키워드를 예시 검색으로 실행하지 않는다. `team.info` 또는 `auth.test`로 workspace 연결이 확인되면, 다음 단계는 사용자의 Slack 표시 이름, `@핸들`, 또는 `U...` member ID를 물어보고 config에 저장하는 것이다.

사용자에게는 Python 스크립트 실행법을 사용법으로 보여주지 않는다. 이 스크립트는 에이전트 내부 도구다. 설정 완료 안내에서는 자연어 요청 예시만 보여준다.

## 처음 설정 순서

### 1. Slack App Management 열기

브라우저에서 다음 링크를 연다.

https://api.slack.com/apps

### 2. 앱 만들기

Slack 화면에서 다음 순서로 누른다.

1. `Create New App`
2. `From scratch`
3. `App Name`: 원하는 이름 입력. 예: `slack-helper-local`
4. `Pick a workspace`: 읽고 싶은 Slack workspace 선택
5. `Create App`

### 3. client_id와 client_secret 확인 후 로컬 설정 저장

앱 생성 후 `Basic Information` 화면에서 아래 값을 찾는다.

- `Client ID`
- `Client Secret`

아래 명령을 터미널에서 실행하면 대화형으로 값을 물어본다. `Client Secret`은 화면에 보이지 않게 입력받고 셸 히스토리에도 남지 않는다. Redirect URI와 scope는 프롬프트에서 Enter만 누르면 기본값으로 저장된다.

```bash
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" init-oauth
```

`Client Secret`은 `--client-secret` 같은 명령 인자로 받지 않는다. 대화형 입력이 유일한 방법이다. `init-oauth`는 터미널(TTY)에서만 동작하며, 파이프나 비대화형 환경에서 실행하면 명확한 에러를 낸다.

### 4. Redirect URL 등록

Slack App 화면의 왼쪽 메뉴에서 `OAuth & Permissions`로 이동한다.

`Redirect URLs` 섹션에서:

1. `Add New Redirect URL`
2. `http://localhost:8765/callback` 입력
3. `Add`
4. `Save URLs`

주의: 이 스킬은 개인 로컬 사용용이다. 실제 localhost 서버를 띄우지 않아도 된다. Slack 승인 후 `localhost` 페이지가 열리지 않더라도 주소창에 `code=...`가 보이면 그 값만 복사하면 된다.

### 5. 권한 추가

같은 `OAuth & Permissions` 화면에서 `Scopes` 섹션을 찾는다.

먼저 `Bot Token Scopes`에 기본 권한 4개를 추가한다.

| 하고 싶은 일 | 필요한 scope |
|---|---|
| 연결 테스트, workspace 정보 읽기 | `team:read` |
| 사용자 목록 읽기, user ID 해석 | `users:read` |
| 공개 채널 목록 읽기 | `channels:read` |
| 특정 공개 채널 메시지 직접 읽기 | `channels:history` |

그 다음 `User Token Scopes`에 검색 권한을 추가한다.

| 하고 싶은 일 | 필요한 scope |
|---|---|
| Slack 메시지 검색 | `search:read` |

검색이 목적이면 `search:read`가 핵심이다. Slack 공식 문서 기준으로 `search.messages`는 User token의 `search:read` scope를 사용한다. Bot Token Scopes만 설정하면 검색은 되지 않는다.

이 스킬의 기본 권한은 `Bot Token Scopes: team:read, users:read, channels:read, channels:history`와 `User Token Scopes: search:read`이다. 검색 API 자체의 핵심은 `search:read`이지만, 기본 4개 Bot scope를 함께 넣어두면 사용자/채널 조회와 `channel-history` 명령까지 바로 쓸 수 있다.

### 6. 로컬 설정을 직접 만들거나 이름 저장하기

Slack 이름, `@핸들`, `U...` member ID는 민감정보가 아니므로 사용자가 채팅으로 알려줘도 된다. 내 Slack 식별자를 저장하려면 에이전트가 아래 명령을 실행해도 된다.

```bash
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" set-me --slack-user "your-slack-name"
```

직접 파일로 만들려면 `~/.config/slack-helper/oauth-app.json`에 저장한다.

```json
{
  "client_id": "123456789.123456789",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uri": "http://localhost:8765/callback",
  "scopes": ["team:read", "users:read", "channels:read", "channels:history"],
  "user_scopes": ["search:read"],
  "user_identity": {
    "identifier": "your-slack-name"
  }
}
```

### 7. Slack 승인 화면 열기

이 명령은 Slack 승인 URL을 만들고 브라우저를 연다.

```bash
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" oauth-start --open
```

Slack 승인 후 `http://localhost:8765/callback?code=...` 형태의 주소로 이동한다. 페이지가 열리지 않아도 괜찮다. 주소창에서 `code=` 뒤의 값만 복사한다.

### 8. code를 토큰으로 교환

```bash
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" oauth-finish --code CODE_FROM_REDIRECT --workspace default
```

성공하면 `~/.config/slack-helper/api-key.json`에 토큰이 저장된다.

### 9. 아무 데이터 하나 읽어서 확인

```bash
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" read-sample --workspace default
```

`read-sample`은 먼저 `team.info`를 읽고, 권한이 부족하면 `auth.test`로 연결 확인을 한다.

### 10. 내 Slack 계정 식별자 확인

연결 확인이 끝나면 검색 테스트를 바로 하지 말고 먼저 사용자의 Slack 식별자를 저장한다.

사용자에게 이렇게 묻는다.

```text
Slack에서 쓰는 표시 이름, @핸들, 또는 U로 시작하는 member ID를 알려주세요.
예: your-slack-name / @your-slack-name / U123...
```

사용자가 알려주면 에이전트가 내부적으로 `set-me`와 `resolve-me`를 실행한다. 저장한 이름/핸들을 `users.list`로 찾아서 `U...` member ID까지 `api-key.json`에 저장한다.

```bash
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" resolve-me --workspace default
```

사용자가 나중에 “your-slack-name이 나야”처럼 알려주면 에이전트가 아래처럼 저장한 뒤 다시 확인할 수 있다.

```bash
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" set-me --slack-user "your-slack-name" --workspace default
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" resolve-me --workspace default
```

### 11. 설정 완료 후 사용자에게 보여줄 예시

설정 완료 메시지에는 Python 명령을 보여주지 않는다. 사용자가 직접 스크립트를 실행하는 도구가 아니라, 에이전트가 내부적으로 실행하는 스킬이기 때문이다.

좋은 완료 안내 예:

```text
설정이 끝났어요. 이제 이런 식으로 물어보시면 제가 Slack에서 찾아서 정리해드릴게요.

- 내 최근 멘션 뭐 있어?
- 이번 주에 나를 멘션한 메시지 정리해줘
- 어제 장애 관련해서 나온 이야기 찾아줘
- 특정 채널에서 온보딩 관련 논의 요약해줘
- OO 프로젝트 관련 최근 결정사항 찾아줘
```

검색 결과는 승인한 사용자 계정이 Slack에서 볼 수 있는 범위에 영향을 받는다. 비공개 채널이나 DM은 그 사용자가 실제로 접근 가능한 내용만 검색된다.

나쁜 완료 안내:

- `배포` 같은 임의 키워드로 검색 테스트 결과를 보여주기
- 사용자가 요청하지 않은 대량 검색 결과를 먼저 요약하기
- `python3 ... slack_api.py search ...` 같은 실행 명령을 사용법으로 보여주기
- "바로 검색하고 싶은 키워드가 있나요?"처럼 키워드 검색만 유도하기

## 터미널에서 안내 보기

사용자가 무엇을 해야 할지 막히면 먼저 이 명령을 실행하게 한다.

```bash
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" setup-guide
```

## 에이전트 내부 명령 참고

아래 명령은 에이전트가 내부적으로 실행할 때만 참고한다. 설정 완료 안내나 일반 사용법 안내로 사용자에게 그대로 보여주지 않는다.

```bash
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" auth-test
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" team-info
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" users --limit 20
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" set-me --slack-user "your-slack-name" --workspace default
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" resolve-me --workspace default
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" channels --limit 20
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" channel-history --channel general --limit 10
python3 "/Users/hsryuuu/dev/personal/agent-toolkit/skills/slack-helper/scripts/slack_api.py" search "검색어" --count 10
```

채널은 Slack channel ID를 직접 넣거나, `~/.config/slack-helper/channel-info.json`에 별칭을 저장해서 쓴다.

```json
{
  "channels": {
    "general": "C0123456789"
  }
}
```

## 안전 규칙

- Slack token, client secret은 채팅에 붙여넣지 않는다. `Client Secret`은 `init-oauth` 대화형 프롬프트로만 입력받는다.
- Slack 표시 이름, `@핸들`, `U...` member ID는 민감정보가 아니므로 사용자가 채팅으로 알려줘도 된다. 에이전트는 이 값을 `set-me`로 로컬 config에 저장할 수 있다.
- `api-key.json`과 `oauth-app.json`은 repo 밖 `~/.config/slack-helper`에 둔다. 파일은 권한 `600`, 디렉토리는 `700`으로 저장한다.
- `search:read`로 하는 검색은 승인한 **사용자 계정 권한**으로 실행된다. 그 사용자가 볼 수 있는 DM과 비공개 채널까지 검색·열람될 수 있으므로, 이 helper로 검색하면 에이전트가 그 범위의 내용을 읽게 된다는 점을 사용자에게 알린다.
- Codex에서 브라우저 열기나 Slack 호출은 GUI/network 승인 요청이 필요할 수 있다.
- 이 helper는 읽기 우선이다. 메시지 쓰기(`chat.postMessage`)는 별도 명령을 추가한 뒤 사용한다.

## 검색 권한 메모

- Slack 메시지 검색 자체는 User Token Scopes의 `search:read`가 핵심이다.
- 이 스킬은 기본적으로 Bot Token Scopes에 `team:read`, `users:read`, `channels:read`, `channels:history`를 함께 넣는다.
- `team:read`는 연결 확인과 workspace 정보 읽기에 사용한다.
- `users:read`는 사용자 목록을 따로 읽거나 검색 결과의 user ID를 해석하고 싶을 때 사용한다.
- `channels:read`는 공개 채널 목록을 따로 읽을 때 사용한다.
- `channels:history`는 특정 공개 채널의 메시지 히스토리를 별도로 읽을 때 사용한다.
