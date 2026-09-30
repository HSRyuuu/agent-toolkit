# Spring Boot 3.x 패턴 (Kotlin)

## API 구현 워크플로우

새 REST API를 구축할 때 아래 순서를 따릅니다:

```
Entity → DTO → Repository → Exception → Service → Controller → Test
```

### 요구사항 체크리스트

**필수 확인:**
- 리소스/엔티티명 (예: Article, User, Notification)
- 필요한 작업 (GET, POST, PUT, DELETE, PATCH)

**선택적 확인:**
- 엔티티 필드 및 관계
- 유효성 검사 규칙
- 페이지네이션 필요 여부
- 이벤트 발행 여부
- 테스트 코드 생성 여부

---

## Controller

```kotlin
@Tag(name = "Article Comment", description = "아티클 댓글 API")
@RestController
@RequestMapping("/api/articles/{articleId}/comments")
class ArticleCommentController(
    private val articleCommentService: ArticleCommentService,
) {
    @Operation(summary = "댓글 목록 조회")
    @GetMapping
    fun getComments(
        @CurrentUserId(required = false) userId: UUID?,
        @PathVariable articleId: UUID,
    ): ResponseEntity<List<CommentResponse>> {
        return ResponseEntity.ok(articleCommentService.getComments(articleId, userId))
    }

    @Operation(summary = "댓글 작성")
    @PostMapping
    fun createComment(
        @CurrentUserId userId: UUID,
        @PathVariable articleId: UUID,
        @Valid @RequestBody request: CommentCreateRequest,
    ): ResponseEntity<CommentResponse> {
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(articleCommentService.createComment(userId, articleId, request))
    }

    @Operation(summary = "댓글 수정")
    @PutMapping("/{commentId}")
    fun updateComment(
        @CurrentUserId userId: UUID,
        @PathVariable articleId: UUID,
        @PathVariable commentId: UUID,
        @Valid @RequestBody request: CommentUpdateRequest,
    ): ResponseEntity<CommentResponse> {
        return ResponseEntity.ok(
            articleCommentService.updateComment(userId, articleId, commentId, request)
        )
    }

    @Operation(summary = "댓글 삭제")
    @DeleteMapping("/{commentId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    fun deleteComment(
        @CurrentUserId userId: UUID,
        @PathVariable articleId: UUID,
        @PathVariable commentId: UUID,
    ) {
        articleCommentService.deleteComment(userId, articleId, commentId)
    }
}
```

### Controller 작성 원칙

- `@Tag`, `@Operation`으로 Swagger 문서화
- `@CurrentUserId` 커스텀 어노테이션으로 인증 사용자 추출
- `@Valid`로 Request Body 유효성 검증
- POST → `HttpStatus.CREATED` (201)
- DELETE → `HttpStatus.NO_CONTENT` (204)
- 컨트롤러 당 하나의 서비스 주입을 권장
- 생성자 주입 (Kotlin 주생성자)

---

## Service

클래스 레벨 `@Transactional(readOnly = true)`, 쓰기 메서드만 `@Transactional`:

```kotlin
@Service
@Transactional(readOnly = true)
class ArticleCommentService(
    private val articleCommentRepository: ArticleCommentRepository,
    private val articleRepository: ArticleRepository,
    private val appUserRepository: AppUserRepository,
    private val eventPublisher: ApplicationEventPublisher,
) {
    fun getComments(articleId: UUID, currentUserId: UUID?): List<CommentResponse> {
        val rootComments = articleCommentRepository
            .findRootCommentsByArticleId(articleId)
        if (rootComments.isEmpty()) return emptyList()

        val rootIds = rootComments.mapNotNull { it.id }
        val repliesMap = articleCommentRepository
            .findRepliesByParentIds(rootIds)
            .groupBy { it.parent?.id }

        return rootComments.map { root ->
            val replies = repliesMap[root.id]
                ?.map { CommentResponse.from(it, currentUserId) }
                ?: emptyList()
            CommentResponse.from(root, currentUserId, replies)
        }
    }

    @Transactional
    fun createComment(
        userId: UUID,
        articleId: UUID,
        request: CommentCreateRequest,
    ): CommentResponse {
        val article = articleRepository.findByIdOrNull(articleId)
            ?: throw GlobalException(ErrorCode.ARTICLE_NOT_FOUND)
        val user = appUserRepository.getReferenceById(userId)

        val comment = articleCommentRepository.save(
            ArticleComment(
                article = article,
                author = user,
                content = request.content,
            )
        )

        articleRepository.updateCommentCount(articleId, 1)

        // 이벤트 발행 (알림 등 부수 효과)
        if (article.author.id != userId) {
            eventPublisher.publishEvent(
                CommentCreatedEvent(
                    articleId = articleId,
                    articleTitle = article.title,
                    articleAuthorId = article.author.id!!,
                    commentAuthorNickname = user.nickname,
                )
            )
        }

        return CommentResponse.from(comment, userId)
    }

    @Transactional
    fun deleteComment(userId: UUID, articleId: UUID, commentId: UUID) {
        val comment = articleCommentRepository.findByIdOrNull(commentId)
            ?: throw GlobalException(ErrorCode.INVALID_REQUEST)
        if (comment.author?.id != userId) {
            throw GlobalException(ErrorCode.FORBIDDEN)
        }
        articleCommentRepository.delete(comment)
        articleRepository.updateCommentCount(articleId, -1)
    }
}
```

