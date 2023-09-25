import json

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
