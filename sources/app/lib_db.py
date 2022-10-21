import psycopg2
from psycopg2.extras import execute_values
import json
import sys
import random
import time

import math

min = -2147483647

import json

def file_to_dict(path):
    f = open(path, encoding="utf-8")
    dict = json.load(f)
    f.close()
    return dict

sources_cnf = file_to_dict("config_sources.ini")

job_server = sources_cnf['job_server']


from datetime import datetime

def file_to_dict(path):
    f = open(path, encoding="utf-8")
    dict = json.load(f)
    f.close()
    return dict

sources_cnf = file_to_dict("config_sources.ini")

db_cnf = file_to_dict("config_db.ini")

def connect_to_db(db_cnf):
    conn = psycopg2.connect(**db_cnf)
    return conn

def update_result_source(source_placeholder, result_id):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("Update result SET source=%s WHERE id = %s", (source_placeholder, result_id))
    conn.commit()
    conn.close()


def get_sources():
    #todo function to calculate the random random_percentage
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "SELECT count(result.id) FROM source RIGHT JOIN result ON source.id = result.source WHERE source.id is NULL"
    cur.execute(sql)
    conn.commit()
    sources_counter = cur.fetchone()
    sources_counter = sources_counter[0]
    conn.close()

    if sources_counter > 100:
        random_percentage = 30

    else:
        random_percentage = 80

    if sources_counter > 1000:
        random_percentage = 1

    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "SELECT result.id, result.url FROM source RIGHT JOIN result TABLESAMPLE SYSTEM("+str(random_percentage)+")  ON source.id = result.source WHERE source.id is NULL ORDER BY result.created_at, result.id LIMIT 5"
    cur.execute(sql)
    conn.commit()
    sources = cur.fetchall()
    conn.close()

    source_placeholder = random.randint(min, -5)
    sources_list = []
    for s in sources:
        result_id = s[0]
        result_url = s[1]
        sources_list.append([result_id, result_url])
        update_result_source(source_placeholder, result_id)

    return sources_list

def get_sources_pending(job_server):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, created_at from source where progress = 2 and job_server =%s",(job_server,))
    conn.commit()
    sources_pending = cur.fetchall()
    conn.close()
    return sources_pending

def get_source_check(url):

    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, created_at from source where progress = 1 and url=%s ORDER by created_at DESC",(url,))
    conn.commit()
    sc = cur.fetchone()
    conn.close()

    if sc:
        timestamp = datetime.now()

        source_id = sc[0]
        created_at = sc[1]
        # Get interval between two timstamps as timedelta object
        diff = timestamp - created_at
        # Get interval between two timstamps in hours
        diff_in_hours = diff.total_seconds() / 3600

        if diff_in_hours < sources_cnf['refresh_time']:
            return source_id
    else:
        return False

def get_source_check_by_result_id(result_id):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id from source where result = %s",(result_id,))
    conn.commit()
    scr = cur.fetchone()
    conn.close()
    return scr

def get_source_check_final_url(final_url):

    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, created_at from source where progress = 1 and final_url=%s ORDER by created_at DESC",(final_url,))
    conn.commit()
    sc = cur.fetchone()
    conn.close()

    if sc:
        timestamp = datetime.now()

        source_id = sc[0]
        created_at = sc[1]
        # Get interval between two timstamps as timedelta object
        diff = timestamp - created_at
        # Get interval between two timstamps in hours
        diff_in_hours = diff.total_seconds() / 3600

        if diff_in_hours < sources_cnf['refresh_time']:
            return source_id
    else:
        return False



def get_source_content(source_id):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT code, bin, content_type, error_code, status_code, final_url, result from source where id=%s ORDER by created_at DESC",(source_id,))
    conn.commit()
    sc = cur.fetchone()
    conn.close()
    return sc


def get_result_content(source_id):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT ip, main, final_url FROM result where source=%s",(source_id,))
    conn.commit()
    rc = cur.fetchone()
    conn.close()
    return rc

def insert_source(url, progress, created_at, result_id, job_server):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("INSERT INTO source (url, progress, created_at, result, job_server) VALUES (%s, %s, %s, %s, %s)  RETURNING id;", (url, progress, created_at, result_id, job_server))
    conn.commit()
    lastrowid = cur.fetchone()
    conn.close()
    return lastrowid

def check_progress(url, result_id):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT source.id FROM source WHERE source.url = %s AND source.result = %s AND progress = 2", (url, result_id))
    conn.commit()
    check_progress = cur.fetchall()
    conn.close()
    if check_progress:
        return True
    else:
        return False

def update_source(source_id, code, bin, progress, content_type, error_code, status_code, final_url, created_at):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("Update source SET code=%s, bin=%s, progress=%s, content_type=%s, error_code=%s, status_code=%s, final_url = %s, created_at=%s WHERE id = %s", (code, bin, progress, content_type, error_code, status_code, final_url, created_at, source_id))
    conn.commit()
    conn.close()

def update_result(result_id, source_id, ip, main, final_url):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("Update result SET source=%s, ip=%s, main=%s, final_url=%s WHERE id = %s", (source_id, ip, main, final_url, result_id))
    conn.commit()
    conn.close()

def delete_source_pending(source_id):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("DELETE from source WHERE id = %s", (source_id,))
    conn.commit()
    conn.close()

def reset_result(source_id):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("Update result SET source = NULL WHERE source = %s", (source_id,))
    conn.commit()
    conn.close()

def reset_results():
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("Update result SET source = NULL WHERE source < 0")
    conn.commit()
    conn.close()

def delete_source(source_id):
    conn = connect_to_db(db_cnf)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("DELETE from source where id = %s", (source_id,))
    conn.commit()
    conn.close()


def reset(job_server):
    sources_pending = get_sources_pending(job_server)
    reset_results()
    for sources_pending in sources_pending:
        source_id = sources_pending[0]
        delete_source_pending(source_id)
        reset_result(source_id)

def test_connection():
    try:
        conn = connect_to_db(db_cnf)
        conn.close()
        return True
    except:
        return False
