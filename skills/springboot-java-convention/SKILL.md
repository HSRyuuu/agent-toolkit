---
name: springboot-java-convention
description: >
  Use whenever writing, modifying, or reviewing Java code in a Spring Boot
  project. Do NOT use for Kotlin projects.
metadata:
  origin: ECC
---

# Java 코딩 컨벤션

## 우선순위

1. **프로젝트 규칙이 있으면 그것이 우선한다.** `AGENTS.md`·`CLAUDE.md`·프로젝트 스킬·기존 코드 관례가 이 스킬과 다르면 프로젝트 쪽을 따른다.
2. **프로젝트가 정하지 않은 부분은 이 스킬이 기준이다.** 모델의 기본 습관보다 이 스킬을 먼저 따른다.

## 먼저 지킬 것 — 기본 습관과 다른 규칙

코드를 쓰기 전에 이 목록을 확인하고, 다 쓴 뒤 다시 대조한다. 자세한 기준은 아래 각 절에 있다.

1. **같은 클래스의 인스턴스 메서드, 특히 private 메서드는 `this.`를 붙여 호출한다** — `this.pushTitle(order)`. 호출하는 자리에서 이 클래스 안의 규칙이라는 것이 바로 보인다.
2. **규칙이 담긴 계산을 인자 안에 숨기지 않는다.** 분기·삼항·문자열 조립·여러 줄 체인은 이름 있는 지역변수나 private 메서드로 뺀 뒤 넘긴다. getter와 단순 호출은 인자에 그대로 둔다.
3. **여러 줄 쿼리 체인의 실행 결과는 지역변수로 받은 뒤 다음 줄에서 가공한다** — `Optional.ofNullable(entity)`, `Set.copyOf(userIds)`, `activeRun != null`.
4. **인자 순서를 해독해야 하는 범용 헬퍼를 미리 만들지 않는다.** 규칙은 그 부분 이름의 private 메서드에 둔다. 같은 규칙이 실제로 반복되면 그때 의미 있는 이름으로 모은다.
5. **메서드·변수 이름은 실제로 일어난 일을 담는다** — `rejected` 대신 `markedFailed`, `claim` 대신 `claimRun`.
6. **여러 줄 record는 컴포넌트를 `(` 뒤 첫 컴포넌트 열에 맞춰 한 줄에 하나씩 쓴다.**
7. **Entity → DTO 매핑은 DTO의 `fromEntity(entity)`에 둔다.** Repository에 `toModel`을 두지 않는다.
8. **도메인 오류는 예외 하나 + `ErrorCode` enum이 기본이다.** 실패 종류는 `errorCode()`로 가른다.
9. **활성/비활성만 다른 구현은 한 클래스 + `enabled` 조기 반환으로 합친다.**

## 핵심 원칙

- **사람이 위에서 아래로 한 번에 읽을 수 있는 코드가 가장 먼저다.** 코드가 몇 줄 길어지더라도 짧은 코드·영리한 코드·미세한 성능보다 앞선다.
- 조회 → 검증 → 분기 → 실행 → 결과가 위에서 아래로 읽히게 쓴다.
- 리팩터링은 관찰 가능한 계약(호출 순서, 트랜잭션 전파, 응답 코드, 직렬화 형태, 재시작 식별자, 실패 전파)을 보존한다. 구조를 단순화해도 비동기 완료 확인이나 통합 롤백을 제거하지 않는다.

## 메서드 분리와 지역변수

메서드가 길어지거나 한 줄에 규칙이 겹칠 때, 읽는 사람이 흐름과 세부 규칙을 나눠 볼 수 있게 쪼갠다. 짧고 곧은 메서드까지 쪼개지 않는다.

