"""
Google Sheets service layer
"""
import logging
from typing import List, Dict, Optional
from google_sheets_transposed import GoogleSheetsManager
import config

logger = logging.getLogger(__name__)

# Singleton instance
_sheets_manager: Optional[GoogleSheetsManager] = None


def get_sheets_manager() -> GoogleSheetsManager:
    """Lazy initialization of sheets manager"""
    global _sheets_manager
    if _sheets_manager is None:
        _sheets_manager = GoogleSheetsManager(
            config.GOOGLE_SHEETS_CREDENTIALS_PATH,
            config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
    return _sheets_manager


async def get_all_worksheets() -> List[str]:
    """Get all worksheet names"""
    manager = get_sheets_manager()
    return manager.get_all_worksheets()


async def get_books_for_worksheet(worksheet_name: str) -> List[Dict]:
    """Get all books for a specific worksheet"""
    manager = get_sheets_manager()
    return manager.get_bsr_history(worksheet_name=worksheet_name)


async def get_default_worksheet() -> str:
    """Get default worksheet name (first available worksheet)"""
    all_worksheets = await get_all_worksheets()
    
    # Return first worksheet if available
    if all_worksheets:
        return all_worksheets[0]
    return 'Crime Fiction - US'


async def get_avg_history_for_worksheet(worksheet_name: str) -> List[Dict]:
    """Get average BSR history for a worksheet"""
    manager = get_sheets_manager()
    return manager.get_avg_history(worksheet_name=worksheet_name)

