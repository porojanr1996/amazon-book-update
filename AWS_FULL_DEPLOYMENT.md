# Deployment Complet pe AWS - Fără Dependențe Local

## Arhitectură Completă pe AWS

```
GitHub/CodeCommit
    ↓ (push code)
GitHub Actions / CodePipeline
    ↓ (deploy automat)
Elastic Beanstalk / EC2
    ↓ (aplicație)
ElastiCache (Redis)
    ↓
Google Sheets API
```

## Opțiunea 1: Elastic Beanstalk cu GitHub Actions (Recomandat)

### Setup Complet

#### 1. Pregătire Cod pe GitHub

```bash
# 1. Creează repository pe GitHub
# 2. Push codul
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/books-reporting.git
git push -u origin main
```

#### 2. Setup GitHub Actions pentru Deployment Automat

Creează `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS Elastic Beanstalk

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        pip install awsebcli
    
    - name: Deploy to EB
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        AWS_DEFAULT_REGION: eu-north-1
      run: |
        eb init -p python-3.13 books-reporting-app --region eu-north-1
        eb deploy books-reporting-env
```

#### 3. Setup Secrets în GitHub

1. GitHub Repository → Settings → Secrets and variables → Actions
2. Adaugă:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `GOOGLE_SHEETS_SPREADSHEET_ID`
   - `GOOGLE_SHEETS_CREDENTIALS` (JSON content)

#### 4. Setup AWS Resources

**A. Elastic Beanstalk Environment:**
```bash
# Prima dată, creează manual în AWS Console sau:
aws elasticbeanstalk create-application \
  --application-name books-reporting-app \
  --region eu-north-1

aws elasticbeanstalk create-environment \
  --application-name books-reporting-app \
  --environment-name books-reporting-env \
  --solution-stack-name "64bit Amazon Linux 2023 v4.0.0 running Python 3.13" \
  --option-settings \
    Namespace=aws:autoscaling:launchconfiguration,OptionName=InstanceType,Value=t3.medium \
    Namespace=aws:elasticbeanstalk:application:environment,OptionName=GOOGLE_SHEETS_SPREADSHEET_ID,Value=YOUR_ID \
    Namespace=aws:elasticbeanstalk:application:environment,OptionName=REDIS_URL,Value=redis://YOUR_ENDPOINT:6379/0
```

**B. ElastiCache Redis:**
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id books-reporting-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --region eu-north-1
```

**C. Secrets Manager pentru credentials.json:**
```bash
# Upload credentials.json
aws secretsmanager create-secret \
  --name books-reporting/google-sheets-credentials \
  --secret-string file://credentials.json \
  --region eu-north-1
```

#### 5. Configurare EB pentru a citi credentials din Secrets Manager

Creează `.ebextensions/01_secrets.config`:

```yaml
files:
  "/opt/elasticbeanstalk/tasks/taillogs.d/credentials.sh":
    mode: "000755"
    owner: root
    group: root
    content: |
      #!/bin/bash
      # Download credentials from Secrets Manager
      aws secretsmanager get-secret-value \
        --secret-id books-reporting/google-sheets-credentials \
        --region eu-north-1 \
        --query SecretString \
        --output text > /var/app/current/credentials.json
      chmod 400 /var/app/current/credentials.json
      chown webapp:webapp /var/app/current/credentials.json

container_commands:
  01_download_credentials:
    command: |
      aws secretsmanager get-secret-value \
        --secret-id books-reporting/google-sheets-credentials \
        --region eu-north-1 \
        --query SecretString \
        --output text > /var/app/current/credentials.json
      chmod 400 /var/app/current/credentials.json
```

---

## Opțiunea 2: EC2 cu Docker + GitHub Actions

### Setup Complet

#### 1. Lansează EC2 Instance

```bash
# Via AWS Console sau CLI
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxx \
  --user-data file://ec2-setup.sh \
  --region eu-north-1
```

#### 2. Script de Setup EC2 (`ec2-setup.sh`):

```bash
#!/bin/bash
# User data script pentru EC2

# Update system
yum update -y

# Install Docker
yum install docker -y
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Git
yum install git -y

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Clone repository
cd /home/ec2-user
git clone https://github.com/YOUR_USERNAME/books-reporting.git
cd books-reporting

# Download credentials from Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id books-reporting/google-sheets-credentials \
  --region eu-north-1 \
  --query SecretString \
  --output text > credentials.json