- 생성자·팩터리·다른 호출의 인자 안에 분기·삼항·문자열 조립·여러 줄 체인을 넣지 않는다. 먼저 이름 있는 지역변수로 받거나 private 메서드로 뺀다. 조건식(`BooleanExpression predicate`), 구간(`TimeRange conversionRange`), 수정 쿼리(`JPAUpdateClause query`)가 대표적이다. getter, 이미 이름이 있는 메서드의 단순 호출, 서비스 결과를 그대로 응답에 싣는 것은 인자에 둬도 된다.
- 결과 하나를 여러 부분으로 조립하는 메서드(메시지·응답·파라미터 조립 등)는 목차처럼 쓴다. 각 부분을 이름 있는 지역변수로 받고, 마지막 줄에서 조립만 한다.
- 각 부분의 규칙(분기·기본값·포맷·문자열 조립)은 그 부분 이름의 private 메서드 하나에 둔다. 이름은 만들어지는 값이다(`pushTitle`, `pushBody`). 조립 메서드에 삼항·문자열 연결이 섞이지 않게 한다.
- 긴 독립 분기는 같은 클래스의 private 메서드로 뺀다(`restartFailedRun`). 같은 객체 생성이 두 분기에 반복되면 그것도 private 메서드 하나로 모은다.
- **여러 줄 쿼리 체인(QueryDSL·client 호출 등)의 실행 결과는 지역변수로 받은 뒤 다음 문장에서 가공한다.** `Optional.ofNullable(...)`·`Set.copyOf(...)`·`!= null` 비교처럼 짧은 후처리도 체인 바깥에서 한다. `findById(id).orElseThrow(...)`처럼 한두 줄로 읽히는 Optional 체인과 `stream()...toList()` 파이프라인은 그대로 둔다.
- 기계적으로 감싸지는 않는다. 이미 있는 메서드를 한 번 단순 호출하는 것, 이미 분리된 상수, projection 결과를 그대로 반환하는 것은 변수나 private 래퍼로 한 번 더 감싸지 않는다.
- `prefixed(prefix, separator, text)`처럼 인자 순서를 해독해야 하는 범용 헬퍼를 미리 만들지 않는다. 부분마다 규칙을 그 부분 이름의 메서드에 둔다. 같은 규칙이 실제로 여러 곳에서 반복되면 그때 의미가 드러나는 이름으로 모은다.
- 우리가 소유한 타입이면, 데이터를 꺼내는 방법은 그 타입의 메서드로 둔다(`message.param(key)`). 인터페이스 static 메서드나 util 클래스에 `text(params, key)`처럼 두지 않는다.
- 인터페이스에는 구현체가 지킬 계약을 둔다. 계약과 무관한 static·default 유틸 메서드를 두지 않는다.
- 인스턴스 메서드 호출에는 `this.`를 붙인다(위 1번).

```java
@Override
public PushContent push(Order order) {
    String title = this.pushTitle(order);
    String body = this.pushBody(order);
    String deepLink = this.deepLink(order);

    return new PushContent(title, body, deepLink);
}

private String pushTitle(Order order) {
    String storeName = order.param("storeName");
    return storeName.isEmpty() ? PUSH_TITLE : storeName + ", " + PUSH_TITLE;
}

// Bad: 조립 자리에서 계산하고, 범용 헬퍼 인자로 규칙을 숨긴다
return new PushContent(
        prefixed(text(order.params(), "storeName"), ", ", PUSH_TITLE),
        prefixed(order.periodText(), " · ", PUSH_BODY),
        deepLink(order));
```

```java
// 조회 결과를 받은 뒤 가공한다
Integer activeRun = queryFactory
        .selectOne()
        .from(orderEntity)
        .where(orderEntity.status.in(ACTIVE_STATUSES))
        .fetchFirst();
return activeRun != null;

// Bad: 체인 끝에서 바로 비교한다
return queryFactory.selectOne().from(orderEntity)...fetchFirst() != null;
```

## 이름

- 이름에 업무 대상·수행 동작·실제 결과를 담는다. 짧은 일반어보다 전체 의미가 드러나는 쪽을 고르되, 주변 이름과 구분되는 데까지만 길게 쓴다.

| 대신 | 쓴다 | 이유 |
|------|------|------|
| `claim()`, `Claim` | `claimRun()`, `ClaimedRun` | 무엇을 선점했는지 |
| `rejected` | `markedFailed` | 실제로 일어난 일(실패로 기록됨) |
| `currentSnapshot()` | `serializeCurrentSnapshot()` | JSON 문자열을 만든다 |
| `previous` | `restartParameters` | fallback 값까지 담는다 |
| `previousOccurrence()` | `firstRunBoundary()` | lookback 경계도 반환한다 |
| `campaignClaimTransactionTemplate` | `runClaimTransaction` | 기술 타입 접미사보다 업무 역할 |
| `ConsentWriter` | `ChannelWriter` | 이 단계의 산출물은 채널 |

