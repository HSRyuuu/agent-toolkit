---
name: springboot-kotlin-standards
description: "Kotlin + Spring Boot 코딩 표준 및 서비스 개발 가이드. Kotlin 코드 작성/리뷰, data class, null safety, 확장 함수, companion object, 생성자 주입, 예외 처리, 테스트 작성 시 사용. Spring Boot 프로젝트에서는 references/spring-boot-patterns.md, JPA/QueryDSL 작업 시에는 references/jpa-patterns.md를 함께 참조."
origin: ECC
---

# Kotlin 코딩 표준 (Kotlin Coding Standards)

Spring Boot 서비스에서 읽기 쉽고 유지보수가 용이한 Kotlin 코드를 작성하기 위한 표준입니다.

## 적용 시점

- Spring Boot 프로젝트에서 Kotlin 코드를 작성하거나 리뷰할 때
- data class, sealed class, companion object 등 Kotlin 고유 기능을 활용할 때
- Null safety, 확장 함수, 스코프 함수 사용을 검토할 때
- 명명 규칙, 패키지 구조, 예외 처리 컨벤션을 강제할 때

## 핵심 원칙

- Kotlin의 간결함을 활용하되, 기교보다는 명확함을 우선시합니다.
- Null safety를 적극 활용하고, nullable 타입은 최소화합니다.
- 기본적으로 불변(`val`)을 지향하며, `var`는 명확한 이유가 있을 때만 사용합니다.
- 보일러플레이트를 제거하되, 가독성을 희생하지 않습니다.

---

## 명명 규칙 (Naming)

```kotlin
// 클래스: PascalCase
class ArticleCommentService
data class ArticleDetailResponse

// 함수/프로퍼티: camelCase
private val articleRepository: ArticleRepository
fun findBySlug(slug: String): Article

// 상수: UPPER_SNAKE_CASE (companion object 내 const)
companion object {
    private const val MAX_PAGE_SIZE = 100
}

// 약어(Acronym)는 일반 단어처럼 처리
XmlHttpRequest, newCustomerId, supportsIpv6OnIos
// Bad: XMLHTTPRequest, newCustomerID, supportsIPv6OnIOS
```

## 불변성 및 상태 관리 (Immutability & State)

```kotlin
// DTO는 data class + val 프로퍼티
data class ArticleDetailResponse(
    val id: UUID,
    val title: String,
    val status: ArticleStatus,
)

// Entity에서 변경 가능한 필드만 var, 나머지는 val
// UUID처럼 기본값 설정이 가능한 ID는 non-null로 선언
class Article(
    @Id
    val id: UUID = UUID.randomUUID(),

    @Column(nullable = false)
    var title: String,

    @Column(nullable = false)
    var status: ArticleStatus = ArticleStatus.DRAFT,
) {
    // setter 대신 비즈니스 메서드
    fun publish() {
        this.status = ArticleStatus.PUBLISHED
    }
}
```

## Null Safety

Kotlin의 타입 시스템을 통해 null을 컴파일 타임에 관리합니다.

```kotlin
// nullable 타입은 명확한 이유가 있을 때만 사용
val parent: ArticleComment? = null  // 루트 댓글은 부모가 없음

// 안전 호출 연산자 (?.)
val authorName = comment.author?.nickname

// 엘비스 연산자 (?:)
val replies = repliesMap[root.id] ?: emptyList()

// let으로 null 체크 후 처리
user.id?.let { service.aggregateWeek(it, startDate, endDate) }

// 절대 !! 연산자를 습관적으로 사용하지 마세요.
// 단, 이미 null이 아님이 보장된 직후(e.g., save 후 id) 등
// 명확한 문맥에서는 허용됩니다.
val savedId = repository.save(entity).id!!
```

## Data Class 활용

```kotlin
// DTO: data class (equals, hashCode, toString, copy 자동 생성)
data class CommentCreateRequest(
    @field:NotBlank(message = "내용은 필수입니다.")
    val content: String,
    val parentId: UUID? = null,
)

// Response에 companion object factory 메서드
data class CommentResponse(
    val id: UUID,
    val content: String,
    val createdAt: LocalDateTime,
    val isMine: Boolean,
) {
    companion object {
        fun from(comment: ArticleComment, currentUserId: UUID?): CommentResponse {
            return CommentResponse(
                id = comment.id!!,
                content = comment.content,
                createdAt = comment.createdAt,
                isMine = currentUserId != null && comment.author?.id == currentUserId,
            )
        }
    }
}

// 이벤트: data class로 간결하게
data class ArticleLikedEvent(
    val articleId: UUID,
    val articleTitle: String,
    val articleAuthorId: UUID,
    val likerNickname: String,
)
```

