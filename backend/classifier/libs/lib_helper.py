import json
import base64
from bs4 import BeautifulSoup

class Helper:
    """
    A utility class providing various helper functions for operations like file reading,
    base64 decoding, and picture decoding.

    Methods:
        __del__(): Destructor for the Helper object.
        file_to_dict(path): Reads a JSON file from the given path and returns its contents as a dictionary.
        decode_code(value): Decodes a base64-encoded string and returns the decoded HTML content.
        decode_picture(value): Decodes a picture value and returns the decoded picture as a string.

    Example:
        helper = Helper()
        file_dict = helper.file_to_dict('path/to/file.json')
        decoded_code = helper.decode_code(base64_encoded_string)
        decoded_picture = helper.decode_picture(picture_value)
        del helper
    """

    def __del__(self):
        """
        Destructor for the Helper object.

        This method is automatically called when the object is about to be destroyed.
        It prints a message indicating that the Helper object has been destroyed.
        """
        print('Helper object destroyed')

    def file_to_dict(self, path):
        """
        Read a JSON file from the specified path and return its contents as a dictionary.

        Args:
            path (str): The file path to read the JSON data from.

        Returns:
            dict: A dictionary containing the parsed JSON data from the file.

        Raises:
            FileNotFoundError: If the file specified by `path` does not exist.
            json.JSONDecodeError: If the file content is not valid JSON.
        """
        with open(path, encoding="utf-8") as f:
            # Load the content of the file as JSON and return it as a dictionary
            return json.load(f)

    def decode_code(self, value):
        """
        Decode a base64-encoded string and return the decoded HTML content.

        Args:
            value (str): A base64-encoded string to be decoded.

        Returns:
            str: The decoded HTML content as a string. If decoding fails, returns "decoding error".
        """
        try:
            # Decode the base64-encoded string
            code_decoded = base64.b64decode(value)
            # Convert the decoded bytes to a BeautifulSoup object and then to a string for HTML parsing
            return str(BeautifulSoup(code_decoded, "html.parser"))
        except Exception:
            # Return an error message if decoding fails
            return "decoding error"

    def decode_picture(self, value):
        """
        Decode a picture value and return the decoded picture as a string.

        Args:
            value: The picture value to be decoded. It is expected to have a `tobytes` method.

        Returns:
            str: The decoded picture data as a string.

        Note:
            This method assumes that `value` has a method `tobytes` that returns byte data which
            can be decoded using ASCII encoding.
        """
        # Convert the picture value to bytes and decode the bytes to a string using ASCII encoding
        return value.tobytes().decode('ascii')
