# Scheduler pentru Actualizare Zilnică BSR

## Descriere

Aplicația include un scheduler automat care actualizează ratingurile BSR (Best Seller Rank) pentru toate cărțile în fiecare zi la **10:01 AM ora Bucureștiului**.

## Configurare

Scheduler-ul este configurat automat când aplicația pornește și folosește:
- **Timezone**: Europe/Bucharest (UTC+2/UTC+3 cu DST)
- **Ora**: 10:01 AM
- **Frecvență**: Zilnic

## Funcționare

1. **La pornirea aplicației**: Scheduler-ul se inițializează automat
2. **La 10:01 AM**: Funcția `run_daily_bsr_update()` este apelată automat
3. **Procesare**: 
   - Se citesc toate cărțile din Google Sheets
   - Pentru fiecare carte, se extrage BSR-ul de pe Amazon
   - Valorile sunt scrise în Google Sheets în rândul zilei curente

## Endpoints API

### Verificare Status Scheduler
```bash
GET /api/scheduler-status
```

Răspuns exemplu:
```json
{
  "scheduler_running": true,
  "jobs": [
    {
      "id": "daily_bsr_update",
      "name": "Daily BSR Update at 10:01 AM Bucharest time",
      "next_run_time": "2024-01-15T10:01:00+02:00",
      "trigger": "cron[hour='10', minute='1']"
    }
  ]
}
```

### Trigger Manual (pentru testare)
```bash
POST /api/update-bsr
```

Acest endpoint permite rularea manuală a actualizării BSR pentru testare.

## Logging

Toate acțiunile scheduler-ului sunt loggate:
- Pornirea scheduler-ului
- Fiecare rulare zilnică
- Succese și eșecuri pentru fiecare carte
- Rezumat final

## Depanare

### Scheduler-ul nu pornește
- Verifică logurile pentru erori
- Asigură-te că aplicația rulează continuu (nu doar o dată)
- Verifică că APScheduler este instalat: `pip install APScheduler==3.10.4`

### Actualizarea nu rulează la ora corectă
- Verifică timezone-ul sistemului
- Verifică că timezone-ul este setat corect în cod (`Europe/Bucharest`)
- Verifică statusul scheduler-ului: `GET /api/scheduler-status`

### Erori la actualizare
- Verifică conexiunea la Google Sheets
- Verifică că credentialele sunt corecte
- Verifică că linkurile Amazon sunt valide
- Verifică logurile pentru detalii despre erori

## Notă Importantă

Pentru ca scheduler-ul să funcționeze continuu, aplicația Flask trebuie să ruleze permanent. În producție, folosește:
- **systemd** (Linux)
- **supervisor** (cross-platform)
- **Docker** cu restart policy
- **Cloud services** (Heroku, AWS, etc.)

## Modificare Ora

Pentru a schimba ora de rulare, modifică în `app.py`:
```python
scheduler.add_job(
    func=run_daily_bsr_update,
    trigger=CronTrigger(hour=10, minute=1, timezone=pytz.timezone('Europe/Bucharest')),
    ...
)
```

Schimbă `hour=10` și `minute=1` cu valorile dorite.

