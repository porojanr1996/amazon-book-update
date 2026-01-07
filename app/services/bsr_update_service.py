"""
BSR update service - handles daily and manual BSR updates
"""
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pytz

from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
from app.services.sheets_service import get_sheets_manager
from app.services.cache_service import invalidate_chart_cache
import config

logger = logging.getLogger(__name__)


def run_worksheet_bsr_update(worksheet_name: str):
    """
    Update BSR for all books in a specific worksheet
    """
    logger.info("=" * 50)
    logger.info(f"Starting BSR update for worksheet: {worksheet_name}")
    logger.info(f"Time: {datetime.now(pytz.timezone('Europe/Bucharest'))}")
    logger.info("=" * 50)
    
    try:
        # Initialize components
        sheets_manager = get_sheets_manager()
        amazon_scraper = AmazonScraper(
            delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
            retry_attempts=config.AMAZON_RETRY_ATTEMPTS
        )
        
        # Get all books from the specific worksheet
        books = sheets_manager.get_all_books(worksheet_name=worksheet_name)
        if not books:
            logger.warning(f"No books found in worksheet '{worksheet_name}'")
            return
        
        logger.info(f"Found {len(books)} books to process in worksheet '{worksheet_name}'")
        
        # Get today's row for this worksheet
        today_row = sheets_manager.get_today_row(worksheet_name=worksheet_name)
        logger.info(f"Today's BSR for {worksheet_name} will be written to row {today_row}")
        
        # Process books in parallel using threading
        success_count = 0
        failure_count = 0
        count_lock = Lock()
        
        def process_book(book):
            """Process a single book in a thread"""
            nonlocal success_count, failure_count
            
            # Create a new scraper instance for each thread (thread-safe)
            thread_scraper = AmazonScraper(
                delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
                retry_attempts=config.AMAZON_RETRY_ATTEMPTS
            )
            
            logger.info(f"Processing: {book['name']} by {book['author']} in {worksheet_name}")
            logger.info(f"Amazon URL: {book['amazon_link']}")
            
            try:
                # Extract BSR
                bsr = thread_scraper.extract_bsr(book['amazon_link'])
                
                if bsr:
                    # Get today's row again (in case it changed) for the specific worksheet
                    current_today_row = sheets_manager.get_today_row(worksheet_name=worksheet_name)
                    sheets_manager.update_bsr(book['col'], current_today_row, bsr, worksheet_name=worksheet_name)
                    logger.info(f"✓ Successfully updated BSR: {bsr} for {book['name']} in {worksheet_name}")
                    with count_lock:
                        success_count += 1
                    return True
                else:
                    logger.warning(f"✗ Could not extract BSR for {book['name']} in {worksheet_name}")
                    with count_lock:
                        failure_count += 1
                    return False
            except Exception as e:
                logger.error(f"✗ Error processing {book['name']} in {worksheet_name}: {e}", exc_info=True)
                with count_lock:
                    failure_count += 1
                return False
        
        # Use ThreadPoolExecutor for parallel processing
        max_workers = min(config.AMAZON_MAX_WORKERS, len(books))
        logger.info(f"Processing {len(books)} books with {max_workers} threads in parallel for {worksheet_name}...")
        
        process_start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for idx, book in enumerate(books, 1):
                if idx > 1:
                    time.sleep(config.AMAZON_DELAY_BETWEEN_REQUESTS / max_workers)
                future = executor.submit(process_book, book)
                futures[future] = book
            
            for future in as_completed(futures):
                book = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Fatal error processing {book['name']} in {worksheet_name}: {e}", exc_info=True)
        
        elapsed_time = time.time() - process_start_time
        logger.info(f"Processing for {worksheet_name} completed in {elapsed_time:.2f} seconds ({len(books)/elapsed_time:.2f} books/sec)")
        
        # Calculate and update average BSR for today's row for this worksheet
        try:
            logger.info(f"Calculating average BSR for today in worksheet: {worksheet_name}...")
            current_today_row = sheets_manager.get_today_row(worksheet_name=worksheet_name)
            sheets_manager.calculate_and_update_average(current_today_row, worksheet_name=worksheet_name)
            logger.info(f"✓ Average BSR calculated and updated successfully for {worksheet_name}")
            
            # Flush all buffered updates to Google Sheets
            logger.info(f"Flushing buffered updates to Google Sheets for {worksheet_name}...")
            sheets_manager.flush_batch_updates(worksheet_name=worksheet_name)
            logger.info(f"✓ All updates flushed to Google Sheets for {worksheet_name}")
            
            # Invalidate caches for this worksheet
            invalidate_chart_cache(worksheet_name=worksheet_name)
            from app.services.sheets_cache import invalidate_metadata
            invalidate_metadata(worksheet_name)
            
            # Update Last-Modified timestamps (so clients know data changed)
            from app.services.etag_service import set_last_modified
            set_last_modified(worksheet_name, 'chart')
            set_last_modified(worksheet_name, 'rankings')
        except Exception as e:
            logger.error(f"✗ Error calculating average BSR or flushing updates for {worksheet_name}: {e}", exc_info=True)
        
        logger.info("=" * 50)
        logger.info(f"BSR update completed for worksheet: {worksheet_name}")
        logger.info(f"Success: {success_count}")
        logger.info(f"Failures: {failure_count}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Error in worksheet BSR update: {e}", exc_info=True)


def run_daily_bsr_update():
    """
    Function to update BSR ratings daily for all worksheets
    This function is called by the scheduler at 10:01 AM Bucharest time
    """
    logger.info("=" * 50)
    logger.info("Starting scheduled daily BSR update for all worksheets...")
    logger.info(f"Time: {datetime.now(pytz.timezone('Europe/Bucharest'))}")
    
    sheets_manager = get_sheets_manager()
    
    # Get all worksheet names
    all_worksheets = sheets_manager.get_all_worksheets()
    if not all_worksheets:
        logger.error("No worksheets found in Google Spreadsheet. Aborting daily update.")
        return
    
    total_success_count = 0
    total_failure_count = 0
    
    for worksheet_name in all_worksheets:
        logger.info(f"\n--- Processing worksheet: {worksheet_name} ---")
        run_worksheet_bsr_update(worksheet_name)
        # Note: success/failure counts are logged within run_worksheet_bsr_update
    
    logger.info("=" * 50)
    logger.info("Daily BSR update completed for all worksheets")
    logger.info("=" * 50)

