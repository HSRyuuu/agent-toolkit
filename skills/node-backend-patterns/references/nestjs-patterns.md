# NestJS 개발 패턴

> 상세 패턴은 개별 레퍼런스 파일을 참조합니다:
> - `nestjs-auth-patterns.md` - 인증/인가 (Guard, 데코레이터, JWT)
> - `nestjs-common-patterns.md` - 공통 패턴 (Exception Filter, Interceptor, main.ts)
> - `nestjs-testing-patterns.md` - 테스트 (단위 테스트, E2E 테스트)

## 프로젝트 구조

모듈 기반 co-location 구조를 사용합니다. 관련 파일을 모듈 단위로 배치하여 모듈 추출, 마이크로서비스 분리, 테스트 격리를 용이하게 합니다:

```
src/
├── app.module.ts
├── main.ts
├── config/
│   ├── app.config.ts              # 환경 설정 스키마
│   └── database.config.ts
├── modules/
│   ├── project/
│   │   ├── project.module.ts
│   │   ├── project.controller.ts
│   │   ├── project.service.ts
│   │   ├── project.repository.ts
│   │   ├── dto/
│   │   │   ├── create-project.dto.ts
│   │   │   └── update-project.dto.ts
│   │   ├── entities/
│   │   │   └── project.entity.ts
│   │   └── __tests__/
│   │       ├── project.controller.spec.ts
│   │       └── project.service.spec.ts
│   ├── auth/
│   │   ├── auth.module.ts
│   │   ├── auth.controller.ts
│   │   ├── auth.service.ts
│   │   ├── guards/
│   │   │   ├── jwt-auth.guard.ts
│   │   │   └── roles.guard.ts
│   │   ├── decorators/
│   │   │   ├── current-user.decorator.ts
│   │   │   └── roles.decorator.ts
│   │   └── strategies/
│   │       └── jwt.strategy.ts
│   └── user/
│       └── ...
└── common/
    ├── filters/
    │   └── all-exceptions.filter.ts
    ├── interceptors/
    │   └── logging.interceptor.ts
    ├── decorators/
    ├── dto/
    │   └── pagination.dto.ts
    └── interfaces/
        └── paginated-result.interface.ts
```

---

## 환경 설정 (ConfigModule)

`@nestjs/config` + `Joi`로 환경 변수를 검증하고 타입 안전하게 관리합니다:

```typescript
// config/app.config.ts
import * as Joi from 'joi';

export const validationSchema = Joi.object({
  NODE_ENV: Joi.string().valid('development', 'production', 'test').default('development'),
  PORT: Joi.number().default(3000),
  DATABASE_URL: Joi.string().required(),
  JWT_SECRET: Joi.string().required(),
  JWT_EXPIRES_IN: Joi.string().default('1h'),
  ALLOWED_ORIGINS: Joi.string().default('http://localhost:3000'),
});
```

```typescript
// app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { validationSchema } from './config/app.config';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      validationSchema,
    }),
  ],
})
export class AppModule {}
```

---

## 모듈 (Module)

기능별로 모듈을 분리하고, `exports`로 다른 모듈에 서비스를 공개합니다:

```typescript
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ProjectController } from './project.controller';
import { ProjectService } from './project.service';
import { ProjectRepository } from './project.repository';
import { ProjectEntity } from './entities/project.entity';

@Module({
  imports: [TypeOrmModule.forFeature([ProjectEntity])],
  controllers: [ProjectController],
  providers: [ProjectService, ProjectRepository],
  exports: [ProjectService],
})
export class ProjectModule {}
```

---

## 컨트롤러 (Controller)

HTTP 요청/응답 처리만 담당합니다. Swagger 데코레이터로 API를 문서화합니다:

