import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException } from '@nestjs/common';
import { TopicsService } from './topics.service';
import { PrismaService } from '../../database/prisma.service';
import { createMockPrismaService } from '../../database/prisma.service.mock';
import { ContentForm, TopicStatus } from '@prisma/client';

describe('TopicsService', () => {
  let service: TopicsService;
  let prisma: ReturnType<typeof createMockPrismaService>;

  const mockTopic = {
    id: 'topic-1',
    title: 'How Are Aluminum Windows Made?',
    contentForm: ContentForm.SHORT_VIDEO,
    tags: ['factory', 'aluminum'],
    contentType: 'factory_tour',
    status: TopicStatus.PENDING,
    isCompleted: false,
    usageCount: 0,
    remark: '备注',
    createdBy: 'user-1',
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  beforeEach(async () => {
    prisma = createMockPrismaService();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        TopicsService,
        { provide: PrismaService, useValue: prisma },
      ],
    }).compile();

    service = module.get<TopicsService>(TopicsService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('create', () => {
    it('should create topic with userId and default contentForm', async () => {
      const dto = { title: 'New Topic' };
      prisma.topic.create.mockResolvedValue(mockTopic as any);

      const result = await service.create('user-1', dto as any);

      expect(prisma.topic.create).toHaveBeenCalledWith({
        data: { ...dto, contentForm: 'SHORT_VIDEO', createdBy: 'user-1' },
      });
      expect(result).toEqual(mockTopic);
    });
  });

  describe('findAll', () => {
    it('should return topics with filters', async () => {
      prisma.topic.findMany.mockResolvedValue([mockTopic] as any);

      const result = await service.findAll({ status: 'PENDING', contentType: 'factory_tour', search: 'aluminum' });

      expect(prisma.topic.findMany).toHaveBeenCalled();
      expect(result).toHaveLength(1);
    });

    it('should sort by usage count when sortBy is usage', async () => {
      prisma.topic.findMany.mockResolvedValue([mockTopic] as any);

      await service.findAll({ sortBy: 'usage' });

      expect(prisma.topic.findMany).toHaveBeenCalledWith(
        expect.objectContaining({ orderBy: { usageCount: 'desc' } }),
      );
    });
  });

  describe('findOne', () => {
    it('should return topic by id', async () => {
      prisma.topic.findUnique.mockResolvedValue(mockTopic as any);

      const result = await service.findOne('topic-1');

      expect(prisma.topic.findUnique).toHaveBeenCalledWith(
        expect.objectContaining({ where: { id: 'topic-1' } }),
      );
      expect(result).toEqual(mockTopic);
    });

    it('should throw NotFoundException when topic not found', async () => {
      prisma.topic.findUnique.mockResolvedValue(null);

      await expect(service.findOne('unknown')).rejects.toThrow(NotFoundException);
    });
  });

  describe('update', () => {
    it('should update topic', async () => {
      prisma.topic.findUnique.mockResolvedValue(mockTopic as any);
      prisma.topic.update.mockResolvedValue({ ...mockTopic, title: 'Updated' } as any);

      const result = await service.update('topic-1', { title: 'Updated' } as any);

      expect(prisma.topic.update).toHaveBeenCalledWith({ where: { id: 'topic-1' }, data: { title: 'Updated' } });
      expect(result.title).toBe('Updated');
    });

    it('should throw NotFoundException when topic not found', async () => {
      prisma.topic.findUnique.mockResolvedValue(null);

      await expect(service.update('unknown', {} as any)).rejects.toThrow(NotFoundException);
    });
  });

  describe('remove', () => {
    it('should delete topic', async () => {
      prisma.topic.findUnique.mockResolvedValue(mockTopic as any);
      prisma.topic.delete.mockResolvedValue(mockTopic as any);

      const result = await service.remove('topic-1');

      expect(prisma.topic.delete).toHaveBeenCalledWith({ where: { id: 'topic-1' } });
      expect(result).toEqual(mockTopic);
    });
  });
});