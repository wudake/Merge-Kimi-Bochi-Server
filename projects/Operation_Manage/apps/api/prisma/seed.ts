import { PrismaClient, UserRole } from '@prisma/client'
import * as bcrypt from 'bcryptjs'

const prisma = new PrismaClient()

async function main() {
  const hashedPassword = await bcrypt.hash('admin123', 10)

  await prisma.user.upsert({
    where: { username: 'admin' },
    update: {},
    create: {
      username: 'admin',
      passwordHash: hashedPassword,
      realName: '超级管理员',
      role: UserRole.SUPER_ADMIN,
      email: 'admin@factory.com',
    },
  })

  await prisma.dictionary.createMany({
    skipDuplicates: true,
    data: [
      { category: 'product_type', code: 'bridge_aluminum', name: '断桥铝' },
      { category: 'product_type', code: 'system_window', name: '系统窗' },
      { category: 'product_type', code: 'sunroom', name: '阳光房' },
      { category: 'content_type', code: 'factory_tour', name: '工厂实拍' },
      { category: 'content_type', code: 'installation', name: '安装案例' },
      { category: 'content_type', code: 'review', name: '产品测评' },
      { category: 'content_type', code: 'knowledge', name: '科普知识' },
      { category: 'market', code: 'north_america', name: '北美' },
      { category: 'market', code: 'europe', name: '欧洲' },
      { category: 'market', code: 'southeast_asia', name: '东南亚' },
    ],
  })

  console.log('Seed data created successfully')
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
