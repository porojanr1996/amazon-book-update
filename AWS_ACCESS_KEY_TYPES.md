# Tipuri de AWS Access Keys - Explicație

## De ce "Application running outside AWS"?

Când creezi Access Keys în AWS IAM, vei vedea mai multe opțiuni. Iată diferențele:

### 1. ✅ "Application running outside AWS" (Recomandat pentru tine)

**Când să folosești:**
- ✅ Aplicația rulează pe computerul tău local (Mac, Windows, Linux)
- ✅ Aplicația rulează pe EC2/Elastic Beanstalk și folosește Access Keys
- ✅ Deployment scripts care rulează local
- ✅ CI/CD pipelines care rulează în afara AWS

**Caracteristici:**
- Generează Access Key ID și Secret Access Key
- Poți folosi cu `aws configure` sau environment variables
- Funcționează de oriunde (local, EC2, alte cloud providers)

**Exemplu pentru tine:**
```bash
# Rulezi deployment-ul de pe Mac-ul tău
./deploy_aws.sh

# Sau aplicația rulează pe EC2 și folosește access keys
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=wJalr...
```

---

### 2. "EC2 Instance" (NU pentru tine acum)

**Când să folosești:**
- Aplicația rulează pe EC2
- Folosești **IAM Roles** în loc de Access Keys (mai sigur!)
- EC2 instance-ul primește automat credentials prin metadata service

**Caracteristici:**
- Nu generează Access Keys tradiționale
- Folosește IAM Instance Profile
- Mai sigur (credentials se rotează automat)
- Funcționează DOAR pe EC2

**Exemplu:**
```python
# Pe EC2, aplicația primește automat credentials
# Nu ai nevoie de access keys în cod!
import boto3
s3 = boto3.client('s3')  # Folosește automat IAM Role
```

**De ce NU pentru tine acum:**
- Aplicația ta rulează local sau pe EB (nu direct pe EC2 cu IAM Role)
- Ai nevoie de Access Keys pentru deployment și configurare inițială

---

### 3. "Lambda function" (NU pentru tine)

**Când să folosești:**
- Doar pentru AWS Lambda functions
- Lambda primește credentials prin Execution Role

**De ce NU pentru tine:**
- Aplicația ta nu e Lambda function
- E FastAPI care rulează pe server

---

### 4. "ECS Task" (NU pentru tine acum)

**Când să folosești:**
- Containere ECS care folosesc Task Roles
- Similar cu EC2 Instance Profile, dar pentru ECS

**De ce NU pentru tine acum:**
- Poți folosi mai târziu dacă migrezi la ECS
- Acum ai nevoie de Access Keys pentru setup inițial

---

## Comparație Rapidă

| Opțiune | Unde rulează | Credentials | Siguranță | Pentru tine? |
|---------|--------------|-------------|-----------|--------------|
| **Application running outside AWS** | Local, EC2, EB, oriunde | Access Keys | ⭐⭐⭐ | ✅ DA |
| EC2 Instance | Doar EC2 | IAM Role (automat) | ⭐⭐⭐⭐⭐ | ❌ Nu acum |
| Lambda function | Doar Lambda | Execution Role | ⭐⭐⭐⭐⭐ | ❌ Nu |
| ECS Task | Doar ECS | Task Role | ⭐⭐⭐⭐⭐ | ❌ Nu acum |

---

## Best Practice - Evoluție

### Faza 1: Development/Deployment (ACUM)
```
✅ Folosește "Application running outside AWS"
✅ Access Keys pentru deployment și setup
✅ Rulează aplicația cu Access Keys
```

### Faza 2: Production pe EC2 (MAI TÂRZIU)
```
✅ Migrează la IAM Instance Profile
✅ Elimină Access Keys din cod
✅ Folosește IAM Role pentru EC2
✅ Mai sigur și mai ușor de gestionat
```

---

## Exemplu Real

### Acum (Development):
```bash
# Pe Mac-ul tău
aws configure  # Folosește Access Keys
./deploy_aws.sh  # Deployment cu Access Keys
```

### Mai târziu (Production pe EC2):
```python
# Pe EC2, aplicația folosește automat IAM Role
# Nu mai ai nevoie de Access Keys în cod!
import boto3
s3 = boto3.client('s3')  # Automat folosește IAM Role
```

---

## Rezumat

**Pentru deployment-ul tău acum:**
- ✅ Selectează **"Application running outside AWS"**
- ✅ Salvează Access Key ID și Secret Access Key
- ✅ Configurează cu `aws configure`
- ✅ Folosește pentru deployment și rulare aplicație

**Mai târziu (când aplicația rulează pe EC2):**
- Migrează la IAM Instance Profile (mai sigur)
- Elimină Access Keys din cod
- Folosește IAM Roles pentru acces la AWS services

