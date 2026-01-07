"""
Celery tasks for BSR updates
"""
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pytz

from app.celery_app import celery_app
from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
from app.services.sheets_service import get_sheets_manager
from app.services.cache_service import invalidate_chart_cache
import config

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='bsr.update_worksheet')
def update_worksheet_bsr(self, worksheet_name: str):
    """
    Celery task to update BSR for all books in a specific worksheet
    
    Args:
        worksheet_name: Name of the worksheet to update
    
    Returns:
        dict with success/failure counts
    """
    task_id = self.request.id if self.request else None
    logger.info("=" * 50)
    logger.info(f"Starting BSR update task {task_id} for worksheet: {worksheet_name}")
    logger.info(f"Time: {datetime.now(pytz.timezone('Europe/Bucharest'))}")
    logger.info("=" * 50)
    
    # Helper function to safely update state only if task_id exists
    def safe_update_state(state, meta):
        """Update task state only if running in Celery context"""
        if task_id:
            try:
                self.update_state(state=state, meta=meta)
            except Exception as e:
                logger.warning(f"Could not update task state: {e}")
        else:
            logger.info(f"[{state}] {meta.get('status', '')}")
    
    try:
        # Update task state
        safe_update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': 0,
                'status': f'Initializing update for worksheet: {worksheet_name}',
                'worksheet': worksheet_name
            }
        )
        
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
            return {
                'status': 'completed',
                'worksheet': worksheet_name,
                'success_count': 0,
                'failure_count': 0,
                'total_books': 0,
                'message': f'No books found in worksheet "{worksheet_name}"'
            }
        
        total_books = len(books)
        logger.info(f"Found {total_books} books to process in worksheet '{worksheet_name}'")
        
        # Get today's row for this worksheet
        today_row = sheets_manager.get_today_row(worksheet_name=worksheet_name)
        logger.info(f"Today's BSR for {worksheet_name} will be written to row {today_row}")
        
        # Update task state
        safe_update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': total_books,
                'status': f'Processing {total_books} books...',
                'worksheet': worksheet_name
            }
        )
        
        # Process books in parallel using threading
        success_count = 0
        failure_count = 0
        count_lock = Lock()
        processed_count = 0
        
        def process_book(book):
            """Process a single book in a thread"""
            nonlocal success_count, failure_count, processed_count
            
            # Create a new scraper instance for each thread (thread-safe)
            thread_scraper = AmazonScraper(
                delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
                retry_attempts=config.AMAZON_RETRY_ATTEMPTS
            )
            
            logger.info(f"Processing: {book['name']} by {book['author']} in {worksheet_name}")
            logger.info(f"Amazon URL: {book['amazon_link']}")
            
            try:
                amazon_url = book['amazon_link']
                logger.info(f"🔍 Extracting BSR for {book['name']} from {amazon_url}")
                
                # Extract BSR (strict parser ensures no invalid values)
                bsr = thread_scraper.extract_bsr(amazon_url, use_playwright=False)
                
                if bsr:
                    logger.info(f"✓ BSR extracted: {bsr} for {book['name']}")
                else:
                    logger.warning(f"✗ BSR extraction returned None for {book['name']}, trying Playwright...")
                    # Try Playwright as fallback
                    bsr = thread_scraper.extract_bsr(amazon_url, use_playwright=True)
                    if bsr:
                        logger.info(f"✓ BSR extracted with Playwright: {bsr} for {book['name']}")
                
                # Double-check: never write invalid BSR values
                if bsr and bsr > 0 and bsr <= 10000000:
                    # Get today's row again (in case it changed) for the specific worksheet
                    current_today_row = sheets_manager.get_today_row(worksheet_name=worksheet_name)
                    sheets_manager.update_bsr(book['col'], current_today_row, bsr, worksheet_name=worksheet_name)
                    logger.info(f"✅ Successfully updated BSR: {bsr} for {book['name']} in {worksheet_name} (row {current_today_row}, col {book['col']})")
                    
                    # Also extract and cache cover image if not already cached
                    try:
                        from app.services.cache_service import get_cached_cover, set_cached_cover
                        cached_cover = get_cached_cover(amazon_url)
                        if not cached_cover:
                            logger.info(f"📸 Extracting cover image for {book['name']}...")
                            cover_url = thread_scraper.extract_cover_image(amazon_url, use_playwright=False)
                            if not cover_url:
                                # Try with Playwright as fallback
                                cover_url = thread_scraper.extract_cover_image(amazon_url, use_playwright=True)
                            
                            if cover_url:
                                # Clean up image URL for better quality
                                import re
                                cover_url = re.sub(r'_SL\d+_', '_SL800_', cover_url)
                                cover_url = re.sub(r'\._AC_[^_]+_', '._AC_SL800_', cover_url)
                                if '_SL' not in cover_url:
                                    cover_url = cover_url.replace('._AC_', '._AC_SL800_')
                                cover_url = re.sub(r'_SX\d+_', '_SX800_', cover_url)
                                set_cached_cover(amazon_url, cover_url)
                                logger.info(f"✓ Cover image cached for {book['name']}: {cover_url[:80]}...")
                            else:
                                # Cache None to avoid retrying too often
                                set_cached_cover(amazon_url, None)
                                logger.debug(f"✗ No cover found for {book['name']}")
                    except Exception as cover_error:
                        logger.debug(f"Could not extract cover for {book['name']}: {cover_error}")
                    
                    with count_lock:
                        success_count += 1
                        processed_count += 1
                    return True
                else:
                    logger.warning(f"✗ Invalid BSR value ({bsr}) for {book['name']} in {worksheet_name}")
                    with count_lock:
                        failure_count += 1
                        processed_count += 1
                    return False
            except Exception as e:
                    logger.error(f"✗ Error processing {book['name']} in {worksheet_name}: {e}", exc_info=True)
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    with count_lock:
                        failure_count += 1
                        processed_count += 1
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
            
            # Update progress as tasks complete
            for future in as_completed(futures):
                book = futures[future]
                try:
                    future.result()
                    # Update task state periodically
                    with count_lock:
                        current_processed = processed_count
                    if current_processed % 5 == 0 or current_processed == total_books:
                        safe_update_state(
                            state='PROGRESS',
                            meta={
                                'current': current_processed,
                                'total': total_books,
                                'status': f'Processed {current_processed}/{total_books} books...',
                                'worksheet': worksheet_name,
                                'success_count': success_count,
                                'failure_count': failure_count
                            }
                        )
                except Exception as e:
                    logger.error(f"Fatal error processing {book['name']} in {worksheet_name}: {e}", exc_info=True)
        
        elapsed_time = time.time() - process_start_time
        logger.info(f"Processing for {worksheet_name} completed in {elapsed_time:.2f} seconds ({len(books)/elapsed_time:.2f} books/sec)")
        
        # Calculate and update average BSR for today's row for this worksheet
        try:
            safe_update_state(
                state='PROGRESS',
                meta={
                    'current': total_books,
                    'total': total_books,
                    'status': 'Calculating average BSR...',
                    'worksheet': worksheet_name
                }
            )
            
            logger.info(f"Calculating average BSR for today in worksheet: {worksheet_name}...")
            current_today_row = sheets_manager.get_today_row(worksheet_name=worksheet_name)
            sheets_manager.calculate_and_update_average(current_today_row, worksheet_name=worksheet_name)
            logger.info(f"✓ Average BSR calculated and updated successfully for {worksheet_name}")
            
            # Flush all buffered updates to Google Sheets
            logger.info(f"Flushing buffered updates to Google Sheets for {worksheet_name}...")
            sheets_manager.flush_batch_updates(worksheet_name=worksheet_name)
            logger.info(f"✓ All updates flushed to Google Sheets for {worksheet_name}")
            
            # Invalidate caches for this worksheet
            logger.info(f"Invalidating caches for worksheet: {worksheet_name}")
            try:
                invalidate_chart_cache(worksheet_name=worksheet_name)
                logger.info(f"✓ Chart cache invalidated for {worksheet_name}")
            except Exception as e:
                logger.error(f"✗ Error invalidating chart cache: {e}", exc_info=True)
            
            try:
                from app.services.sheets_cache import invalidate_metadata
                invalidate_metadata(worksheet_name)
                logger.info(f"✓ Metadata cache invalidated for {worksheet_name}")
            except Exception as e:
                logger.error(f"✗ Error invalidating metadata cache: {e}", exc_info=True)
            
            # Update Last-Modified timestamps (so clients know data changed)
            try:
                from app.services.etag_service import set_last_modified
                set_last_modified(worksheet_name, 'chart')
                set_last_modified(worksheet_name, 'rankings')
                logger.info(f"✓ Last-Modified timestamps updated for {worksheet_name}")
            except Exception as e:
                logger.error(f"✗ Error updating Last-Modified timestamps: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"✗ Error calculating average BSR or flushing updates for {worksheet_name}: {e}", exc_info=True)
        
        result = {
            'status': 'completed',
            'worksheet': worksheet_name,
            'success_count': success_count,
            'failure_count': failure_count,
            'total_books': total_books,
            'elapsed_time': elapsed_time,
            'message': f'BSR update completed: {success_count} success, {failure_count} failures'
        }
        
        logger.info("=" * 50)
        logger.info(f"BSR update completed for worksheet: {worksheet_name}")
        logger.info(f"Success: {success_count}")
        logger.info(f"Failures: {failure_count}")
        logger.info("=" * 50)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in worksheet BSR update task: {e}", exc_info=True)
        safe_update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'worksheet': worksheet_name
            }
        )
        raise


