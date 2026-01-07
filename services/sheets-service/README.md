# Sheets Service

Microserviciu pentru operațiuni Google Sheets.

## Responsabilități

- Citire/scriere date din Google Sheets
- Gestionare worksheets
- Batch updates optimizate
- Metadata caching

## Endpoints

- `GET /health` - Health check
- `GET /api/worksheets` - Lista tuturor worksheets
- `GET /api/books?worksheet=...` - Lista cărților dintr-un worksheet
- `GET /api/bsr-history?worksheet=...` - Istoric BSR pentru toate cărțile
- `GET /api/avg-history?worksheet=...` - Istoric medii BSR
- `POST /api/update-bsr` - Actualizare BSR pentru o carte
- `POST /api/calculate-average` - Calculare și actualizare medie BSR

## Rulare

```bash
cd services/sheets-service
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Logging

Logs în `logs/sheets-service.log` cu format JSON structurat.

## Dependențe

- Google Sheets API
- Redis (pentru caching)

