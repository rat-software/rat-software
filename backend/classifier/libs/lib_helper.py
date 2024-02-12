"""
Helper

This class provides helper functions for various operations.

Methods:
    __init__(): Initializes the Helper object.
    __del__(): Destructor for the Helper object.
    file_to_dict(path): Reads a file and returns its contents as a dictionary.
    decode_code(value): Decodes a base64-encoded code and returns the decoded value.
    decode_picture(value): Decodes a picture value and returns the decoded picture.

Example:
    helper = Helper()
    file_dict = helper.file_to_dict(path)
    decoded_code = helper.decode_code(value)
    decoded_picture = helper.decode_picture(value)
    del helper
"""

import json
import base64
from bs4 import BeautifulSoup


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
        Read a file and return its contents as a dictionary.

        Args:
            path (str): The path to the file.

        Returns:
            dict: The contents of the file as a dictionary.
        """
        f = open(path, encoding="utf-8")
        dict = json.load(f)
        f.close()
        return dict

    def decode_code(self, value):
        """
        Decode a base64-encoded code and return the decoded value.

        Args:
            value (str): The base64-encoded value.

        Returns:
            str: The decoded value.
        """
        try:
            code_decoded = base64.b64decode(value)
            code_decoded = BeautifulSoup(code_decoded, "html.parser")
            code_decoded = str(code_decoded)
        except:
            code_decoded = "decoding error"
        return code_decoded

    def decode_picture(self, value):
        """
        Decode a picture value and return the decoded picture.

        Args:
            value: The picture value.

        Returns:
            str: The decoded picture.
        """
        picture = value.tobytes()
        picture = picture.decode('ascii')
        return picture