## Enum 패턴

```kotlin
// 단순 Enum
enum class ArticleStatus {
    DRAFT, PUBLISHED, PRIVATE,
}

// 프로퍼티를 가진 Enum
enum class AiTemperature(val value: Double) {
    STRICT(0.1),
    BALANCED(0.3),
    MODERATE(0.5),
    CREATIVE(0.7),
}

// companion object로 변환 로직 포함
enum class YNFlag(val value: Boolean) {
    Y(true), N(false);

    companion object {
        fun fromBoolean(value: Boolean): YNFlag = if (value) Y else N
    }
}
```

## 컬렉션 및 스코프 함수

```kotlin
// 변환 작업에 컬렉션 함수를 활용
val names = markets.mapNotNull { it.name }
val rootIds = rootComments.mapNotNull { it.id }
val repliesMap = replies.groupBy { it.parent?.id }

// apply: 객체 초기화/설정 체이닝
val template = RedisTemplate<String, Any>().apply {
    connectionFactory = factory
    keySerializer = StringRedisSerializer()
    afterPropertiesSet()
}

// let: null 체크 후 처리
user.id?.let { userId -> service.process(userId) }

// also: 부수 효과 (로깅 등)
repository.save(entity).also { log.info("Saved entity: ${it.id}") }

// runCatching: 예외를 Result로 래핑
runCatching { service.aggregateWeek(userId, start, end) }
    .onFailure { log.error("Failed for user=$userId", it) }
```

## 생성자 주입 (Constructor Injection)

```kotlin
// Kotlin에서는 @RequiredArgsConstructor 없이 주생성자로 직접 주입
@Service
@Transactional(readOnly = true)
class ArticleCommentService(
    private val articleCommentRepository: ArticleCommentRepository,
    private val articleRepository: ArticleRepository,
    private val eventPublisher: ApplicationEventPublisher,
)

// @Autowired, @Inject 등 필드 주입은 엄격히 금지
// Bad:
// @Autowired
// private lateinit var repository: ArticleRepository
```

## 예외 처리 (Exceptions)

```kotlin
// 중앙화된 ErrorCode enum
enum class ErrorCode(val status: HttpStatus, val message: String) {
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "사용자를 찾을 수 없습니다"),
    ARTICLE_NOT_FOUND(HttpStatus.NOT_FOUND, "아티클을 찾을 수 없습니다"),
    UNAUTHORIZED(HttpStatus.UNAUTHORIZED, "인증이 필요합니다"),
    FORBIDDEN(HttpStatus.FORBIDDEN, "접근 권한이 없습니다"),
    INVALID_REQUEST(HttpStatus.BAD_REQUEST, "요청 값이 올바르지 않습니다"),
    DUPLICATE_EMAIL(HttpStatus.CONFLICT, "이미 사용 중인 이메일입니다"),
}

// 단일 GlobalException 클래스
class GlobalException(
    val errorCode: ErrorCode,
    override val cause: Throwable? = null,
    val data: Any? = null,
) : RuntimeException(errorCode.message, cause)

// 사용 (findByIdOrNull: Spring Data Kotlin 확장 함수)
articleRepository.findByIdOrNull(id)
    ?: throw GlobalException(ErrorCode.ARTICLE_NOT_FOUND)
```

## Validation

```kotlin
// data class에서 @field: 접두사 필수 (Kotlin의 annotation target 지정)
data class ArticleCreateRequest(
    @field:NotBlank(message = "제목은 필수입니다.")
    @field:Size(max = 300, message = "제목은 최대 300자입니다.")
    val title: String,

    @field:NotBlank(message = "내용은 필수입니다.")
    val content: String,

    val keywordNames: List<String> = emptyList(),
)
```

## Pair 및 Destructuring

```kotlin
// to infix 함수로 Pair 생성
val entry = articleId to totalScore
val keyValue = "kakaoId" to "email"

// Pair destructuring
val (kakaoId, email) = parseTokenValue(redisValue)

// 함수 반환 타입으로 Pair 활용 (private/내부 함수에서 허용)
// 외부에 노출되는 public 함수에서는 의미 있는 data class를 사용하세요.
private fun parseTokenValue(value: String): Pair<String, String> {
    val parts = value.split(":", limit = 3)
    return parts[0] to parts[1]
}

// List<Pair>에서 sortedByDescending
val scored = data.map { d -> d.articleId to calculateScore(d) }
    .sortedByDescending { it.second }
```

