# Fluxul Actual de Scraping Amazon BSR

## Overview

Sistemul folosește **Playwright refactorizat** (production-ready) pentru scraping, cu următoarele caracteristici:

## Fluxul Complet

### 1. Entry Point: `update_bsr.py`
```python
scraper.extract_bsr(amazon_url, use_playwright=True)
```

### 2. `amazon_scraper.py` - Logică de routing
- **UK domains**: Folosește direct Playwright (Amazon UK blochează requests simple)
- **US domains pe EC2**: Folosește direct Playwright (Amazon US blochează IP-uri EC2)
- **US domains local**: Ar putea încerca requests simple, dar default e Playwright

### 3. `playwright_scraper_refactored.py` - Wrapper Playwright
```python
extract_bsr_with_playwright_sync(amazon_url)
  ↓
extract_bsr_with_playwright(amazon_url)  # async
  ↓
fetch_page(url)  # din browser_pool_refactored
  ↓
parse_bsr(html)  # din bsr_parser.py
```

### 4. `browser_pool_refactored.py` - Browser Pool (Single Browser)

**Caracteristici:**
- ✅ **Single browser** (pool size = 1, fără paralel)
- ✅ **Persistent session** (storage_state salvat în `/tmp/playwright_storage/amazon_session.json`)
- ✅ **Delay random**: 45-120 secunde (sau din env: `AMAZON_DELAY_MIN`/`AMAZON_DELAY_MAX`)
- ✅ **Exponential backoff**: 1 min → 3 min → 10 min pentru 500/503
- ✅ **Stealth optimizations**: User-agent real, viewport, timezone, locale, headers realiste

**Flux de navigare:**
1. **Delay**: Așteaptă 45-120s (random)
2. **Navigate**: `page.goto(url, wait_until='networkidle')`
3. **Handle 500/503**: Exponential backoff (1m → 3m → 10m)
4. **Detect "Continue shopping"**: 
   - Detectează pagina intermediară
   - Face click automat pe butonul "Continue shopping"
   - Așteaptă redirect
5. **Human-like behavior**:
   - Mouse movements
   - Scrolling gradual
   - Waits random (2-4s)
6. **Get HTML**: `page.content()`
7. **Detect CAPTCHA**: Dacă detectează CAPTCHA → **ABORT IMEDIAT** (nu retry)
8. **Save session**: Salvează storage_state pentru următoarea sesiune

### 5. `bsr_parser.py` - Extragere BSR din HTML

**Metode de extragere (în ordine de prioritate):**

1. **SalesRank div** (prioritate 1):
   - Caută `<div id="SalesRank">`
   - Pattern: `Best Sellers Rank: #10,839 in Kindle Store (See Top 100...)`
   - Extrage: `10,839` → `10839`

2. **Page text** (prioritate 2):
   - Caută în tot textul paginii
   - Pattern: `Best Sellers Rank: #(\d{1,3}(?:,\d{3})*) in Kindle Store`
   - Acceptă și cu "(See Top 100 in Kindle Store)" suffix

3. **Specific elements** (prioritate 3):
   - Caută în elemente cu ID-uri care conțin "rank" sau "bsr"

**Pattern principal:**
```regex
Best\s+Sellers\s+Rank:\s*#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store(?:\s*\(See\s+Top.*?\))?
```

## Gestionarea Erorilor

### CAPTCHA Detection
- **Detectare**: Pattern-uri regex pentru "captcha", "verify you are human", etc.
- **Acțiune**: **ABORT IMEDIAT** - returnează `(None, "captcha")`
- **Nu retry**: Nu mai încearcă alte metode
- **Metrics**: Înregistrează în `scraper_metrics`

### "Continue shopping" Interstitial
- **Detectare**: Text "Continue shopping" sau "Click the button below"
- **Acțiune**: Click automat pe buton
- **Dacă rămâne pe interstitial**: Marchează ca blocat

### Network Errors (500/503)
- **Acțiune**: Exponential backoff (1m → 3m → 10m)
- **Retry**: Da, până la 3 încercări

### Timeout
- **Acțiune**: Retry cu backoff
- **Dacă tot timeout**: Returnează `(None, "timeout")`

## Metrics Tracking

Sistemul trackează:
- `success_rate`: % extrageri reușite
- `captcha_rate`: % CAPTCHA detectate
- `retry_rate`: % request-uri retry
- `avg_scrape_time`: Timp mediu per request
- `network_error_rate`: % erori de rețea

## Configurare

### Environment Variables
```bash
# Delay-uri (secunde)
AMAZON_DELAY_MIN=45      # Min delay între request-uri
AMAZON_DELAY_MAX=120     # Max delay între request-uri

# Browser mode
PLAYWRIGHT_HEADLESS=true  # false pentru test local (headed)

# Proxy (opțional)
AMAZON_USE_PROXY=false
AMAZON_PROXY=http://user:pass@proxy:port
```

### Config Defaults
- Delay: 45-120s (production)
- Browser pool: 1 (single browser)
- Headless: true (production)
- Skip on CAPTCHA: true

## Exemplu de Flow Complet

```
1. update_bsr.py → extract_bsr(url, use_playwright=True)
2. amazon_scraper.py → detectează US pe EC2 → use_playwright=True
3. playwright_scraper_refactored.py → extract_bsr_with_playwright_sync()
4. browser_pool_refactored.py → fetch_page():
   - Așteaptă 45-120s
   - Navighează la URL
   - Detectează "Continue shopping" → click
   - Așteaptă redirect
   - Scroll, mouse movements
   - Extrage HTML
   - Detectează CAPTCHA → ABORT (dacă există)
5. bsr_parser.py → parse_bsr(html):
   - Caută în SalesRank div
   - Caută în page text
   - Extrage BSR: #10,839 → 10839
6. Returnează BSR sau None (dacă CAPTCHA/eroare)
```

## Diferențe față de Versiunea Veche

| Aspect | Versiunea Veche | Versiunea Refactorizată |
|--------|----------------|------------------------|
| Browser pool | 2-3 browsers (paralel) | 1 browser (secvențial) |
| Delay | 25-75s | 45-120s |
| CAPTCHA | Retry cu alte metode | ABORT imediat |
| "Continue shopping" | Nu era tratat | Click automat |
| Retry logic | Retry toate erorile | Doar network errors |
| Metrics | Nu există | Tracking complet |
| Session persistence | Nu | Da (storage_state) |

