"""
Database and Storage Cleanup Utility.

This script identifies and removes 'orphan' files from the storage directory 
that are no longer referenced in the 'serp' or 'source' database tables.
"""

import os
from sqlalchemy import create_engine, text

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
# Database connection URI and local storage path
DB_URI = os.getenv('SQLALCHEMY_DATABASE_URI') # Your DB URI e. g. 'postgresql://user:password@ip/dbname'
STORAGE_FOLDER = os.getenv('STORAGE_FOLDER') # Define your STORAGE Folder on your web server
# ---------------------

def clean_orphans():
    """
    Scans the storage directory and compares contents with database records.
    Prompts the user to delete files that exist on disk but not in the DB.
    """
    print(f"Starting cleanup in: {STORAGE_FOLDER}")
    
    # Check if the storage directory exists before proceeding
    if not os.path.exists(STORAGE_FOLDER):
        print(f"ERROR: Directory {STORAGE_FOLDER} not found.")
        return

    try:
        # Establish database connection
        engine = create_engine(DB_URI)
        with engine.connect() as conn:
            # Fetch all registered file paths and normalize them to lowercase
            serp_res = conn.execute(text("SELECT file_path FROM serp WHERE file_path IS NOT NULL"))
            source_res = conn.execute(text("SELECT file_path FROM source WHERE file_path IS NOT NULL"))
            
            # Use a set for O(1) lookup efficiency during comparison
            db_files = {row[0].lower() for row in serp_res}
            db_files.update({row[0].lower() for row in source_res})
            
    except Exception as e:
        print(f"Database Error: {e}")
        return

    print(f"-> {len(db_files)} files registered in the database.")

    # Scan physical files on the storage drive
    physical_files = os.listdir(STORAGE_FOLDER)
    orphans = []

    for f in physical_files:
        # Ignore system files (like .DS_Store or .gitignore)
        if f.startswith('.'): 
            continue 
        
        # Comparison: Is the physical file (lowercase) MISSING from the DB set?
        if f.lower() not in db_files:
            orphans.append(f)

    # Exit if no orphans are found
    if not orphans:
        print("Everything is clean! No orphaned files found.")
        return

    # Report findings
    print(f"!!! {len(orphans)} ORPHANED FILES FOUND !!!")
    for o in orphans[:10]: # Show a preview of the first 10 files
        print(f" - {o}")

    # Interactive confirmation before deletion
    ans = input(f"\nDo you want to delete these {len(orphans)} files now? (y/n): ")
    if ans.lower() == 'y':
        count = 0
        for o in orphans:
            try:
                os.remove(os.path.join(STORAGE_FOLDER, o))
                count += 1
            except Exception:
                # Silently skip files that cannot be deleted (e.g., permission issues)
                pass
        print(f"Successfully deleted {count} files.")

if __name__ == "__main__":
    clean_orphans()