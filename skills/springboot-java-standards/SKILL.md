---
name: springboot-java-standards
description: >
  Use when writing or reviewing Java 17+ code in a Spring Boot project,
  especially naming, package structure, immutability, Optional, streams,
  records/sealed classes, generics, Lombok, exceptions, tests, JPA/QueryDSL, or
  service-layer design. Triggers: "Java 코드 리뷰", "Spring Boot 서비스 작성",
  "Optional 써도 돼?", "JPA/QueryDSL 패턴". Do NOT use for Kotlin projects.
metadata:
  origin: ECC
---

# Java 코딩 표준 (Java Coding Standards)

Spring Boot 서비스에서 읽기 쉽고 유지보수가 용이한 Java(17+) 코드를 작성하기 위한 표준입니다.

## 적용 시점

- Spring Boot 프로젝트에서 Java 코드를 작성하거나 리뷰할 때
- 명명 규칙, 불변성 또는 예외 처리 컨벤션을 강제할 때
- Record, Sealed 클래스 또는 패턴 매칭(Java 17+)을 사용할 때
- Optional, 스트림 또는 제네릭 사용을 검토할 때
- 패키지 구조 및 프로젝트 레이아웃을 구성할 때

## 핵심 원칙

- 기교보다는 명확함을 우선시합니다.
- 기본적으로 불변(Immutable) 상태를 지향하며, 공유되는 가변 상태를 최소화합니다.
- 의미 있는 예외를 통해 최대한 빨리 실패(Fail-fast)하도록 합니다.
- 일관된 명명 규칙과 패키지 구조를 유지합니다.
- 조회 → 검증 → 분기 → 실행 → 결과가 위에서 아래로 읽히게 씁니다. 긴 체인을 다른 호출의 인자에 중첩하지 않고, 실행 결과를 의미 있는 지역변수로 받습니다.
- 리팩터링은 관찰 가능한 계약(호출 순서, 트랜잭션 전파, 응답 코드, 직렬화 형태, 실패 전파)을 보존합니다.

---

## 명명 규칙 (Naming)

```java
// 클래스/Record: PascalCase
public class MarketService {}
public record Money(BigDecimal amount, Currency currency) {}

// 메서드/필드: camelCase
private final MarketRepository marketRepository;
public Market findBySlug(String slug) {}

// 상수: UPPER_SNAKE_CASE
private static final int MAX_PAGE_SIZE = 100;

// 약어(Acronym)는 일반 단어처럼 처리
XmlHttpRequest, newCustomerId, supportsIpv6OnIos
// Bad: XMLHTTPRequest, newCustomerID, supportsIPv6OnIOS
```

- 이름에 업무 대상·수행 동작·실제 결과를 담습니다. `claim`보다 `claimRun`, JSON을 반환하면 `serializeSnapshot`처럼 전체 의미를 드러냅니다.
- DB·API와 같은 개념에는 같은 용어를 씁니다. `key`와 `code`처럼 서로 다른 의미를 섞지 않되, 모든 내부 이름을 컬럼명에 기계적으로 맞추지는 않습니다.
- 긴 독립 분기는 먼저 같은 클래스의 private 메서드로 나눕니다. 짧은 단순 호출까지 지역변수나 래퍼로 감싸지 않습니다.

## 불변성 및 엔티티 상태 (Immutability & State)

- 고정 필드 DTO·조회 결과·스냅샷은 **record를 우선**합니다. 상태 변경, 표현 은닉, 프레임워크 제약(JPA Entity 등)이 있을 때만 클래스를 씁니다.
- 짧은 record는 한 줄로, 여러 줄이면 컴포넌트를 한 줄에 하나씩 씁니다. 첫 컴포넌트는 `(` 바로 뒤에 두고 다음 컴포넌트를 첫 컴포넌트 시작 열에 맞춘 뒤, 마지막 컴포넌트 뒤에 `) {`를 둡니다.
- 메서드 내부 결과 두세 값을 묶는 타입은 private record로 충분합니다. 기능 전용 조회 모델이 여러 개일 때만 독립 record로 승격합니다.

```java
// 불변 DTO는 Record와 final 필드를 선호합니다.
public record MarketDto(Long id, String name, MarketStatus status) {}

// 여러 줄 record 포매팅
public record MarketSummary(Long id,
                            String name,
                            MarketStatus status,
                            LocalDateTime closedAt) {
}

public class Market {
  private final Long id;
  private String name;
  private MarketStatus status;
  
  // setter를 무분별하게 만들지 않고, 도메인의 행위와 의도를 나타내는 비즈니스 메서드를 제공합니다.
  public void activate() {
      this.status = MarketStatus.ACTIVE;
  }
  
  public void close(String reason) {
      this.status = MarketStatus.CLOSED;
      // 관련된 비즈니스 로직 처리...
  }
}
```

