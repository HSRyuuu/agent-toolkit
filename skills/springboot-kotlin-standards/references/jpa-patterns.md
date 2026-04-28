# JPA & QueryDSL 패턴 (Kotlin)

## Entity 패턴

### 기본 Entity + UUID + JPA Auditing

```kotlin
@EntityListeners(AuditingEntityListener::class)
@Entity
@Table(name = "article_comment")
class ArticleComment(
    @Id
    val id: UUID = UUID.randomUUID(),

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "article_id", nullable = false)
    val article: Article,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "author_id")
    val author: AppUser?,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parent_id")
    val parent: ArticleComment? = null,

    @Column(nullable = false, columnDefinition = "TEXT")
    var content: String,

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    val createdAt: LocalDateTime = LocalDateTime.now(),

    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    var updatedAt: LocalDateTime = LocalDateTime.now(),
)
```

### 유니크 제약 조건 Entity

```kotlin
@Entity
@Table(
    name = "article_bookmark",
    uniqueConstraints = [
        UniqueConstraint(columnNames = ["article_id", "user_id"])
    ]
)
class ArticleBookmark(
    @Id
    val id: UUID = UUID.randomUUID(),

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "article_id", nullable = false)
    val article: Article,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    val user: AppUser,

    @Column(name = "created_at", nullable = false, updatable = false)
    val createdAt: LocalDateTime = LocalDateTime.now(),
)
```

### JSON 컬럼 Entity

```kotlin
@EntityListeners(AuditingEntityListener::class)
@Entity
@Table(name = "diary_analysis_report")
class DiaryAnalysisReport(
    @Id
    val id: UUID = UUID.randomUUID(),

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "diary_id", nullable = false)
    val diary: Diary,

    @Column(columnDefinition = "TEXT")
    val keywords: String? = null,

    @Column(name = "emotion_summary", columnDefinition = "TEXT")
    val emotionSummary: String? = null,

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    var status: AnalysisStatus = AnalysisStatus.PENDING,

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    val createdAt: LocalDateTime = LocalDateTime.now(),

    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    var updatedAt: LocalDateTime = LocalDateTime.now(),
) {
    // JPA Auditing + Kotlin 조합에서 equals/hashCode 재정의
    // UUID 전략(val id: UUID = UUID.randomUUID())에서는 id가 항상 non-null이므로
    // id != null 체크는 선택적입니다. Long? = null (Auto Increment) 전략에서는 필수입니다.
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is DiaryAnalysisReport) return false
        return id == other.id
    }

    override fun hashCode(): Int = javaClass.hashCode()
}
```

### Entity 설계 원칙

- **UUID 식별자**: `@Id val id: UUID = UUID.randomUUID()` — 기본값을 코드에서 직접 생성하여 non-null 타입으로 유지. `@UuidGenerator`나 `UUID? = null` 방식보다 Kotlin의 null safety를 살릴 수 있음. 단, Auto Increment(Long) 등 DB가 값을 생성하는 경우에는 `val id: Long? = null` 허용
- **지연 로딩**: 모든 `@ManyToOne`, `@OneToOne`에 `FetchType.LAZY` 필수
- **val vs var**: 식별자와 생성 시간은 `val`, 변경 가능한 필드만 `var`
- **기본값**: `LocalDateTime.now()`, `AnalysisStatus.PENDING` 등 의미 있는 초기값
- **Enum**: `@Enumerated(EnumType.STRING)` (ORDINAL 사용 금지)
- **비즈니스 메서드**: setter 대신 의미 있는 이름의 메서드로 상태 변경
- **JPA Auditing**: `@CreatedDate`, `@LastModifiedDate` + `@EntityListeners`
- **equals/hashCode**: Auditing 사용 시 id 기반으로 재정의. UUID 전략에서는 `id != null` 체크 생략 가능, Auto Increment(`Long? = null`) 전략에서는 필수

### ID 전략 선택 가이드

| ID 타입 | 패턴 | 설명 |
|---------|------|------|
| UUID | `val id: UUID = UUID.randomUUID()` | 코드에서 기본값 생성, non-null 유지 권장 |
| Long (Auto Increment) | `val id: Long? = null` | DB가 생성하므로 nullable 허용 |
| 복합 키 | `@EmbeddedId val id: CompositeKey` | 별도 `@Embeddable` 클래스 |

### allOpen 설정 필수

Kotlin 클래스는 기본적으로 `final`이므로, JPA 프록시 생성을 위해 `build.gradle.kts`에 설정 필요:

