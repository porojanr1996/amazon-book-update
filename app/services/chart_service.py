"""
Chart data processing service
"""
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.services.sheets_service import get_avg_history_for_worksheet, get_default_worksheet
from app.services.redis_cache import get_redis_client
from app.models.schemas import ChartData

logger = logging.getLogger(__name__)


def parse_date(date_str):
    """
    Parse date string in various formats and return datetime object
    
    Supports:
    - YYYY-MM-DD (e.g., '2024-02-06')
    - M/D/YYYY (e.g., '2/6/2024', '02/06/2024')
    - MM/DD/YYYY (e.g., '02/06/2024')
    - M-D-YYYY (e.g., '2-6-2024')
    - Various other common formats
    
    Returns:
        datetime object or None if parsing fails
    """
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
        # Convert 2-digit year to 4-digit (assume 2000s if < 50, else 1900s)
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
    
    # Try DD/MM/YYYY format (European)
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except ValueError:
        pass
    
    logger.warning(f"Could not parse date: {date_str}")
    return None


def normalize_date(date_str):
    """
    Normalize date string to YYYY-MM-DD format
    
    Returns:
        Normalized date string in YYYY-MM-DD format, or original string if parsing fails
    """
    dt = parse_date(date_str)
    if dt:
        return dt.strftime('%Y-%m-%d')
    return date_str


async def get_chart_data(time_range: str, worksheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get chart data for a specific time range and worksheet (with Redis caching)
    
    Args:
        time_range: Time range filter ('1', '7', '30', '90', '365', 'all')
        worksheet_name: Worksheet name (optional)
    
    Returns:
        Chart data dictionary
    """
    import time as time_module
    
    # Get default worksheet if not specified
    if not worksheet_name:
        worksheet_name = await get_default_worksheet()
    
    start_time = time_module.time()
    
    logger.info(f"Chart data request: range={time_range}, worksheet={worksheet_name}")
    
    # Use get_or_set for Redis caching
    cache_key = f"chart:{time_range}:{worksheet_name}"
    
    async def _build_chart_data():
        """Build chart data (called on cache miss)"""
        # Get average history from Google Sheets
        logger.info(f"Building chart data for {worksheet_name} - fetching from Google Sheets...")
        avg_history = await get_avg_history_for_worksheet(worksheet_name)
        
        load_time = time_module.time() - start_time
        logger.info(f"Loaded {len(avg_history)} average values from AVG column in {load_time:.2f}s")
        
        # Log last few entries for debugging
        if avg_history:
            last_entries = avg_history[-5:] if len(avg_history) >= 5 else avg_history
            logger.info(f"Last {len(last_entries)} average entries: {[(e.get('date'), e.get('average_bsr')) for e in last_entries]}")
        
        # Process data for chart
        chart_data = {
            'dates': [],
            'average_bsr': [],
            'books': []
        }
        
        if not avg_history:
            logger.warning("No average history found")
            return chart_data
        
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
            logger.warning("No valid dates found in average history")
            return chart_data
        
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
        chart_data['dates'] = [entry['date'] for entry in filtered_history]
        chart_data['average_bsr'] = [entry['average_bsr'] for entry in filtered_history]
        
        # Log last few data points for debugging
        if chart_data['dates'] and chart_data['average_bsr']:
            last_dates = chart_data['dates'][-5:] if len(chart_data['dates']) >= 5 else chart_data['dates']
            last_averages = chart_data['average_bsr'][-5:] if len(chart_data['average_bsr']) >= 5 else chart_data['average_bsr']
            logger.info(f"Chart data last {len(last_dates)} points: dates={last_dates}, averages={last_averages}")
        
        # Get total books count
        from app.services.sheets_service import get_books_for_worksheet
        books_data = await get_books_for_worksheet(worksheet_name)
        chart_data['total_books'] = len(books_data)
        chart_data['worksheet'] = worksheet_name
        
        logger.info(f"Built chart data: {len(chart_data['dates'])} dates, {len(chart_data['average_bsr'])} averages, {chart_data['total_books']} books")
        
        return chart_data
    
    # Check cache first, but don't use get_or_set because callback is async
    # Instead, manually check cache and build if needed
    redis_client = get_redis_client()
    if redis_client:
        try:
            cached_value = redis_client.get(cache_key)
            if cached_value is not None:
                try:
                    cached_data = json.loads(cached_value)
                    logger.info(f"Returning cached chart data for {time_range}:{worksheet_name}")
                    return ChartData(**cached_data)
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    logger.warning(f"Invalid cached chart data, rebuilding: {e}")
                    # Delete invalid cache
                    redis_client.delete(cache_key)
        except Exception as e:
            logger.warning(f"Error reading chart cache: {e}")
    
    # Cache miss - build chart data from Google Sheets
    logger.info(f"Cache miss for {cache_key}, building chart data from Google Sheets...")
    chart_data_dict = await _build_chart_data()
    
    # Cache the result
    if redis_client:
        try:
            serialized = json.dumps(chart_data_dict)
            redis_client.setex(cache_key, 300, serialized)  # 5 minutes TTL
            logger.info(f"Cached chart data for {time_range}:{worksheet_name} (TTL: 300s)")
        except Exception as e:
            logger.warning(f"Error caching chart data: {e}")
    
    return ChartData(**chart_data_dict)