### JPA 엔티티 작성 시 Lombok 안티패턴 엄격 금지
- `@Data`는 엔티티 클래스에 절대 사용하지 않습니다.
- `@ToString` 사용 시 연관관계 필드로 인한 무한 루프나 지연 로딩(LazyLoading) 폭발 방지를 위해 `@ToString(exclude = "연관관계필드")`를 강제합니다.
- `@EqualsAndHashCode`는 JPA 프록시 특성을 무시하므로, 비즈니스 키(Business Key)를 통해서만 재정의합니다.

## Optional 사용

- **클래스 필드나 메서드 파라미터로는 절대 `Optional`을 사용하지 않습니다.** 직렬화(Serializable)가 되지 않으며, 불필요한 객체 래핑 비용이 발생합니다.

```java
// find* 메서드에서는 Optional을 반환합니다.
Optional<Market> market = marketRepository.findBySlug(slug);

// 반환된 Optional은 get() 대신 map/flatMap을 사용합니다.
return market
    .map(MarketResponse::from)
    .orElseThrow(() -> new MarketException(MarketErrorCode.MARKET_NOT_FOUND, slug));
```

## 스트림 (Streams)

```java
// 변환 작업에 스트림을 사용하고, 파이프라인은 짧게 유지합니다.
List<String> names = markets.stream()
    .map(Market::name)
    .filter(Objects::nonNull)
    .toList();

// 복잡하고 중첩된 스트림은 피하세요. 명확성을 위해 루프가 나을 수 있습니다.
```

## 예외 처리 (Exceptions)

- 도메인 에러에는 Unchecked Exception을 사용하고, 기술적인 예외는 컨텍스트를 포함하여 래핑합니다.
- 같은 도메인의 오류는 **도메인 예외 하나 + `ErrorCode` enum**으로 모읍니다. 사례마다 예외 하위 클래스를 만들지 않습니다.
- HTTP 상태와 응답 문구는 `ErrorCode` 한 곳에 두고, `@RestControllerAdvice` 핸들러는 응답 변환만 담당합니다.
- 프로그래밍 오류(`IllegalArgumentException`, `IllegalStateException` 등)는 표준 예외를 유지합니다.
- 오류 코드 문자열이 외부로 나가면 enum 상수 이름 변경도 계약 변경입니다.
- 중앙에서 다시 던지거나 로깅하는 경우가 아니라면 광범위한 `catch (Exception ex)`는 피합니다.

```java
throw new MarketException(MarketErrorCode.MARKET_NOT_FOUND, slug);
```

전체 구성은 `references/spring-boot-patterns.md`의 예외 처리 절을 참조하세요.

## 제네릭 및 타입 안정성 (Generics)

- Raw 타입을 피하고 제네릭 파라미터를 선언합니다.
- 재사용 가능한 유틸리티에는 경계가 있는 제네릭(Bounded Generics)을 선호합니다.

```java
public <T extends Identifiable> Map<Long, T> indexById(Collection<T> items) { ... }
```

---

## 매핑 · 계층 · Lombok 패턴

### Entity ↔ DTO 매핑 위치

- 기본은 **DTO 쪽 정적 팩터리**입니다. Entity → DTO는 `UserResponse.from(user)`, Request → Entity는 `request.toEntity()`에 둡니다.
- 여러 소스를 합치거나 변환에 정책이 섞이면 그때 `Mapper`/`Assembler`(또는 MapStruct)로 분리합니다. 단순 위임만 하는 Assembler를 기본 계층으로 두지 않습니다.
- Repository에 `toModel`/`toDto` 필드 매핑을 남기지 않습니다. 조인 조회는 DTO 생성자 projection을 먼저 고려합니다.
- 프로젝트가 계층 의존을 명시적으로 제한하면(DTO가 도메인 타입을 몰라야 하면) 그 경계를 따라 Mapper를 씁니다.
- DTO 네이밍은 두 방식 모두 허용합니다. 개별 탑레벨 타입(`CreateUserRequest`·`UserResponse`)과 기능 단위 묶음(`UserDto.Request`·`UserDto.Response`) 중 프로젝트가 이미 쓰는 쪽을 따르고, 한 프로젝트 안에서 섞지 않습니다.
- record는 Jackson 역직렬화를 지원합니다. 클래스를 써야 한다면 `PROTECTED` 기본 생성자를 둡니다.

