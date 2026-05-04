"""
End-to-End Test Script for the RAT Storage Service.

This script simulates a complete cycle: 
1. Creating a dummy ZIP archive in memory.
2. Uploading the archive via the API.
3. Generating a secure ticket and verifying the retrieval (view) of the content.
"""

import requests
import io
import zipfile
from itsdangerous import URLSafeTimedSerializer

# ==========================================
# CONFIGURATION
# ==========================================
# Ensure the BASE_URL matches your actual server deployment
BASE_URL = "" # Base URL of the Storage Service
API_KEY = ""  # Must match the STORAGE_SERVICE API_KEY
FILENAME = "full_cycle_test.zip" # Test File Name
# ==========================================

def create_test_zip():
    """
    Creates an in-memory ZIP file containing a dummy HTML file and a fake PNG.
    
    Returns:
        io.BytesIO: A binary stream containing the ZIP data.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add a dummy HTML file
        zf.writestr('source.html', '<h1>Test successful!</h1>')
        # Add a dummy JPG file header
        zf.writestr('screenshot.jpg', b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR') 
    
    zip_buffer.seek(0)
    return zip_buffer

def run_test():
    """
    Executes the upload and retrieval test sequence.
    """
    # 1. Test File Upload
    print(f"🚀 Step 1: Uploading test file...")
    files = {'file': (FILENAME, create_test_zip(), 'application/zip')}
    
    # Note: Ensure the endpoint path matches your Flask route configuration
    up_res = requests.post(
        f"{BASE_URL}/upload", 
        headers={'X-API-Key': API_KEY}, 
        files=files
    )
    
    if up_res.status_code == 200:
        server_file = up_res.json().get('filename')
        print(f"✅ Upload successful: {server_file}")

        # 2. Test Content Retrieval (View)
        print(f"\n🔍 Step 2: Validating View route...")
        
        # Generate a secure timed ticket for the specific filename
        serializer = URLSafeTimedSerializer(API_KEY)
        ticket = serializer.dumps({'filename': server_file}, salt='source-view')
        
        # Request the HTML content from the uploaded ZIP
        view_url = f"{BASE_URL}/view/{server_file}/html"
        down_res = requests.get(view_url, params={'ticket': ticket})
        
        if down_res.status_code == 200:
            print(f"✅ VIEW successful: Received content: {down_res.text[:25]}...")
        else:
            print(f"❌ VIEW failed: Status {down_res.status_code} - {down_res.text}")
    else:
        print(f"❌ UPLOAD failed: Status {up_res.status_code} - {up_res.text}")

if __name__ == "__main__":
    run_test()