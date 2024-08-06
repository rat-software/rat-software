import sys
import json
from pathlib import Path
import pandas as pd
import psycopg2.extras

def export_classifier_results(study_id, DB):

    """
    Export results from a study and write them to a CSV file [study_id]_classifier_results.csv.

    Args:
        study_id: The ID of the study to export results from.
        DB: The database connection object.

    Returns:
        None
    """    

    def fetch_query_results(query, params):
        with DB.connect_to_db(db) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()

    # Get classifier indicators
    indicators = fetch_query_results("SELECT DISTINCT (indicator) FROM classifier_indicator ORDER BY indicator ASC", ())

    # Get classifier results
    results = fetch_query_results("SELECT DISTINCT (result) FROM classifier_result, result WHERE classifier_result.result = result.id AND study = %s ORDER BY result ASC", (study,))

   
    csv_file = str(study + "_classifier_results.csv")
    results_csv = []

    if Path(csv_file).exists():
        Path(csv_file).unlink()

    counter = len(results)

    for r in results:
        # Decrease the counter to show how many results are left
        counter -=1
        print(counter)
        
        result = r[0]
        res_dict = {"result": result}

        for i in indicators:
            indicator = i[0]
            # Query to fetch data for a specific indicator and result
            query = """
            SELECT classifier_result.value, classifier_indicator.result, indicator, classifier_indicator.value, result.url, result.main, result.ip, result_source.source, result_source.created_at 
            FROM classifier_indicator
            JOIN classifier_result ON classifier_result.result = classifier_indicator.result
            JOIN result ON classifier_indicator.result = result.id
            JOIN result_source ON result_source.result = classifier_result.result
            WHERE indicator = %s AND classifier_indicator.result = %s
            GROUP BY classifier_result.value, classifier_indicator.result, indicator, classifier_indicator.value, result.url, result.main, result.ip, result_source.source, result_source.created_at
            """

            # Fetch query results for the current indicator and result
            row = fetch_query_results(query, (indicator, result))

            if row:
                row = row[0]
                class_res = row[0]
                ind = row[2]
                val = row[3]
                url = row[4]
                main = row[5]
                ip = str(row[6])
                source = str(row[7])
                created_at = row[8]
            else:
                # If no results found, fetch default values
                query = """
                SELECT classifier_result.value, classifier_result.result, result.url, result.main, result.ip, result_source.source, result_source.created_at 
                FROM classifier_result
                JOIN result ON classifier_result.result = result.id
                JOIN result_source ON result_source.result = classifier_result.result
                WHERE classifier_result.result = %s
                GROUP BY classifier_result.value, classifier_result.result, result.url, result.main, result.ip, result_source.source, result_source.created_at
                """
                row = fetch_query_results(query, (result,))
                row = row[0]
                class_res = row[0]
                ind = indicator
                val = "error"
                url = row[2]
                main = row[3]
                ip = str(row[4])
                source = str(row[5])
                created_at = row[6]

            # Create a dictionary with the fetched data and update the result dictionary
            ind_val_dict = {"url": url, "main": main, "source_id": source, "created_at": created_at, "ip": ip, "classifier_result": class_res, ind: val}
            res_dict.update(ind_val_dict)

    
        results_csv.append(res_dict)

    # Create DataFrame and save to CSV
    df = pd.DataFrame(results_csv)
    df.to_csv(csv_file, sep='\t', index=False)

if __name__ == "__main__":
    # Directory management
    parentdir = Path(__file__).resolve().parent.parent
    backenddir = parentdir.parent


    from libs.lib_db_classifier import DB

    # Read JSON configuration
    path_db_cnf = parentdir / "config/config_db.ini"
    with open(path_db_cnf, encoding="utf-8") as f:
        db_cnf = json.load(f)    

    # Database operations
    db = DB(db_cnf)
    db.deleteClassifierDuplicates()

    study = str(sys.argv[1])

    export_classifier_results(study, DB)