- DB·API와 같은 개념에는 같은 용어를 쓴다. `key`와 `code`, 동의 여부와 도달 수단처럼 서로 다른 의미를 섞지 않는다. 다만 모든 내부 이름을 컬럼명에 기계적으로 맞추지는 않는다.
- 약어는 일반 단어처럼 쓴다: `XmlHttpRequest`, `newCustomerId`.
- `UPPER_SNAKE_CASE`는 값 상수에 쓴다. `static final ObjectMapper objectMapper`처럼 상태나 동작을 가진 객체는 camelCase로 쓴다.
- 코드로 관리되는 고정 식별 문자열(`"ORDER_PAID"`)이 여러 곳에 반복되면 enum으로 모으고 `OrderCode.ORDER_PAID.name()`으로 참조한다. 운영 데이터로 늘어나는 값은 enum화하지 않는다(값 객체와 시간 절).

## 데이터 객체와 매핑

- 필드가 적고 고정된 전달 값·조회 결과·스냅샷은 record가 기본이다.
- 필요하면 일반 클래스 DTO를 쓴다. 다음 경우엔 클래스가 더 읽기 좋다.
  - 필드가 많고 선택값이 섞여 생성 시 `@Builder`가 읽기 쉬운 경우
  - `@ModelAttribute` 바인딩이나 `Projections.bean`처럼 기본 생성자·setter가 필요한 경우
  - 값을 단계적으로 채우거나 공통 상위 응답을 상속하는 경우
- 클래스 DTO는 `@Getter` + `@NoArgsConstructor(access = PROTECTED)`를 기본으로 하고, setter는 바인딩에 필요할 때만 연다.
- 프로젝트가 이미 클래스 DTO를 쓰고 있으면 그 관례를 따른다. 같은 역할의 DTO(예: API 응답)는 이유 없이 record와 클래스를 섞지 않는다.
- record 선언이 한 줄에 들어가면 한 줄로 쓴다. 길면 컴포넌트를 한 줄에 하나씩 쓴다. 첫 컴포넌트는 `(` 바로 뒤에 두고, 다음 컴포넌트를 첫 컴포넌트 시작 열에 맞춘 뒤, 마지막 컴포넌트 뒤에 `) {`를 둔다. 어노테이션이 붙은 컴포넌트도 같다.
- 메서드 내부 결과 두세 값을 묶는 타입은 private record로 충분하다. 한 기능 전용 조회 모델이 여러 개면 `<기능>/model` 패키지의 독립 record로 뺀다.
- Entity → DTO 매핑은 DTO의 `fromEntity(entity)` 정적 팩터리에 둔다. entity를 받는 생성자가 이미 있으면 그것을 재사용하고, 생성자와 팩터리를 매번 둘 다 새로 만들지는 않는다. `Optional.map(OrderDto::fromEntity)`처럼 메서드 참조로 쓴다.
- Repository에 `toModel`/`toDto` 필드 매핑을 남기지 않는다. 여러 소스를 합치거나 변환에 정책이 섞일 때만 `Mapper`/`Assembler`로 분리한다.
- 정적 팩터리는 생성 의미가 이름으로 더 분명해질 때만 쓴다. 값 조합은 `of(...)`, 엔티티 변환은 `fromEntity(...)`로 쓰고, 모든 생성자마다 `of`를 덧붙이지 않는다.
- 공통 검증과 방어 복사는 생성자(compact constructor)에 둔다. 팩터리를 거치지 않는 생성에도 불변식이 적용되어야 한다.
- API 한 기능의 요청·응답은 `<기능>Dto.Request`·`<기능>Dto.Response`로 묶는 것을 우선한다. 프로젝트가 이미 개별 탑레벨 타입(`CreateOrderRequest`)을 쓰면 그쪽을 따르고, 한 프로젝트 안에서 섞지 않는다.

