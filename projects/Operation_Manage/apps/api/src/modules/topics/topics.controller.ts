import { Controller, Get, Post, Body, Param, Put, Delete, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation, ApiQuery } from '@nestjs/swagger';
import { TopicsService } from './topics.service';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { CurrentUser } from '../../common/decorators/current-user.decorator';
import { CreateTopicDto, UpdateTopicDto } from './dto';

@ApiTags('选题库')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('topics')
export class TopicsController {
  constructor(private topicsService: TopicsService) {}

  @Post()
  @ApiOperation({ summary: '创建选题' })
  async create(@Body() dto: CreateTopicDto, @CurrentUser('userId') userId: string) {
    return this.topicsService.create(userId, dto);
  }

  @Get()
  @ApiOperation({ summary: '选题列表' })
  @ApiQuery({ name: 'status', required: false })
  @ApiQuery({ name: 'contentType', required: false })
  @ApiQuery({ name: 'search', required: false })
  @ApiQuery({ name: 'sortBy', required: false, description: 'usage | createdAt' })
  async findAll(
    @Query('status') status?: string,
    @Query('contentType') contentType?: string,
    @Query('search') search?: string,
    @Query('sortBy') sortBy?: string,
  ) {
    return this.topicsService.findAll({ status, contentType, search, sortBy });
  }

  @Get(':id')
  @ApiOperation({ summary: '选题详情' })
  async findOne(@Param('id') id: string) {
    return this.topicsService.findOne(id);
  }

  @Put(':id')
  @ApiOperation({ summary: '更新选题' })
  async update(@Param('id') id: string, @Body() dto: UpdateTopicDto) {
    return this.topicsService.update(id, dto);
  }

  @Delete(':id')
  @ApiOperation({ summary: '删除选题' })
  async remove(@Param('id') id: string) {
    return this.topicsService.remove(id);
  }
}
