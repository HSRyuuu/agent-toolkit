---
name: prompt-composer
description: >
  Use when the user wants to see which prompt snippets are stored in this plugin,
  read what a snippet does, or insert one or more stored snippets into a target
  prompt file such as CLAUDE.md, AGENTS.md, a SKILL.md, or a system prompt file.
  Triggers: "프롬프트 조각 목록 보여줘", "스니펫 뭐 있어", "이 스니펫 무슨 내용이야",
  "ASD-STE100 규칙 CLAUDE.md에 넣어줘", "이 조각 AGENTS.md에 추가해줘",
  "응답 스타일 프롬프트 설치해줘", "/prompt-composer". Do NOT use for writing a
  new prompt from scratch (use `prompt-master`) or for diagnosing an existing
  prompt (use `prompt-modernizer`).
---

# Prompt Composer

저장해 둔 프롬프트 조각을 보여 주고, 사용자가 고른 조각을 대상 파일의 구조에 맞게 넣는다.

조각 목록은 이 문서에 적지 않는다. 실행할 때마다 조각 폴더를 읽는다.

## 조각 폴더

- 위치: 이 스킬 디렉토리 기준 `../../snippets/*.md` (plugin 루트의 `snippets/`). plugin이 캐시에 설치되어도 상대 위치는 같다.
- 형식: frontmatter와 본문으로 나뉜다.
  - `name`: 조각 이름. 파일 이름과 같다.
  - `description`: 이 조각이 모델의 행동을 어떻게 바꾸는지 한 줄.
  - `placement`: 넣기 좋은 위치에 대한 힌트. 없을 수도 있다.
  - 본문: 대상 파일에 들어갈 텍스트.
- 폴더가 없거나 비었으면 그렇게 보고하고 멈춘다. 조각을 지어내지 않는다.

## 작업 흐름

### 1. 목록과 설명

- 사용자가 조각을 지목하지 않았으면 모든 조각의 frontmatter만 읽어 `name | description` 표로 보여 준다.
- 특정 조각을 물으면 그 조각의 본문을 읽고 무엇을 지시하는지 요약한다.
- 목록이나 설명만 원했으면 여기서 끝낸다.

### 2. 대상 파일 확정

- 사용자가 경로를 말했으면 그 파일이 대상이다.
- 말하지 않았으면 실제로 있는 후보만 보여 주고 고르게 한다.
  - 현재 프로젝트: `CLAUDE.md`, `.claude/CLAUDE.md`, `AGENTS.md`
  - 전역: `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`
- 대상 파일이 없으면 새로 만들지 묻는다.

### 3. 중복과 충돌 확인

대상 파일 전체를 읽고 조각 본문과 비교한다.

- 같은 규칙이 이미 있으면 넣지 않고, 어디에 있는지 알려 준다.
- 일부만 겹치면 빠진 규칙만 넣는다.
- 조각과 반대되는 지시가 있으면 넣기 전에 어느 쪽을 따를지 묻는다. 예: 대상은 "자세히 길게 설명한다", 조각은 "짧은 문장으로 쓴다".

### 4. 위치와 형태 결정

- 위치: `placement` 힌트와 대상 파일의 섹션 구조를 함께 본다. 주제가 맞는 섹션이 있으면 그 안에 넣는다. 없으면 새 섹션을 만들어 흐름에 맞는 자리에 둔다.
- 형태: 헤딩 레벨, 목록 기호, 언어, 문체를 대상 파일에 맞춘다.
- 의미는 바꾸지 않는다. 조각의 규칙을 빼거나, 약하게 만들거나, 새 규칙을 더하지 않는다.
- 대상 파일의 기존 문장은 3단계에서 사용자가 승인한 경우에만 고친다.

### 5. 적용과 보고

- 대상 파일과 조각을 사용자가 모두 지목했고 3단계에서 걸린 것이 없으면 바로 넣는다.
- 그 밖의 경우에는 넣을 위치와 문안을 먼저 보여 주고 확인을 받는다.
- 넣은 뒤에는 대상 경로, 들어간 섹션, 넣은 문안을 보고한다.
- 조각을 여러 개 골랐으면 조각마다 3~4단계를 반복하고, 보고는 한 번에 한다.
