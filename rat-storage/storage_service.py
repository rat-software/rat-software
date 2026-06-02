from flask import Flask, request, send_file
import os, zipfile, io, time  # <--- Added time import here
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeSerializer, BadSignature
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['API_KEY'] = os.getenv('API_UPLOAD_KEY', 'your_api_key_here')  
app.config['STORAGE_FOLDER'] = os.getenv('STORAGE_FOLDER', 'your_storage_folder')  
app.config['SESSION_COOKIE_NAME'] = 'rat_storage_session'
app.config['SESSION_COOKIE_PATH'] = '/storage'

@app.route('/')
def index():
    return "RAT Storage Service is running!", 200

@app.route('/upload', methods=['POST'])
def upload():
    if request.headers.get('X-API-Key') != app.config['API_KEY']:
        return {"error": "Unauthorized"}, 401
    
    if 'file' not in request.files:
        return {"error": "No file part"}, 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    
    os.makedirs(app.config['STORAGE_FOLDER'], exist_ok=True)
    file.save(os.path.join(app.config['STORAGE_FOLDER'], filename))
    
    return {"message": "Upload OK", "filename": filename}, 200

@app.route('/view/<filename>/<file_type>')
def view(filename, file_type):
    """
    Retrieve and serve specific content from stored files using an explicit expiration timestamp.
    """
    ticket = request.args.get('ticket')
    if not ticket:
        return "Missing ticket", 401

    serializer = URLSafeSerializer(app.config['API_KEY'])
    
    try:
        # 1. Decrypt ticket and verify cryptographic signature
        data = serializer.loads(ticket, salt='source-view')
        
        # 2. Prevent parameter tampering (verify filename matches)
        if data.get('filename') != filename:
            return "Access denied (Ticket mismatch)", 403
            
        # 3. Manually verify expiration using timezone-agnostic Unix Epoch time
        current_time = int(time.time())
        if current_time > data.get('expires_at', 0):
            return "Access denied (Ticket expired)", 403
            
    except BadSignature:
        return "Access denied (Invalid token or signature)", 403
    except Exception as e:
        return f"Access denied (Error: {type(e).__name__})", 403

    # Build absolute path to the archive file
    zip_path = os.path.join(app.config['STORAGE_FOLDER'], secure_filename(filename))
    if not os.path.exists(zip_path):
        return "File not found", 404

    if filename.lower().endswith('.pdf'):
        return send_file(zip_path, mimetype='application/pdf')

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            files_in_zip = z.namelist()
            
            if file_type == 'screenshot':
                target = 'screenshot.jpg'
                mime = 'image/jpeg'
            else:
                if 'source.pdf' in files_in_zip:
                    target = 'source.pdf'
                    mime = 'application/pdf'
                else:
                    target = 'source.html'
                    mime = 'text/html'
                    
            if file_type != 'screenshot' and 'source.html' in files_in_zip:
                html_data = z.read('source.html')
                if html_data.strip() == b"pdf" and 'screenshot.jpg' in files_in_zip and 'source.pdf' not in files_in_zip:
                    target = 'screenshot.jpg'
                    mime = 'application/pdf'
            
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