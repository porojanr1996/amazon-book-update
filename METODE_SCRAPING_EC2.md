# 🚀 Metode Eficiente de Scraping pe EC2 AWS

## 📊 Metode Disponibile

### 1. **Playwright Headless (ACTUAL - RECOMANDAT) ✅**

**Status:** Deja implementat și optimizat pentru EC2

**Caracteristici:**
- ✅ Browser real (Chromium) - nu poate fi detectat ușor
- ✅ Session persistence - păstrează cookies între request-uri
- ✅ Human-like behavior - mouse movements, scrolling
- ✅ CAPTCHA detection - oprește automat dacă detectează
- ✅ Exponential backoff - retry inteligent pentru erori
- ✅ Stealth optimizations - headers realiste, viewport, timezone

**Performanță:**
- Timp per request: ~45-120 secunde (cu delay-uri)
- Succes rate: ~95%+ (dacă nu e blocat)
- Resurse: ~100-200 MB RAM per browser

**Optimizări actuale:**
```python
# Browser pool cu session persistence
- Single browser (pool size = 1)
- Storage state salvat în /tmp/playwright_storage/
- Delay random: 45-120s (configurabil)
- Exponential backoff: 1m → 3m → 10m
```

**Cum funcționează pe EC2:**
```bash
# Detectează automat EC2
is_ec2 = os.path.exists('/sys/hypervisor/uuid')
# Folosește Playwright direct pentru UK și US pe EC2
```

---

### 2. **Requests + BeautifulSoup (ALTERNATIVĂ - NU RECOMANDAT PE EC2)**

**Status:** Disponibil dar nu funcționează bine pe EC2

**Probleme pe EC2:**
- ❌ Amazon blochează IP-urile EC2 pentru requests simple
- ❌ Rate limit foarte agresiv
- ❌ CAPTCHA imediat
- ❌ Succes rate: ~10-20%

**Când funcționează:**
- Doar local (IP-uri rezidențiale)
- Cu proxy-uri rotative (costuri mari)
- Pentru testare rapidă (nu producție)

---

### 3. **Selenium (ALTERNATIVĂ - DEPRECATED)**

**Status:** Nu mai este folosit (înlocuit cu Playwright)

**De ce nu:**
- ❌ Mai lent decât Playwright
- ❌ Mai multe resurse
- ❌ Mai greu de configurat pe EC2
- ❌ Mai ușor de detectat

---

## 🎯 Recomandare: Playwright Headless (Actual)

**De ce este cea mai bună metodă pentru EC2:**

1. **Funcționează pe EC2** - Amazon nu poate detecta ușor browser-ul real
2. **Session persistence** - păstrează cookies, reduce CAPTCHA
3. **Human-like** - comportament natural, mai puține blocări
4. **Optimizat** - delay-uri inteligente, retry logic
5. **Production-ready** - deja implementat și testat

---

## ⚡ Optimizări Disponibile

### A. Proxy Rotation (Dacă e necesar)

```python
# În config.py
AMAZON_USE_PROXY = True
AMAZON_PROXY = "http://user:pass@proxy-server:port"
```

**Avantaje:**
- Reduce blocările
- Permite scraping mai agresiv

**Dezavantaje:**
- Costuri (proxy-uri costă $10-50/lună)
- Complexitate suplimentară

### B. Delay-uri Configurabile

```bash
# În .env sau config.py
AMAZON_DELAY_MIN=45  # Minimum delay între request-uri
AMAZON_DELAY_MAX=120 # Maximum delay
```

**Optimizare:**
- Delay-uri mai mici = mai rapid, dar mai multe blocări
- Delay-uri mai mari = mai lent, dar mai puține blocări

### C. Browser Pool Size

```python
# Actual: pool_size = 1 (single browser)
# Poate fi mărit la 2-3 pentru paralelism
AMAZON_BROWSER_POOL_SIZE=2
```

**Notă:** Nu recomand paralelism pentru Amazon - blochează mai agresiv

