#!/bin/bash
# Script pentru a vizualiza cărțile care au eșuat

echo "📊 RAPORT CĂRȚI EȘUATE"
echo "======================"
echo ""

if [ ! -f "failed_books_report.json" ]; then
    echo "❌ Raportul nu există. Rulează mai întâi:"
    echo "   python3 analyze_failed_books.py"
    exit 1
fi

# Afișează rezumat
echo "📈 STATISTICI:"
python3 << 'PYTHON'
import json
with open('failed_books_report.json', 'r') as f:
    report = json.load(f)
    
print(f"   Total cărți: {report['total_books']}")
print(f"   ✅ Succese: {report['summary']['success_count']} ({report['summary']['success_rate']})")
print(f"   ❌ Eșecuri: {report['summary']['failure_count']}")
print()
PYTHON

# Afișează lista cărților eșuate
echo "❌ CĂRȚI CARE AU EȘUAT:"
echo "----------------------"
python3 << 'PYTHON'
import json
with open('failed_books_report.json', 'r') as f:
    report = json.load(f)
    
for i, book in enumerate(report['failed'], 1):
    print(f"{i}. {book['name']}")
    print(f"   Autor: {book['author']}")
    print(f"   URL: {book['amazon_link']}")
    print(f"   Coloană: {book['col']}")
    print(f"   Motiv: {book['reason']}")
    print()
PYTHON

echo ""
echo "💡 Pentru a re-analiza, rulează:"
echo "   python3 analyze_failed_books.py"

