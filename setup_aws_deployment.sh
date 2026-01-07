#!/bin/bash
# Script pentru setup complet deployment pe AWS

set -e

echo "🚀 Setup Deployment Complet pe AWS"
echo "===================================="
echo ""

# Verifică dacă Git este instalat
if ! command -v git &> /dev/null; then
    echo "❌ Git nu este instalat!"
    exit 1
fi

# Verifică dacă credentials.json există
if [ ! -f "credentials.json" ]; then
    echo "⚠️  ATENȚIE: credentials.json nu există!"
    echo "   Creează credentials.json înainte de a continua."
    exit 1
fi

# Inițializare Git (dacă nu există)
if [ ! -d ".git" ]; then
    echo "📦 Inițializare Git repository..."
    git init
    git branch -M main
    echo "✅ Git repository inițializat"
else
    echo "✅ Git repository deja există"
fi

# Verifică dacă există remote
if ! git remote get-url origin &> /dev/null; then
    echo ""
    echo "📝 Configurare GitHub Remote:"
    read -p "Introdu URL-ul repository-ului GitHub (ex: https://github.com/USERNAME/books-reporting.git): " GITHUB_URL
    
    if [ -z "$GITHUB_URL" ]; then
        echo "❌ URL GitHub este necesar!"
        exit 1
    fi
    
    git remote add origin "$GITHUB_URL"
    echo "✅ Remote adăugat: $GITHUB_URL"
else
    echo "✅ Remote deja configurat: $(git remote get-url origin)"
fi

# Adaugă toate fișierele
echo ""
echo "📦 Adăugare fișiere în Git..."
git add .

# Commit
echo ""
echo "💾 Commit modificări..."
git commit -m "Initial commit - Ready for AWS deployment" || echo "⚠️  Nu sunt modificări de commit"

# Push (opțional)
echo ""
read -p "Vrei să faci push pe GitHub acum? (da/nu): " PUSH_NOW
if [[ "$PUSH_NOW" =~ ^[Dd][Aa]$|^[Yy][Ee][Ss]$|^[Yy]$ ]]; then
    echo "📤 Push pe GitHub..."
    git push -u origin main || echo "⚠️  Push a eșuat. Verifică credentials și URL."
else
    echo "ℹ️  Push pe GitHub mai târziu cu: git push -u origin main"
fi

echo ""
echo "===================================="
echo "✅ Setup complet!"
echo ""
echo "📋 URMĂTORII PAȘI:"
echo ""
echo "1. Creează repository pe GitHub (dacă nu există):"
echo "   https://github.com/new"
echo ""
echo "2. Setup Secrets în GitHub:"
echo "   Repository → Settings → Secrets and variables → Actions"
echo "   Adaugă:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - GOOGLE_SHEETS_SPREADSHEET_ID"
echo "   - REDIS_URL"
echo "   - REDIS_CACHE_URL"
echo ""
echo "3. Setup AWS Resources (vezi AWS_FULL_DEPLOYMENT.md):"
echo "   - ElastiCache Redis"
echo "   - Secrets Manager (upload credentials.json)"
echo "   - Elastic Beanstalk Environment"
echo ""
echo "4. Push codul:"
echo "   git push"
echo ""
echo "5. GitHub Actions va deploya automat pe AWS!"
echo ""
echo "📖 Documentație completă:"
echo "   - AWS_FULL_DEPLOYMENT.md"
echo "   - GITHUB_ACTIONS_SETUP.md"
echo ""