```kotlin
allOpen {
    annotation("jakarta.persistence.Entity")
    annotation("jakarta.persistence.MappedSuperclass")
}
```

---

## Repository 패턴

### JpaRepository 인터페이스

```kotlin
interface ArticleRepository : JpaRepository<Article, UUID> {

    @Query("""
        SELECT a FROM Article a
        LEFT JOIN FETCH a.keywords
        LEFT JOIN FETCH a.author
        WHERE a.id = :id
    """)
    fun findByIdWithKeywordsAndAuthor(@Param("id") id: UUID): Article?

    @Query("""
        SELECT a FROM Article a
        LEFT JOIN FETCH a.keywords
        LEFT JOIN FETCH a.author
        WHERE a.id IN :ids
    """)
    fun findByIdInWithKeywordsAndAuthor(@Param("ids") ids: List<UUID>): List<Article>

    fun findByAuthorId(authorId: UUID, pageable: Pageable): Page<Article>

    @Modifying(clearAutomatically = true)
    @Query("UPDATE Article a SET a.viewCount = a.viewCount + 1 WHERE a.id = :id")
    fun incrementViewCount(@Param("id") id: UUID)

    @Modifying(flushAutomatically = true, clearAutomatically = true)
    @Query("UPDATE Article a SET a.likeCount = a.likeCount + :delta WHERE a.id = :id")
    fun updateLikeCount(@Param("id") id: UUID, @Param("delta") delta: Long)
}

interface ArticleCommentRepository : JpaRepository<ArticleComment, UUID> {

    @Query("""
        SELECT c FROM ArticleComment c
        LEFT JOIN FETCH c.author
        WHERE c.article.id = :articleId AND c.parent IS NULL
        ORDER BY c.createdAt DESC
    """)
    fun findRootCommentsByArticleId(@Param("articleId") articleId: UUID): List<ArticleComment>

    @Query("""
        SELECT c FROM ArticleComment c
        LEFT JOIN FETCH c.author
        WHERE c.parent.id IN :parentIds
        ORDER BY c.createdAt ASC
    """)
    fun findRepliesByParentIds(@Param("parentIds") parentIds: List<UUID>): List<ArticleComment>

    fun countByArticleId(articleId: UUID): Long
    fun deleteByParentId(parentId: UUID)
}

interface NotificationRepository : JpaRepository<Notification, UUID> {

    fun findByUserIdOrderByCreatedAtDesc(userId: UUID, pageable: Pageable): Page<Notification>

    @Modifying
    @Query("DELETE FROM Notification n WHERE n.createdAt < :threshold")
    fun deleteOlderThan(@Param("threshold") threshold: LocalDateTime)
}
```

### Repository 작성 원칙

- Spring Data JPA 메서드 네이밍 컨벤션 활용
- N+1 방지를 위해 `LEFT JOIN FETCH` 사용
- `@Modifying`은 `clearAutomatically = true` 권장 (1차 캐시 동기화)
- 카운트 업데이트 쿼리: `flushAutomatically = true, clearAutomatically = true`
- 반환 타입: 단건 nullable → `Article?`, Optional 필요 시 → `Optional<Article>`
- 벌크 삭제/수정: `@Query` + `@Modifying`

### JPA Projection (interface 기반)

JPQL 집계 쿼리의 결과를 interface로 매핑하는 패턴입니다. Entity 전체를 로딩하지 않고 필요한 필드만 조회할 때 유용합니다.

```kotlin
interface DiaryRepository : JpaRepository<Diary, UUID> {

    @Query("""
        SELECT d.date as date, COUNT(d) as count
        FROM Diary d
        WHERE d.user.id = :userId AND d.date BETWEEN :startDate AND :endDate
        GROUP BY d.date ORDER BY d.date
    """)
    fun countByUserIdGroupByDate(
        @Param("userId") userId: UUID,
        @Param("startDate") startDate: LocalDate,
        @Param("endDate") endDate: LocalDate,
    ): List<DateCountProjection>

    @Query("""
        SELECT DISTINCT YEAR(d.date)
        FROM Diary d
        WHERE d.user.id = :userId
        ORDER BY YEAR(d.date) DESC
    """)
    fun findDistinctYearsByUserId(@Param("userId") userId: UUID): List<Int>

    // Projection interface: JPQL alias와 getter 이름이 일치해야 함
    interface DateCountProjection {
        fun getDate(): LocalDate
        fun getCount(): Long
    }
}
```

### Projection 작성 원칙

