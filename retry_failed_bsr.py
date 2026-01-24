#!/usr/bin/env python3
"""
Script pentru a identifica cărțile care au eșuat la update BSR din log-uri
și a re-pornește update-ul doar pentru acele cărți
"""
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
import config

def extract_failed_books_from_logs(log_file_path="app.log", max_lines=10000):
    """
    Extrage cărțile care au eșuat din log-uri
    
    Returnează: dict cu {worksheet_name: [list of amazon_urls]}
    """
    failed_books = {}  # {worksheet: [urls]}
    current_worksheet = None
    current_book_url = None
    
    print("📋 Analizare log-uri pentru cărți eșuate...")
    print()
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            # Citește ultimele max_lines linii
            lines = f.readlines()[-max_lines:]
            
            for line in lines:
                # Identifică worksheet-ul curent
                worksheet_match = re.search(r'Procesare:\s*(.+?)$', line)
                if worksheet_match:
                    current_worksheet = worksheet_match.group(1).strip()
                    if current_worksheet not in failed_books:
                        failed_books[current_worksheet] = []
                
                # Identifică URL-ul cărții curente
                url_match = re.search(r'URL:\s*(https?://[^\s]+)', line)
                if url_match:
                    current_book_url = url_match.group(1).strip()
                
                # Identifică eșecuri
                if re.search(r'❌ Nu s-a putut extrage BSR|Failed to scrape BSR|BSR not found|Request error', line, re.IGNORECASE):
                    if current_worksheet and current_book_url:
                        # Adaugă URL-ul dacă nu există deja
                        if current_book_url not in failed_books.get(current_worksheet, []):
                            failed_books.setdefault(current_worksheet, []).append(current_book_url)
                            print(f"   ❌ Eșec găsit: {current_worksheet} - {current_book_url}")
    
    except FileNotFoundError:
        print(f"⚠️  Fișierul de log nu a fost găsit: {log_file_path}")
        return {}
    except Exception as e:
        print(f"❌ Eroare la citirea log-urilor: {e}")
        return {}
    
    print()
    return failed_books

def get_books_by_urls(sheets_manager, worksheet_name, urls):
    """Obține cărțile din Google Sheets care au URL-urile specificate"""
    all_books = sheets_manager.get_all_books(worksheet_name)
    matching_books = []
    
    for book in all_books:
        book_url = book.get('amazon_link', '').strip()
        # Normalizează URL-urile pentru comparație
        for url in urls:
            url_normalized = url.strip()
            # Compară URL-urile (poate fi cu sau fără trailing slash, query params, etc.)
            if url_normalized in book_url or book_url in url_normalized:
                matching_books.append(book)
                break
    
    return matching_books

