# Soluție fără SSH - Repornire Servicii

## Problema
EC2 Instance Connect nu funcționează. Trebuie să repornim serviciile fără SSH.

## Soluții

### Opțiunea 1: AWS Systems Manager Session Manager

1. **Instalează Session Manager Plugin local:**
   ```bash
   # macOS
   brew install --cask session-manager-plugin
   ```

2. **Verifică dacă instance-ul are SSM Agent:**
   - EC2 → Instances → books-reporting-app
   - Tab "Connect" → "Session Manager"
   - Dacă apare butonul "Connect", click pe el

3. **Dacă nu apare, instalează SSM Agent pe EC2:**
   - Trebuie să rulezi user-data script care instalează SSM Agent
   - SAU folosește un AMI care are SSM Agent pre-installat

### Opțiunea 2: Adaugă SSH în Security Group temporar

1. **EC2 → Security Groups → launch-wizard-1**
2. **Edit Inbound Rules → Add Rule**
3. **Type:** SSH (22)
4. **Source:** My IP (sau un IP specific)
5. **Save rules**
6. **Conectează-te prin SSH:**
   ```bash
   ssh -i /tmp/ec2_key.pem ec2-user@16.171.115.88
   ```
7. **După ce termini, șterge regula SSH**

### Opțiunea 3: Rulează aplicația standalone (fără microservicii)

Aplicația poate funcționa fără sheets-service și scraper-service dacă:
- Folosește direct `GoogleSheetsManager` (deja face asta)
- Folosește direct `AmazonScraper` (deja face asta)

**Problema actuală:** sheets-service și scraper-service au crash-at, dar API-ul funcționează standalone.

### Opțiunea 4: Restart EC2 Instance

1. **EC2 → Instances → books-reporting-app**
2. **Instance State → Reboot**
3. **Așteaptă 2-3 minute**
4. **Testează:** `http://16.171.115.88:5001/health`

**ATENȚIE:** Dacă user-data script-ul nu a rulat corect prima dată, reboot-ul nu va rezolva problema.

### Opțiunea 5: Creează un nou EC2 Instance

Dacă nimic nu funcționează, cel mai simplu e să creezi un nou instance cu:
- User data script corect
- Security Group care permite SSH de la IP-ul tău
- IAM Role pentru Secrets Manager

## Recomandare

**Încearcă Opțiunea 2 (SSH temporar)** - e cea mai rapidă:
1. Adaugă SSH în Security Group (My IP)
2. Conectează-te și repornește serviciile
3. Șterge regula SSH după

