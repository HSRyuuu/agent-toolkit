# Spring Boot 패턴 예시

규칙은 `SKILL.md`에 있다. 이 파일은 규칙을 적용한 모양만 보여준다.

## Controller

입력과 응답만 연결한다. 서비스 결과를 그대로 응답에 싣는 한 줄은 지역변수로 쪼개지 않는다.

```java
@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
public class OrderController {
    private final OrderService orderService;

    @GetMapping("/{id}")
    public ResponseEntity<OrderDto.Response> getOrder(@PathVariable long id) {
        return ResponseEntity.ok(orderService.findById(id));
    }

    @PostMapping
    public ResponseEntity<OrderDto.Response> createOrder(@Valid @RequestBody OrderDto.Request request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(orderService.create(request));
    }
}
```

## Service

클래스 레벨 `@Transactional(readOnly = true)`, 쓰기 메서드만 `@Transactional`.

```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class OrderService {
    private final OrderRepository orderRepository;

    public OrderDto.Response findById(long id) {
        OrderEntity order = orderRepository.findById(id)
                .orElseThrow(() -> new OrderException(ORDER_NOT_FOUND, id));
        return OrderDto.Response.fromEntity(order);
    }

    @Transactional
    public OrderDto.Response create(OrderDto.Request request) {
        OrderEntity saved = orderRepository.save(request.toEntity());
        return OrderDto.Response.fromEntity(saved);
    }
}
```

## DTO

기능 단위로 `Request`·`Response`를 묶는다. 매핑은 DTO가 갖는다.

```java
public class OrderDto {
    private OrderDto() {}

    public record Request(@NotBlank String productCode,
                          @NotNull @Min(1) Integer quantity) {
        public OrderEntity toEntity() {
            return OrderEntity.builder()
                    .productCode(productCode)
                    .quantity(quantity)
                    .build();
        }
    }

    public record Response(long id,
                           String productCode,
                           int quantity,
                           OrderStatus status) {
        public static Response fromEntity(OrderEntity entity) {
            return new Response(entity.getId(),
                    entity.getProductCode(),
                    entity.getQuantity(),
                    entity.getStatus());
        }
    }
}
```

### Mapper (여러 소스를 합칠 때만)

```java
@Component
@RequiredArgsConstructor
public class OrderDetailMapper {
    private final MembershipRepository membershipRepository;

    // 주문과 회원 등급을 합치므로 DTO 정적 팩터리로는 표현하기 어렵다
    public OrderDetailResponse toDetailResponse(OrderEntity order) {
        Membership membership = membershipRepository.findActiveByUserId(order.getUserId())
                .orElse(Membership.none());
        return new OrderDetailResponse(order.getId(), order.getProductCode(), membership.grade());
    }
}
```

## 예외 처리

도메인 예외 하나 + `ErrorCode` enum. 핸들러는 `ErrorCode`를 응답으로 옮기기만 한다.

```java
/**
 * 이름은 호출자와의 계약이므로 바꾸면 안 된다. 메시지는 계약이 아니다.
 */
public enum OrderErrorCode {
    INVALID_REQUEST(HttpStatus.BAD_REQUEST, "Invalid request."),
    ORDER_NOT_FOUND(HttpStatus.NOT_FOUND, "Order not found."),
    ORDER_ALREADY_PAID(HttpStatus.CONFLICT, "Order is already paid."),
    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "Internal server error.");

    private final HttpStatus status;
    private final String defaultMessage;

    OrderErrorCode(HttpStatus status, String defaultMessage) {
        this.status = status;
        this.defaultMessage = defaultMessage;
    }

    public HttpStatus status() {
        return status;
    }

    public String defaultMessage() {
        return defaultMessage;
    }
}

/** 호출자가 실패 종류로 갈라야 하면 타입을 새로 만들지 않고 {@link #errorCode()}를 본다. */
public class OrderException extends RuntimeException {
    private final OrderErrorCode errorCode;

    public OrderException(OrderErrorCode errorCode, Object detail) {
        this(errorCode, detail, null);
    }

    public OrderException(OrderErrorCode errorCode, Object detail, Throwable cause) {
        super(errorCode.name() + ": " + detail, cause);
        this.errorCode = errorCode;
    }

    public OrderErrorCode errorCode() {
        return errorCode;
    }
}

@Slf4j
@RequiredArgsConstructor
@RestControllerAdvice
public class OrderExceptionHandler {
    private final Clock clock;

    @ExceptionHandler(OrderException.class)
    public ResponseEntity<ProblemResponse> handleOrderFailure(OrderException exception) {
        return this.problem(exception.errorCode());
    }

    @ExceptionHandler({MethodArgumentNotValidException.class, HttpMessageNotReadableException.class})
    public ResponseEntity<ProblemResponse> handleInvalidRequest() {
        return this.problem(INVALID_REQUEST);
    }

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<ProblemResponse> handleUnexpected(RuntimeException exception) {
        log.error("order_request_failed", exception);
        return this.problem(INTERNAL_SERVER_ERROR);
    }

    private ResponseEntity<ProblemResponse> problem(OrderErrorCode code) {
        ProblemResponse body = new ProblemResponse(code.name(), code.defaultMessage(), clock.instant());
        return ResponseEntity.status(code.status()).body(body);
    }

    public record ProblemResponse(String code, String message, Instant timestamp) {
    }
}
```

실패 종류로 분기할 때는 타입이 아니라 코드를 본다.

```java
} catch (RuntimeException exception) {
    if (exception instanceof OrderException order && order.errorCode() == ORDER_ALREADY_PAID) {
        log.debug("order_already_paid orderId={}", orderId);
        return;
    }
    log.error("failed_pay_order orderId={}", orderId, exception);
}
```

여러 도메인의 ErrorCode enum을 한 핸들러가 받아야 할 때만 공통 `ErrorCode` 인터페이스(`status()`, `defaultMessage()`, `name()`)를 둔다.

## 활성/비활성만 다른 구현

인터페이스 + 실제 구현 + Noop 구현을 두지 않고 한 클래스로 합친다.

```java
@Slf4j
@Component
public class OrderEventPublisher {
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final boolean enabled;

    public OrderEventPublisher(KafkaTemplate<String, String> kafkaTemplate,
                               @Value("${order.publisher.enabled:false}") boolean enabled) {
        this.kafkaTemplate = kafkaTemplate;
        this.enabled = enabled;
    }

    public void publish(List<OrderEvent> events) {
        if (!enabled) {
            log.info("order_event_publish_skipped events={} reason=publisher_disabled", events.size());
            return;
        }
        ...
    }
}
```