### D. Session Persistence (DEJA IMPLEMENTAT)

```python
# Storage state salvat automat în:
/tmp/playwright_storage/amazon_session.json
```

**Beneficii:**
- Păstrează cookies între sesiuni
- Reduce CAPTCHA
- Mai rapid (nu trebuie să se logheze de fiecare dată)

---

## 📈 Comparație Performanță

| Metodă | Viteză | Succes Rate | Resurse | Cost |
|--------|--------|-------------|---------|------|
| **Playwright Headless** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Requests + BS | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Selenium | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Playwright + Proxy | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

---

## 🛠️ Configurare Optimă pentru EC2

### Configurație Actuală (Recomandat)

```python
# config.py
AMAZON_DELAY_BETWEEN_REQUESTS = 45  # Base delay
AMAZON_DELAY_MIN = 45
AMAZON_DELAY_MAX = 120
AMAZON_RETRY_ATTEMPTS = 1  # Nu retry agresiv
AMAZON_MAX_WORKERS = 1  # Single worker (nu paralel)
AMAZON_BROWSER_POOL_SIZE = 1  # Single browser
AMAZON_PLAYWRIGHT_DELAY = 45  # Delay înainte de Playwright
```

### Pentru Viteză Maximă (Risc de Blocare)

```python
AMAZON_DELAY_MIN = 30
AMAZON_DELAY_MAX = 60
AMAZON_MAX_WORKERS = 2  # Paralelism (risc!)
```

### Pentru Siguranță Maximă (Mai Lent)

```python
AMAZON_DELAY_MIN = 60
AMAZON_DELAY_MAX = 180
AMAZON_MAX_WORKERS = 1
```

---

## 🚀 Cum Rulează Actual pe EC2

### Fluxul Complet:

1. **Detectare EC2:**
   ```python
   is_ec2 = os.path.exists('/sys/hypervisor/uuid')
   ```

2. **Selectare Metodă:**
   - UK domains → Playwright direct
   - US domains pe EC2 → Playwright direct
   - US domains local → Poate încerca requests (dar default Playwright)

3. **Browser Pool:**
   - Single browser cu session persistence
   - Delay random: 45-120s
   - Human-like behavior

4. **Extract BSR:**
   - Parse HTML cu `bsr_parser.py`
   - Fallback la screenshot OCR dacă nu găsește în HTML

5. **Update Google Sheets:**
   - Batch updates pentru performanță
   - Cache pentru reducere request-uri

---

## 💡 Recomandări Finale

### ✅ Folosește Metoda Actuală (Playwright Headless)

**De ce:**
- Deja optimizată pentru EC2
- Funcționează bine (95%+ succes rate)
- Production-ready
- Session persistence
- CAPTCHA detection

### ⚠️ Dacă Ai Probleme cu Blocări:

1. **Mărește delay-urile:**
   ```bash
   AMAZON_DELAY_MIN=60
   AMAZON_DELAY_MAX=180
   ```

2. **Folosește Proxy:**
   ```bash
   AMAZON_USE_PROXY=true
   AMAZON_PROXY=http://proxy-server:port
   ```

3. **Verifică Session Persistence:**
   ```bash
   ls -la /tmp/playwright_storage/
   # Ar trebui să vezi amazon_session.json
   ```

### 🎯 Pentru Performanță Maximă:

- Păstrează configurația actuală
- Rulează o dată pe zi (10:00 AM)
- Monitorizează logurile pentru CAPTCHA
- Folosește Celery pentru background processing

---

## 📊 Concluzie

**Metoda cea mai eficientă pentru EC2:** **Playwright Headless** (actual)

**De ce:**
- ✅ Funcționează pe EC2
- ✅ Succes rate ridicat
- ✅ Optimizat pentru producție
- ✅ Session persistence
- ✅ CAPTCHA detection
- ✅ Human-like behavior

**Nu schimba nimic** - metoda actuală este cea mai bună pentru EC2! 🎉

