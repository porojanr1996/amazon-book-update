import express from 'express';
import { z } from 'zod';
import pino from 'pino';
import { prisma } from '@bsr-tracker/db';
import { scrapeAmazonBSR } from '@bsr-tracker/scraper';

const logger = pino({ name: 'books-routes' });
export const router = express.Router();

// Validation schemas
const TrackBookSchema = z.object({
  url: z.string().url().or(z.string().length(10)),
});

const ScrapeBookSchema = z.object({
  asin: z.string().length(10),
});

// POST /track - Add a book to tracking
router.post('/track', async (req, res) => {
  try {
    const { url } = TrackBookSchema.parse(req.body);

    logger.info(`Tracking request for: ${url}`);

    // Scrape immediately to get book data
    const bookData = await scrapeAmazonBSR(url);

    // Check if book already exists
    let book = await prisma.book.findUnique({
      where: { asin: bookData.asin },
    });

    if (!book) {
      // Create new book
      book = await prisma.book.create({
        data: {
          asin: bookData.asin,
          title: bookData.title,
          url: `https://www.amazon.com/dp/${bookData.asin}/`,
        },
      });
      logger.info(`✅ Book added: ${book.title} (${book.asin})`);
    } else {
      logger.info(`Book already tracked: ${book.title} (${book.asin})`);
    }

    // Save ranking data
    await prisma.rankHistory.create({
      data: {
        bookId: book.id,
        rank: bookData.rank,
        category: bookData.category,
        timestamp: bookData.timestamp,
      },
    });

    res.json({
      success: true,
      book,
      rankData: {
        rank: bookData.rank,
        category: bookData.category,
        timestamp: bookData.timestamp,
      },
    });

  } catch (error) {
    logger.error('Error tracking book:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Invalid request', details: error.errors });
    }

    res.status(500).json({ error: 'Failed to track book', message: (error as Error).message });
  }
});

// POST /scrape - Trigger scraping for a specific book
router.post('/scrape', async (req, res) => {
  try {
    const { asin } = ScrapeBookSchema.parse(req.body);

    logger.info(`Manual scrape triggered for ASIN: ${asin}`);

    const book = await prisma.book.findUnique({
      where: { asin },
    });

    if (!book) {
      return res.status(404).json({ error: 'Book not found. Add it first with POST /track' });
    }

    // Scrape in background
    scrapeAmazonBSR(`https://www.amazon.com/dp/${asin}/`)
      .then(async (bookData) => {
        await prisma.rankHistory.create({
          data: {
            bookId: book.id,
            rank: bookData.rank,
            category: bookData.category,
            timestamp: bookData.timestamp,
          },
        });
        logger.info(`✅ Scraping completed for ${asin}: Rank #${bookData.rank}`);
      })
      .catch((error) => {
        logger.error(`❌ Scraping failed for ${asin}:`, error);
      });

    res.json({
      success: true,
      message: `Scraping started for ${book.title}`,
      asin,
    });

  } catch (error) {
    logger.error('Error in scrape endpoint:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Invalid request', details: error.errors });
    }

    res.status(500).json({ error: 'Failed to scrape', message: (error as Error).message });
  }
});

// GET /books - Get all tracked books
router.get('/', async (req, res) => {
  try {
    const books = await prisma.book.findMany({
      include: {
        rankHistory: {
          orderBy: { timestamp: 'desc' },
          take: 1, // Get latest rank only
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    const booksWithLatestRank = books.map(book => ({
      id: book.id,
      asin: book.asin,
      title: book.title,
      url: book.url,
      currentRank: book.rankHistory[0]?.rank || null,
      lastUpdated: book.rankHistory[0]?.timestamp || null,
    }));

    res.json(booksWithLatestRank);

  } catch (error) {
    logger.error('Error fetching books:', error);
    res.status(500).json({ error: 'Failed to fetch books' });
  }
});

// GET /books/:asin/history - Get ranking history for a book
router.get('/:asin/history', async (req, res) => {
  try {
    const { asin } = req.params;
    const limit = parseInt(req.query.limit as string) || 100;

    const book = await prisma.book.findUnique({
      where: { asin },
      include: {
        rankHistory: {
          orderBy: { timestamp: 'desc' },
          take: limit,
        },
      },
    });

    if (!book) {
      return res.status(404).json({ error: 'Book not found' });
    }

    res.json({
      book: {
        id: book.id,
        asin: book.asin,
        title: book.title,
        url: book.url,
      },
      history: book.rankHistory.map(h => ({
        rank: h.rank,
        category: h.category,
        timestamp: h.timestamp,
      })),
    });

  } catch (error) {
    logger.error('Error fetching book history:', error);
    res.status(500).json({ error: 'Failed to fetch book history' });
  }
});
