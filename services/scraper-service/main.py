"""
Scraper Service - Amazon scraping microservice
"""
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging

from shared.config import SCRAPER_SERVICE_PORT, SERVICE_HOST, SERVICE_ENV
from shared.utils.logger import setup_logger
from shared.models import ErrorResponse

# Import scraper
from amazon_scraper import AmazonScraper
from app.services.playwright_scraper import extract_bsr_with_playwright_sync, extract_cover_image_with_playwright_sync

# Setup logger
logger = setup_logger('scraper-service')

# Create FastAPI app
app = FastAPI(
    title="Scraper Service",
    description="Amazon scraping microservice",
    version="1.0.0"
)


class ExtractBSRRequest(BaseModel):
    """Request model for BSR extraction"""
    amazon_url: str
    use_playwright: bool = False


class ExtractCoverRequest(BaseModel):
    """Request model for cover extraction"""
    amazon_url: str
    use_playwright: bool = True


class ExtractBatchRequest(BaseModel):
    """Request model for batch extraction"""
    amazon_urls: List[str]
    use_playwright: bool = False


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Simple health check - just verify scraper can be initialized
        scraper = AmazonScraper(delay_between_requests=1, retry_attempts=1)
        return {
            "status": "healthy",
            "service": "scraper-service",
            "playwright_available": True  # Assume Playwright is available
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/api/extract-bsr")
async def extract_bsr(request: ExtractBSRRequest):
    """Extract BSR from Amazon URL"""
    try:
        logger.info(f"Extracting BSR from {request.amazon_url}")
        
        scraper = AmazonScraper(
            delay_between_requests=8,  # Conservative delay
            retry_attempts=3
        )
        
        bsr = scraper.extract_bsr(request.amazon_url, use_playwright=request.use_playwright)
        
        if bsr:
            logger.info(f"✓ BSR extracted: {bsr} from {request.amazon_url}")
            return {
                "status": "success",
                "bsr": bsr,
                "amazon_url": request.amazon_url
            }
        else:
            logger.warning(f"✗ BSR extraction failed for {request.amazon_url}")
            return {
                "status": "failed",
                "bsr": None,
                "amazon_url": request.amazon_url,
                "error": "BSR not found or page blocked"
            }
    except Exception as e:
        logger.error(f"Error extracting BSR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract-cover")
async def extract_cover(request: ExtractCoverRequest):
    """Extract cover image from Amazon URL"""
    try:
        logger.info(f"Extracting cover from {request.amazon_url}")
        
        scraper = AmazonScraper(
            delay_between_requests=8,
            retry_attempts=2
        )
        
        cover_url = scraper.extract_cover_image(
            request.amazon_url,
            use_playwright=request.use_playwright
        )
        
        if cover_url:
            # Clean up image URL for better quality
            import re
            cover_url = re.sub(r'_SL\d+_', '_SL800_', cover_url)
            cover_url = re.sub(r'\._AC_[^_]+_', '._AC_SL800_', cover_url)
            if '_SL' not in cover_url:
                cover_url = cover_url.replace('._AC_', '._AC_SL800_')
            cover_url = re.sub(r'_SX\d+_', '_SX800_', cover_url)
            
            logger.info(f"✓ Cover extracted: {cover_url[:80]}...")
            return {
                "status": "success",
                "cover_url": cover_url,
                "amazon_url": request.amazon_url
            }
        else:
            logger.warning(f"✗ Cover extraction failed for {request.amazon_url}")
            return {
                "status": "failed",
                "cover_url": None,
                "amazon_url": request.amazon_url,
                "error": "Cover not found or page blocked"
            }
    except Exception as e:
        logger.error(f"Error extracting cover: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract-batch")
async def extract_batch(request: ExtractBatchRequest):
    """Extract BSR for multiple URLs (sequential to avoid rate limiting)"""
    try:
        logger.info(f"Extracting BSR for {len(request.amazon_urls)} URLs")
        
        scraper = AmazonScraper(
            delay_between_requests=8,
            retry_attempts=2
        )
        
        results = []
        for idx, url in enumerate(request.amazon_urls):
            if idx > 0:
                import time
                time.sleep(8)  # Delay between requests
            
            try:
                bsr = scraper.extract_bsr(url, use_playwright=request.use_playwright)
                results.append({
                    "amazon_url": url,
                    "bsr": bsr,
                    "status": "success" if bsr else "failed"
                })
            except Exception as e:
                logger.error(f"Error extracting BSR for {url}: {e}")
                results.append({
                    "amazon_url": url,
                    "bsr": None,
                    "status": "error",
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["status"] == "success")
        logger.info(f"Batch extraction completed: {success_count}/{len(results)} success")
        
        return {
            "status": "completed",
            "total": len(results),
            "success": success_count,
            "failed": len(results) - success_count,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in batch extraction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=SERVICE_HOST,
        port=SCRAPER_SERVICE_PORT,
        reload=(SERVICE_ENV == 'development'),
        log_level="info"
    )

