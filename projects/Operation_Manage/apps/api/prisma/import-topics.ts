import { PrismaClient, ContentForm, TopicStatus } from '@prisma/client'

const prisma = new PrismaClient()

const topicsData = [
  'How we pack aluminum windows and doors for sea shipping',
  'What should Australian builders check before ordering windows from China?',
  'How Are Aluminum Windows Made in a Factory?',
  'What Does a Reliable Window Factory Look Like?',
  'How Do We Check Aluminum Window Quality Before Shipping?',
  'How Are Windows Packed for Overseas Shipping?',
  'What Happens Before Aluminum Windows Are Loaded into Containers?',
  'How Do We Make Sure Custom Windows Match the Drawings?',
  'What Makes a High-Quality Aluminum Window?',
  'Why Does Aluminum Profile Thickness Matter?',
  'What Is Inside a Thermal Break Aluminum Window?',
  'How Does Low-E Glass Work?',
  'Why Are Good Window Seals Important?',
  'How Do Multi-Point Locks Improve Window Security?',
  'What Hardware Should Good Aluminum Windows Use?',
  'Aluminum Windows or Vinyl Windows: Which Is Better?',
  'Cheap Windows or Quality Windows: What Is the Real Difference?',
  'Regular Aluminum Windows or Thermal Break Aluminum Windows?',
  'Single Glass or Double Glazing: Which Should You Choose?',
  'Regular Windows or Impact Windows: What Is the Difference?',
  'Local Retail Windows or Factory-Direct Windows?',
  'How Do Aluminum Windows Look After Installation?',
  'What Windows Did This Villa Project Use?',
  'How Do Aluminum Bifold Doors Look in a Modern Home?',
  'What Window System Was Used in This Commercial Project?',
  'How Were These Custom Windows Produced for an Overseas Client?',
  'Why Did This Contractor Choose Factory-Direct Aluminum Windows?',
  'How to choose a reliable aluminum window supplier from China?',
  'Where can I find aluminum window manufacturers?',
  'How do I find a reliable window and door manufacturer?',
  'Where can contractors buy wholesale windows and doors?',
  'Is factory-direct window supply cheaper than local retail?',
  'How can builders import windows and doors from China?',
  'What should I ask before buying windows from a factory?',
  'How do I verify a Chinese aluminum window supplier?',
  'What makes a good aluminum window manufacturer?',
  'How do I compare window and door suppliers?',
  'What are the best aluminum windows?',
  'Are aluminum windows better than vinyl windows?',
  'What are thermal break aluminum windows?',
  'Are thermal break aluminum windows worth it?',
  'What are the best aluminum sliding windows?',
  'How do I choose aluminum casement windows?',
  'What are the best aluminum bifold doors?',
  'How do I choose aluminum patio doors?',
  'What makes a high-quality aluminum window?',
  'What aluminum profile thickness is best for windows?',
  'How much do aluminum windows cost?',
  'Why do window prices vary so much?',
  'What affects the price of aluminum windows and doors?',
  'Are Chinese aluminum windows cost-effective?',
  'How can contractors reduce window costs?',
  'Is it cheaper to buy windows directly from a factory?',
  'What are the best replacement windows for the money?',
  'How much do impact windows cost?',
  'How does bulk ordering affect window prices?',
  'What are the risks of buying cheap windows?',
  'What are the best energy-efficient windows?',
  'How do thermal break aluminum windows improve insulation?',
  'What is the difference between Low-E glass and regular glass?',
  'What are impact windows?',
  'What is the difference between impact windows and regular windows?',
  'Are impact windows worth it in Florida?',
  'How do I choose windows for a commercial project?',
  'Where can I find commercial aluminum window manufacturers?',
  'How can contractors source custom windows for building projects?',
  'What should builders know before ordering custom aluminum windows?',
]

function inferContentType(title: string): string {
  const t = title.toLowerCase()
  if (t.includes('factory') || t.includes('made') || t.includes('produced') || t.includes('shipping') || t.includes('containers') || t.includes('pack')) {
    return 'factory_tour'
  }
  if (t.includes('quality') || t.includes('check') || t.includes('thickness') || t.includes('seals') || t.includes('locks') || t.includes('hardware') || t.includes('drawings')) {
    return 'review'
  }
  if (t.includes('vs') || t.includes('or ') || t.includes('difference') || t.includes('better')) {
    return 'comparison'
  }
  if (t.includes('cost') || t.includes('price') || t.includes('cheap') || t.includes('money') || t.includes('bulk')) {
    return 'pricing'
  }
  if (t.includes('installation') || t.includes('villa') || t.includes('project') || t.includes('home') || t.includes('look')) {
    return 'installation'
  }
  if (t.includes('choose') || t.includes('find') || t.includes('buy') || t.includes('supplier') || t.includes('manufacturer') || t.includes('import') || t.includes('verify') || t.includes('compare') || t.includes('ask') || t.includes('source')) {
    return 'buying_guide'
  }
  if (t.includes('energy') || t.includes('insulation') || t.includes('low-e') || t.includes('glass') || t.includes('impact') || t.includes('thermal break')) {
    return 'knowledge'
  }
  return 'knowledge'
}

function extractTags(title: string): string[] {
  const t = title.toLowerCase()
  const tags: string[] = []
  const keywordMap: Record<string, string> = {
    'aluminum window': 'aluminum_window',
    'aluminum doors': 'aluminum_door',
    'bifold door': 'bifold_door',
    'sliding window': 'sliding_window',
    'casement window': 'casement_window',
    'patio door': 'patio_door',
    'impact window': 'impact_window',
    'thermal break': 'thermal_break',
    'low-e': 'low_e_glass',
    'double glazing': 'double_glazing',
    'vinyl': 'vinyl',
    'factory': 'factory',
    'shipping': 'shipping',
    'installation': 'installation',
    'quality': 'quality',
    'price': 'price',
    'cost': 'cost',
    'china': 'china',
    'australia': 'australia',
    'florida': 'florida',
    'commercial': 'commercial',
    'villa': 'villa',
    'custom': 'custom',
    'security': 'security',
    'energy': 'energy_efficient',
    'bulk': 'bulk_order',
  }
  Object.entries(keywordMap).forEach(([keyword, tag]) => {
    if (t.includes(keyword)) tags.push(tag)
  })
  return [...new Set(tags)]
}

async function main() {
  const admin = await prisma.user.findUnique({
    where: { username: 'admin' },
    select: { id: true },
  })

  if (!admin) {
    console.error('Admin user not found. Please run seed first.')
    process.exit(1)
  }

  let created = 0
  let skipped = 0

  for (const title of topicsData) {
    const cleanTitle = title.replace(/^[-\s]+/, '').trim()
    if (!cleanTitle) continue

    const existing = await prisma.topic.findFirst({
      where: { title: { equals: cleanTitle, mode: 'insensitive' } },
    })

    if (existing) {
      skipped++
      continue
    }

    const contentType = inferContentType(cleanTitle)
    const tags = extractTags(cleanTitle)

    await prisma.topic.create({
      data: {
        title: cleanTitle,
        contentForm: ContentForm.SHORT_VIDEO,
        contentType,
        tags,
        status: TopicStatus.PENDING,
        createdBy: admin.id,
      },
    })
    created++
  }

  console.log(`Import completed: ${created} created, ${skipped} skipped (duplicates)`)
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
