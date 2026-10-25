# context-map — SOURCE_MAP.md / CODEBASE_CONTEXT.md

에이전트가 저장소를 넓게 뒤지기 전에 맞는 파일을 찾도록 소스 기반 내비게이션 문서를 만든다.

## 세 층을 분리한다

| 층 | 용도 | 신뢰도 |
| --- | --- | --- |
| `docs/SOURCE_MAP.md` | 중요한 코드가 어디 있는지 고른 라우팅 맵 | 높음. 최신으로 유지해야 함 |
| `docs/CODEBASE_CONTEXT.md` | 에이전트 읽기 정책과 생성된 컨텍스트 목록 | 중간 |
| `.codesight/` | 선택. Codesight가 만든 구조 힌트 | 탐색 보조일 뿐 |

생성된 맵은 어디를 볼지 알려 줄 뿐이다. 구현 전에 소스를 읽는 것을 대신하지 않는다.

## 절차

1. 저장소 루트와 기존 문서를 확인한다.
2. 생성기를 돌린다.

   ```bash
   python3 <skill>/scripts/build_context_map.py "$TARGET"
   ```

   Node/npx가 있고 담당자가 `.codesight/` 출력을 원할 때만 `--run-codesight`를 붙인다. Codesight 설치나 MCP·watch·hook 연동을 원하면 먼저 `codesight-install.md`를 읽는다.
3. 생성된 `docs/SOURCE_MAP.md`, `docs/CODEBASE_CONTEXT.md`를 검토한다. 사람만 아는 맥락은 생성 구역이 아니라 `## Manual Notes`에 적는다.
4. 경로 참조를 검증한다.

   ```bash
   python3 <skill>/scripts/validate_context_map.py "$TARGET"
   ```

5. 진입점 매핑 표에 두 문서를 넣고, 넓은 탐색 전에 `SOURCE_MAP.md`를 먼저 읽으라고 적는다.

`templates/docs/SOURCE_MAP.md`는 생성기를 쓸 수 없는 환경에서 손으로 작성할 때의 형식 참고용이다.

## 무엇을 넣나

`SOURCE_MAP.md`는 선별한다. 에이전트가 다시 찾느라 시간을 쓸 파일만 넣는다.

- 프론트엔드 라우트, 레이아웃, 공용 컴포넌트, API 클라이언트, 라우트 상수
- 백엔드 controller, service, repository, entity/model, DTO
- 스키마와 마이그레이션 파일
- 인증, 미들웨어, 예외, 설정, 환경, 배포 진입점
- 테스트와 영향이 큰 공용 파일

모든 파일을 나열하지 않는다. 디렉토리 이름으로 충분하면 파일 여러 행 대신 디렉토리 한 행을 쓴다.

## 함께 읽을 것

- `output-structure.md` — 목표 파일 배치와 소유 경계
- `source-map-rules.md` — `SOURCE_MAP.md` 선별·갱신 규칙
- `codesight-policy.md` — Codesight 출력을 안전하게 쓰는 법
- `codesight-install.md` — 선택. Codesight 설치, 갱신, MCP, CI
