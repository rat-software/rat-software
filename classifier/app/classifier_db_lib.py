import psycopg2
from psycopg2.extras import execute_values
import json

from datetime import datetime

import base64

from bs4 import BeautifulSoup

def file_to_dict(path):
    f = open(path, encoding="utf-8")
    dict = json.load(f)
    f.close()
    return dict

db_cnf = file_to_dict("config_db.ini")

def connect_to_db(db_cnf):
    conn = psycopg2.connect(**db_cnf)
    return conn

def get_values(classifier):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT result.id, result.url, result.main, result.position, searchengine.name AS searchengine, result.title, result.description, result.ip, result.source, source.code, source.bin, source.content_type, source.error_code, source.status_code, source.final_url, query.query FROM source, result, query, scraper, searchengine WHERE source.id = result.source AND result.scraper = scraper.id AND scraper.searchengine = searchengine.id AND query.id = result.query AND source.progress = 1 AND result.id NOT IN (SELECT classificationresult.result FROM classificationresult where classificationresult.class = %s) ORDER BY result.created_at, result.id" , (classifier,))
    conn.commit()
    values = cur.fetchall()
    conn.close()
    return values

def decode_code(value):
    try:
        code_decoded = base64.b64decode(value)
        code_decoded = BeautifulSoup(code_decoded, "html.parser")
        code_decoded = str(code_decoded)
    except:
        code_decoded = "decoding error"
    return code_decoded

def decode_picture(value):
    picture = value.tobytes()
    picture = picture.decode('ascii')
    return picture


def insert_indicator(indicator, value, classifier, result):
    try:
        created_at = datetime.now()
        conn = connect_to_db(db_cnf)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO classificationindicator (indicator, value, class, result, created_at) VALUES (%s, %s, %s, %s, %s);", (indicator, value, classifier, result, created_at))
        conn.commit()
        conn.close()
    except:
        pass

def insert_classification_result(classifier, value, result):
    try:
        created_at = datetime.now()
        conn = connect_to_db(db_cnf)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO classificationresult (class, value, result, created_at) VALUES (%s, %s, %s, %s);", (classifier, value, result, created_at))
        conn.commit()
        conn.close()
    except:
        pass

def update_classification_result(classifier, value, result):
    try:
        created_at = datetime.now()
        conn = connect_to_db(db_cnf)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("UPDATE classificationresult SET class=%s, value=%s, created_at=%s WHERE result = %s", (classifier, value, created_at, result))
        conn.commit()
        conn.close()

    except:
        pass

def reset_classifiers(result):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("DELETE FROM classificationindicator WHERE result = %s", (result,))
    cur.execute("DELETE FROM classificationresult WHERE result = %s", (result,))
    cur.execute("DELETE FROM classificationresult WHERE value = 'in process'", (result,))
    conn.commit()
    conn.close()

def test_connection():
    try:
        conn = connect_to_db(db_cnf)
        conn.close()
        return True
    except:
        return False

def reset():
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT classificationindicator.result FROM classificationindicator, classificationresult WHERE classificationindicator.result NOT IN (SELECT classificationresult.result FROM classificationresult) GROUP BY classificationindicator.result")
    conn.commit()
    values = cur.fetchall()
    for v in values:
        result = v['result']
        reset_classifiers(result)
    conn.close()
