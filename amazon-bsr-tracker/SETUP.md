# 🚀 Setup Instructions

## Quick Start (5 minutes)

```bash
# 1. Install dependencies
npm install

# 2. Install Playwright browsers
npx playwright install chromium

# 3. Generate Prisma client
npm run db:generate

# 4. Create database
npm run db:push

# 5. Start development
npm run dev
```

Open:
- Dashboard: http://localhost:3001
- API: http://localhost:3000

## Step-by-Step Setup

### 1. Install Node.js

Make sure you have Node.js 18+ installed:

```bash
node --version  # Should be >= 18.0.0
```

### 2. Clone and Install

```bash
cd /Users/testing/books-reporting/amazon-bsr-tracker
npm install
```

### 3. Install Playwright

```bash
npx playwright install chromium
```

### 4. Setup Database

```bash
# Generate Prisma client
npm run db:generate

# Push schema to database (creates tables)
npm run db:push

# (Optional) Open Prisma Studio to view data
npm run db:studio
```

### 5. Environment Variables

Create `.env` in the root:

```env
DATABASE_URL="file:./packages/db/prisma/dev.db"
PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:3000
PLAYWRIGHT_HEADLESS=true
```

### 6. Start Development

```bash
# Start all services (API + Dashboard)
npm run dev
```

## 🧪 Testing the Scraper

### Test scraping manually:

```bash
# Scrape a single book
npm run scrape https://www.amazon.com/dp/B0CSZHZRSR

# Or just the ASIN
npm run scrape B0CSZHZRSR
```

### Add a book via API:

```bash
curl -X POST http://localhost:3000/api/books/track \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.amazon.com/dp/B0CSZHZRSR"}'
```

### View in dashboard:

Open http://localhost:3001

## 🤖 Ollama Setup (Optional)

For AI diagnostics when scraping fails:

```bash
# 1. Install Ollama
curl https://ollama.ai/install.sh | sh

# 2. Pull model
ollama pull codellama
# or
ollama pull deepseek-coder

# 3. Run diagnostics
npm run diagnose ./errors/error.txt ./errors/html.html
```

## 🐳 Docker Setup (Alternative)

```bash
# Build
docker-compose build

# Run
docker-compose up

# Or detached
docker-compose up -d
```

## 📝 Development Commands

```bash
# Start dev servers
npm run dev

# Build for production
npm run build

# Start production
npm run start

# Database commands
npm run db:generate   # Generate Prisma client
npm run db:migrate    # Run migrations
npm run db:push       # Push schema
npm run db:studio     # Open Prisma Studio

# Scraping commands
npm run scrape <url>  # Scrape single book
npm run scrape:all    # Scrape all tracked books

# AI diagnostics
npm run diagnose <error-file> <html-file>
```

## 🚀 Deployment to EC2

```bash
# 1. SSH to EC2
ssh ec2-user@your-ec2-ip

# 2. Clone repo
git clone <your-repo>
cd amazon-bsr-tracker

# 3. Install Node.js 18+
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# 4. Install dependencies
npm install
npx playwright install chromium --with-deps

# 5. Setup database
npm run db:generate
npm run db:push

# 6. Build
npm run build

# 7. Install PM2
npm install -g pm2

# 8. Start services
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 🔍 Troubleshooting

### Playwright not working on EC2

```bash
# Install dependencies
sudo yum install -y \
  libnss3 \
  libatk-bridge2.0-0 \
  libdrm2 \
  libxkbcommon0 \
  libgbm1 \
  libasound2
```

### Database issues

```bash
# Reset database
rm packages/db/prisma/dev.db
npm run db:push
```

### Port already in use

```bash
# Find process
lsof -ti:3000
# or
lsof -ti:3001

# Kill process
kill -9 <PID>
```

## 📊 Dashboard Features

- **Books Table**: View all tracked books with current rank
- **Book Detail Page**: View ranking history chart
- **Add Book**: Track new books via UI
- **Auto Refresh**: Data refreshes automatically

## ⚡ Performance

- **Scraping Speed**: ~5-10 seconds per book
- **Rate Limiting**: 2-5 second delay between requests
- **Database**: SQLite (fast for small-medium datasets)
- **Memory**: ~100-200 MB per scraping process

## 📄 License

MIT
