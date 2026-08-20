import os
import inspect
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'libs')))
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(currentdir + "/libs/")
sys.path.append(currentdir + "/../")

from text_analyzer import *
from classifier import *

class ReadabilityScore(Classifier):
    """Handles Readability scoring logic using Text_Analyzer"""
    
    def __init__(self, classifier_id: int = None, db=None, job_server: str = None):
        super().__init__(classifier_id, db, job_server)

    def get_indicators(self, result, helper):
        """
        Lagert die Extraktion komplett an die Basisklasse aus.
        """
        clean_text, error_reason = self.extract_clean_text(result, helper)
        
        if error_reason:
            return {'excluded': True, 'reason': error_reason}

        return {'clean_text': clean_text}

    def process_result(self, result, indicators):
        """
        Process the extracted indicators to calculate readability.
        """
        result_id = result["id"]
        classification_result = "error"

        if indicators.get('excluded'):
            reason = indicators.get('reason', 'Unknown exclusion reason')
            print(reason)
            self.insert_indicator("reason", reason, result_id)
            return classification_result

        clean_text = indicators.get('clean_text')

        try:
            tx = Text_Analyzer()
            analysis_output = tx.analyze(clean_text)
            
            if isinstance(analysis_output, (int, float)):
                score_value = f"{analysis_output:.2f}"
                self.insert_indicator("Reading Ease", score_value, result_id)
                classification_result = score_value
            else:
                print(f"Non-numerical output: {analysis_output}")
                
                # Prüfen, ob es einer unserer vordefinierten Abbrüche ist
                if "too_short" in str(analysis_output) or "not supported" in str(analysis_output):
                    classification_result = "skipped_incompatible"
                    self.insert_indicator("exclusion_reason", str(analysis_output), result_id)
                else:
                    classification_result = "error"
                    self.insert_indicator("exclusion_reason", str(analysis_output), result_id)
        except Exception as e:
            error_msg = str(e)
            print(f"Analyzer exception: {error_msg}")
            
            # Wenn es an der Sprache/Mathe liegt, vergeben wir "N/A" statt eines harten Fehlers
            if "division by zero" in error_msg.lower() or "syllable" in error_msg.lower():
                classification_result = "language_not_supported"
                self.insert_indicator("Reading Ease", "N/A", result_id)
            else:
                self.insert_indicator("reason", f"Analyzer exception: {error_msg}", result_id)

        return classification_result

if __name__ == "__main__":
    pass