- Repository 내부에 중첩 `interface`로 선언 (응집도 유지)
- JPQL `SELECT` 절의 alias와 Projection의 getter 이름이 일치해야 함 (`as date` → `getDate()`)
- 단순 값 반환은 `List<Int>`, `List<String>` 등 기본 타입도 가능
- 복잡한 매핑이 필요하면 `data class` + JPQL `new` 생성자 또는 `@SqlResultSetMapping` 활용

---

## QueryDSL 패턴

### Custom Repository 구현

```kotlin
@Repository
class DiaryQueryRepository(
    private val queryFactory: JPAQueryFactory,
) {
    fun findByUserIdWithFilters(
        userId: UUID,
        dateStart: LocalDate?,
        dateEnd: LocalDate?,
        searchWord: String?,
        pageable: Pageable,
    ): Page<Diary> {
        val diary = QDiary.diary
        val diaryAnalysisReport = QDiaryAnalysisReport.diaryAnalysisReport

        val builder = BooleanBuilder()
        builder.and(diary.user.id.eq(userId))

        if (dateStart != null) {
            builder.and(diary.date.goe(dateStart))
        }
        if (dateEnd != null) {
            builder.and(diary.date.loe(dateEnd))
        }

        val query = queryFactory.selectFrom(diary)

        if (!searchWord.isNullOrBlank()) {
            query.leftJoin(diaryAnalysisReport)
                .on(diaryAnalysisReport.diary.id.eq(diary.id))
            builder.and(
                diary.content.containsIgnoreCase(searchWord)
                    .or(diaryAnalysisReport.keywords.containsIgnoreCase(searchWord))
            )
        }

        val content = query
            .where(builder)
            .orderBy(diary.createdAt.desc())
            .offset(pageable.offset)
            .limit(pageable.pageSize.toLong())
            .fetch()

        val total = queryFactory
            .select(diary.count())
            .from(diary)
            .apply {
                if (!searchWord.isNullOrBlank()) {
                    leftJoin(diaryAnalysisReport)
                        .on(diaryAnalysisReport.diary.id.eq(diary.id))
                }
            }
            .where(builder)
            .fetchOne() ?: 0L

        return PageImpl(content, pageable, total)
    }
}
```

### JdbcTemplate 활용 (복잡한 네이티브 쿼리)

```kotlin
@Repository
class TrendingQueryRepository(
    private val jdbcTemplate: JdbcTemplate,
) {
    fun findArticleTrendingData(): List<ArticleTrendingData> {
        val sql = """
            WITH view_stats AS (
                SELECT article_id, COUNT(*) as recent_views
                FROM article_view_log
                WHERE viewed_at >= NOW() - INTERVAL '7 days'
                GROUP BY article_id
            )
            SELECT a.id as article_id,
                   COALESCE(vs.recent_views, 0) as recent_views
            FROM article a
            LEFT JOIN view_stats vs ON a.id = vs.article_id
        """.trimIndent()

        return jdbcTemplate.query(sql) { rs, _ ->
            ArticleTrendingData(
                articleId = UUID.fromString(rs.getString("article_id")),
                recentViews = rs.getLong("recent_views"),
            )
        }
    }
}

data class ArticleTrendingData(
    val articleId: UUID,
    val recentViews: Long,
)
```

### QueryDSL 작성 원칙

- `BooleanBuilder`로 동적 조건 조합. 또는 `BooleanExpression?`을 반환하는 메서드 분리 패턴도 활용 가능:
  ```kotlin
  private fun dateGoe(date: LocalDate?): BooleanExpression? =
      date?.let { QDiary.diary.date.goe(it) }
  // 사용: .where(dateGoe(dateStart), dateGoe(dateEnd))  // null은 자동 무시
  ```
- nullable 파라미터를 `if (param != null)` 조건으로 동적 쿼리 구성
- Kotlin의 `.apply {}` 활용하여 조건부 join 추가
- 카운트 쿼리는 별도로 실행하여 `PageImpl`로 감싸기
- `?.isNullOrBlank()`로 String null/empty 동시 체크
- 복잡한 통계 쿼리는 `JdbcTemplate` + `trimIndent()` 활용
- 결과 매핑: lambda `{ rs, _ -> ... }` 패턴

### QueryDSL 설정 (build.gradle.kts)

```kotlin
dependencies {
    implementation("com.querydsl:querydsl-jpa:5.0.0:jakarta")
    kapt("com.querydsl:querydsl-apt:5.0.0:jakarta")  // QueryDSL은 아직 KSP 미지원, kapt 사용
}
```
