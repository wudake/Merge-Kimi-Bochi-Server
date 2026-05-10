import { Test, TestingModule } from '@nestjs/testing';
import { ConfigService } from '@nestjs/config';
import { AuthController } from './auth.controller';
import { AuthService } from './auth.service';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';

describe('AuthController', () => {
  let controller: AuthController;
  let authService: jest.Mocked<Partial<AuthService>>;

  beforeEach(async () => {
    authService = {
      login: jest.fn().mockResolvedValue({
        accessToken: 'token',
        refreshToken: 'refresh',
        user: { id: '1', username: 'admin', realName: '管理员', role: 'SUPER_ADMIN', avatar: null },
      }),
      refresh: jest.fn().mockResolvedValue({ accessToken: 'new-token' }),
    };

    const module: TestingModule = await Test.createTestingModule({
      controllers: [AuthController],
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: ConfigService, useValue: { get: jest.fn().mockReturnValue('localhost') } },
      ],
    })
      .overrideGuard(JwtAuthGuard)
      .useValue({ canActivate: () => true })
      .compile();

    controller = module.get<AuthController>(AuthController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('login', () => {
    it('should call authService.login with credentials and set cookie', async () => {
      const dto = { username: 'admin', password: 'admin123' };
      const mockRes = { cookie: jest.fn() } as any;
      const result = await controller.login(dto, mockRes);

      expect(authService.login).toHaveBeenCalledWith('admin', 'admin123');
      expect(result).toEqual(expect.objectContaining({ accessToken: 'token' }));
      expect(mockRes.cookie).toHaveBeenCalledWith(
        'token', 'token', expect.objectContaining({ httpOnly: true, path: '/' })
      );
    });
  });

  describe('refresh', () => {
    it('should call authService.refresh with userId from token payload', async () => {
      const refreshToken = 'header.eyJzdWIiOiJ1c2VyLTEifQ.signature';
      const result = await controller.refresh(refreshToken);

      expect(authService.refresh).toHaveBeenCalledWith('user-1');
      expect(result).toEqual({ accessToken: 'new-token' });
    });
  });

  describe('logout', () => {
    it('should clear cookie and return success message', async () => {
      const mockRes = { clearCookie: jest.fn() } as any;
      const result = await controller.logout(mockRes);
      expect(mockRes.clearCookie).toHaveBeenCalledWith(
        'token', expect.objectContaining({ path: '/' })
      );
      expect(result).toEqual({ message: '退出成功' });
    });
  });

  describe('me', () => {
    it('should return current user', async () => {
      const user = { sub: '1', username: 'admin' };
      const result = await controller.me(user as any);
      expect(result).toEqual(user);
    });
  });

  describe('verify', () => {
    it('should return ok and set X-User-Id / X-User-Role headers for Nginx auth_request', async () => {
      const mockRes = {
        setHeader: jest.fn(),
      } as any;
      const user = { userId: 'u1', role: 'ADMIN' };
      const result = await controller.verify(user as any, mockRes);
      expect(result).toEqual({ ok: true });
      expect(mockRes.setHeader).toHaveBeenCalledWith('X-User-Id', 'u1');
      expect(mockRes.setHeader).toHaveBeenCalledWith('X-User-Role', 'ADMIN');
    });
  });
});
