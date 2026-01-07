# Pasul 5: Deploy Automat cu GitHub Actions

## Cum funcționează:

1. **Push un commit pe GitHub**
2. **GitHub Actions detectează automat** (workflow-ul rulează la fiecare push pe `main`)
3. **Build și deploy** pe Elastic Beanstalk
4. **Aplicația este live!**

---

## Pasul 1: Trigger Deployment

### Opțiunea A: Push un commit nou

```bash
# Adaugă un fișier sau modifică ceva
echo "# Deployment ready" >> README.md

# Commit și push
git add .
git commit -m "Trigger deployment to AWS"
git push
```

### Opțiunea B: Trigger manual (dacă ai făcut deja push)

1. Mergi pe: https://github.com/porojanr1996/amazon-book-update/actions
2. Click pe workflow-ul "Deploy to AWS Elastic Beanstalk"
3. Click "Run workflow" → "Run workflow"

---

## Pasul 2: Monitorizează Deployment

1. **Mergi pe:** https://github.com/porojanr1996/amazon-book-update/actions
2. **Click pe workflow-ul care rulează** (cel mai recent)
3. **Vezi progresul:**
   - ✅ Checkout code
   - ✅ Setup Python
   - ✅ Install EB CLI
   - ✅ Configure AWS credentials
   - ✅ Initialize EB
   - ✅ Set environment variables
   - ✅ Deploy to Elastic Beanstalk
   - ✅ Health check

---

## Pasul 3: Verifică Elastic Beanstalk

1. **Mergi pe:** https://console.aws.amazon.com/elasticbeanstalk/
2. **Selectează environment-ul:** `books-reporting-env`
3. **Verifică:**
   - **Health:** Trebuie să fie "Ok" (verde)
   - **Status:** "Ready"
   - **URL:** Click pe URL pentru a accesa aplicația

---

## Pasul 4: Verifică Logs

Dacă deployment-ul eșuează sau aplicația nu pornește:

1. **EB Console** → **Logs** → **Request logs**
2. **Sau:** **GitHub Actions** → **View logs** pentru detalii

---

## Troubleshooting

### Deployment eșuează
- Verifică că toate secrets sunt setate corect în GitHub
- Verifică că EB environment există
- Verifică logs în GitHub Actions

### Aplicația nu pornește
- Verifică EB logs
- Verifică că credentials.json este descărcat din Secrets Manager
- Verifică environment variables în EB Console

### Redis connection issues
- Verifică Security Groups (allow port 6379)
- Verifică că ElastiCache este în același VPC cu EB
- Verifică endpoint-ul Redis în secrets

---

## ✅ Succes!

După deployment, aplicația va fi accesibilă la:
- **URL-ul EB:** `http://books-reporting-env.xxxxx.eu-north-1.elasticbeanstalk.com`
- **Sau:** URL-ul personalizat dacă ai configurat unul

---

## Workflow Viitor

De acum înainte, orice push pe `main` va deploya automat:

```bash
git add .
git commit -m "Update"
git push
```

🎉 **Deployment automat!**

