# Datadog Log Helper Setup Guide

Use this file when config is missing, keys are invalid, Datadog site is unknown,
or log search returns authentication/permission errors.

## Tone

설정 안내를 받는 사용자는 비개발자일 수 있다.

- 모든 안내는 한글로 한다.
- 한 응답에는 한 단계만 안내한다.
- API key는 "조직을 식별하는 열쇠", application key는 "내 계정 또는 서비스 계정 권한으로 API를 쓰게 해주는 열쇠"라고 풀어 설명한다.
- 키 값은 채팅창에 붙여넣지 않게 한다. 터미널의 대화형 입력으로만 받는다.
- `<SKILL_DIR>`은 이 스킬이 실제 설치된 디렉터리의 절대 경로로 바꿔서 실행한다.

## Required Datadog Access

- Datadog site: 예) `datadoghq.com`, `us3.datadoghq.com`, `us5.datadoghq.com`, `datadoghq.eu`, `ap1.datadoghq.com`, `ap2.datadoghq.com`, `ddog-gov.com`
- API key
- Application key
- 로그 조회 권한. scoped application key를 쓰는 경우 최소 로그 읽기 권한이 필요하다.

## 진행 방식

아래 1~4단계를 순서대로 진행한다. 이미 완료된 단계는 검증 후 건너뛴다.

## 1단계: Datadog site 확인

사용자가 접속하는 Datadog URL을 기준으로 site를 고른다.

```text
1단계: Datadog site 확인

브라우저에서 Datadog에 접속했을 때 주소가 어떻게 시작하는지 봐주세요.

- https://app.datadoghq.com 이면 site는 datadoghq.com
- https://us3.datadoghq.com 이면 site는 us3.datadoghq.com
- https://us5.datadoghq.com 이면 site는 us5.datadoghq.com
- https://app.datadoghq.eu 이면 site는 datadoghq.eu
- https://ap1.datadoghq.com 이면 site는 ap1.datadoghq.com
- https://ap2.datadoghq.com 이면 site는 ap2.datadoghq.com

어느 주소를 쓰는지 확인되면 알려주세요.
```

## 2단계: API key와 application key 준비

Datadog의 Organization Settings 또는 Personal Settings에서 API key와
application key를 준비하게 안내한다. 가능하면 개인 키보다 서비스 계정의 scoped
application key를 권장한다.

```text
2단계: Datadog API key / application key 준비

Datadog에서 API key와 application key를 준비해주세요.

- API key: 우리 Datadog 조직을 식별하는 열쇠예요.
- Application key: 내 계정 또는 서비스 계정 권한으로 API를 쓰게 해주는 열쇠예요.

권한은 로그 조회가 가능해야 합니다. scoped application key를 만들 수 있다면 로그 읽기 권한만 주는 쪽이 좋아요.

키 값은 이 채팅창에 붙여넣지 마세요. 다음 단계에서 터미널이 안전하게 물어볼 거예요.
준비되면 "완료"라고 알려주세요.
```

## 3단계: 로컬에 키 등록

아래 명령을 절대 경로로 바꿔 안내하거나 직접 실행한다.

```bash
python3 "<SKILL_DIR>/scripts/datadog_setup.py" init-keys --profile default --site datadoghq.com
```

명령은 API key와 application key를 대화형으로 묻는다. 입력값은
`~/.config/datadog-log-helper/config.json`에 저장되고 파일 권한은 `600`으로
맞춰진다.

**에이전트 확인:** 사용자가 완료했다고 하면 아래를 실행한다.

```bash
python3 "<SKILL_DIR>/scripts/datadog_setup.py" profiles
```

profile이 보이면 4단계로 간다. 없으면 어느 지점에서 막혔는지 묻고 다시 안내한다.

## 4단계: 연결과 로그 조회 확인

먼저 API key가 유효한지 확인한다.

```bash
python3 "<SKILL_DIR>/scripts/datadog_setup.py" auth-test --profile default
```

성공하면 로그 조회 권한까지 확인한다.

```bash
python3 "<SKILL_DIR>/scripts/datadog_setup.py" logs-test --profile default
```

성공하면 이렇게 마무리한다.

```text
Datadog 로그 조회 설정이 끝났어요. 이제 이런 식으로 물어보시면 됩니다.

- payments-api 최근 에러 로그 봐줘
- prod에서 30분 동안 500 에러가 늘었는지 봐줘
- 배포 이후 에러 타임라인 만들어줘
- 이 서비스 로그 접근 방법 MEMORY.md에 저장해줘
```

## Avoid

- API key나 application key를 채팅으로 받기.
- config 내용을 그대로 출력하기.
- 테스트 목적으로 긴 기간의 `*` 검색을 실행하기.
- 로그 원문을 `MEMORY.md`에 저장하기.
