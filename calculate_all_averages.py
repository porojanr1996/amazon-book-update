"""
Script to calculate and update average BSR for all dates in Google Sheets
Extracts all data from all columns and generates averages in the table
"""
import sys
import logging
from google_sheets_transposed import GoogleSheetsManager
import config
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def calculate_all_averages(worksheet_name: str = 'Crime Fiction - US'):
    """
    Calculate and update average BSR for all dates in Google Sheets
    
    Args:
        worksheet_name: Name of the worksheet to process
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting calculation of averages for all dates")
        logger.info("=" * 60)
        
        # Initialize Google Sheets manager
        sheets_manager = GoogleSheetsManager(
            config.GOOGLE_SHEETS_CREDENTIALS_PATH,
            config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        
        # Get worksheet
        worksheet = sheets_manager.spreadsheet.worksheet(worksheet_name)
        all_values = worksheet.get_all_values()
        
        if not all_values or len(all_values) < 5:
            logger.error("Not enough data in Google Sheets")
            return
        
        logger.info(f"Loaded {len(all_values)} rows from Google Sheets")
        
        # Get all books to know which columns to check
        books = sheets_manager.get_all_books(worksheet_name)
        if not books:
            logger.error("No books found in Google Sheets")
            return
        
        logger.info(f"Found {len(books)} books")
        
        # Find the average column (look for "AVG RANKS" or "AVERAGE" in headers)
        avg_col = None
        headers = all_values[0] if len(all_values) > 0 else []
        
        # Check column A first
        if len(headers) > 0 and headers[0].strip().upper() in ['AVG RANKS', 'AVERAGE', 'AVG', 'MEAN']:
            avg_col = 1
        else:
            # Look for a column with "AVG" or "AVERAGE" in header
            for col_idx, header in enumerate(headers, start=1):
                if header.strip().upper() in ['AVG RANKS', 'AVERAGE', 'AVG', 'MEAN']:
                    avg_col = col_idx
                    break
        
        # If no average column found, use column A (but don't overwrite dates)
        if avg_col is None:
            logger.warning("No 'AVG RANKS' column found. Will use column A, but make sure it doesn't contain dates!")
            avg_col = 1
        
        logger.info(f"Using column {avg_col} for averages")
        
        # Get book column indices (1-based)
        book_cols = [book['col'] for book in books]
        logger.info(f"Book columns: {book_cols}")
        
        # Process each date row (starting from row 5, index 4, after categories row)
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        # Date rows start from row 5 (index 4)
        for row_idx in range(4, len(all_values)):
            row_num = row_idx + 1  # Convert to 1-based
            
            # Check if this row has a date in column A
            date_cell = all_values[row_idx][0].strip() if len(all_values[row_idx]) > 0 else ''
            
            # Skip if no date (empty row or header)
            if not date_cell:
                continue
            
            # Try to parse date to verify it's a date row
            # Dates can be in various formats: M/D/YYYY, MM/DD/YYYY, etc.
            is_date_row = False
            if '/' in date_cell or '-' in date_cell:
                # Likely a date
                is_date_row = True
            
            if not is_date_row:
                continue
            
            # Collect BSR values from all book columns for this row
            bsr_values = []
            
            for col in book_cols:
                col_idx = col - 1  # Convert to 0-based index
                if row_idx < len(all_values) and col_idx < len(all_values[row_idx]):
                    bsr_str = all_values[row_idx][col_idx].strip()
                    if bsr_str:
                        # Try to parse as number (remove commas)
                        bsr_str_clean = bsr_str.replace(',', '').replace(' ', '')
                        if bsr_str_clean.isdigit():
                            bsr_value = int(bsr_str_clean)
                            bsr_values.append(bsr_value)
            
            if not bsr_values:
                logger.warning(f"Row {row_num} ({date_cell}): No BSR values found, skipping")
                skipped_count += 1
                continue
            
            # Calculate average
            avg_bsr = sum(bsr_values) / len(bsr_values)
            avg_bsr_rounded = round(avg_bsr, 2)
            
            # Write average to the average column
            try:
                worksheet.update_cell(row_num, avg_col, avg_bsr_rounded)
                logger.info(f"Row {row_num} ({date_cell}): Average = {avg_bsr_rounded} (from {len(bsr_values)} books)")
                processed_count += 1
            except Exception as e:
                logger.error(f"Row {row_num} ({date_cell}): Error writing average: {e}")
                error_count += 1
        
        # Summary
        logger.info("=" * 60)
        logger.info("Calculation completed!")
        logger.info(f"Processed: {processed_count} rows")
        logger.info(f"Skipped: {skipped_count} rows (no data)")
        logger.info(f"Errors: {error_count} rows")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    try:
        calculate_all_averages()
        logger.info("✅ All averages calculated and updated successfully!")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