### Service 작성 원칙

- 클래스 레벨 `@Transactional(readOnly = true)` → 읽기 최적화
- 쓰기 메서드만 `@Transactional` 개별 선언
- `getReferenceById()`: 즉시 조회가 불필요한 연관관계 설정 시 사용 (프록시만 반환)
- `findByIdOrNull() ?: throw`: 엔티티가 반드시 존재해야 할 때 (Spring Data의 Kotlin 확장 함수, `Optional` 대신 nullable 반환)
- 이벤트 발행으로 부수 효과를 분리 (알림, 로깅 등)
- Kotlin 컬렉션 함수 적극 활용 (`mapNotNull`, `groupBy`, `map`)

---

## DTO 패턴

### Request DTO

```kotlin
data class ArticleCreateRequest(
    @field:NotBlank(message = "제목은 필수입니다.")
    @field:Size(max = 300, message = "제목은 최대 300자입니다.")
    val title: String,

    @field:NotBlank(message = "내용은 필수입니다.")
    val content: String,

    val keywordNames: List<String> = emptyList(),
    val sourceAiDocumentId: UUID? = null,
)

data class CommentCreateRequest(
    @field:NotBlank(message = "내용은 필수입니다.")
    val content: String,
    val parentId: UUID? = null,
)
```

### Response DTO

```kotlin
data class ArticleDetailResponse(
    val id: UUID,
    val title: String,
    val content: String,
    val authorNickname: String,
    val status: ArticleStatus,
    val viewCount: Long,
    val likeCount: Long,
    val liked: Boolean,
    val bookmarked: Boolean,
    val keywords: List<String>,
    val publishedAt: LocalDateTime?,
    val createdAt: LocalDateTime,
)

data class CommentResponse(
    val id: UUID,
    val authorNickname: String?,
    val content: String,
    val createdAt: LocalDateTime,
    val isEdited: Boolean,
    val isMine: Boolean,
    val replies: List<CommentResponse>,
) {
    companion object {
        fun from(
            comment: ArticleComment,
            currentUserId: UUID?,
            replies: List<CommentResponse> = emptyList(),
        ): CommentResponse {
            return CommentResponse(
                id = comment.id!!,
                authorNickname = comment.author?.nickname,
                content = comment.content,
                createdAt = comment.createdAt,
                isEdited = comment.createdAt != comment.updatedAt,
                isMine = currentUserId != null
                    && comment.author?.id == currentUserId,
                replies = replies,
            )
        }
    }
}
```

### DTO 작성 원칙

- data class + `val` 프로퍼티로 불변 보장
- Request DTO: `@field:` 접두사로 Bean Validation 어노테이션 적용
- Response DTO: `companion object { fun from() }` 팩토리 메서드로 Entity → DTO 변환
- Boolean 프로퍼티: `is` 접두사 사용 (`isEdited`, `isMine`, `isRead`)
- 선택적 필드: 기본값 활용 (`val keywordNames: List<String> = emptyList()`)
- 후행 콤마(trailing comma) 사용

### 페이지네이션 Response