```java
public record CreateUserRequest(@NotBlank @Size(min = 2, max = 50) String name,
                                @NotBlank @Email String email) {
    public User toEntity() {
        return User.builder()
                .name(name)
                .email(email)
                .build();
    }
}

public record UserResponse(Long id,
                           String name,
                           String email) {
    public static UserResponse from(User user) {
        return new UserResponse(user.getId(), user.getName(), user.getEmail());
    }
}
```

### 인터페이스는 필요할 때만

- 구현이 하나뿐인 `XxxService` + `XxxServiceImpl` 쌍을 관성으로 만들지 않습니다. 구체 클래스 하나로 시작합니다.
- 실제로 늘어나는 전략, 독립적인 전송 방식, 의존성 격리가 필요해질 때 인터페이스를 도입합니다.
- 같은 동작의 활성/비활성만 다른 구현은 한 구체 클래스와 조기 반환으로 합칩니다.
- 단순 위임만 늘리는 계층은 만들지 않습니다. Controller는 입력과 응답을 연결하고, 순서·검증·트랜잭션은 Service, 쿼리는 Repository가 맡습니다.

### 필드 주입 금지 및 생성자 주입 강제
- `@Autowired` 등을 이용한 **필드 주입(Field Injection)은 엄격히 금지**합니다. (의존성 숨김 현상, 순환 참조 방지 및 테스트 용이성 측면)
- 항상 생성자 주입을 사용해야 합니다.

```java
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
}
```

---

## 포매팅 및 스타일 (Formatting)

- 프로젝트 표준에 따라 2칸 또는 4칸 공백을 일관되게 사용합니다.
- 컬럼 제한: 100자 (package/import 문 예외).
- K&R 스타일 중괄호를 사용하며, 단일 문장에도 중괄호 필수입니다.
- 파일당 하나의 public 탑레벨 타입을 유지합니다.
- 멤버 순서: 상수 → 필드 → 생성자 → public 메서드 → protected → private.

```java
// 중괄호 필수
if (condition) {
  return value;
}
```

## Import 규칙

- 와일드카드 import(`*`)를 사용하지 않습니다.
- 순서: static import → non-static import (그룹 내 ASCII 정렬, 그룹 간 빈 줄 하나).

```java
import java.util.List;
import java.util.Map;
// Bad: import java.util.*;
```

## Switch 문

모든 switch는 `default`를 포함합니다 (enum 전체 매칭 제외).

---

## 피해야 할 코드 스멜 (Code Smells)

- 긴 파라미터 리스트 → DTO나 빌더(Builder)를 사용하세요.
- 깊은 중첩 → Early Return을 사용하세요.
- 매직 넘버 → 명명된 상수를 사용하세요.
- 정적 가변 상태 → 의존성 주입(Dependency Injection)을 선호하세요.
- 비어있는 catch 블록 → 로깅 후 조치를 취하거나 다시 던지세요.

## 로깅 (Logging)

단일 요청이 여러 스레드나 서비스를 오가는 환경(MSA, 비동기 등)을 고려하여 `MDC (Mapped Diagnostic Context)`를 활용해 모든 로그 라인에 `trace-id`나 `user-id`가 남도록 로깅 정책을 설정하는 것을 권장합니다.

```java
private static final Logger log = LoggerFactory.getLogger(MarketService.class);

// MDC 활용 예시 (일반적으로 Filter, Interceptor 등 앞단에서 설정)
MDC.put("traceId", UUID.randomUUID().toString());

log.info("fetch_market slug={}", slug);
log.error("failed_fetch_market slug={}", slug, ex);

MDC.clear();
```

## Null 처리 (Null Handling)

- 불가피한 경우에만 `@Nullable`을 허용하며, 그 외에는 `@NonNull`을 사용합니다.
- 입력값에 대해 Bean Validation (`@NotNull`, `@NotBlank` 등)을 사용합니다.

## 값 객체와 시간 (Value Objects & Time)

