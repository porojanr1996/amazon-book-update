"""
Sheets Service - Google Sheets operations microservice
"""
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import logging

from shared.config import SHEETS_SERVICE_PORT, SERVICE_HOST, SERVICE_ENV
from shared.utils.logger import setup_logger
from shared.models import ErrorResponse

# Import sheets manager
from google_sheets_transposed import GoogleSheetsManager

# Setup logger
logger = setup_logger('sheets-service')

# Create FastAPI app
app = FastAPI(
    title="Sheets Service",
    description="Google Sheets operations microservice",
    version="1.0.0"
)

# Initialize sheets manager
_sheets_manager = None

def get_sheets_manager():
    """Lazy initialization of sheets manager"""
    global _sheets_manager
    if _sheets_manager is None:
        from shared.config import GOOGLE_SHEETS_CREDENTIALS_PATH, GOOGLE_SHEETS_SPREADSHEET_ID
        import os
        # Resolve credentials path relative to project root
        creds_path = GOOGLE_SHEETS_CREDENTIALS_PATH
        if not os.path.isabs(creds_path):
            # If relative path, resolve from project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
            creds_path = os.path.join(project_root, creds_path)
        _sheets_manager = GoogleSheetsManager(
            credentials_path=creds_path,
            spreadsheet_id=GOOGLE_SHEETS_SPREADSHEET_ID
        )
    return _sheets_manager


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        manager = get_sheets_manager()
        # Try to get worksheets as health check
        worksheets = manager.get_all_worksheets()
        return {
            "status": "healthy",
            "service": "sheets-service",
            "worksheets_count": len(worksheets)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/api/worksheets")
async def get_worksheets():
    """Get list of all worksheets"""
    try:
        manager = get_sheets_manager()
        worksheets = manager.get_all_worksheets()
        # Filter out unwanted sheets
        filtered = [ws for ws in worksheets if ws not in ['Sheet1', 'Sheet3']]
        return filtered
    except Exception as e:
        logger.error(f"Error getting worksheets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/books")
async def get_books(worksheet: str = Query('Crime Fiction - US')):
    """Get all books from a worksheet"""
    try:
        manager = get_sheets_manager()
        books = manager.get_all_books(worksheet_name=worksheet)
        return books
    except Exception as e:
        logger.error(f"Error getting books: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bsr-history")
async def get_bsr_history(worksheet: str = Query('Crime Fiction - US')):
    """Get BSR history for all books"""
    try:
        manager = get_sheets_manager()
        history = manager.get_bsr_history(worksheet_name=worksheet)
        return history
    except Exception as e:
        logger.error(f"Error getting BSR history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/avg-history")
async def get_avg_history(worksheet: str = Query('Crime Fiction - US')):
    """Get average BSR history"""
    try:
        manager = get_sheets_manager()
        history = manager.get_avg_history(worksheet_name=worksheet)
        return history
    except Exception as e:
        logger.error(f"Error getting avg history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/update-bsr")
async def update_bsr(data: dict):
    """Update BSR for a book"""
    try:
        worksheet = data.get('worksheet', 'Crime Fiction - US')
        col = data.get('col')
        row = data.get('row')
        bsr_value = data.get('bsr_value')
        
        if not all([col, row, bsr_value]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: col, row, bsr_value"
            )
        
        manager = get_sheets_manager()
        manager.update_bsr(col, row, bsr_value, worksheet_name=worksheet)
        
        # Flush batch updates
        manager.flush_batch_updates(worksheet_name=worksheet)
        
        return {"status": "success", "message": "BSR updated"}
    except Exception as e:
        logger.error(f"Error updating BSR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calculate-average")
async def calculate_average(data: dict):
    """Calculate and update average BSR"""
    try:
        worksheet = data.get('worksheet', 'Crime Fiction - US')
        row = data.get('row')
        
        if not row:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: row"
            )
        
        manager = get_sheets_manager()
        manager.calculate_and_update_average(row, worksheet_name=worksheet)
        
        # Flush batch updates
        manager.flush_batch_updates(worksheet_name=worksheet)
        
        return {"status": "success", "message": "Average calculated"}
    except Exception as e:
        logger.error(f"Error calculating average: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/flush-updates")
async def flush_updates(data: dict):
    """Flush batch updates to Google Sheets"""
    try:
        worksheet = data.get('worksheet', 'Crime Fiction - US')
        manager = get_sheets_manager()
        manager.flush_batch_updates(worksheet_name=worksheet)
        return {"status": "success", "message": "Updates flushed"}
    except Exception as e:
        logger.error(f"Error flushing updates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/today-row")
async def get_today_row(worksheet: str = Query('Crime Fiction - US')):
    """Get today's row index"""
    try:
        manager = get_sheets_manager()
        row = manager.get_today_row(worksheet_name=worksheet)
        return {"row": row}
    except Exception as e:
        logger.error(f"Error getting today row: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=SERVICE_HOST,
        port=SHEETS_SERVICE_PORT,
        reload=(SERVICE_ENV == 'development'),
        log_level="info"
    )

