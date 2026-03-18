import os
import sys
import requests
import time
from itsdangerous import URLSafeTimedSerializer

# Pfad erweitern, damit 'libs' gefunden wird (falls Skript im Root liegt)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.lib_sources import Sources

# ==========================================
# KONFIGURATION
# ==========================================
# WICHTIG: Hier muss jetzt deine HAUPT-DOMAIN stehen (ohne Port 5000!)
STORAGE_BASE_URL = "https://tool.rat-software.org/storage"
#STORAGE_BASE_URL = "http://127.0.0.1:5001"          # <-- Lokal testen (Achte auf den Port deines Storage-Services)

# Muss exakt mit API_UPLOAD_KEY in deiner config.py übereinstimmen
API_UPLOAD_KEY = "8eMYe0Y1sZ2MSv48NOt9EPhh1g61ze" 

def generate_test_ticket(filename):
    """Generiert ein Ticket, um den geschützten Download zu testen"""
    serializer = URLSafeTimedSerializer(API_UPLOAD_KEY)
    # Der Salt muss exakt 'source-view' sein (wie in assessment.py definiert)
    return serializer.dumps({'filename': filename}, salt='source-view')

if __name__ == "__main__":
    # URL zum Testen
    url = "https://www.hamburg.de"
    print(f"--- 1. Starte Scraping & Upload für: {url} ---")
    
    # Scraper initialisieren und ausführen
    sources = Sources()
    result = sources.save_code(url) 
    
    file_path = result.get('file_path')
    error_codes = result.get('error_codes', '')
    content_type = result.get('request', {}).get('content_type', '')
    
    if not file_path:
        print("\n❌ FEHLER: Kein 'file_path' erhalten. Upload fehlgeschlagen!")
        print(f"Details: {error_codes}")
        
        # Falls es ein lokaler Pfad ist (Fallback), zeigen wir das an
        if result.get('file_path') and 'http' not in result.get('file_path'):
             print("Hinweis: Datei wurde lokal gespeichert (Scraper im Offline-Modus?).")
        exit(1)
    
    print(f"✅ Upload erfolgreich! Server-Dateiname: {file_path}")
    print(f"📄 Erkannter Content-Type: {content_type}")
    
    # --- 2. DOWNLOAD TESTEN (Das Assessment simulieren) ---
    print(f"\n--- 2. Teste Download vom Server ({STORAGE_BASE_URL}) ---")
    
    ticket = generate_test_ticket(file_path)
    print(f"Ticket generiert: {ticket[:15]}...")
    
    # WEICHE: Handelt es sich um ein PDF oder um eine HTML-Seite?
    is_pdf = "pdf" in content_type.lower()
    
    if is_pdf:
        print("-> PDF erkannt! Überspringe Screenshot-Test und lade Dokument herunter.")
        test_endpoints = [
            {"type": "html", "name": "PDF-Dokument (über 'html' Parameter wie im Frontend)", "ext": "pdf"}
        ]
    else:
        print("-> Webseite erkannt! Teste HTML-Quelltext und Screenshot.")
        test_endpoints = [
            {"type": "screenshot", "name": "Screenshot (JPG)", "ext": "jpg"},
            {"type": "html", "name": "Quelltext (HTML)", "ext": "html"}
        ]
    
    for endpoint in test_endpoints:
        download_url = f"{STORAGE_BASE_URL}/view/{file_path}/{endpoint['type']}?ticket={ticket}"
        print(f"\nTeste {endpoint['name']}...")
        print(f"URL: {download_url}")
        
        try:
            response = requests.get(download_url, timeout=15)
            
            if response.status_code == 200:
                size_kb = len(response.content) / 1024
                print(f"  ✅ ERFOLG: {size_kb:.2f} KB empfangen.")
                
                out_filename = f"test_download.{endpoint['ext']}"
                with open(out_filename, "wb") as f:
                    f.write(response.content)
                print(f"     (Gespeichert als {out_filename} - Bitte im Ordner prüfen!)")
                
            else:
                print(f"  ❌ FEHLER: Status Code {response.status_code}")
                print(f"  Antwort: {response.text[:200]}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")

    print("\n--- Test abgeschlossen ---")