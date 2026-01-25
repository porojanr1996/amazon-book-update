# 🔒 Fix Security Group - Permite Acces la Port 5001

## Problema
Aplicația rulează și răspunde local, dar nu este accesibilă din exterior. Security Group-ul blochează traficul.

## Soluție: Adaugă Regulă în Security Group

### Opțiunea 1: AWS Console (Recomandat)

1. **Deschide AWS Console:**
   - Mergi la EC2 → Instances
   - Selectează instanța ta

2. **Accesează Security Group:**
   - Click pe tab-ul "Security"
   - Click pe Security Group ID (ex: sg-xxxxxxxxx)

3. **Adaugă Inbound Rule:**
   - Click pe "Edit inbound rules"
   - Click "Add rule"
   - Configurează:
     - **Type:** Custom TCP
     - **Port range:** 5001
     - **Source:** 0.0.0.0/0 (sau IP-ul tău specific pentru securitate)
     - **Description:** Books Reporting API
   - Click "Save rules"

4. **Verifică:**
   - Ar trebui să vezi regula nouă în listă
   - Testează: `curl http://51.20.76.150:5001/api/scheduler-status`

### Opțiunea 2: AWS CLI

```bash
# Pe EC2 sau local (cu AWS CLI configurat)

# 1. Obține ID-ul instanței
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)

# 2. Obține Security Group ID
SG_ID=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region eu-north-1 \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text)

echo "Security Group ID: $SG_ID"

# 3. Adaugă regula pentru port 5001
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5001 \
  --cidr 0.0.0.0/0 \
  --region eu-north-1 \
  --description "Books Reporting API"

# 4. Verifică regulile
aws ec2 describe-security-groups \
  --group-ids $SG_ID \
  --region eu-north-1 \
  --query 'SecurityGroups[0].IpPermissions[?FromPort==`5001`]'
```

### Opțiunea 3: Script Automat

```bash
#!/bin/bash
# Pe EC2

INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
SG_ID=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region eu-north-1 \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text)

echo "Adding rule for port 5001 to Security Group: $SG_ID"

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5001 \
  --cidr 0.0.0.0/0 \
  --region eu-north-1 \
  --description "Books Reporting API" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Rule added successfully!"
else
    echo "⚠️  Rule might already exist (that's OK)"
fi

echo ""
echo "Testing connection..."
sleep 2
curl -s http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5001/api/scheduler-status | head -c 100
```

## Verificare

După ce adaugi regula, testează:

```bash
# De pe calculatorul tău local
curl http://51.20.76.150:5001/api/scheduler-status

# Ar trebui să vezi:
# {"running":true,"next_run":"2026-01-26 10:00:00+02:00",...}
```

## Securitate

Pentru securitate mai bună, în loc de `0.0.0.0/0`, poți folosi:
- **IP-ul tău specific:** `YOUR_IP/32`
- **Range de IP-uri:** `YOUR_NETWORK/24`

Exemplu:
```bash
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5001 \
  --cidr YOUR_IP/32 \
  --region eu-north-1 \
  --description "Books Reporting API - My IP only"
```

## Note

- Dacă regula există deja, vei primi eroare "already exists" - asta e OK
- Schimbările în Security Group sunt aplicate imediat
- Nu este nevoie să repornești instanța

