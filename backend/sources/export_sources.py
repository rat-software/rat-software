#Export classifier results from a study "python export_classifier_results.py [study_id]"

import os
import sys
import inspect

import pytest

import json

from pathlib import Path

import pandas as pd

import base64

import uuid #used to generate random file names

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
backenddir = str(Path(parentdir).parents[0])

sys.path.insert(0, parentdir)

study = str(sys.argv[1])

print(study)

from libs.lib_db import *

from libs.lib_helper import *

helper = Helper()

path_db_cnf = parentdir+"/config/config_db.ini"
f = open(path_db_cnf, encoding="utf-8")
db_cnf = json.load(f)
f.close()
print(db_cnf)

#folder to store the interim results
html_folder = 'export_sources/' + str(study) + "/html/"
png_folder = "export_sources/"  + str(study) + "/png/"

try:
    os.makedirs(html_folder)
except FileExistsError:
    # directory already exists
    pass

try:
    os.makedirs(png_folder)
except FileExistsError:
    # directory already exists
    pass

db = DB(db_cnf, 'export_job', 48) 


conn = DB.connect_to_db(db)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
sql = ""
cur.execute("SELECT result from result_source, result where result_source.result = result.id and study = %s and result_source.progress = 1 ORDER BY result ASC", (study,))
results = cur.fetchall()
conn.close()

for r in results:
    result = r[0]

    print(result)

    html_file = html_folder + str(result) + ".html"

    png_file = png_folder + str(result) + ".png"

    try:
        if not os.path.isfile(html_file):
            conn = DB.connect_to_db(db)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            sql = ""
            cur.execute("SELECT code from result_source, source where result_source.source = source.id and result_source.result = %s", (result,))
            row = cur.fetchone()
            code = row[0]
            conn.close()

            conn = DB.connect_to_db(db)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            sql = ""
            cur.execute("SELECT bin from result_source, source where result_source.source = source.id and result_source.result = %s", (result,))
            row = cur.fetchone()
            png = row[0]
            conn.close()       

            decoded_code = helper.decode_code(code)

            if not os.path.isfile(html_file):
                with open(html_file,'w+', errors="ignore") as f:
                    f.write(decoded_code)
                f.close()

            else:
                print("html file exists already")

            

            base64_string = str(bytes(png))

            base64_string = base64_string.replace("b'", "")

            base64_string = base64_string.replace("'", "")

            png_image = base64.b64decode(base64_string)       

            png = bytes(png).decode('ascii')

            bytes_base64 = png.encode()
            png_image = base64.urlsafe_b64decode(bytes_base64)

            if not os.path.isfile(png_file):
                with open(png_file,'wb+') as f:
                    f.write(png_image)
                f.close()

            else:
                print("png file exists already")
        else:
            print("already exported!")                

    except Exception as e:
        print(str(e))
        pass





        