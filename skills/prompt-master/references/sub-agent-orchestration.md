# 서브에이전트 오케스트레이션 패턴

멀티에이전트 시스템에서 에이전트 간 역할 분리, 위임, 라우팅을 설계할 때 적용하는 패턴 모음이다.

---

## 1. 역할 경계 테이블

각 에이전트의 책임 소재를 마크다운 테이블로 명확히 구분하고, 특정 상황에서 어떤 에이전트에게 위임해야 하는지를 명시한다. 이를 통해 에이전트 간 책임이 겹치거나 무한 루프에 빠지는 것을 방지한다.

```xml
<Role_Boundaries>
## Hand Off To

| Situation | Hand Off To | Reason |
|-----------|-------------|--------|
| 요구사항 격차 감지 | `analyst` (Metis) | 격차 분석은 Metis의 역할 |
| 코드베이스 컨텍스트 필요 | `explore` | 탐색을 통한 코드베이스 사실 확인 |
| 코드 분석 필요 | `architect` (Oracle) | 코드 분석은 Oracle의 역할 |
| 계획 리뷰 필요 | `critic` | 계획 검토는 Critic의 역할 |
</Role_Boundaries>
```

**핵심:** 역할 경계를 자연어 설명이 아닌 테이블로 표현하면, LLM이 현재 상황에 해당하는 행을 즉시 찾아 위임할 수 있다. "else" 행이 없으므로 반드시 정의된 역할 중 하나로 라우팅된다.

---

## 2. 자연어 상태 머신 (Phase 분리)

작업 워크플로우를 명확한 Phase로 분리하고 전이 조건을 명시한다. 이를 통해 LLM이 정보 수집도 없이 성급하게 결과를 생성하는 것을 방지한다.

```xml
<Operational_Phases>
## Phase 1: Context Gathering (MANDATORY)
분석 전에 반드시 컨텍스트를 수집한다:
1. Codebase Structure: Glob 사용
2. Related Code: Grep/Read 사용
3. Dependencies: 프로젝트 매니페스트 확인
4. Test Coverage: 기존 테스트 탐색

## Phase 2: Deep Analysis
컨텍스트 수집 완료 후 체계적 분석 수행

## Phase 3: Recommendation Synthesis
구조화된 출력 생성:
1. Summary: 2-3문장 개요
2. Diagnosis: 무엇이 왜 발생하는지
3. Root Cause: 근본적인 원인
4. Recommendations: 우선순위별 실행 단계
5. Trade-offs: 각 접근 방식의 트레이드오프
</Operational_Phases>
```

**효과:**
- **성급한 결론 방지**: Phase 1에서 정보 수집을 강제하여, 전체 문맥 없이 답변 생성을 시작하는 실수를 차단
- **순차적 사고 유도**: 정보 수집 → 깊은 분석 → 해결책 구조화라는 논리적 파이프라인을 따르도록 강제
- **모드 전환 통제**: "분석이 끝나기 전까지는 코드를 작성하지 마라"와 같은 단계별 전이 조건 설정

---

## 3. 템플릿 상속 (`<Inherits_From>`)

공통 규칙을 중복 작성하지 않고 base 프롬프트에서 상속받아 사용한다. 에이전트가 여러 개로 늘어날 때 핵심 규칙 누락을 방지한다.

```xml
<Inherits_From>
Base: architect.md - Strategic Architecture & Debugging Advisor
</Inherits_From>
```

프로그래밍의 상속 원칙이 프롬프트 엔지니어링에서도 동일하게 적용된다. 공통 행동 규칙, 검증 프로토콜, 출력 형식 등을 base 문서에 정의하고, 각 에이전트 프롬프트에서 이를 참조하도록 한다.

---

## 4. 복잡도 기반 3-Tier 모델 라우팅

작업 복잡도에 따라 적절한 모델 Tier로 라우팅하여 비용 효율성과 품질의 균형을 확보한다.

| Domain | LOW (Haiku) | MEDIUM (Sonnet) | HIGH (Opus) |
|--------|-------------|-----------------|-------------|
| Analysis | `architect-low` | `architect-medium` | `architect` |
| Execution | `executor-low` | `executor` | `executor-high` |
| Search | `explore` | `explore-medium` | `explore-high` |

**일반적 기준:**
- **Haiku (LOW)**: 간단한 읽기 작업, 빠른 조회, 좁은 범위의 검색
- **Sonnet (MEDIUM)**: 계획에 따른 작업 실행, 코드 구현, 디버깅
- **Opus (HIGH)**: 요구사항 분석, 복잡한 계획 생성, 아키텍처 설계, 심층 검증

---

## 5. 에이전트 위임 구조 (컨텍스트 유실 방지)

에이전트에게 작업을 위임할 때 완벽한 컨텍스트를 전달하여 재작업을 최소화한다. 상황마다 정해진 정보 템플릿을 사용한다.

### 탐색/리서치 위임 템플릿

```markdown
- **TASK**: 탐색해야 할 대상
- **EXPECTED OUTCOME**: 오케스트레이터가 기대하는 반환값
- **CONTEXT**: 배경 정보
- **MUST DO**: 필수 수행 사항
- **MUST NOT DO**: 제약 조건
- **REQUIRED SKILLS**: 필요한 스킬
- **REQUIRED TOOLS**: 사용할 도구
```

### 실행 위임 템플릿

```markdown
- **TASK**: 구현해야 할 기능/수정
- **ACCEPTANCE CRITERIA**: 완료 기준 (구체적, 검증 가능한 조건)
- **CONTEXT**: 관련 코드 위치, 기존 패턴, 의존성
- **CONSTRAINTS**: 성능/보안/호환성 제약
- **VERIFICATION**: 완료 확인 방법 (테스트 명령어 등)
```

이렇게 7단계 규격으로 위임하면, 작업을 넘겨받은 에이전트가 앞선 맥락을 완벽히 이해하고 바로 작업에 착수할 수 있어 컨텍스트 유실로 인한 재작업을 획기적으로 줄인다.

---

## 적용 판단 기준

| 상황 | 적용할 패턴 |
|------|-----------|
| 에이전트 간 책임이 겹침 | 역할 경계 테이블 |
| 에이전트가 단계를 건너뜀 | Phase 분리 (자연어 상태 머신) |
| 공통 규칙이 여러 에이전트에 필요 | 템플릿 상속 |
| 비용 최적화가 필요 | 3-Tier 모델 라우팅 |
| 위임 후 재작업이 발생 | 위임 템플릿으로 컨텍스트 전달 |
