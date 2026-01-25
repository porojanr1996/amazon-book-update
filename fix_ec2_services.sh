#!/bin/bash
# Script pentru repornire servicii pe EC2
# Salvează acest script ca fix_ec2_services.sh
# Rulează: bash fix_ec2_services.sh

# Salvează cheia SSH
cat > /tmp/ec2_key.pem << 'KEY_END'
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAzHtJ+T079WwyGb8bBM4Id8EJOZkl/xDHO607ADPlOtbsv30l
k22JDTj1fB1ulM4122hcQUISh9cSH7cHPsGZnSvQWFb8NsaNvOhrfSvFTc53jild
h5eC81SPe75aAAa7lHgcz/9S0QvBaj27+vG6o1LdBTlqkeBRzF8b8zEa4Q9NsHQh
OQE2/yRuFkFGAaW3Mu3LJpdC6Jap4NeL9WBDegSpFIytLBbM9BecUNaVYOs4iVLk
VIANSscZdrGLNUyvzhRu0voMLlb+MINgndkcTXSwzvqP6udHvvFzSQCqtiEZnZyU
Wh7rF13EibWJ8VRLPWK8WKBap2GIsszhd+jwDQIDAQABAoIBAQCXPLjBtyCZrKSB
lm8NZrWsnQGNsFACDw7MfJue0sNAeaYxGwanu+QZ+37VhY88UChVVyKkwZGjFtc4
zc52BArxzG4UaIGyobhDeEPIGI+dtI+Ifd/HYbBg+LIG/Ark6hXjAdONo3JFW0R6
p55ZRGCeW7NNIeJIcnkNh2rMvAz9V1g5R8T4gNEDWw/xS4ufRNhP7DWB8yqhd4I2
tEIvOEHy2tGtwuzVev30OQe7dY5FECgaE8GFbvPQXruku3W9REsR4zwADH19lk9E
YwgWPLOMDsqofBrQNRKhh0B73VnyLnZkjAV7T+y06lVbTUzUrgDyH2B2VFDMi0Pu
T3Gcxd8BAoGBAPw0jhTJkkrcSFxzCpzyfHPcRCb0ch1uXFfxrM1MvJtyKvupaisP
Yx0lPyFeR37Y7Nw/v3qx/5xeh1Mcf1Q4pC2L4ya5TRqlwq8Z1Tjx8FZTkxXt2g19
44L6tVrLSuD0H8IUNQ7clXeYqo0w/5L2yaTSGJ20CGRVnpji3y9HNzSFAoGBAM+O
6WVJwcTc3sFr+Qg8foc2BVcODxv9HFgyZY3BeFe8qQW4bh/Km9bEiqzHuwUm826y
dxXYKIKAv6Xilna9e2H8/nbwhTK3VNJu7k+Xmnjyuny3Qzj4cbvGQLuQcFa11bGE
EWcdg35ew2LrhQmEOSj5gV7gewZT+rSxyRtfmIfpAoGAcIQp1xBOmeNIzSXt2DM+
XpooNZDc0FCKFhoV08mmY1s93eSpHujQeRJC5eofz3GLyn8ON/jtZp+tk+Ck1bgn
VsKP5pjI01icUG4f+DXH2VuTxTbGDzrYo3iiLA2CLHX9LSLCwQycCi0r+a2gd7pu
H4AzxzeofsrL5L1igL8u29kCgYBY0QK2wRUVtJ3tjtKF370VBtzKH83/YBQc+ZPT
URK6GJULSZx2JjEBeiENRnqU/dH1cJDc3B6ZmZZo2ckhDnwZtjT9mHam+SRm1+lK
TclgMB30+EbfvhCNFYzlti0cLbs/tw/rXAnErbBWSAopxFbhXcMqYkzCrHT/lYRF
Hmca4QKBgQC7x1eI5vhFRtnIE70yb8VHlx0IaFFHjAJ9U3tkIhIrhhECJYJmZulg
hJTRnnsesmKC12mNezDB5cQU7pcS7MhnnvD0MFkKLP7ZmcPvmCJbkG190AWlUGaN
G6DmbZkwV+3Zk82okgvsPa45xsT6w7LERAp3l7O+L7vcibpTs9U1gA==
-----END RSA PRIVATE KEY-----
KEY_END

chmod 600 /tmp/ec2_key.pem

echo "🔧 Conectare la EC2 și repornire servicii..."
echo ""

ssh -i /tmp/ec2_key.pem -o StrictHostKeyChecking=no ec2-user@16.171.115.88 << 'SSH_END'
cd /home/ec2-user/app/books-reporting
export GOOGLE_SHEETS_SPREADSHEET_ID=1-y5ly84oAV1GkhpLlD3MfvLZSi-5UThypHXsmch6RiA

echo "=== Status curent ==="
sudo docker ps -a

echo ""
echo "=== Oprește serviciile ==="
sudo docker-compose -f docker/docker-compose.yml down

echo ""
echo "=== Repornește serviciile ==="
sudo docker-compose -f docker/docker-compose.yml up -d

echo ""
echo "=== Așteaptă 10 secunde ==="
sleep 10

echo ""
echo "=== Status final ==="
sudo docker ps

echo ""
echo "=== Verifică logs sheets-service ==="
sudo docker logs docker-sheets-service-1 --tail 10 2>&1 | tail -5

echo ""
echo "=== Verifică logs scraper-service ==="
sudo docker logs docker-scraper-service-1 --tail 10 2>&1 | tail -5

echo ""
echo "✅ Gata! Testează: http://16.171.115.88:5001"
SSH_END

echo ""
echo "🧹 Ștergere cheie SSH..."
rm -f /tmp/ec2_key.pem

