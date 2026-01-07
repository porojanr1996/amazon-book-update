# Setup GitHub Actions pentru Deployment Automat

## Pași Compleți

### 1. Creează Repository pe GitHub

1. Mergi pe https://github.com/new
2. Nume: `books-reporting`
3. Public sau Private (după preferință)
4. Click "Create repository"

### 2. Push Codul pe GitHub

```bash
cd /Users/testing/books-reporting

# Inițializare Git (dacă nu există)
git init

# Adaugă toate fișierele
git add .

# Commit
git commit -m "Initial commit - Ready for AWS deployment"

# Adaugă remote
git remote add origin https://github.com/YOUR_USERNAME/books-reporting.git

# Push
git branch -M main
git push -u origin main
```

### 3. Setup Secrets în GitHub

1. Mergi în repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Adaugă următoarele secrets:

   **a. AWS_ACCESS_KEY_ID**
   - Name: `AWS_ACCESS_KEY_ID`
   - Value: Access Key ID-ul tău AWS

   **b. AWS_SECRET_ACCESS_KEY**
   - Name: `AWS_SECRET_ACCESS_KEY`
   - Value: Secret Access Key-ul tău AWS

   **c. GOOGLE_SHEETS_SPREADSHEET_ID**
   - Name: `GOOGLE_SHEETS_SPREADSHEET_ID`
   - Value: ID-ul spreadsheet-ului tău Google Sheets

   **d. REDIS_URL**
   - Name: `REDIS_URL`
   - Value: `redis://books-reporting-redis.xxxxx.cache.amazonaws.com:6379/0`
   - (Înlocuiește cu endpoint-ul real al ElastiCache)

   **e. REDIS_CACHE_URL**
   - Name: `REDIS_CACHE_URL`
   - Value: `redis://books-reporting-redis.xxxxx.cache.amazonaws.com:6379/1`

### 4. Setup AWS Resources (Prima Dată)

#### A. ElastiCache Redis

```bash
# Via AWS Console:
# 1. ElastiCache → Create Redis cluster
# 2. Name: books-reporting-redis
# 3. Engine: Redis 7.x
# 4. Node type: cache.t3.micro
# 5. Number of nodes: 1
# 6. Security: Create new security group
# 7. Notează endpoint-ul: books-reporting-redis.xxxxx.cache.amazonaws.com:6379
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

#### C. Elastic Beanstalk (Prima Dată)

```bash
# Via AWS Console:
# 1. Elastic Beanstalk → Create application
# 2. Application name: books-reporting-app
# 3. Platform: Python
# 4. Platform branch: Python 3.13 running on 64bit Amazon Linux 2023
# 5. Application code: Sample application (pentru prima dată)
# 6. Environment name: books-reporting-env
# 7. Domain: books-reporting (sau lasă gol)
# 8. Instance type: t3.medium
# 9. Create environment
```

### 5. Configurare IAM Role pentru EB

EB instance-ul trebuie să poată accesa Secrets Manager:

1. IAM → Roles
2. Găsește role-ul: `aws-elasticbeanstalk-ec2-role`
3. Adaugă policy: `SecretsManagerReadWrite`
4. Sau creează policy custom:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "secretsmanager:GetSecretValue"
    ],
    "Resource": "arn:aws:secretsmanager:eu-north-1:*:secret:books-reporting/*"
  }]
}
```

### 6. Test Deployment

```bash
# Push un commit pentru a trigger deployment
git add .
git commit -m "Test deployment"
git push
```

Verifică în GitHub:
- Actions tab → Vezi workflow-ul care rulează
- Logs → Vezi progresul deployment-ului

### 7. Verificare Aplicație

După deployment:
```bash
# Obține URL-ul aplicației
eb status

# Sau în AWS Console:
# Elastic Beanstalk → books-reporting-env → URL
```

---

## Workflow Complet

1. **Tu faci modificări** (local sau direct pe GitHub)
2. **Push pe GitHub:**
   ```bash
   git add .
   git commit -m "Update"
   git push
   ```
3. **GitHub Actions rulează automat:**
   - Checkout code
   - Setup Python și EB CLI
   - Configure AWS credentials
   - Deploy pe Elastic Beanstalk
4. **Aplicația este live pe AWS!**

---

## Troubleshooting

### Deployment eșuează
- Verifică logs în GitHub Actions
- Verifică că toate secrets sunt setate corect
- Verifică că EB environment există

### Aplicația nu pornește
- Verifică logs în EB Console → Logs
- Verifică că credentials.json este descărcat corect
- Verifică environment variables

### Redis connection issues
- Verifică Security Groups (allow port 6379)
- Verifică că ElastiCache este în același VPC cu EB
- Verifică endpoint-ul Redis

---

## Comenzi Utile

```bash
# Vezi status deployment
eb status

# Vezi logs
eb logs

# SSH în instance (dacă e nevoie)
eb ssh

# Open în browser
eb open
```

