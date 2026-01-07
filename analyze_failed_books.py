#!/usr/bin/env python3
"""
Analiză detaliată pentru cărțile care au eșuat la extragerea BSR-ului
"""
import json
from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
import config
from datetime import datetime

def analyze_failed_books():
    """Analizează cărțile care au eșuat și salvează raportul"""
    
    print("=" * 70)
    print("📊 ANALIZĂ DETALIATĂ CĂRȚI EȘUATE")
    print("=" * 70)
    print()
    
    sheets_manager = GoogleSheetsManager(
        config.GOOGLE_SHEETS_CREDENTIALS_PATH,
        config.GOOGLE_SHEETS_SPREADSHEET_ID
    )
    
    books = sheets_manager.get_all_books()
    print(f"📚 Total cărți în Google Sheets: {len(books)}")
    print()
    
    scraper = AmazonScraper(delay_between_requests=1, retry_attempts=1)
    
    successful = []
    failed = []
    
    print("🔍 Testare extragere BSR pentru toate cărțile...")
    print()
    
    for idx, book in enumerate(books, 1):
        print(f"[{idx}/{len(books)}] {book['name']}...", end=' ')
        try:
            bsr = scraper.extract_bsr(book['amazon_link'])
            if bsr:
                successful.append({
                    'name': book['name'],
                    'author': book['author'],
                    'amazon_link': book['amazon_link'],
                    'col': book['col'],
                    'bsr': bsr
                })
                print(f"✅ #{bsr:,}")
            else:
                failed.append({
                    'name': book['name'],
                    'author': book['author'],
                    'amazon_link': book['amazon_link'],
                    'col': book['col'],
                    'reason': 'BSR not found on page',
                    'possible_causes': [
                        'Amazon a blocat scraping-ul',
                        'Structura paginii s-a schimbat',
                        'Link-ul nu este complet sau corect',
                        'Produsul nu mai are BSR afișat'
                    ]
                })
                print("❌ BSR not found")
        except Exception as e:
            failed.append({
                'name': book['name'],
                'author': book['author'],
                'amazon_link': book['amazon_link'],
                'col': book['col'],
                'reason': str(e),
                'possible_causes': ['Eroare de conectare', 'Timeout', 'Amazon a blocat request-ul']
            })
            print(f"❌ Error: {str(e)[:40]}")
    
    print()
    print("=" * 70)
    print("📊 REZUMAT")
    print("=" * 70)
    print(f"✅ Succese: {len(successful)}/{len(books)} ({len(successful)/len(books)*100:.1f}%)")
    print(f"❌ Eșecuri: {len(failed)}/{len(books)} ({len(failed)/len(books)*100:.1f}%)")
    print()
    
    # Salvează raportul în JSON
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_books': len(books),
        'successful': successful,
        'failed': failed,
        'summary': {
            'success_count': len(successful),
            'failure_count': len(failed),
            'success_rate': f"{len(successful)/len(books)*100:.1f}%"
        }
    }
    
    with open('failed_books_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("💾 Raport salvat în: failed_books_report.json")
    print()
    
    if failed:
        print("=" * 70)
        print("❌ CĂRȚI CARE AU EȘUAT (Detalii)")
        print("=" * 70)
        print()
        
        for i, item in enumerate(failed, 1):
            print(f"{i}. {item['name']}")
            print(f"   Autor: {item['author']}")
            print(f"   Coloană în Sheet: {item['col']}")
            print(f"   URL: {item['amazon_link']}")
            print(f"   Motiv: {item['reason']}")
            if 'possible_causes' in item:
                print(f"   Posibile cauze:")
                for cause in item['possible_causes']:
                    print(f"     - {cause}")
            print()
        
        # Analiză link-uri
        print("=" * 70)
        print("🔍 ANALIZĂ LINK-URI")
        print("=" * 70)
        print()
        
        links_with_ref = [f for f in failed if '/ref' in f['amazon_link']]
        links_without_ref = [f for f in failed if '/ref' not in f['amazon_link']]
        
        print(f"Link-uri cu '/ref': {len(links_with_ref)}")
        print(f"Link-uri fără '/ref': {len(links_without_ref)}")
        print()
        
        if links_with_ref:
            print("⚠️  Link-uri cu '/ref' care au eșuat:")
            for item in links_with_ref[:5]:
                print(f"   - {item['name']}: {item['amazon_link']}")
            if len(links_with_ref) > 5:
                print(f"   ... și încă {len(links_with_ref) - 5}")
            print()
    
    if successful:
        print("=" * 70)
        print("✅ CĂRȚI CU SUCCES")
        print("=" * 70)
        print()
        for item in successful[:10]:
            print(f"   - {item['name']}: BSR #{item['bsr']:,}")
        if len(successful) > 10:
            print(f"   ... și încă {len(successful) - 10}")
        print()
    
    return report

if __name__ == '__main__':
    analyze_failed_books()

