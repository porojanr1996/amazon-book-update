import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import pinoHttp from 'pino-http';
import pino from 'pino';
import rateLimit from 'express-rate-limit';
import cron from 'node-cron';
import dotenv from 'dotenv';

import { router as booksRouter } from './routes/books';
import { scrapeAllBooks } from './services/scheduler';

dotenv.config();

const logger = pino({ name: 'api-server' });
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(pinoHttp({ logger }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
});

app.use('/api', limiter);

// Routes
app.use('/api/books', booksRouter);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Scheduler: Scrape all books every 6 hours
cron.schedule('0 */6 * * *', async () => {
  logger.info('Running scheduled scraping for all books...');
  try {
    await scrapeAllBooks();
    logger.info('✅ Scheduled scraping completed');
  } catch (error) {
    logger.error('❌ Scheduled scraping failed:', error);
  }
});

logger.info('Scheduler configured: scraping every 6 hours');

// Start server
app.listen(PORT, () => {
  logger.info(`🚀 API Server running on http://localhost:${PORT}`);
  logger.info(`📊 Dashboard: http://localhost:3001`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  process.exit(0);
});
