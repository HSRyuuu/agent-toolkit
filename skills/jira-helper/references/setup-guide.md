# Jira Helper Setup Guide

Use this file when config is missing, credentials are invalid (401/403), the
Jira site is unknown, or issue search returns authentication errors.

## Tone

설정 안내를 받는 사용자는 비개발자일 수 있다.

- 모든 안내는 한글로 한다.
- 한 응답에는 한 단계만 안내한다.
- API token은 "비밀번호 대신 쓰는 개인용 열쇠"라고 풀어 설명한다.
- token 값은 채팅창에 붙여넣지 않게 한다. 터미널의 대화형 입력으로만 받는다.
- `<SKILL_DIR>`은 이 스킬이 실제 설치된 디렉터리의 절대 경로로 바꿔서 실행한다.

## Required Jira Access

- Jira Cloud site 주소: 예) `your-org.atlassian.net`
- Atlassian 계정 email
- Atlassian API token (계정 비밀번호가 아니다)
- 조회 권한: 해당 사이트에서 이슈를 볼 수 있는 계정이면 충분하다. 이 스킬은
  읽기 API만 호출한다.

## 진행 방식

아래 1~4단계를 순서대로 진행한다. 이미 완료된 단계는 검증 후 건너뛴다.

## 1단계: Jira site 확인

```text
1단계: Jira 주소 확인

브라우저에서 Jira에 접속했을 때 주소창이 어떻게 시작하는지 봐주세요.

- 예: https://your-org.atlassian.net/... 이면 site는 your-org.atlassian.net

어느 주소를 쓰는지 알려주세요.
```

## 2단계: API token 발급

```text
2단계: Atlassian API token 준비

API token은 비밀번호 대신 쓰는 개인용 열쇠예요. 아직 없다면 이렇게 만들어요.

1. 브라우저에서 https://id.atlassian.com/manage-profile/security/api-tokens 접속
2. [Create API token] 버튼 클릭
3. 이름을 입력하고 (예: jira-helper) 만들기
4. 표시된 token을 복사해두기 (창을 닫으면 다시 볼 수 없어요)

token 값은 이 채팅창에 붙여넣지 마세요. 다음 단계에서 터미널이 안전하게 물어볼
거예요. 준비되면 "완료"라고 알려주세요.
```

## 3단계: 로컬에 자격증명 등록

아래 명령을 절대 경로로 바꿔 안내하거나 직접 실행한다. site와 email은 인자로
넘길 수 있고, API token은 항상 대화형으로만 묻는다.

```bash
python3 "<SKILL_DIR>/scripts/jira_setup.py" init-keys --site your-org.atlassian.net --email yourname@example.com
```

명령은 API token을 화면에 표시되지 않는 입력으로 묻는다. 입력값은
`~/.config/jira-helper/config.json`에 저장되고 파일 권한은 `600`으로 맞춰진다.

**에이전트 확인:** 사용자가 완료했다고 하면 아래를 실행한다.

```bash
python3 "<SKILL_DIR>/scripts/jira_setup.py" profiles
```

profile이 보이면 4단계로 간다. 없으면 어느 지점에서 막혔는지 묻고 다시 안내한다.

## 4단계: 연결과 조회 확인

먼저 자격증명이 유효한지 확인한다. 성공하면 내 계정 이름과 accountId가
profile에 캐시된다.

```bash
python3 "<SKILL_DIR>/scripts/jira_setup.py" auth-test
```

성공하면 이슈 검색 권한을 확인한다.

```bash
python3 "<SKILL_DIR>/scripts/jira_setup.py" search-test
```

401/403이 나오면 email 또는 token이 잘못된 것이다. 2~3단계를 다시 안내한다.

성공하면 이렇게 마무리한다.

```text
Jira 조회 설정이 끝났어요. 이제 이런 식으로 물어보시면 됩니다.

- 내가 맡은 진행 중인 티켓 보여줘
- 이번 주에 내가 작업한 티켓 정리해줘
- 기한이 일주일 안 남은 내 티켓 찾아줘
- 결제 오류 관련 티켓 찾아줘
- ABC-123 내용이랑 최근 코멘트 보여줘
- 이 프로젝트 별칭 MEMORY.md에 저장해줘
```

## Avoid

- API token을 채팅으로 받기.
- config 내용을 그대로 출력하기.
- 테스트 목적으로 넓은 범위의 무제한 검색을 실행하기.
- 이슈 본문을 `MEMORY.md`에 저장하기.
