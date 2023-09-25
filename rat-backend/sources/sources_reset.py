"""Class to reset failured scraping jobs"""
#load custom libs
from libs.lib_db import *
from libs.lib_logger import *
from libs.lib_helper import *

#load required libs
from datetime import datetime
import json
import os
import inspect

class SourcesReset:

    """Sources_Reset Object"""
    args: list
    """The args for the controller to stop it
    XXXX
    """

    def __init__(self, db:object, logger:object):
        self = self
        self.db = db
        self.logger = logger

    def __del__(self):
        print('Sources Reset object destroyed')

    def reset(self, db:object):
        sources_pending = db.get_sources_pending()
        timestamp = datetime.now()
        for s in sources_pending:
            source_id = s[0]
            created_at = s[1]
            result_id = s[2]
            # Get interval between two timstamps as timedelta object
            diff = timestamp - created_at
            # Get interval between two timstamps in hours
            diff_in_hours = diff.total_seconds() / 3600



            if diff_in_hours > 0.2:
                print(source_id)
                log = "Reset \t source \t"+str(source_id)+"\t "
                logger.write_to_log(log)
                counter = db.get_source_counter_result(result_id)
                counter = counter + 1
                progress = 0
                created_at = datetime.now()
                db.reset_result_source(progress, counter, created_at, source_id)
                db.delete_source_pending(source_id, progress, created_at)



if __name__ == "__main__":

    logger = Logger()
    logger.write_to_log("Reset \t \t sources\t ")

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    path_db_cnf = currentdir+"/../config/config_db.ini"
    path_sources_cnf = currentdir+"/../config/config_sources.ini"

    helper = Helper()

    db_cnf = helper.file_to_dict(path_db_cnf)
    sources_cnf = helper.file_to_dict(path_sources_cnf)

    job_server = sources_cnf['job_server']
    refresh_time = sources_cnf['refresh_time']

    db = DB(db_cnf, job_server, refresh_time)

    sources_reset = SourcesReset(db, logger)
    sources_reset.reset(db)

    del logger
    del db
    del sources_reset
