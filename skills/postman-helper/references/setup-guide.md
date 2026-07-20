# Postman Helper Setup Guide

Use this file when `config.json` is missing, the API key is invalid, or a cloud
command returns 401/403. **로컬 파일 소스(`--file`)만 쓸 거라면 설정이 전혀 필요
없다** — 이 가이드는 클라우드 API(`--collection`, `workspaces`, `collections`)를
쓸 때만 필요하다.

## Tone

- 모든 안내는 한글로 한다.
- 한 응답에는 한 단계만 안내한다.
- API key는 "내 Postman 계정 권한으로 API를 쓰게 해주는 열쇠"라고 풀어 설명한다.
- 키 값은 채팅창에 붙여넣지 않게 한다. 터미널 대화형 입력으로만 받는다.
- `<SKILL_DIR>`은 이 스킬이 설치된 절대 경로로 바꿔 실행한다.

## 1단계: Postman API key 발급

```text
1단계: Postman API key 준비

1) 브라우저에서 https://go.postman.co/settings/me/api-keys 에 접속하세요.
   (Postman 앱에서는 오른쪽 위 프로필 > Settings > API keys)
2) "Generate API Key" 버튼을 누르세요.
3) 이름을 아무거나 정하고(예: postman-helper) 생성하세요.
4) 생성된 키가 화면에 한 번만 보입니다. 복사해 두세요.
   (채팅에 붙여넣지 마세요. 다음 단계에서 터미널에 직접 입력합니다.)
```

## 2단계: 키 등록

터미널에서 아래를 실행하면 키를 물어본다. 입력값은 화면에 표시되지 않는다.

```bash
python3 <SKILL_DIR>/scripts/postman_setup.py init-key
```

- 여러 계정을 쓰면 `--profile <name>`으로 프로필을 나눈다.
- 저장 위치: `~/.config/postman-helper/config.json` (파일 `600`, 디렉토리 `700`).

## 3단계: 검증

```bash
python3 <SKILL_DIR>/scripts/postman_setup.py auth-test
```

`Postman API key is valid. ... user=<username>`가 나오면 성공이다. 401이 나오면
키를 잘못 복사한 것이니 1단계부터 다시 한다.

## 확인 명령

```bash
python3 <SKILL_DIR>/scripts/postman_setup.py profiles   # 등록된 프로필 목록(키는 마스킹)
```
