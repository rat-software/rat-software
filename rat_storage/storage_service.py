"""
Main storage Flask application to manage scraped URLs and search engine result pages.

This service stores screenshots, HTML source code, and PDFs. It provides endpoints 
to upload files and securely retrieve content from within ZIP archives.

Ensure that the user running the Flask app has read/write permissions for your STORAGE FOLDER.
"""

from flask import Flask, request, send_file
import os, zipfile, io
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)

# Configuration constants
# Note: These values must remain synchronized with the main scraper service
API_KEY = "" # Add your own safe API-Key
STORAGE_FOLDER = "/var/www/rat/storage/sources/" # Define your STORAGE Folder on your web server

app.config['SESSION_COOKIE_NAME'] = 'rat_storage_session' # Set unique SESSION COOKIE NAME
app.config['SESSION_COOKIE_PATH'] = '/storage' # Set unique SESSION COOKIE PATH

@app.route('/upload', methods=['POST'])
def upload():
    """
    Handle file uploads from the scraper.
    """
    # API Key check
    if request.headers.get('X-API-Key') != API_KEY:
        return {"error": "Unauthorized"}, 401
    
    if 'file' not in request.files:
        return {"error": "No file part"}, 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    
    os.makedirs(STORAGE_FOLDER, exist_ok=True)
    file.save(os.path.join(STORAGE_FOLDER, filename))
    
    return {"message": "Upload OK", "filename": filename}, 200

@app.route('/view/<filename>/<file_type>')
def view(filename, file_type):
    """
    Retrieve and serve specific content from stored files.
    """
    ticket = request.args.get('ticket')
    if not ticket:
        return "Missing ticket", 401

    # Secure ticket validation
    serializer = URLSafeTimedSerializer(API_KEY)
    
    try:
        data = serializer.loads(ticket, salt='source-view', max_age=14400)
        if data.get('filename') != filename:
            return "Access denied (Ticket mismatch)", 403
    except Exception as e:
        return "Access denied (Ticket expired or invalid)", 403

    zip_path = os.path.join(STORAGE_FOLDER, secure_filename(filename))
    if not os.path.exists(zip_path):
        return "File not found", 404

    # CASE 1: PDF Files - Serve directly (falls alte Scrapes direkt als .pdf gespeichert wurden)
    if filename.lower().endswith('.pdf'):
        return send_file(zip_path, mimetype='application/pdf')

    # CASE 2: ZIP Files
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            files_in_zip = z.namelist()
            
            # --- LOGIK-UPDATE ---
            if file_type == 'screenshot':
                target = 'screenshot.jpg'
                mime = 'image/jpeg'
            else:
                # Wenn 'html' angefragt wird, prüfen wir zuerst, ob es eigentlich ein PDF gibt!
                if 'source.pdf' in files_in_zip:
                    target = 'source.pdf'
                    mime = 'application/pdf'
                else:
                    target = 'source.html'
                    mime = 'text/html'
                    
            # REPARATUR-HACK FÜR GANZ ALTE SCRAPES (als das PDF versehentlich als screenshot.jpg gespeichert wurde)
            if file_type != 'screenshot' and 'source.html' in files_in_zip:
                html_data = z.read('source.html')
                if html_data.strip() == b"pdf" and 'screenshot.jpg' in files_in_zip and 'source.pdf' not in files_in_zip:
                    target = 'screenshot.jpg'
                    mime = 'application/pdf'
            # ---------------------
            
            if target not in files_in_zip:
                return f"{target} not found in ZIP", 404
                
            data = z.read(target)
            response = send_file(io.BytesIO(data), mimetype=mime)
            
            if mime == 'text/html':
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
                
            return response
    except Exception as e:
        return f"Error processing file: {str(e)}", 500

if __name__ == '__main__':
    app.run(port=5001)