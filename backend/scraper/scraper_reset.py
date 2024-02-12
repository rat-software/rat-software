"""
ScraperReset

This class represents a controller for resetting sources in the scraper.

Attributes:
    args (list): The args for the controller to stop it.
        args[0] (list): Name of browser process (chrome, chromium, firefox).
        args[1] (object): Database object.

Methods:
    __init__(db): Initializes the ScraperReset object.
    __del__(): Destructor for the ScraperReset object.
    reset(db): Resets the sources in the scraper.

Example:
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    db_cnf = currentdir+"/../config/config_db.ini"

    helper = Helper()

    db_cnf = helper.file_to_dict(db_cnf)

    db = DB(db_cnf)

    scraper_reset = ScraperReset(db)
    scraper_reset.reset(db)
    del scraper_reset
"""

from libs.lib_helper import *
from libs.lib_db import *

from datetime import datetime

import json

import os
import inspect

class ScraperReset:

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
