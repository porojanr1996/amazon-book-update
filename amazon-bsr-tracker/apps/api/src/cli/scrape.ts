#!/usr/bin/env ts-node

import { scrapeAmazonBSR } from '@bsr-tracker/scraper';

const url = process.argv[2];

if (!url) {
  console.error('Usage: npm run scrape <amazon-url-or-asin>');
  process.exit(1);
}

(async () => {
  try {
    console.log(`🔍 Scraping: ${url}`);
    const data = await scrapeAmazonBSR(url);
    console.log('✅ Success:');
    console.log(JSON.stringify(data, null, 2));
  } catch (error) {
    console.error('❌ Scraping failed:', error);
    process.exit(1);
  }
})();
