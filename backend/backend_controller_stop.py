import psutil
import time
import os
import sys
import inspect
import json

import psycopg2
from psycopg2.extras import execute_values

if __name__ == "__main__":
    
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    
    path_db_cnf = currentdir+"/config/config_db.ini"
    
    f = open(path_db_cnf, encoding="utf-8")
    db_conn = json.load(f)
    f.close()
    
    #stop all processes
    
    try:

        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            if proc.info['cmdline']:
                for c in proc.info['cmdline']:
                    if '--headless=new' in c:
                        print(proc.info['pid'])
                        proc.kill()
                        print(c)
                    if 'sources' in c:
                        if '.py' in c:
                            print(proc.info['pid'])
                            proc.kill()
                            print(c)
                    if 'classifier' in c:
                        if '.py' in c:
                            print(proc.info['pid'])
                            proc.kill()
                            print(c)
                    if 'scraper' in c:
                        if '.py' in c:
                            print(proc.info['pid'])
                            proc.kill()
                            print(c)

    except Exception as e:
        print("Doesnt work properly on a Windows machine")
        print(str(e))

    #update pending db jobs
def reset_classifiers(result):
    conn =  psycopg2.connect(**db_conn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("DELETE FROM classifier_indicator WHERE result = %s", (result,))
    cur.execute("DELETE FROM classifier_result WHERE result = %s", (result,))
    cur.execute("DELETE FROM classifier_result WHERE value = 'in process'", (result,))
    conn.commit()
    conn.close()


conn =  psycopg2.connect(**db_conn)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("SELECT classifier_indicator.result FROM classifier_indicator, classifier_result WHERE classifier_indicator.result NOT IN (SELECT classifier_result.result FROM classifier_result) GROUP BY classifier_indicator.result")
conn.commit()
values = cur.fetchall()
for v in values:
    result = v['result']
    reset_classifiers(result)
conn.close()

conn =  psycopg2.connect(**db_conn)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cur.execute("Update scraper SET progress=0 WHERE progress = -1 OR progress = 2")
conn.commit()
conn.close()

def get_sources_pending():
    """
    Get all pending sources (progress = 2)
    """
    conn =  psycopg2.connect(**db_conn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, created_at from source where progress = 2")
    conn.commit()
    sources_pending = cur.fetchall()
    conn.close()
    return sources_pending

def delete_source_pending(source_id):
    """
    Delete pending sources
    """
    conn =  psycopg2.connect(**db_conn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("DELETE from source WHERE id = %s", (source_id,))
    conn.commit()
    conn.close()

def reset_result_source(source_id):
    """
    Reset a source in result_source
    """
    conn =  psycopg2.connect(**db_conn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("DELETE from result_source WHERE source = %s", (source_id,))
    conn.commit()
    conn.close()

"""
Call reset when the sources_controller stops and delete pending sources
"""
sources_pending = get_sources_pending()

for sources_pending in sources_pending:
    source_id = sources_pending[0]
    reset_result_source(source_id)
    delete_source_pending(source_id)