```kotlin
data class CommonPageResponse<T>(
    val total: Long = 0L,
    val currentPage: Int = 0,
    val pageSize: Int = 0,
    val totalPages: Int = 0,
    val list: List<T> = emptyList(),
) {
    constructor(page: Page<T>) : this(
        total = page.totalElements,
        currentPage = page.number,
        pageSize = page.size,
        totalPages = page.totalPages,
        list = page.content,
    )

    companion object {
        fun <T, R> from(page: Page<T>, mapper: (T) -> R): CommonPageResponse<R> {
            return CommonPageResponse(
                total = page.totalElements,
                currentPage = page.number,
                pageSize = page.size,
                totalPages = page.totalPages,
                list = page.content.map(mapper),
            )
        }
    }
}
```

### 공통 처리 결과 DTO

```kotlin
data class ProcessResult<T>(
    val result: OperationResult,
    val data: T? = null,
    val message: String? = null,
) {
    companion object {
        fun <T> success(data: T? = null, message: String? = null) =
            ProcessResult(result = OperationResult.SUCCESS, data = data, message = message)

        fun <T> error(message: String? = null, data: T? = null) =
            ProcessResult(result = OperationResult.ERROR, data = data, message = message)
    }
}
```

---

## 예외 처리 (Exception Handling)

### ErrorCode + GlobalException

```kotlin
enum class ErrorCode(val status: HttpStatus, val message: String) {
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "사용자를 찾을 수 없습니다"),
    ARTICLE_NOT_FOUND(HttpStatus.NOT_FOUND, "아티클을 찾을 수 없습니다"),
    UNAUTHORIZED(HttpStatus.UNAUTHORIZED, "인증이 필요합니다"),
    FORBIDDEN(HttpStatus.FORBIDDEN, "접근 권한이 없습니다"),
    INVALID_REQUEST(HttpStatus.BAD_REQUEST, "요청 값이 올바르지 않습니다"),
    DUPLICATE_EMAIL(HttpStatus.CONFLICT, "이미 사용 중인 이메일입니다"),
}

class GlobalException(
    val errorCode: ErrorCode,
    override val cause: Throwable? = null,
    val data: Any? = null,
) : RuntimeException(errorCode.message, cause)
```

### GlobalExceptionHandler (ProblemDetail 활용)

```kotlin
@RestControllerAdvice
class GlobalExceptionHandler {

    private val log = LoggerFactory.getLogger(javaClass)

    @ExceptionHandler(GlobalException::class)
    fun handleGlobalException(
        ex: GlobalException,
        request: HttpServletRequest,
    ): ProblemDetail {
        val ec = ex.errorCode
        log.error("Error: {}", ec.message, ex)

        return ProblemDetail.forStatusAndDetail(ec.status, ec.message).apply {
            type = URI.create("https://example.app/problems/${ec.name.lowercase()}")
            title = ec.name
            instance = URI.create(request.requestURI)
            setProperty("code", ec.name)
            if (ex.data != null) {
                setProperty("data", ex.data)
            }
        }
    }

    @ExceptionHandler(MethodArgumentNotValidException::class)
    fun handleValidationException(
        ex: MethodArgumentNotValidException,
        request: HttpServletRequest,
    ): ProblemDetail {
        val errors = ex.bindingResult.fieldErrors.map {
            mapOf("field" to it.field, "message" to (it.defaultMessage ?: "Invalid value"))
        }
        log.error("Validation error: {}", errors, ex)

        return ProblemDetail.forStatusAndDetail(
            ErrorCode.INVALID_REQUEST.status,
            ErrorCode.INVALID_REQUEST.message,
        ).apply {
            type = URI.create("https://example.app/problems/validation-error")
            title = "Validation failed"
            instance = URI.create(request.requestURI)
            setProperty("code", ErrorCode.INVALID_REQUEST.name)
            setProperty("errors", errors)
        }
    }

    @ExceptionHandler(Exception::class)
    fun handleUnknownException(
        ex: Exception,
        request: HttpServletRequest,
    ): ProblemDetail {
        log.error("Unexpected error: {}", ex.message, ex)
        return ProblemDetail.forStatusAndDetail(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "서버 오류가 발생했습니다.",
        ).apply {
            type = URI.create("https://example.app/problems/internal-server-error")
            title = "INTERNAL_SERVER_ERROR"
            instance = URI.create(request.requestURI)
        }
    }
}
```

### 예외 처리 원칙

