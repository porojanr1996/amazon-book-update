# Deployment pe AWS - Ghid Complet

## Opțiuni de Deployment

### Opțiunea 1: AWS Elastic Beanstalk (Recomandat - Cel mai simplu)

**Avantaje:**
- Setup rapid și simplu
- Gestionare automată a scaling, load balancing, health checks
- Integrare cu AWS services (RDS, ElastiCache)
- Deployment prin Git sau EB CLI

**Pași:**

1. **Instalare EB CLI:**
```bash
pip install awsebcli
```

2. **Inițializare proiect EB:**
```bash
cd /Users/testing/books-reporting
eb init -p python-3.13 books-reporting-app --region eu-north-1
```

3. **Creare environment:**
```bash
eb create books-reporting-env \
  --instance-type t3.medium \
  --envvars \
    GOOGLE_SHEETS_CREDENTIALS_PATH=/var/app/current/credentials.json,\
    GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id,\
    REDIS_URL=redis://your-elasticache-endpoint:6379/0,\
    REDIS_CACHE_URL=redis://your-elasticache-endpoint:6379/1,\
    FLASK_HOST=0.0.0.0,\
    FLASK_PORT=5001
```

4. **Setup ElastiCache pentru Redis:**
```bash
# În AWS Console:
# 1. ElastiCache → Create Redis cluster
# 2. Engine: Redis 7.x
# 3. Node type: cache.t3.micro (pentru test) sau cache.t3.small (pentru producție)
# 4. Security: Allow access from EB security group
```

5. **Upload credentials.json:**
```bash
# Creează .ebextensions/credentials.config
eb deploy
```

6. **Deployment:**
```bash
eb deploy
```

---

### Opțiunea 2: AWS ECS/Fargate (Pentru microservicii)

**Avantaje:**
- Scalare automată
- Gestionare containerizată
- Suport pentru Docker Compose

**Pași:**

1. **Build și push Docker image:**
```bash
# Login în ECR
aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com

# Creare repository
aws ecr create-repository --repository-name books-reporting --region eu-north-1

# Build image
docker build -t books-reporting:latest .

# Tag și push
docker tag books-reporting:latest YOUR_ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com/books-reporting:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com/books-reporting:latest
```

2. **Creare ECS Task Definition:**
```json
{
  "family": "books-reporting",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [{
    "name": "books-reporting",
    "image": "YOUR_ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com/books-reporting:latest",
    "portMappings": [{
      "containerPort": 5001,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "GOOGLE_SHEETS_SPREADSHEET_ID", "value": "your_spreadsheet_id"},
      {"name": "REDIS_URL", "value": "redis://your-elasticache:6379/0"}
    ],
    "secrets": [
      {"name": "GOOGLE_SHEETS_CREDENTIALS", "valueFrom": "arn:aws:secretsmanager:..."}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/books-reporting",
        "awslogs-region": "eu-north-1",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]
}
```

3. **Creare ECS Service cu Application Load Balancer**

---

### Opțiunea 3: EC2 cu Docker Compose (Cel mai simplu pentru început)

**Avantaje:**
- Control complet
- Setup rapid
- Costuri mici

**Pași:**

1. **Lansare EC2 Instance:**
   - AMI: Amazon Linux 2023 sau Ubuntu 22.04
   - Instance type: t3.medium (minimum pentru Playwright)
   - Security Group: Allow HTTP (80), HTTPS (443), SSH (22)

2. **Conectare și setup:**
```bash
# Conectare SSH
ssh -i your-key.pem ec2-user@your-ec2-ip

# Instalare Docker
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Instalare Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clonează proiectul
git clone your-repo-url
cd books-reporting
```

3. **Setup environment:**
```bash
# Creează .env
cat > .env << EOF
GOOGLE_SHEETS_CREDENTIALS_PATH=/app/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
EOF

# Upload credentials.json (folosește SCP sau AWS Secrets Manager)
```

4. **Start aplicația:**
```bash
docker-compose -f docker/docker-compose.yml up -d
```

5. **Setup Nginx reverse proxy (opțional):**
```bash
sudo yum install nginx -y
# Configurează Nginx pentru reverse proxy
```

---

## Configurare AWS Services

### 1. ElastiCache (Redis)

```bash
# AWS Console sau CLI
aws elasticache create-cache-cluster \
  --cache-cluster-id books-reporting-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --region eu-north-1
```

### 2. Secrets Manager (pentru credentials.json)

```bash
# Upload credentials.json ca secret
aws secretsmanager create-secret \
  --name books-reporting/google-sheets-credentials \
  --secret-string file://credentials.json \
  --region eu-north-1
```

### 3. IAM Role (pentru acces la Secrets Manager)

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

---

## Variabile de Mediu pentru AWS

Creează `.ebextensions/environment.config` (pentru Elastic Beanstalk):

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    GOOGLE_SHEETS_SPREADSHEET_ID: 'your_spreadsheet_id'
    REDIS_URL: 'redis://your-elasticache-endpoint:6379/0'
    REDIS_CACHE_URL: 'redis://your-elasticache-endpoint:6379/1'
    FLASK_HOST: '0.0.0.0'
    FLASK_PORT: '5001'
    AMAZON_DELAY_BETWEEN_REQUESTS: '8'
    AMAZON_RETRY_ATTEMPTS: '3'
```

---

## Costuri Estimat (eu-north-1)

### Opțiunea 1: Elastic Beanstalk
- EC2 t3.medium: ~$30/lună
- ElastiCache cache.t3.micro: ~$15/lună
- **Total: ~$45/lună**

### Opțiunea 2: ECS Fargate
- Fargate (1 vCPU, 2GB RAM): ~$35/lună
- ElastiCache: ~$15/lună
- **Total: ~$50/lună**

### Opțiunea 3: EC2 direct
- EC2 t3.medium: ~$30/lună
- **Total: ~$30/lună** (Redis inclus în EC2)

---

## Checklist Deployment

- [ ] AWS Account creat
- [ ] IAM User cu permisiuni (EC2, ECS, ElastiCache, Secrets Manager)
- [ ] Security Groups configurate
- [ ] ElastiCache Redis cluster creat
- [ ] credentials.json uploadat în Secrets Manager
- [ ] Environment variables configurate
- [ ] Docker image buildat și pushat (dacă folosești ECS)
- [ ] Health checks configurate
- [ ] Logging configurat (CloudWatch)
- [ ] Monitoring setup (CloudWatch Alarms)

---

## Comenzi Rapide

### Elastic Beanstalk
```bash
eb init
eb create
eb deploy
eb logs
eb status
```

### ECS
```bash
aws ecs create-cluster --cluster-name books-reporting
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster books-reporting --service-name books-reporting-service --task-definition books-reporting
```

### EC2
```bash
# SSH în EC2
ssh -i key.pem ec2-user@ip

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## Troubleshooting

### Playwright nu funcționează pe EC2
```bash
# Instalează dependențe suplimentare
sudo yum install -y \
  libnss3 \
  libatk-bridge2.0-0 \
  libdrm2 \
  libxkbcommon0 \
  libxcomposite1 \
  libxdamage1 \
  libxrandr2 \
  libgbm1 \
  libasound2
```

### Redis connection issues
- Verifică Security Groups (allow port 6379)
- Verifică că ElastiCache este în același VPC
- Verifică că endpoint-ul este corect

### Credentials.json issues
- Folosește AWS Secrets Manager în loc de file system
- Verifică IAM permissions
- Verifică că path-ul este corect

