import { Test, TestingModule } from '@nestjs/testing';
import { AccountsController } from './accounts.controller';
import { AccountsService } from './accounts.service';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { RolesGuard } from '../../common/guards/roles.guard';

describe('AccountsController', () => {
  let controller: AccountsController;
  let accountsService: jest.Mocked<Partial<AccountsService>>;

  const mockAccount = {
    id: 'acc-1',
    platform: 'FACEBOOK',
    name: 'Test',
    status: 'ACTIVE',
    createdAt: new Date(),
  };

  beforeEach(async () => {
    accountsService = {
      create: jest.fn().mockResolvedValue(mockAccount),
      findAll: jest.fn().mockResolvedValue([mockAccount]),
      findOne: jest.fn().mockResolvedValue(mockAccount),
      update: jest.fn().mockResolvedValue(mockAccount),
      remove: jest.fn().mockResolvedValue(mockAccount),
      transfer: jest.fn().mockResolvedValue(mockAccount),
      findAllGroups: jest.fn().mockResolvedValue([{ id: 'g1', name: 'Group1' }]),
      createGroup: jest.fn().mockResolvedValue({ id: 'g1', name: 'Group1' }),
      updateGroup: jest.fn().mockResolvedValue({ id: 'g1', name: 'Updated' }),
      removeGroup: jest.fn().mockResolvedValue({ id: 'g1' }),
    };

    const module: TestingModule = await Test.createTestingModule({
      controllers: [AccountsController],
      providers: [{ provide: AccountsService, useValue: accountsService }],
    })
      .overrideGuard(JwtAuthGuard)
      .useValue({ canActivate: () => true })
      .overrideGuard(RolesGuard)
      .useValue({ canActivate: () => true })
      .compile();

    controller = module.get<AccountsController>(AccountsController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('create', () => {
    it('should create account', async () => {
      const dto = { name: 'Test', platform: 'FACEBOOK' };
      const result = await controller.create(dto as any);
      expect(accountsService.create).toHaveBeenCalledWith(dto);
      expect(result).toEqual(mockAccount);
    });
  });

  describe('findAll', () => {
    it('should return accounts with query params', async () => {
      const result = await controller.findAll('FACEBOOK', 'ACTIVE', undefined, 'Test');
      expect(accountsService.findAll).toHaveBeenCalledWith({ platform: 'FACEBOOK', status: 'ACTIVE', groupId: undefined, search: 'Test' });
      expect(result).toEqual([mockAccount]);
    });
  });

  describe('findOne', () => {
    it('should return account by id', async () => {
      const result = await controller.findOne('acc-1');
      expect(accountsService.findOne).toHaveBeenCalledWith('acc-1');
      expect(result).toEqual(mockAccount);
    });
  });

  describe('update', () => {
    it('should update account', async () => {
      const dto = { name: 'Updated' };
      const result = await controller.update('acc-1', dto as any);
      expect(accountsService.update).toHaveBeenCalledWith('acc-1', dto);
    });
  });

  describe('remove', () => {
    it('should delete account', async () => {
      const result = await controller.remove('acc-1');
      expect(accountsService.remove).toHaveBeenCalledWith('acc-1');
    });
  });

  describe('transfer', () => {
    it('should transfer account', async () => {
      const result = await controller.transfer('acc-1', ['user-2']);
      expect(accountsService.transfer).toHaveBeenCalledWith('acc-1', ['user-2']);
    });
  });

  describe('findAllGroups', () => {
    it('should return all groups', async () => {
      const result = await controller.findAllGroups();
      expect(accountsService.findAllGroups).toHaveBeenCalled();
    });
  });
});