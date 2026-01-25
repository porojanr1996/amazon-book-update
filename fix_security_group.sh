#!/bin/bash
# Script pentru a adăuga regula Security Group pentru port 5001

echo "🔒 Fix Security Group - Port 5001"
echo ""

# Obține informații despre instanță
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null)
REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null || echo "eu-north-1")

if [ -z "$INSTANCE_ID" ]; then
    echo "❌ Nu pot obține Instance ID. Rulează scriptul pe EC2."
    exit 1
fi

echo "📋 Informații instanță:"
echo "   Instance ID: $INSTANCE_ID"
echo "   Region: $REGION"
echo ""

# Obține Security Group ID
SG_ID=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $REGION \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text 2>/dev/null)

if [ -z "$SG_ID" ] || [ "$SG_ID" = "None" ]; then
    echo "❌ Nu pot obține Security Group ID. Verifică AWS CLI credentials."
    exit 1
fi

echo "   Security Group ID: $SG_ID"
echo ""

# Verifică dacă regula există deja
EXISTING_RULE=$(aws ec2 describe-security-groups \
  --group-ids $SG_ID \
  --region $REGION \
  --query "SecurityGroups[0].IpPermissions[?FromPort==\`5001\` && ToPort==\`5001\` && IpProtocol==\`tcp\`]" \
  --output text 2>/dev/null)

if [ -n "$EXISTING_RULE" ]; then
    echo "✅ Regula pentru port 5001 există deja!"
    echo ""
    echo "📋 Reguli existente pentru port 5001:"
    aws ec2 describe-security-groups \
      --group-ids $SG_ID \
      --region $REGION \
      --query "SecurityGroups[0].IpPermissions[?FromPort==\`5001\`]" \
      --output table
    exit 0
fi

# Adaugă regula
echo "➕ Adăugare regulă pentru port 5001..."
echo "   Type: Custom TCP"
echo "   Port: 5001"
echo "   Source: 0.0.0.0/0 (toate IP-urile)"
echo ""

RESULT=$(aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5001 \
  --cidr 0.0.0.0/0 \
  --region $REGION \
  --description "Books Reporting API" 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ Regulă adăugată cu succes!"
else
    if echo "$RESULT" | grep -q "already exists"; then
        echo "✅ Regula există deja (asta e OK)"
    else
        echo "❌ Eroare la adăugarea regulii:"
        echo "$RESULT"
        exit 1
    fi
fi

echo ""
echo "🔍 Verificare reguli..."
aws ec2 describe-security-groups \
  --group-ids $SG_ID \
  --region $REGION \
  --query "SecurityGroups[0].IpPermissions[?FromPort==\`5001\`]" \
  --output table

echo ""
echo "🌐 Testare conectivitate..."
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
if [ -n "$PUBLIC_IP" ]; then
    echo "   IP Public: $PUBLIC_IP"
    sleep 2
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$PUBLIC_IP:5001/api/scheduler-status 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ Aplicația răspunde la IP public!"
    else
        echo "   ⚠️  Aplicația nu răspunde încă (HTTP $HTTP_CODE)"
        echo "   Așteaptă 10-30 secunde pentru propagare"
    fi
else
    echo "   ⚠️  Nu pot obține IP public"
fi

echo ""
echo "✅ Gata! Aplicația ar trebui să fie accesibilă la:"
echo "   http://$PUBLIC_IP:5001"
echo "   sau"
echo "   http://51.20.76.150:5001"

