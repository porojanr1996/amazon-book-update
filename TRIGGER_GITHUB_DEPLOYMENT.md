# Cum să Rulezi Deployment-ul din GitHub Actions

## Workflow-ul rulează în GitHub Actions, nu în EB Console

GitHub Actions este serviciul care rulează workflow-ul și deployează automat pe EB.

---

## Opțiunea 1: Trigger Automat (Push pe GitHub)

Workflow-ul rulează automat când faci push pe branch-ul `main`:

```bash
# Fă o modificare (sau un commit gol)
git commit --allow-empty -m "Trigger deployment"
git push origin main
```

Workflow-ul va rula automat și va deploya pe EB.

---

## Opțiunea 2: Trigger Manual din GitHub

1. **Mergi pe:** https://github.com/porojanr1996/amazon-book-update/actions
2. **Click pe workflow-ul "Deploy to AWS Elastic Beanstalk"** (în stânga)
3. **Click pe butonul "Run workflow"** (în dreapta sus)
4. **Selectează branch:** `main`
5. **Click "Run workflow"**
6. **Monitorizează** progresul în Actions tab

---

## Opțiunea 3: Verifică Status în EB Console

După ce workflow-ul rulează în GitHub Actions:

1. **Mergi pe:** https://console.aws.amazon.com/elasticbeanstalk/
2. **Selectează environment-ul:** `Books-reporting-app-env` (sau `Books-amazon-env-env`)
3. **Monitorizează:**
   - **Events** tab - vezi deployment-ul în progres
   - **Health** - verifică status-ul
   - **Logs** - vezi logs-urile dacă apare o eroare

---

## Verificare Workflow în GitHub Actions

1. **Mergi pe:** https://github.com/porojanr1996/amazon-book-update/actions
2. **Click pe workflow-ul care rulează** (cel mai recent)
3. **Click pe job-ul "deploy"**
4. **Vezi logs-urile** în timp real:
   - Checkout code
   - Setup Python
   - Install EB CLI
   - Configure AWS credentials
   - Initialize EB
   - Set environment variables
   - Wait for Ready state
   - Deploy to Elastic Beanstalk
   - Health check

---

## Troubleshooting

### Workflow-ul nu rulează automat
- Verifică că ai făcut push pe branch-ul `main`
- Verifică că workflow-ul este în `.github/workflows/deploy.yml`

### Deployment eșuează
- Verifică logs-urile în GitHub Actions
- Verifică logs-urile în EB Console → Logs
- Verifică că environment-ul este "Ready" înainte de deployment

### Environment nu este Ready
- Așteaptă ca environment-ul să devină "Ready" în EB Console
- Sau face rebuild environment-ul

---

## Rezumat

1. **Workflow-ul rulează în GitHub Actions** (nu în EB Console)
2. **Trigger automat:** Push pe `main`
3. **Trigger manual:** GitHub → Actions → Run workflow
4. **Monitorizează:** GitHub Actions logs + EB Console Events

---

## Link-uri Utile

- **GitHub Actions:** https://github.com/porojanr1996/amazon-book-update/actions
- **EB Console:** https://console.aws.amazon.com/elasticbeanstalk/
- **Workflow file:** `.github/workflows/deploy.yml`