```java
public record OrderSummary(long id,
                           String status,
                           LocalDateTime createdAt) {
    public static OrderSummary fromEntity(OrderEntity entity) {
        return new OrderSummary(entity.getId(), entity.getStatus(), entity.getCreatedAt());
    }
}

public class OrderRunDto {
    private OrderRunDto() {}

    public record Request(@NotBlank String orderCode, OffsetDateTime referenceAt) {}

    public record Response(long runId, String status) {}
}
```

## 계층과 인터페이스

- Controller는 입력과 응답을 연결한다. 여러 저장소 작업의 순서·검증·트랜잭션은 Service, 조회와 변경 쿼리는 Repository가 맡는다. Controller에 SQL·트랜잭션이 있으면 Service/Repository로 옮긴다.
- 단순 위임만 늘리는 계층은 만들지 않는다.
- 구현이 하나뿐인 `XxxService` + `XxxServiceImpl` 쌍을 관성으로 만들지 않는다. 구체 클래스 하나로 시작한다.
- 같은 동작의 활성/비활성만 다른 구현(`KafkaPublisher` + `NoopPublisher`)은 한 구체 클래스와 `enabled` 플래그 조기 반환으로 합친다. 실제로 늘어나는 전략이나 독립 전송 방식은 인터페이스로 유지한다.
- 패키지는 기술 종류(`service`·`model`·`util`)로 전역에 모으기보다 기능과 실행 단계 가까이에 둔다. 기능 전용 쿼리·모델·계산기는 그 기능 안에 두고, 여러 기능이 실제로 공유할 때만 공통 패키지로 올린다.
- 기존 프로젝트의 패키지 구조를 따른다. 구조를 바꾸자는 판단은 따로 제안한다. 따를 구조가 없는 새 프로젝트면 기능 단위 패키지로 시작한다.

## Repository와 SQL

- QueryDSL 조회는 `fetchFirst()`·`fetchOne()`·`fetch()`까지 실행한 결과를 지역변수로 받은 뒤 Optional 변환·매핑·방어 복사를 한다.
- 여러 소스를 합친 조회는 생성자 projection을 먼저 쓴다. DTO 생성자를 쓸 수 있으면 Tuple 해체용 helper를 만들지 않는다.
- update/delete는 clause를 `query` 지역변수로 구성한 뒤 실행한다. bulk 쿼리는 flush/clear와 트랜잭션 경계를 보존한다.
- 긴 SQL이 로직을 가리면 같은 패키지의 `<사용클래스>Sql`로 옮긴다(package-private final class, `static final String`, private 생성자).
- JDBC는 실제 bulk insert/upsert나 ORM으로 표현하기 어려운 쿼리에만 쓴다. 조회 전체를 JDBC로 바꾸거나 공통 repository 프레임워크를 만들지 않는다.

예시: `references/jpa-patterns.md`

## 값 객체와 시간

- 항상 함께 다니고 지켜야 할 불변식이 있는 값(시간 구간, 금액+통화 등)은 값 객체로 묶는다. 함께 전달된다는 이유만으로 모든 파라미터 묶음을 타입으로 만들지는 않는다. `from`·`to` 파라미터 쌍은 구간 타입 하나로 바꾸고, 조회부터 저장 직전까지 구간으로 전달한 뒤 DB 컬럼·외부 파라미터 경계에서만 분해한다.
- 구간 타입은 null·역전·양 끝 포함 여부·빈 구간 허용 여부를 명시하고 생성 시 검증한다. 기존 `[from, to)` 계약이 같은 경계의 빈 구간을 허용하면 이를 거부하도록 바꾸지 않는다.
- 시간 변환은 방향이 이름에 드러나는 공통 메서드로 모은다(`toUtcLocalDateTime`, `utcToInstant`). `ZoneId.systemDefault()`에 의존하지 않고, 반복되는 시간대는 상수로 둔다(`TimeZoneUtil.SEOUL`).
- `Instant`와 `LocalDateTime`의 선택은 그 시스템의 저장·도메인 계약을 따른다. 시간 util은 변환만 맡고, 업무 정책은 계산기가 맡는다.
- 코드로 관리되는 고정 집합은 enum을 한 출처로 삼는다. DB/API 경계가 String이면 기존 문자열 계약을 유지하고, 운영 데이터로 자유롭게 늘어나는 값을 임의로 enum화하지 않는다.

