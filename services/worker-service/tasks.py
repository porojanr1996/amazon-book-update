"""
Celery tasks for worker service
"""
import sys
import os
import httpx
import logging
import time
from datetime import datetime
import pytz

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import celery_app from same directory
# Use direct import since we're in the same directory
from celery_app import celery_app
from shared.config import SHEETS_SERVICE_URL, SCRAPER_SERVICE_URL
from shared.utils.logger import setup_logger

logger = setup_logger('worker-service')

# HTTP client for inter-service communication
http_client = httpx.Client(timeout=300.0)


def call_sheets_service(endpoint: str, params: dict = None, method: str = 'GET', data: dict = None):
    """Call sheets-service endpoint"""
    try:
        url = f"{SHEETS_SERVICE_URL}{endpoint}"
        if method == 'GET':
            response = http_client.get(url, params=params)
        elif method == 'POST':
            response = http_client.post(url, json=data, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error calling sheets-service {endpoint}: {e}")
        raise


def call_scraper_service(endpoint: str, data: dict):
    """Call scraper-service endpoint"""
    try:
        url = f"{SCRAPER_SERVICE_URL}{endpoint}"
        response = http_client.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error calling scraper-service {endpoint}: {e}")
        raise


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
    logger.info(f"Starting BSR update task {task_id} for worksheet: {worksheet_name}")
    
    try:
        # Get books from sheets-service
        books = call_sheets_service("/api/books", {"worksheet": worksheet_name})
        
        if not books:
            logger.warning(f"No books found in worksheet '{worksheet_name}'")
            return {
                'status': 'completed',
                'worksheet': worksheet_name,
                'success_count': 0,
                'failure_count': 0,
                'total_books': 0
            }
        
        total_books = len(books)
        logger.info(f"Found {total_books} books to process")
        
        # Get today's row
        today_row_data = call_sheets_service("/api/today-row", {"worksheet": worksheet_name})
        today_row = today_row_data.get('row', 4)
        
        success_count = 0
        failure_count = 0
        
        # Process books sequentially to avoid rate limiting
        for idx, book in enumerate(books):
            if task_id:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': idx,
                        'total': total_books,
                        'status': f'Processing {book.get("name", "Unknown")}...',
                        'worksheet': worksheet_name
                    }
                )
            
            amazon_url = book.get('amazon_link')
            if not amazon_url:
                failure_count += 1
                continue
            
            try:
                # Extract BSR from scraper-service - try without Playwright first
                result = call_scraper_service("/api/extract-bsr", {
                    "amazon_url": amazon_url,
                    "use_playwright": False
                })
                
                bsr = result.get('bsr')
                
                # If failed, try with Playwright
                if not bsr or bsr <= 0:
                    logger.info(f"Retrying BSR extraction with Playwright for {book.get('name', 'Unknown')}...")
                    result = call_scraper_service("/api/extract-bsr", {
                        "amazon_url": amazon_url,
                        "use_playwright": True
                    })
                    bsr = result.get('bsr')
                
                if bsr and bsr > 0 and bsr <= 10000000:
                    # Update BSR in sheets-service
                    call_sheets_service("/api/update-bsr", method='POST', data={
                        "worksheet": worksheet_name,
                        "col": book.get('col'),
                        "row": today_row,
                        "bsr_value": bsr
                    })
                    
                    # Extract and cache cover image
                    try:
                        # Check if cover is already cached
                        from app.services.redis_cache import get_cache, set_cache
                        cache_key = f"cover:{amazon_url}"
                        cached_cover = get_cache(cache_key)
                        
                        if not cached_cover:
                            logger.info(f"📸 Extracting cover image for {book.get('name', 'Unknown')}...")
                            cover_result = call_scraper_service("/api/extract-cover", {
                                "amazon_url": amazon_url,
                                "use_playwright": False
                            })
                            
                            cover_url = cover_result.get('cover_url')
                            if not cover_url:
                                # Try with Playwright as fallback
                                cover_result = call_scraper_service("/api/extract-cover", {
                                    "amazon_url": amazon_url,
                                    "use_playwright": True
                                })
                                cover_url = cover_result.get('cover_url')
                            
                            if cover_url:
                                # Clean up image URL for better quality
                                import re
                                cover_url = re.sub(r'_SL\d+_', '_SL800_', cover_url)
                                cover_url = re.sub(r'\._AC_[^_]+_', '._AC_SL800_', cover_url)
                                if '_SL' not in cover_url:
                                    cover_url = cover_url.replace('._AC_', '._AC_SL800_')
                                cover_url = re.sub(r'_SX\d+_', '_SX800_', cover_url)
                                
                                # Cache cover image (24 hours TTL)
                                set_cache(cache_key, cover_url, 86400)
                                logger.info(f"✓ Cover image cached for {book.get('name', 'Unknown')}: {cover_url[:80]}...")
                            else:
                                # Cache None to avoid retrying too often
                                set_cache(cache_key, None, 86400)
                                logger.debug(f"✗ No cover found for {book.get('name', 'Unknown')}")
                    except Exception as cover_error:
                        logger.debug(f"Could not extract cover for {book.get('name', 'Unknown')}: {cover_error}")
                    
                    success_count += 1
                    logger.info(f"✓ Updated BSR: {bsr} for {book.get('name', 'Unknown')}")
                else:
                    failure_count += 1
                    logger.warning(f"✗ Invalid BSR for {book.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error processing {book.get('name', 'Unknown')}: {e}")
                failure_count += 1
            
            # Delay between requests
            if idx < total_books - 1:
                time.sleep(8)
        
        # Flush batch updates before calculating average
        try:
            call_sheets_service("/api/flush-updates", method='POST', data={
                "worksheet": worksheet_name
            })
            logger.info("✓ Flushed batch updates to Google Sheets")
        except Exception as e:
            logger.warning(f"Could not flush batch updates: {e}")
        
        # Calculate average
        try:
            call_sheets_service("/api/calculate-average", method='POST', data={
                "worksheet": worksheet_name,
                "row": today_row
            })
        except Exception as e:
            logger.error(f"Error calculating average: {e}")
        
        # Flush batch updates again after calculating average
        try:
            call_sheets_service("/api/flush-updates", method='POST', data={
                "worksheet": worksheet_name
            })
            logger.info("✓ Flushed batch updates after calculating average")
        except Exception as e:
            logger.warning(f"Could not flush batch updates: {e}")
        
        # Invalidate chart cache
        try:
            from app.services.redis_cache import delete_cache_pattern
            pattern = f"chart:*:{worksheet_name}"
            delete_cache_pattern(pattern)
            logger.info(f"✓ Invalidated chart cache for worksheet: {worksheet_name}")
        except Exception as e:
            logger.warning(f"Could not invalidate chart cache: {e}")
        
        result = {
            'status': 'completed',
            'worksheet': worksheet_name,
            'success_count': success_count,
            'failure_count': failure_count,
            'total_books': total_books
        }
        
        logger.info(f"✅ BSR update completed: {success_count} success, {failure_count} failures")
        return result
        
    except Exception as e:
        logger.error(f"Error in BSR update task: {e}", exc_info=True)
        raise


