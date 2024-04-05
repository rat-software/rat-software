#test script to check if Seleniium works correctly

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

from libs.lib_sources import *

# def test_sources_scraper():
    
#     def check_sources_by_error_code():
#         sources = Sources()
#         url = "https://stahlschlag.de"
     
#         result_dict = sources.save_code(url)

#         error_codes = result_dict["error_codes"]

#         print(result_dict)
      
#         if len(error_codes) > 0:
#             print(error_codes)
#             return False
#         else:
#             return True

#     assert check_sources_by_error_code() == True,"Could not scrape the URL; test failed;"

# test_sources_scraper()

#botc=https://nowsecure.nl/#relaxss

sources = Sources()
url = "https://nowsecure.nl/#relax"
result_dict = sources.save_code(url)
print(result_dict)

