#!/usr/bin/env python3
"""
Script pentru actualizarea BSR-ului pentru toate cărțile
Similar cu populate_cover_images.py, dar pentru BSR
"""
import sys
import time
from datetime import datetime
import pytz
from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
import config

def update_bsr_for_worksheets(worksheet_names=None, dry_run=False, retry_failed=False):
    """
    Actualizează BSR-ul pentru toate cărțile din worksheet-urile specificate
    
    Args:
        worksheet_names: Lista de worksheet-uri (None = toate)
        dry_run: Dacă True, nu scrie în Google Sheets, doar afișează
        retry_failed: Dacă True, procesează doar cărțile care nu au BSR pentru ziua curentă
    """
    
    print("=" * 60)
    print("🔄 ACTUALIZARE BSR PENTRU CĂRȚI")
    print("=" * 60)
    print()
    
    if dry_run:
        print("⚠️  MOD DRY-RUN: Nu se vor scrie date în Google Sheets")
        print()
    
    # Conectare la Google Sheets
    print("📋 Conectare la Google Sheets...")
    try:
        # Verifică și corectează calea către credentials.json
        import os
        creds_path = config.GOOGLE_SHEETS_CREDENTIALS_PATH
        
        # Dacă fișierul nu există la calea specificată, încearcă alte locații
        if not os.path.exists(creds_path):
            # Încearcă calea relativă la directorul curent
            script_dir = os.path.dirname(os.path.abspath(__file__))
            creds_path_abs = os.path.join(script_dir, 'credentials.json')
            if os.path.exists(creds_path_abs):
                creds_path = creds_path_abs
            else:
                # Fallback: calea standard pe EC2
                ec2_path = '/home/ec2-user/app/books-reporting/credentials.json'
                if os.path.exists(ec2_path):
                    creds_path = ec2_path
                else:
                    # Ultimul fallback: calea relativă
                    creds_path = os.path.join(script_dir, 'credentials.json')
        
        if not os.path.exists(creds_path):
            print(f"❌ Fișierul credentials.json nu a fost găsit!")
            print(f"   Căută la: {creds_path}")
            print(f"   💡 Setează variabila GOOGLE_SHEETS_CREDENTIALS_PATH sau plasează fișierul în directorul proiectului")
            return False
        
        sheets_manager = GoogleSheetsManager(
            creds_path,
            config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        print("✅ Conectat cu succes")
    except Exception as e:
        print(f"❌ Eroare la conectare: {e}")
        return False
    print()
    
    # Obține worksheet-urile
    if worksheet_names is None:
        all_worksheets = sheets_manager.get_all_worksheets()
        # Filtrează Sheet1 și Sheet3 dacă sunt goale
        worksheet_names = [ws for ws in all_worksheets if ws not in ['Sheet1', 'Sheet3']]
        # Sau procesează toate dacă vrei
        # worksheet_names = all_worksheets
    
    print(f"📚 Worksheet-uri de procesat: {len(worksheet_names)}")
    for ws in worksheet_names:
        print(f"   - {ws}")
    print()
    
    # Inițializare scraper
    scraper = AmazonScraper(
        delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
        retry_attempts=config.AMAZON_RETRY_ATTEMPTS
    )
    
    total_success = 0
    total_failed = 0
    total_worksheets = len(worksheet_names)
    
    # Procesează fiecare worksheet
    for worksheet_idx, worksheet_name in enumerate(worksheet_names, 1):
        print(f"📚 [{worksheet_idx}/{total_worksheets}] Procesare: {worksheet_name}")
        print("-" * 60)
        
        try:
            books = sheets_manager.get_all_books(worksheet_name)
            if not books:
                print(f"   ⚠️  Nu s-au găsit cărți în {worksheet_name}")
                print()
                continue
            
            print(f"   📖 Găsite {len(books)} cărți")
            print()
            
            # Obține rândul pentru astăzi
            today_row = sheets_manager.get_today_row(worksheet_name)
            print(f"   📅 Rând pentru astăzi: {today_row}")
            print(f"   🕐 Data: {datetime.now(pytz.timezone('Europe/Bucharest')).strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Dacă e retry-failed, filtrează doar cărțile care nu au BSR pentru ziua curentă
            if retry_failed:
                print(f"   🔄 Mod RETRY-FAILED: Filtrare cărți fără BSR pentru ziua curentă...")
                books_without_bsr = []
                try:
                    worksheet = sheets_manager.spreadsheet.worksheet(worksheet_name)
                    all_values = worksheet.get_all_values()
                    
                    for book in books:
                        col_idx = book['col'] - 1  # Convert to 0-based
                        # Check if today_row has BSR value for this book
                        if today_row <= len(all_values):
                            row_values = all_values[today_row - 1]  # today_row is 1-based
                            if col_idx < len(row_values):
                                bsr_str = row_values[col_idx].strip()
                                # If empty or not a number, consider it failed
                                if not bsr_str or not bsr_str.replace(',', '').isdigit():
                                    books_without_bsr.append(book)
                        else:
                            # Row doesn't exist yet, consider it failed
                            books_without_bsr.append(book)
                    
                    if not books_without_bsr:
                        print(f"   ✅ Toate cărțile au BSR pentru ziua curentă!")
                        print()
                        continue
                    
                    print(f"   📋 Găsite {len(books_without_bsr)} cărți fără BSR pentru ziua curentă:")
                    for book in books_without_bsr:
                        print(f"      - {book['name']}")
                    print()
                    books = books_without_bsr
                except Exception as e:
                    print(f"   ⚠️  Eroare la filtrare: {e}")
                    print(f"   📋 Se procesează toate cărțile...")
                    print()
            
            worksheet_success = 0
            worksheet_failed = 0
            failed_books = []  # Listă cu cărțile care au eșuat
            
            # Procesează fiecare carte
            for i, book in enumerate(books, 1):
                print(f"   📖 [{i}/{len(books)}] {book['name']}")
                print(f"      👤 Autor: {book['author']}")
                print(f"      🔗 URL: {book['amazon_link']}")
                
                try:
                    # Folosește direct Playwright pentru toate domeniile (Amazon blochează request-uri simple pe EC2)
                    is_uk = '.co.uk' in book['amazon_link'] or 'amazon.co.uk' in book['amazon_link']
                    domain_type = "UK" if is_uk else "US"
                    
                    print(f"      🔍 Extragere BSR cu Playwright ({domain_type})...", end=' ', flush=True)
                    try:
                        bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=True)
                    except Exception as e:
                        print(f"\n      ❌ Eroare Playwright: {e}")
                        bsr = None
                        
                        # Dacă Playwright eșuează, încearcă metoda simplă ca ultim fallback
                        if not bsr:
                            print(f"      🔄 Încercare cu metoda simplă (fallback)...", end=' ', flush=True)
                            try:
                                bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=False)
                            except Exception as e2:
                                print(f"\n      ❌ Eroare metoda simplă: {e2}")
                                bsr = None
                    
                    if bsr:
                        print(f"✅ BSR: #{bsr:,}")
                        
                        if not dry_run:
                            # Scrie în Google Sheets
                            sheets_manager.update_bsr(book['col'], today_row, bsr, worksheet_name)
                            print(f"      ✅ Scris în Google Sheets (coloana {book['col']}, rândul {today_row})")
                        else:
                            print(f"      ⚠️  DRY-RUN: Ar fi scris BSR #{bsr:,} în coloana {book['col']}, rândul {today_row}")
                        
                        worksheet_success += 1
                        total_success += 1
                    else:
                        # Verifică dacă e blocat de CAPTCHA sau alte probleme
                        is_blocked = False
                        error_msg = str(e) if 'e' in locals() else "Unknown error"
                        
                        # Dacă Playwright a eșuat cu CAPTCHA sau blocking
                        if 'captcha' in error_msg.lower() or 'blocked' in error_msg.lower():
                            is_blocked = True
                        
                        if is_blocked:
                            print(f"⚠️  Carte blocată de Amazon - va fi re-încercată mai târziu")
                            # Marchează în Google Sheets cu valoare specială pentru tracking
                            if not dry_run:
                                try:
                                    # Scrie "BLOCKED" sau lasă gol pentru a indica că trebuie actualizat manual
                                    # Nu scriem nimic - rândul rămâne gol, indicând că trebuie actualizat
                                    print(f"      ⚠️  Rândul {today_row}, coloana {book['col']} rămâne neactualizat (blocat)")
                                except Exception as e:
                                    print(f"      ⚠️  Nu s-a putut marca ca blocat: {e}")
                        else:
                            print(f"❌ Nu s-a putut extrage BSR")
                        
                        worksheet_failed += 1
                        total_failed += 1
                        # Salvează cartea pentru retry
                        failed_books.append(book)
                
                except Exception as e:
                    print(f"❌ Eroare: {e}")
                    worksheet_failed += 1
                    total_failed += 1
                    # Salvează cartea pentru retry
                    failed_books.append(book)
                
                print()
                
                # Delay între request-uri (dacă nu e ultima carte)
                if i < len(books):
                    delay = config.AMAZON_DELAY_BETWEEN_REQUESTS
                    # Dacă a eșuat, așteaptă mai mult înainte de următorul request
                    if not bsr:
                        delay = delay * 1.5  # 50% mai mult dacă a eșuat
                    print(f"      ⏳ Așteptare {delay:.1f}s între request-uri...")
                    time.sleep(delay)
                    print()
            
            # Rezumat pentru worksheet
            print(f"   📊 Rezumat {worksheet_name}:")
            print(f"      ✅ Succese: {worksheet_success}")
            print(f"      ❌ Eșecuri: {worksheet_failed}")
            print()
            
            # Retry pentru cărțile care au eșuat (max 2 retries)
            max_retries = 2
            retry_count = 0
            while failed_books and retry_count < max_retries:
                retry_count += 1
                print(f"   🔄 Retry #{retry_count} pentru {len(failed_books)} cărți care au eșuat...")
                print()
                
                retry_failed = []
                for i, book in enumerate(failed_books, 1):
                    print(f"   📖 [{i}/{len(failed_books)}] RETRY: {book['name']}")
                    print(f"      👤 Autor: {book['author']}")
                    print(f"      🔗 URL: {book['amazon_link']}")
                    
                    try:
                        is_uk = '.co.uk' in book['amazon_link'] or 'amazon.co.uk' in book['amazon_link']
                        domain_type = "UK" if is_uk else "US"
                        
                        print(f"      🔍 Extragere BSR cu Playwright ({domain_type})...", end=' ', flush=True)
                        try:
                            bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=True)
                        except Exception as e:
                            print(f"\n      ❌ Eroare Playwright: {e}")
                            bsr = None
                            
                            if not bsr:
                                print(f"      🔄 Încercare cu metoda simplă (fallback)...", end=' ', flush=True)
                                try:
                                    bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=False)
                                except Exception as e2:
                                    print(f"\n      ❌ Eroare metoda simplă: {e2}")
                                    bsr = None
                        
                        if bsr:
                            print(f"✅ BSR: #{bsr:,}")
                            
                            if not dry_run:
                                sheets_manager.update_bsr(book['col'], today_row, bsr, worksheet_name)
                                print(f"      ✅ Scris în Google Sheets (coloana {book['col']}, rândul {today_row})")
                            else:
                                print(f"      ⚠️  DRY-RUN: Ar fi scris BSR #{bsr:,} în coloana {book['col']}, rândul {today_row}")
                            
                            worksheet_success += 1
                            total_success += 1
                            worksheet_failed -= 1
                            total_failed -= 1
                        else:
                            print(f"❌ Nu s-a putut extrage BSR (retry {retry_count}/{max_retries})")
                            retry_failed.append(book)
                        
                    except Exception as e:
                        print(f"❌ Eroare: {e}")
                        retry_failed.append(book)
                    
                    print()
                    
                    # Delay între request-uri
                    if i < len(failed_books):
                        delay = config.AMAZON_DELAY_BETWEEN_REQUESTS * 1.5  # Mai mult delay la retry
                        print(f"      ⏳ Așteptare {delay:.1f}s între request-uri...")
                        time.sleep(delay)
                        print()
                
                failed_books = retry_failed
                
                if failed_books:
                    print(f"   ⚠️  {len(failed_books)} cărți au eșuat și la retry #{retry_count}")
                    if retry_count < max_retries:
                        print(f"   🔄 Se va încerca încă o dată...")
                    print()
            
            # Calculează și actualizează media (dacă nu e dry-run)
            if not dry_run and worksheet_success > 0:
                try:
                    print(f"   📊 Calculare medie BSR pentru {worksheet_name}...")
                    sheets_manager.calculate_and_update_average(today_row, worksheet_name)
                    print(f"   ✅ Medie actualizată")
                except Exception as e:
                    print(f"   ⚠️  Eroare la calcularea mediei: {e}")
                print()
            
            # Dacă mai sunt cărți care au eșuat după toate retry-urile
            if failed_books:
                print(f"   ⚠️  {len(failed_books)} cărți au eșuat după {max_retries} încercări:")
                for book in failed_books:
                    print(f"      - {book['name']} ({book['amazon_link']})")
                print()
        
        except Exception as e:
            print(f"   ❌ Eroare la procesarea worksheet-ului {worksheet_name}: {e}")
            print()
    
    # Rezumat final
    print("=" * 60)
    print("📊 REZUMAT FINAL")
    print("=" * 60)
    print(f"   ✅ Succese: {total_success}")
    print(f"   ❌ Eșecuri: {total_failed}")
    print(f"   📚 Total procesate: {total_success + total_failed}")
    print(f"   📋 Worksheet-uri procesate: {total_worksheets}")
    print()
    
    if dry_run:
        print("⚠️  MOD DRY-RUN: Nu s-au scris date în Google Sheets")
        print("   Rulează fără --dry-run pentru a scrie efectiv datele")
    else:
        print("✅ Actualizare BSR finalizată!")
        print(f"   Verifică Google Sheets pentru a vedea noile valori BSR")
    
    print()
    return total_success > 0


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Actualizează BSR-ul pentru cărți')
    parser.add_argument('--worksheet', '-w', action='append', 
                       help='Worksheet-uri de procesat (poate fi folosit de mai multe ori)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Mod dry-run: nu scrie în Google Sheets, doar afișează')
    parser.add_argument('--all', action='store_true',
                       help='Procesează toate worksheet-urile')
    parser.add_argument('--retry-failed', action='store_true',
                       help='Procesează doar cărțile care nu au BSR pentru ziua curentă (retry pentru eșecuri)')
    
    args = parser.parse_args()
    
    worksheet_names = None
    if args.worksheet:
        worksheet_names = args.worksheet
    elif not args.all:
        # Default: doar Crime Fiction - US
        worksheet_names = ['Crime Fiction - US']
    
    print()
    if args.dry_run:
        print("⚠️  ATENȚIE: Mod DRY-RUN activat - nu se vor scrie date!")
    else:
        print("⚠️  ATENȚIE: Acest script va scrie date reale în Google Sheets!")
        if args.retry_failed:
            print("   🔄 Mod RETRY-FAILED: Va procesa doar cărțile fără BSR pentru ziua curentă.")
        else:
            print("   Va actualiza BSR-ul pentru toate cărțile din worksheet-urile selectate.")
    print()
    
    if not args.dry_run:
        response = input("Continuă? (da/nu): ").strip().lower()
        if response not in ['da', 'yes', 'y', 'd']:
            print("❌ Anulat.")
            sys.exit(0)
        print()
    
    success = update_bsr_for_worksheets(worksheet_names, dry_run=args.dry_run, retry_failed=args.retry_failed)
    sys.exit(0 if success else 1)

