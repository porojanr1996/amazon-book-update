"""
FastAPI routes - maintains backward compatibility with Flask routes
"""
from fastapi import APIRouter, HTTPException, Query, Request, Form, Header
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from typing import Optional, List
import logging
import re
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pytz
from apscheduler.triggers.date import DateTrigger

from app.models.schemas import (
    Book, ChartData, ErrorResponse, SuccessResponse, SchedulerStatus, JobStatus
)
from app.services.sheets_service import (
    get_all_worksheets, get_books_for_worksheet, get_default_worksheet
)
from app.services.chart_service import get_chart_data
from app.services.cache_service import (
    get_cached_cover, set_cached_cover, clear_all_caches, invalidate_chart_cache
)
from app.services.redis_cache import get_or_set
from app.services.etag_service import (
    generate_etag, get_last_modified, set_last_modified,
    check_if_none_match, check_if_modified_since
)
from amazon_scraper import AmazonScraper
import config

logger = logging.getLogger(__name__)

router = APIRouter()

# Templates directory
templates = Jinja2Templates(directory="templates")

# Helper function for url_for in templates (FastAPI compatible)
def url_for_static(filename: str, base_path: str = "") -> str:
    """Generate URL for static files
    filename can be like 'css/style.css' or 'js/app.js'
    """
    # Remove leading slash if present
    filename = filename.lstrip('/')
    return f"{base_path}/static/{filename}"


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page"""
    # Get base path from X-Script-Name header or request path
    base_path = request.headers.get("X-Script-Name", "")
    
    # Check if accessed via subdomain (books-reporting.novamediamarketing.net)
    host = request.headers.get("Host", "")
    if "books-reporting.novamediamarketing.net" in host:
        base_path = ""  # No prefix needed for subdomain
    elif not base_path:
        # Try to extract from request path
        path = str(request.url.path)
        if path.startswith("/books-reporting"):
            base_path = "/books-reporting"
    
    # Create url_for function with base_path
    def url_for_with_base(filename: str) -> str:
        return url_for_static(filename, base_path)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "url_for": url_for_with_base,
        "base_path": base_path
    })


@router.get("/api/worksheets", response_model=List[str])
async def get_worksheets():
    """Get all worksheet names from the Google Spreadsheet (excluding Sheet1 and Sheet3)"""
    try:
        all_worksheets = await get_all_worksheets()
        
        # Filter out Sheet1 and Sheet3
        filtered_worksheets = [ws for ws in all_worksheets if ws not in ['Sheet1', 'Sheet3']]
        
        logger.info(f"Found {len(all_worksheets)} total worksheets: {all_worksheets}")
        logger.info(f"Returning {len(filtered_worksheets)} filtered worksheets (excluding Sheet1, Sheet3): {filtered_worksheets}")
        return filtered_worksheets
    except Exception as e:
        logger.error(f"Error getting worksheets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/books", response_model=List[Book])
async def get_books(worksheet: Optional[str] = Query(None, alias="worksheet")):
    """Get all books with BSR history for a specific worksheet"""
    try:
        worksheet_name = worksheet or await get_default_worksheet()
        books_data = await get_books_for_worksheet(worksheet_name)
        return books_data
    except Exception as e:
        logger.error(f"Error getting books: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/rankings", response_model=List[Book])
async def get_rankings(
    worksheet: Optional[str] = Query(None, alias="worksheet"),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    if_modified_since: Optional[str] = Header(None, alias="If-Modified-Since")
):
    """Get all rankings for a specific worksheet (with ETag and Last-Modified support)"""
    try:
        worksheet_name = worksheet or await get_default_worksheet()
        
        logger.info(f"Getting rankings for worksheet: {worksheet_name}")
        books_data = await get_books_for_worksheet(worksheet_name)
        
        logger.info(f"Total books found in worksheet '{worksheet_name}': {len(books_data)}")
        
        # Separate books with and without BSR
        books_with_bsr = [b for b in books_data if b.get('current_bsr') is not None]
        books_without_bsr = [b for b in books_data if b.get('current_bsr') is None]
        
        logger.info(f"Books with BSR: {len(books_with_bsr)}, Books without BSR: {len(books_without_bsr)}")
        
        # Sort books with BSR by current BSR (lower is better)
        books_with_bsr.sort(key=lambda x: x['current_bsr'])
        
        # Combine: books with BSR first (sorted), then books without BSR
        all_books = books_with_bsr + books_without_bsr
        
        logger.info(f"Returning all {len(all_books)} books from worksheet '{worksheet_name}'")
        
        # Extract cover images for all books (with caching and threading)
        def extract_cover_for_book(book_data):
            """Extract cover image for a single book in a thread"""
            book, idx = book_data
            amazon_link = book.get('amazon_link')
            if not amazon_link or book.get('cover_image'):
                return book
            
            # Validate that amazon_link is actually a URL (not a BSR number or invalid data)
            if not isinstance(amazon_link, str) or not amazon_link.startswith(('http://', 'https://', 'www.')):
                logger.warning(f"Invalid amazon_link for {book.get('name', 'Unknown')}: {amazon_link[:50] if amazon_link else 'None'}")
                book['cover_image'] = None
                return book
            
            # Check cache first
            try:
                cached_cover = get_cached_cover(amazon_link)
                if cached_cover:
                    book['cover_image'] = cached_cover
                    logger.debug(f"Using cached cover for {book['name']}")
                    return book
            except Exception as e:
                logger.debug(f"Cache check failed for {book['name']}: {e}, will extract fresh")
            
            # Extract cover if not in cache
            try:
                thread_scraper = AmazonScraper(
                    delay_between_requests=0.1,
                    retry_attempts=1
                )
                
                cover_url = thread_scraper.extract_cover_image(amazon_link, use_playwright=True)
                
                if cover_url:
                    # Clean up image URL for better quality
                    cover_url = re.sub(r'_SL\d+_', '_SL800_', cover_url)
                    cover_url = re.sub(r'\._AC_[^_]+_', '._AC_SL800_', cover_url)
                    if '_SL' not in cover_url:
                        cover_url = cover_url.replace('._AC_', '._AC_SL800_')
                    cover_url = re.sub(r'_SX\d+_', '_SX800_', cover_url)
                    book['cover_image'] = cover_url
                    try:
                        set_cached_cover(amazon_link, cover_url)
                    except Exception as cache_err:
                        logger.warning(f"Failed to cache cover for {book['name']}: {cache_err}")
                    logger.info(f"✓ Extracted cover for {book['name']}: {cover_url[:80]}...")
                else:
                    book['cover_image'] = None
                    try:
                        set_cached_cover(amazon_link, None)
                    except Exception as cache_err:
                        logger.warning(f"Failed to cache None cover for {book['name']}: {cache_err}")
                    logger.debug(f"✗ No cover found for {book['name']}")
            except Exception as e:
                logger.error(f"Error extracting cover for {book['name']}: {e}", exc_info=True)
                book['cover_image'] = None
                try:
                    set_cached_cover(amazon_link, None)
                except Exception as cache_err:
                    logger.warning(f"Failed to cache error cover for {book['name']}: {cache_err}")
            
            return book
        
        # Use ThreadPoolExecutor for parallel cover extraction
        books_needing_covers = [(book, idx) for idx, book in enumerate(all_books) 
                                if book.get('amazon_link') and not book.get('cover_image')]
        
        if books_needing_covers:
            max_workers = min(
                max(config.AMAZON_MAX_WORKERS, 5),
                len(books_needing_covers),
                10
            )
            logger.info(f"Extracting covers for {len(books_needing_covers)} books with {max_workers} threads (optimized)...")
            
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(extract_cover_for_book, book_data): book_data 
                    for book_data in books_needing_covers
                }
                
                completed_count = 0
                for future in as_completed(futures):
                    book_data = futures[future]
                    try:
                        updated_book = future.result()
                        book_idx = book_data[1]
                        all_books[book_idx] = updated_book
                        completed_count += 1
                        if completed_count % 5 == 0:
                            logger.debug(f"Extracted {completed_count}/{len(books_needing_covers)} covers...")
                    except Exception as e:
                        logger.error(f"Error extracting cover for book {book_data[0].get('name', 'Unknown')}: {e}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Cover extraction completed: {len(books_needing_covers)} books in {elapsed_time:.2f}s")
        
        # Generate ETag from data
        etag = generate_etag(all_books)
        
        # Check If-None-Match header
        if if_none_match and check_if_none_match(if_none_match, etag):
            logger.info(f"ETag match for rankings ({worksheet_name}), returning 304")
            return Response(status_code=304)
        
        # Get Last-Modified timestamp
        last_modified = get_last_modified(worksheet_name, 'rankings')
        if not last_modified:
            # Set Last-Modified if not exists
            set_last_modified(worksheet_name, 'rankings')
            last_modified = get_last_modified(worksheet_name, 'rankings')
        
        # Check If-Modified-Since header
        if if_modified_since and last_modified:
            if not check_if_modified_since(if_modified_since, last_modified):
                logger.info(f"Not modified since {if_modified_since} for rankings ({worksheet_name}), returning 304")
                return Response(status_code=304)
        
        # Convert books to dict for JSON serialization
        books_dict = []
        covers_found = 0
        for book in all_books:
            if hasattr(book, 'dict'):
                book_dict = book.dict()
            elif isinstance(book, dict):
                book_dict = book.copy()
            else:
                # Fallback: convert to dict manually
                book_dict = {
                    'name': getattr(book, 'name', ''),
                    'author': getattr(book, 'author', None),
                    'amazon_link': getattr(book, 'amazon_link', None),
                    'category': getattr(book, 'category', None),
                    'bsr_history': getattr(book, 'bsr_history', []),
                    'current_bsr': getattr(book, 'current_bsr', None),
                    'cover_image': getattr(book, 'cover_image', None),
                    'col': getattr(book, 'col', None)
                }
            
            # Ensure cover_image is included (double-check)
            if 'cover_image' not in book_dict:
                book_dict['cover_image'] = book.get('cover_image') if isinstance(book, dict) else getattr(book, 'cover_image', None)
            
            # Convert None to null for JSON (None becomes null in JSON, which is falsy in JS)
            if book_dict.get('cover_image') is None:
                book_dict['cover_image'] = None  # Keep as None/null for JSON
            
            if book_dict.get('cover_image'):
                covers_found += 1
            
            books_dict.append(book_dict)
        
        logger.info(f"Returning {len(books_dict)} books, {covers_found} with cover images")
        
        # Return response with ETag and Last-Modified headers
        response = JSONResponse(content=books_dict)
        response.headers["ETag"] = etag
        if last_modified:
            response.headers["Last-Modified"] = last_modified
        response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
        
        return response
    except Exception as e:
        logger.error(f"Error getting rankings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/chart-data", response_model=ChartData)
async def get_chart_data_endpoint(
    range: str = Query("30", alias="range"),
    worksheet: Optional[str] = Query(None, alias="worksheet"),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    if_modified_since: Optional[str] = Header(None, alias="If-Modified-Since")
):
    """Get chart data for a specific time range and worksheet (with ETag and Last-Modified support)"""
    try:
        from app.services.sheets_service import get_default_worksheet
        
        worksheet_name = worksheet or await get_default_worksheet()
        
        # Get chart data
        chart_data = await get_chart_data(range, worksheet_name)
        
        # Generate ETag from data
        etag = generate_etag(chart_data)
        
        # Check If-None-Match header
        if if_none_match and check_if_none_match(if_none_match, etag):
            logger.info(f"ETag match for chart data ({range}:{worksheet_name}), returning 304")
            return Response(status_code=304)
        
        # Get Last-Modified timestamp
        last_modified = get_last_modified(worksheet_name, 'chart')
        if not last_modified:
            # Set Last-Modified if not exists
            set_last_modified(worksheet_name, 'chart')
            last_modified = get_last_modified(worksheet_name, 'chart')
        
        # Check If-Modified-Since header
        if if_modified_since and last_modified:
            if not check_if_modified_since(if_modified_since, last_modified):
                logger.info(f"Not modified since {if_modified_since} for chart data ({range}:{worksheet_name}), returning 304")
                return Response(status_code=304)
        
        # Convert to dict if needed
        chart_dict = chart_data.dict() if hasattr(chart_data, 'dict') else chart_data
        
        # Return response with ETag and Last-Modified headers
        response = JSONResponse(content=chart_dict)
        response.headers["ETag"] = etag
        if last_modified:
            response.headers["Last-Modified"] = last_modified
        response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
        
        return response
    except Exception as e:
        logger.error(f"Error getting chart data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/clear-cache")
async def clear_cache():
    """Clear all caches (for debugging)"""
    try:
        clear_all_caches()
        logger.info("All caches cleared")
        return {"status": "success", "message": "All caches cleared"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/update-bsr")
@router.post("/api/trigger-bsr-update")
async def trigger_bsr_update(request: Request):
    """
    Manually trigger BSR update for a specific worksheet
    Runs update_bsr.py logic for the selected worksheet
    """
    try:
        import threading
        
        # Parse request body
        body = await request.json()
        worksheet_name = body.get('worksheet', '')
        
        if not worksheet_name:
            raise HTTPException(status_code=400, detail="Worksheet name is required")
        
        logger.info(f"Manual BSR update triggered via API for worksheet: {worksheet_name}")
        
        # Import function from update_bsr.py
        import sys
        from pathlib import Path
        
        # Add project root to path to import update_bsr
        project_root = Path(__file__).parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from update_bsr import update_bsr_for_worksheets
        
        # Run update in background thread (non-blocking)
        def run_update():
            """Run BSR update in background"""
            try:
                # Create new event loop for this thread (Playwright needs it)
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                logger.info(f"Starting BSR update for {worksheet_name} in background thread")
                success = update_bsr_for_worksheets([worksheet_name], dry_run=False)
                if success:
                    logger.info(f"✅ BSR update completed successfully for {worksheet_name}")
                else:
                    logger.warning(f"⚠️ BSR update completed with some failures for {worksheet_name}")
            except Exception as e:
                logger.error(f"Error in BSR update thread: {e}", exc_info=True)
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Start in background thread
        thread = threading.Thread(target=run_update, daemon=True)
        thread.start()
        
        # Return immediately
        return {
            "status": "started",
            "message": f'BSR update started for worksheet "{worksheet_name}". This may take a few minutes.',
            "worksheet": worksheet_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual BSR update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/schedule-test-job")
async def schedule_test_job(request: Request):
    """
    Schedule a test BSR update job in X minutes (for testing)
    """
    try:
        from datetime import datetime, timedelta
        from apscheduler.triggers.date import DateTrigger
        
        scheduler = request.app.state.scheduler
        if not scheduler or not scheduler.running:
            raise HTTPException(status_code=400, detail="Scheduler is not running")
        
        # Get minutes from request (default 5 minutes)
        body = await request.json()
        minutes = body.get('minutes', 5)
        
        # Calculate run time (now + minutes)
        bucharest_tz = pytz.timezone('Europe/Bucharest')
        run_time = datetime.now(bucharest_tz) + timedelta(minutes=minutes)
        
        # Import Celery task
        from app.tasks.bsr_tasks import update_all_worksheets_bsr
        
        # Add one-time test job
        job_id = f'test_bsr_update_{int(run_time.timestamp())}'
        scheduler.add_job(
            func=lambda: update_all_worksheets_bsr.delay(),
            trigger=DateTrigger(run_date=run_time),
            id=job_id,
            name=f'Test BSR Update in {minutes} minutes',
            replace_existing=True
        )
        
        logger.info(f"Test job scheduled: {job_id} at {run_time}")
        
        return {
            "status": "scheduled",
            "job_id": job_id,
            "scheduled_time": run_time.isoformat(),
            "minutes": minutes,
            "message": f"Test BSR update scheduled for {run_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        }
        
    except Exception as e:
        logger.error(f"Error scheduling test job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/scheduler-status", response_model=SchedulerStatus)
async def get_scheduler_status(request: Request):
    """Get scheduler status"""
    try:
        # Get scheduler from app state
        scheduler = request.app.state.scheduler
        
        if scheduler and scheduler.running:
            jobs = []
            for job in scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": str(job.next_run_time) if job.next_run_time else None
                })
            
            next_run = None
            if jobs:
                next_run = jobs[0].get("next_run")
            
            return {
                "running": True,
                "next_run": next_run,
                "jobs": jobs
            }
        else:
            return {
                "running": False,
                "next_run": None,
                "jobs": []
            }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Get status of a background job
    
    Returns:
        Job status with progress, errors, and result
    """
    try:
        from app.celery_app import celery_app
        
        task = celery_app.AsyncResult(job_id)
        
        if task.state == 'PENDING':
            # Job is waiting to be processed
            response = {
                'job_id': job_id,
                'state': task.state,
                'status': 'Job is waiting to be processed',
                'progress': None
            }
        elif task.state == 'PROGRESS':
            # Job is in progress
            response = {
                'job_id': job_id,
                'state': task.state,
                'status': task.info.get('status', 'Processing...'),
                'progress': {
                    'current': task.info.get('current', 0),
                    'total': task.info.get('total', 0),
                    'percentage': round((task.info.get('current', 0) / task.info.get('total', 1)) * 100, 2) if task.info.get('total', 0) > 0 else 0
                },
                'worksheet': task.info.get('worksheet'),
                'success_count': task.info.get('success_count'),
                'failure_count': task.info.get('failure_count')
            }
        elif task.state == 'SUCCESS':
            # Job completed successfully
            response = {
                'job_id': job_id,
                'state': task.state,
                'status': 'completed',
                'result': task.result,
                'progress': {
                    'current': task.result.get('total_books', task.result.get('total_worksheets', 0)),
                    'total': task.result.get('total_books', task.result.get('total_worksheets', 0)),
                    'percentage': 100
                }
            }
        elif task.state == 'FAILURE':
            # Job failed
            response = {
                'job_id': job_id,
                'state': task.state,
                'status': 'failed',
                'error': str(task.info) if isinstance(task.info, (str, dict)) else 'Unknown error',
                'traceback': task.traceback if hasattr(task, 'traceback') else None
            }
        else:
            # Unknown state
            response = {
                'job_id': job_id,
                'state': task.state,
                'status': f'Job state: {task.state}',
                'info': task.info
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