```typescript
import {
  Controller, Get, Post, Patch, Delete,
  Param, Body, Query, ParseUUIDPipe, HttpCode, HttpStatus,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { ProjectService } from './project.service';
import { CreateProjectDto } from './dto/create-project.dto';
import { UpdateProjectDto } from './dto/update-project.dto';
import { PaginationQueryDto } from '../../common/dto/pagination.dto';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { Roles } from '../auth/decorators/roles.decorator';
import { UserPayload } from '../auth/interfaces/user-payload.interface';

@ApiTags('Projects')
@ApiBearerAuth()
@Controller('projects')
export class ProjectController {
  constructor(private readonly projectService: ProjectService) {}

  @Get()
  @ApiOperation({ summary: '프로젝트 목록 조회' })
  findAll(@Query() query: PaginationQueryDto) {
    return this.projectService.findAll(query);
  }

  @Get(':id')
  @ApiOperation({ summary: '프로젝트 상세 조회' })
  @ApiResponse({ status: 404, description: 'Project not found' })
  findOne(@Param('id', ParseUUIDPipe) id: string) {
    return this.projectService.findOne(id);
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: '프로젝트 생성' })
  create(
    @Body() dto: CreateProjectDto,
    @CurrentUser() user: UserPayload,
  ) {
    return this.projectService.create(dto, user.id);
  }

  @Patch(':id')
  @ApiOperation({ summary: '프로젝트 수정' })
  update(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateProjectDto,
  ) {
    return this.projectService.update(id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @Roles('admin')
  @ApiOperation({ summary: '프로젝트 삭제 (관리자 전용)' })
  remove(@Param('id', ParseUUIDPipe) id: string) {
    return this.projectService.remove(id);
  }
}
```

---

## 서비스 (Service)

비즈니스 로직을 담당합니다. DB 접근은 Repository에 위임합니다:

```typescript
import { Injectable } from '@nestjs/common';
import { ProjectRepository } from './project.repository';
import { CreateProjectDto } from './dto/create-project.dto';
import { UpdateProjectDto } from './dto/update-project.dto';
import { PaginationQueryDto } from '../../common/dto/pagination.dto';

@Injectable()
export class ProjectService {
  constructor(private readonly projectRepository: ProjectRepository) {}

  findAll(query: PaginationQueryDto) {
    return this.projectRepository.findPaginated(query);
  }

  findOne(id: string) {
    return this.projectRepository.findOneOrFail(id);
  }

  create(dto: CreateProjectDto, userId: string) {
    return this.projectRepository.createProject(dto, userId);
  }

  update(id: string, dto: UpdateProjectDto) {
    return this.projectRepository.updateProject(id, dto);
  }

  remove(id: string) {
    return this.projectRepository.removeProject(id);
  }
}
```

---

## Repository (데이터 액세스)

DB 접근 로직을 캡슐화합니다. 서비스에서 ORM 의존성을 분리합니다:

```typescript
import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, DataSource } from 'typeorm';
import { ProjectEntity } from './entities/project.entity';
import { CreateProjectDto } from './dto/create-project.dto';
import { UpdateProjectDto } from './dto/update-project.dto';
import { PaginationQueryDto } from '../../common/dto/pagination.dto';
import { PaginatedResult } from '../../common/interfaces/paginated-result.interface';

@Injectable()
export class ProjectRepository {
  constructor(
    @InjectRepository(ProjectEntity)
    private readonly repo: Repository<ProjectEntity>,
    private readonly dataSource: DataSource,
  ) {}

  async findPaginated(query: PaginationQueryDto): Promise<PaginatedResult<ProjectEntity>> {
    const { page = 1, limit = 20 } = query;
    const [items, total] = await this.repo.findAndCount({
      skip: (page - 1) * limit,
      take: limit,
      order: { createdAt: 'DESC' },
    });

    return {
      items,
      meta: { total, page, limit, totalPages: Math.ceil(total / limit) },
    };
  }

  async findOneOrFail(id: string): Promise<ProjectEntity> {
    const project = await this.repo.findOne({ where: { id } });
    if (!project) {
      throw new NotFoundException(`Project #${id} not found`);
    }
    return project;
  }

  async createProject(dto: CreateProjectDto, userId: string): Promise<ProjectEntity> {
    const project = this.repo.create({ ...dto, createdBy: userId });
    return this.repo.save(project);
  }

  async updateProject(id: string, dto: UpdateProjectDto): Promise<ProjectEntity> {
    const project = await this.findOneOrFail(id);
    Object.assign(project, dto);
    return this.repo.save(project);
  }

  async removeProject(id: string): Promise<void> {
    const project = await this.findOneOrFail(id);
    await this.repo.remove(project);
  }

  /** 여러 엔티티를 수정하는 경우 트랜잭션을 사용합니다 */
  async transferTasks(fromProjectId: string, toProjectId: string): Promise<void> {
    const queryRunner = this.dataSource.createQueryRunner();
    await queryRunner.connect();
    await queryRunner.startTransaction();

    try {
      await queryRunner.manager.update('task', { projectId: fromProjectId }, { projectId: toProjectId });
      await queryRunner.manager.update('project', { id: fromProjectId }, { status: 'archived' });
      await queryRunner.commitTransaction();
    } catch (error) {
      await queryRunner.rollbackTransaction();
      throw error;
    } finally {
      await queryRunner.release();
    }
  }
}
```

---

## Entity & DTO

### Entity

```typescript
import {
  Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn,
} from 'typeorm';

