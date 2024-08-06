import os
import sys
import inspect
import json
import base64

def export_sources(study):
    """
    Export sources from a study and write the html files and screenshots to a folder /export_sources/[study_id]/html and /export_sources/[study_id]/png.

    Args:
        study: The study ID for which sources are being exported.

    Returns:
        None
    """

    # Get the current directory and parent directory
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0, parentdir)  # Insert parent directory into system path

    # Load database configuration from a file
    path_db_cnf = os.path.join(parentdir, "config", "config_db.ini")
    with open(path_db_cnf, encoding="utf-8") as f:
        db_cnf = json.load(f)

    # Create folders for HTML and PNG files
    html_folder = os.path.join('export_sources', str(study), "html")
    png_folder = os.path.join('export_sources', str(study), "png")
    os.makedirs(html_folder, exist_ok=True)  # Create HTML folder if it doesn't exist
    os.makedirs(png_folder, exist_ok=True)  # Create PNG folder if it doesn't exist

    # Connect to the database
    db = DB(db_cnf, 'export_job', 48)
    conn = DB.connect_to_db(db)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Query to get results for the given study
    cur.execute(
        "SELECT result from result_source, result where result_source.result = result.id and study = %s and result_source.progress = 1 ORDER BY result ASC",
        (study,))
    results = cur.fetchall()
    conn.close()

    # Initialize counter for results
    counter = len(results)
    for r in results:
        counter -= 1
        print(counter)  # Print remaining count
        result = r[0]
        html_file = os.path.join(html_folder, f"{result}.html")
        png_file = os.path.join(png_folder, f"{result}.png")

        # Skip if files already exist
        if os.path.isfile(html_file) and os.path.isfile(png_file):
            print("already exported!")
            continue

        # Reconnect to the database for each result
        conn = DB.connect_to_db(db)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT code, bin from result_source, source where result_source.source = source.id and result_source.result = %s",
            (result,))
        row = cur.fetchone()
        conn.close()

        code, png = row[0], row[1]
        decoded_code = helper.decode_code(code)  # Decode the source code

        # Write HTML file if it doesn't exist
        if not os.path.isfile(html_file):
            with open(html_file, 'w+', errors="ignore") as f:
                f.write(decoded_code)

        # Process and decode PNG image
        base64_string = str(bytes(png))
        base64_string = base64_string.replace("b'", "").replace("'", "")
        png_image = base64.b64decode(base64_string)

        png = bytes(png).decode('ascii')
        bytes_base64 = png.encode()
        png_image = base64.urlsafe_b64decode(bytes_base64)

        # Write PNG file if it doesn't exist
        if not os.path.isfile(png_file):
            with open(png_file, 'wb+') as f:
                f.write(png_image)

if __name__ == "__main__":
    try:
        # Import necessary libraries from the project
        from libs.lib_db_results import *
        from libs.lib_helper import *

        # Get study ID from command-line arguments and run export_sources
        study = str(sys.argv[1])
        export_sources(study)
    except Exception as e:
        # Print error message and usage instructions
        print(e)
        print("To export the results type: python export_sources.py [study_id]")
