import sys
import json
import csv
import pandas as pd
from pathlib import Path
from libs.lib_db_results import *
import psycopg2

def export_results(study):
    """
    Export results from a study and write them to a CSV file [study_id]_results.csv.

    Args:
        study (str): The study ID for which results are being exported.

    Returns:
        None
    """

    # Get the current directory and parent directory
    currentdir = Path(__file__).resolve().parent
    parentdir = currentdir.parent

    # Load database configuration from a file
    path_db_cnf = parentdir / "config" / "config_db.ini"
    with path_db_cnf.open(encoding="utf-8") as f:
        db_cnf = json.load(f)

    # Connect to the database and fetch results
    with psycopg2.connect(**db_cnf) as conn:
        df = pd.read_sql(
            """
            SELECT result.id, result.created_at, result.url, result.main, searchengine.name, 
                   result.ip, result.position, result.title, result.description, query.query 
            FROM result
            JOIN query ON result.query = query.id
            JOIN scraper ON result.scraper = scraper.id
            JOIN searchengine ON scraper.searchengine = searchengine.id
            WHERE result.study = %s
            ORDER BY result.query, searchengine.name, result.position
            """, 
            conn, 
            params=[study]
        )
        df = df.dropna(axis=0)  # Drop rows with any missing values
        csv_file = f"{study}_results.csv"  # Generate CSV file name
        df.to_csv(csv_file, index=False, encoding='utf-8-sig', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)  # Save DataFrame to CSV

if __name__ == "__main__":
    try:
        study = str(sys.argv[1])  # Get study ID from command-line arguments
        export_results(study)  # Call the export_results function
    except IndexError:
        # Print error message and usage instructions if no study ID is provided
        print("To export the results type: python export_results.py [study_id]")
