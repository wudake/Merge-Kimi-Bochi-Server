import { PrismaClient, Platform, AccountStatus } from '@prisma/client';

const prisma = new PrismaClient();

const DANNY_ID = '8fda33c9-5ef6-473b-8419-d9cd5db3ffe8';
const BENNY_ID = 'e6cc3a1d-6c69-4077-93a0-4ac003de1060';

const PLATFORM_MAP: Record<string, Platform> = {
  FB: Platform.FACEBOOK,
  Ins: Platform.INSTAGRAM,
  YTB: Platform.YOUTUBE,
  TK: Platform.TIKTOK,
};

const STATUS_MAP: Record<string, AccountStatus> = {
  '正常运营': AccountStatus.ACTIVE,
  '暂未运营': AccountStatus.PAUSED,
  '无播放量废号': AccountStatus.BANNED,
};

function op(name: string | null): string[] {
  if (name === 'Danny') return [DANNY_ID];
  if (name === 'Benny') return [BENNY_ID];
  return [];
}

const accounts = [
  {
    name: 'Foshan Boswindor Window and Door Limited',
    platform: PLATFORM_MAP.FB,
    accountType: '主公共主页',
    operators: op('Danny'),
    loginEmail: 'wudake264@gmail.com',
    loginPhone: null,
    loginPassword: 'Bos2025$',
    followerCount: 553,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'boswindor_limited',
    platform: PLATFORM_MAP.Ins,
    accountType: '主账户',
    operators: op('Danny'),
    loginEmail: 'boswindor@gmail.com',
    loginPhone: null,
    loginPassword: 'Boswindor888888',
    followerCount: 570,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'Foshan Boswindor Window and Door Limited',
    platform: PLATFORM_MAP.YTB,
    accountType: '主账户',
    operators: op('Danny'),
    loginEmail: 'boswindor@gmail.com',
    loginPhone: null,
    loginPassword: 'Boswindor123$%',
    followerCount: 74,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'china_window_door',
    platform: PLATFORM_MAP.TK,
    accountType: '主账户',
    operators: op('Danny'),
    loginEmail: 'zzhu96663@gmail.com',
    loginPhone: '17329524698',
    loginPassword: 'Bos123456',
    followerCount: 1258,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'Boswindor Building Material',
    platform: PLATFORM_MAP.TK,
    accountType: '混剪账号02',
    operators: op('Danny'),
    loginEmail: 'bhe05798@gmail.com',
    loginPhone: '18126652290',
    loginPassword: 'Boswindor250331+',
    followerCount: 259,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'Boswindor Building Material',
    platform: PLATFORM_MAP.YTB,
    accountType: '混剪账号02',
    operators: op('Danny'),
    loginEmail: 'bhe05798@gmail.com',
    loginPhone: '18126652290',
    loginPassword: 'Boswindor250331+',
    followerCount: 3180,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'Boswindor Building Material',
    platform: PLATFORM_MAP.Ins,
    accountType: '混剪账号02',
    operators: op('Danny'),
    loginEmail: 'zzhu96663@gmail.com',
    loginPhone: '17329524698',
    loginPassword: 'Bos123456',
    followerCount: 26,
    status: STATUS_MAP['正常运营'],
    remark: 'ins账号都要用用户名登录',
  },
  {
    name: 'boswindor factory',
    platform: PLATFORM_MAP.FB,
    accountType: '副公共主页01',
    operators: op('Benny'),
    loginEmail: 'zzhu96663@gmail.com',
    loginPhone: '17329524698',
    loginPassword: 'Bos123456',
    followerCount: 17,
    status: STATUS_MAP['正常运营'],
    remark: '已注册公共主页',
  },
  {
    name: 'boswindor_factory',
    platform: PLATFORM_MAP.Ins,
    accountType: '副账号01',
    operators: op('Benny'),
    loginEmail: 'zzhu96663@gmail.com',
    loginPhone: '17329524698',
    loginPassword: 'Bos123456',
    followerCount: 22,
    status: STATUS_MAP['正常运营'],
    remark: 'ins使用账号名称登陆账号',
  },
  {
    name: 'boswindor_factory',
    platform: PLATFORM_MAP.YTB,
    accountType: '副账号01',
    operators: op('Benny'),
    loginEmail: 'zzhu96663@gmail.com',
    loginPhone: '17329524698',
    loginPassword: 'Bos123456',
    followerCount: 2490,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'boswindor_factory',
    platform: PLATFORM_MAP.TK,
    accountType: '副账号01',
    operators: op('Benny'),
    loginEmail: 'Sienna4698@outlook.com',
    loginPhone: '17329524698',
    loginPassword: 'Bos123456',
    followerCount: 0,
    status: STATUS_MAP['暂未运营'],
    remark: '忘记密码，建议重新注册一个tk账号',
  },
  {
    name: 'Boswindor doors and window',
    platform: PLATFORM_MAP.YTB,
    accountType: '混剪账号01',
    operators: op('Benny'),
    loginEmail: 'boswindor05@gmail.com',
    loginPhone: '18825938997',
    loginPassword: 'Boswindor05$.@',
    followerCount: 0,
    status: STATUS_MAP['正常运营'],
    remark: '邮箱密码',
  },
  {
    name: 'Boswindor doors and window',
    platform: PLATFORM_MAP.Ins,
    accountType: '混剪账号01',
    operators: op('Benny'),
    loginEmail: 'boswindor01@outlook.com',
    loginPhone: null,
    loginPassword: 'Boswindor123$%',
    followerCount: 0,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'Boswindor PremiumDoors',
    platform: PLATFORM_MAP.Ins,
    accountType: '副账号',
    operators: op('Danny'),
    loginEmail: 'boswindor06@gmail.com',
    loginPhone: '18126652290',
    loginPassword: 'Boswindor06$.',
    followerCount: 0,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'Boswindor PremiumDoors',
    platform: PLATFORM_MAP.YTB,
    accountType: '副账号',
    operators: op('Danny'),
    loginEmail: 'boswindor06@gmail.com',
    loginPhone: '18126652290',
    loginPassword: 'Boswindor06$.',
    followerCount: 7,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'Boswindor PremiumDoors',
    platform: PLATFORM_MAP.FB,
    accountType: '副公共主页',
    operators: op('Danny'),
    loginEmail: 'boswindor06@gmail.com',
    loginPhone: '18126652290',
    loginPassword: 'Boswindor06$.',
    followerCount: 0,
    status: STATUS_MAP['正常运营'],
    remark: null,
  },
  {
    name: 'Boswindor-Premium-Doors',
    platform: PLATFORM_MAP.TK,
    accountType: '副账号',
    operators: op('Danny'),
    loginEmail: 'boswindor06@gmail.com',
    loginPhone: '18126652290',
    loginPassword: 'Boswindor06$.',
    followerCount: 0,
    status: STATUS_MAP['正常运营'],
    remark: '谷歌登录',
  },
  {
    name: 'boswindordoorswindowsfactory',
    platform: PLATFORM_MAP.Ins,
    accountType: null,
    operators: op(null),
    loginEmail: 'boswindor02@outlook.com',
    loginPhone: null,
    loginPassword: 'Boswindor123$%',
    followerCount: 0,
    status: STATUS_MAP['正常运营'],
    remark: '绑定了购买账号广告主页（邮箱登录）',
  },
  {
    name: 'boswindor.lulu',
    platform: PLATFORM_MAP.YTB,
    accountType: null,
    operators: op(null),
    loginEmail: 'info@boswindor.com',
    loginPhone: '17329524698',
    loginPassword: 'Bos123$%',
    followerCount: 37,
    status: AccountStatus.ACTIVE,
    remark: null,
  },
  {
    name: 'boswindor Lulu',
    platform: PLATFORM_MAP.FB,
    accountType: null,
    operators: op(null),
    loginEmail: 'shuanglianguo311@gmail.com',
    loginPhone: null,
    loginPassword: 'gsl123456789',
    followerCount: 8,
    status: AccountStatus.ACTIVE,
    remark: '手机号：刘总手机号',
  },
  {
    name: 'boswindor1',
    platform: PLATFORM_MAP.TK,
    accountType: null,
    operators: op(null),
    loginEmail: 'boswindor@gmail.com',
    loginPhone: null,
    loginPassword: 'Bos123456%',
    followerCount: 0,
    status: STATUS_MAP['无播放量废号'],
    remark: null,
  },
];

async function main() {
  // Clear existing accounts and relations
  await prisma.$executeRawUnsafe('TRUNCATE TABLE "_AccountToUser", "accounts" CASCADE');
  console.log('Cleared existing accounts');

  for (const acc of accounts) {
    const data: any = { ...acc };
    const opIds = data.operators;
    delete data.operators;
    if (opIds && opIds.length > 0) {
      data.operators = { connect: opIds.map((id: string) => ({ id })) };
    }
    if (!data.accountType) delete data.accountType;
    if (!data.loginPhone) delete data.loginPhone;
    if (!data.remark) delete data.remark;

    await prisma.account.create({ data });
  }

  console.log(`Imported ${accounts.length} accounts`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
