import { Controller, Post, Body, Get, UseGuards, Res } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation } from '@nestjs/swagger';
import { ConfigService } from '@nestjs/config';
import { Response } from 'express';
import { AuthService } from './auth.service';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { CurrentUser } from '../../common/decorators/current-user.decorator';
import { LoginDto } from './dto';

@ApiTags('认证')
@Controller('auth')
export class AuthController {
  constructor(
    private authService: AuthService,
    private configService: ConfigService,
  ) {}

  @Post('login')
  @ApiOperation({ summary: '用户登录' })
  async login(@Body() dto: LoginDto, @Res({ passthrough: true }) res: Response) {
    const result = await this.authService.login(dto.username, dto.password);
    const domain = this.configService.get<string>('COOKIE_DOMAIN');
    res.cookie('token', result.accessToken, {
      ...(domain && { domain }),
      path: '/',
      httpOnly: true,
      sameSite: 'lax',
      maxAge: 2 * 60 * 60 * 1000,
    });
    return result;
  }

  @Post('refresh')
  @ApiOperation({ summary: '刷新 Token' })
  async refresh(@Body('refreshToken') refreshToken: string) {
    const payload = JSON.parse(
      Buffer.from(refreshToken.split('.')[1], 'base64').toString(),
    );
    return this.authService.refresh(payload.sub);
  }

  @Post('logout')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: '退出登录' })
  async logout(@Res({ passthrough: true }) res: Response) {
    const domain = this.configService.get<string>('COOKIE_DOMAIN');
    res.clearCookie('token', {
      ...(domain && { domain }),
      path: '/',
    });
    return { message: '退出成功' };
  }

  @Get('me')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: '获取当前用户信息' })
  async me(@CurrentUser() user: any) {
    return user;
  }

  @Get('verify')
  @UseGuards(JwtAuthGuard)
  @ApiOperation({ summary: 'SSO 校验 (供 Nginx auth_request 使用)' })
  async verify(@CurrentUser() user: any, @Res({ passthrough: true }) res: Response) {
    res.setHeader('X-User-Id', user.userId);
    res.setHeader('X-User-Role', user.role);
    return { ok: true };
  }
}
