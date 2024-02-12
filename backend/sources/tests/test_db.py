#Simple Test for the database connection
#todo: writing pytests for all single tests

import os
import sys
import inspect

import pytest

import json

from pathlib import Path

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
backenddir = str(Path(parentdir).parents[0])

sys.path.insert(0, parentdir)

from libs.lib_db import *

def test_db_connection():
    
    path_db_cnf = backenddir+"/config/config_db.ini"
    f = open(path_db_cnf, encoding="utf-8")
    db_cnf = json.load(f)
    f.close()

    db = DB(db_cnf, "0", 0) 
    db_connection = db.check_db_connection()
    assert db_connection == True,"Could not connect to database; test failed; Please check your database credintials at /config/config_db.ini or install the PostgreSQL-Database for the application."

