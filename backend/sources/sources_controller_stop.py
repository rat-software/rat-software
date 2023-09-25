"""
Controller to start the Sources Scraper
"""

#load required libs
import threading
from subprocess import call
import psutil
import time
import os
import sys
import inspect

#load custom libs
from libs.lib_logger import *
from libs.lib_helper import *
from libs.lib_db import *

class SourcesController:

    """SourcesController"""
    args: list
    """The class has no args for the start function.
    \nThe args for the stop function are:
    \n<b>args[0]:list</b> = name of browser process (chrome, chromium, firefox)
    \n<b>db:object</b> = Database object
    """

    def __init__(self):
        self = self

    def __del__(self):
        """Destroy the sources controller"""
        print('Sources Controller object destroyed')

    def stop(self, args:list):
        """Method to stop the controller:
        \nThe method uses the psutil library to indentify specific scripts and browser instances.
        \n<b>It is recommended not to use the software on servers running other Python scripts or instances of web browsers.</b>
        """

        #Identify the python processes and web browser instances
        for proc in psutil.process_iter(attrs=['pid', 'name']):

            if ("python" in proc.info['name']):

                try:
                    if ("python.exe" in proc.info['name']):

                        proc.kill()
                except:
                    pass

                try:
                    if ("job_sources.py" in proc.info['name']) or ("job_sources.py" in proc.cmdline()):
                        proc.kill()
                except:
                    pass

                try:
                    if ("sources_scraper.py" in proc.info['name']) or ("sources_scraper.py" in proc.cmdline()):
                        proc.kill()
                except:
                    pass

                try:
                    if ("sources_reset.py" in proc.info['name']) or ("sources_reset.py" in proc.cmdline()):
                        proc.kill()
                except:
                    pass

                try:
                    if ("job_reset_sources.py" in proc.info['name']) or ("job_reset.py" in proc.cmdline()):
                        proc.kill()
                except:
                    pass

            try:
                for browser in args[0]:

                    if (browser in proc.info['name']) or (browser in proc.cmdline()):

                        proc.kill()
            except:
                pass

        #Use some artifical break before calling the functions to reset the entries in the database.
        time.sleep(60)
        db.reset()
    

if __name__ == "__main__":
    """Main call for the Sources Controller"""
    sources_controller = SourcesController()

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    if os.path.exists(currentdir + '/jobs/job_sources.py' ):
        workingdir = currentdir

    elif os.path.exists(parentdir + '/jobs/job_sources.py' ):
        workingdir = parentdir



    #Load all necessary config files to connect to the database and load the parameters for the sources scraper

    path_db_cnf = workingdir+"/config/config_db.ini"
    path_sources_cnf = workingdir+"/config/config_sources.ini"

    helper = Helper()

    db_cnf = helper.file_to_dict(path_db_cnf)
    sources_cnf = helper.file_to_dict(path_sources_cnf)

    job_server = sources_cnf['job_server']
    refresh_time = sources_cnf['refresh_time']

    db = DB(db_cnf, job_server, refresh_time)

    sources_controller.stop([["chromium", "chrome"], db])

    del helper
    del db
    del sources_controller