- `ProblemDetail` (RFC 7807) 표준 사용
- 중앙화된 `ErrorCode` enum으로 에러 코드 관리
- 단일 `GlobalException` 클래스로 모든 도메인 예외 표현
- `.apply {}` 스코프 함수로 `ProblemDetail` 설정 체이닝
- 예상치 못한 예외는 `Exception` 핸들러에서 500 반환

---

## 이벤트 패턴 (Event)

### 이벤트 정의

```kotlin
data class ArticleLikedEvent(
    val articleId: UUID,
    val articleTitle: String,
    val articleAuthorId: UUID,
    val likerNickname: String,
)

data class CommentCreatedEvent(
    val articleId: UUID,
    val articleTitle: String,
    val articleAuthorId: UUID,
    val commentAuthorNickname: String,
    val parentCommentAuthorId: UUID?,
)
```

### 이벤트 리스너

```kotlin
@Component
class NotificationEventListener(
    private val notificationService: NotificationService,
) {
    private val logger = LoggerFactory.getLogger(javaClass)

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    fun onArticleLiked(event: ArticleLikedEvent) {
        try {
            notificationService.createNotification(
                userId = event.articleAuthorId,
                type = NotificationType.ARTICLE_LIKE,
                title = "새 추천",
                message = "${event.likerNickname}님이 '${event.articleTitle}'에 추천했습니다",
                link = "/articles/${event.articleId}",
                referenceId = event.articleId,
            )
        } catch (e: Exception) {
            logger.warn("Failed to create like notification", e)
        }
    }
}
```

### 이벤트 패턴 원칙

- 이벤트 data class에 리스너가 필요한 모든 컨텍스트 포함 (title, nickname 등)
- `@Async` + `@TransactionalEventListener(phase = AFTER_COMMIT)`: 메인 트랜잭션 커밋 후 비동기 실행
- `@Async`는 별도 스레드에서 실행되므로 기존 트랜잭션 컨텍스트가 없음 → 별도의 `@Transactional` 없이도 새 트랜잭션이 시작됨. DB 쓰기가 필요한 경우에만 `@Transactional`을 명시
- try-catch로 감싸서 부수 효과 실패가 메인 로직에 영향 주지 않도록
- 에러는 `warn` 레벨로 로깅

---

## 배치 패턴 (Batch / Scheduled)

```kotlin
@Service
class CountSyncBatchService(
    private val jdbcTemplate: JdbcTemplate,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    @Scheduled(cron = "0 0 3 * * *") // 매일 03:00
    fun syncAllCounts() {
        log.info("[CountSync] Starting daily count synchronization")
        try {
            val likeFixed = syncLikeCount()
            val bookmarkFixed = syncBookmarkCount()
            log.info("[CountSync] Completed - likes: $likeFixed, bookmarks: $bookmarkFixed corrections")
        } catch (e: Exception) {
            log.error("[CountSync] Failed", e)
        }
    }

    private fun syncLikeCount(): Int {
        return jdbcTemplate.update("""
            UPDATE article a SET like_count = (
                SELECT COUNT(*) FROM article_like al WHERE al.article_id = a.id
            )
            WHERE a.like_count != (
                SELECT COUNT(*) FROM article_like al WHERE al.article_id = a.id
            )
        """.trimIndent())
    }
}

@Component
class NotificationCleanupBatch(
    private val notificationRepository: NotificationRepository,
) {
    private val logger = LoggerFactory.getLogger(javaClass)

    @Scheduled(cron = "0 0 4 * * *") // 매일 04:00
    @Transactional
    fun cleanupOldNotifications() {
        val threshold = LocalDateTime.now().minusDays(30)
        notificationRepository.deleteOlderThan(threshold)
        logger.info("Cleaned up notifications older than {}", threshold)
    }
}
```

### 배치 작성 원칙

- `@Scheduled(cron = ...)` 으로 주기적 실행
- 대량 처리 시 페이지네이션 (`PageRequest`) 활용
- `runCatching` + `onFailure`로 개별 항목 실패 처리
- 시작/완료/에러 로깅 필수 (접두사 태그 활용: `[CountSync]`)
- `trimIndent()`로 멀티라인 SQL 가독성 확보

---

## 커스텀 어노테이션 & ArgumentResolver

