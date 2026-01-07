# FastAPI Migration Guide

## Overview

The Flask backend has been migrated to FastAPI while maintaining **100% backward compatibility** with existing frontend code and API responses.

## Structure

```
app/
  main.py              # FastAPI application entry point
  api/
    routes.py          # API route handlers
  services/
    sheets_service.py   # Google Sheets operations
    cache_service.py    # Caching logic
    chart_service.py    # Chart data processing
    bsr_update_service.py  # BSR update logic
  models/
    schemas.py         # Pydantic models for API responses
```

## Running the Application

### Option 1: Using the run script
```bash
python run_fastapi.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5001 --reload
```

## API Endpoints (Backward Compatible)

All endpoints maintain the same URLs and JSON response formats:

- `GET /` - Dashboard page
- `GET /api/worksheets` - List all worksheets
- `GET /api/books?worksheet=...` - Get books for worksheet
- `GET /api/rankings?worksheet=...` - Get rankings
- `GET /api/chart-data?range=...&worksheet=...` - Get chart data
- `POST /api/trigger-bsr-update` - Manual BSR update
- `GET /api/scheduler-status` - Scheduler status
- `GET /api/clear-cache` - Clear caches

## Key Features

1. **Async Support**: Routes are async where applicable for better performance
2. **Pydantic Models**: All responses use Pydantic models for validation
3. **Type Safety**: Full type hints throughout
4. **Backward Compatible**: All JSON responses match Flask format exactly
5. **Same Functionality**: All features work identically to Flask version

## Migration Notes

- Flask `jsonify()` → FastAPI automatic JSON serialization
- Flask `request.args.get()` → FastAPI `Query()` parameters
- Flask `request.json` → FastAPI `Request.json()` (async)
- Flask templates → FastAPI Jinja2Templates (same)
- Flask CORS → FastAPI CORSMiddleware (same config)

## Testing

The frontend should work without any changes. All API endpoints return the same JSON structure as before.

## Dependencies

New dependencies added:
- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `python-multipart`

Flask dependencies are kept for now but can be removed after full migration.