- 여러 계층에서 함께 전달되는 값은 의미 있는 값 객체로 묶습니다. 시간 구간은 조회부터 저장 직전까지 구간 타입으로 전달하고, DB 컬럼·외부 파라미터 경계에서만 분해합니다.
- 구간 타입은 null·역전·양 끝 포함 여부·빈 구간 허용 여부를 명시하고 생성 시 검증합니다. 기존 `[from, to)` 계약이 같은 경계의 빈 구간을 허용한다면 이를 거부하도록 바꾸지 않습니다.
- 시간 변환은 출발·도착 의미가 드러나는 공통 메서드로 모읍니다. `toUtcLocalDateTime`·`utcToInstant`처럼 방향을 이름에 담고, `ZoneId.systemDefault()`에 의존하지 않습니다.
- `Instant`와 `LocalDateTime`의 선택은 그 시스템의 저장·도메인 계약을 따릅니다. 시간 util은 변환만 맡고, 업무 정책은 계산기가 맡습니다.
- 코드로 관리되는 고정 집합은 enum을 한 출처로 삼습니다. DB/API 경계가 String이면 기존 문자열 계약을 유지하고, 운영 데이터로 자유롭게 늘어나는 값을 임의로 enum화하지 않습니다.

```java
/** UTC 기준 [from, to). 같은 경계는 빈 구간으로 허용한다. */
public record TimeRange(LocalDateTime from,
                        LocalDateTime to) {
    public TimeRange {
        Objects.requireNonNull(from, "from");
        Objects.requireNonNull(to, "to");
        if (to.isBefore(from)) {
            throw new IllegalArgumentException("to must not be before from: " + from + " ~ " + to);
        }
    }
}
```

## 주석 (Comments)

- 코드만으로 알 수 없는 제약·경계·상태 변경 주체에 씁니다 (구간의 포함 관계, 트랜잭션 밖 호출 금지 이유 등).
- 이름을 풀어 쓴 설명이나 변경 이력은 남기지 않습니다.

## 유틸리티 클래스 (Utility Class)

인스턴스화를 방지합니다:
```java
public final class DateUtils {
    private DateUtils() {
        throw new AssertionError("Utility class cannot be instantiated");
    }

    public static LocalDateTime startOfDay(LocalDate date) {
        return date.atStartOfDay();
    }
}
```

---

## 테스트 (Testing)

깊은 Mock 지향 테스트와 리플렉션을 이용한 구조를 지양하고, **객체 행위와 상태 검증** 중심의 테스트 작성을 위해 별도로 분리된 패턴을 따릅니다.

- 변경된 동작의 경계와 실패 경로를 그 프로젝트의 기존 테스트 방식으로 검증합니다.
- 순수 계산은 Spring 컨텍스트 없이, DB 원자성은 필요한 만큼의 통합 테스트로 확인합니다.
- 포맷 변경에 전용 테스트를 새로 만들지 않습니다.

참조: `references/junit-test-patterns.md`

---

## 프로젝트 구조 (Project Structure)

**도메인형 패키지 구조(Package-by-Feature)**를 디폴트로 강력히 권장합니다. 응집도를 높이고 변경 범위를 최소화할 수 있습니다.

```
src/main/java/com/example/app/
  global/               // 글로벌 설정, 예외 처리, 공통 유틸리티
    config/
    exception/
    util/
  market/               // 특정 도메인 모듈 (Package-by-Feature)
    controller/
    service/
    repository/
    domain/
    dto/
  user/                 // 또 다른 도메인 모듈
    controller/
    service/
    repository/
    ...
src/main/resources/
  application.yml
src/test/java/... (mirrors main)
```

- 기술 종류만으로 전역 `service`·`model`·`util`에 모으지 않습니다. 기능 전용 쿼리·조회 모델·계산기는 해당 기능 안에 둡니다.
- 기능 전용 조회 모델이 여러 개이면 `<기능>/model`의 독립 record로 둡니다.
- 변환이 복잡해 Mapper/Assembler를 분리한 경우에만 `assembler/`(또는 `mapper/`)를 만듭니다.
- 위 하위 레이어는 관례이지 고정 틀이 아닙니다. 실행 단계가 뚜렷한 모듈(배치 Job 등)은 레이어 대신 실행 단계 이름으로 나눕니다.
- 공통화는 실제 공유 의미를 기준으로 합니다. 기능 정책까지 범용 util로 끌어올리지 않습니다.

---

## 상세 참조

상황에 맞는 레퍼런스를 참조하세요:

- **Spring Boot 컨트롤러/서비스/DTO/예외처리 패턴**: `references/spring-boot-patterns.md`
- **JPA Entity/Repository/QueryDSL 패턴**: `references/jpa-patterns.md`
- **JUnit 및 상태 검증 테스트 패턴**: `references/junit-test-patterns.md`

**기억하세요**: 코드는 의도적이고, 타입이 지정되어 있으며, 관찰 가능해야 합니다. 입증된 필요성이 없는 한, 미세 최적화(Micro-optimization)보다는 유지보수성을 위해 최적화하세요.
