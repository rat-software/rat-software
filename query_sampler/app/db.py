# Custom Library for all Database operations

# Import psycopg2 to communicate with the RAT Database
import psycopg2
from psycopg2.extras import execute_values
import psycopg2.extras
from datetime import datetime

# Import Pandas to generate the downloadable keyword ideas of a study
import pandas as pd
import warnings

# Suppress UserWarnings from Pandas
warnings.simplefilter(action='ignore', category=UserWarning)

# Credentials for the db access
database = "your_db"
user = "your_db_user"
password = "your_db_password"
host = "your_db_host"
port = "5432"

def get_studies():
    """
    Retrieve all studies from the database.
    
    Returns:
        list: A list of study records.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # Initialize the database cursor
    cur.execute("SELECT * FROM qs_study")  # Execute SQL query to fetch all studies
    conn.commit()
    studies = cur.fetchall()  # Fetch the results
    conn.close()  # Close the connection
    return studies  # Return the results

def insert_study(name):
    """
    Insert a new study into the database.
    
    Args:
        name (str): The name of the study.
    
    Returns:
        tuple: The ID of the newly created study.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    created_at = datetime.now()  # Get the current timestamp
    cur.execute("INSERT INTO qs_study (name, created_at) VALUES (%s, %s) RETURNING id;", (name, created_at))
    conn.commit()
    lastrowid = cur.fetchone()  # Fetch the ID of the newly created study
    conn.close()
    return lastrowid

def get_study(id):
    """
    Retrieve a specific study by its ID.
    
    Args:
        id (int): The ID of the study to retrieve.
    
    Returns:
        dict: The study record.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM qs_study WHERE qs_study.id = %s;", (id,))
    conn.commit()
    study = cur.fetchone()  # Fetch the study record
    conn.close()
    return study

def get_regions():
    """
    Retrieve all regions from the database for the form in forms.py.
    
    Returns:
        list: A list of region records.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT name, criterion_id FROM qs_geotarget WHERE target_type = 'Country' ORDER BY name ASC")
    conn.commit()
    regions = cur.fetchall()  # Fetch all regions
    conn.close()
    return regions

def get_languages():
    """
    Retrieve all languages from the database for the form in forms.py.
    
    Returns:
        list: A list of language records.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT name, criterion_id FROM qs_language_code ORDER BY name ASC")
    conn.commit()
    languages = cur.fetchall()  # Fetch all languages
    conn.close()
    return languages

def get_keywords(id):
    """
    Retrieve the keyword set for a specific study.
    
    Args:
        id (int): The ID of the study for which to retrieve keywords.
    
    Returns:
        list: A list of keyword records.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT keyword, qs_language_code.name AS language, qs_geotarget.name AS region, qs_language_code_criterion_id AS language_criterion_id, qs_geotarget_criterion_id AS region_criterion_id, qs_keyword.id AS keyword_id FROM qs_keyword, qs_language_code, qs_geotarget WHERE qs_study_id = %s AND qs_language_code_criterion_id = qs_language_code.criterion_id AND qs_geotarget_criterion_id = qs_geotarget.criterion_id ORDER BY qs_keyword.id;", (id,))
    conn.commit()
    keywords = cur.fetchall()  # Fetch all keywords
    conn.close()
    return keywords

def get_keyword_ideas(id):
    """
    Retrieve all generated keyword ideas for a specific study.
    
    Args:
        id (int): The ID of the study for which to retrieve keyword ideas.
    
    Returns:
        list: A list of keyword idea records.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM qs_keyword_idea WHERE qs_study_id = %s;", (id,))
    conn.commit()
    keywords = cur.fetchall()  # Fetch all keyword ideas
    conn.close()
    return keywords

def insert_keyword(study_id, region, language, keyword):
    """
    Insert a new keyword into the database.
    
    Args:
        study_id (int): The ID of the study to which the keyword belongs.
        region (int): The region criterion ID.
        language (int): The language criterion ID.
        keyword (str): The keyword to insert.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    created_at = datetime.now()  # Get the current timestamp
    cur.execute("INSERT INTO qs_keyword (qs_study_id, qs_geotarget_criterion_id, qs_language_code_criterion_id, keyword, created_at) VALUES (%s, %s, %s, %s, %s);", (study_id, region, language, keyword, created_at))
    conn.commit()
    conn.close()