## object + const val 상수 관리

```kotlin
// 도메인 상수는 object에 const val로 관리
object PromptRole {
    const val DIARY_ANALYZER = """
    # Role: 학습 분석 전문가
    당신은 학습 분석 전문가입니다.
    """
}

// Redis 키 관리
object RedisKeys {
    const val TRENDING_ARTICLES = "trending:articles"
    fun blacklist(token: String) = "blacklist:$token"
    fun kakaoSignup(token: String) = "kakao:signup:$token"
}

// 배치 서비스 내 가중치 상수
companion object {
    val TRENDING_TTL: Duration = Duration.ofHours(2)
    const val VIEW_WEIGHT = 1.0
    const val LIKE_WEIGHT = 3.0
}
```

## 중첩 클래스 (Nested Class)

```kotlin
// Configuration 내 중첩 data class로 프로퍼티 그룹화
@Configuration
@ConfigurationProperties(prefix = "async")
class AsyncConfig {
    var ai: ExecutorProperties = ExecutorProperties()

    data class ExecutorProperties(
        var coreSize: Int = 5,
        var maxSize: Int = 20,
        var queueCapacity: Int = 100,
    )
}
```

## 미사용 변수 관례

```kotlin
// 미사용 변수는 _ 로 표기
entries.forEach { (member, score) -> ops.add(key, member, score) }

// catch에서 예외 객체를 사용하지 않을 때
try { redisTemplate.delete(tempKey) } catch (_: Exception) {}

// lambda에서 미사용 파라미터
jdbcTemplate.query(sql) { rs, _ -> mapRow(rs) }
```

---

## Gradle Kotlin DSL 빌드 설정

Kotlin + Spring Boot 프로젝트의 필수 빌드 설정입니다.

```kotlin
plugins {
    kotlin("jvm") version "1.9.25"              // 프로젝트에 맞는 최신 안정 버전 사용
    kotlin("plugin.spring") version "1.9.25"    // open class 자동 처리
    kotlin("plugin.jpa") version "1.9.25"       // no-arg 생성자 자동 생성
    id("com.google.devtools.ksp") version "1.9.25-1.0.20"  // KSP 권장
    // kotlin("kapt") version "1.9.25"          // KSP 미지원 라이브러리가 있을 때만 사용
    id("org.springframework.boot") version "3.2.12"
    id("io.spring.dependency-management") version "1.1.7"
}

dependencies {
    // Kotlin 필수
    implementation("org.jetbrains.kotlin:kotlin-reflect")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin")

    // KSP (annotationProcessor 대신, kapt보다 빌드 속도 우수)
    ksp("org.springframework.boot:spring-boot-configuration-processor")

    // QueryDSL: 아직 KSP를 공식 지원하지 않으므로 kapt 사용
    // kapt("com.querydsl:querydsl-apt:5.0.0:jakarta")

    // Test: mockito-kotlin
    testImplementation("org.mockito.kotlin:mockito-kotlin:5.4.0")
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit5")
}

// Kotlin 컴파일러 옵션: JSR-305 null safety 어노테이션 strict 모드
kotlin {
    compilerOptions {
        freeCompilerArgs.addAll("-Xjsr305=strict")
    }
}

// JPA Entity가 final이면 프록시 생성 불가 → allOpen 필수
allOpen {
    annotation("jakarta.persistence.Entity")
    annotation("jakarta.persistence.MappedSuperclass")
    annotation("jakarta.persistence.Embeddable")
}

// QueryDSL Q클래스 소스 경로
sourceSets {
    main {
        java { srcDir("build/generated/source/kapt/main") }
    }
}
```

### 빌드 설정 핵심 포인트

