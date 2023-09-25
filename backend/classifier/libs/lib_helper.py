import json
import base64
from bs4 import BeautifulSoup


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

    def decode_code(self, value):

        try:
            code_decoded = base64.b64decode(value)
            code_decoded = BeautifulSoup(code_decoded, "html.parser")
            code_decoded = str(code_decoded)
        except:
            code_decoded = "decoding error"
        return code_decoded

    def decode_picture(self, value):
        picture = value.tobytes()
        picture = picture.decode('ascii')
        return picture
