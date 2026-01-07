# Pasul 4: Setup AWS Resources

## A. ElastiCache Redis

### Via AWS Console:

1. **Mergi pe:** https://console.aws.amazon.com/elasticache/
2. **Selectează regiunea:** `eu-north-1` (Stockholm) - sau alta dacă preferi
3. **Click "Create"** sau **"Redis cluster"**
4. **Completează:**
   - **Cluster name:** `books-reporting-redis`
   - **Engine:** Redis
   - **Engine version:** 7.x (sau cea mai recentă)
   - **Node type:** `cache.t3.micro` (cel mai mic, ~$15/lună)
   - **Number of nodes:** 1
   - **Subnet group:** Create new (sau folosește default)
   - **Security groups:** Create new security group
     - Name: `books-reporting-redis-sg`
     - Inbound rules: Allow port 6379 from your EB security group (sau 0.0.0.0/0 temporar pentru test)
   - **Backup:** Opțional (poți dezactiva pentru a economisi)
5. **Click "Create"**
6. **Așteaptă** ~5-10 minute pentru creare
7. **Notează endpoint-ul:**
   - Mergi în cluster → Click pe cluster-ul creat
   - Copiază **Primary endpoint** (ex: `books-reporting-redis.xxxxx.cache.amazonaws.com:6379`)

### Via AWS CLI (alternativ):

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id books-reporting-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --region eu-north-1
```

---

## B. Secrets Manager (Upload credentials.json)

### Via AWS Console:

1. **Mergi pe:** https://console.aws.amazon.com/secretsmanager/
2. **Selectează regiunea:** `eu-north-1` (sau aceeași ca ElastiCache)
3. **Click "Store a new secret"**
4. **Selectează:**
   - **Secret type:** "Other type of secret"
   - **Key/value pairs:** Click "Plaintext" tab
5. **Upload credentials.json:**
   - Deschide `credentials.json` de pe computer
   - Copiază tot conținutul JSON
   - Paste în câmpul "Plaintext"
6. **Click "Next"**
7. **Secret name:** `books-reporting/google-sheets-credentials`
8. **Click "Next"**
9. **Rotation:** Skip (nu e necesar)
10. **Click "Store"**

### Upload Spreadsheet ID (opțional, dar recomandat):

1. **Click "Store a new secret"** din nou
2. **Secret type:** "Other type of secret" → "Plaintext"
3. **Value:** `1-y5ly84oAV1GkhpLlD3MfvLZSi-5UThypHXsmch6RiA` (sau ID-ul tău)
4. **Secret name:** `books-reporting/spreadsheet-id`
5. **Click "Store"**

### Via AWS CLI (alternativ):

```bash
# Upload credentials.json
aws secretsmanager create-secret \
  --name books-reporting/google-sheets-credentials \
  --secret-string file://credentials.json \
  --region eu-north-1

# Upload Spreadsheet ID
aws secretsmanager create-secret \
  --name books-reporting/spreadsheet-id \
  --secret-string "1-y5ly84oAV1GkhpLlD3MfvLZSi-5UThypHXsmch6RiA" \
  --region eu-north-1
```

---

## C. Elastic Beanstalk Environment

### Via AWS Console:

1. **Mergi pe:** https://console.aws.amazon.com/elasticbeanstalk/
2. **Selectează regiunea:** `eu-north-1` (sau aceeași ca celelalte)
3. **Click "Create application"**
4. **Completează:**
   - **Application name:** `books-reporting-app`
   - **Description:** (opțional) "Books Reporting Application"
5. **Click "Create"**
6. **Click "Create environment"**
7. **Selectează:**
   - **Environment tier:** Web server environment
   - **Platform:** Python
   - **Platform branch:** Python 3.13 running on 64bit Amazon Linux 2023
   - **Platform version:** (lasă default, cea mai recentă)
8. **Application code:**
   - **Source:** Sample application (pentru prima dată)
   - Sau upload code manual (dar GitHub Actions va face deploy automat)
9. **Click "Configure more options"**
10. **Instance type:** `t3.medium` (sau `t3.small` pentru test)
11. **Capacity:**
    - **Environment type:** Single instance (pentru început)
    - Sau Load balanced (dacă vrei high availability)
12. **Security:**
    - **EC2 key pair:** (opțional, pentru SSH)
    - **IAM instance profile:** `aws-elasticbeanstalk-ec2-role` (default)
13. **Click "Create environment"**
14. **Așteaptă** ~5-10 minute pentru creare
15. **Notează URL-ul:** Va fi ceva de genul `books-reporting-env.xxxxx.eu-north-1.elasticbeanstalk.com`

---

## D. Configurează IAM Role pentru Secrets Manager

Elastic Beanstalk instance-ul trebuie să poată citi din Secrets Manager:

1. **Mergi pe:** https://console.aws.amazon.com/iam/
2. **Roles** → Caută `aws-elasticbeanstalk-ec2-role`
3. **Click pe role**
4. **Click "Add permissions"** → **"Attach policies"**
5. **Caută:** `SecretsManagerReadWrite`
6. **Bifează** și click **"Add permissions"**

SAU creează policy custom (mai restrictiv):

1. **IAM** → **Policies** → **Create policy**
2. **JSON tab:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ],
    "Resource": "arn:aws:secretsmanager:eu-north-1:*:secret:books-reporting/*"
  }]
}
```
3. **Name:** `BooksReportingSecretsRead`
4. **Click "Create policy"**
5. **Attach la** `aws-elasticbeanstalk-ec2-role`

---

## E. Actualizează GitHub Secrets cu Redis URL

După ce ai creat ElastiCache:

1. **Mergi pe:** https://github.com/porojanr1996/amazon-book-update/settings/secrets/actions
2. **Click pe** `REDIS_URL`
3. **Update value cu endpoint-ul real:**
   - Ex: `redis://books-reporting-redis.xxxxx.cache.amazonaws.com:6379/0`
4. **Click "Update secret"**
5. **La fel pentru** `REDIS_CACHE_URL:`
   - Ex: `redis://books-reporting-redis.xxxxx.cache.amazonaws.com:6379/1`

---

## ✅ Verificare Finală

După ce ai terminat, ar trebui să ai:

- ✅ ElastiCache Redis cluster creat
- ✅ Secrets Manager cu credentials.json
- ✅ Elastic Beanstalk environment creat
- ✅ IAM Role configurat pentru Secrets Manager
- ✅ GitHub Secrets actualizate cu Redis URL real

---

## 📝 Note Importante

- **Regiunea:** Folosește aceeași regiune pentru toate resursele (recomand `eu-north-1`)
- **Security Groups:** Asigură-te că ElastiCache permite conexiuni de la EB
- **Costuri:** ~$45/lună total (EB t3.medium + ElastiCache t3.micro)
- **Timp:** ~15-20 minute pentru crearea tuturor resurselor

---

## 🚀 Următorul Pas

După ce ai terminat, continuăm cu **Pasul 5: Deploy automat cu GitHub Actions!**

