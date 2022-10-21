from lib_db import *
from lib_log import *

from datetime import datetime

import json

def file_to_dict(path):
    f = open(path, encoding="utf-8")
    dict = json.load(f)
    f.close()
    return dict

sources_cnf = file_to_dict("config_sources.ini")

job_server = sources_cnf['job_server']

write_to_log("Reset \t \t sources\t ")

sources_pending = get_sources_pending(job_server)

timestamp = datetime.now()

for s in sources_pending:
    source_id = s[0]
    created_at = s[1]
    # Get interval between two timstamps as timedelta object
    diff = timestamp - created_at
    # Get interval between two timstamps in hours
    diff_in_hours = diff.total_seconds() / 3600

    if diff_in_hours > 1:
        log = "Reset \t source \t"+str(source_id)+"\t "
        write_to_log(log)
        delete_source_pending(source_id)
        reset_result(source_id)