```java
/** UTC 기준 반개구간 [from, to). 두 경계가 같으면 빈 구간이다. */
public record TimeRange(LocalDateTime from, LocalDateTime to) {
    public TimeRange {
        Objects.requireNonNull(from, "from must not be null");
        Objects.requireNonNull(to, "to must not be null");
        if (from.isAfter(to)) {
            throw new IllegalArgumentException("from must not be after to");
        }
    }
}
```

## 예외

- 같은 도메인의 오류는 **도메인 예외 하나 + `ErrorCode` enum**으로 모은다. 사례마다 예외 하위 클래스를 만들지 않는다. 추가 데이터를 실어야 하거나 catch 대상을 따로 잡아야 하는(재시도 가능 여부 등) 경우에만 하위 타입을 둔다.
- HTTP 상태와 기본 문구는 `ErrorCode` enum에 두고, `@RestControllerAdvice` 핸들러는 `ErrorCode` → 응답 변환만 한다. 핸들러에 상태 코드나 문구 리터럴을 두지 않는다.
- 호출자가 실패 종류로 갈라야 하면 타입을 새로 만들지 않고 `exception.errorCode()`를 본다.
- 오류 코드 이름이 응답으로 나가면 enum 상수 이름 변경도 계약 변경이다.
- 프로그래밍 오류(`IllegalArgumentException`, `IllegalStateException` 등)는 표준 예외를 유지한다.

예시: `references/spring-boot-patterns.md`의 예외 처리 절

## Entity와 Lombok

- Entity는 `@NoArgsConstructor(access = PROTECTED)` + `@Getter`를 기본으로 하고, 상태 변경은 의도가 드러나는 메서드로 제한한다. 상태 판정을 호출자의 문자열 비교로 흩뜨리지 않는다(`order.isPaid()`).
- Entity에 `@Data`·`@Setter`·클래스 레벨 `@EqualsAndHashCode`를 쓰지 않는다. `@ToString`을 쓰면 연관 필드는 `@ToString.Exclude`로 뺀다.
- Lombok은 반복 코드를 줄이는 데 쓴다. 생성되는 setter·equals·생성자가 객체 계약을 깨지 않는지 확인한다.

## Spring과 실행 상태

- 순수 계산기는 Spring 없이 실행 가능하게 둔다.
- 실행별 상태는 실행 범위 객체(`@StepScope` 빈, 요청 객체 등)에 두고 싱글턴 필드에 저장하지 않는다.
- Optional은 반환 타입에만 쓴다. 필드·파라미터로 쓰지 않는다.

## 주석

- 코드만으로 알 수 없는 제약·경계·상태 변경 주체에 쓴다. 분기의 이유가 코드로 드러나지 않으면 그 자리에 한 줄 주석을 둔다. 예: `// worker가 시작한 실행의 상태는 listener가 관리한다.`
- 정책을 계산하는 메서드는 그 메서드가 지키는 정책을 한 줄로 적을 수 있다. 예: `// 성공 이력이 없으면 최초 경계에서 조회 오프셋을 뺀 시각을 조회 시작점으로 삼는다.`
- 이름을 풀어 쓴 설명, 결정 근거, 변경 이력은 남기지 않는다.

## 포매팅

- 프로젝트에 formatter·Checkstyle·`.editorconfig`가 있으면 그것을 따른다.
- 없으면: 120자, K&R 중괄호, 단일 문장에도 중괄호, 와일드카드 import 금지, static import → 일반 import 순서.

## 테스트

- 변경된 동작의 경계와 실패 경로를 그 프로젝트의 기존 테스트 방식으로 검증한다.
- 순수 계산은 Spring 컨텍스트 없이, DB 원자성은 필요한 만큼의 통합 테스트로 확인한다.
- 리플렉션으로 필드를 주입하지 않는다. 포맷 변경에 전용 테스트를 새로 만들지 않는다.

예시: `references/junit-test-patterns.md`

## 상세 참조

- **Controller/Service/DTO/예외 처리 예시**: `references/spring-boot-patterns.md`
- **JPA Entity/Repository/QueryDSL 예시**: `references/jpa-patterns.md`
- **JUnit 테스트 예시**: `references/junit-test-patterns.md`
