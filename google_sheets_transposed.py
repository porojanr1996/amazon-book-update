"""
Google Sheets Integration - Transposed Format
Reads book data from transposed format (books in columns, dates in rows)
"""
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
import logging
from datetime import datetime
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleSheetsManager:
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """
        Initialize Google Sheets connection
        
        Args:
            credentials_path: Path to Google Service Account credentials JSON
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Google Sheets"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scope
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            logger.info("Successfully connected to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            raise
    
    def get_all_books(self, worksheet_name: str = 'Crime Fiction - US @zsh (32-38)') -> List[Dict[str, str]]:
        """
        Get all books from Google Sheets (transposed format)
        
        Expected format:
        - Row 1: Book titles (starting from column B)
        - Row 2: Authors
        - Row 3: Amazon links
        - Row 4: Categories (optional, can be empty)
        - Row 5+: Dates with BSR values
        
        Returns:
            List of dictionaries with book data
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            if not all_values or len(all_values) < 3:
                logger.warning("Sheet doesn't have enough rows")
                return []
            
            # Row 1: Book titles (skip column A which might be "Book Title" header)
            titles = all_values[0]  # Row 1 (0-indexed)
            authors = all_values[1] if len(all_values) > 1 else []  # Row 2
            links = all_values[2] if len(all_values) > 2 else []  # Row 3
            categories = all_values[3] if len(all_values) > 3 else []  # Row 4 (optional)
            
            books = []
            # Start from column B (index 1) since column A might be header
            for col_idx in range(1, len(titles)):
                # Skip empty columns or columns marked with ">>>SKIP" or ">>>STOP"
                title = titles[col_idx].strip() if col_idx < len(titles) else ''
                if not title or title.startswith('>>>') or title.upper() in ['AVG RANKS', 'AVERAGE']:
                    continue
                
                author = authors[col_idx].strip() if col_idx < len(authors) else ''
                link = links[col_idx].strip() if col_idx < len(links) else ''
                category = categories[col_idx].strip() if col_idx < len(categories) else ''
                
                if title and link:
                    books.append({
                        'col': col_idx + 1,  # 1-based column index for gspread
                        'name': title,
                        'author': author,
                        'amazon_link': link,
                        'category': category
                    })
            
            logger.info(f"Retrieved {len(books)} books from Google Sheets")
            return books
            
        except Exception as e:
            logger.error(f"Error reading books from Google Sheets: {e}")
            return []
    
    def get_today_row(self, worksheet_name: str = 'Crime Fiction - US @zsh (32-38)') -> int:
        """
        Get the row index for today's date
        
        Returns:
            Row index (1-based) for today's BSR data
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            # Dates start from row 5 (index 4, after categories row)
            today = datetime.now().strftime('%-m/%-d/%Y')  # Format: 1/15/2024
            today_alt = datetime.now().strftime('%m/%d/%Y')  # Format: 01/15/2024
            today_alt2 = datetime.now().strftime('%#m/%#d/%Y')  # Windows format
            
            # Check existing date rows (starting from row 5, index 4)
            for row_idx in range(4, len(all_values)):
                if row_idx < len(all_values):
                    date_cell = all_values[row_idx][0] if len(all_values[row_idx]) > 0 else ''
                    if date_cell.strip() in [today, today_alt, today_alt2]:
                        return row_idx + 1  # Convert to 1-based
            
            # If not found, add new row
            new_row = len(all_values) + 1
            worksheet.update_cell(new_row, 1, datetime.now().strftime('%m/%d/%Y'))
            logger.info(f"Created new row for date: {datetime.now().strftime('%m/%d/%Y')} at row {new_row}")
            
            return new_row
            
        except Exception as e:
            logger.error(f"Error getting today's row: {e}")
            # Default to row 4 if error
            return 4
    
    def update_bsr(self, col: int, row: int, bsr_value: int, worksheet_name: str = 'Crime Fiction - US @zsh (32-38)'):
        """
        Update BSR value for a specific book
        
        Args:
            col: Column number (1-based) - book column
            row: Row number (1-based) - date row
            bsr_value: BSR value to write
            worksheet_name: Name of the worksheet
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            worksheet.update_cell(row, col, bsr_value)
            logger.info(f"Updated BSR for column {col}, row {row}: {bsr_value}")
        except Exception as e:
            logger.error(f"Error updating BSR: {e}")
            raise
    
    def calculate_and_update_average(self, row: int, worksheet_name: str = 'Crime Fiction - US @zsh (32-38)'):
        """
        Calculate and update the average BSR for a specific date row
        
        Args:
            row: Row number (1-based) - date row
            worksheet_name: Name of the worksheet
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            if row > len(all_values):
                logger.warning(f"Row {row} doesn't exist yet")
                return
            
            # Get all books to know which columns to check
            books = self.get_all_books(worksheet_name)
            if not books:
                logger.warning("No books found, cannot calculate average")
                return
            
            # Collect BSR values from all book columns for this row
            bsr_values = []
            row_idx = row - 1  # Convert to 0-based index
            
            for book in books:
                col_idx = book['col'] - 1  # Convert to 0-based index
                if row_idx < len(all_values) and col_idx < len(all_values[row_idx]):
                    bsr_str = all_values[row_idx][col_idx].strip()
                    if bsr_str and bsr_str.replace(',', '').isdigit():
                        bsr_value = int(bsr_str.replace(',', ''))
                        bsr_values.append(bsr_value)
            
            if not bsr_values:
                logger.warning(f"No BSR values found for row {row}, cannot calculate average")
                return
            
            # Calculate average
            avg_bsr = sum(bsr_values) / len(bsr_values)
            avg_bsr_rounded = round(avg_bsr, 2)
            
            # Find the average column (usually column A or a column marked "AVG RANKS" or "AVERAGE")
            # Check column A first (index 0)
            avg_col = 1  # Column A (1-based)
            
            # Check if column A header indicates it's for averages
            if len(all_values) > 0:
                header_a = all_values[0][0].strip().upper() if len(all_values[0]) > 0 else ''
                if header_a not in ['AVG RANKS', 'AVERAGE', 'AVG', 'MEAN']:
                    # Look for a column with "AVG" or "AVERAGE" in header
                    headers = all_values[0] if len(all_values) > 0 else []
                    for col_idx, header in enumerate(headers, start=1):
                        if header.strip().upper() in ['AVG RANKS', 'AVERAGE', 'AVG', 'MEAN']:
                            avg_col = col_idx
                            break
            
            # Write average to the average column
            worksheet.update_cell(row, avg_col, avg_bsr_rounded)
            logger.info(f"Updated average BSR for row {row}, column {avg_col}: {avg_bsr_rounded} (from {len(bsr_values)} books)")
            
        except Exception as e:
            logger.error(f"Error calculating/updating average: {e}")
            raise
    
    def get_bsr_history(self, worksheet_name: str = 'Crime Fiction - US @zsh (32-38)') -> List[Dict]:
        """
        Get BSR history for all books (optimized)
        
        Returns:
            List of dictionaries with book data and BSR history
        """
        try:
            import time
            start_time = time.time()
            
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            load_time = time.time() - start_time
            logger.info(f"Loaded data from Google Sheets in {load_time:.2f}s")
            
            if not all_values or len(all_values) < 4:
                return []
            
            # Get book info from rows 1-3
            titles = all_values[0]
            authors = all_values[1] if len(all_values) > 1 else []
            links = all_values[2] if len(all_values) > 2 else []
            
            books_data = []
            process_start = time.time()
            
            # Process each book (column) - optimized
            for col_idx in range(1, len(titles)):
                title = titles[col_idx].strip() if col_idx < len(titles) else ''
                if not title or title.startswith('>>>') or title.upper() in ['AVG RANKS', 'AVERAGE']:
                    continue
                
                author = authors[col_idx].strip() if col_idx < len(authors) else ''
                link = links[col_idx].strip() if col_idx < len(links) else ''
                
                if not title or not link:
                    continue
                
                # Extract BSR values from date rows (starting from row 5, index 4, after categories row)
                bsr_history = []
                current_bsr = None
                
                # Get category from row 4 (index 3) if available
                category = ''
                if len(all_values) > 3 and col_idx < len(all_values[3]):
                    category = all_values[3][col_idx].strip() if col_idx < len(all_values[3]) else ''
                
                # Process rows normally (chronological order) - start from row 5 (index 4)
                for row_idx in range(4, len(all_values)):
                    if col_idx < len(all_values[row_idx]):
                        bsr_str = all_values[row_idx][col_idx].strip()
                        if bsr_str and bsr_str.replace(',', '').isdigit():
                            date_str = all_values[row_idx][0] if len(all_values[row_idx]) > 0 else ''
                            bsr_value = int(bsr_str.replace(',', ''))
                            bsr_history.append({
                                'date': date_str,
                                'bsr': bsr_value
                            })
                            current_bsr = bsr_value
                
                books_data.append({
                    'name': title,
                    'author': author,
                    'amazon_link': link,
                    'category': category,
                    'bsr_history': bsr_history,
                    'current_bsr': current_bsr
                })
            
            process_time = time.time() - process_start
            total_time = time.time() - start_time
            logger.info(f"Processed {len(books_data)} books in {process_time:.2f}s | Total: {total_time:.2f}s")
            
            return books_data
            
        except Exception as e:
            logger.error(f"Error getting BSR history: {e}", exc_info=True)
            return []
    
    def get_avg_history(self, worksheet_name: str = 'Crime Fiction - US') -> List[Dict]:
        """
        Get average BSR history from the AVG column in Google Sheets
        
        Returns:
            List of dictionaries with date and average BSR
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            if not all_values or len(all_values) < 5:
                return []
            
            # Find the AVG column
            headers = all_values[0] if len(all_values) > 0 else []
            avg_col = None
            
            # Look for AVG column in headers
            for col_idx, header in enumerate(headers):
                if header.strip().upper() in ['AVG RANKS', 'AVERAGE', 'AVG', 'MEAN']:
                    avg_col = col_idx
                    break
            
            if avg_col is None:
                logger.warning("No AVG column found in Google Sheets")
                return []
            
            logger.info(f"Found AVG column at index {avg_col}")
            
            # Extract date and average values from date rows (starting from row 5, index 4)
            avg_history = []
            
            for row_idx in range(4, len(all_values)):
                date_str = all_values[row_idx][0].strip() if len(all_values[row_idx]) > 0 else ''
                if not date_str:
                    continue
                
                # Get average value from AVG column
                if avg_col < len(all_values[row_idx]):
                    avg_str = all_values[row_idx][avg_col].strip()
                    if avg_str:
                        # Try to parse as float (remove commas)
                        avg_str_clean = avg_str.replace(',', '').replace(' ', '')
                        try:
                            avg_value = float(avg_str_clean)
                            avg_history.append({
                                'date': date_str,
                                'average_bsr': avg_value
                            })
                        except ValueError:
                            continue
            
            logger.info(f"Extracted {len(avg_history)} average values from AVG column")
            return avg_history
            
        except Exception as e:
            logger.error(f"Error getting AVG history: {e}", exc_info=True)
            return []
    
    def get_all_worksheets(self) -> List[str]:
        """
        Get list of all worksheet names in the spreadsheet
        
        Returns:
            List of worksheet names
        """
        try:
            worksheets = self.spreadsheet.worksheets()
            worksheet_names = [ws.title for ws in worksheets]
            logger.info(f"Found {len(worksheet_names)} worksheets: {worksheet_names}")
            return worksheet_names
        except Exception as e:
            logger.error(f"Error getting worksheets: {e}")
            return []

