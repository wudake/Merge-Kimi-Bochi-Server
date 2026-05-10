import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../../database/prisma.service';
import { CreateTopicDto, UpdateTopicDto } from './dto';

@Injectable()
export class TopicsService {
  constructor(private prisma: PrismaService) {}

  async create(userId: string, dto: CreateTopicDto) {
    const data: any = { ...dto, contentForm: 'SHORT_VIDEO', createdBy: userId };
    if (data.completedAt) data.completedAt = new Date(data.completedAt);
    return this.prisma.topic.create({ data });
  }

  async findAll(params: {
    status?: string;
    contentType?: string;
    search?: string;
    sortBy?: string;
  }) {
    const where: any = {};
    if (params.status) where.status = params.status;
    if (params.contentType) where.contentType = params.contentType;
    if (params.search) {
      where.OR = [
        { title: { contains: params.search, mode: 'insensitive' } },
        { tags: { has: params.search } },
      ];
    }

    const orderBy: any = {};
    if (params.sortBy === 'usage') {
      orderBy.usageCount = 'desc';
    } else {
      orderBy.createdAt = 'desc';
    }

    return this.prisma.topic.findMany({
      where,
      orderBy,
      include: {
        creator: { select: { id: true, realName: true } },
        _count: { select: { contents: true } },
      },
    });
  }

  async findOne(id: string) {
    const topic = await this.prisma.topic.findUnique({
      where: { id },
      include: {
        creator: { select: { id: true, realName: true } },
        contents: {
          select: {
            id: true,
            title: true,
            status: true,
            createdAt: true,
            operator: { select: { id: true, realName: true } },
          },
        },
      },
    });
    if (!topic) throw new NotFoundException('选题不存在');
    return topic;
  }

  async update(id: string, dto: UpdateTopicDto) {
    await this.findOne(id);
    const data: any = { ...dto };
    if (data.completedAt) data.completedAt = new Date(data.completedAt);
    return this.prisma.topic.update({ where: { id }, data });
  }

  async remove(id: string) {
    await this.findOne(id);
    return this.prisma.topic.delete({ where: { id } });
  }
}
