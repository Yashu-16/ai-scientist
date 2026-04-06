const { PrismaClient } = require('@prisma/client');
const { PrismaNeon } = require('@prisma/adapter-neon');
const { neonConfig } = require('@neondatabase/serverless');
const ws = require('ws');
require('dotenv').config({ path: '.env.local' });

neonConfig.webSocketConstructor = ws;
const adapter = new PrismaNeon({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({ adapter });

async function main() {
  const user = await prisma.user.update({
    where: { email: 'yash.randhe164@gmail.com' },
    data: { emailVerified: new Date() }
  });
  console.log('Updated:', user.email, user.emailVerified);
  await prisma.disconnect();
}

main().catch(console.error);
