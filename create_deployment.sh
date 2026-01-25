#!/bin/bash
# Creează ZIP pentru deployment EB

echo "📦 Creating deployment package..."

# Exclude fișierele care nu trebuie
zip -r deployment.zip . \
  -x "*.git*" \
  -x "*venv*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*.log" \
  -x "*.env" \
  -x "*credentials.json" \
  -x "*test_*" \
  -x "*debug_*" \
  -x "*.md" \
  -x "*backup_*" \
  -x "*BundleLogs*" \
  -x "*.zip" \
  -x "*.sh" \
  -x "*node_modules*"

echo "✅ deployment.zip created!"
echo "📤 Upload this file in EB Console → Upload and deploy"
