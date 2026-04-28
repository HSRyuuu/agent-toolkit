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
