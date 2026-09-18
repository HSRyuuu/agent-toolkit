# Spring Boot 3.x 패턴

## API 구현 워크플로우

새 REST API를 구축할 때 아래 순서를 따릅니다:

```
Entity → DTO → Repository → ErrorCode/Exception → Service → Controller → Test
```

### 요구사항 체크리스트

**필수 확인:**
- 리소스/엔티티명 (예: User, Product, Order)
- 필요한 작업 (GET, POST, PUT, DELETE, PATCH)
- 언어 선택 (Java / Kotlin)

**선택적 확인:**
- 엔티티 필드 및 관계
- 유효성 검사 규칙
- 페이지네이션 필요 여부
- 테스트 코드 생성 여부

---

## Controller

```java
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Validated
public class UserController {
    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(userService.findById(id));
    }

    @PostMapping
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody CreateUserRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(userService.create(request));
    }

    @PutMapping("/{id}")
    public ResponseEntity<UserResponse> updateUser(
            @PathVariable Long id,
            @Valid @RequestBody UpdateUserRequest request) {
        return ResponseEntity.ok(userService.update(id, request));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        userService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

## Service

구현이 하나면 구체 클래스 하나로 시작합니다. `XxxService` 인터페이스 + `XxxServiceImpl` 쌍은 실제로 구현이 둘 이상 생기거나 의존성 격리가 필요해질 때 도입합니다.

클래스 레벨 `@Transactional(readOnly = true)`, 쓰기 메서드만 `@Transactional`:

```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {
    private final UserRepository userRepository;

    public UserResponse findById(Long id) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new UserException(UserErrorCode.USER_NOT_FOUND, id));
        return UserResponse.from(user);
    }

    public List<UserResponse> findAll() {
        return userRepository.findAll().stream()
                .map(UserResponse::from)
                .toList();
    }

    @Transactional
    public UserResponse create(CreateUserRequest request) {
        User saved = userRepository.save(request.toEntity());
        return UserResponse.from(saved);
    }

    @Transactional
    public UserResponse update(Long id, UpdateUserRequest request) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new UserException(UserErrorCode.USER_NOT_FOUND, id));
        request.applyTo(user);
        return UserResponse.from(user);
    }

    @Transactional
    public void delete(Long id) {
        if (!userRepository.existsById(id)) {
            throw new UserException(UserErrorCode.USER_NOT_FOUND, id);
        }
        userRepository.deleteById(id);
    }
}
```

---

## DTO 패턴

고정 필드 DTO는 record가 기본입니다. 네이밍은 개별 탑레벨 타입(`CreateUserRequest`)과 기능 단위 묶음(`UserDto.Request`) 중 프로젝트가 이미 쓰는 쪽을 따릅니다.

### Request DTO

```java
public record CreateUserRequest(@NotBlank(message = "Name is required")
                                @Size(min = 2, max = 50) String name,

                                @NotBlank @Email String email,

                                @NotNull @Min(18) Integer age) {
    public User toEntity() {
        return User.builder()
                .name(name)
                .email(email)
                .age(age)
                .build();
    }
}
```

### Update DTO (Partial Update / PATCH)

null 체크로 부분 업데이트:

```java
public record UpdateUserRequest(String name,
                                Integer age) {
    public void applyTo(User user) {
        if (name != null) {
            user.updateName(name);
        }
        if (age != null) {
            user.updateAge(age);
        }
    }
}
```

### Response DTO

```java
public record UserResponse(Long id,
                           String name,
                           String email,
                           UserStatus status,
                           LocalDateTime createdAt) {
    public static UserResponse from(User user) {
        return new UserResponse(user.getId(), user.getName(), user.getEmail(),
                user.getStatus(), user.getCreatedAt());
    }
}
```

### 페이지네이션 Response

```java
public record PageResponse<T>(List<T> content,
                              int totalPages,
                              long totalElements,
                              int number,
                              int size) {
    public static <T, R> PageResponse<R> from(Page<T> page, Function<T, R> mapper) {
        List<R> content = page.getContent().stream()
                .map(mapper)
                .toList();
        return new PageResponse<>(content, page.getTotalPages(), page.getTotalElements(),
                page.getNumber(), page.getSize());
    }
}
```

### Mapper / Assembler (복잡한 변환 시)

기본은 DTO 내 `toEntity()`, `from()`입니다. 여러 소스를 합치거나 변환에 정책이 섞일 때만 별도 Mapper(또는 Assembler, MapStruct)를 분리합니다. 단순 위임만 하는 매핑 계층은 만들지 않습니다.

```java
@Component
@RequiredArgsConstructor
public class UserMapper {
    private final MembershipRepository membershipRepository;

