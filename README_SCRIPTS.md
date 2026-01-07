# 📜 Scripturi pentru Actualizare Date

## 🖼️ `populate_cover_images.py` - Actualizare Imagini Cover

Populează cache-ul cu imagini cover pentru toate cărțile.

**Utilizare:**
```bash
# Populează imagini pentru toate worksheet-urile
python populate_cover_images.py

# Va dura ~2-3 minute (delay între request-uri)
```

**Ce face:**
- Extrage imagini cover de pe Amazon
- Salvează în cache (Redis)
- Skip cărțile care au deja imagini în cache

---

## 🔄 `update_bsr.py` - Actualizare BSR

Actualizează BSR-ul pentru cărți și scrie în Google Sheets.

**Utilizare:**
```bash
# Dry-run (nu scrie, doar afișează)
python update_bsr.py --dry-run

# Actualizare pentru un worksheet specific
python update_bsr.py --worksheet "Crime Fiction - US"

# Actualizare pentru mai multe worksheet-uri
python update_bsr.py -w "Crime Fiction - US" -w "Crime Fiction - UK"

# Actualizare pentru toate worksheet-urile
python update_bsr.py --all
```

**Opțiuni:**
- `--worksheet, -w`: Specifică worksheet-uri (poate fi folosit de mai multe ori)
- `--dry-run`: Mod test - nu scrie în Google Sheets
- `--all`: Procesează toate worksheet-urile

**Ce face:**
- Extrage BSR de pe Amazon pentru fiecare carte
- Scrie BSR-ul în Google Sheets (coloana cărții, rândul zilei curente)
- Calculează și actualizează media BSR pentru ziua curentă
- Respectă delay-ul între request-uri pentru a evita rate limiting

**Exemplu:**
```bash
# Test pentru un worksheet (dry-run)
python update_bsr.py --dry-run -w "Crime Fiction - US"

# Actualizare reală pentru un worksheet
python update_bsr.py -w "Crime Fiction - US"
```

---

## 📝 Note

- Ambele scripturi respectă `AMAZON_DELAY_BETWEEN_REQUESTS` din `config.py`
- Ambele scripturi pot fi rulate independent
- `update_bsr.py` cere confirmare înainte de a scrie date (dacă nu e --dry-run)
- `populate_cover_images.py` nu scrie în Google Sheets, doar în cache
