#!/usr/bin/env ts-node

import { scrapeAllBooks } from '../services/scheduler';

(async () => {
  try {
    console.log('🔍 Scraping all tracked books...');
    await scrapeAllBooks();
    console.log('✅ All books scraped');
  } catch (error) {
    console.error('❌ Scraping failed:', error);
    process.exit(1);
  }
})();
