#!/usr/bin/env python3
"""
Script pentru retry-ul cărților care au eșuat la update BSR
Analizează log-urile și re-pornește update-ul doar pentru cărțile care au eșuat
"""
import re
import sys
import time
from pathlib import Path
from collections import defaultdict
from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
import config
import pytz
from datetime import datetime

def parse_log_for_failed_books(log_file_path, worksheet_name=None):
    """
    Parsează log-urile pentru a găsi cărțile care au eșuat
    
    Returnează: dict cu {worksheet_name: [list of book names]}
    """
    failed_books = defaultdict(list)
    current_book = None
    current_worksheet = None
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ Fișierul de log nu a fost găsit: {log_file_path}")
        return failed_books
    
    # Pattern-uri pentru a identifica cărțile și eșecurile
    book_pattern = r'📖\s*\[\d+/\d+\]\s*(.+?)\s*$'
    worksheet_pattern = r'📚\s*\[.*?\]\s*Procesare:\s*(.+?)$'
    failure_pattern = r'❌\s*Nu s-a putut extrage BSR'
    error_pattern = r'ERROR:amazon_scraper:.*?for url: (https://www\.amazon\.com/dp/[A-Z0-9]+)'
    
    for i, line in enumerate(lines):
        # Identifică worksheet-ul curent
        worksheet_match = re.search(worksheet_pattern, line)
        if worksheet_match:
            current_worksheet = worksheet_match.group(1).strip()
            if worksheet_name and current_worksheet != worksheet_name:
                continue
        
        # Identifică cartea curentă
        book_match = re.search(book_pattern, line)
        if book_match:
            current_book = book_match.group(1).strip()
            # Extrage autorul dacă există
            if '👤 Autor:' in line or (i + 1 < len(lines) and '👤 Autor:' in lines[i + 1]):
                # Autorul este pe linia următoare
                pass
        
        # Verifică dacă cartea curentă a eșuat
        if current_book and current_worksheet:
            if failure_pattern in line:
                # Verifică dacă nu e deja adăugată
                if current_book not in failed_books[current_worksheet]:
                    failed_books[current_worksheet].append(current_book)
                    print(f"   📖 Găsită carte eșuată: {current_book} în {current_worksheet}")
    
    return failed_books

