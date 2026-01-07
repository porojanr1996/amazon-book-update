#!/usr/bin/env python3
"""
Debug script pentru a vedea ce returnează Playwright pentru UK
"""
import sys
from pathlib import Path
import asyncio

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.services.browser_pool import fetch_page
from app.utils.bsr_parser import parse_bsr
from bs4 import BeautifulSoup
import re

async def debug_uk_bsr(url: str):
    """Debug BSR extraction for UK URL"""
    print(f"\n🔍 Debug pentru: {url}")
    print("=" * 60)
    
    # Clean URL
    clean_url = url.split('/ref')[0].split('?')[0].rstrip('/')
    if not clean_url.endswith('/'):
        clean_url += '/'
    
    print(f"📡 Fetching cu Playwright: {clean_url}")
    html = await fetch_page(clean_url, timeout=30000, retries=1)
    
    if not html:
        print("❌ Nu s-a putut obține HTML")
        return
    
    print(f"✅ HTML obținut: {len(html)} caractere")
    
    # Verifică dacă e pagina de eroare
    if "Continue shopping" in html or "Conditions of Use" in html:
        print("⚠️  Pagină de eroare/blocare detectată")
    
    # Caută BSR în HTML
    soup = BeautifulSoup(html, 'lxml')
    
    # Caută "Best Sellers Rank" sau "BSR"
    rank_text = soup.find_all(text=re.compile(r'Best.*Seller.*Rank|BSR', re.I))
    if rank_text:
        print(f"\n✅ Găsit text cu 'Best Sellers Rank':")
        for text in rank_text[:5]:  # Primele 5
            parent = text.parent if hasattr(text, 'parent') else None
            if parent:
                print(f"   {parent.get_text()[:200]}")
    else:
        print("\n❌ Nu s-a găsit 'Best Sellers Rank' în HTML")
    
    # Caută div-ul SalesRank
    sales_rank_div = soup.find('div', {'id': 'SalesRank'})
    if sales_rank_div:
        print(f"\n✅ Găsit div#SalesRank:")
        print(f"   {sales_rank_div.get_text()[:500]}")
    else:
        print("\n❌ Nu s-a găsit div#SalesRank")
    
    # Caută orice număr cu "#" urmat de "in"
    hash_pattern = re.compile(r'#(\d{1,3}(?:,\d{3})*)\s+in', re.I)
    matches = hash_pattern.findall(html)
    if matches:
        print(f"\n✅ Găsite pattern-uri '#X in':")
        for match in matches[:10]:  # Primele 10
            print(f"   #{match}")
    else:
        print("\n❌ Nu s-au găsit pattern-uri '#X in'")
    
    # Testează parser-ul strict
    print(f"\n🧪 Testare parser strict:")
    bsr = parse_bsr(html)
    if bsr:
        print(f"   ✅ BSR extras: #{bsr:,}")
    else:
        print(f"   ❌ Parser strict nu a găsit BSR")
    
    # Salvează HTML pentru inspecție manuală
    debug_file = f"/tmp/amazon_uk_debug_{url.split('/')[-1].split('?')[0]}.html"
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n💾 HTML salvat în: {debug_file}")

async def main():
    urls = [
        "https://www.amazon.co.uk/gp/product/B0DXN9WZGG?ref",
        "https://www.amazon.co.uk/gp/product/B08KPJVQN3?ref",
    ]
    
    for url in urls:
        await debug_uk_bsr(url)
        await asyncio.sleep(2)  # Delay între request-uri

if __name__ == '__main__':
    asyncio.run(main())

