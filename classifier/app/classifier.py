import json
import importlib

print("Next \t \t Job\t ")

def file_to_dict(path):
    f = open(path, encoding="utf-8")
    dict = json.load(f)
    f.close()
    return dict

def load_classifier(classifier_cnf):
    for k, v in classifier_cnf.items():
        classifier = k
        for k, x in v.items():
            module = x
        mod_folder = classifier+"."+module
        module = importlib.import_module(mod_folder)
        module.main()

classifier_cnf = file_to_dict("config_classifier.ini")
load_classifier(classifier_cnf)
