import { IsString, IsOptional, IsEnum, IsNotEmpty, IsArray, IsDateString, IsNumber } from 'class-validator';
import { ContentStatus, Platform } from '@prisma/client';

export class CreateContentDto {
  @IsString()
  @IsNotEmpty()
  title: string;

  @IsString()
  @IsOptional()
  topicId?: string;

  @IsArray()
  @IsOptional()
  accountIds?: string[];

  @IsString()
  @IsOptional()
  operatorId?: string;

  @IsDateString()
  @IsOptional()
  plannedPublishAt?: string;

  @IsString()
  @IsOptional()
  publishUrl?: string;

  @IsString()
  @IsOptional()
  contentType?: string;

  @IsString()
  @IsOptional()
  script?: string;

  @IsString()
  @IsOptional()
  description?: string;

  @IsOptional()
  attachments?: any[];

  @IsNumber()
  @IsOptional()
  productionTimeHours?: number;

  @IsString()
  @IsOptional()
  remark?: string;
}

export class UpdateContentDto {
  @IsString()
  @IsOptional()
  title?: string;

  @IsString()
  @IsOptional()
  topicId?: string;

  @IsArray()
  @IsOptional()
  accountIds?: string[];

  @IsString()
  @IsOptional()
  operatorId?: string;

  @IsEnum(ContentStatus)
  @IsOptional()
  status?: ContentStatus;

  @IsDateString()
  @IsOptional()
  plannedPublishAt?: string;

  @IsDateString()
  @IsOptional()
  actualPublishAt?: string;

  @IsString()
  @IsOptional()
  publishUrl?: string;

  @IsString()
  @IsOptional()
  contentType?: string;

  @IsString()
  @IsOptional()
  script?: string;

  @IsString()
  @IsOptional()
  description?: string;

  @IsOptional()
  attachments?: any[];

  @IsNumber()
  @IsOptional()
  productionTimeHours?: number;

  @IsString()
  @IsOptional()
  rating?: string;

  @IsString()
  @IsOptional()
  remark?: string;
}

export class UpdateContentStatusDto {
  @IsEnum(ContentStatus)
  status: ContentStatus;
}

export class BatchCreateContentDto {
  @IsArray()
  items: CreateContentDto[];
}

export class CalendarQueryDto {
  @IsDateString()
  startDate: string;

  @IsDateString()
  endDate: string;

  @IsString()
  @IsOptional()
  operatorId?: string;

  @IsString()
  @IsOptional()
  accountId?: string;
}
