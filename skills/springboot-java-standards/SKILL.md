---
name: springboot-java-standards
description: "Java 17+ 코딩 표준 및 Spring Boot 서비스 개발 가이드. Java 코드 작성/리뷰, 명명 규칙, 불변성, Optional, 스트림, 예외 처리, 제네릭, Lombok 활용, 테스트 작성 시 사용. Spring Boot 프로젝트에서는 references/spring-boot-patterns.md, JPA/QueryDSL 작업 시에는 references/jpa-patterns.md를 함께 참조."
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

## 불변성 및 엔티티 상태 (Immutability & State)

```java
// 불변 DTO는 Record와 final 필드를 선호합니다.
public record MarketDto(Long id, String name, MarketStatus status) {}

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
    .map(userAssembler::toResponse)
    .orElseThrow(() -> new EntityNotFoundException("Market not found"));
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
- 도메인 특화 예외를 생성합니다 (예: `MarketNotFoundException`).
- 중앙에서 다시 던지거나 로깅하는 경우가 아니라면 광범위한 `catch (Exception ex)`는 피합니다.

```java
throw new MarketNotFoundException(slug);
```

## 제네릭 및 타입 안정성 (Generics)

- Raw 타입을 피하고 제네릭 파라미터를 선언합니다.
- 재사용 가능한 유틸리티에는 경계가 있는 제네릭(Bounded Generics)을 선호합니다.

```java
public <T extends Identifiable> Map<Long, T> indexById(Collection<T> items) { ... }
```

---

## Lombok 패턴 및 의존성

### DTO와 Entity 분리 (Assembler 계층)
웹 계층(DTO)과 도메인 계층(Entity) 간의 강결합을 피하기 위해 DTO 내부에 엔티티 변환 메서드를 두지 않고 `Assembler` 클래스(또는 MapStruct 등)를 도입합니다.
Jackson deserialization을 위해 요청 DTO에 `PROTECTED` 파라미터 없는 생성자를 배치합니다.

```java
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class CreateUserRequest {
    @NotBlank
    private String name;

    @Builder
    public CreateUserRequest(String name) {
        this.name = name;
    }
}

@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class UserResponse {
    private Long id;
    private String name;

    @Builder
    public UserResponse(Long id, String name) {
        this.id = id;
        this.name = name;
    }
}

@Component
public class UserAssembler {
    public User toEntity(CreateUserRequest request) {
        return User.builder()
                .name(request.getName())
                .build();
    }

    public UserResponse toResponse(User user) {
        return UserResponse.builder()
                .id(user.getId())
                .name(user.getName())
                .build();
    }
}
```

### 필드 주입 금지 및 생성자 주입 강제
- `@Autowired` 등을 이용한 **필드 주입(Field Injection)은 엄격히 금지**합니다. (의존성 숨김 현상, 순환 참조 방지 및 테스트 용이성 측면)
- 항상 생성자 주입을 사용해야 합니다.

```java
@Service
@RequiredArgsConstructor
public class UserServiceImpl {
    private final UserRepository userRepository;
    private final UserAssembler userAssembler;
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
    assembler/
  user/                 // 또 다른 도메인 모듈
    controller/
    service/
    repository/
    ...
src/main/resources/
  application.yml
src/test/java/... (mirrors main)
```

---

## 상세 참조

상황에 맞는 레퍼런스를 참조하세요:

- **Spring Boot 컨트롤러/서비스/DTO/예외처리 패턴**: `references/spring-boot-patterns.md`
- **JPA Entity/Repository/QueryDSL 패턴**: `references/jpa-patterns.md`
- **JUnit 및 상태 검증 테스트 패턴**: `references/junit-test-patterns.md`

**기억하세요**: 코드는 의도적이고, 타입이 지정되어 있으며, 관찰 가능해야 합니다. 입증된 필요성이 없는 한, 미세 최적화(Micro-optimization)보다는 유지보수성을 위해 최적화하세요.
