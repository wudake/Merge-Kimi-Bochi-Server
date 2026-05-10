import { IsString, IsOptional, IsEnum, IsNotEmpty, IsArray, IsDateString } from 'class-validator';
import { Platform, AccountStatus } from '@prisma/client';

export class CreateAccountDto {
  @IsEnum(Platform)
  platform: Platform;

  @IsString()
  @IsNotEmpty()
  name: string;

  @IsString()
  @IsOptional()
  accountId?: string;

  @IsString()
  @IsOptional()
  accountType?: string;

  @IsString()
  @IsOptional()
  homeUrl?: string;

  @IsString()
  @IsOptional()
  market?: string;

  @IsString()
  @IsOptional()
  targetAudience?: string;

  @IsString()
  @IsOptional()
  loginEmail?: string;

  @IsString()
  @IsOptional()
  loginPhone?: string;

  @IsString()
  @IsOptional()
  loginPassword?: string;

  @IsString()
  @IsOptional()
  linkedPhone?: string;

  @IsDateString()
  @IsOptional()
  registeredAt?: string;

  @IsString()
  @IsOptional()
  commonDevices?: string;

  @IsEnum(AccountStatus)
  @IsOptional()
  status?: AccountStatus;

  @IsOptional()
  followerCount?: number;

  @IsString()
  @IsOptional()
  persona?: string;

  @IsString()
  @IsOptional()
  remark?: string;

  @IsString()
  @IsOptional()
  customGroup?: string;

  @IsOptional()
  contactInfo?: Record<string, any>;

  @IsString()
  @IsOptional()
  groupId?: string;

  @IsArray()
  @IsOptional()
  tags?: string[];

  @IsArray()
  @IsOptional()
  operatorIds?: string[];
}

export class UpdateAccountDto {
  @IsEnum(Platform)
  @IsOptional()
  platform?: Platform;

  @IsString()
  @IsOptional()
  name?: string;

  @IsString()
  @IsOptional()
  accountId?: string;

  @IsString()
  @IsOptional()
  accountType?: string;

  @IsString()
  @IsOptional()
  homeUrl?: string;

  @IsString()
  @IsOptional()
  market?: string;

  @IsString()
  @IsOptional()
  targetAudience?: string;

  @IsString()
  @IsOptional()
  loginEmail?: string;

  @IsString()
  @IsOptional()
  loginPhone?: string;

  @IsString()
  @IsOptional()
  loginPassword?: string;

  @IsString()
  @IsOptional()
  linkedPhone?: string;

  @IsDateString()
  @IsOptional()
  registeredAt?: string;

  @IsString()
  @IsOptional()
  commonDevices?: string;

  @IsEnum(AccountStatus)
  @IsOptional()
  status?: AccountStatus;

  @IsOptional()
  followerCount?: number;

  @IsString()
  @IsOptional()
  persona?: string;

  @IsString()
  @IsOptional()
  remark?: string;

  @IsString()
  @IsOptional()
  customGroup?: string;

  @IsOptional()
  contactInfo?: Record<string, any>;

  @IsString()
  @IsOptional()
  groupId?: string;

  @IsArray()
  @IsOptional()
  tags?: string[];

  @IsArray()
  @IsOptional()
  operatorIds?: string[];
}

export class CreateAccountGroupDto {
  @IsString()
  @IsNotEmpty()
  name: string;

  @IsString()
  @IsOptional()
  description?: string;
}

export class UpdateAccountGroupDto {
  @IsString()
  @IsOptional()
  name?: string;

  @IsString()
  @IsOptional()
  description?: string;
}
