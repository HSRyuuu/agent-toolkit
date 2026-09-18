# JPA & QueryDSL 패턴

## Entity 패턴

### 기본 Entity + JPA Auditing

```java
@Entity
@Table(name = "users")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@EntityListeners(AuditingEntityListener.class)
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50)
    private String name;

    @Column(nullable = false, unique = true, length = 100)
    private String email;

    @Column(nullable = false)
    private Integer age;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private UserStatus status;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @Builder
    public User(String name, String email, Integer age) {
        this.name = name;
        this.email = email;
        this.age = age;
        this.status = UserStatus.ACTIVE;
    }

    // 비즈니스 메서드로 상태 변경 (setter 대신)
    public void update(String name, Integer age) {
        this.name = name;
        this.age = age;
    }

    public void updateName(String name) {
        this.name = name;
    }

    public void updateAge(Integer age) {
        this.age = age;
    }
}
```

### Entity 설계 원칙

- `@NoArgsConstructor(access = AccessLevel.PROTECTED)`: JPA 프록시 생성용, 외부 직접 생성 방지
- `@Builder`는 의미 있는 생성자에 적용 (클래스 레벨 아닌 생성자 레벨)
- setter 대신 비즈니스 의미를 가진 메서드로 상태 변경
- Enum은 `@Enumerated(EnumType.STRING)` 사용 (ORDINAL은 순서 변경 시 위험)
- Auditing: `@EnableJpaAuditing` 설정 필요

---

## Repository 패턴

```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    List<User> findAllByStatus(UserStatus status);
    boolean existsByEmail(String email);

    @Query("SELECT u FROM User u WHERE u.createdAt >= :date")
    List<User> findRecentUsers(@Param("date") LocalDateTime date);
}
```

### Repository 작성 원칙

- Spring Data JPA 메서드 네이밍 컨벤션을 활용합니다.
- 복잡한 쿼리는 `@Query`로 JPQL을 작성합니다.
- 동적 조건이 필요하면 QueryDSL을 사용합니다 (아래 참조).

---

## QueryDSL 패턴

동적 쿼리가 필요한 경우 타입 안전한 QueryDSL을 사용합니다.

### Custom Repository 구현

```java
// 인터페이스
public interface UserRepositoryCustom {
    Page<User> findByConditions(String name, UserStatus status,
                                LocalDateTime createdAfter, Pageable pageable);
}

// 구현
@Repository
@RequiredArgsConstructor
public class UserRepositoryCustomImpl implements UserRepositoryCustom {

    private final JPAQueryFactory queryFactory;

    public Page<User> findByConditions(
            String name,
            UserStatus status,
            LocalDateTime createdAfter,
            Pageable pageable) {

        QUser user = QUser.user;
        BooleanBuilder builder = new BooleanBuilder();

        if (name != null) {
            builder.and(user.name.eq(name));
        }
        if (status != null) {
            builder.and(user.status.eq(status));
        }
        if (createdAfter != null) {
            builder.and(user.createdAt.goe(createdAfter));
        }

        List<User> content = queryFactory
                .selectFrom(user)
                .where(builder)
                .offset(pageable.getOffset())
                .limit(pageable.getPageSize())
                .fetch();

        Long total = queryFactory
                .select(user.count())
                .from(user)
                .where(builder)
                .fetchOne();

        return new PageImpl<>(content, pageable, total != null ? total : 0L);
    }
}
```

### Repository 통합

```java
public interface UserRepository extends JpaRepository<User, Long>, UserRepositoryCustom {
    // Spring Data 메서드 + QueryDSL 커스텀 메서드 모두 사용 가능
}
```

### QueryDSL 설정 (build.gradle.kts)

```kotlin
dependencies {
    implementation("com.querydsl:querydsl-jpa:5.0.0:jakarta")
    annotationProcessor("com.querydsl:querydsl-apt:5.0.0:jakarta")
    annotationProcessor("jakarta.persistence:jakarta.persistence-api")
}
```

---

## 쿼리 실행과 변환

- `fetchFirst()`·`fetchOne()`·`fetch()`까지 **실행한 결과를 지역변수로 받은 뒤** Optional 변환·매핑·방어 복사를 합니다. 쿼리 객체만 떼어 내고 실행과 변환을 다시 중첩하지 않습니다.
- Repository에 `toModel`/`toDto` 필드 매핑을 남기지 않습니다. 변환은 DTO의 정적 팩터리 또는 생성자 projection이 담당합니다.
- 여러 소스를 합친 조회는 생성자 projection이나 필요한 필드만의 projection을 씁니다. DTO 생성자를 쓸 수 있으면 Tuple 해체용 공통 helper를 만들지 않습니다. projection 결과를 그대로 반환할 때는 불필요한 중간변수를 만들지 않습니다.
- update/delete는 clause를 지역변수로 구성한 뒤 실행합니다. bulk 쿼리의 flush/clear와 트랜잭션 경계를 보존하고, 모양을 맞추려고 execute helper를 새로 만들지 않습니다.

```java
User user = queryFactory
        .selectFrom(qUser)
        .where(qUser.email.eq(email))
        .fetchFirst();
return Optional.ofNullable(user).map(UserResponse::from);
```

```java
// 생성자 projection: 매핑 helper 없이 바로 DTO로 받는다
List<UserSummary> summaries = queryFactory
        .select(Projections.constructor(UserSummary.class,
                qUser.id, qUser.name, qOrder.count()))
        .from(qUser)
        .leftJoin(qOrder).on(qOrder.userId.eq(qUser.id))
        .groupBy(qUser.id, qUser.name)
        .fetch();
```

```java
// bulk 변경: clause를 구성한 뒤 실행하고, 영속성 컨텍스트를 정리한다
JPAUpdateClause update = queryFactory.update(qUser)
        .set(qUser.status, UserStatus.INACTIVE)
        .where(qUser.lastLoginAt.lt(threshold));
long updated = update.execute();

entityManager.flush();
entityManager.clear();
```

---

## 긴 SQL 분리

긴 SQL이 로직을 가리면 같은 패키지의 `<사용클래스>Sql`로 옮깁니다. package-private final class, `static final String`, private 생성자를 씁니다. 쿼리 자체가 역할인 reader나 짧은 SQL 하나는 그대로 두어도 됩니다.

```java
final class UserReportSql {
    static final String MONTHLY_SUMMARY = """
            SELECT u.id, u.name, COUNT(o.id) AS order_count
              FROM users u
              LEFT JOIN orders o ON o.user_id = u.id
             WHERE o.created_at >= :from AND o.created_at < :to
             GROUP BY u.id, u.name
            """;

    private UserReportSql() {
    }
}
```

---

## JDBC 사용 기준

- JPA/QueryDSL이 기본입니다. JDBC는 실제 bulk insert/upsert 또는 ORM으로 표현하기 어려운 쿼리에만 씁니다.
- 조회 전체를 JDBC로 바꾸거나 공통 repository 프레임워크를 새로 만들지 않습니다.
- JDBC로 bulk 변경을 하면 영속성 컨텍스트의 flush/clear와 통합 트랜잭션 경계를 유지합니다.
