import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../../database/prisma.service';
import { CreateAccountDto, UpdateAccountDto, CreateAccountGroupDto, UpdateAccountGroupDto } from './dto';

@Injectable()
export class AccountsService {
  constructor(private prisma: PrismaService) {}

  async create(dto: CreateAccountDto) {
    const data: any = { ...dto };
    if (dto.operatorIds) {
      data.operators = { connect: dto.operatorIds.map((id) => ({ id })) };
      delete data.operatorIds;
    }
    return this.prisma.account.create({
      data,
      include: { group: true, operators: { select: { id: true, realName: true } } },
    });
  }

  async findAll(params: { platform?: string; status?: string; groupId?: string; search?: string }) {
    const where: any = {};
    if (params.platform) where.platform = params.platform;
    if (params.status) where.status = params.status;
    if (params.groupId) where.groupId = params.groupId;
    if (params.search) {
      where.OR = [
        { name: { contains: params.search, mode: 'insensitive' } },
        { accountId: { contains: params.search, mode: 'insensitive' } },
      ];
    }

    return this.prisma.account.findMany({
      where,
      include: {
        group: true,
        operators: { select: { id: true, realName: true, username: true } },
        _count: { select: { contents: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async findOne(id: string) {
    const account = await this.prisma.account.findUnique({
      where: { id },
      include: {
        group: true,
        operators: { select: { id: true, realName: true, username: true } },
        contents: { take: 10, orderBy: { createdAt: 'desc' } },
      },
    });
    if (!account) throw new NotFoundException('账号不存在');
    return account;
  }

  async update(id: string, dto: UpdateAccountDto) {
    await this.findOne(id);
    const data: any = { ...dto };
    if (dto.operatorIds) {
      data.operators = { set: dto.operatorIds.map((id) => ({ id })) };
      delete data.operatorIds;
    }
    return this.prisma.account.update({
      where: { id },
      data,
      include: { group: true, operators: { select: { id: true, realName: true } } },
    });
  }

  async remove(id: string) {
    await this.findOne(id);
    return this.prisma.account.delete({ where: { id } });
  }

  async transfer(id: string, newOperatorIds: string[]) {
    await this.findOne(id);
    return this.prisma.account.update({
      where: { id },
      data: {
        operators: { set: newOperatorIds.map((id) => ({ id })) },
      },
      include: { operators: { select: { id: true, realName: true } } },
    });
  }

  // Account Groups
  async createGroup(dto: CreateAccountGroupDto) {
    return this.prisma.accountGroup.create({ data: dto });
  }

  async findAllGroups() {
    return this.prisma.accountGroup.findMany({
      include: { _count: { select: { accounts: true } } },
      orderBy: { createdAt: 'desc' },
    });
  }

  async updateGroup(id: string, dto: UpdateAccountGroupDto) {
    return this.prisma.accountGroup.update({ where: { id }, data: dto });
  }

  async removeGroup(id: string) {
    return this.prisma.accountGroup.delete({ where: { id } });
  }
}
