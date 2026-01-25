#!/bin/bash
# Script pentru verificare Secrets Manager

echo "🔍 Verificare Secrets Manager..."
echo ""

# Verifică dacă AWS CLI este instalat
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI nu este instalat"
    echo ""
    echo "Instalează AWS CLI:"
    echo "  brew install awscli"
    echo ""
    echo "SAU verifică manual în AWS Console:"
    echo "  AWS Console → Secrets Manager → Region: eu-north-1"
    echo "  Caută:"
    echo "    - books-reporting/google-sheets-credentials"
    echo "    - books-reporting/spreadsheet-id"
    exit 1
fi

echo "✅ AWS CLI este instalat"
echo ""

# Verifică credentials
echo "Verificare credentials AWS..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials nu sunt configurate"
    echo "Rulează: aws configure"
    exit 1
fi

echo "✅ AWS credentials configurate"
echo ""

# Verifică secrets
REGION="eu-north-1"

echo "Verificare secrets în region: $REGION"
echo ""

# Verifică credentials secret
echo "1. Verificare: books-reporting/google-sheets-credentials"
if aws secretsmanager describe-secret --secret-id books-reporting/google-sheets-credentials --region $REGION &> /dev/null; then
    echo "   ✅ Secret există"
    SECRET_INFO=$(aws secretsmanager describe-secret --secret-id books-reporting/google-sheets-credentials --region $REGION --query '{Name:Name, ARN:ARN}' --output json)
    echo "   $SECRET_INFO"
else
    echo "   ❌ Secret NU există"
    echo "   Trebuie să-l creezi în AWS Console"
fi
echo ""

# Verifică spreadsheet-id secret
echo "2. Verificare: books-reporting/spreadsheet-id"
if aws secretsmanager describe-secret --secret-id books-reporting/spreadsheet-id --region $REGION &> /dev/null; then
    echo "   ✅ Secret există"
    SECRET_INFO=$(aws secretsmanager describe-secret --secret-id books-reporting/spreadsheet-id --region $REGION --query '{Name:Name, ARN:ARN}' --output json)
    echo "   $SECRET_INFO"
else
    echo "   ❌ Secret NU există"
    echo "   Trebuie să-l creezi în AWS Console"
fi
echo ""

echo "=========================================="
echo "Dacă secrets NU există, creează-le în AWS Console:"
echo ""
echo "1. AWS Console → Secrets Manager → Store a new secret"
echo "2. Secret type: Other type of secret → Plaintext"
echo "3. Pentru credentials.json: copiază tot conținutul fișierului"
echo "4. Pentru spreadsheet-id: 1-y5ly84oAV1GkhpLlD3MfvLZSi-5UThypHXsmch6RiA"
echo ""

