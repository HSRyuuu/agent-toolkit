# NestJS 테스트 패턴

## 서비스 단위 테스트

`Test.createTestingModule()`로 의존성을 모킹하여 서비스를 격리 테스트합니다:

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException } from '@nestjs/common';
import { ProjectService } from '../project.service';
import { ProjectRepository } from '../project.repository';

describe('ProjectService', () => {
  let service: ProjectService;
  let repository: jest.Mocked<ProjectRepository>;

  beforeEach(async () => {
    const mockRepository = {
      findPaginated: jest.fn(),
      findOneOrFail: jest.fn(),
      createProject: jest.fn(),
      updateProject: jest.fn(),
      removeProject: jest.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        ProjectService,
        { provide: ProjectRepository, useValue: mockRepository },
      ],
    }).compile();

    service = module.get(ProjectService);
    repository = module.get(ProjectRepository);
  });

  describe('findOne', () => {
    it('존재하는 프로젝트를 반환한다', async () => {
      const project = { id: '1', name: 'Test' };
      repository.findOneOrFail.mockResolvedValue(project as any);

      const result = await service.findOne('1');
      expect(result).toEqual(project);
      expect(repository.findOneOrFail).toHaveBeenCalledWith('1');
    });

    it('존재하지 않는 프로젝트는 NotFoundException을 던진다', async () => {
      repository.findOneOrFail.mockRejectedValue(new NotFoundException());

      await expect(service.findOne('999')).rejects.toThrow(NotFoundException);
    });
  });

  describe('create', () => {
    it('프로젝트를 생성하고 반환한다', async () => {
      const dto = { name: 'New Project' };
      const created = { id: '1', ...dto, createdBy: 'user-1' };
      repository.createProject.mockResolvedValue(created as any);

      const result = await service.create(dto as any, 'user-1');
      expect(result).toEqual(created);
      expect(repository.createProject).toHaveBeenCalledWith(dto, 'user-1');
    });
  });
});
```

---

## 컨트롤러 E2E 테스트

실제 모듈을 로드하여 HTTP 요청/응답을 통합 테스트합니다:

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../../app.module';

describe('ProjectController (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = module.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: true,
    }));
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  describe('POST /api/projects', () => {
    it('유효한 데이터로 프로젝트를 생성한다', () => {
      return request(app.getHttpServer())
        .post('/api/projects')
        .send({ name: 'New Project', priority: 1 })
        .expect(201)
        .expect((res) => {
          expect(res.body).toHaveProperty('id');
          expect(res.body.name).toBe('New Project');
        });
    });

    it('name이 없으면 400을 반환한다', () => {
      return request(app.getHttpServer())
        .post('/api/projects')
        .send({ priority: 1 })
        .expect(400);
    });

    it('허용되지 않은 필드가 있으면 400을 반환한다', () => {
      return request(app.getHttpServer())
        .post('/api/projects')
        .send({ name: 'Test', hackField: 'malicious' })
        .expect(400);
    });
  });

  describe('GET /api/projects', () => {
    it('페이지네이션된 목록을 반환한다', () => {
      return request(app.getHttpServer())
        .get('/api/projects?page=1&limit=10')
        .expect(200)
        .expect((res) => {
          expect(res.body).toHaveProperty('items');
          expect(res.body).toHaveProperty('meta');
          expect(res.body.meta).toHaveProperty('total');
          expect(res.body.meta).toHaveProperty('totalPages');
        });
    });
  });
});
```

---

## 테스트 구성 규칙

1. **테스트 파일 위치**: 모듈 디렉터리 내 `__tests__/` 폴더에 배치합니다.
2. **네이밍**: `*.spec.ts` (단위), `*.e2e-spec.ts` (E2E).
3. **모킹**: 외부 의존성(Repository, 외부 API)은 반드시 모킹합니다.
4. **격리**: 각 테스트는 독립적으로 실행 가능해야 합니다.
5. **ValidationPipe**: E2E 테스트에서도 프로덕션과 동일한 파이프 설정을 적용합니다.
