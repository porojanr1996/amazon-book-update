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

def update_bsr_for_worksheets(worksheet_names=None, dry_run=False):
    """
    Actualizează BSR-ul pentru toate cărțile din worksheet-urile specificate
    
    Args:
        worksheet_names: Lista de worksheet-uri (None = toate)
        dry_run: Dacă True, nu scrie în Google Sheets, doar afișează
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
            
            worksheet_success = 0
            worksheet_failed = 0
            
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
                    
                    # Check for existing screenshots before scraping
                    import os
                    from pathlib import Path
                    screenshot_dir = Path(os.getenv('SCREENSHOT_DIR', '/tmp/amazon_screenshots'))
                    screenshots_before = set()
                    if screenshot_dir.exists():
                        screenshots_before = set(screenshot_dir.glob('amazon_bsr_*.png'))
                    
                    try:
                        bsr = scraper.extract_bsr(book['amazon_link'], use_playwright=True)
                        
                        # Check if a new screenshot was created (scraping stopped for OCR processing)
                        screenshots_after = set()
                        if screenshot_dir.exists():
                            screenshots_after = set(screenshot_dir.glob('amazon_bsr_*.png'))
                        
                        new_screenshots = screenshots_after - screenshots_before
                        if new_screenshots:
                            # A new screenshot was created - scraping stopped
                            latest_screenshot = max(new_screenshots, key=lambda p: p.stat().st_mtime)
                            print(f"\n      📸 Screenshot salvat: {latest_screenshot.name}")
                            print(f"      🛑 Scraping oprit - screenshot salvat pentru procesare OCR")
                            print(f"\n      💡 Rulează scriptul de procesare:")
                            print(f"         python process_screenshots.py")
                            print(f"\n      🚫 Oprește scraping-ul pentru a procesa screenshot-ul...")
                            # Stop processing more books
                            print(f"\n   ⚠️  Scraping oprit după screenshot. Procesează screenshot-urile cu:")
                            print(f"      python process_screenshots.py")
                            break
                    except Exception as e:
                        print(f"\n      ❌ Eroare Playwright: {e}")
                        bsr = None
                        
                        # Check if screenshot was created even on error
                        screenshots_after = set()
                        if screenshot_dir.exists():
                            screenshots_after = set(screenshot_dir.glob('amazon_bsr_*.png'))
                        
                        new_screenshots = screenshots_after - screenshots_before
                        if new_screenshots:
                            latest_screenshot = max(new_screenshots, key=lambda p: p.stat().st_mtime)
                            print(f"\n      📸 Screenshot salvat: {latest_screenshot.name}")
                            print(f"      🛑 Scraping oprit - screenshot salvat pentru procesare OCR")
                            print(f"\n      💡 Rulează: python process_screenshots.py")
                            break
                        
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
                
                except Exception as e:
                    print(f"❌ Eroare: {e}")
                    worksheet_failed += 1
                    total_failed += 1
                
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
            
            # Calculează și actualizează media (dacă nu e dry-run)
            if not dry_run and worksheet_success > 0:
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
        print("   Va actualiza BSR-ul pentru toate cărțile din worksheet-urile selectate.")
    print()
    
    if not args.dry_run:
        response = input("Continuă? (da/nu): ").strip().lower()
        if response not in ['da', 'yes', 'y', 'd']:
            print("❌ Anulat.")
            sys.exit(0)
        print()
    
    success = update_bsr_for_worksheets(worksheet_names, dry_run=args.dry_run)
    sys.exit(0 if success else 1)

