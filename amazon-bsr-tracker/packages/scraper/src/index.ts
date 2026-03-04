import { chromium, Browser, Page } from 'playwright';
import pino from 'pino';
import { z } from 'zod';

const logger = pino({ name: 'amazon-scraper' });

// Validation schemas
export const BookDataSchema = z.object({
  asin: z.string().min(10).max(10),
  title: z.string(),
  rank: z.number().int().positive(),
  category: z.string(),
  timestamp: z.date(),
});

export type BookData = z.infer<typeof BookDataSchema>;

export interface ScraperConfig {
  headless?: boolean;
  timeout?: number;
  retries?: number;
  delayMin?: number;
  delayMax?: number;
}

export class AmazonBSRScraper {
  private browser: Browser | null = null;
  private config: Required<ScraperConfig>;

  constructor(config: ScraperConfig = {}) {
    this.config = {
      headless: config.headless ?? true,
      timeout: config.timeout ?? 60000,
      retries: config.retries ?? 3,
      delayMin: config.delayMin ?? 2000,
      delayMax: config.delayMax ?? 5000,
    };
  }

  async initialize(): Promise<void> {
    if (this.browser) return;

    logger.info('Initializing browser...');
    this.browser = await chromium.launch({
      headless: this.config.headless,
      args: [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
      ],
    });
  }

  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      logger.info('Browser closed');
    }
  }

  private extractASIN(input: string): string {
    // Extract ASIN from URL or return as-is if already ASIN
    const asinMatch = input.match(/\/dp\/([A-Z0-9]{10})/i) || input.match(/\/gp\/product\/([A-Z0-9]{10})/i);
    if (asinMatch) {
      return asinMatch[1];
    }

    // If input is already a 10-character ASIN
    if (/^[A-Z0-9]{10}$/i.test(input)) {
      return input.toUpperCase();
    }

    throw new Error(`Invalid Amazon URL or ASIN: ${input}`);
  }

  private buildAmazonURL(asin: string): string {
    return `https://www.amazon.com/dp/${asin}/`;
  }

  private async delay(min: number = this.config.delayMin, max: number = this.config.delayMax): Promise<void> {
    const ms = Math.random() * (max - min) + min;
    logger.debug(`Waiting ${ms.toFixed(0)}ms...`);
    await new Promise(resolve => setTimeout(resolve, ms));
  }

  private async dismissPopups(page: Page): Promise<void> {
    try {
      // Wait for potential popups
      await page.waitForTimeout(1500);

      const popupSelectors = [
        'button:has-text("Dismiss")',
        'button:has-text("Accept")',
        'button:has-text("Accept Cookies")',
        '[data-action="dismiss"]',
        'button[aria-label*="Close"]',
        '.a-button-close',
      ];

      for (const selector of popupSelectors) {
        try {
          const element = await page.$(selector);
          if (element && (await element.isVisible())) {
            logger.info(`Dismissing popup: ${selector}`);
            await element.click();
            await page.waitForTimeout(1000);
            break;
          }
        } catch {
          continue;
        }
      }

      // Press Escape as fallback
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
    } catch (error) {
      logger.debug('Error dismissing popups (non-critical)');
    }
  }

  async scrape(input: string): Promise<BookData> {
    if (!this.browser) {
      await this.initialize();
    }

    const asin = this.extractASIN(input);
    const url = this.buildAmazonURL(asin);

    logger.info(`Scraping ASIN: ${asin} from ${url}`);

    for (let attempt = 1; attempt <= this.config.retries; attempt++) {
      const page = await this.browser!.newPage({
        viewport: { width: 1920, height: 1080 },
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        extraHTTPHeaders: {
          'Accept-Language': 'en-US,en;q=0.9',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
      });

      try {
        logger.info(`Attempt ${attempt}/${this.config.retries}`);

        // Random delay before navigation
        await this.delay();

        // Navigate to product page
        await page.goto(url, { waitUntil: 'networkidle', timeout: this.config.timeout });

        // Dismiss popups
        await this.dismissPopups(page);

        // Wait for product details section
        await page.waitForSelector('#productDetails_detailBullets_sections1, #detailBullets_feature_div, #detailBulletsWrapper_feature_div', {
          timeout: 10000,
        }).catch(() => logger.warn('Product details section not found, continuing...'));

        // Extract title
        const title = await page.$eval('#productTitle', el => el.textContent?.trim()).catch(() => {
          logger.warn('Title not found');
          return `Book ${asin}`;
        });

        // Extract BSR with fallback selectors
        const bsrData = await this.extractBSR(page);

        if (!bsrData) {
          throw new Error('BSR not found on page');
        }

        const bookData: BookData = {
          asin,
          title: title || `Book ${asin}`,
          rank: bsrData.rank,
          category: bsrData.category,
          timestamp: new Date(),
        };

        logger.info(`✅ Successfully scraped: ${title}, Rank: #${bsrData.rank.toLocaleString()}`);

        await page.close();
        return bookData;

      } catch (error) {
        logger.error(`Attempt ${attempt} failed: ${error}`);

        // Save error artifacts
        if (attempt === this.config.retries) {
          await this.saveErrorArtifacts(page, asin, error as Error);
        }

        await page.close();

        if (attempt < this.config.retries) {
          await this.delay(5000, 10000); // Longer delay between retries
        } else {
          throw new Error(`Failed to scrape after ${this.config.retries} attempts: ${error}`);
        }
      }
    }

    throw new Error('Scraping failed after all retries');
  }

  private async extractBSR(page: Page): Promise<{ rank: number; category: string } | null> {
    // Strategy 1: Look for text containing "Best Sellers Rank"
    try {
      const text = await page.textContent('body');
      if (!text) return null;

      // Pattern for BSR in Kindle Store
      const patterns = [
        /#([\d,]+)\s+in\s+Kindle\s+Store/i,
        /Best\s+Sellers\s+Rank:\s*#([\d,]+)\s+in\s+Kindle\s+Store/i,
        /Best\s+Sellers\s+Rank[:\s]*#?([\d,]+)\s+in\s+Kindle/i,
      ];

      for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match) {
          const rank = parseInt(match[1].replace(/,/g, ''));
          if (rank > 0 && rank < 10000000) {
            return { rank, category: 'Kindle Store' };
          }
        }
      }
    } catch (error) {
      logger.debug('Strategy 1 failed');
    }

    // Strategy 2: Check specific elements
    const selectors = [
      '#detailBullets_feature_div',
      '#productDetails_detailBullets_sections1',
      '#detailBulletsWrapper_feature_div',
      '.product-facts-detail',
    ];

    for (const selector of selectors) {
      try {
        const element = await page.$(selector);
        if (element) {
          const text = await element.textContent();
          if (text && text.includes('Best Sellers Rank')) {
            const match = text.match(/#([\d,]+)\s+in\s+Kindle\s+Store/i);
            if (match) {
              const rank = parseInt(match[1].replace(/,/g, ''));
              if (rank > 0 && rank < 10000000) {
                return { rank, category: 'Kindle Store' };
              }
            }
          }
        }
      } catch {
        continue;
      }
    }

    return null;
  }

  private async saveErrorArtifacts(page: Page, asin: string, error: Error): Promise<void> {
    try {
      const timestamp = Date.now();
      const screenshotPath = `./errors/screenshot_${asin}_${timestamp}.png`;
      const htmlPath = `./errors/html_${asin}_${timestamp}.html`;

      // Save screenshot
      await page.screenshot({ path: screenshotPath, fullPage: true });
      logger.info(`Saved screenshot: ${screenshotPath}`);

      // Save HTML
      const html = await page.content();
      const fs = await import('fs/promises');
      await fs.mkdir('./errors', { recursive: true });
      await fs.writeFile(htmlPath, html);
      logger.info(`Saved HTML: ${htmlPath}`);

    } catch (saveError) {
      logger.error(`Failed to save error artifacts: ${saveError}`);
    }
  }
}

export async function scrapeAmazonBSR(input: string, config?: ScraperConfig): Promise<BookData> {
  const scraper = new AmazonBSRScraper(config);
  try {
    await scraper.initialize();
    return await scraper.scrape(input);
  } finally {
    await scraper.close();
  }
}