```kotlin
// 어노테이션 정의
@Target(AnnotationTarget.VALUE_PARAMETER)
@Retention(AnnotationRetention.RUNTIME)
annotation class CurrentUserId(
    val required: Boolean = true,
)

// ArgumentResolver 구현
@Component
class CurrentUserIdArgumentResolver : HandlerMethodArgumentResolver {

    override fun supportsParameter(parameter: MethodParameter): Boolean {
        return parameter.hasParameterAnnotation(CurrentUserId::class.java)
    }

    override fun resolveArgument(
        parameter: MethodParameter,
        mavContainer: ModelAndViewContainer?,
        webRequest: NativeWebRequest,
        binderFactory: WebDataBinderFactory?,
    ): Any? {
        val annotation = parameter.getParameterAnnotation(CurrentUserId::class.java)
        val required = annotation?.required ?: true

        val authentication = SecurityContextHolder.getContext().authentication

        if (authentication == null
            || !authentication.isAuthenticated
            || authentication.principal !is UserPrincipal
        ) {
            if (!required) return null
            throw GlobalException(ErrorCode.UNAUTHORIZED)
        }

        val principal = authentication.principal as UserPrincipal
        return principal.id
    }
}

// WebMvcConfig에 등록
@Configuration
class WebMvcConfig(
    private val currentUserIdArgumentResolver: CurrentUserIdArgumentResolver,
) : WebMvcConfigurer {
    override fun addArgumentResolvers(resolvers: MutableList<HandlerMethodArgumentResolver>) {
        resolvers.add(currentUserIdArgumentResolver)
    }
}
```

---

## AOP 패턴

```kotlin
@Aspect
@Component
class ControllerLoggingAspect {

    private val log = LoggerFactory.getLogger(ControllerLoggingAspect::class.java)

    @Around("within(@org.springframework.web.bind.annotation.RestController *)")
    fun logAround(joinPoint: ProceedingJoinPoint): Any? {
        val signature = joinPoint.signature as MethodSignature
        val method = signature.method
        val className = signature.declaringType.simpleName
        val methodName = method.name

        val operation = method.getAnnotation(Operation::class.java)
        val summary = operation?.summary ?: methodName

        log.debug(">>> [START] {} - {}.{}", summary, className, methodName)
        val startTime = System.currentTimeMillis()

        return try {
            val result = joinPoint.proceed()
            val elapsed = System.currentTimeMillis() - startTime
            log.debug("<<< [END] {} - {}.{} ({}ms)", summary, className, methodName, elapsed)
            result
        } catch (e: Exception) {
            val elapsed = System.currentTimeMillis() - startTime
            log.debug("<!> {} - {}.{} ({}ms) - {}", summary, className, methodName, elapsed, e.message)
            throw e
        }
    }
}
```

---

## Configuration 패턴

### Properties 바인딩

```kotlin
@ConfigurationProperties(prefix = "jwt")
data class JwtProperties(
    val secret: String,
    val accessTokenExp: Long,
    val refreshTokenExp: Long,
)
```

### QueryDSL 설정

```kotlin
@Configuration
class QueryDslConfig(
    @PersistenceContext private val entityManager: EntityManager,
) {
    @Bean
    fun jpaQueryFactory(): JPAQueryFactory = JPAQueryFactory(entityManager)
}
```

### JPA Auditing 설정

```kotlin
@EnableJpaAuditing
@Configuration
class JpaAuditConfig : AuditorAware<UUID> {
    override fun getCurrentAuditor(): Optional<UUID> {
        val authentication = SecurityContextHolder.getContext().authentication
            ?: return Optional.empty()
        if (!authentication.isAuthenticated) return Optional.empty()
        val principal = authentication.principal as? UserPrincipal
            ?: return Optional.empty()
        return Optional.ofNullable(principal.id)
    }
}
```

### Swagger 설정

```kotlin
@Configuration
class SwaggerConfig {

    init {
        SpringDocUtils.getConfig().addAnnotationsToIgnore(CurrentUserId::class.java)
    }

    @Bean
    fun openApi(): OpenAPI {
        val securitySchemeName = "bearerAuth"

        return OpenAPI()
            .info(
                Info()
                    .title("My API")
                    .description("API 설명")
                    .version("v1.0.0")
            )
            .components(
                Components().addSecuritySchemes(
                    securitySchemeName,
                    SecurityScheme()
                        .name("Authorization")
                        .type(SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")
                )
            )
            .addSecurityItem(SecurityRequirement().addList(securitySchemeName))
    }
}
```

