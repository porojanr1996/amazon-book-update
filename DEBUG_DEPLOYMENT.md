# Debug Deployment - Pași de Rezolvare

## Problema: Deployment eșuează

### Verificare 1: Environment-ul EB există?

1. **Mergi pe:** https://console.aws.amazon.com/elasticbeanstalk/
2. **Verifică:**
   - Există aplicația `books-reporting-app`?
   - Există environment-ul `books-reporting-env`?

**Dacă NU există:**
- Trebuie să-l creezi manual prima dată (vezi mai jos)

---

## Soluție: Creează Environment-ul Manual

### Pasul 1: Creează Application (dacă nu există)

1. **Mergi pe:** https://console.aws.amazon.com/elasticbeanstalk/
2. **Click "Create application"**
3. **Application name:** `books-reporting-app`
4. **Click "Create"**

### Pasul 2: Creează Environment

1. **Click "Create environment"**
2. **Environment tier:** Web server environment
3. **Platform:**
   - **Platform:** Python
   - **Platform branch:** Python 3.13 running on 64bit Amazon Linux 2023
4. **Application code:**
   - **Source:** Sample application (pentru prima dată)
5. **Click "Configure more options"**
6. **Instance type:** `t3.medium` (sau `t3.small` pentru test)
7. **Environment type:** Single instance
8. **Service role și EC2 instance profile:** (creează-le dacă nu există)
9. **Click "Create environment"**
10. **Așteaptă** ~5-10 minute

---

## Verificare 2: GitHub Actions Logs

1. **Mergi pe:** https://github.com/porojanr1996/amazon-book-update/actions
2. **Click pe workflow-ul eșuat**
3. **Click pe job-ul "deploy"**
4. **Vezi eroarea exactă**

Erori comune:
- `ERROR: Environment 'books-reporting-env' not found.`
  - **Soluție:** Creează environment-ul manual (vezi mai sus)
- `ERROR: Invalid credentials`
  - **Soluție:** Verifică AWS secrets în GitHub
- `ERROR: Permission denied`
  - **Soluție:** Verifică IAM permissions

---

## Verificare 3: Secrets în GitHub

1. **Mergi pe:** https://github.com/porojanr1996/amazon-book-update/settings/secrets/actions
2. **Verifică că există:**
   - ✅ `AWS_ACCESS_KEY_ID`
   - ✅ `AWS_SECRET_ACCESS_KEY`
   - ✅ `GOOGLE_SHEETS_SPREADSHEET_ID`
   - ✅ `REDIS_URL`
   - ✅ `REDIS_CACHE_URL`

---

## Verificare 4: IAM Permissions

1. **Mergi pe:** https://console.aws.amazon.com/iam/
2. **Users** → Click pe user-ul tău
3. **Permissions** → Verifică că ai:
   - `ElasticBeanstalkFullAccess` (sau permisiuni similare)
   - `SecretsManagerReadWrite` (pentru credentials)

---

## După ce creezi Environment-ul

1. **Trigger deployment din nou:**
   - Push un commit nou, SAU
   - GitHub Actions → Click "Run workflow"

2. **Monitorizează:**
   - GitHub Actions → Vezi progresul
   - EB Console → Vezi status-ul environment-ului

---

## Comenzi Utile (dacă ai EB CLI local)

```bash
# Verifică dacă environment-ul există
eb list

# Vezi status
eb status

# Vezi logs
eb logs
```

