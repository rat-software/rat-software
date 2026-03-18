import json
import base64
from bs4 import BeautifulSoup

class Helper:
    """
    A utility class providing various helper functions for file handling and code decoding.
    """

    def __init__(self):
        """
        Initializes a Helper instance.
        """
        # Initialization logic can be added here if needed
        pass

    def __del__(self):
        """
        Destructor for the Helper class, which is called when an object is destroyed.
        """
        print('Helper object destroyed')

    def file_to_dict(self, path):
        """
        Reads a JSON file and converts its contents into a dictionary.

        Args:
            path (str): The file path to the JSON file.

        Returns:
            dict: The dictionary representation of the JSON file's contents.
        """
        # Open the JSON file for reading with UTF-8 encoding
        with open(path, encoding="utf-8") as f:
            # Load the JSON content into a dictionary
            data = json.load(f)
        
        return data

