import { Test, TestingModule } from '@nestjs/testing';
import { UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { AuthService } from './auth.service';
import { PrismaService } from '../../database/prisma.service';
import { createMockPrismaService } from '../../database/prisma.service.mock';
import { UserRole, UserStatus } from '@prisma/client';

describe('AuthService', () => {
  let service: AuthService;
  let prisma: ReturnType<typeof createMockPrismaService>;
  let jwtService: jest.Mocked<Partial<JwtService>>;

  const mockUser = {
    id: 'user-1',
    username: 'admin',
    passwordHash: '$2a$10$hashedpassword',
    realName: '管理员',
    role: UserRole.SUPER_ADMIN,
    status: UserStatus.ACTIVE,
    avatar: null,
  };

  beforeEach(async () => {
    prisma = createMockPrismaService();
    jwtService = {
      sign: jest.fn().mockReturnValue('mock-token'),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AuthService,
        { provide: PrismaService, useValue: prisma },
        { provide: JwtService, useValue: jwtService },
        { provide: ConfigService, useValue: { get: jest.fn().mockReturnValue('7d') } },
      ],
    }).compile();

    service = module.get<AuthService>(AuthService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('validateUser', () => {
    it('should return user when credentials are valid', async () => {
      prisma.user.findUnique.mockResolvedValue(mockUser as any);
      jest.spyOn(require('bcryptjs'), 'compare').mockResolvedValue(true);

      const result = await service.validateUser('admin', 'admin123');

      expect(prisma.user.findUnique).toHaveBeenCalledWith({ where: { username: 'admin' } });
      expect(result).toEqual(mockUser);
    });

    it('should return null when user not found', async () => {
      prisma.user.findUnique.mockResolvedValue(null);

      const result = await service.validateUser('unknown', 'password');

      expect(result).toBeNull();
    });

    it('should return null when password does not match', async () => {
      prisma.user.findUnique.mockResolvedValue(mockUser as any);
      jest.spyOn(require('bcryptjs'), 'compare').mockResolvedValue(false);

      const result = await service.validateUser('admin', 'wrongpassword');

      expect(result).toBeNull();
    });
  });

  describe('login', () => {
    it('should throw UnauthorizedException when user not found', async () => {
      prisma.user.findUnique.mockResolvedValue(null);

      await expect(service.login('unknown', 'password')).rejects.toThrow(UnauthorizedException);
    });

    it('should return tokens and user info when login succeeds', async () => {
      prisma.user.findUnique.mockResolvedValue(mockUser as any);
      jest.spyOn(require('bcryptjs'), 'compare').mockResolvedValue(true);

      const result = await service.login('admin', 'admin123');

      expect(jwtService.sign).toHaveBeenCalledTimes(2);
      expect(result).toEqual({
        accessToken: 'mock-token',
        refreshToken: 'mock-token',
        user: {
          id: mockUser.id,
          username: mockUser.username,
          realName: mockUser.realName,
          role: mockUser.role,
          avatar: mockUser.avatar,
        },
      });
    });
  });

  describe('refresh', () => {
    it('should throw UnauthorizedException when user not found', async () => {
      prisma.user.findUnique.mockResolvedValue(null);

      await expect(service.refresh('user-1')).rejects.toThrow(UnauthorizedException);
    });

    it('should throw UnauthorizedException when user is inactive', async () => {
      prisma.user.findUnique.mockResolvedValue({ ...mockUser, status: UserStatus.INACTIVE } as any);

      await expect(service.refresh('user-1')).rejects.toThrow(UnauthorizedException);
    });

    it('should return new access token when user is active', async () => {
      prisma.user.findUnique.mockResolvedValue(mockUser as any);

      const result = await service.refresh('user-1');

      expect(jwtService.sign).toHaveBeenCalledWith({ sub: mockUser.id, username: mockUser.username });
      expect(result).toEqual({ accessToken: 'mock-token' });
    });
  });
});