---

## Application 진입점

```kotlin
@SpringBootApplication
@ConfigurationPropertiesScan   // @ConfigurationProperties 클래스 자동 스캔
@EnableFeignClients
@EnableScheduling
class FlicleApplication

fun main(args: Array<String>) {
    runApplication<FlicleApplication>(*args)  // Kotlin 확장 함수 (SpringApplication.run 대신)
}
```

- `runApplication<T>(*args)`: Spring Boot의 Kotlin 확장 함수로, Java의 `SpringApplication.run(T::class.java, *args)` 대체
- `@ConfigurationPropertiesScan`: `@ConfigurationProperties` 클래스를 별도 `@Bean` 등록 없이 자동 스캔

---

## Security 패턴

### SecurityFilterChain (Lambda DSL)

```kotlin
@Configuration
class SecurityConfig(
    private val jwtAuthenticationFilter: JwtAuthenticationFilter,
    @Value("\${cors.allowed-origins:http://localhost:3000}")
    private val corsAllowedOrigins: String,
) {
    companion object {
        val PERMIT_ALL_URLS = listOf(
            "/health",
            "/api/auth/login",
            "/api/auth/signup",
            "/api/auth/refresh",
            "/api/public/**",
        )
        val PUBLIC_GET_PATTERNS = listOf(
            "/api/articles/{articleId}",
            "/api/articles/{articleId}/comments",
        )
        val SWAGGER_URLS = listOf("/v3/api-docs/**", "/swagger-ui/**", "/swagger-ui.html")
    }

    @Bean
    fun securityFilterChain(http: HttpSecurity): SecurityFilterChain {
        http
            .csrf { it.disable() }
            .cors { it.configurationSource(corsConfigurationSource()) }
            .sessionManagement { it.sessionCreationPolicy(SessionCreationPolicy.STATELESS) }
            .exceptionHandling { exceptions ->
                exceptions.authenticationEntryPoint { request, response, _ ->
                    response.status = HttpStatus.UNAUTHORIZED.value()
                    response.contentType = MediaType.APPLICATION_JSON_VALUE
                    response.characterEncoding = "UTF-8"

                    val err = ProblemDetail.forStatusAndDetail(
                        HttpStatus.UNAUTHORIZED, "인증이 필요합니다."
                    ).apply {
                        type = URI.create("https://example.app/problems/unauthorized")
                        title = "UNAUTHORIZED"
                        instance = URI.create(request.requestURI)
                    }
                    response.writer.write(ObjectMapper().writeValueAsString(err))
                }
            }
            .authorizeHttpRequests { authorize ->
                authorize
                    .requestMatchers(*PERMIT_ALL_URLS.toTypedArray()).permitAll()
                    .requestMatchers(*SWAGGER_URLS.toTypedArray()).permitAll()
                    .requestMatchers(HttpMethod.GET, *PUBLIC_GET_PATTERNS.toTypedArray()).permitAll()
                    .anyRequest().authenticated()
            }
            .formLogin { it.disable() }
            .httpBasic { it.disable() }
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter::class.java)

        return http.build()
    }

    @Bean
    fun passwordEncoder(): PasswordEncoder = BCryptPasswordEncoder()

    @Bean
    fun corsConfigurationSource(): CorsConfigurationSource {
        val configuration = CorsConfiguration()
        configuration.allowedOrigins = corsAllowedOrigins.split(",").map { it.trim() }
        configuration.allowedMethods = listOf("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
        configuration.allowedHeaders = listOf("Authorization", "Content-Type")
        configuration.allowCredentials = true

        val source = UrlBasedCorsConfigurationSource()
        source.registerCorsConfiguration("/**", configuration)
        return source
    }
}
```

### Security 패턴 원칙

- `companion object`에 URL 패턴을 `listOf`로 관리 → `toTypedArray()`로 vararg 전달
- Lambda DSL: `{ it.disable() }` 패턴으로 간결한 설정
- `ProblemDetail` + `.apply {}` 로 일관된 에러 응답
- `@Value`로 환경별 CORS 설정 분리

### UserPrincipal (UserDetails 구현)

