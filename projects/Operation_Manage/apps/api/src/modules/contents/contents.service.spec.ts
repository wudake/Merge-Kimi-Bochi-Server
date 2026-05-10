import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException } from '@nestjs/common';
import { ContentsService } from './contents.service';
import { PrismaService } from '../../database/prisma.service';
import { createMockPrismaService } from '../../database/prisma.service.mock';
import { ContentStatus } from '@prisma/client';

describe('ContentsService', () => {
  let service: ContentsService;
  let prisma: ReturnType<typeof createMockPrismaService>;

  const mockContent = {
    id: 'content-1',
    title: 'Test Content',
    status: ContentStatus.PENDING,
    plannedPublishAt: new Date(),
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  beforeEach(async () => {
    prisma = createMockPrismaService();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        ContentsService,
        { provide: PrismaService, useValue: prisma },
      ],
    }).compile();

    service = module.get<ContentsService>(ContentsService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('create', () => {
    it('should create content with account connections', async () => {
      const dto = { title: 'New', accountIds: ['acc-1', 'acc-2'] };
      prisma.content.create.mockResolvedValue(mockContent as any);

      const result = await service.create(dto as any);

      expect(prisma.content.create).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            title: 'New',
            accounts: { connect: [{ id: 'acc-1' }, { id: 'acc-2' }] },
          }),
          include: expect.anything(),
        }),
      );
      expect(result).toEqual(mockContent);
    });
  });

  describe('findAll', () => {
    it('should return contents with filters', async () => {
      prisma.content.findMany.mockResolvedValue([mockContent] as any);

      const result = await service.findAll({ status: 'PENDING', search: 'Test' });

      expect(prisma.content.findMany).toHaveBeenCalled();
      expect(result).toHaveLength(1);
    });
  });

  describe('findCalendar', () => {
    it('should return contents within date range', async () => {
      prisma.content.findMany.mockResolvedValue([mockContent] as any);

      const result = await service.findCalendar({ startDate: '2026-04-01', endDate: '2026-04-07' });

      expect(prisma.content.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            plannedPublishAt: {
              gte: new Date('2026-04-01'),
              lte: new Date('2026-04-07'),
            },
          }),
        }),
      );
    });
  });

  describe('findOne', () => {
    it('should return content by id', async () => {
      prisma.content.findUnique.mockResolvedValue(mockContent as any);

      const result = await service.findOne('content-1');

      expect(prisma.content.findUnique).toHaveBeenCalledWith(
        expect.objectContaining({ where: { id: 'content-1' } }),
      );
      expect(result).toEqual(mockContent);
    });

    it('should throw NotFoundException when content not found', async () => {
      prisma.content.findUnique.mockResolvedValue(null);

      await expect(service.findOne('unknown')).rejects.toThrow(NotFoundException);
    });
  });

  describe('update', () => {
    it('should update content status and topic usage', async () => {
      prisma.content.findUnique.mockResolvedValue({ ...mockContent, topicId: 'topic-1' } as any);
      prisma.content.update.mockResolvedValue(mockContent as any);
      prisma.topic.update.mockResolvedValue({} as any);

      const result = await service.update('content-1', { status: 'PUBLISHED' } as any);

      expect(prisma.topic.update).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({ status: 'USED', usageCount: { increment: 1 } }),
        }),
      );
    });

    it('should throw NotFoundException when content not found', async () => {
      prisma.content.findUnique.mockResolvedValue(null);

      await expect(service.update('unknown', {} as any)).rejects.toThrow(NotFoundException);
    });
  });

  describe('updateStatus', () => {
    it('should delegate to update', async () => {
      prisma.content.findUnique.mockResolvedValue({ ...mockContent, topicId: null } as any);
      prisma.content.update.mockResolvedValue(mockContent as any);

      const result = await service.updateStatus('content-1', { status: ContentStatus.PUBLISHED } as any);

      expect(prisma.content.update).toHaveBeenCalled();
    });
  });

  describe('remove', () => {
    it('should delete content', async () => {
      prisma.content.findUnique.mockResolvedValue(mockContent as any);
      prisma.content.delete.mockResolvedValue(mockContent as any);

      const result = await service.remove('content-1');

      expect(prisma.content.delete).toHaveBeenCalledWith({ where: { id: 'content-1' } });
    });
  });

  describe('batchCreate', () => {
    it('should create multiple contents', async () => {
      prisma.content.create.mockResolvedValue(mockContent as any);

      const result = await service.batchCreate({ items: [{ title: 'A' }, { title: 'B' }] as any });

      expect(prisma.content.create).toHaveBeenCalledTimes(2);
      expect(result).toHaveLength(2);
    });
  });

  describe('batchAssign', () => {
    it('should assign operator to multiple contents', async () => {
      prisma.content.updateMany.mockResolvedValue({ count: 2 } as any);

      const result = await service.batchAssign(['c1', 'c2'], 'user-1');

      expect(prisma.content.updateMany).toHaveBeenCalledWith({
        where: { id: { in: ['c1', 'c2'] } },
        data: { operatorId: 'user-1' },
      });
    });
  });
});