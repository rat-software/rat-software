import os
import requests
import zipfile
import io
import json

from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer, BadSignature

class Helper:
    def __init__(self):
        """initializes the helper class with the necessary configurations to connect to the storage service (/rat_storage)."""
        self.api_key = "your_api_key_here"  # Replace with your actual Storage API key
        self.base_url = "your_storage_base_url_here"  # Replace with your actual Storage base URL
        self.serializer = URLSafeTimedSerializer(self.api_key)

    def decode_code(self, filename):
        """Retrieves the source.html via HTTP from the storage server."""
        if not filename or filename == "error":
            return ""
            
        # 1. Generate a ticket to request the file
        ticket = self.serializer.dumps({'filename': filename}, salt='source-view')
        
        # 2. Retrieve a file via HTTP
        url = f"{self.base_url}/view/{filename}/html"
        try:
            response = requests.get(url, params={'ticket': ticket}, timeout=15)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Error: Server responded with status code {response.status_code}")
        except Exception as e:
            print(f"Connection error retrieving source code: {e}")
            
        return ""

    def decode_picture(self, filename):
        """Retrieves the screenshot via HTTP from the storage server."""
        if not filename or filename == "error":
            return None
            
        ticket = self.serializer.dumps({'filename': filename}, salt='source-view')
        url = f"{self.base_url}/view/{filename}/screenshot"
        
        try:
            response = requests.get(url, params={'ticket': ticket}, timeout=15)
            if response.status_code == 200:
                return response.content # Gibt rohe Bytes zurück
        except Exception as e:
            print(f"Connection error retrieving image: {e}")
            
        return None
    
    def __del__(self):
        """
        Destructor for the Helper object.

        This method is automatically called when the object is about to be destroyed.
        It prints a message indicating that the Helper object has been destroyed.
        """
        print('Helper object destroyed')

    def file_to_dict(self, path):
        """
        Read a JSON file from the specified path and return its contents as a dictionary.

        Args:
            path (str): The file path to read the JSON data from.

        Returns:
            dict: A dictionary containing the parsed JSON data from the file.

        Raises:
            FileNotFoundError: If the file specified by `path` does not exist.
            json.JSONDecodeError: If the file content is not valid JSON.
        """
        with open(path, encoding="utf-8") as f:
            # Load the content of the file as JSON and return it as a dictionary
            return json.load(f)
