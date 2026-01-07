# Cum să obții AWS Access Keys

## Pași pentru a obține AWS Access Key ID și Secret Access Key

### 1. Creează un AWS Account (dacă nu ai deja)

1. Mergi la https://aws.amazon.com/
2. Click pe "Create an AWS Account"
3. Completează formularul și verifică email-ul
4. Adaugă o metodă de plată (necesară pentru cont nou)

### 2. Creează un IAM User

**IMPORTANT:** Nu folosi niciodată root account credentials pentru aplicații! Creează întotdeauna un IAM user.

#### Pasul 1: Deschide IAM Console
1. Loghează-te în AWS Console: https://console.aws.amazon.com/
2. Caută "IAM" în search bar
3. Click pe "IAM" (Identity and Access Management)

#### Pasul 2: Creează User Nou
1. În meniul din stânga, click pe **"Users"**
2. Click pe butonul **"Create user"**
3. **User name:** `books-reporting-deploy` (sau orice nume vrei)
4. Click **"Next"**

#### Pasul 3: Setează Permisiuni
1. Selectează **"Attach policies directly"**
2. Caută și selectează următoarele policies:
   - `AWSElasticBeanstalkFullAccess` (pentru EB deployment)
   - `AmazonElastiCacheFullAccess` (pentru Redis)
   - `AmazonEC2FullAccess` (pentru EC2 dacă folosești)
   - `AmazonECS_FullAccess` (pentru ECS dacă folosești)
   - `SecretsManagerReadWrite` (pentru credentials.json)
   - `CloudWatchLogsFullAccess` (pentru logging)

   **SAU** pentru simplitate (doar pentru test):
   - `PowerUserAccess` (acordă acces la majoritatea serviciilor AWS, fără IAM)

3. Click **"Next"**
4. Click **"Create user"**

#### Pasul 4: Creează Access Keys
1. Click pe user-ul nou creat (`books-reporting-deploy`)
2. Click pe tab-ul **"Security credentials"**
3. Scroll down la secțiunea **"Access keys"**
4. Click pe **"Create access key"**
5. Selectează **"Application running outside AWS"** (sau "Local code")
   
   **De ce această opțiune?**
   - ✅ Aplicația ta rulează pe computerul tău local (Mac) sau pe EC2/EB
   - ✅ Nu rulează în Lambda, ECS Task, sau EC2 Instance Profile
   - ✅ Ai nevoie de Access Keys pentru a autentifica din exteriorul AWS
   - ❌ "EC2" - pentru aplicații care rulează direct pe EC2 și folosesc IAM Roles (mai sigur, dar nu e cazul tău acum)
   - ❌ "Lambda" - doar pentru funcții Lambda
   - ❌ "ECS Task" - doar pentru containere ECS cu Task Roles
   
6. Click **"Next"**
7. (Opțional) Adaugă o descriere: "Books Reporting Deployment"
8. Click **"Create access key"**

#### Pasul 5: Salvează Credentials
**⚠️ IMPORTANT: Salvează aceste valori ACUM! Nu vei putea vedea Secret Access Key din nou!**

1. **Access Key ID:** `AKIA...` (copiază această valoare)
2. **Secret Access Key:** `wJalr...` (copiază această valoare)

**Salvează-le într-un loc sigur!**

### 3. Configurează AWS CLI

```bash
# Instalează AWS CLI (dacă nu e instalat)
pip install awscli

# Configurează credentials
aws configure

# Va întreba:
# AWS Access Key ID [None]: PASTE_ACCESS_KEY_ID_HERE
# AWS Secret Access Key [None]: PASTE_SECRET_ACCESS_KEY_HERE
# Default region name [None]: eu-north-1
# Default output format [None]: json
```

### 4. Verifică Configurarea

```bash
# Testează conexiunea
aws sts get-caller-identity

# Ar trebui să returneze:
# {
#     "UserId": "...",
#     "Account": "...",
#     "Arn": "arn:aws:iam::ACCOUNT_ID:user/books-reporting-deploy"
# }
```

## Alternative: AWS CLI cu Profile

Dacă ai mai multe AWS accounts, poți folosi profiles:

```bash
# Configurează un profile specific
aws configure --profile books-reporting

# Folosește profile-ul
aws --profile books-reporting sts get-caller-identity
```

## Securitate - Best Practices

1. ✅ **Folosește IAM users**, nu root account
2. ✅ **Principiul least privilege** - dă doar permisiunile necesare
3. ✅ **Rotează access keys** periodic (la 90 de zile)
4. ✅ **Nu partaja access keys** în cod sau Git
5. ✅ **Folosește IAM roles** pentru EC2/ECS (mai sigur decât access keys)
6. ✅ **Activează MFA** pentru root account

## Troubleshooting

### "Access Denied" erori
- Verifică că policies-urile sunt atașate corect
- Verifică că access keys sunt corecte
- Verifică că region-ul este corect

### "Invalid credentials"
- Verifică că ai copiat corect Access Key ID și Secret
- Verifică că nu ai spații înainte/după
- Regenerează access keys dacă e necesar

## Unde găsesc Access Keys în AWS Console?

1. AWS Console → IAM → Users
2. Click pe user-ul tău
3. Tab "Security credentials"
4. Secțiunea "Access keys"
5. Click "Create access key" pentru a crea unul nou

## Ștergere Access Keys

Dacă ai pierdut sau compromis access keys:
1. IAM → Users → [your-user] → Security credentials
2. Găsește access key-ul compromis
3. Click "Delete"
4. Creează unul nou

