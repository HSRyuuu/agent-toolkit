# JUnit 테스트 패턴 예시

규칙은 `SKILL.md`의 테스트 절에 있다.

## 원칙

- 리플렉션(`ReflectionTestUtils.setField()`)으로 필드를 주입하지 않는다. 생성 이후에만 생기는 값(ID 등)은 실제로 저장한 뒤 확인한다.
- 순수 계산기와 도메인 객체는 Spring 컨텍스트나 Mock 없이 POJO로 검증한다.
- 부분 모킹(Spy)은 쓰지 않는다. 필요하다는 느낌이 들면 객체 역할이 섞였는지 먼저 본다.
- Mock은 협력 객체 경계에서만 쓴다. `mock()`으로 만든 뒤 테스트 대상에 생성자로 넣는다.

## 도메인·계산기

```java
class TimeRangeTest {
    @Test
    void acceptsOrderedAndEmptyRangesAndRejectsReversedBounds() {
        LocalDateTime from = LocalDateTime.of(2026, 9, 1, 4, 0);
        LocalDateTime to = from.plusMinutes(10);

        assertThat(new TimeRange(from, from).to()).isEqualTo(from);
        assertThatThrownBy(() -> new TimeRange(to, from))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
```

## 도메인 예외는 errorCode로 검증

```java
assertThatThrownBy(() -> orderService.pay(orderId))
        .asInstanceOf(throwable(OrderException.class))
        .returns(ORDER_ALREADY_PAID, OrderException::errorCode);
```

## 협력 객체 경계의 Mock

```java
class OrderResetServiceTest {
    private final OrderResetRepository repository = mock(OrderResetRepository.class);
    private final OrderResetService service = new OrderResetService(repository);

    @Test
    void resetDeletesEveryRowOfTheRun() {
        when(repository.findRecentRuns(anyInt())).thenReturn(List.of(RUN));
        when(repository.deleteItems(anyLong())).thenReturn(1);

        OrderResetService.Deleted deleted = service.reset(RUN_CODE);

        assertThat(deleted.items()).isEqualTo(1);
        verify(repository).deleteItems(RUN.id());
    }
}
```

## Repository (`@DataJpaTest`)

Mock 대신 실제 DB(Testcontainers 등) 슬라이스로 쿼리와 영속성 동작을 확인한다.

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = Replace.NONE)
class OrderRepositoryTest {
    @Autowired
    private OrderRepository orderRepository;

    @Test
    void findByIdReturnsSavedOrder() {
        OrderEntity saved = orderRepository.save(new OrderEntity("P-1", 2));

        Optional<OrderSummary> found = orderRepository.findSummaryById(saved.getId());

        assertThat(found).map(OrderSummary::quantity).contains(2);
    }
}
```

## Controller (`@WebMvcTest`)

Bean Validation, 직렬화, 오류 응답 변환을 검증한다. Service는 `@MockitoBean`으로 격리한다(`@MockBean`은 Boot 3.4에서 deprecated).

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private OrderService orderService;

    @Test
    void reportsMissingOrderWithItsErrorCode() throws Exception {
        when(orderService.findById(1L)).thenThrow(new OrderException(ORDER_NOT_FOUND, 1L));

        mockMvc.perform(get("/api/v1/orders/{id}", 1L))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("ORDER_NOT_FOUND"));
    }
}
```