def retry_failed_books(failed_books_dict, max_retries=2):
    """
    Re-pornește update-ul BSR pentru cărțile care au eșuat
    """
    if not failed_books_dict:
        print("✅ Nu s-au găsit cărți eșuate!")
        return True
    
    print("=" * 60)
    print("🔄 RETRY PENTRU CĂRȚILE EȘUATE")
    print("=" * 60)
    print()
    
    # Conectare la Google Sheets
    print("📋 Conectare la Google Sheets...")
    try:
        sheets_manager = GoogleSheetsManager(
            config.GOOGLE_SHEETS_CREDENTIALS_PATH,
            config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        print("✅ Conectat cu succes")
    except Exception as e:
        print(f"❌ Eroare la conectare: {e}")
        return False
    print()
    
    # Inițializare scraper
    scraper = AmazonScraper(
        delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
        retry_attempts=config.AMAZON_RETRY_ATTEMPTS
    )
    
    total_success = 0
    total_failed = 0
    
    # Procesează fiecare worksheet cu cărți eșuate
    for worksheet_name, book_names in failed_books_dict.items():
        print(f"📚 Worksheet: {worksheet_name}")
        print(f"   📖 Cărți de retry: {len(book_names)}")
        print("-" * 60)
        
        try:
            # Obține toate cărțile din worksheet
            all_books = sheets_manager.get_all_books(worksheet_name)
            
            # Filtrează doar cărțile care au eșuat
            failed_books_data = []
            for book in all_books:
                # Caută potrivire parțială a numelui
                for failed_book_name in book_names:
                    if failed_book_name.lower() in book['name'].lower() or book['name'].lower() in failed_book_name.lower():
                        failed_books_data.append(book)
                        break
            
            if not failed_books_data:
                print(f"   ⚠️  Nu s-au găsit cărțile eșuate în Google Sheets")
                print()
                continue
            
            print(f"   📖 Găsite {len(failed_books_data)} cărți pentru retry")
            print()
            
            # Obține rândul pentru astăzi
            today_row = sheets_manager.get_today_row(worksheet_name)
            print(f"   📅 Rând pentru astăzi: {today_row}")
            print()
            
            worksheet_success = 0
            worksheet_failed = 0
            
            # Procesează fiecare carte eșuată
            for i, book in enumerate(failed_books_data, 1):
                print(f"   📖 [{i}/{len(failed_books_data)}] {book['name']}")
                print(f"      👤 Autor: {book.get('author', 'N/A')}")
                print(f"      🔗 URL: {book['amazon_link']}")
                
                retry_success = False
                for retry_num in range(max_retries):
                    try:
                        # Pentru UK, folosește direct Playwright
                        is_uk = '.co.uk' in book['amazon_link'] or 'amazon.co.uk' in book['amazon_link']
                        
                        if is_uk:
                            print(f"      🔍 Retry {retry_num + 1}/{max_retries} cu Playwright (UK)...", end=' ', flush=True)
                            bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=True)
                        else:
                            # Pentru US, încearcă mai întâi cu requests
                            print(f"      🔍 Retry {retry_num + 1}/{max_retries}...", end=' ', flush=True)
                            bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=False)
                            
                            # Dacă nu funcționează, încearcă cu Playwright
                            if not bsr:
                                print(f"\n      🔄 Încercare cu Playwright...", end=' ', flush=True)
                                bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=True)
                        
                        if bsr:
                            print(f"✅ BSR: #{bsr:,}")
                            
                            # Scrie în Google Sheets
                            sheets_manager.update_bsr(book['col'], today_row, bsr, worksheet_name)
                            print(f"      ✅ Scris în Google Sheets (coloana {book['col']}, rândul {today_row})")
                            
                            worksheet_success += 1
                            total_success += 1
                            retry_success = True
                            break
                        else:
                            print(f"❌ Nu s-a putut extrage BSR")
                            if retry_num < max_retries - 1:
                                print(f"      ⏳ Așteptare înainte de următorul retry...")
                                time.sleep(5)
                    
                    except Exception as e:
                        print(f"❌ Eroare: {e}")
                        if retry_num < max_retries - 1:
                            print(f"      ⏳ Așteptare înainte de următorul retry...")
                            time.sleep(5)
                
                if not retry_success:
                    worksheet_failed += 1
                    total_failed += 1
                
                print()
                
                # Delay între request-uri
                if i < len(failed_books_data):
                    delay = config.AMAZON_DELAY_BETWEEN_REQUESTS
                    print(f"      ⏳ Așteptare {delay}s între request-uri...")
                    time.sleep(delay)
                    print()
            
            # Rezumat pentru worksheet
            print(f"   📊 Rezumat retry pentru {worksheet_name}:")
            print(f"      ✅ Succese: {worksheet_success}")
            print(f"      ❌ Eșecuri: {worksheet_failed}")
            print()
            
            # Calculează și actualizează media dacă au fost succese
            if worksheet_success > 0:
                try:
                    print(f"   📊 Calculare medie BSR pentru {worksheet_name}...")
                    sheets_manager.calculate_and_update_average(today_row, worksheet_name)
                    print(f"   ✅ Medie actualizată")
                except Exception as e:
                    print(f"   ⚠️  Eroare la calcularea mediei: {e}")
                print()
        
        except Exception as e:
            print(f"   ❌ Eroare la procesarea worksheet-ului {worksheet_name}: {e}")
            print()
    
    # Rezumat final
    print("=" * 60)
    print("📊 REZUMAT FINAL RETRY")
    print("=" * 60)
    print(f"   ✅ Succese: {total_success}")
    print(f"   ❌ Eșecuri: {total_failed}")
    print(f"   📚 Total procesate: {total_success + total_failed}")
    print()
    
    return total_failed == 0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Retry BSR update pentru cărțile care au eșuat')
    parser.add_argument('--log-file', '-l', 
                       default='app.log',
                       help='Calea către fișierul de log (default: app.log)')
    parser.add_argument('--worksheet', '-w',
                       help='Worksheet specific (opțional)')
    parser.add_argument('--max-retries', '-r',
                       type=int,
                       default=2,
                       help='Număr maxim de retry-uri per carte (default: 2)')
    
    args = parser.parse_args()
    
    log_file_path = Path(args.log_file)
    if not log_file_path.is_absolute():
        # Dacă e path relativ, încearcă în directorul curent sau în directorul proiectului
        project_root = Path(__file__).parent
        log_file_path = project_root / log_file_path
    
    print("=" * 60)
    print("🔍 ANALIZĂ LOG-URI PENTRU CĂRȚI EȘUATE")
    print("=" * 60)
    print()
    print(f"📄 Fișier log: {log_file_path}")
    print()
    
    # Parsează log-urile
    failed_books = parse_log_for_failed_books(str(log_file_path), args.worksheet)
    
    if not failed_books:
        print("✅ Nu s-au găsit cărți eșuate în log-uri!")
        return 0
    
    print()
    print(f"📊 Găsite cărți eșuate în {len(failed_books)} worksheet-uri:")
    for worksheet, books in failed_books.items():
        print(f"   - {worksheet}: {len(books)} cărți")
    print()
    
    # Confirmare
    response = input("Continuă cu retry? (da/nu): ").strip().lower()
    if response not in ['da', 'yes', 'y', 'd']:
        print("❌ Anulat.")
        return 0
    print()
    
    # Rulează retry
    success = retry_failed_books(failed_books, max_retries=args.max_retries)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())

