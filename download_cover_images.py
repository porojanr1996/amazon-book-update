#!/usr/bin/env python3
"""
Script pentru extragerea și descărcarea imaginilor de copertă pentru toate cărțile
Salvează imaginile local pe EC2 pentru acces permanent
"""
import sys
import os
import time
import requests
from pathlib import Path
from datetime import datetime
import pytz
from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
import config
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_image(image_url: str, save_path: Path) -> bool:
    """
    Descarcă o imagine de la URL și o salvează local
    
    Args:
        image_url: URL-ul imaginii
        save_path: Path-ul unde să salveze imaginea
        
    Returns:
        True dacă a reușit, False altfel
    """
    try:
        # Create directory if it doesn't exist
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Save to file
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"✅ Imagine descărcată: {save_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Eroare la descărcarea imaginii {image_url}: {e}")
        return False


def get_image_filename(book_name: str, amazon_url: str) -> str:
    """
    Generează un nume de fișier unic pentru imagine
    
    Args:
        book_name: Numele cărții
        amazon_url: URL-ul Amazon
        
    Returns:
        Numele fișierului (cu extensie .jpg)
    """
    # Extract ASIN from URL if possible
    asin = None
    if '/dp/' in amazon_url:
        parts = amazon_url.split('/dp/')
        if len(parts) > 1:
            asin = parts[1].split('/')[0].split('?')[0]
    
    if asin:
        return f"{asin}.jpg"
    else:
        # Use hash of URL as fallback
        url_hash = hashlib.md5(amazon_url.encode()).hexdigest()[:8]
        # Clean book name for filename
        clean_name = "".join(c for c in book_name[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_name = clean_name.replace(' ', '_')
        return f"{clean_name}_{url_hash}.jpg"


def download_covers_for_worksheets(worksheet_names=None, covers_dir=None, dry_run=False):
    """
    Descarcă imaginile de copertă pentru toate cărțile din worksheet-uri
    
    Args:
        worksheet_names: Lista de worksheet-uri (None = toate)
        covers_dir: Directorul unde să salveze imaginile (None = folosește default)
        dry_run: Dacă True, nu descarcă, doar afișează
    """
    
    print("=" * 60)
    print("📸 DESCĂRCARE IMAGINI DE COPERTĂ")
    print("=" * 60)
    print()
    
    if dry_run:
        print("⚠️  MOD DRY-RUN: Nu se vor descărca imagini")
        print()
    
    # Set default covers directory
    if covers_dir is None:
        # Default: /var/www/covers/ pe EC2, sau ./covers/ local
        if os.path.exists('/var/www'):
            covers_dir = '/var/www/covers'
        else:
            covers_dir = os.path.join(os.path.dirname(__file__), 'covers')
    
    covers_path = Path(covers_dir)
    covers_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Director pentru imagini: {covers_path}")
    print()
    
    # Conectare la Google Sheets
    print("📋 Conectare la Google Sheets...")
    try:
        import os
        creds_path = config.GOOGLE_SHEETS_CREDENTIALS_PATH
        
        if not os.path.exists(creds_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            creds_path_abs = os.path.join(script_dir, 'credentials.json')
            if os.path.exists(creds_path_abs):
                creds_path = creds_path_abs
            else:
                ec2_path = '/home/ec2-user/app/books-reporting/credentials.json'
                if os.path.exists(ec2_path):
                    creds_path = ec2_path
                else:
                    creds_path = os.path.join(script_dir, 'credentials.json')
        
        if not os.path.exists(creds_path):
            print(f"❌ Fișierul credentials.json nu a fost găsit!")
            return False
        
        sheets_manager = GoogleSheetsManager(
            creds_path,
            config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        print("✅ Conectat la Google Sheets")
        print()
        
    except Exception as e:
        print(f"❌ Eroare la conectarea la Google Sheets: {e}")
        return False
    
    # Obține worksheet-urile
    if worksheet_names is None:
        all_worksheets = sheets_manager.get_all_worksheets()
        worksheet_names = [ws for ws in all_worksheets if ws not in ['Sheet1', 'Sheet3']]
    
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
    total_skipped = 0
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
            
            worksheet_success = 0
            worksheet_failed = 0
            worksheet_skipped = 0
            
            # Procesează fiecare carte
            for i, book in enumerate(books, 1):
                print(f"   📖 [{i}/{len(books)}] {book['name']}")
                print(f"      👤 Autor: {book['author']}")
                print(f"      🔗 URL: {book['amazon_link']}")
                
                try:
                    # Generează numele fișierului
                    filename = get_image_filename(book['name'], book['amazon_link'])
                    save_path = covers_path / filename
                    
                    # Verifică dacă imaginea există deja
                    if save_path.exists():
                        print(f"      ⏭️  Imagine există deja: {filename}")
                        worksheet_skipped += 1
                        total_skipped += 1
                        print()
                        continue
                    
                    # Extrage cover image URL
                    print(f"      🔍 Extragere URL copertă...", end=' ', flush=True)
                    try:
                        cover_url = scraper.extract_cover_image(book['amazon_link'], use_playwright=False)
                    except Exception as e:
                        print(f"\n      ❌ Eroare: {e}")
                        cover_url = None
                    
                    # Dacă nu a reușit, încearcă cu Playwright
                    if not cover_url:
                        print(f"      🔄 Încercare cu Playwright...", end=' ', flush=True)
                        try:
                            cover_url = scraper.extract_cover_image(book['amazon_link'], use_playwright=True)
                        except Exception as e2:
                            print(f"\n      ❌ Eroare Playwright: {e2}")
                            cover_url = None
                    
                    if cover_url:
                        print(f"✅ URL: {cover_url[:60]}...")
                        
                        if not dry_run:
                            # Descarcă imaginea
                            print(f"      📥 Descărcare imagine...", end=' ', flush=True)
                            if download_image(cover_url, save_path):
                                print(f"✅")
                                worksheet_success += 1
                                total_success += 1
                            else:
                                print(f"❌")
                                worksheet_failed += 1
                                total_failed += 1
                        else:
                            print(f"      ⚠️  DRY-RUN: Ar descărca în {save_path}")
                            worksheet_success += 1
                            total_success += 1
                    else:
                        print(f"❌ Nu s-a putut extrage URL copertă")
                        worksheet_failed += 1
                        total_failed += 1
                
                except Exception as e:
                    print(f"❌ Eroare: {e}")
                    worksheet_failed += 1
                    total_failed += 1
                
                print()
                
                # Delay între request-uri
                if i < len(books):
                    delay = config.AMAZON_DELAY_BETWEEN_REQUESTS
                    print(f"      ⏳ Așteptare {delay:.1f}s între request-uri...")
                    time.sleep(delay)
                    print()
            
            # Rezumat pentru worksheet
            print(f"   📊 Rezumat {worksheet_name}:")
            print(f"      ✅ Succese: {worksheet_success}")
            print(f"      ⏭️  Sărite (există deja): {worksheet_skipped}")
            print(f"      ❌ Eșecuri: {worksheet_failed}")
            print()
        
        except Exception as e:
            print(f"   ❌ Eroare la procesarea worksheet-ului {worksheet_name}: {e}")
            print()
    
    # Rezumat final
    print("=" * 60)
    print("📊 REZUMAT FINAL")
    print("=" * 60)
    print(f"   ✅ Succese: {total_success}")
    print(f"   ⏭️  Sărite: {total_skipped}")
    print(f"   ❌ Eșecuri: {total_failed}")
    print(f"   📚 Total procesate: {total_success + total_failed + total_skipped}")
    print(f"   📋 Worksheet-uri procesate: {total_worksheets}")
    print(f"   📁 Director: {covers_path}")
    print()
    
    if dry_run:
        print("⚠️  MOD DRY-RUN: Nu s-au descărcat imagini")
    else:
        print("✅ Descărcare finalizată!")
        print(f"   Imaginile sunt salvate în: {covers_path}")
    
    print()
    return total_success > 0


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Descarcă imaginile de copertă pentru cărți')
    parser.add_argument('--worksheet', '-w', action='append', 
                       help='Worksheet-uri de procesat (poate fi folosit de mai multe ori)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Mod dry-run: nu descarcă, doar afișează')
    parser.add_argument('--all', action='store_true',
                       help='Procesează toate worksheet-urile')
    parser.add_argument('--covers-dir', type=str,
                       help='Directorul unde să salveze imaginile (default: /var/www/covers pe EC2, ./covers local)')
    
    args = parser.parse_args()
    
    worksheet_names = None
    if args.worksheet:
        worksheet_names = args.worksheet
    elif not args.all:
        # Default: doar Crime Fiction - US
        worksheet_names = ['Crime Fiction - US']
    
    print()
    if args.dry_run:
        print("⚠️  ATENȚIE: Mod DRY-RUN activat - nu se vor descărca imagini!")
    else:
        print("⚠️  ATENȚIE: Acest script va descărca imagini reale pe disk!")
        print(f"   Director: {args.covers_dir or 'default'}")
    print()
    
    if not args.dry_run:
        response = input("Continuă? (da/nu): ").strip().lower()
        if response not in ['da', 'yes', 'y', 'd']:
            print("❌ Anulat.")
            sys.exit(0)
        print()
    
    success = download_covers_for_worksheets(
        worksheet_names, 
        covers_dir=args.covers_dir,
        dry_run=args.dry_run
    )
    sys.exit(0 if success else 1)