```kotlin
class UserPrincipal(
    val id: UUID?,
    private val email: String,
    private val password: String,
    private val role: UserRole,
) : UserDetails {

    companion object {
        fun from(appUser: AppUser): UserPrincipal {
            return UserPrincipal(
                id = appUser.id,
                email = appUser.email,
                password = appUser.password ?: "",
                role = UserRole.ROLE_USER,
            )
        }
    }

    override fun getAuthorities(): MutableCollection<out GrantedAuthority> =
        mutableListOf(SimpleGrantedAuthority(role.name))

    override fun getUsername(): String = email
    override fun getPassword(): String = password
    override fun isAccountNonExpired(): Boolean = true
    override fun isAccountNonLocked(): Boolean = true
    override fun isCredentialsNonExpired(): Boolean = true
    override fun isEnabled(): Boolean = true
}
```

### JwtAuthenticationFilter

```kotlin
@Component
class JwtAuthenticationFilter(
    private val jwtTokenProvider: JwtTokenProvider,
    private val redisTemplate: StringRedisTemplate,
) : OncePerRequestFilter() {

    companion object {
        const val BEARER_PREFIX = "Bearer "
    }

    private val log = LoggerFactory.getLogger(javaClass)

    override fun doFilterInternal(
        request: HttpServletRequest,
        response: HttpServletResponse,
        filterChain: FilterChain,
    ) {
        val jwt = resolveToken(request)

        if (jwt == null) {
            filterChain.doFilter(request, response)
            return
        }

        try {
            val userInfo = jwtTokenProvider.validateAndGetUser(jwt)
            if (userInfo != null && SecurityContextHolder.getContext().authentication == null) {
                val principal = UserPrincipal(
                    id = userInfo.id,
                    email = userInfo.email,
                    password = "",
                    role = userInfo.role,
                )
                val authentication = UsernamePasswordAuthenticationToken(
                    principal, null, principal.authorities
                )
                authentication.details = WebAuthenticationDetailsSource().buildDetails(request)
                SecurityContextHolder.getContext().authentication = authentication
            }
        } catch (ex: ExpiredJwtException) {
            log.debug("토큰 만료: ${ex.message}")
            sendErrorResponse(response, request.requestURI, ErrorCode.TOKEN_EXPIRED)
            return
        } catch (ex: Exception) {
            log.error("인증 오류: ${ex.message}")
            sendErrorResponse(response, request.requestURI, ErrorCode.UNAUTHORIZED)
            return
        }

        filterChain.doFilter(request, response)
    }

    private fun resolveToken(request: HttpServletRequest): String? {
        val authHeader = request.getHeader("Authorization")
        if (authHeader != null && authHeader.startsWith(BEARER_PREFIX)) {
            return authHeader.substring(BEARER_PREFIX.length)
        }
        return null
    }

    private fun sendErrorResponse(
        response: HttpServletResponse,
        requestUri: String,
        errorCode: ErrorCode,
    ) {
        response.status = errorCode.status.value()
        response.contentType = MediaType.APPLICATION_JSON_VALUE
        response.characterEncoding = "UTF-8"

        val err = ProblemDetail.forStatusAndDetail(errorCode.status, errorCode.message).apply {
            title = errorCode.name
            instance = URI.create(requestUri)
        }
        response.writer.write(ObjectMapper().writeValueAsString(err))
    }
}
```

---

## OpenFeign Client 패턴

외부 API 호출은 `@FeignClient` interface로 선언적으로 정의합니다.

```kotlin
@FeignClient(name = "kakao-auth", url = "https://kauth.kakao.com")
interface KakaoAuthClient {

    @PostMapping("/oauth/token", consumes = [MediaType.APPLICATION_FORM_URLENCODED_VALUE])
    fun getToken(@RequestBody params: MultiValueMap<String, String>): KakaoTokenResponse
}

@FeignClient(name = "kakao-api", url = "https://kapi.kakao.com")
interface KakaoApiClient {

    @GetMapping("/v2/user/me")
    fun getUserInfo(@RequestHeader("Authorization") authorization: String): KakaoUserResponse
}
```

### Feign 작성 원칙

- `interface`로 선언 (Kotlin에서 별도 `abstract` 불필요)
- Application 클래스에 `@EnableFeignClients` 필수
- 응답 DTO는 `data class`로 매핑
- 의존성: `org.springframework.cloud:spring-cloud-starter-openfeign`

---

