import { Test, TestingModule } from '@nestjs/testing';
import { TopicsController } from './topics.controller';
import { TopicsService } from './topics.service';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';

describe('TopicsController', () => {
  let controller: TopicsController;
  let topicsService: jest.Mocked<Partial<TopicsService>>;

  const mockTopic = {
    id: 'topic-1',
    title: 'Test Topic',
    contentForm: 'SHORT_VIDEO',
    status: 'PENDING',
    createdAt: new Date(),
  };

  beforeEach(async () => {
    topicsService = {
      create: jest.fn().mockResolvedValue(mockTopic),
      findAll: jest.fn().mockResolvedValue([mockTopic]),
      findOne: jest.fn().mockResolvedValue(mockTopic),
      update: jest.fn().mockResolvedValue(mockTopic),
      remove: jest.fn().mockResolvedValue(mockTopic),
    };

    const module: TestingModule = await Test.createTestingModule({
      controllers: [TopicsController],
      providers: [{ provide: TopicsService, useValue: topicsService }],
    })
      .overrideGuard(JwtAuthGuard)
      .useValue({ canActivate: () => true })
      .compile();

    controller = module.get<TopicsController>(TopicsController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('create', () => {
    it('should create topic with current user', async () => {
      const dto = { title: 'New', contentForm: 'SHORT_VIDEO' };
      const result = await controller.create(dto as any, 'user-1');

      expect(topicsService.create).toHaveBeenCalledWith('user-1', dto);
      expect(result).toEqual(mockTopic);
    });
  });

  describe('findAll', () => {
    it('should return topics with query params', async () => {
      const result = await controller.findAll('PENDING', 'factory_tour', 'aluminum');

      expect(topicsService.findAll).toHaveBeenCalledWith({
        status: 'PENDING',
        contentType: 'factory_tour',
        search: 'aluminum',
      });
      expect(result).toEqual([mockTopic]);
    });
  });

  describe('findOne', () => {
    it('should return topic by id', async () => {
      const result = await controller.findOne('topic-1');
      expect(topicsService.findOne).toHaveBeenCalledWith('topic-1');
    });
  });

  describe('update', () => {
    it('should update topic', async () => {
      const dto = { title: 'Updated' };
      const result = await controller.update('topic-1', dto as any);
      expect(topicsService.update).toHaveBeenCalledWith('topic-1', dto);
    });
  });

  describe('remove', () => {
    it('should delete topic', async () => {
      const result = await controller.remove('topic-1');
      expect(topicsService.remove).toHaveBeenCalledWith('topic-1');
    });
  });
});