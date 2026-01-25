# Deployment Manual prin EB Console

## Pași pentru Deployment prin AWS Console

### Pasul 1: Pregătește Codul

1. **Creează un ZIP file** cu codul aplicației:
   ```bash
   # Exclude fișierele care nu trebuie în deployment
   zip -r deployment.zip . \
     -x "*.git*" \
     -x "*venv*" \
     -x "*__pycache__*" \
     -x "*.pyc" \
     -x "*.log" \
     -x "*.env" \
     -x "*credentials.json" \
     -x "*test_*" \
     -x "*debug_*" \
     -x "*.md" \
     -x "*backup_*"
   ```

### Pasul 2: Upload și Deploy prin EB Console

1. **Mergi pe:** https://console.aws.amazon.com/elasticbeanstalk/
2. **Selectează environment-ul:** `Books-amazon-env-env` (sau `Books-reporting-app-env`)
3. **Click pe butonul portocaliu "Upload and deploy"**
4. **Completează:**
   - **Version label:** `app-$(date +%Y%m%d-%H%M%S)` (ex: `app-20260107-120000`)
   - **Description:** (opțional) "Deployment manual"
   - **Source:** Click "Choose file" și selectează `deployment.zip`
5. **Click "Deploy"**
6. **Așteaptă** ~5-10 minute pentru deployment

### Pasul 3: Verificare

1. **Monitorizează Events** în EB Console
2. **Verifică Health** - ar trebui să fie "Ok" (verde)
3. **Click pe URL-ul environment-ului** pentru a accesa aplicația

---

## Script Rapid pentru Creare ZIP

Creează un script `create_deployment.sh`:

```bash
#!/bin/bash
# Creează ZIP pentru deployment EB

echo "📦 Creating deployment package..."

# Exclude fișierele care nu trebuie
zip -r deployment.zip . \
  -x "*.git*" \
  -x "*venv*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*.log" \
  -x "*.env" \
  -x "*credentials.json" \
  -x "*test_*" \
  -x "*debug_*" \
  -x "*.md" \
  -x "*backup_*" \
  -x "*BundleLogs*" \
  -x "*.zip"

echo "✅ deployment.zip created!"
echo "📤 Upload this file in EB Console → Upload and deploy"
```

---

## Notă Importantă

- **credentials.json** NU trebuie inclus în ZIP (se descarcă din Secrets Manager)
- **.env** NU trebuie inclus (se folosesc environment variables din EB)
- **venv/** NU trebuie inclus (EB instalează dependențele automat)

---

## După Deployment

1. **Verifică logs-urile** în EB Console → Logs
2. **Testează aplicația** pe URL-ul environment-ului
3. **Verifică Health** - ar trebui să fie "Ok"

