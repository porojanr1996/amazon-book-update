#!/usr/bin/env python3
"""
Script pentru actualizarea BSR-ului pentru toate worksheet-urile via API
Rulează update-ul pentru fiecare worksheet în paralel
"""
import requests
import json
import time
import sys

# URL-ul aplicației
BASE_URL = "https://books-reporting.novamediamarketing.net"
# Sau folosește IP direct dacă DNS nu funcționează:
# BASE_URL = "http://13.48.29.45:5001"

def get_worksheets():
    """Obține lista de worksheet-uri"""
    try:
        response = requests.get(f"{BASE_URL}/api/worksheets", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Eroare la obținerea worksheet-urilor: {e}")
        return []

def trigger_bsr_update(worksheet_name):
    """Trigger BSR update pentru un worksheet"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/update-bsr",
            json={"worksheet": worksheet_name},
            timeout=5
        )
        response.raise_for_status()
        result = response.json()
        return result.get("status") == "started"
    except Exception as e:
        print(f"❌ Eroare la trigger update pentru {worksheet_name}: {e}")
        return False

def main():
    print("=" * 60)
    print("🔄 ACTUALIZARE BSR PENTRU TOATE WORKSHEET-URILE")
    print("=" * 60)
    print()
    
    # Obține worksheet-urile
    print("📋 Obținere lista de worksheet-uri...")
    worksheets = get_worksheets()
    
    if not worksheets:
        print("❌ Nu s-au găsit worksheet-uri sau eroare la conectare")
        sys.exit(1)
    
    print(f"✅ Găsite {len(worksheets)} worksheet-uri:")
    for ws in worksheets:
        print(f"   - {ws}")
    print()
    
    # Confirmare
    print("⚠️  Acest script va declanșa actualizarea BSR pentru toate worksheet-urile.")
    print("   Actualizarea se va face în background și poate dura câteva minute.")
    print()
    response = input("Continuă? (da/nu): ").strip().lower()
    if response not in ['da', 'yes', 'y', 'd']:
        print("❌ Anulat.")
        sys.exit(0)
    print()
    
    # Trigger update pentru fiecare worksheet
    print("🚀 Declanșare actualizări BSR...")
    print()
    
    success_count = 0
    failed_count = 0
    
    for worksheet in worksheets:
        print(f"📚 Declanșare update pentru: {worksheet}...")
        if trigger_bsr_update(worksheet):
            print(f"   ✅ Update declanșat cu succes pentru {worksheet}")
            success_count += 1
        else:
            print(f"   ❌ Eroare la declanșare update pentru {worksheet}")
            failed_count += 1
        print()
        time.sleep(1)  # Mic delay între request-uri
    
    print("=" * 60)
    print(f"✅ Actualizări declanșate: {success_count}")
    if failed_count > 0:
        print(f"❌ Erori: {failed_count}")
    print("=" * 60)
    print()
    print("📊 Actualizările rulează în background.")
    print("   Verifică log-urile aplicației pentru progres:")
    print("   tail -f /home/ec2-user/app/books-reporting/app.log")
    print()
    print("💡 Graficele se vor actualiza automat când se reîncarcă pagina.")

if __name__ == "__main__":
    main()

