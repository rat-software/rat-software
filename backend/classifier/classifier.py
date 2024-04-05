"""
Class for loading and running classifiers.

Methods:
    load_classifier: Load and run classifiers.

Args:
    classifiers (list): List of classifiers.
    db (object): Database object.
    helper (object): Helper object.

"""

import importlib
from pathlib import Path
from libs.lib_helper import Helper
from libs.lib_db import DB

class Classifier:

    def load_classifier(self, classifiers, db, helper):
        """        
        Load and run classifiers.
        """        
        for c in classifiers:
            classifier_id = c['id']
            classifier_name = c['name']
            mod_folder = f"classifiers.{classifier_name}.{classifier_name}"
            module = importlib.import_module(mod_folder)
            module.main(classifier_id, db, helper)

def main():
    helper = Helper()   

    currentdir = Path(__file__).resolve().parent

    path_db_cnf = currentdir / ".." / "config" / "config_db.ini"
    path_sources_cnf = currentdir / ".." / "config" / "config_sources.ini"

    db_cnf = helper.file_to_dict(path_db_cnf)
    sources_cnf = helper.file_to_dict(path_sources_cnf)

    db = DB(db_cnf)

    classifiers = db.get_classifiers()

    classifier = Classifier()

    classifier.load_classifier(classifiers, db, helper)

if __name__ == "__main__":
    main()
