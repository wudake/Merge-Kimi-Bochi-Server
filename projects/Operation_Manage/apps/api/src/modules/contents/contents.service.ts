import { Injectable, NotFoundException } from '@nestjs/common';
import { ContentStatus } from '@prisma/client';
import { PrismaService } from '../../database/prisma.service';
import { CreateContentDto, UpdateContentDto, UpdateContentStatusDto } from './dto';

@Injectable()
export class ContentsService {
  constructor(private prisma: PrismaService) {}

  async create(dto: CreateContentDto) {
    const data: any = { ...dto };
    if (dto.accountIds) {
      data.accounts = { connect: dto.accountIds.map((id) => ({ id })) };
      delete data.accountIds;
    }
    if (dto.plannedPublishAt) {
      data.plannedPublishAt = new Date(dto.plannedPublishAt);
    }
    return this.prisma.content.create({
      data,
      include: {
        topic: { select: { id: true, title: true } },
        operator: { select: { id: true, realName: true } },
        accounts: { select: { id: true, name: true, platform: true } },
      },
    });
  }

  async findAll(params: {
    status?: string;
    operatorId?: string;
    accountId?: string;
    search?: string;
    startDate?: string;
    endDate?: string;
  }) {
    const where: any = {};
    if (params.status) where.status = params.status;
    if (params.operatorId) where.operatorId = params.operatorId;
    if (params.accountId) {
      where.accounts = { some: { id: params.accountId } };
    }
    if (params.search) {
      where.title = { contains: params.search, mode: 'insensitive' };
    }
    if (params.startDate || params.endDate) {
      where.plannedPublishAt = {};
      if (params.startDate) where.plannedPublishAt.gte = new Date(params.startDate);
      if (params.endDate) where.plannedPublishAt.lte = new Date(params.endDate);
    }

    return this.prisma.content.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      include: {
        topic: { select: { id: true, title: true } },
        operator: { select: { id: true, realName: true } },
        accounts: { select: { id: true, name: true, platform: true } },
        _count: { select: { contentData: true, leads: true } },
      },
    });
  }

  async findCalendar(params: { startDate: string; endDate: string; operatorId?: string; accountId?: string }) {
    const where: any = {
      plannedPublishAt: {
        gte: new Date(params.startDate),
        lte: new Date(params.endDate),
      },
    };
    if (params.operatorId) where.operatorId = params.operatorId;
    if (params.accountId) {
      where.accounts = { some: { id: params.accountId } };
    }

    return this.prisma.content.findMany({
      where,
      orderBy: { plannedPublishAt: 'asc' },
      include: {
        topic: { select: { id: true, title: true } },
        operator: { select: { id: true, realName: true } },
        accounts: { select: { id: true, name: true, platform: true } },
      },
    });
  }

  async findOne(id: string) {
    const content = await this.prisma.content.findUnique({
      where: { id },
      include: {
        topic: { select: { id: true, title: true } },
        operator: { select: { id: true, realName: true } },
        accounts: { select: { id: true, name: true, platform: true } },
        comments: {
          include: { user: { select: { id: true, realName: true, avatar: true } } },
          orderBy: { createdAt: 'asc' },
        },
        contentData: {
          include: { account: { select: { id: true, name: true, platform: true } } },
        },
      },
    });
    if (!content) throw new NotFoundException('内容不存在');
    return content;
  }

  async update(id: string, dto: UpdateContentDto) {
    await this.findOne(id);
    const data: any = { ...dto };
    if (dto.accountIds) {
      data.accounts = { set: dto.accountIds.map((id) => ({ id })) };
      delete data.accountIds;
    }
    if (dto.plannedPublishAt) {
      data.plannedPublishAt = new Date(dto.plannedPublishAt);
    }
    if (dto.actualPublishAt) {
      data.actualPublishAt = new Date(dto.actualPublishAt);
    }

    // Update topic usage count if status changes to PUBLISHED
    if (dto.status === 'PUBLISHED') {
      const content = await this.prisma.content.findUnique({ where: { id }, select: { topicId: true } });
      if (content?.topicId) {
        await this.prisma.topic.update({
          where: { id: content.topicId },
          data: { status: 'USED', usageCount: { increment: 1 } },
        });
      }
    }

    return this.prisma.content.update({
      where: { id },
      data,
      include: {
        topic: { select: { id: true, title: true } },
        operator: { select: { id: true, realName: true } },
        accounts: { select: { id: true, name: true, platform: true } },
      },
    });
  }

  async updateStatus(id: string, dto: UpdateContentStatusDto) {
    return this.update(id, { status: dto.status });
  }

  async remove(id: string) {
    await this.findOne(id);
    return this.prisma.content.delete({ where: { id } });
  }

  async batchCreate(dto: { items: CreateContentDto[] }) {
    const results = [];
    for (const item of dto.items) {
      results.push(await this.create(item));
    }
    return results;
  }

  async batchAssign(contentIds: string[], operatorId: string) {
    return this.prisma.content.updateMany({
      where: { id: { in: contentIds } },
      data: { operatorId },
    });
  }

  async batchUpdatePublishTime(contentIds: string[], plannedPublishAt: string) {
    return this.prisma.content.updateMany({
      where: { id: { in: contentIds } },
      data: { plannedPublishAt: new Date(plannedPublishAt) },
    });
  }
}