    // 여러 소스를 합치므로 DTO 정적 팩터리로는 표현이 어렵다
    public UserDetailResponse toDetailResponse(User user) {
        Membership membership = membershipRepository.findActiveByUserId(user.getId())
                .orElse(Membership.none());
        return new UserDetailResponse(user.getId(), user.getName(), membership.grade());
    }
}
```

---

## 예외 처리 (Exception Handling)

같은 도메인의 오류는 **도메인 예외 하나 + `ErrorCode` enum**으로 모읍니다. 사례마다 예외 하위 클래스를 만들지 않습니다.

```java
// 에러 코드 계약 (name()은 enum이 자동 제공)
public interface ErrorCode {
    HttpStatus getStatus();
    String getMessage();
    String name();
}

@Getter
@RequiredArgsConstructor
public enum UserErrorCode implements ErrorCode {
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "User not found"),
    DUPLICATE_EMAIL(HttpStatus.CONFLICT, "Email already exists");

    private final HttpStatus status;
    private final String message;
}

// 도메인 예외 하나
@Getter
public class UserException extends RuntimeException {
    private final ErrorCode errorCode;

    public UserException(ErrorCode errorCode, Object detail) {
        super(errorCode.getMessage() + ": " + detail);
        this.errorCode = errorCode;
    }

    public UserException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }
}

// 글로벌 핸들러는 응답 변환만 담당
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(UserException.class)
    public ResponseEntity<ErrorResponse> handleDomain(UserException e) {
        ErrorCode errorCode = e.getErrorCode();
        log.warn("domain_error code={} message={}", errorCode.name(), e.getMessage());
        return ResponseEntity.status(errorCode.getStatus())
                .body(ErrorResponse.of(errorCode, e.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(
            MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getAllErrors().stream()
                .map(DefaultMessageSourceResolvable::getDefaultMessage)
                .collect(Collectors.joining(", "));
        return ResponseEntity.badRequest()
                .body(new ErrorResponse("INVALID_REQUEST", message, LocalDateTime.now()));
    }
}

// 에러 응답 DTO
public record ErrorResponse(String code,
                            String message,
                            LocalDateTime timestamp) {
    public static ErrorResponse of(ErrorCode errorCode, String message) {
        return new ErrorResponse(errorCode.name(), message, LocalDateTime.now());
    }
}
```

- HTTP 상태와 기본 문구는 `ErrorCode` 한 곳에만 둡니다.
- 응답의 `code` 값이 외부 계약이면 enum 상수 이름 변경도 계약 변경입니다.
- 프로그래밍 오류(`IllegalArgumentException`, `IllegalStateException` 등)는 표준 예외를 유지합니다.

---

## 레이어별 테스트

### Controller 테스트

```java
@WebMvcTest(UserController.class)
class UserControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("GET /users/{id} returns 200")
    void getUser_success() throws Exception {
        Long userId = 1L;
        UserResponse response = new UserResponse(userId, "John", "john@test.com",
                UserStatus.ACTIVE, LocalDateTime.now());

        when(userService.findById(userId)).thenReturn(response);

        mockMvc.perform(get("/api/v1/users/{id}", userId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(userId))
                .andExpect(jsonPath("$.name").value("John"));
    }

    @Test
    @DisplayName("POST /users returns 201")
    void createUser_success() throws Exception {
        CreateUserRequest request = new CreateUserRequest("John", "john@test.com", 25);
        UserResponse response = new UserResponse(1L, "John", "john@test.com",
                UserStatus.ACTIVE, LocalDateTime.now());

        when(userService.create(any())).thenReturn(response);

        mockMvc.perform(post("/api/v1/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(1L));
    }
}
```

### Service 테스트

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    @DisplayName("findById throws when not found")
    void findById_notFound() {
        when(userRepository.findById(1L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> userService.findById(1L))
                .isInstanceOf(UserException.class)
                .extracting("errorCode")
                .isEqualTo(UserErrorCode.USER_NOT_FOUND);
    }

    @Test
    @DisplayName("create saves and returns response")
    void create_success() {
        CreateUserRequest request = new CreateUserRequest("John", "john@test.com", 25);
        User savedUser = User.builder()
                .name("John").email("john@test.com").age(25).build();

        when(userRepository.save(any(User.class))).thenReturn(savedUser);

        UserResponse response = userService.create(request);

        assertThat(response.name()).isEqualTo("John");
        assertThat(response.email()).isEqualTo("john@test.com");
        verify(userRepository).save(any(User.class));
    }
}
```

생성된 ID처럼 영속화 이후에만 존재하는 값은 `ReflectionTestUtils`로 주입하지 말고 `@DataJpaTest`에서 실제 저장 후 확인합니다.

### Repository 테스트

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = Replace.NONE)
class UserRepositoryTest {
    @Autowired
    private UserRepository userRepository;

    @Test
    @DisplayName("findByEmail returns user")
    void findByEmail_success() {
        User user = User.builder()
                .name("John").email("john@test.com").age(25).build();
        userRepository.save(user);

        Optional<User> found = userRepository.findByEmail("john@test.com");

        assertThat(found).isPresent();
        assertThat(found.get().getName()).isEqualTo("John");
    }
}
```
