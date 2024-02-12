"""
Helper class for various utility functions.

Methods:
    __init__: Initialize the Helper object.
    __del__: Destructor for the Helper object.
    file_to_dict: Read a JSON file and return its contents as a dictionary.

"""

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
        """
        Initialize the Helper object.
        """        
        self = self

    def __del__(self):
        """
        Destructor for the Helper object.
        """        
        print('Helper object destroyed')

    def file_to_dict(self, path):
        """
        Read a JSON file and return its contents as a dictionary.

        Args:
            path (str): Path to the JSON file.

        Returns:
            dict: Dictionary containing the contents of the JSON file.
        """        
        f = open(path, encoding="utf-8")
        dict = json.load(f)
        f.close()
        return dict
