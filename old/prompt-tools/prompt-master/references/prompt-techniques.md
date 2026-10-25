# Prompt Engineering Techniques - 18가지 기법 레퍼런스

프롬프트 전략을 선택할 때 참조하는 학술 기반 기법 모음이다. SKILL.md의 "기법 선택 가이드"에서 특정 기법의 상세 설명이 필요할 때 이 문서를 읽는다.

---

## 목차

1. [Zero-Shot Prompting](#1-zero-shot-prompting)
2. [Few-Shot Prompting](#2-few-shot-prompting)
3. [Chain-of-Thought (CoT)](#3-chain-of-thought-cot-prompting)
4. [Self-Consistency](#4-self-consistency)
5. [Generated Knowledge Prompting](#5-generated-knowledge-prompting)
6. [Prompt Chaining](#6-prompt-chaining)
7. [Tree of Thoughts (ToT)](#7-tree-of-thoughts-tot)
8. [Retrieval Augmented Generation (RAG)](#8-retrieval-augmented-generation-rag)
9. [Automatic Reasoning and Tool-use (ART)](#9-automatic-reasoning-and-tool-use-art)
10. [Automatic Prompt Engineer (APE)](#10-automatic-prompt-engineer-ape)
11. [Active-Prompt](#11-active-prompt)
12. [Directional Stimulus Prompting](#12-directional-stimulus-prompting)
13. [Program-Aided Language Models (PAL)](#13-program-aided-language-models-pal)
14. [ReAct](#14-react)
15. [Reflexion](#15-reflexion)
16. [Multimodal CoT](#16-multimodal-cot)
17. [Graph Prompting](#17-graph-prompting)
18. [Meta Prompting](#18-meta-prompting)

---

## 1. Zero-Shot Prompting

모델에 예시를 전혀 제공하지 않고 바로 작업을 수행하도록 하는 기법. Instruction Tuning과 RLHF로 학습된 최신 LLM은 예시 없이도 다양한 작업을 처리할 수 있다. 제로샷이 잘 동작하지 않을 때는 Few-Shot으로 전환한다.

```
Prompt: 텍스트를 중립, 부정 또는 긍정으로 분류합니다.
텍스트: 휴가는 괜찮을 것 같아요.
감정:

Output: 중립
```

**적합한 상황**: 단순 분류, 번역, 요약 등 명확한 작업 / 모델이 충분히 학습한 일반적 태스크

---

## 2. Few-Shot Prompting

프롬프트 내에 소수의 데모/예시를 제공하여 문맥 내 학습(in-context learning)을 유도하는 기법. 레이블 공간, 입력 텍스트 분포, 사용 형식이 성능에 중요한 역할을 한다.

```
Prompt: "whatpu"는 탄자니아에 서식하는 작은 털복숭이 동물입니다.
whatpu를 사용하는 문장의 예: 우리는 아프리카를 여행하고 있었는데 아주 귀여운 whatpu를 보았습니다.
"farduddle"을 한다는 것은 정말 빠르게 위아래로 점프한다는 뜻입니다.
farduddle을 사용하는 문장의 예:

Output: 게임에서 이겼을 때 우리 모두는 farduddle를 시작했습니다.
```

**적합한 상황**: 모델이 학습하지 않은 커스텀 포맷/분류 체계 / 출력 일관성이 중요한 경우
**예시 구성 원칙**: 최소 2개~최대 5개, Good/Bad 쌍, 경계 사례 포함, 쉬운→어려운 순서 배치

---

## 3. Chain-of-Thought (CoT) Prompting

중간 추론 단계를 포함한 예시를 제공하여 복잡한 추론을 유도하는 기법. Wei et al.(2022) 제안. Zero-shot CoT는 "단계별로 생각해 보자"라는 문구만 추가하여 별도 예시 없이도 추론을 유도한다.

```
Prompt: 나는 시장에서 사과 10개를 샀어. 2개를 이웃에게, 2개를 수리공에게 주었어.
그리고 5개를 더 사서 1개를 먹었어. 사과가 몇 개 남았니? 단계별로 생각해 보자.

Output: 10개로 시작 → 4개를 줌 → 6개 남음 → 5개 추가 → 11개 → 1개 먹음 → 10개
```

**적합한 상황**: 산술, 상식, 상징적 추론이 필요한 복잡한 문제
**변형**: Zero-shot CoT ("단계별로 생각하자"), Auto-CoT (자동화)

---

## 4. Self-Consistency

Few-shot CoT를 통해 여러 다양한 추론 경로를 샘플링한 뒤, 다수결로 최종 답을 선택하는 기법. Wang et al.(2022) 제안. 탐욕 디코딩을 대체하여 CoT의 성능을 향상시킨다.

```
Q: 내가 6살이었을 때 여동생은 내 나이의 절반이었어. 지금 나는 70살이면 여동생은 몇 살?

Output 1: 6살 때 여동생은 3살 → 나이 차이 3살 → 70-3 = 67살 (정답)
Output 2: 70-3 = 67살 (정답)
Output 3: 70/2 = 35살 (오답)

→ 다수결: 67살 (정답)
```

**적합한 상황**: 높은 정확도가 필요한 산술/상식 추론 / API에서 temperature를 올려 다양한 경로 샘플링 가능할 때

---

## 5. Generated Knowledge Prompting

예측 전에 모델에게 먼저 관련 지식을 생성하게 한 뒤, 그 지식을 통합하여 더 정확한 답변을 이끌어내는 기법. Liu et al.(2022) 제안.

```
1단계(지식 생성): "골프의 목적" → 골프는 최소 스트로크로 홀을 플레이하는 것이 목표

2단계(지식 통합):
Prompt: 골프의 목적 중 하나는 더 높은 점수를 얻는 것이다. 예/아니오?
Knowledge: 골프의 목적은 최소의 스트로크로 플레이하는 것...

Output: 아니요, 가장 적은 스트로크가 목표입니다.
```

**적합한 상황**: 상식 추론, 사실 검증 / 모델의 내부 지식을 명시적으로 활성화해야 할 때

---

## 6. Prompt Chaining

복잡한 작업을 하위 작업으로 분할하고, 각 단계의 출력을 다음 프롬프트의 입력으로 사용하는 기법. 투명성, 제어 가능성, 안정성을 높이며 디버깅이 용이하다.

```
Prompt 1: 문서에서 질문과 관련된 인용문을 추출하세요 → <quotes>추출된 인용문들</quotes>
Prompt 2: 추출된 인용문과 원본 문서를 바탕으로 질문에 답변하세요

→ Output: 정리된 최종 답변
```

**적합한 상황**: 문서 QA, 멀티스텝 분석, 대화형 어시스턴트 구축 / 단일 프롬프트로 처리하기 복잡한 작업

---

## 7. Tree of Thoughts (ToT)

CoT를 일반화한 프레임워크로, 여러 중간 "생각"을 트리 구조로 탐색한다. Yao et al.(2023) 제안. BFS, DFS 등과 결합하여 선제적 탐색과 백트래킹이 가능하다.

```
세 명의 다른 전문가들이 이 질문에 답하고 있다고 상상해보자.
모든 전문가들은 자신의 생각의 한 단계를 적어내고 그룹과 공유할 거야.
만약 어떤 전문가가 자신이 틀렸다는 것을 깨달으면 그들은 떠나.
그렇다면 질문은...
```

**적합한 상황**: 전략적 예측, 복잡한 수학 추론, 창의적 문제 해결 / 여러 경로를 동시에 탐색해야 할 때

---

## 8. Retrieval Augmented Generation (RAG)

외부 지식 소스에서 관련 문서를 검색(retrieve)한 뒤, 프롬프트와 결합하여 답변을 생성하는 기법. Meta AI 도입. 환각 완화, 사실적 일관성 향상, 재학습 없이 최신 정보 적용 가능.

```
사용자 질문: "양자 컴퓨팅의 최신 발전은?"

→ 검색 단계: Wikipedia 등에서 관련 문서 검색
→ 생성 단계: 검색된 문서 + 질문을 결합하여 LLM이 최종 답변 생성
```

**적합한 상황**: 최신 정보 필요, 도메인 특화 질의응답, 사실 기반 응답이 중요한 경우

---

## 9. Automatic Reasoning and Tool-use (ART)

작업 라이브러리에서 추론/도구 사용 시연을 자동 선택하고, 외부 도구 필요 시 생성을 일시 중단하여 도구 출력을 통합하는 프레임워크. Paranjape et al.(2023) 제안. 제로샷 방식.

```
새 작업 입력 → 작업 라이브러리에서 유사 시연 자동 선택
→ LLM이 추론 단계 생성 → 외부 도구 호출 필요 시 일시 중단
→ 도구 출력 통합 → 최종 답변 생성
```

**적합한 상황**: 도구 사용이 필요한 복합 작업 / 확장 가능한 에이전트 시스템 구축

---

## 10. Automatic Prompt Engineer (APE)

LLM을 사용하여 프롬프트를 자동 생성하고 최적의 프롬프트를 선택하는 프레임워크. Zhou et al.(2022) 제안. 명령 생성을 블랙박스 최적화 문제로 접근한다.

```
사람이 설계: "단계별로 생각하자"
APE가 발견: "올바른 답을 가지고 있는지 확인하기 위해 단계적으로 이 문제를 해결합시다."

→ APE가 찾은 프롬프트가 MultiArith, GSM8K 벤치마크에서 더 높은 성능 달성
```

**적합한 상황**: 프롬프트 최적화가 필요한 대규모 시스템 / 사람이 설계한 프롬프트 개선

---

## 11. Active-Prompt

LLM에 질문을 던져 불확실성이 가장 높은 질문을 식별한 뒤, 사람이 CoT 주석을 달아 예시로 활용하는 기법. Diao et al.(2023) 제안.

```
1단계: LLM에 학습 질문들을 던져 k개 답변 생성
2단계: 답변 간 불일치(불확실성)가 가장 큰 질문 선별
3단계: 사람이 해당 질문에 CoT 주석 작성
4단계: 주석이 달린 새 예시로 각 질문 추론 → 성능 향상
```

**적합한 상황**: 고정 예시가 아닌 작업별 최적 예시가 필요할 때 / 대규모 Few-Shot 최적화

---

## 12. Directional Stimulus Prompting

작은 정책 LM이 힌트/자극(stimulus)을 생성하고, 이를 블랙박스 LLM에 전달하여 원하는 출력 방향으로 유도하는 기법. Li et al.(2023) 제안. RL로 정책 LM 최적화.

```
표준 프롬프팅:    입력 → LLM → 출력
방향 자극 프롬프팅: 입력 → 정책 LM이 힌트 생성 → (입력 + 힌트) → LLM → 개선된 출력
```

**적합한 상황**: 큰 LLM을 직접 조정하지 않고 출력을 제어하고 싶을 때 / 요약 품질 향상

---

## 13. Program-Aided Language Models (PAL)

LLM이 자연어 문제를 읽고 중간 추론 단계로 프로그램 코드를 생성하며, 런타임에서 실행하여 답을 얻는 기법. Gao et al.(2022) 제안.

```
Q: 오늘은 2023년 2월 27일이야. 나는 정확히 25년 전에 태어났어.
   생일을 MM/DD/YYYY로 알려줘.

LLM 생성 코드:
  today = datetime(2023, 2, 27)
  born = today - relativedelta(years=25)
  born.strftime('%m/%d/%Y')

실행 결과: 02/27/1998
```

**적합한 상황**: 수학적 계산, 날짜 연산, 논리적 추론 / CoT의 계산 오류를 코드 실행으로 해결

---

## 14. ReAct

추론(Reasoning)과 행동(Acting)을 인터리브 방식으로 결합하는 프레임워크. Yao et al.(2022) 제안. 외부 도구와 상호작용하며 정보를 수집하여 환각을 줄인다.

```
질문: 콜로라도 조산 운동의 동쪽 구역이 확장되는 지역의 표고 범위는?

생각 1: 콜로라도 조산 운동을 검색해야 해
→ 행동 1: 검색[콜로라도 조산 운동]
→ 관찰 1: 산이 형성되는 과정...

생각 2: 동부 섹터를 찾아야 해
→ ... → 최종 답변: 1,800~7,000피트
```

**적합한 상황**: 사실 확인이 필요한 질의응답 / 외부 도구 연동 에이전트 설계

---

## 15. Reflexion

언어적 피드백을 통해 에이전트를 강화하는 프레임워크. Shinn et al.(2023) 제안. Actor, Evaluator, Self-Reflection 세 모델로 구성.

```
시도 1: 작업 수행 → 실패 → 평가: "목표 물체를 잘못된 위치에서 찾았음"
자기성찰: "다음에는 먼저 올바른 방을 확인해야 함"

시도 2: 성찰을 컨텍스트로 포함 → 올바른 방 탐색 → 작업 성공
```

**적합한 상황**: 반복적 개선이 필요한 에이전트 태스크 / 실패에서 학습하는 자율 시스템

---

## 16. Multimodal CoT

텍스트와 이미지를 결합한 2단계 CoT 프레임워크. Zhang et al.(2023) 제안. 1단계에서 근거(rationale) 생성, 2단계에서 답변 추론.

```
입력: [과학 문제 텍스트] + [관련 다이어그램 이미지]

1단계(근거 생성): 이미지와 텍스트를 분석하여 "그림에서 물체 A가 B보다 높이 있으므로..."
2단계(답변 추론): 생성된 근거를 활용 → 최종 정답 도출
```

**적합한 상황**: 텍스트+이미지 입력이 있는 복합 문제 / 과학, 수학 등 다이어그램 기반 추론

---

## 17. Graph Prompting

그래프 구조 데이터에 특화된 프롬프팅 프레임워크. Liu et al.(2023) GraphPrompt 소개. 사전학습과 다운스트림 작업 간의 간극을 줄인다.

```
그래프 데이터 입력 (노드, 엣지 구조)
→ GraphPrompt 프레임워크가 작업 특화 프롬프트 템플릿 적용
→ 노드 분류 또는 그래프 분류 등 다운스트림 작업 수행 → 성능 향상
```

**적합한 상황**: 그래프 구조 데이터 처리, 노드/그래프 분류

---

## 18. Meta Prompting

구조와 형식(syntax)에 초점을 맞추는 고급 기법. Zhang et al.(2024) 제안. 추상화된 예시를 프레임워크로 활용하여 문제의 패턴을 안내한다. Few-shot 대비 토큰 효율적.

```
Few-shot:     구체적 예시 (1+1=2, 2+3=5, ...)를 제공
Meta Prompt:  구조만 제공 → "Input: [수학식] → Step: [연산 과정] → Output: [결과]"

→ 모델이 구조 패턴을 학습하여 새로운 문제에 적용
```

**적합한 상황**: 토큰 절약이 필요한 경우 / 복잡한 추론, 수학, 코딩 / 구조 패턴이 내용보다 중요한 작업
