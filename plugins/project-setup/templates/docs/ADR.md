# {PROJECT_NAME} Architecture Decision Records

> 최종 업데이트: YYYY-MM-DD
>
> **작성 원칙**
> - 한 결정 = 한 섹션. 새 결정은 **목록 위쪽(최신이 위)**에 추가하고, 인덱스 표를 함께 갱신한다.
> - 한 번 채택된 결정은 **삭제하지 않는다.** 폐기되면 상태를 `Superseded` 또는 `Deprecated`로 바꾸고, 후속 ADR 번호를 명시한다 — 결정의 흐름이 추적 가능해야 한다.
> - "왜 이렇게 안 했는가"가 더 중요하다. **Alternatives Considered** 섹션을 비우지 않는다.
> - 결정의 범위는 **되돌리기 어려운 것**으로 한정한다. (DB 엔진 선택 ✓ / 버튼 색상 ✗)

---

## 인덱스

| # | 결정 | 상태 | 날짜 | 태그 |
|---|------|------|------|------|
| 0001 | <한 줄 제목> | <Proposed / Accepted / Superseded by ADR-NNNN / Deprecated> | YYYY-MM-DD | `<tag>` |

> 상태 표기:
> - **Proposed** — 검토 중, 아직 미적용
> - **Accepted** — 채택, 코드/인프라에 반영됨
> - **Superseded by ADR-NNNN** — 후속 결정으로 대체됨 (원문은 그대로 둠)
> - **Deprecated** — 더 이상 적용되지 않음, 후속 결정도 없음

---

## ADR-0001: <한 줄 제목>

- **Date**: YYYY-MM-DD
- **Status**: <Proposed / Accepted / Superseded by ADR-NNNN / Deprecated>
- **Decision Makers**: <이름 / 역할>
- **Tags**: `<infra>`, `<frontend>`, `<db>` 등

### Context

> 어떤 문제·제약 때문에 이 결정이 필요했는가. 기술적 배경, 비즈니스 제약, 시간/비용 제약 등을 적는다.
> 이 섹션을 읽고 미래의 본인이 "왜 이걸 고민했는지" 다시 떠올릴 수 있어야 한다.

### Decision

> 무엇을 결정했는가. **명령형 한 문장**으로 시작하고, 필요하면 그 아래에 세부를 적는다.
> 예: "프론트엔드는 Next.js 15 App Router로 간다."

### Alternatives Considered

> 검토했지만 선택하지 않은 대안. 각 대안마다 **거절 사유**를 한 줄로.

- **<대안 A>** — <왜 거절했는가>
- **<대안 B>** — <왜 거절했는가>

### Consequences

> 이 결정이 가져올 결과. **좋은 면과 나쁜 면을 모두** 적는다.

- **Positive**: <얻는 것>
- **Negative**: <감수해야 할 것>
- **Follow-ups**: <후속으로 해야 할 작업, 추가로 결정해야 할 것>

### References

- <PR / 이슈 / 문서 링크>

---

## ADR-0000: 템플릿 (실제 ADR 작성 시 위 0001 형식을 복사하세요)

> 첫 결정을 추가하면 이 섹션은 삭제한다. 인덱스 표의 0001 행도 실제 결정으로 바꾼다.