## @ConfigurationProperties + Data Class 바인딩

```kotlin
// data class로 타입 안전한 프로퍼티 바인딩
// data class + val: 불변 바인딩 (생성자가 하나이면 @ConstructorBinding 생략 가능)
// 반드시 @ConfigurationPropertiesScan이 Application 클래스에 있어야 자동 스캔됨
@ConfigurationProperties(prefix = "jwt")
data class JwtProperties(
    val secret: String,
    val accessTokenExp: Long,
    val refreshTokenExp: Long,
)

// 중첩 data class로 프로퍼티 그룹화
@Configuration
@ConfigurationProperties(prefix = "async")
class AsyncConfig {
    var ai: ExecutorProperties = ExecutorProperties()

    @Bean(name = ["aiExecutor"])
    fun aiExecutor(): Executor {
        return ThreadPoolTaskExecutor().apply {
            corePoolSize = ai.coreSize
            maxPoolSize = ai.maxSize
            queueCapacity = ai.queueCapacity
            setThreadNamePrefix("AiExecutor-")
            setRejectedExecutionHandler(CallerRunsPolicy())
            initialize()
        }
    }

    data class ExecutorProperties(
        var coreSize: Int = 5,
        var maxSize: Int = 20,
        var queueCapacity: Int = 100,
    )
}
```

### @ConfigurationProperties 원칙

- Application 클래스에 `@ConfigurationPropertiesScan` 필수
- 불변 바인딩이면 `data class` + `val`, 변경 가능하면 `var` + 기본값
- `kapt("org.springframework.boot:spring-boot-configuration-processor")` 의존성 필요

---

## Redis 패턴

### Redis 키 관리 (object 싱글턴)

```kotlin
object RedisKeys {
    const val TRENDING_ARTICLES = "trending:articles"
    const val TRENDING_KEYWORDS = "trending:keywords"

    fun blacklist(token: String) = "blacklist:$token"
    fun kakaoSignup(token: String) = "kakao:signup:$token"
}
```

### Redis 임시 토큰 관리

```kotlin
@Component
class KakaoSignupTokenManager(
    private val redisTemplate: StringRedisTemplate,
) {
    companion object {
        private const val SIGNUP_TOKEN_TTL_MINUTES = 5L
    }

    fun issueSignupToken(kakaoId: String, email: String): String {
        val signupToken = UUID.randomUUID().toString()
        val redisValue = "$kakaoId:$email"
        redisTemplate.opsForValue()
            .set(RedisKeys.kakaoSignup(signupToken), redisValue, SIGNUP_TOKEN_TTL_MINUTES, TimeUnit.MINUTES)
        return signupToken
    }

    fun getAndInvalidate(signupToken: String): Pair<String, String> {
        val result = get(signupToken)
        redisTemplate.delete(RedisKeys.kakaoSignup(signupToken))
        return result
    }

    private fun get(signupToken: String): Pair<String, String> {
        val redisValue = redisTemplate.opsForValue().get(RedisKeys.kakaoSignup(signupToken))
            ?: throw GlobalException(ErrorCode.KAKAO_SIGNUP_TOKEN_EXPIRED)
        val parts = redisValue.split(":", limit = 2)
        return parts[0] to parts[1]
    }
}
```

### Redis Pipeline (원자적 갱신)

```kotlin
/**
 * Sorted Set을 원자적으로 교체하는 패턴.
 * 임시 키에 데이터를 쌓은 뒤 rename으로 원자 교체합니다.
 */
private fun atomicSwap(targetKey: String, entries: List<Pair<String, Double>>) {
    val tempKey = "${targetKey}:temp:${System.currentTimeMillis()}"

    try {
        val ops = redisTemplate.opsForZSet()
        redisTemplate.expire(tempKey, Duration.ofMinutes(10))  // 방어적 TTL

        entries.forEach { (member, score) ->
            ops.add(tempKey, member, score)
        }

        // Pipeline으로 rename + expire 원자 실행
        redisTemplate.executePipelined { connection ->
            connection.rename(tempKey.toByteArray(), targetKey.toByteArray())
            connection.expire(targetKey.toByteArray(), TRENDING_TTL.seconds)
            null
        }
    } catch (e: Exception) {
        try { redisTemplate.delete(tempKey) } catch (_: Exception) {}
        throw e
    }
}
```
