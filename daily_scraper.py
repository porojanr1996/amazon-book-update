"""
Daily BSR Scraper
Main script that runs daily to scrape BSR values and update Google Sheets
"""
import logging
import sys
from datetime import datetime
from amazon_scraper import AmazonScraper
from google_sheets_transposed import GoogleSheetsManager
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_daily_scrape():
    """Main function to run daily BSR scraping"""
    logger.info("=" * 50)
    logger.info("Starting daily BSR scrape")
    logger.info(f"Time: {datetime.now()}")
    logger.info("=" * 50)
    
    try:
        # Initialize components
        sheets_manager = GoogleSheetsManager(
            config.GOOGLE_SHEETS_CREDENTIALS_PATH,
            config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        
        amazon_scraper = AmazonScraper(
            delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
            retry_attempts=config.AMAZON_RETRY_ATTEMPTS
        )
        
        # Get all books from Google Sheets
        books = sheets_manager.get_all_books()
        
        if not books:
            logger.warning("No books found in Google Sheets")
            return
        
        logger.info(f"Found {len(books)} books to process")
        
        # Get today's row (for transposed format)
        today_row = sheets_manager.get_today_row()
        logger.info(f"Today's BSR will be written to row {today_row}")
        
        # Process each book
        success_count = 0
        failure_count = 0
        
        for book in books:
            logger.info(f"Processing: {book['name']} by {book['author']}")
            logger.info(f"Amazon URL: {book['amazon_link']}")
            
            bsr = amazon_scraper.extract_bsr(book['amazon_link'])
            
            if bsr:
                try:
                    today_row = sheets_manager.get_today_row()
                    sheets_manager.update_bsr(book['col'], today_row, bsr)
                    logger.info(f"✓ Successfully updated BSR: {bsr}")
                    success_count += 1
                except Exception as e:
                    logger.error(f"✗ Failed to update Google Sheets: {e}")
                    failure_count += 1
            else:
                logger.warning(f"✗ Could not extract BSR for {book['name']}")
                failure_count += 1
        
        # Summary
        logger.info("=" * 50)
        logger.info("Daily scrape completed")
        logger.info(f"Success: {success_count}")
        logger.info(f"Failures: {failure_count}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Fatal error in daily scrape: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    run_daily_scrape()

