# 🚀 Quick Start - Deployment Complet pe AWS

## Obiectiv: Totul pe AWS, fără dependențe locale

---

## 📋 Checklist Pre-Deployment

### 1. Pregătire Cod
- [x] ✅ Codul este pregătit
- [x] ✅ GitHub Actions workflow creat (`.github/workflows/deploy.yml`)
- [x] ✅ EB extensions configurate (`.ebextensions/`)
- [x] ✅ `.gitignore` actualizat (exclude credentials)

### 2. Setup GitHub
- [ ] Creează repository pe GitHub
- [ ] Push codul pe GitHub
- [ ] Setup Secrets în GitHub Actions

### 3. Setup AWS
- [ ] Creează ElastiCache Redis
- [ ] Upload credentials.json în Secrets Manager
- [ ] Creează Elastic Beanstalk Environment
- [ ] Configurează IAM Role pentru Secrets Manager

---

## 🎯 Pași Rapizi

### Pasul 1: Setup GitHub Repository

```bash
# Rulează scriptul de setup
./setup_aws_deployment.sh
```

SAU manual:

```bash
# Inițializează Git
git init
git branch -M main

# Adaugă remote (înlocuiește cu URL-ul tău)
git remote add origin https://github.com/YOUR_USERNAME/books-reporting.git

# Commit și push
git add .
git commit -m "Initial commit - Ready for AWS"
git push -u origin main
```

### Pasul 2: Setup GitHub Secrets

1. Mergi în repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Adaugă:

| Secret Name | Value |
|------------|-------|
| `AWS_ACCESS_KEY_ID` | Access Key ID-ul tău AWS |
| `AWS_SECRET_ACCESS_KEY` | Secret Access Key-ul tău AWS |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | ID-ul spreadsheet-ului |
| `REDIS_URL` | `redis://books-reporting-redis.xxxxx.cache.amazonaws.com:6379/0` |
| `REDIS_CACHE_URL` | `redis://books-reporting-redis.xxxxx.cache.amazonaws.com:6379/1` |

### Pasul 3: Setup AWS Resources

#### A. ElastiCache Redis

```bash
# Via AWS Console:
# 1. ElastiCache → Create Redis cluster
# 2. Name: books-reporting-redis
# 3. Engine: Redis 7.x
# 4. Node type: cache.t3.micro
# 5. Security group: Allow port 6379 from EB security group
# 6. Notează endpoint-ul
```

#### B. Secrets Manager

```bash
# Upload credentials.json
aws secretsmanager create-secret \
  --name books-reporting/google-sheets-credentials \
  --secret-string file://credentials.json \
  --region eu-north-1

# Upload Spreadsheet ID
aws secretsmanager create-secret \
  --name books-reporting/spreadsheet-id \
  --secret-string "YOUR_SPREADSHEET_ID" \
  --region eu-north-1
```

#### C. Elastic Beanstalk

```bash
# Via AWS Console:
# 1. Elastic Beanstalk → Create application
# 2. Application name: books-reporting-app
# 3. Platform: Python 3.13
# 4. Environment name: books-reporting-env
# 5. Instance type: t3.medium
# 6. Create environment
```

#### D. IAM Role pentru EB

1. IAM → Roles → `aws-elasticbeanstalk-ec2-role`
2. Attach policy: `SecretsManagerReadWrite`
3. Sau creează policy custom pentru `books-reporting/*`

### Pasul 4: Deploy!

```bash
# Push un commit pentru a trigger deployment
git add .
git commit -m "Deploy to AWS"
git push
```

GitHub Actions va deploya automat!

---

## ✅ Verificare

### 1. Verifică GitHub Actions
- Repository → **Actions** tab
- Vezi workflow-ul care rulează
- Verifică logs pentru erori

### 2. Verifică Elastic Beanstalk
- AWS Console → Elastic Beanstalk → `books-reporting-env`
- Verifică Health status (trebuie să fie "Ok")
- Click pe URL pentru a accesa aplicația

### 3. Verifică Logs
- EB Console → Logs → Request logs
- Verifică că aplicația pornește corect
- Verifică că credentials.json este descărcat

---

## 🔄 Workflow Viitor

1. **Modifică codul** (local sau pe GitHub)
2. **Commit și push:**
   ```bash
   git add .
   git commit -m "Update"
   git push
   ```
3. **GitHub Actions deployează automat**
4. **Aplicația este live pe AWS!**

**Nu mai ai nevoie de Mac pentru deployment!** 🎉

---

## 🆘 Troubleshooting

### Deployment eșuează
- Verifică GitHub Actions logs
- Verifică că toate secrets sunt setate
- Verifică că EB environment există

### Aplicația nu pornește
- Verifică EB logs
- Verifică că credentials.json este descărcat
- Verifică environment variables

### Redis connection issues
- Verifică Security Groups
- Verifică că ElastiCache este în același VPC
- Verifică endpoint-ul Redis

---

## 📚 Documentație Completă

- **AWS_FULL_DEPLOYMENT.md** - Ghid complet cu toate opțiunile
- **GITHUB_ACTIONS_SETUP.md** - Setup detaliat GitHub Actions
- **AWS_SETUP_CREDENTIALS.md** - Cum să obții AWS Access Keys

---

## 💰 Costuri Estimative

- **Elastic Beanstalk (t3.medium):** ~$30/lună
- **ElastiCache (cache.t3.micro):** ~$15/lună
- **GitHub Actions:** Gratis (2000 minute/lună)
- **Total: ~$45/lună**

---

## 🎉 Gata!

După setup, totul rulează pe AWS:
- ✅ Aplicația pe Elastic Beanstalk
- ✅ Redis pe ElastiCache
- ✅ Deployment automat cu GitHub Actions
- ✅ Nu mai ai nevoie de Mac!

