#!/bin/bash
# User data script pentru EC2 - Setup complet automat

set -e

echo "🚀 Starting EC2 setup for Books Reporting..."

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

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

# Install Python 3.13 (dacă e necesar)
yum install python3 python3-pip -y

# Create app directory
mkdir -p /home/ec2-user/app
cd /home/ec2-user/app

# Clone repository (sau copiază codul)
# git clone https://github.com/YOUR_USERNAME/books-reporting.git
# cd books-reporting

# Download credentials from Secrets Manager
echo "Downloading credentials from Secrets Manager..."
aws secretsmanager get-secret-value \
  --secret-id books-reporting/google-sheets-credentials \
  --region eu-north-1 \
  --query SecretString \
  --output text > credentials.json
chmod 400 credentials.json

# Get Spreadsheet ID from Secrets Manager
SPREADSHEET_ID=$(aws secretsmanager get-secret-value \
  --secret-id books-reporting/spreadsheet-id \
  --region eu-north-1 \
  --query SecretString \
  --output text | tr -d '"')

# Get ElastiCache endpoint (trebuie să-l configurezi manual sau să-l pui în Secrets Manager)
# REDIS_ENDPOINT=$(aws secretsmanager get-secret-value \
#   --secret-id books-reporting/redis-endpoint \
#   --region eu-north-1 \
#   --query SecretString \
#   --output text | tr -d '"')

# Create .env file
cat > .env << EOF
GOOGLE_SHEETS_CREDENTIALS_PATH=/app/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=${SPREADSHEET_ID}
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
AMAZON_DELAY_BETWEEN_REQUESTS=8
AMAZON_RETRY_ATTEMPTS=3
AMAZON_MAX_WORKERS=1
FLASK_ENV=production
EOF

# Start services with Docker Compose
echo "Starting services..."
docker-compose -f docker/docker-compose.yml up -d

echo "✅ Setup complete!"
echo "Aplicația rulează pe: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5001"

