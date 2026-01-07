#!/bin/bash
# Script pentru deployment pe AWS

set -e

echo "🚀 AWS Deployment Script pentru Books Reporting"
echo "============================================================"

# Verifică dacă AWS CLI este instalat
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI nu este instalat!"
    echo "   Instalează cu: pip install awscli"
    exit 1
fi

# Verifică dacă AWS credentials sunt configurate
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials nu sunt configurate!"
    echo ""
    echo "   Configurează cu:"
    echo "   aws configure"
    echo ""
    echo "   Vei avea nevoie de:"
    echo "   - AWS Access Key ID (din IAM Console)"
    echo "   - AWS Secret Access Key (din IAM Console)"
    echo "   - Default region: eu-north-1"
    echo ""
    echo "   Vezi AWS_SETUP_CREDENTIALS.md pentru detalii"
    exit 1
fi

echo "✅ AWS credentials configurate"
echo "   Account: $(aws sts get-caller-identity --query Account --output text)"
echo "   User: $(aws sts get-caller-identity --query Arn --output text)"
echo ""

# Verifică dacă EB CLI este instalat
if ! command -v eb &> /dev/null; then
    echo "❌ Elastic Beanstalk CLI nu este instalat!"
    echo "   Instalează cu: pip install awsebcli"
    exit 1
fi

# Verifică credentials.json
if [ ! -f "credentials.json" ]; then
    echo "❌ credentials.json nu există!"
    echo "   Creează credentials.json înainte de deployment"
    exit 1
fi

echo ""
echo "📋 Pași de deployment:"
echo "1. Inițializare Elastic Beanstalk (dacă nu există)"
echo "2. Creare ElastiCache Redis cluster"
echo "3. Upload credentials.json în Secrets Manager"
echo "4. Deploy aplicație"
echo ""

read -p "Continuă? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 1. Inițializare EB (dacă nu există)
if [ ! -d ".elasticbeanstalk" ]; then
    echo ""
    echo "📦 Inițializare Elastic Beanstalk..."
    eb init -p python-3.13 books-reporting-app --region eu-north-1
fi

# 2. Creare environment (dacă nu există)
echo ""
echo "🌍 Verificare environment..."
if ! eb list | grep -q "books-reporting-env"; then
    echo "   Creare environment nou..."
    eb create books-reporting-env \
      --instance-type t3.medium \
      --platform "Python 3.13" \
      --region eu-north-1
else
    echo "   Environment există deja"
fi

# 3. Setup ElastiCache (manual - necesită AWS Console)
echo ""
echo "⚠️  IMPORTANT: Creează ElastiCache Redis cluster manual în AWS Console:"
echo "   1. ElastiCache → Create Redis cluster"
echo "   2. Engine: Redis 7.x"
echo "   3. Node type: cache.t3.micro"
echo "   4. Security: Allow access from EB security group"
echo ""
read -p "Ai creat ElastiCache cluster? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "   Creează cluster-ul și rulează scriptul din nou"
    exit 1
fi

# 4. Upload credentials.json în Secrets Manager
echo ""
echo "🔐 Upload credentials.json în Secrets Manager..."
SECRET_NAME="books-reporting/google-sheets-credentials"
if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region eu-north-1 &>/dev/null; then
    echo "   Secret există deja, actualizare..."
    aws secretsmanager update-secret \
      --secret-id "$SECRET_NAME" \
      --secret-string file://credentials.json \
      --region eu-north-1
else
    echo "   Creare secret nou..."
    aws secretsmanager create-secret \
      --name "$SECRET_NAME" \
      --secret-string file://credentials.json \
      --region eu-north-1
fi

# 5. Setare environment variables
echo ""
echo "⚙️  Setare environment variables..."
read -p "ElastiCache endpoint (ex: books-reporting-redis.xxxxx.cache.amazonaws.com:6379): " ELASTICACHE_ENDPOINT
read -p "Google Sheets Spreadsheet ID: " SPREADSHEET_ID

eb setenv \
  GOOGLE_SHEETS_SPREADSHEET_ID="$SPREADSHEET_ID" \
  REDIS_URL="redis://${ELASTICACHE_ENDPOINT}/0" \
  REDIS_CACHE_URL="redis://${ELASTICACHE_ENDPOINT}/1" \
  FLASK_HOST="0.0.0.0" \
  FLASK_PORT="5001" \
  AMAZON_DELAY_BETWEEN_REQUESTS="8" \
  AMAZON_RETRY_ATTEMPTS="3"

# 6. Deploy
echo ""
echo "🚀 Deploy aplicație..."
eb deploy

echo ""
echo "✅ Deployment complet!"
echo "   Verifică status: eb status"
echo "   Vezi logs: eb logs"
echo "   Open în browser: eb open"

