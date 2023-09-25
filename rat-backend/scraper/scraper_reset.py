
from libs.lib_helper import *
from libs.lib_db import *

from datetime import datetime

import json

import os
import inspect

class ScraperReset:

    """Sources_Reset_Controller Scraper"""
    args: list
    """The args for the controller to stop it
    \nparam: args[0]:list = name of browser process (chrome, chromium, firefox)
    \nparam: db:object = Database object
    """

    def __init__(self, db):
        self = self
        self.db = db

    def __del__(self):
        print('Sources Reset object destroyed')

    def reset(self, db):
        db.reset()

if __name__ == "__main__":

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    db_cnf = currentdir+"/../config/config_db.ini"
     
    helper = Helper()

    db_cnf = helper.file_to_dict(db_cnf)

    db = DB(db_cnf)

    scraper_reset = ScraperReset(db)
    scraper_reset.reset(db)

    del db
    del scraper_reset
