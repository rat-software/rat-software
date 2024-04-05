#Export classifier results from a study "python export_classifier_results.py [study_id]"

import os
import sys
import inspect

import pytest

import json

from pathlib import Path

import pandas as pd

import uuid #used to generate random file names

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
backenddir = str(Path(parentdir).parents[0])

sys.path.insert(0, parentdir)

study = str(sys.argv[1])

from libs.lib_db import *

path_db_cnf = parentdir+"/config/config_db.ini"
f = open(path_db_cnf, encoding="utf-8")
db_cnf = json.load(f)
f.close()
print(db_cnf)

#folder to store the interim results
tmp = 'tmp/'

db = DB(db_cnf, "0", 0) 

db.deleteClassifierDuplicates()

conn = DB.connect_to_db(db)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
sql = ""
cur.execute("SELECT count(distinct(result)) from classifier_result, result where classifier_result.result = result.id and study = %s", (study))
rows = cur.fetchall()
conn.close()

#Get classifier indicators
conn = DB.connect_to_db(db)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cur.execute("SELECT DISTINCT (indicator) FROM classifier_indicator ORDER BY indicator ASC")
indicators = cur.fetchall()
conn.close()

# Get classifier results
conn = DB.connect_to_db(db)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
sql = "SELECT DISTINCT (result) FROM classifier_indicator ORDER BY result ASC"
cur.execute("SELECT DISTINCT (result) FROM classifier_indicator, result where classifier_indicator.result = result.id and study = %s ORDER BY result ASC", (study))
results = cur.fetchall()
conn.close()

csv_file = str(uuid.uuid1())+".csv"

results_csv = {}

if os.path.exists(csv_file):
    os.remove(csv_file)

x = 0

for r in results:
    result = r[0]
    res_dict = {"result": result}
  
    for i in indicators:
        indicator = i[0]
        conn = DB.connect_to_db(db)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT classifier_result.value, classifier_indicator.result, indicator, classifier_indicator.value, result.url, result.position, query.query FROM classifier_indicator, classifier_result, result, query WHERE classifier_result.result = classifier_indicator.result AND indicator = %s AND classifier_indicator.result = %s AND classifier_indicator.result = result.id AND query.id = result.query GROUP BY classifier_result.value, classifier_indicator.result, indicator, classifier_indicator.value, result.url, result.position, query.query", (indicator,result))
        row = cur.fetchone()
        class_res = row[0]
        ind = row[2]
        val = row[3]
        url = row[4]
        position = row[5]
        query = row[6]
        conn.close
        ind_val_dict = {"query":query,"url":url, "position": position, "classifier_result":class_res, ind:val}
        res_dict.update(ind_val_dict)
   
    if x == 0:
        csv_header = ""

        for k in res_dict:
            csv_header = csv_header+k+"\t"
        
        with open(csv_file,'w+') as f:
            f.write(csv_header)
        f.close()

    values = ""

    for v in res_dict.values():
        values = values+str(v)+"\t"

    print(values)
    
    with open(csv_file,'a+') as f:
        f.write("\n"+values)
    f.close()       

    x = 1
        


