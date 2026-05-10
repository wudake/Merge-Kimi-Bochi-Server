import { Controller, Get, Post, Body, Param, Put, Delete, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation, ApiQuery } from '@nestjs/swagger';
import { AccountsService } from './accounts.service';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { Roles } from '../../common/decorators/roles.decorator';
import { RolesGuard } from '../../common/guards/roles.guard';
import { UserRole } from '@prisma/client';
import { CreateAccountDto, UpdateAccountDto, CreateAccountGroupDto, UpdateAccountGroupDto } from './dto';

@ApiTags('账号管理')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard, RolesGuard)
@Controller('accounts')
export class AccountsController {
  constructor(private accountsService: AccountsService) {}

  @Post()
  @Roles(UserRole.SUPER_ADMIN, UserRole.MANAGER)
  @ApiOperation({ summary: '创建账号' })
  async create(@Body() dto: CreateAccountDto) {
    return this.accountsService.create(dto);
  }

  @Get()
  @ApiOperation({ summary: '账号列表' })
  @ApiQuery({ name: 'platform', required: false })
  @ApiQuery({ name: 'status', required: false })
  @ApiQuery({ name: 'groupId', required: false })
  @ApiQuery({ name: 'search', required: false })
  async findAll(
    @Query('platform') platform?: string,
    @Query('status') status?: string,
    @Query('groupId') groupId?: string,
    @Query('search') search?: string,
  ) {
    return this.accountsService.findAll({ platform, status, groupId, search });
  }

  // Groups — must be before :id routes to avoid shadowing
  @Get('groups/all')
  @ApiOperation({ summary: '分组列表' })
  async findAllGroups() {
    return this.accountsService.findAllGroups();
  }

  @Post('groups')
  @Roles(UserRole.SUPER_ADMIN, UserRole.MANAGER)
  @ApiOperation({ summary: '创建分组' })
  async createGroup(@Body() dto: CreateAccountGroupDto) {
    return this.accountsService.createGroup(dto);
  }

  @Put('groups/:id')
  @Roles(UserRole.SUPER_ADMIN, UserRole.MANAGER)
  @ApiOperation({ summary: '更新分组' })
  async updateGroup(@Param('id') id: string, @Body() dto: UpdateAccountGroupDto) {
    return this.accountsService.updateGroup(id, dto);
  }

  @Delete('groups/:id')
  @Roles(UserRole.SUPER_ADMIN, UserRole.MANAGER)
  @ApiOperation({ summary: '删除分组' })
  async removeGroup(@Param('id') id: string) {
    return this.accountsService.removeGroup(id);
  }

  @Get(':id')
  @ApiOperation({ summary: '账号详情' })
  async findOne(@Param('id') id: string) {
    return this.accountsService.findOne(id);
  }

  @Put(':id')
  @Roles(UserRole.SUPER_ADMIN, UserRole.MANAGER)
  @ApiOperation({ summary: '更新账号' })
  async update(@Param('id') id: string, @Body() dto: UpdateAccountDto) {
    return this.accountsService.update(id, dto);
  }

  @Delete(':id')
  @Roles(UserRole.SUPER_ADMIN, UserRole.MANAGER)
  @ApiOperation({ summary: '删除账号' })
  async remove(@Param('id') id: string) {
    return this.accountsService.remove(id);
  }

  @Post(':id/transfer')
  @Roles(UserRole.SUPER_ADMIN, UserRole.MANAGER)
  @ApiOperation({ summary: '账号交接' })
  async transfer(@Param('id') id: string, @Body('operatorIds') operatorIds: string[]) {
    return this.accountsService.transfer(id, operatorIds);
  }
}
