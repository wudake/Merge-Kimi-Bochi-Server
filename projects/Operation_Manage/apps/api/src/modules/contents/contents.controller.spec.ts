import { Test, TestingModule } from '@nestjs/testing';
import { ContentsController } from './contents.controller';
import { ContentsService } from './contents.service';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { RolesGuard } from '../../common/guards/roles.guard';

describe('ContentsController', () => {
  let controller: ContentsController;
  let contentsService: jest.Mocked<Partial<ContentsService>>;

  const mockContent = {
    id: 'content-1',
    title: 'Test Content',
    status: 'PENDING',
    createdAt: new Date(),
  };

  beforeEach(async () => {
    contentsService = {
      create: jest.fn().mockResolvedValue(mockContent),
      findAll: jest.fn().mockResolvedValue([mockContent]),
      findCalendar: jest.fn().mockResolvedValue([mockContent]),
      findOne: jest.fn().mockResolvedValue(mockContent),
      update: jest.fn().mockResolvedValue(mockContent),
      updateStatus: jest.fn().mockResolvedValue(mockContent),
      remove: jest.fn().mockResolvedValue(mockContent),
      batchCreate: jest.fn().mockResolvedValue([mockContent]),
      batchAssign: jest.fn().mockResolvedValue({ count: 2 }),
    };

    const module: TestingModule = await Test.createTestingModule({
      controllers: [ContentsController],
      providers: [{ provide: ContentsService, useValue: contentsService }],
    })
      .overrideGuard(JwtAuthGuard)
      .useValue({ canActivate: () => true })
      .overrideGuard(RolesGuard)
      .useValue({ canActivate: () => true })
      .compile();

    controller = module.get<ContentsController>(ContentsController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('create', () => {
    it('should create content', async () => {
      const dto = { title: 'New' };
      const result = await controller.create(dto as any);
      expect(contentsService.create).toHaveBeenCalledWith(dto);
      expect(result).toEqual(mockContent);
    });
  });

  describe('findAll', () => {
    it('should return contents with query params', async () => {
      const result = await controller.findAll('PENDING', 'user-1', 'acc-1', 'Test');
      expect(contentsService.findAll).toHaveBeenCalledWith({
        status: 'PENDING', operatorId: 'user-1', accountId: 'acc-1', search: 'Test',
      });
    });
  });

  describe('findCalendar', () => {
    it('should return calendar data', async () => {
      const result = await controller.findCalendar('2026-04-01', '2026-04-07', 'user-1');
      expect(contentsService.findCalendar).toHaveBeenCalledWith({
        startDate: '2026-04-01', endDate: '2026-04-07', operatorId: 'user-1',
      });
    });
  });

  describe('findOne', () => {
    it('should return content by id', async () => {
      const result = await controller.findOne('content-1');
      expect(contentsService.findOne).toHaveBeenCalledWith('content-1');
    });
  });

  describe('update', () => {
    it('should update content', async () => {
      const dto = { title: 'Updated' };
      const result = await controller.update('content-1', dto as any);
      expect(contentsService.update).toHaveBeenCalledWith('content-1', dto);
    });
  });

  describe('updateStatus', () => {
    it('should update content status', async () => {
      const dto = { status: 'PUBLISHED' };
      const result = await controller.updateStatus('content-1', dto as any);
      expect(contentsService.updateStatus).toHaveBeenCalledWith('content-1', dto);
    });
  });

  describe('remove', () => {
    it('should delete content', async () => {
      const result = await controller.remove('content-1');
      expect(contentsService.remove).toHaveBeenCalledWith('content-1');
    });
  });

  describe('batchCreate', () => {
    it('should batch create contents', async () => {
      const dto = { items: [{ title: 'A' }] };
      const result = await controller.batchCreate(dto as any);
      expect(contentsService.batchCreate).toHaveBeenCalledWith(dto);
    });
  });

  describe('batchAssign', () => {
    it('should batch assign operator', async () => {
      const result = await controller.batchAssign(['c1', 'c2'], 'user-1');
      expect(contentsService.batchAssign).toHaveBeenCalledWith(['c1', 'c2'], 'user-1');
    });
  });
});