import os
import hashlib
import base64
from cryptography.fernet import Fernet
from flask import current_app

def _get_fernet_instance():
    """
    Creates the Fernet instance using exactly the same SHA256 hashing logic
    as lib_helper.py in the distributed backend.
    """
    master_key = None
    if current_app:
        master_key = current_app.config.get('LLM_SECRET_KEY')
    
    if not master_key:
        master_key = os.environ.get('LLM_SECRET_KEY')

    if not master_key:
        print("WARNING: LLM_SECRET_KEY is missing! Cannot initialize encryption.")
        return None

    
    key_bytes = hashlib.sha256(master_key.encode('utf-8')).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    
    return Fernet(fernet_key)

def encrypt_key(plain_text_key):
    """Encrypts an API key for storage in the database."""
    if not plain_text_key:
        return None
        
    f = _get_fernet_instance()
    if not f:
        return None
        
    return f.encrypt(plain_text_key.encode('utf-8')).decode('utf-8')

def decrypt_key(encrypted_key):
    """Decrypts an API key (e.g., for the Connection Test in the frontend)."""
    if not encrypted_key:
        return None
        
    f = _get_fernet_instance()
    if not f:
        return None
        
    try:
        return f.decrypt(encrypted_key.encode('utf-8')).decode('utf-8')
    except Exception as e:
        print(f"Decryption error (Frontend): {e}")
        return None