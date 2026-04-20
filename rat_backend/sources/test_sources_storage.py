import os
import sys
import requests
import time
from itsdangerous import URLSafeTimedSerializer

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.lib_sources import Sources

STORAGE_BASE_URL = "your_storage_base_url_here" # Storage Base URL
API_UPLOAD_KEY = "your_api_key_here" # Storage API Key

def generate_test_ticket(filename):
    """Generiert ein Ticket, um den geschützten Download zu testen"""
    serializer = URLSafeTimedSerializer(API_UPLOAD_KEY)
    return serializer.dumps({'filename': filename}, salt='source-view')

if __name__ == "__main__":
    url = "https://www.example.com/" # Replace with the URL you want to scrape
    print(f"--- 1. Start scraping and upload to storage: {url} ---")
    
    # Scraper initialisieren und ausführen
    sources = Sources()
    result = sources.save_code(url) 
    
    file_path = result.get('file_path')
    error_codes = result.get('error_codes', '')
    content_type = result.get('request', {}).get('content_type', '')
    
    if not file_path:
        print("\n❌ Error: No file path found!")
        print(f"Details: {error_codes}")
        
        if result.get('file_path') and 'http' not in result.get('file_path'):
             print("Notice: URL was saved locally.")
        exit(1)
    
    print(f"✅ Upload successful! Server file path: {file_path}")
    print(f"📄 Content type: {content_type}")
    
    print(f"\n--- 2. Test download from storage server ({STORAGE_BASE_URL}) ---")
    
    ticket = generate_test_ticket(file_path)
    print(f"Ticket generated: {ticket[:15]}...")
    
    is_pdf = "pdf" in content_type.lower()
    
    if is_pdf:
        print("-> PDF found!.")
        test_endpoints = [
            {"type": "html", "name": "PDF test", "ext": "pdf"}
        ]
    else:
        print("-> Webpage recognized. Test HTML and screenshot")
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
                print(f"  ✅ Success: {size_kb:.2f} KB received.")
                
                out_filename = f"test_download.{endpoint['ext']}"
                with open(out_filename, "wb") as f:
                    f.write(response.content)
                print(f"     (Saved as {out_filename} - Check directory!)")
                
            else:
                print(f"  ❌ ERROR: Status Code {response.status_code}")
                print(f"  Answer: {response.text[:200]}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")

    print("\n--- Test done ---")