def retry_failed_books(failed_books_dict, dry_run=False):
    """
    Re-încearcă update-ul BSR pentru cărțile care au eșuat
    
    Args:
        failed_books_dict: {worksheet_name: [list of amazon_urls]}
        dry_run: Dacă True, nu scrie în Google Sheets
    """
    if not failed_books_dict:
        print("✅ Nu s-au găsit cărți eșuate în log-uri!")
        return True
    
    print("=" * 60)
    print("🔄 RE-ÎNCERCARE UPDATE BSR PENTRU CĂRȚI EȘUATE")
    print("=" * 60)
    print()
    
    if dry_run:
        print("⚠️  MOD DRY-RUN: Nu se vor scrie date în Google Sheets")
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
    
    # Procesează fiecare worksheet
    for worksheet_name, failed_urls in failed_books_dict.items():
        print(f"📚 Worksheet: {worksheet_name}")
        print(f"   📖 Cărți eșuate: {len(failed_urls)}")
        print("-" * 60)
        
        # Obține cărțile care au eșuat
        failed_books = get_books_by_urls(sheets_manager, worksheet_name, failed_urls)
        
        if not failed_books:
            print(f"   ⚠️  Nu s-au găsit cărți în Google Sheets pentru URL-urile eșuate")
            print()
            continue
        
        print(f"   📖 Găsite {len(failed_books)} cărți pentru re-încercare")
        print()
        
        # Obține rândul pentru astăzi
        today_row = sheets_manager.get_today_row(worksheet_name)
        print(f"   📅 Rând pentru astăzi: {today_row}")
        print()
        
        worksheet_success = 0
        worksheet_failed = 0
        
        # Procesează fiecare carte eșuată
        for i, book in enumerate(failed_books, 1):
            print(f"   📖 [{i}/{len(failed_books)}] {book['name']}")
            print(f"      👤 Autor: {book['author']}")
            print(f"      🔗 URL: {book['amazon_link']}")
            
            try:
                # Pentru UK, folosește direct Playwright
                is_uk = '.co.uk' in book['amazon_link'] or 'amazon.co.uk' in book['amazon_link']
                
                if is_uk:
                    print(f"      🔍 Re-încercare cu Playwright (UK)...", end=' ', flush=True)
                    try:
                        bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=True)
                    except Exception as e:
                        print(f"\n      ❌ Eroare Playwright: {e}")
                        bsr = None
                else:
                    # Pentru US, încearcă mai întâi cu requests
                    print(f"      🔍 Re-încercare extragere BSR...", end=' ', flush=True)
                    bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=False)
                    
                    # Dacă nu funcționează, încearcă cu Playwright
                    if not bsr:
                        print(f"\n      🔄 Încercare cu Playwright...", end=' ', flush=True)
                        bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=True)
                
                if bsr:
                    print(f"✅ BSR: #{bsr:,}")
                    
                    if not dry_run:
                        # Scrie în Google Sheets
                        sheets_manager.update_bsr(book['col'], today_row, bsr, worksheet_name)
                        print(f"      ✅ Scris în Google Sheets (coloana {book['col']}, rândul {today_row})")
                    else:
                        print(f"      ⚠️  DRY-RUN: Ar fi scris BSR #{bsr:,}")
                    
                    worksheet_success += 1
                    total_success += 1
                else:
                    print(f"❌ Nu s-a putut extrage BSR (din nou)")
                    worksheet_failed += 1
                    total_failed += 1
            
            except Exception as e:
                print(f"❌ Eroare: {e}")
                worksheet_failed += 1
                total_failed += 1
            
            print()
            
            # Delay între request-uri
            if i < len(failed_books):
                delay = config.AMAZON_DELAY_BETWEEN_REQUESTS
                print(f"      ⏳ Așteptare {delay}s între request-uri...")
                time.sleep(delay)
                print()
        
        # Rezumat pentru worksheet
        print(f"   📊 Rezumat {worksheet_name}:")
        print(f"      ✅ Succese: {worksheet_success}")
        print(f"      ❌ Eșecuri: {worksheet_failed}")
        print()
        
        # Calculează și actualizează media (dacă nu e dry-run)
        if not dry_run and worksheet_success > 0:
            try:
                print(f"   📊 Recalculare medie BSR pentru {worksheet_name}...")
                sheets_manager.calculate_and_update_average(today_row, worksheet_name)
                print(f"   ✅ Medie actualizată")
            except Exception as e:
                print(f"   ⚠️  Eroare la calcularea mediei: {e}")
            print()
    
    # Rezumat final
    print("=" * 60)
    print("📊 REZUMAT FINAL RE-ÎNCERCARE")
    print("=" * 60)
    print(f"   ✅ Succese: {total_success}")
    print(f"   ❌ Eșecuri: {total_failed}")
    print(f"   📚 Total procesate: {total_success + total_failed}")
    print()
    
    return total_failed == 0

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Re-încearcă update BSR pentru cărțile eșuate')
    parser.add_argument('--log-file', '-l', default='app.log',
                       help='Calea către fișierul de log (default: app.log)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Mod dry-run: nu scrie în Google Sheets')
    parser.add_argument('--max-lines', type=int, default=10000,
                       help='Numărul maxim de linii de log de analizat (default: 10000)')
    
    args = parser.parse_args()
    
    print()
    if args.dry_run:
        print("⚠️  ATENȚIE: Mod DRY-RUN activat - nu se vor scrie date!")
    else:
        print("⚠️  ATENȚIE: Acest script va scrie date reale în Google Sheets!")
    print()
    
    # Extrage cărțile eșuate din log-uri
    failed_books = extract_failed_books_from_logs(args.log_file, args.max_lines)
    
    if not failed_books:
        print("✅ Nu s-au găsit cărți eșuate în log-uri!")
        sys.exit(0)
    
    print(f"📊 Găsite cărți eșuate în {len(failed_books)} worksheet-uri:")
    for ws, urls in failed_books.items():
        print(f"   - {ws}: {len(urls)} cărți")
    print()
    
    if not args.dry_run:
        response = input("Continuă cu re-încercarea? (da/nu): ").strip().lower()
        if response not in ['da', 'yes', 'y', 'd']:
            print("❌ Anulat.")
            sys.exit(0)
        print()
    
    # Re-încearcă update-ul
    success = retry_failed_books(failed_books, dry_run=args.dry_run)
    sys.exit(0 if success else 1)

