# JPA & QueryDSL 패턴 예시

규칙은 `SKILL.md`의 Repository와 SQL 절에 있다. 이 파일은 적용한 모양만 보여준다.

## Entity

```java
@Entity
@Table(name = "orders")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class OrderEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50)
    private String productCode;

    @Column(nullable = false)
    private Integer quantity;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private OrderStatus status;

    @Builder
    public OrderEntity(String productCode, Integer quantity) {
        this.productCode = productCode;
        this.quantity = quantity;
        this.status = OrderStatus.CREATED;
    }

    // setter 대신 의도가 드러나는 상태 변경
    public void pay() {
        this.status = OrderStatus.PAID;
    }

    public boolean isPaid() {
        return this.status == OrderStatus.PAID;
    }
}
```

## 조회: 실행 결과를 받은 뒤 변환

```java
public Optional<OrderSummary> findById(long id) {
    OrderEntity entity = queryFactory
            .selectFrom(orderEntity)
            .where(orderEntity.id.eq(id))
            .fetchFirst();
    return Optional.ofNullable(entity).map(OrderSummary::fromEntity);
}

public Set<Long> findUserIdsByProductCodeAndOrderedRange(String productCode, TimeRange orderedRange) {
    List<Long> userIds = queryFactory
            .select(orderEntity.userId).distinct()
            .from(orderEntity)
            .where(orderEntity.productCode.eq(productCode),
                    orderEntity.orderedAt.goe(orderedRange.from()),
                    orderEntity.orderedAt.lt(orderedRange.to()))
            .fetch();
    return Set.copyOf(userIds);
}

// Bad: 실행과 변환이 한 식에 중첩된다
return Optional.ofNullable(queryFactory
                .selectFrom(orderEntity)
                .where(orderEntity.id.eq(id))
                .fetchFirst())
        .map(OrderRepository::toModel);
```

## 생성자 projection

```java
// 매핑 helper 없이 바로 DTO로 받는다
List<UserOrderCount> counts = queryFactory
        .select(Projections.constructor(UserOrderCount.class,
                userEntity.id, userEntity.name, orderEntity.count()))
        .from(userEntity)
        .leftJoin(orderEntity).on(orderEntity.userId.eq(userEntity.id))
        .groupBy(userEntity.id, userEntity.name)
        .fetch();
```

## 동적 조건

```java
public List<OrderEntity> findByConditions(String productCode, OrderStatus status) {
    BooleanBuilder condition = new BooleanBuilder();
    if (productCode != null) {
        condition.and(orderEntity.productCode.eq(productCode));
    }
    if (status != null) {
        condition.and(orderEntity.status.eq(status));
    }

    return queryFactory
            .selectFrom(orderEntity)
            .where(condition)
            .fetch();
}
```

## 변경: clause를 구성한 뒤 실행

```java
@Transactional
public boolean markPaidIfCreated(long id) {
    BooleanExpression predicate = orderEntity.id.eq(id)
            .and(orderEntity.status.eq(OrderStatus.CREATED));
    JPAUpdateClause query = queryFactory.update(orderEntity)
            .set(orderEntity.status, OrderStatus.PAID)
            .where(predicate);
    return this.execute(query) == 1;
}

/**
 * bulk update는 영속성 컨텍스트를 건너뛴다. 먼저 flush해서 대기 중인 변경을 반영하고,
 * 실행 뒤 clear해서 오래된 엔티티를 읽지 않게 한다.
 */
private long execute(JPAUpdateClause query) {
    entityManager.flush();
    long affected = query.execute();
    entityManager.clear();
    return affected;
}
```

## 긴 SQL 분리

```java
final class OrderReportRepositorySql {
    static final String MONTHLY_SUMMARY = """
            SELECT u.id, u.name, COUNT(o.id) AS order_count
              FROM users u
              LEFT JOIN orders o ON o.user_id = u.id
             WHERE o.created_at >= :from AND o.created_at < :to
             GROUP BY u.id, u.name
            """;

    private OrderReportRepositorySql() {
    }
}
```
