#Simple Test for the database connection
#todo: writing pytests for all single tests

import os
import sys
import inspect

import pytest

import json

import psycopg2

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
path_db_cnf = parentdir+"/config/config_db.ini"
f = open(path_db_cnf, encoding="utf-8")
db_cnf = json.load(f)
f.close()

def test_db_connection():

    def check_db_connection():
        try:
            conn =  psycopg2.connect(**db_cnf)
            conn.close()
            return True
        except:
            return False
        
    db_connection = check_db_connection()
    assert db_connection == True,"Could not connect to database; test failed; Please check your database credintials at /config/config_db.ini or install the PostgreSQL-Database for the application."
