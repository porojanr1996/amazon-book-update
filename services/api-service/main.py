"""
API Service - Web API microservice for frontend
"""
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI, HTTPException, Query, Request, Header
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
import httpx
import logging

from shared.config import (
    API_SERVICE_PORT, SERVICE_HOST, SERVICE_ENV,
    SHEETS_SERVICE_URL, SCRAPER_SERVICE_URL, WORKER_SERVICE_PORT
)
from shared.utils.logger import setup_logger
from shared.models import Book, ChartData, ErrorResponse, SuccessResponse, JobStatus

# Setup logger
logger = setup_logger('api-service')

# Create FastAPI app
app = FastAPI(
    title="API Service",
    description="Web API microservice for frontend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP client for inter-service communication
http_client = httpx.AsyncClient(timeout=30.0)

# Mount static files (from root directory) - AFTER routes to avoid conflicts
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static'))
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates directory (from root directory)
templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))
templates = Jinja2Templates(directory=templates_dir)

# Add url_for helper to templates for backward compatibility
def url_for_static(request: Request, filename: str):
    """Helper function to generate static file URLs"""
    return f"/static/{filename}"

# Make url_for available in templates
templates.env.globals['url_for'] = lambda name, **kwargs: url_for_static if name == 'static' else f"/{name}"


async def call_sheets_service(endpoint: str, params: dict = None):
    """Call sheets-service endpoint"""
    try:
        url = f"{SHEETS_SERVICE_URL}{endpoint}"
        response = await http_client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error calling sheets-service {endpoint}: {e}")
        raise HTTPException(status_code=503, detail=f"Sheets service unavailable: {e}")