def check_keyword(study_id, region, language, keyword):
    """
    Check if a keyword already exists to prevent duplicates.
    
    Args:
        study_id (int): The ID of the study to which the keyword belongs.
        region (int): The region criterion ID.
        language (int): The language criterion ID.
        keyword (str): The keyword to check.
    
    Returns:
        list: A list of existing keyword records.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM qs_keyword WHERE qs_study_id = %s AND qs_geotarget_criterion_id = %s AND qs_language_code_criterion_id = %s AND keyword = %s AND status = 0;", (study_id, region, language, keyword))
    conn.commit()
    keywords = cur.fetchall()  # Fetch existing keywords
    conn.close()
    return keywords

def get_keyword_status_study(study_id):
    """
    Check the status of keyword operations for a specific study.
    
    Args:
        study_id (int): The ID of the study for which to check the status.
    
    Returns:
        dict: The status record of the study.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM qs_keyword WHERE qs_study_id = %s AND status = 0;", (study_id,))
    conn.commit()
    status = cur.fetchone()  # Fetch the status record
    conn.close()
    return status

def get_keyword_status(keyword_id, status):
    """
    Check the status of a specific keyword operation.
    
    Args:
        keyword_id (int): The ID of the keyword.
        status (int): The status to check.
    
    Returns:
        dict: The status record of the keyword.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM qs_keyword WHERE qs_keyword.id = %s AND status = %s;", (keyword_id, status))
    conn.commit()
    status = cur.fetchone()  # Fetch the status record
    conn.close()
    return status

def update_keyword_status(status, keyword_id):
    """
    Update the status of a specific keyword.
    
    Args:
        status (int): The new status of the keyword.
        keyword_id (int): The ID of the keyword to update.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("UPDATE qs_keyword SET status=%s WHERE qs_keyword.id = %s", (status, keyword_id))
    conn.commit()
    conn.close()

def insert_keyword_idea(study_id, keyword_id, keyword_idea, avg_monthly_searches, competition):
    """
    Insert a generated keyword idea into the database.
    
    Args:
        study_id (int): The ID of the study associated with the keyword idea.
        keyword_id (int): The ID of the keyword.
        keyword_idea (str): The generated keyword idea.
        avg_monthly_searches (int): The average number of monthly searches for the keyword idea.
        competition (float): The competition level for the keyword idea.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    created_at = datetime.now()  # Get the current timestamp
    cur.execute("INSERT INTO qs_keyword_idea (qs_study_id, qs_keyword_id, keyword_idea, avg_monthly_searches, competition, created_at) VALUES (%s, %s, %s, %s, %s, %s);", (study_id, keyword_id, keyword_idea, avg_monthly_searches, competition, created_at))
    conn.commit()
    conn.close()

def select_keywords_ideas(study_id):
    """
    Prepare the keyword ideas for a specific study and save them as a Pandas DataFrame.
    
    Args:
        study_id (int): The ID of the study for which to prepare keyword ideas.
    
    Returns:
        DataFrame: A Pandas DataFrame containing the keyword ideas.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)  # Connection to the database
    with conn.cursor() as cursor:
        # Query and import as DataFrame
        df = pd.read_sql("SELECT qs_keyword_idea.id, keyword, keyword_idea, avg_monthly_searches, competition, qs_keyword_idea.created_at, qs_language_code.name AS language, qs_geotarget.name AS country FROM qs_keyword, qs_keyword_idea, qs_language_code, qs_geotarget WHERE qs_keyword_id = qs_keyword.id AND qs_keyword_idea.qs_study_id = {} AND qs_language_code.criterion_id = qs_language_code_criterion_id AND qs_geotarget.criterion_id = qs_geotarget_criterion_id ORDER BY qs_keyword_idea ASC;".format(study_id), conn)
        # Drop rows with missing values
        df = df.dropna(axis=0)
        
        conn.commit()
        conn.close()
    
    return df
