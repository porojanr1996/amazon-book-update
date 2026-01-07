# Pasul 3: Setup Secrets în GitHub

## Unde să mergi:

1. **Mergi pe repository-ul tău:**
   https://github.com/porojanr1996/amazon-book-update

2. **Click pe "Settings"** (în partea de sus a repository-ului)

3. **În meniul din stânga, click pe:**
   **"Secrets and variables"** → **"Actions"**

4. **Click pe "New repository secret"**

---

## Secrets de adăugat:

### 1. AWS_ACCESS_KEY_ID
- **Name:** `AWS_ACCESS_KEY_ID`
- **Value:** Access Key ID-ul tău AWS (din AWS_SETUP_CREDENTIALS.md)
- **Click "Add secret"**

### 2. AWS_SECRET_ACCESS_KEY
- **Name:** `AWS_SECRET_ACCESS_KEY`
- **Value:** Secret Access Key-ul tău AWS
- **Click "Add secret"**

### 3. GOOGLE_SHEETS_SPREADSHEET_ID
- **Name:** `GOOGLE_SHEETS_SPREADSHEET_ID`
- **Value:** ID-ul spreadsheet-ului tău Google Sheets
- **Click "Add secret"**

### 4. REDIS_URL
- **Name:** `REDIS_URL`
- **Value:** `redis://books-reporting-redis.xxxxx.cache.amazonaws.com:6379/0`
- **⚠️ IMPORTANT:** Înlocuiește `xxxxx` cu endpoint-ul real al ElastiCache (îl vei crea în pasul următor)
- **Pentru acum:** Poți pune un placeholder, dar trebuie actualizat după ce creezi ElastiCache
- **Click "Add secret"**

### 5. REDIS_CACHE_URL
- **Name:** `REDIS_CACHE_URL`
- **Value:** `redis://books-reporting-redis.xxxxx.cache.amazonaws.com:6379/1`
- **⚠️ IMPORTANT:** Același endpoint ca REDIS_URL, dar cu DB 1
- **Pentru acum:** Poți pune un placeholder
- **Click "Add secret"**

---

## ✅ Verificare:

După ce ai adăugat toate secrets, ar trebui să vezi în listă:
- ✅ AWS_ACCESS_KEY_ID
- ✅ AWS_SECRET_ACCESS_KEY
- ✅ GOOGLE_SHEETS_SPREADSHEET_ID
- ✅ REDIS_URL
- ✅ REDIS_CACHE_URL

---

## ⚠️ Note:

- **REDIS_URL și REDIS_CACHE_URL** vor trebui actualizate după ce creezi ElastiCache în AWS
- Pentru acum, poți pune placeholder-uri, dar **trebuie actualizate înainte de deployment**
- Secrets sunt criptate și nu pot fi citite de nimeni (nici măcar tu după ce le adaugi)

---

## 📝 După ce ai terminat:

**Spune-mi când ai adăugat toate secrets** și continuăm cu setup-ul AWS Resources!