chmod 400 credentials.json

# Create .env
cat > .env << EOF
GOOGLE_SHEETS_CREDENTIALS_PATH=/app/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=\$(aws secretsmanager get-secret-value --secret-id books-reporting/spreadsheet-id --region eu-north-1 --query SecretString --output text)
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
EOF

# Start services
docker-compose -f docker/docker-compose.yml up -d
```

#### 3. GitHub Actions pentru Deployment pe EC2

```yaml
name: Deploy to EC2

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to EC2
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.EC2_HOST }}
        username: ec2-user
        key: ${{ secrets.EC2_SSH_KEY }}
        script: |
          cd /home/ec2-user/books-reporting
          git pull origin main
          docker-compose -f docker/docker-compose.yml down
          docker-compose -f docker/docker-compose.yml build
          docker-compose -f docker/docker-compose.yml up -d
```

---

## Opțiunea 3: ECS Fargate cu CodePipeline (Complet Automat)

### Setup Complet

#### 1. ECR Repository

```bash
aws ecr create-repository --repository-name books-reporting --region eu-north-1
```

#### 2. CodePipeline pentru CI/CD

1. AWS Console → CodePipeline → Create pipeline
2. Source: GitHub (conectează repository-ul)
3. Build: AWS CodeBuild (build Docker image)
4. Deploy: ECS (deploy pe Fargate)

#### 3. CodeBuild Buildspec

Creează `buildspec.yml`:

```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/books-reporting
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $REPOSITORY_URI:latest .
      - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker images...
      - docker push $REPOSITORY_URI:latest
      - docker push $REPOSITORY_URI:$IMAGE_TAG
      - echo Writing image definitions file...
      - printf '[{"name":"books-reporting","imageUri":"%s"}]' $REPOSITORY_URI:latest > imagedefinitions.json
artifacts:
  files: imagedefinitions.json
```

---

## Configurare Completă - Pași Detaliați

### Pasul 1: Pregătire Cod

```bash
# Pe Mac (ultima dată)
cd /Users/testing/books-reporting
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/books-reporting.git
git push -u origin main
```

### Pasul 2: Setup AWS Resources

**A. ElastiCache Redis:**
```bash
# Via AWS Console:
# 1. ElastiCache → Create Redis cluster
# 2. Name: books-reporting-redis
# 3. Node type: cache.t3.micro
# 4. Security: Create new security group, allow port 6379
# 5. Notează endpoint-ul: books-reporting-redis.xxxxx.cache.amazonaws.com:6379
```

**B. Secrets Manager:**
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

**C. Elastic Beanstalk:**
```bash
# Via AWS Console:
# 1. Elastic Beanstalk → Create application
# 2. Name: books-reporting-app
# 3. Platform: Python 3.13
# 4. Upload code: Upload your code (prima dată)
# 5. Instance type: t3.medium
```

### Pasul 3: Setup GitHub Actions

Creează `.github/workflows/deploy.yml` în repository.

### Pasul 4: Configurare Environment Variables

În Elastic Beanstalk Console:
- Configuration → Software → Environment properties
- Adaugă:
  - `GOOGLE_SHEETS_SPREADSHEET_ID`
  - `REDIS_URL`
  - `REDIS_CACHE_URL`
  - etc.

---

## Workflow Final

1. **Tu faci modificări local** (opțional, poate fi doar pe GitHub)
2. **Push pe GitHub:**
   ```bash
   git add .
   git commit -m "Update"
   git push
   ```
3. **GitHub Actions rulează automat:**
   - Build aplicația
   - Deploy pe AWS
   - Aplicația rulează pe AWS
4. **Aplicația este live pe AWS** - nu mai ai nevoie de Mac!

---

## Costuri

- **Elastic Beanstalk (t3.medium):** ~$30/lună
- **ElastiCache (cache.t3.micro):** ~$15/lună
- **GitHub Actions:** Gratis (2000 minute/lună)
- **Total: ~$45/lună**

---

## Beneficii

✅ **Nu mai ai nevoie de Mac** - totul rulează pe AWS
✅ **Deployment automat** - push pe GitHub = deploy automat
✅ **Scalare automată** - AWS gestionează resursele
✅ **Backup automat** - AWS face snapshot-uri
✅ **Monitoring** - CloudWatch pentru logs și metrics

