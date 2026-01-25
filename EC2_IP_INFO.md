# 🌐 EC2 IP Information

## IP Public Actual

**IP Public:** `51.20.76.150`

## Acces Aplicație

Aplicația este accesibilă la:
- **URL:** `http://51.20.76.150:5001`
- **Sau:** `http://51.20.76.150:5001/books-reporting` (dacă este configurat subpath)

## SSH Connection

```bash
ssh -i /path/to/your-key.pem ec2-user@51.20.76.150
```

## Verificare Status

### 1. Verifică dacă aplicația rulează
```bash
curl http://51.20.76.150:5001/api/scheduler-status
```

### 2. Verifică serviciile
```bash
# Pe EC2
sudo systemctl status books-reporting
ps aux | grep celery
redis-cli ping
```

## Configurare Security Group

Asigură-te că Security Group-ul permite:
- **Port 22** (SSH) - pentru acces
- **Port 5001** (HTTP) - pentru aplicație
- **Port 6379** (Redis) - doar din interior (nu trebuie să fie public)

## Note

- IP-ul public poate să se schimbe dacă instanța este oprită și repornită (dacă nu folosești Elastic IP)
- Pentru IP static, folosește **Elastic IP** în AWS
- Aplicația folosește `localhost` pentru servicii interne (Redis, Celery), deci nu este necesar să actualizezi configurația internă

## Elastic IP (Recomandat)

Pentru a avea un IP static:

1. **Alocă Elastic IP:**
```bash
aws ec2 allocate-address --region eu-north-1
```

2. **Asociază cu instanța:**
```bash
aws ec2 associate-address \
  --instance-id i-xxxxxxxxxxxxx \
  --allocation-id eipalloc-xxxxxxxxxxxxx \
  --region eu-north-1
```

3. **Verifică:**
```bash
aws ec2 describe-addresses --region eu-north-1
```

