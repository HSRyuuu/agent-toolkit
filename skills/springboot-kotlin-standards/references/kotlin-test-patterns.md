# Kotlin 테스트 패턴 (Kotlin Test Patterns)

Kotlin Spring Boot 애플리케이션에서 테스트 품질을 높이고 유지보수성을 확보하기 위한 테스트 작성 가이드입니다.

## 핵심 원칙

- **리플렉션 금지**: `ReflectionTestUtils.setField()` 사용을 자제합니다. Entity 생성자에서 모든 필드를 설정할 수 있도록 설계합니다.
- **깊은 Mock 지양**: 상태 기반 테스트를 우선하고, 슬라이스 테스트 환경을 권장합니다.
- **한글 테스트 이름**: 백틱(`` ` ``)을 활용하여 한글로 테스트 의도를 명확히 표현합니다.

---

## Service 단위 테스트

```kotlin
@ExtendWith(MockitoExtension::class)
class UserServiceTest {

    @Mock
    private lateinit var appUserRepository: AppUserRepository

    @InjectMocks
    private lateinit var userService: UserService

    private val testUserId = UUID.randomUUID()
    private val testUser = AppUser(
        id = testUserId,
        email = "test@example.com",
        nickname = "테스터",
        password = "encodedPassword",
        personaType = PersonaType.ENGINEERING,
        createdAt = LocalDateTime.of(2024, 1, 15, 10, 30),
    )

    @Test
    fun `내정보조회_성공`() {
        // given
        whenever(appUserRepository.findById(testUserId))
            .thenReturn(Optional.of(testUser))

        // when
        val result = userService.getMyInfo(testUserId)

        // then
        assertEquals(testUserId, result.id)
        assertEquals("test@example.com", result.email)
        assertEquals("테스터", result.nickname)
    }

    @Test
    fun `내정보조회_사용자없음_실패`() {
        // given
        val unknownId = UUID.randomUUID()
        whenever(appUserRepository.findById(unknownId))
            .thenReturn(Optional.empty())

        // when & then
        val exception = assertThrows<GlobalException> {
            userService.getMyInfo(unknownId)
        }
        assertEquals(ErrorCode.USER_NOT_FOUND, exception.errorCode)
    }
}
```

### @Nested로 테스트 그룹화

```kotlin
@ExtendWith(MockitoExtension::class)
class AuthServiceTest {

    @Mock private lateinit var appUserRepository: AppUserRepository
    @Mock private lateinit var passwordEncoder: PasswordEncoder
    @Mock private lateinit var jwtTokenProvider: JwtTokenProvider

    @InjectMocks
    private lateinit var authService: AuthService

    @Nested
    inner class Signup {
        @Test
        fun `signup_성공`() {
            // given
            val request = SignupRequest(
                email = "new@example.com",
                password = "password123",
                nickname = "신규유저",
                personaType = PersonaType.ENGINEERING,
            )
            whenever(appUserRepository.existsByEmail(request.email))
                .thenReturn(false)
            whenever(passwordEncoder.encode(request.password))
                .thenReturn("encodedPassword")
            whenever(appUserRepository.save(any()))
                .thenAnswer { it.arguments[0] as AppUser }

            // when
            val result = authService.signup(request)

            // then
            assertEquals("new@example.com", result.email)
            verify(appUserRepository).save(any())
        }

        @Test
        fun `signup_이메일중복_실패`() {
            // given
            val request = SignupRequest(
                email = "existing@example.com",
                password = "password123",
                nickname = "유저",
                personaType = PersonaType.ENGINEERING,
            )
            whenever(appUserRepository.existsByEmail(request.email))
                .thenReturn(true)

            // when & then
            val exception = assertThrows<GlobalException> {
                authService.signup(request)
            }
            assertEquals(ErrorCode.DUPLICATE_EMAIL, exception.errorCode)
        }
    }

    @Nested
    inner class Login {
        @Test
        fun `login_성공`() { /* ... */ }

        @Test
        fun `login_비밀번호불일치_실패`() { /* ... */ }
    }
}
```

---

## Controller 테스트

```kotlin
@WebMvcTest(UserController::class)
@AutoConfigureMockMvc(addFilters = false)
@DisplayName("UserController 테스트")
class UserControllerTest {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @Autowired
    private lateinit var objectMapper: ObjectMapper

    @MockBean  // Spring Boot 3.4+에서는 @MockitoBean으로 대체
    private lateinit var userService: UserService

    private val testUserId = UUID.randomUUID()

    @BeforeEach
    fun setUp() {
        // SecurityContext에 인증 정보 설정
        val principal = UserPrincipal(
            id = testUserId,
            email = "test@example.com",
            password = "",
            role = UserRole.ROLE_USER,
        )
        val auth = UsernamePasswordAuthenticationToken(
            principal, null, principal.authorities
        )
        SecurityContextHolder.getContext().authentication = auth
    }

    @Test
    fun `내정보조회_성공_200`() {
        // given
        val response = MyInfoResponse(
            id = testUserId,
            email = "test@example.com",
            nickname = "테스터",
            personaType = PersonaType.ENGINEERING,
            createdAt = LocalDateTime.of(2024, 1, 15, 10, 30),
        )
        whenever(userService.getMyInfo(testUserId)).thenReturn(response)

        // when & then
        mockMvc.perform(get("/api/users/me"))
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.id").value(testUserId.toString()))
            .andExpect(jsonPath("$.email").value("test@example.com"))
            .andExpect(jsonPath("$.nickname").value("테스터"))
    }

    @Test
    fun `닉네임변경_성공_200`() {
        // given
        val request = NicknameUpdateRequest(nickname = "새닉네임")
        val response = MyInfoResponse(/* ... */)
        whenever(userService.updateNickname(eq(testUserId), any()))
            .thenReturn(response)

        // when & then
        mockMvc.perform(
            patch("/api/users/me/nickname")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request))
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.nickname").value("새닉네임"))
    }
}
```

---

## 배치/스케줄러 테스트

```kotlin
@ExtendWith(MockitoExtension::class)
class DiaryTopicCleanupBatchTest {

