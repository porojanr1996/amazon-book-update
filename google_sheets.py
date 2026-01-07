"""
Google Sheets Integration
Reads book data and writes BSR values to Google Sheets
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
    
    def get_all_books(self, worksheet_name: str = 'Sheet1') -> List[Dict[str, str]]:
        """
        Get all books from Google Sheets
        
        Expected format:
        - Column A: Book name (flexible: "Book Name", "nume carte", "Title", etc.)
        - Column B: Author (flexible: "Author", "autor", etc.)
        - Column C: Amazon link (flexible: "Amazon Link", "link Amazon", "URL", etc.)
        - Column D (optional): Category
        
        Returns:
            List of dictionaries with book data
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            if not all_values or len(all_values) < 2:
                logger.warning("Sheet is empty or has no data rows")
                return []
            
            # Get header row
            headers = [h.strip().lower() for h in all_values[0]]
            
            # Find column indices (flexible matching)
            name_col = None
            author_col = None
            link_col = None
            category_col = None
            
            for idx, header in enumerate(headers):
                header_lower = header.lower()
                if name_col is None and any(x in header_lower for x in ['book', 'nume', 'title', 'name']):
                    name_col = idx
                elif author_col is None and any(x in header_lower for x in ['author', 'autor']):
                    author_col = idx
                elif link_col is None and any(x in header_lower for x in ['amazon', 'link', 'url']):
                    link_col = idx
                elif category_col is None and 'categor' in header_lower:
                    category_col = idx
            
            # Fallback: use first 3 columns if headers not found
            if name_col is None:
                name_col = 0
            if author_col is None:
                author_col = 1
            if link_col is None:
                link_col = 2
            
            books = []
            for i, row in enumerate(all_values[1:], start=2):  # Start from row 2
                if len(row) <= max(name_col, author_col, link_col):
                    continue
                    
                book_name = row[name_col].strip() if len(row) > name_col else ''
                amazon_link = row[link_col].strip() if len(row) > link_col else ''
                
                if book_name and amazon_link:
                    books.append({
                        'row': i,
                        'name': book_name,
                        'author': row[author_col].strip() if len(row) > author_col else '',
                        'amazon_link': amazon_link,
                        'category': row[category_col].strip() if category_col and len(row) > category_col else ''
                    })
            
            logger.info(f"Retrieved {len(books)} books from Google Sheets")
            return books
            
        except Exception as e:
            logger.error(f"Error reading books from Google Sheets: {e}")
            return []
    
    def get_today_column(self, worksheet_name: str = 'Sheet1') -> int:
        """
        Get the column index for today's date
        
        Returns:
            Column index (1-based) for today's BSR data
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            header_row = worksheet.row_values(1)
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Check if today's column already exists
            for col_idx, header in enumerate(header_row, start=1):
                if header == today:
                    return col_idx
            
            # If not found, find the last date column and add a new one
            # Assuming dates start from column D (index 4)
            last_col = len(header_row) + 1
            
            # Add today's date as header
            worksheet.update_cell(1, last_col, today)
            logger.info(f"Created new column for date: {today} at column {last_col}")
            
            return last_col
            
        except Exception as e:
            logger.error(f"Error getting today's column: {e}")
            # Default to column D (4) if error
            return 4
    
    def update_bsr(self, row: int, column: int, bsr_value: int, worksheet_name: str = 'Sheet1'):
        """
        Update BSR value for a specific book
        
        Args:
            row: Row number (1-based)
            column: Column number (1-based)
            bsr_value: BSR value to write
            worksheet_name: Name of the worksheet
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            worksheet.update_cell(row, column, bsr_value)
            logger.info(f"Updated BSR for row {row}, column {column}: {bsr_value}")
        except Exception as e:
            logger.error(f"Error updating BSR: {e}")
            raise
    
    def get_bsr_history(self, worksheet_name: str = 'Sheet1') -> List[Dict]:
        """
        Get BSR history for all books
        
        Returns:
            List of dictionaries with book data and BSR history
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            if not all_values or len(all_values) < 2:
                return []
            
            # First row is headers
            headers = all_values[0]
            
            # Find date columns (assuming they start from column D, index 3)
            date_columns = []
            for idx, header in enumerate(headers):
                if idx >= 3:  # Skip A, B, C columns
                    try:
                        # Try to parse as date
                        datetime.strptime(header, '%Y-%m-%d')
                        date_columns.append((idx, header))
                    except ValueError:
                        pass
            
            books_data = []
            for row_idx, row in enumerate(all_values[1:], start=2):
                if len(row) < 3 or not row[0]:  # Skip empty rows
                    continue
                
                book_name = row[0]
                author = row[1] if len(row) > 1 else ''
                amazon_link = row[2] if len(row) > 2 else ''
                category = row[3] if len(row) > 3 and 'Category' in headers else ''
                
                # Extract BSR values
                bsr_history = []
                for col_idx, date_str in date_columns:
                    if col_idx < len(row):
                        bsr_str = row[col_idx]
                        if bsr_str and bsr_str.isdigit():
                            bsr_history.append({
                                'date': date_str,
                                'bsr': int(bsr_str)
                            })
                
                books_data.append({
                    'name': book_name,
                    'author': author,
                    'amazon_link': amazon_link,
                    'category': category,
                    'bsr_history': bsr_history,
                    'current_bsr': bsr_history[-1]['bsr'] if bsr_history else None
                })
            
            return books_data
            
        except Exception as e:
            logger.error(f"Error getting BSR history: {e}")
            return []