@Entity('projects')
export class ProjectEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ length: 200 })
  name: string;

  @Column({ type: 'text', nullable: true })
  description: string | null;

  @Column({ type: 'int', default: 1 })
  priority: number;

  @Column({ length: 20, default: 'active' })
  status: string;

  @Column({ name: 'created_by' })
  createdBy: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;
}
```

### Create DTO

`class-validator` + Swagger 데코레이터를 함께 사용합니다:

```typescript
import { IsString, IsOptional, IsInt, Min, Max, MaxLength } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CreateProjectDto {
  @ApiProperty({ example: 'My Project', maxLength: 200 })
  @IsString()
  @MaxLength(200)
  name: string;

  @ApiPropertyOptional({ example: 'Project description' })
  @IsOptional()
  @IsString()
  @MaxLength(2000)
  description?: string;

  @ApiPropertyOptional({ example: 1, minimum: 1, maximum: 100 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  priority?: number;
}
```

### Update DTO

```typescript
import { PartialType } from '@nestjs/swagger';
import { CreateProjectDto } from './create-project.dto';

export class UpdateProjectDto extends PartialType(CreateProjectDto) {}
```

### Pagination DTO & Interface

```typescript
// common/dto/pagination.dto.ts
import { IsOptional, IsInt, Min, Max } from 'class-validator';
import { Type } from 'class-transformer';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class PaginationQueryDto {
  @ApiPropertyOptional({ default: 1, minimum: 1 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number = 1;

  @ApiPropertyOptional({ default: 20, minimum: 1, maximum: 100 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 20;
}

// common/interfaces/paginated-result.interface.ts
export interface PaginatedResult<T> {
  items: T[];
  meta: {
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  };
}
```

---

## 규칙

### 반드시 지킬 것

1. **모듈 기반 co-location**: 관련 파일(controller, service, repository, dto, entity, test)을 모듈 디렉터리에 함께 배치합니다.
2. **레이어 분리**: Controller(HTTP) → Service(비즈니스 로직) → Repository(데이터 액세스)를 명확히 분리합니다.
3. **DTO 검증**: 입력은 `class-validator` + `ValidationPipe`로 검증하고, Swagger 데코레이터를 함께 선언합니다.
4. **환경 설정**: 하드코딩 대신 `ConfigModule` + `Joi` 스키마로 환경 변수를 관리합니다.
5. **인증/인가**: Guard + 커스텀 데코레이터로 처리하며, 컨트롤러나 서비스에 인증 로직을 넣지 않습니다.
6. **트랜잭션**: 여러 엔티티를 수정하는 작업은 반드시 트랜잭션을 사용합니다.
7. **에러 처리**: NestJS 내장 예외를 활용하고, 전역 필터로 일관된 응답 포맷을 유지합니다.

### 하지 말 것

1. **컨트롤러에 비즈니스 로직 작성**: 컨트롤러는 요청/응답 변환만 담당합니다.
2. **서비스에서 ORM 직접 사용**: Repository를 통해 접근하여 데이터 액세스를 캡슐화합니다.
3. **`enableCors()` 무인자 호출**: 반드시 origin whitelist를 지정합니다.
4. **포트/시크릿 하드코딩**: 모든 설정은 환경 변수로 관리합니다.
5. **`findAll()` 전체 조회**: 반드시 페이지네이션을 적용합니다.
6. **프로덕션에서 내부 에러 메시지 노출**: 5xx 에러는 일반 메시지만 반환합니다.
7. **`as any` 타입 캐스팅**: 적절한 타입 가드나 인터페이스를 정의합니다.
