# 🚀 Instrucțiuni Pornire - Simplu și Rapid

## Comandă Principală

**Rulează în consolă:**

```bash
cd /Users/testing/books-reporting
source venv/bin/activate
./START_SIMPLE.sh
```

Sau:

```bash
cd /Users/testing/books-reporting
source venv/bin/activate
./scripts/start_all_services.sh
```

---

## Ce Se Întâmplă

1. ✅ Verifică Redis (pornește dacă nu rulează)
2. ✅ Oprește serviciile vechi (dacă există)
3. ✅ Pornește Sheets Service (port 8001)
4. ✅ Pornește Scraper Service (port 8002)
5. ✅ Pornește API Service (port 5001)
6. ✅ Pornește Worker Service (Celery)

---

## Verificare Rapidă

După ce rulezi scriptul, verifică:

```bash
# Health checks
curl http://localhost:8001/health  # Sheets
curl http://localhost:8002/health  # Scraper
curl http://localhost:5001/health  # API

# Dashboard
open http://localhost:5001/
```

Sau deschide în browser: **http://localhost:5001/**

---

## Oprire Servicii

```bash
# Oprește toate serviciile
lsof -ti:8001,8002,5001 | xargs kill
pkill -f "celery.*celery_app"
```

---

## Logs

```bash
# Vezi logs live
tail -f logs/api-service.log
tail -f logs/sheets-service.log
tail -f logs/scraper-service.log
tail -f logs/worker-service.log
```

---

## Troubleshooting

### Eroare "Internal Server Error"
- Verifică logs: `tail -f logs/api-service.log`
- Verifică că toate serviciile rulează: `lsof -ti:8001,8002,5001`

### Service nu pornește
- Verifică că venv este activat: `source venv/bin/activate`
- Verifică că Redis rulează: `redis-cli ping`
- Verifică logs pentru erori

### Port deja folosit
- Oprește serviciile vechi: `lsof -ti:8001,8002,5001 | xargs kill`
- Sau schimbă porturile în `shared/config/__init__.py`

---

## ✅ Gata!

După ce rulezi scriptul, toate serviciile vor rula și poți accesa dashboard-ul la:

**http://localhost:5001/**