| 설정 | Java 대비 차이 | 이유 |
|------|---------------|------|
| `plugin.spring` | `@Component` 등 Spring 클래스를 자동으로 `open` 처리 | Kotlin 클래스는 기본 `final` |
| `plugin.jpa` | Entity에 기본 생성자 자동 생성 | JPA 프록시/리플렉션에 필요 |
| `ksp` (권장) / `kapt` | `annotationProcessor` 대신 사용 | KSP가 빌드 속도 우수, KSP 미지원 시 kapt 사용 |
| `-Xjsr305=strict` | Spring의 `@Nullable`/`@NonNull`을 Kotlin 타입에 반영 | null safety 강화 |
| `allOpen` | Entity 클래스를 `open`으로 변환 | 지연 로딩 프록시 생성 |
| `jackson-module-kotlin` | data class 직렬화/역직렬화 지원 | 기본 생성자 없이도 동작 |

---

## 유틸리티 클래스

```kotlin
// object 선언으로 싱글턴 유틸리티 (인스턴스화 방지 자동)
object TextUtils {
    fun extractJson(raw: String): String {
        val trimmed = raw.trim()
        if (trimmed.startsWith("```")) {
            return trimmed.lines()
                .dropWhile { it.startsWith("```") }
                .dropLastWhile { it.startsWith("```") }
                .joinToString("\n")
        }
        return trimmed
    }
}
```

## 로깅 (Logging)

```kotlin
// 권장: companion object 로거 (클래스당 하나, Java의 static 로거와 동일)
companion object {
    private val log = LoggerFactory.getLogger(ArticleService::class.java)
}

// 또는 인스턴스 로거 (간단하지만 인스턴스마다 생성됨)
private val log = LoggerFactory.getLogger(javaClass)

// 구조화된 로깅
log.info("[CountSync] Completed - likes: $likeFixed, bookmarks: $bookmarkFixed corrections")
log.error("[CountSync] Failed", e)
```

## 포매팅 및 스타일

- 4칸 공백 들여쓰기
- 후행 콤마(trailing comma) 사용 권장 (diff 최소화)
- 파라미터가 3개 이상이면 각 파라미터를 개별 줄에 배치
- 단일 표현식 함수는 `=` 구문 활용 가능하나, 복잡한 로직에는 블록 본문 사용

```kotlin
// 후행 콤마
data class MyResponse(
    val id: UUID,
    val name: String,
    val status: Status,  // trailing comma
)

// 단일 표현식 함수
fun isActive(): Boolean = status == Status.ACTIVE
```

---

## 프로젝트 구조 (Project Structure)

**도메인형 패키지 구조(Package-by-Feature)**를 강력히 권장합니다.

```
src/main/kotlin/com/example/app/
  application/            // 글로벌 설정, 보안, 예외 처리
    config/
    exception/
    security/
    annotation/
    aop/
    property/
  domain/                 // 도메인 모듈들
    article/
      controller/
      service/
      repository/
      model/
        entity/
        dto/
        type/             // Enum 등
      batch/
    user/
      auth/
        controller/
        service/
        model/dto/
      appuser/
        controller/
        service/
        model/
          entity/
          dto/
          type/
    notification/
      controller/
      service/
      repository/
      model/
        entity/
        dto/
        type/
      event/
      batch/
  common/                 // 공통 유틸리티, 공유 DTO
    utils/
    dto/
      type/
    ai/
src/test/kotlin/... (mirrors main)
```

---

## 피해야 할 패턴 (Anti-patterns)

- `!!` 남용 → 안전 호출 `?.` + 엘비스 `?:` 사용
- `lateinit var`를 일반 로직에 사용 → 생성자 주입 또는 `by lazy` 활용
- Java의 `@Data`, `@Getter`, `@Setter` 사용 → Kotlin의 프로퍼티와 data class로 대체
- `when` 문에서 모든 분기를 처리하지 않음 → sealed class 또는 `else` 분기 필수
- mutable 컬렉션을 외부에 노출 → `List`(불변 인터페이스) 반환

---

## 테스트 (Testing)

상태 검증 중심의 테스트 작성을 위해 별도 패턴을 따릅니다.
참조: `references/kotlin-test-patterns.md`

---

## 상세 참조

상황에 맞는 레퍼런스를 참조하세요:

- **Spring Boot 컨트롤러/서비스/DTO/예외처리 패턴**: `references/spring-boot-patterns.md`
- **JPA Entity/Repository/QueryDSL 패턴**: `references/jpa-patterns.md`
- **Kotlin 테스트 패턴**: `references/kotlin-test-patterns.md`

**기억하세요**: 코드는 의도적이고, 타입이 안전하며, 관찰 가능해야 합니다. Kotlin의 간결함을 활용하되, 유지보수성을 위해 최적화하세요.