@celery_app.task(bind=True, name='covers.extract_all')
def extract_all_covers(worksheet_name: str):
    """
    Extract cover images for all books in a worksheet
    
    Args:
        worksheet_name: Name of the worksheet
    
    Returns:
        dict with success/failure counts
    """
    logger.info(f"Starting cover extraction for worksheet: {worksheet_name}")
    
    try:
        # Get books from sheets-service
        books = call_sheets_service("/api/books", {"worksheet": worksheet_name})
        
        success_count = 0
        failure_count = 0
        
        for idx, book in enumerate(books):
            amazon_url = book.get('amazon_link')
            if not amazon_url:
                continue
            
            try:
                # Extract cover from scraper-service
                result = call_scraper_service("/api/extract-cover", {
                    "amazon_url": amazon_url,
                    "use_playwright": True
                })
                
                if result.get('cover_url'):
                    success_count += 1
                    logger.info(f"✓ Cover extracted for {book.get('name', 'Unknown')}")
                else:
                    failure_count += 1
            except Exception as e:
                logger.error(f"Error extracting cover for {book.get('name', 'Unknown')}: {e}")
                failure_count += 1
            
            # Delay between requests
            if idx < len(books) - 1:
                time.sleep(10)
        
        logger.info(f"✅ Cover extraction completed: {success_count} success, {failure_count} failures")
        return {
            'status': 'completed',
            'worksheet': worksheet_name,
            'success_count': success_count,
            'failure_count': failure_count,
            'total_books': len(books)
        }
        
    except Exception as e:
        logger.error(f"Error in cover extraction task: {e}", exc_info=True)
        raise

