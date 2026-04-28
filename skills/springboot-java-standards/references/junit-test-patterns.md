# JUnit 테스트 패턴 (JUnit Test Patterns)

Java Spring Boot 애플리케이션에서 테스트 품질을 높이고 유지보수성을 확보하기 위한 테스트 작성 가이드입니다.

## 핵심 원칙

- **리플렉션 금지**: `ReflectionTestUtils.setField()`와 같이 캡슐화를 깨뜨리는 리플렉션 사용을 자제합니다. 리팩토링 시 테스트가 깨지는 주 원인이 됩니다.
- **깊은 Mock 지양**: 모든 의존성을 Mocking하기보다는 상태 기반의 테스트(State-based target)나 통합 슬라이스 테스트 환경을 권장합니다.
- **부분 모킹(Partial Mocks) 지양**: 스파이(Spy) 사용은 객체의 역할이 불분명함을 의미할 수 있으므로 피합니다.

## 테스트 픽스처 (Test Fixtures)

식별자(ID)가 없어도 비즈니스 로직을 검증할 수 있도록 설계하고, 생성자나 빌더를 통해 안전하게 테스트용 픽스처(Fixture)를 생성하세요.

```java
// 좋은 예: 생성자나 팩토리 메서드를 활용해 유효한 객체 상태를 구성할 수 있어야 함
var user = User.builder().name("John").build();
user.activate(); // 도메인 로직 검증에 집중
```

## 계층별 테스트 전략

### 도메인(Entity) 테스트 (POJO)
- 도메인 단위의 핵심 비즈니스 로직(예: 상태 변경)을 검증합니다.
- 외부 프레임워크나 Mocking 없이 순수한 Java 객체(POJO)로 아주 빠르게 실행되어야 합니다.

### Repository 테스트 (`@DataJpaTest`)
- Mockito를 통한 쿼리 모킹 대신 실제 동작하는 DB(Testcontainers 등) 환경에서의 슬라이스 테스트를 강력히 권장합니다.
- 영속성 관리가 예상대로 동작하는지 확인합니다.

### Controller 테스트 (`@WebMvcTest`)
- Spring Security, Interceptor, DTO 유효성 검증(Bean Validation), 직렬화/역직렬화를 검증합니다.
- `MockMvc`를 활용하고, Service 계층의 비즈니스 로직은 `@MockBean`으로 격리합니다.

## (AS-IS) 레거시 Mock 지향 테스트 참고

아래는 제한적인 환경에서 여전히 사용되는 Mockito 기반의 단위 테스트입니다. 가급적 위 전략에 맞춰 리팩토링해 나가는 것을 권장합니다.

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository userRepository;

    @Mock
    private UserAssembler userAssembler;

    @InjectMocks
    private UserServiceImpl userService;

    @Test
    void createUser_success() {
        // given
        var request = CreateUserRequest.builder().name("John").build();
        var user = User.builder().name("John").build();
        var response = UserResponse.builder().id(1L).name("John").build();

        when(userAssembler.toEntity(any())).thenReturn(user);
        when(userRepository.save(any(User.class))).thenReturn(user);
        when(userAssembler.toResponse(any())).thenReturn(response);

        // when
        var result = userService.create(request);

        // then
        assertThat(result.getName()).isEqualTo("John");
        verify(userRepository).save(any(User.class));
    }
}
```