async def call_scraper_service(endpoint: str, data: dict):
    """Call scraper-service endpoint"""
    try:
        url = f"{SCRAPER_SERVICE_URL}{endpoint}"
        response = await http_client.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error calling scraper-service {endpoint}: {e}")
        raise HTTPException(status_code=503, detail=f"Scraper service unavailable: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check dependencies (non-blocking)
        dependencies_status = {}
        try:
            sheets_health = await http_client.get(f"{SHEETS_SERVICE_URL}/health", timeout=2.0)
            dependencies_status["sheets-service"] = sheets_health.json() if sheets_health.status_code == 200 else "unhealthy"
        except:
            dependencies_status["sheets-service"] = "unreachable"
        
        try:
            scraper_health = await http_client.get(f"{SCRAPER_SERVICE_URL}/health", timeout=2.0)
            dependencies_status["scraper-service"] = scraper_health.json() if scraper_health.status_code == 200 else "unhealthy"
        except:
            dependencies_status["scraper-service"] = "unreachable"
        
        return {
            "status": "healthy",
            "service": "api-service",
            "dependencies": dependencies_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page"""
    # Add url_for helper to context
    def url_for(name: str, **kwargs):
        if name == 'static':
            filename = kwargs.get('filename', '')
            return f"/static/{filename}"
        return f"/{name}"
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "url_for": url_for
    })


@app.get("/api/worksheets")
async def get_worksheets():
    """Get all worksheet names"""
    try:
        worksheets = await call_sheets_service("/api/worksheets")
        return worksheets
    except Exception as e:
        logger.error(f"Error getting worksheets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rankings")
async def get_rankings(
    worksheet: Optional[str] = Query(None),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    if_modified_since: Optional[str] = Header(None, alias="If-Modified-Since")
):
    """Get rankings with cover images"""
    try:
        worksheet_name = worksheet or 'Crime Fiction - US'
        
        # Get books from sheets-service
        books_data = await call_sheets_service("/api/bsr-history", {"worksheet": worksheet_name})
        
        # Separate books with and without BSR
        books_with_bsr = [b for b in books_data if b.get('current_bsr') is not None]
        books_without_bsr = [b for b in books_data if b.get('current_bsr') is None]
        
        # Sort books with BSR
        books_with_bsr.sort(key=lambda x: x['current_bsr'])
        
        # Combine
        all_books = books_with_bsr + books_without_bsr
        
        # Get cover images from Redis cache
        try:
            # Import cache service functions
            from app.services.redis_cache import get_cache
            
            covers_found = 0
            for book in all_books:
                amazon_link = book.get('amazon_link')
                if amazon_link and not book.get('cover_image'):
                    # Check Redis cache
                    cache_key = f"cover:{amazon_link}"
                    try:
                        cached_cover = get_cache(cache_key)
                        if cached_cover:
                            book['cover_image'] = cached_cover
                            covers_found += 1
                    except Exception as e:
                        logger.debug(f"Could not get cover from cache for {book.get('name', 'Unknown')}: {e}")
            
            logger.info(f"Returning {len(all_books)} books, {covers_found} with cover images (from cache)")
        except Exception as e:
            logger.warning(f"Error loading cover images from cache: {e}")
            # Continue without covers if cache fails
        
        return all_books
    except Exception as e:
        logger.error(f"Error getting rankings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def parse_date(date_str):
    """Parse date string in various formats"""
    from datetime import datetime
    
    if not date_str:
        return None
    
    if isinstance(date_str, datetime):
        return date_str
    
    date_str = str(date_str).strip()
    if not date_str:
        return None
    
    # Try YYYY-MM-DD format first
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        pass
    
    # Try M/D/YYYY or MM/DD/YYYY format
    try:
        return datetime.strptime(date_str, '%m/%d/%Y')
    except ValueError:
        pass
    
    # Try M/D/YY format (2-digit year)
    try:
        parsed = datetime.strptime(date_str, '%m/%d/%y')
        if parsed.year < 50:
            parsed = parsed.replace(year=parsed.year + 2000)
        else:
            parsed = parsed.replace(year=parsed.year + 1900)
        return parsed
    except ValueError:
        pass
    
    # Try M-D-YYYY format
    try:
        return datetime.strptime(date_str, '%m-%d-%Y')
    except ValueError:
        pass
    
    return None


def normalize_date(date_str):
    """Normalize date string to YYYY-MM-DD format"""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime('%Y-%m-%d')
    return date_str


@app.get("/api/chart-data")
async def get_chart_data(
    range: str = Query('30'),
    worksheet: Optional[str] = Query(None)
):
    """Get chart data with date range filtering"""
    try:
        from datetime import timedelta
        
        worksheet_name = worksheet or 'Crime Fiction - US'
        time_range = range
        
        # Get average history from sheets-service
        avg_history = await call_sheets_service("/api/avg-history", {"worksheet": worksheet_name})
        
        if not avg_history:
            return {
                "dates": [],
                "average_bsr": [],
                "worksheet": worksheet_name
            }
        
        # Parse and normalize all dates
        parsed_history = []
        for entry in avg_history:
            original_date = entry.get('date', '').strip()
            if not original_date:
                continue
            
            entry_date = parse_date(original_date)
            if not entry_date:
                continue
            
            normalized_date = normalize_date(original_date)
            if normalized_date:
                parsed_entry = {
                    'date': normalized_date,
                    'original_date': original_date,
                    'average_bsr': entry.get('average_bsr'),
                    'parsed_date': entry_date
                }
                parsed_history.append(parsed_entry)
        
        # Sort by date
        parsed_history.sort(key=lambda x: x['parsed_date'])
        
        if not parsed_history:
            return {
                "dates": [],
                "average_bsr": [],
                "worksheet": worksheet_name
            }
        
        # Filter by time range
        latest_date = parsed_history[-1]['parsed_date']
        filtered_history = []
        
        if time_range == 'all':
            filtered_history = parsed_history
        else:
            try:
                days = int(time_range)
                cutoff_date = latest_date - timedelta(days=days)
                filtered_history = [e for e in parsed_history if e['parsed_date'] >= cutoff_date]
            except ValueError:
                filtered_history = parsed_history
        
        # Limit data points for performance (except for 'all')
        if time_range != 'all' and len(filtered_history) > 200:
            step = max(1, len(filtered_history) // 200)
            filtered_history = filtered_history[::step][:200]
        
        # Extract dates and averages
        dates = [entry['date'] for entry in filtered_history]
        averages = [entry['average_bsr'] for entry in filtered_history]
        
        return {
            "dates": dates,
            "average_bsr": averages,
            "worksheet": worksheet_name
        }
    except Exception as e:
        logger.error(f"Error getting chart data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trigger-bsr-update")
async def trigger_bsr_update(request: Request):
    """Trigger BSR update (enqueue Celery task)"""
    try:
        body = await request.json()
        worksheet = body.get('worksheet', '')
        
        # Try to enqueue Celery task directly
        try:
            # Import Celery app and tasks (add worker-service directory to path)
            import sys
            import os
            worker_service_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../worker-service'))
            if worker_service_dir not in sys.path:
                sys.path.insert(0, worker_service_dir)
            
            from celery_app import celery_app
            from tasks import update_worksheet_bsr
            import redis
            
            # Check if Redis is available
            from shared.config import REDIS_URL
            r = redis.from_url(REDIS_URL)
            r.ping()
            
            # Enqueue Celery task
            if worksheet:
                task = update_worksheet_bsr.delay(worksheet)
                logger.info(f"Enqueued BSR update task {task.id} for worksheet: {worksheet}")
                return {
                    "status": "started",
                    "message": f"BSR update started for worksheet '{worksheet}'.",
                    "worksheet": worksheet,
                    "job_id": task.id
                }
            else:
                # Update all worksheets - get list and enqueue for each
                worksheets = await call_sheets_service("/api/worksheets", {})
                if not worksheets:
                    worksheets = ['Crime Fiction - US']
                
                job_ids = []
                for ws in worksheets:
                    task = update_worksheet_bsr.delay(ws)
                    job_ids.append(task.id)
                
                logger.info(f"Enqueued BSR update tasks for {len(worksheets)} worksheets")
                return {
                    "status": "started",
                    "message": f"BSR update started for {len(worksheets)} worksheets.",
                    "job_ids": job_ids,
                    "job_id": job_ids[0] if job_ids else "pending"
                }
        except ImportError as e:
            logger.warning(f"Could not import Celery tasks: {e}")
            return {
                "status": "error",
                "message": "Celery tasks not available. Make sure worker-service is properly configured.",
                "worksheet": worksheet
            }
        except redis.ConnectionError:
            logger.warning("Redis not available, cannot enqueue Celery task")
            return {
                "status": "error",
                "message": "Redis not available. Please start Redis and worker-service.",
                "worksheet": worksheet
            }
        except Exception as e:
            logger.error(f"Error enqueueing Celery task: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error starting BSR update: {str(e)}",
                "worksheet": worksheet
            }
    except Exception as e:
        logger.error(f"Error triggering BSR update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status from Celery"""
    try:
        # Import Celery app to check task status
        import sys
        import os
        worker_service_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../worker-service'))
        if worker_service_dir not in sys.path:
            sys.path.insert(0, worker_service_dir)
        
        from celery_app import celery_app
        
        # Get task result from Celery
        task_result = celery_app.AsyncResult(job_id)
        
        if task_result.state == 'PENDING':
            # Task is waiting to be processed
            return {
                "job_id": job_id,
                "state": "PENDING",
                "status": "Job is waiting to be processed..."
            }
        elif task_result.state == 'PROGRESS':
            # Task is in progress
            info = task_result.info or {}
            return {
                "job_id": job_id,
                "state": "PROGRESS",
                "status": info.get('status', 'Processing...'),
                "progress": {
                    "current": info.get('current', 0),
                    "total": info.get('total', 0),
                    "percentage": (info.get('current', 0) / info.get('total', 1)) * 100 if info.get('total', 0) > 0 else 0
                },
                "success_count": info.get('success_count', 0),
                "failure_count": info.get('failure_count', 0)
            }
        elif task_result.state == 'SUCCESS':
            # Task completed successfully
            result = task_result.result or {}
            return {
                "job_id": job_id,
                "state": "SUCCESS",
                "status": "Completed",
                "result": result
            }
        elif task_result.state == 'FAILURE':
            # Task failed
            return {
                "job_id": job_id,
                "state": "FAILURE",
                "status": "Failed",
                "error": str(task_result.info) if task_result.info else "Unknown error"
            }
        else:
            return {
                "job_id": job_id,
                "state": task_result.state,
                "status": f"Unknown state: {task_result.state}"
            }
    except ImportError:
        logger.warning("Could not import Celery app, returning mock status")
        return {
            "job_id": job_id,
            "state": "PENDING",
            "status": "Job status check not available"
        }
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await http_client.aclose()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=SERVICE_HOST,
        port=API_SERVICE_PORT,
        reload=(SERVICE_ENV == 'development'),
        log_level="info"
    )

