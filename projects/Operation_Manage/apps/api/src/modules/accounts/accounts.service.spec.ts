import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException } from '@nestjs/common';
import { AccountsService } from './accounts.service';
import { PrismaService } from '../../database/prisma.service';
import { createMockPrismaService } from '../../database/prisma.service.mock';
import { AccountStatus, Platform } from '@prisma/client';

describe('AccountsService', () => {
  let service: AccountsService;
  let prisma: ReturnType<typeof createMockPrismaService>;

  const mockAccount = {
    id: 'acc-1',
    platform: Platform.FACEBOOK,
    name: 'Test Account',
    accountType: '主账户',
    loginEmail: 'test@test.com',
    loginPhone: '1234567890',
    loginPassword: 'password',
    status: AccountStatus.ACTIVE,
    followerCount: 100,
    customGroup: '主账号组',
    remark: '备注',
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  beforeEach(async () => {
    prisma = createMockPrismaService();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AccountsService,
        { provide: PrismaService, useValue: prisma },
      ],
    }).compile();

    service = module.get<AccountsService>(AccountsService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('create', () => {
    it('should create account with operators', async () => {
      const dto = { name: 'New', platform: Platform.TIKTOK, operatorIds: ['user-1'] };
      prisma.account.create.mockResolvedValue(mockAccount as any);

      const result = await service.create(dto as any);

      expect(prisma.account.create).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            name: 'New',
            operators: { connect: [{ id: 'user-1' }] },
          }),
          include: expect.anything(),
        }),
      );
      expect(result).toEqual(mockAccount);
    });
  });

  describe('findAll', () => {
    it('should return accounts with filters', async () => {
      prisma.account.findMany.mockResolvedValue([mockAccount] as any);

      const result = await service.findAll({ platform: 'FACEBOOK', status: 'ACTIVE', search: 'Test' });

      expect(prisma.account.findMany).toHaveBeenCalled();
      expect(result).toHaveLength(1);
    });
  });

  describe('findOne', () => {
    it('should return account by id', async () => {
      prisma.account.findUnique.mockResolvedValue(mockAccount as any);

      const result = await service.findOne('acc-1');

      expect(prisma.account.findUnique).toHaveBeenCalledWith(
        expect.objectContaining({ where: { id: 'acc-1' } }),
      );
      expect(result).toEqual(mockAccount);
    });

    it('should throw NotFoundException when account not found', async () => {
      prisma.account.findUnique.mockResolvedValue(null);

      await expect(service.findOne('unknown')).rejects.toThrow(NotFoundException);
    });
  });

  describe('update', () => {
    it('should update account', async () => {
      prisma.account.findUnique.mockResolvedValue(mockAccount as any);
      prisma.account.update.mockResolvedValue({ ...mockAccount, name: 'Updated' } as any);

      const result = await service.update('acc-1', { name: 'Updated' } as any);

      expect(prisma.account.update).toHaveBeenCalled();
      expect(result.name).toBe('Updated');
    });
  });

  describe('remove', () => {
    it('should delete account', async () => {
      prisma.account.findUnique.mockResolvedValue(mockAccount as any);
      prisma.account.delete.mockResolvedValue(mockAccount as any);

      const result = await service.remove('acc-1');

      expect(prisma.account.delete).toHaveBeenCalledWith({ where: { id: 'acc-1' } });
      expect(result).toEqual(mockAccount);
    });
  });

  describe('transfer', () => {
    it('should transfer account to new operators', async () => {
      prisma.account.findUnique.mockResolvedValue(mockAccount as any);
      prisma.account.update.mockResolvedValue(mockAccount as any);

      const result = await service.transfer('acc-1', ['user-2']);

      expect(prisma.account.update).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            operators: { set: [{ id: 'user-2' }] },
          }),
        }),
      );
    });
  });

  describe('findAllGroups', () => {
    it('should return all account groups', async () => {
      prisma.accountGroup.findMany.mockResolvedValue([{ id: 'g1', name: 'Group1' }] as any);

      const result = await service.findAllGroups();

      expect(prisma.accountGroup.findMany).toHaveBeenCalled();
      expect(result).toHaveLength(1);
    });
  });
});