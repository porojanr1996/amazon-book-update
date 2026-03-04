import { prisma } from '@bsr-tracker/db';
import { scrapeAmazonBSR } from '@bsr-tracker/scraper';
import pino from 'pino';

const logger = pino({ name: 'scheduler' });

export async function scrapeAllBooks(): Promise<void> {
  logger.info('Starting scraping for all tracked books...');

  const books = await prisma.book.findMany();

  if (books.length === 0) {
    logger.info('No books to scrape');
    return;
  }

  logger.info(`Scraping ${books.length} books...`);

  let successCount = 0;
  let failureCount = 0;

  for (const book of books) {
    try {
      logger.info(`Scraping: ${book.title} (${book.asin})`);

      const bookData = await scrapeAmazonBSR(book.url);

      await prisma.rankHistory.create({
        data: {
          bookId: book.id,
          rank: bookData.rank,
          category: bookData.category,
          timestamp: bookData.timestamp,
        },
      });

      successCount++;
      logger.info(`✅ Success: ${book.title} - Rank #${bookData.rank}`);

      // Delay between requests (2-5 seconds)
      await new Promise(resolve => setTimeout(resolve, Math.random() * 3000 + 2000));

    } catch (error) {
      failureCount++;
      logger.error(`❌ Failed: ${book.title} (${book.asin})`, error);
    }
  }

  logger.info(`Scraping completed: ${successCount} success, ${failureCount} failures`);
}