@celery_app.task(bind=True, name='bsr.update_all_worksheets')
def update_all_worksheets_bsr(self):
    """
    Celery task to update BSR for all worksheets
    
    Returns:
        dict with results for each worksheet
    """
    task_id = self.request.id if self.request else None
    logger.info("=" * 50)
    logger.info(f"Starting BSR update task {task_id} for all worksheets")
    logger.info(f"Time: {datetime.now(pytz.timezone('Europe/Bucharest'))}")
    logger.info("=" * 50)
    
    # Helper function to safely update state only if task_id exists
    def safe_update_state(state, meta):
        """Update task state only if running in Celery context"""
        if task_id:
            try:
                self.update_state(state=state, meta=meta)
            except Exception as e:
                logger.warning(f"Could not update task state: {e}")
        else:
            logger.info(f"[{state}] {meta.get('status', '')}")
    
    try:
        sheets_manager = get_sheets_manager()
        
        # Get all worksheet names
        all_worksheets = sheets_manager.get_all_worksheets()
        if not all_worksheets:
            logger.error("No worksheets found in Google Spreadsheet. Aborting daily update.")
            return {
                'status': 'completed',
                'total_worksheets': 0,
                'results': [],
                'message': 'No worksheets found'
            }
        
        total_worksheets = len(all_worksheets)
        
        safe_update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': total_worksheets,
                'status': f'Processing {total_worksheets} worksheets...',
                'worksheets': all_worksheets
            }
        )
        
        results = []
        for idx, worksheet_name in enumerate(all_worksheets, 1):
            logger.info(f"\n--- Processing worksheet {idx}/{total_worksheets}: {worksheet_name} ---")
            
            # Update each worksheet using the single worksheet task
            worksheet_task = update_worksheet_bsr.delay(worksheet_name)
            
            # Wait for completion and get result
            try:
                worksheet_result = worksheet_task.get(timeout=3600)  # 1 hour timeout
                results.append(worksheet_result)
            except Exception as e:
                logger.error(f"Error processing worksheet {worksheet_name}: {e}")
                results.append({
                    'worksheet': worksheet_name,
                    'status': 'failed',
                    'error': str(e)
                })
            
            # Update progress
            safe_update_state(
                state='PROGRESS',
                meta={
                    'current': idx,
                    'total': total_worksheets,
                    'status': f'Completed {idx}/{total_worksheets} worksheets...',
                    'results': results
                }
            )
        
        total_success = sum(r.get('success_count', 0) for r in results if isinstance(r, dict))
        total_failure = sum(r.get('failure_count', 0) for r in results if isinstance(r, dict))
        
        result = {
            'status': 'completed',
            'total_worksheets': total_worksheets,
            'results': results,
            'total_success': total_success,
            'total_failure': total_failure,
            'message': f'All worksheets processed: {total_success} success, {total_failure} failures'
        }
        
        logger.info("=" * 50)
        logger.info("Daily BSR update completed for all worksheets")
        logger.info(f"Total Success: {total_success}")
        logger.info(f"Total Failures: {total_failure}")
        logger.info("=" * 50)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in all worksheets BSR update task: {e}", exc_info=True)
        safe_update_state(
            state='FAILURE',
            meta={
                'error': str(e)
            }
        )
        raise