    @Mock
    private lateinit var diaryAnalysisReportRepository: DiaryAnalysisReportRepository

    @InjectMocks
    private lateinit var batch: DiaryTopicCleanupBatch

    @Test
    fun `오래된_분석보고서_정리_성공`() {
        // given
        val oldReports = listOf(
            DiaryAnalysisReport(
                diary = mockDiary(),
                status = AnalysisStatus.COMPLETED,
                createdAt = LocalDateTime.now().minusDays(90),
            )
        )
        whenever(diaryAnalysisReportRepository.findOlderThan(any()))
            .thenReturn(oldReports)

        // when
        batch.cleanupOldTopics()

        // then
        verify(diaryAnalysisReportRepository).deleteAll(oldReports)
    }
}
```

---

## 테스트 작성 원칙

### 구조

- **Given-When-Then** 패턴 준수 (주석으로 명시)
- 한 테스트에 하나의 검증 포인트
- 테스트 데이터는 테스트 클래스 필드 또는 메서드 내 지역 변수로 준비

### 명명 규칙

- 백틱(`` ` ``)으로 한글 테스트 이름: `` `내정보조회_성공` ``
- 패턴: `{행위}_{조건}_{결과}` 또는 `{행위}_{결과}`
- Controller 테스트: 상태 코드 포함 `` `내정보조회_성공_200` ``

### 계층별 테스트 전략

| 계층 | 어노테이션 | Mock 대상 | 검증 포인트 |
|------|-----------|-----------|------------|
| Service | `@ExtendWith(MockitoExtension::class)` | Repository, 외부 서비스 | 비즈니스 로직, 예외 처리 |
| Controller | `@WebMvcTest` | Service | HTTP 상태, 응답 JSON, 유효성 검증 |
| Repository | `@DataJpaTest` | 없음 (실제 DB) | 쿼리 정확성, 페이지네이션 |
| Batch | `@ExtendWith(MockitoExtension::class)` | Repository | 배치 실행 결과, 에러 처리 |

### 라이브러리

- **mockito-kotlin**: `whenever`, `any()`, `eq()`, `verify()` 등 Kotlin 친화적 API
- **JUnit 5**: `@Test`, `@Nested`, `@BeforeEach`, `@DisplayName`
- **AssertJ / JUnit Assertions**: `assertEquals`, `assertThrows<T>`

### 테스트 픽스처

```kotlin
// 생성자에서 모든 필드를 설정할 수 있도록 Entity를 설계
private val testUser = AppUser(
    id = UUID.randomUUID(),
    email = "test@example.com",
    nickname = "테스터",
    password = "encodedPassword",
    personaType = PersonaType.ENGINEERING,
    createdAt = LocalDateTime.of(2024, 1, 15, 10, 30),
)

// ReflectionTestUtils 대신 생성자 활용
// Bad: ReflectionTestUtils.setField(user, "id", testUserId)
// Good: AppUser(id = testUserId, ...)
```

### mockito-kotlin 사용법

```kotlin
// 의존성
testImplementation("org.mockito.kotlin:mockito-kotlin:5.4.0")

// whenever (= Mockito.when)
whenever(repository.findById(any())).thenReturn(Optional.of(entity))

// any(), eq(): 타입 안전한 매처
whenever(service.update(eq(userId), any())).thenReturn(response)

// verify: 호출 검증
verify(repository).save(any())
verify(repository, times(1)).deleteById(any())

// thenAnswer: 동적 응답
whenever(repository.save(any())).thenAnswer { it.arguments[0] as AppUser }
```

### Controller 테스트 보안 설정

```kotlin
// Security Filter 비활성화
@AutoConfigureMockMvc(addFilters = false)

// 또는 SecurityContext 직접 설정
@BeforeEach
fun setUp() {
    val principal = UserPrincipal(
        id = testUserId,
        email = "test@example.com",
        password = "",
        role = UserRole.ROLE_USER,
    )
    val auth = UsernamePasswordAuthenticationToken(
        principal, null, principal.authorities
    )
    SecurityContextHolder.getContext().authentication = auth
}
```
