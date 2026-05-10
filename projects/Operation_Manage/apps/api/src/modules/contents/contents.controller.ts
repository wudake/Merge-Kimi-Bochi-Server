import { Controller, Get, Post, Body, Param, Put, Delete, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation, ApiQuery } from '@nestjs/swagger';
import { ContentsService } from './contents.service';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { Roles } from '../../common/decorators/roles.decorator';
import { RolesGuard } from '../../common/guards/roles.guard';
import { UserRole } from '@prisma/client';
import { CreateContentDto, UpdateContentDto, UpdateContentStatusDto } from './dto';

@ApiTags('内容产出')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('contents')
export class ContentsController {
  constructor(private contentsService: ContentsService) {}

  @Post()
  @ApiOperation({ summary: '创建内容' })
  async create(@Body() dto: CreateContentDto) {
    return this.contentsService.create(dto);
  }

  @Get()
  @ApiOperation({ summary: '内容列表' })
  @ApiQuery({ name: 'status', required: false })
  @ApiQuery({ name: 'operatorId', required: false })
  @ApiQuery({ name: 'accountId', required: false })
  @ApiQuery({ name: 'search', required: false })
  @ApiQuery({ name: 'startDate', required: false })
  @ApiQuery({ name: 'endDate', required: false })
  async findAll(
    @Query('status') status?: string,
    @Query('operatorId') operatorId?: string,
    @Query('accountId') accountId?: string,
    @Query('search') search?: string,
    @Query('startDate') startDate?: string,
    @Query('endDate') endDate?: string,
  ) {
    return this.contentsService.findAll({ status, operatorId, accountId, search, startDate, endDate });
  }

  @Get('calendar')
  @ApiOperation({ summary: '日历视图数据' })
  @ApiQuery({ name: 'startDate', required: true })
  @ApiQuery({ name: 'endDate', required: true })
  @ApiQuery({ name: 'operatorId', required: false })
  @ApiQuery({ name: 'accountId', required: false })
  async findCalendar(
    @Query('startDate') startDate: string,
    @Query('endDate') endDate: string,
    @Query('operatorId') operatorId?: string,
    @Query('accountId') accountId?: string,
  ) {
    return this.contentsService.findCalendar({ startDate, endDate, operatorId, accountId });
  }

  @Get(':id')
  @ApiOperation({ summary: '内容详情' })
  async findOne(@Param('id') id: string) {
    return this.contentsService.findOne(id);
  }

  @Put(':id')
  @ApiOperation({ summary: '更新内容' })
  async update(@Param('id') id: string, @Body() dto: UpdateContentDto) {
    return this.contentsService.update(id, dto);
  }

  @Put(':id/status')
  @ApiOperation({ summary: '更新内容状态' })
  async updateStatus(@Param('id') id: string, @Body() dto: UpdateContentStatusDto) {
    return this.contentsService.updateStatus(id, dto);
  }

  @Delete(':id')
  @Roles(UserRole.SUPER_ADMIN, UserRole.MANAGER)
  @UseGuards(RolesGuard)
  @ApiOperation({ summary: '删除内容' })
  async remove(@Param('id') id: string) {
    return this.contentsService.remove(id);
  }

  @Post('batch')
  @ApiOperation({ summary: '批量创建内容' })
  async batchCreate(@Body() dto: { items: CreateContentDto[] }) {
    return this.contentsService.batchCreate(dto);
  }

  @Post('batch/assign')
  @ApiOperation({ summary: '批量指派负责人' })
  async batchAssign(@Body('contentIds') contentIds: string[], @Body('operatorId') operatorId: string) {
    return this.contentsService.batchAssign(contentIds, operatorId);
  }
}
