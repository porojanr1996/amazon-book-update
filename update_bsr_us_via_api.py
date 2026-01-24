#!/usr/bin/env python3
"""
Script pentru actualizarea BSR-ului doar pentru US via API
"""
import requests
import json
import sys

# URL-ul aplicației
BASE_URL = "https://books-reporting.novamediamarketing.net"
# Sau folosește IP direct dacă DNS nu funcționează:
# BASE_URL = "http://13.48.29.45:5001"

def trigger_bsr_update_us():
    """Trigger BSR update pentru Crime Fiction - US"""
    worksheet_name = "Crime Fiction - US"
    
    try:
        print(f"🚀 Declanșare update BSR pentru: {worksheet_name}...")
        response = requests.post(
            f"{BASE_URL}/api/update-bsr",
            json={"worksheet": worksheet_name},
            timeout=5
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("status") == "started":
            print(f"✅ Update declanșat cu succes pentru {worksheet_name}")
            print(f"   Mesaj: {result.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ Eroare: {result.get('message', 'Status necunoscut')}")
            return False
    except Exception as e:
        print(f"❌ Eroare la declanșare update: {e}")
        return False

def main():
    print("=" * 60)
    print("🔄 ACTUALIZARE BSR PENTRU CRIME FICTION - US")
    print("=" * 60)
    print()
    
    print("⚠️  Acest script va declanșa actualizarea BSR pentru Crime Fiction - US.")
    print("   Actualizarea se va face în background și poate dura câteva minute.")
    print()
    
    response = input("Continuă? (da/nu): ").strip().lower()
    if response not in ['da', 'yes', 'y', 'd']:
        print("❌ Anulat.")
        sys.exit(0)
    print()
    
    success = trigger_bsr_update_us()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Actualizare declanșată cu succes!")
    else:
        print("❌ Eroare la declanșare actualizare")
    print("=" * 60)
    print()
    print("📊 Actualizarea rulează în background.")
    print("   Verifică log-urile aplicației pentru progres:")
    print("   tail -f /home/ec2-user/app/books-reporting/app.log")
    print()
    print("💡 Graficele se vor actualiza automat când se reîncarcă pagina.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

