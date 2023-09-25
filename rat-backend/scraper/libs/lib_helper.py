import json
import base64
from bs4 import BeautifulSoup

from urllib import request
from urllib.parse import urlsplit
from urllib.parse import urlparse
import urllib.parse
import socket

import os
import inspect

class Helper:

    def __init__(self):
        self = self

    def __del__(self):
        print('Helper object destroyed')

    def file_to_dict(self, path):
        f = open(path, encoding="utf-8")
        dict = json.load(f)
        f.close()
        return dict
