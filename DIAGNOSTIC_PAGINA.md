# 🔍 Diagnostic Pagină Nu Se Încarcă

## Verificări Pas cu Pas

### 1. Verifică dacă aplicația rulează pe EC2

```bash
# Conectează-te la EC2
ssh -i /path/to/your-key.pem ec2-user@51.20.76.150

# Verifică serviciul systemd
sudo systemctl status books-reporting

# Verifică procesele
ps aux | grep -E "(uvicorn|python.*main|fastapi)"

# Verifică dacă portul 5001 este în uz
sudo netstat -tlnp | grep 5001
# SAU
sudo ss -tlnp | grep 5001
```

### 2. Verifică logurile pentru erori

```bash
# Loguri systemd
sudo journalctl -u books-reporting -n 50 --no-pager

# Loguri în timp real
sudo journalctl -u books-reporting -f
```

### 3. Verifică dacă aplicația răspunde local

```bash
# Pe EC2, testează local
curl http://localhost:5001
curl http://localhost:5001/api/scheduler-status
curl http://127.0.0.1:5001
```

### 4. Verifică Security Group în AWS

```bash
# Obține ID-ul instanței
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)

# Obține Security Group ID
SG_ID=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region eu-north-1 \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text)

# Verifică regulile Security Group
aws ec2 describe-security-groups \
  --group-ids $SG_ID \
  --region eu-north-1 \
  --query 'SecurityGroups[0].IpPermissions'
```

**Sau în AWS Console:**
1. EC2 → Instances → Selectează instanța
2. Security → Security Groups → Click pe Security Group
3. Inbound Rules → Verifică dacă există regula pentru port 5001

### 5. Verifică firewall local (dacă există)

```bash
# Verifică firewall
sudo firewall-cmd --list-all
# SAU
sudo iptables -L -n
```

### 6. Testează conectivitatea din exterior

```bash
# De pe calculatorul tău local
curl -v http://51.20.76.150:5001
curl -v http://51.20.76.150:5001/api/scheduler-status

# Verifică dacă portul este deschis
telnet 51.20.76.150 5001
# SAU
nc -zv 51.20.76.150 5001
```

### 7. Verifică configurația aplicației

```bash
# Pe EC2
cd /home/ec2-user/app/books-reporting

# Verifică config.py
grep -E "(FLASK_HOST|FLASK_PORT)" config.py

# Verifică .env (dacă există)
cat .env | grep -E "(HOST|PORT)"

# Verifică systemd service
cat /etc/systemd/system/books-reporting.service
```

### 8. Repornește serviciul (dacă este necesar)

```bash
# Oprește
sudo systemctl stop books-reporting

# Așteaptă 3 secunde
sleep 3

# Pornește
sudo systemctl start books-reporting

# Verifică statusul
sudo systemctl status books-reporting

# Verifică logurile
sudo journalctl -u books-reporting -n 30 --no-pager
```

## Probleme Comune

### Problema 1: Security Group nu permite traficul
**Soluție:** Adaugă regula în Security Group:
- Type: Custom TCP
- Port: 5001
- Source: 0.0.0.0/0 (sau IP-ul tău specific)

### Problema 2: Aplicația nu rulează
**Soluție:** 
```bash
sudo systemctl restart books-reporting
sudo systemctl enable books-reporting  # Pentru auto-start
```

### Problema 3: Portul este blocat de firewall
**Soluție:**
```bash
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

### Problema 4: Aplicația rulează pe alt port
**Soluție:** Verifică configurația și actualizează Security Group

## Test Rapid

Rulează acest script pe EC2:

```bash
#!/bin/bash
echo "=== Diagnostic Rapid ==="
echo ""
echo "1. Serviciul systemd:"
sudo systemctl is-active books-reporting
echo ""
echo "2. Procese Python:"
ps aux | grep -E "(uvicorn|python.*main)" | grep -v grep
echo ""
echo "3. Port 5001:"
sudo ss -tlnp | grep 5001
echo ""
echo "4. Test local:"
curl -s http://localhost:5001/api/scheduler-status | head -c 200
echo ""
echo "5. Ultimele erori:"
sudo journalctl -u books-reporting -n 10 --no-pager | grep -i error
```

