import os
import requests
import zipfile
import io
import json
import time

from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer, BadSignature

class Helper:
    def __init__(self):
        """Initializes the helper class by loading settings from the config folder."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '../../config/config_sources.ini')
        config_path = os.path.normpath(config_path)

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.api_key = config_data.get("api-key", "default_key_if_missing")
            raw_url = config_data.get("storage-url", "default_url_if_missing")
            self.base_url = raw_url.removesuffix('/upload').removesuffix('/upload/')
            
        except FileNotFoundError:
            print(f"Critical Error: Configuration file not found at {config_path}")
            self.api_key = None
            self.base_url = None
        except json.JSONDecodeError:
            print(f"Critical Error: Failed to decode JSON from {config_path}. Ensure it is formatted as JSON.")
            self.api_key = None
            self.base_url = None

        self.serializer = URLSafeTimedSerializer(self.api_key) if self.api_key else None
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def decode_code(self, filename_from_db):
        """
        Requests the source.html from the RAT Storage Service.
        The storage service handles the ZIP extraction natively and returns the raw HTML string.
        """
        if not filename_from_db or filename_from_db == "error" or not self.serializer:
            return ""
            
        filename = str(filename_from_db).strip()
            
        ticket = self.serializer.dumps({'filename': filename}, salt='source-view')
        url = f"{self.base_url}/view/{filename}/html?ticket={ticket}"
        
        for attempt in range(3):
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                
                if response.status_code == 200:
                    return response.text
                        
                elif response.status_code == 403:
                    print(f"Warning: 403 Forbidden for ID {file_id}. Attempt {attempt + 1}/3. Retrying...")
                    time.sleep(1) 
                    
                else:
                    print(f"Error: Storage server responded with status code {response.status_code} for ID {file_id}")
                    break 
                    
            except requests.exceptions.RequestException as e:
                print(f"Connection error retrieving source code for ID {file_id}: {e}")
                time.sleep(1)
                
        return ""

    def decode_picture(self, filename_from_db):
        """Retrieves the screenshot with automatic retry on 403."""
        if not filename_from_db or filename_from_db == "error" or not self.serializer:
            return None
            
        filename = str(filename_from_db).strip()
        ticket = self.serializer.dumps({'filename': filename}, salt='source-view')
        url = f"{self.base_url}/view/{filename}/screenshot?ticket={ticket}"
        
        for attempt in range(3):
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                
                if response.status_code == 200:
                    return response.content
                elif response.status_code == 403:
                    print(f"Warning: 403 for screenshot {filename}. Attempt {attempt + 1}/3. Retrying...")
                    time.sleep(1)
                else:
                    print(f"Error: Server responded with status code {response.status_code} for {filename}")
                    break
                    
            except Exception as e:
                print(f"Connection error retrieving image: {e}")
                time.sleep(1)
                
        return None
    
    def __del__(self):
        print('Helper object destroyed')

    def file_to_dict(self, path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)