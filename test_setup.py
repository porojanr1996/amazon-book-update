"""
Test script to verify setup is correct
Run this before deploying to check if everything is configured properly
"""
import sys
import os

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    try:
        import gspread
        import bs4
        import requests
        import flask
        import schedule
        from google.oauth2 import service_account
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  Run: pip install -r requirements.txt")
        return False

def test_config():
    """Test if configuration file exists and is valid"""
    print("\nTesting configuration...")
    try:
        import config
        print(f"✓ Config loaded")
        print(f"  - Credentials path: {config.GOOGLE_SHEETS_CREDENTIALS_PATH}")
        print(f"  - Spreadsheet ID: {'Set' if config.GOOGLE_SHEETS_SPREADSHEET_ID else 'NOT SET'}")
        print(f"  - Schedule time: {config.SCHEDULE_TIME}")
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False

def test_credentials():
    """Test if Google credentials file exists"""
    print("\nTesting Google credentials...")
    try:
        import config
        creds_path = config.GOOGLE_SHEETS_CREDENTIALS_PATH
        
        if not os.path.exists(creds_path):
            print(f"✗ Credentials file not found: {creds_path}")
            print("  Download credentials.json from Google Cloud Console")
            return False
        
        # Try to load credentials
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(creds_path)
        print(f"✓ Credentials file is valid")
        print(f"  - Service account email: {creds.service_account_email}")
        return True
    except Exception as e:
        print(f"✗ Credentials error: {e}")
        return False

def test_google_sheets_connection():
    """Test connection to Google Sheets"""
    print("\nTesting Google Sheets connection...")
    try:
        from google_sheets import GoogleSheetsManager
        import config
        
        if not config.GOOGLE_SHEETS_SPREADSHEET_ID:
            print("✗ Spreadsheet ID not set in config")
            return False
        
        manager = GoogleSheetsManager(
            config.GOOGLE_SHEETS_CREDENTIALS_PATH,
            config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        
        books = manager.get_all_books()
        print(f"✓ Successfully connected to Google Sheets")
        print(f"  - Found {len(books)} books")
        
        if books:
            print(f"  - Example book: {books[0]['name']}")
        
        return True
    except Exception as e:
        print(f"✗ Google Sheets connection error: {e}")
        print("  Make sure:")
        print("  1. Spreadsheet ID is correct")
        print("  2. Service account has access to the sheet")
        print("  3. Google Sheets API is enabled")
        return False

def test_amazon_scraper():
    """Test Amazon scraper (without actually scraping)"""
    print("\nTesting Amazon scraper...")
    try:
        from amazon_scraper import AmazonScraper
        scraper = AmazonScraper()
        print("✓ Amazon scraper initialized")
        return True
    except Exception as e:
        print(f"✗ Amazon scraper error: {e}")
        return False

def test_flask_app():
    """Test Flask app initialization"""
    print("\nTesting Flask app...")
    try:
        from app import app
        print("✓ Flask app initialized")
        return True
    except Exception as e:
        print(f"✗ Flask app error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Setup Verification Test")
    print("=" * 50)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Credentials", test_credentials()))
    
    # Only test Sheets connection if credentials exist
    if results[-1][1]:
        results.append(("Google Sheets", test_google_sheets_connection()))
    
    results.append(("Amazon Scraper", test_amazon_scraper()))
    results.append(("Flask App", test_flask_app()))
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("✓ All tests passed! Setup is correct.")
        return 0
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

