# docs — 사람이 관리하는 프로젝트 문서

## 대상

| 문서 | 기본 위치 | 권할 때 |
| --- | --- | --- |
| `PROJECT_OVERVIEW.md` | `docs/PROJECT_OVERVIEW.md` | 거의 항상. 정체성, 스택, 마일스톤, 링크 |
| `DB_SCHEMA.md` | `docs/DB_SCHEMA.md` | 마이그레이션, ORM 스키마, entity, DB 사용이 있을 때 |
| `DEPLOY.md` | `docs/DEPLOY.md` | CI/CD, Docker, Vercel, 클라우드 설정, 환경변수, 도메인이 있을 때 |
| `DESIGN.md` | `docs/DESIGN.md` | 프론트엔드 UI, Tailwind/테마 토큰, 디자인 시스템, Figma 링크가 있을 때 |
| `ADR.md` | `docs/ADR.md` | 되돌리기 어려운 아키텍처 결정이나 여러 모듈이 있을 때 |

원본은 `templates/docs/<문서>.md`다. 사용자가 다른 위치(`.claude/`, `documents/`, `wiki/` 등)를 원하면 그곳에 둔다. 어디에 두든 진입점 매핑 표에는 실제 경로를 적는다.

## 절차

1. 사용자가 고른 문서만, 원본이 있는 것만 대상으로 한다.
2. 쓰기 전에 목적지 경로를 보여 준다.
3. 복사한 뒤 설치 안내 주석을 지우고, 코드에서 확인되는 값(스택, 패키지 매니저, 테이블 이름, 배포 대상 등)은 채운다. 코드로 알 수 없는 값은 placeholder로 남긴다.
4. 충돌하면 유지 / 백업 후 교체 / 빠진 `##` 섹션만 추가 / 취소 중에서 묻는다.

## 병합 규칙

- `PROJECT_OVERVIEW.md`, `DB_SCHEMA.md`, `DEPLOY.md`, `DESIGN.md`: 병합은 기존 파일에 없는 템플릿 `##` 섹션만 덧붙이는 것이다.
- `ADR.md`: 번호와 인덱스가 깨지기 쉬우니 섹션 병합을 하지 않는다. 유지, 백업 후 교체, 수동 갱신 중에서 고르게 한다.

## 검증

```bash
for doc in PROJECT_OVERVIEW.md DB_SCHEMA.md DEPLOY.md DESIGN.md ADR.md; do
  test -f "$TARGET/docs/$doc" && echo "FOUND docs/$doc"
done
```
