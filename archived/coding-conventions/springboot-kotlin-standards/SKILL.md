---
name: springboot-kotlin-standards
description: >
  Use when writing or reviewing Kotlin code in a Spring Boot project.
  Do NOT use for Java projects.
metadata:
  origin: ECC
---

# Kotlin 코딩 표준

## 우선순위

1. **프로젝트 규칙이 있으면 그것이 우선한다.** `AGENTS.md`·`CLAUDE.md`·프로젝트 스킬·기존 코드 관례가 이 스킬과 다르면 프로젝트 쪽을 따른다.
2. **프로젝트가 정하지 않은 부분은 이 스킬이 기준이다.**

Kotlin·Spring의 일반 관용구는 모델이 이미 안다. 아래는 그 기본 습관과 다르게 지키는 규칙만 적는다.

## 핵심 원칙

- 간결함보다 명확함이 먼저다. 보일러플레이트는 줄이되 가독성을 희생하지 않는다.
- 불변(`val`)이 기본이다. `var`는 상태 변경이 필요한 Entity 필드처럼 이유가 있을 때만 쓴다.

## 규칙

- **주입은 주생성자로만 한다.** 필드 주입(`@Autowired`, `lateinit var`)을 쓰지 않는다. `lateinit var`는 일반 로직에 쓰지 않고 생성자 주입이나 `by lazy`를 쓴다.
- **`!!`는 직후 값이 보장된 맥락에서만 쓴다**(`save` 직후 `id!!` 등). 그 외에는 `?.`·`?:`·`let`으로 처리한다.
- **Entity 상태 변경은 의도가 드러나는 메서드로 한다**(`article.publish()`). 식별자·생성 시각은 `val`, 변경되는 필드만 `var`. 상태 판정을 호출자의 비교로 흩뜨리지 않는다.
- **Entity에 Java식 `@Data`·`@Getter`·`@Setter`를 쓰지 않는다.** JPA는 `plugin.jpa`·`allOpen`(`Entity`·`MappedSuperclass`·`Embeddable`)으로 맞춘다.
- **DTO는 `data class` + `val`이다.** 검증 어노테이션은 `@field:` 접두사를 붙인다. Entity → Response 변환은 Response의 `companion object`에 `from(entity)`로 둔다.
- **도메인 오류는 예외 하나(`GlobalException`) + `ErrorCode` enum**으로 모은다. HTTP 상태와 기본 문구는 enum에 두고, 핸들러는 `ErrorCode` → 응답 변환만 한다. 사례마다 예외 하위 클래스를 만들지 않는다. 조회 실패는 `findByIdOrNull(id) ?: throw GlobalException(ErrorCode.X)`.
- **public 함수는 `Pair`를 반환하지 않는다.** 의미 있는 `data class`를 쓴다. `Pair`·destructuring은 private/내부 함수에서만 허용한다.
- **`when`은 모든 분기를 처리한다**(sealed class 또는 `else`).
- **mutable 컬렉션을 외부에 노출하지 않는다.** `List` 같은 불변 인터페이스로 반환한다.
- **상수는 `object`/`companion object`의 `const val`로 둔다.** 키·접두사처럼 조립이 필요한 값은 `object` 안의 함수로 둔다(`RedisKeys.blacklist(token)`).
- **약어는 일반 단어처럼 쓴다**: `XmlHttpRequest`, `newCustomerId`.
- **미사용 변수·예외·람다 파라미터는 `_`로 표기한다.**
- **로거는 `companion object`에 클래스당 하나**(`LoggerFactory.getLogger(Xxx::class.java)`). 로그는 `[작업명]` 접두사로 구분한다.

## 포매팅

- 프로젝트에 formatter·`.editorconfig`가 있으면 그것을 따른다.
- 없으면: 4칸 공백, 후행 콤마, 파라미터 3개 이상이면 줄마다 하나씩. 단일 표현식 함수만 `=` 구문을 쓰고 복잡한 로직은 블록 본문을 쓴다.

## 패키지 구조

기능 단위(Package-by-Feature)로 나눈다: `domain/<기능>/{controller,service,repository,model/{entity,dto,type}}`. 전역 설정·예외·보안은 `application/`, 여러 기능이 실제로 공유하는 것만 `common/`에 둔다. 기존 프로젝트의 구조가 있으면 그것을 따른다.

## 빌드

Kotlin + Spring Boot는 `kotlin("plugin.spring")`, `kotlin("plugin.jpa")`, `kotlin-reflect`, `jackson-module-kotlin`, `-Xjsr305=strict`, `allOpen` 설정이 있는지 확인한다. 어노테이션 프로세서는 KSP를 우선하고, 지원하지 않는 라이브러리(QueryDSL 등)에만 kapt를 쓴다.

## 테스트

- 리플렉션으로 필드를 주입하지 않는다(`ReflectionTestUtils.setField` 지양).
- 깊은 Mock보다 상태 기반 검증을 우선한다.
- 테스트 이름은 백틱 한글로 쓰고 Given-When-Then 주석으로 구조를 나눈다. mock은 mockito-kotlin을 쓴다.
