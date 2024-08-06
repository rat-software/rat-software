import json
import base64
from bs4 import BeautifulSoup

class Helper:
    """
    A utility class for various helper functions related to file handling and decoding.
    """

    def __init__(self):
        """
        Initializes the Helper object. Currently, it does nothing special.
        """
        self = self

    def __del__(self):
        """
        Destructor for the Helper object.
        Prints a message indicating that the Helper object has been destroyed.
        """
        print('Helper object destroyed')

    def file_to_dict(self, path):
        """
        Reads a JSON file and converts its contents to a dictionary.

        Args:
            path (str): The path to the JSON file.

        Returns:
            dict: The dictionary representation of the JSON file's contents.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data

    def decode_code(self, code):
        """
        Decodes a base64 encoded string and parses it into a BeautifulSoup object for HTML parsing.

        Args:
            code (str): The base64 encoded string.

        Returns:
            str: The decoded HTML content as a string.
        """
        # Decode the base64 encoded string
        code_decoded = base64.b64decode(code)

        # Parse the decoded HTML content with BeautifulSoup
        soup = BeautifulSoup(code_decoded, "html.parser")

        # Convert BeautifulSoup object back to string
        code_decoded = str(soup)
        return code_decoded
