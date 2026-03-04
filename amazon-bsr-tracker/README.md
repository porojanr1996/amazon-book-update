# 📊 Amazon BSR Tracker

Production-ready Amazon Best Sellers Rank tracker built with Node.js, TypeScript, Playwright, and Next.js.

## 🚀 Features

- **Automated Scraping**: Track book rankings every 6 hours
- **Real-time Dashboard**: Next.js UI with ranking history charts
- **Robust Scraping**: Playwright with retry logic and error handling
- **AI Diagnostics**: Ollama integration for automatic selector fixing
- **Rate Limiting**: Respect Amazon's rate limits with delays
- **SQLite Database**: Prisma ORM for data persistence

## 🛠️ Tech Stack

- **Node.js + TypeScript**
- **Playwright** - Web scraping
- **Express** - API server
- **SQLite + Prisma** - Database
- **Next.js** - Frontend dashboard
- **Tailwind CSS** - Styling
- **Zod** - Validation
- **Pino** - Logging
- **Ollama** - AI diagnostics (optional)

## 📦 Project Structure

```
amazon-bsr-tracker/
├── apps/
│   ├── web/          # Next.js dashboard
│   └── api/          # Express API server
├── packages/
│   ├── scraper/      # Playwright scraper
│   ├── ai-diagnostics/  # Ollama integration
│   └── db/           # Prisma schema
```

## 🚀 Setup Instructions

### Prerequisites

- Node.js 18+ 
- npm or yarn
- (Optional) Ollama for AI diagnostics

### Installation

```bash
# 1. Install dependencies
npm install

# 2. Install Playwright browsers
npx playwright install chromium

# 3. Setup database
npm run db:generate
npm run db:migrate

# 4. Start development servers
npm run dev
```

This will start:
- API Server: http://localhost:3000
- Dashboard: http://localhost:3001

### Production Build

```bash
npm run build
npm run start
```

## 📖 Usage

### Add a Book to Track

```bash
# Via API
curl -X POST http://localhost:3000/api/books/track \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.amazon.com/dp/B0CSZHZRSR"}'

# Via CLI
npm run scrape https://www.amazon.com/dp/B0CSZHZRSR
```

### Manual Scraping

```bash
# Scrape single book
npm run scrape <amazon-url-or-asin>

# Scrape all tracked books
npm run scrape:all
```

### AI Diagnostics (requires Ollama)

```bash
# Install Ollama: https://ollama.ai
ollama run codellama

# Run diagnostics on error
npm run diagnose ./errors/error.txt ./errors/html.html
```

## 🔄 Scheduler

The system automatically scrapes all tracked books every 6 hours.

To modify the schedule, edit `apps/api/src/index.ts`:

```typescript
// Current: every 6 hours
cron.schedule('0 */6 * * *', async () => {
  await scrapeAllBooks();
});

// Daily at 10 AM
cron.schedule('0 10 * * *', async () => {
  await scrapeAllBooks();
});
```

## 📊 API Endpoints

### `POST /api/books/track`
Add a book to tracking

**Request:**
```json
{
  "url": "https://www.amazon.com/dp/B0CSZHZRSR"
}
```

**Response:**
```json
{
  "success": true,
  "book": {
    "id": "...",
    "asin": "B0CSZHZRSR",
    "title": "Book Title"
  },
  "rankData": {
    "rank": 12345,
    "category": "Kindle Store",
    "timestamp": "2024-01-01T00:00:00.000Z"
  }
}
```

### `POST /api/books/scrape`
Trigger manual scraping

**Request:**
```json
{
  "asin": "B0CSZHZRSR"
}
```

### `GET /api/books`
Get all tracked books

### `GET /api/books/:asin/history`
Get ranking history for a book

**Query params:**
- `limit` (default: 100)

## 🎨 Dashboard

Visit http://localhost:3001 to:
- View all tracked books
- See current rankings
- Click on a book to view history chart

## ⚙️ Configuration

Create `.env` file in the root:

```env
# Database
DATABASE_URL="file:./dev.db"

# API
PORT=3000

# Dashboard
NEXT_PUBLIC_API_URL=http://localhost:3000

# Ollama (optional)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=codellama

# Scraper
PLAYWRIGHT_HEADLESS=true
SCRAPE_DELAY_MIN=2000
SCRAPE_DELAY_MAX=5000
```

## 🐛 Error Handling

When scraping fails:
- HTML snapshot saved to `./errors/html_<asin>_<timestamp>.html`
- Screenshot saved to `./errors/screenshot_<asin>_<timestamp>.png`
- Error logged with full stack trace

Run AI diagnostics:
```bash
npm run diagnose ./errors/error.txt ./errors/html_<asin>_<timestamp>.html
```

## 🔒 Rate Limiting

The scraper includes:
- Random delays (2-5 seconds between requests)
- Retry logic with exponential backoff
- Realistic browser headers
- Human-like behavior

## 📝 Development

```bash
# Run tests
npm test

# Lint
npm run lint

# Format
npm run format

# Type check
npm run type-check
```

## 🚀 Deployment

### Deploy to EC2

```bash
# 1. Clone repo on EC2
git clone <your-repo-url>
cd amazon-bsr-tracker

# 2. Install dependencies
npm install
npx playwright install chromium --with-deps

# 3. Setup database
npm run db:generate
npm run db:push

# 4. Build
npm run build

# 5. Start with PM2
npm install -g pm2
pm2 start ecosystem.config.js
pm2 save
```

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Please open an issue first to discuss changes.
