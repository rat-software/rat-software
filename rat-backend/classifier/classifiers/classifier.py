from flask import json
import os
import inspect
import sys
from bs4 import BeautifulSoup

# Import path setup from original script
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(currentdir + "/../libs/")

from lib_helper import Helper


class Classifier:
    def __init__(self, classifier_id: int = None, db=None, job_server: str = None):
        self.helper = Helper()
        self.classifier_id = classifier_id
        self.db = db
        self.job_server = job_server

    def extract_clean_text(self, result, helper):
        """
        Dynamically extracts and cleans text content based on the result type.
        Handles both organic HTML files and AI plain-text database entries.
        
        Returns:
            tuple: (clean_text, exclusion_reason) - If clean_text is None, exclusion_reason contains the error.
        """
        fk_column = result.get("fk_column", "result")
        clean_text = ""

        if fk_column in ['result', 'result_ai_source']:
            status_code = result.get("status_code", 200)
            error_code = result.get("error_code")
            file_path = result.get("file_path")
            
            if status_code != 200:
                return None, f"HTTP error {status_code}"
            if error_code:
                return None, f"Error code {error_code}"

            raw_code = helper.decode_code(file_path) if file_path else None
            if not raw_code:
                return None, "No content in file"

            soup = BeautifulSoup(raw_code, "html.parser")
            for s in soup(["script", "style", "noscript", "svg"]): 
                s.extract()
            clean_text = soup.get_text(separator=' ', strip=True)

        elif fk_column in ['result_ai', 'result_chatbot']:
            answer_text = result.get("answer")
            
            if not answer_text:
                return None, "AI answer is empty"
                
            if "<" in answer_text:
                soup = BeautifulSoup(answer_text, "html.parser")
                clean_text = soup.get_text(separator=' ', strip=True)
            else:
                clean_text = answer_text

            clean_text = clean_text.replace('\n', '. ').replace('*', '')
            
        else:
            return None, f"Unknown result type: {fk_column}"

        # Validierung des finalen Textes
        if not clean_text or not str(clean_text).strip():
            return None, "No readable text content"

        return clean_text, None

    def insert_indicator(self, key, value, result_id):
        """Insert an indicator into the database"""
        db = self.db
        classifier_id = self.classifier_id
        job_server = self.job_server
        db.insert_indicator(key, value, classifier_id, result_id, job_server)
    
    def classify_results(self, results, helper):
        """Classify results and update database with scores and indicators"""
        
        # ==========================================
        # 🐛 GLOBAL Debug
        # ==========================================
        print(f"\n{'='*50}")
        print(f"🔍 [GLOBAL DEBUG] Classifier ID {self.classifier_id} gestartet!")
        print(f"📦 Empfangene Datensätze von der DB: {len(results)}")
        
        for r in results:
            r_id = r.get('id')
            fk_col = r.get('fk_column')
            f_path = r.get('file_path', 'NULL')
            source = r.get('source', 'NULL')
            #print(f"  -> ID: {r_id} | Typ: {fk_col} | Source-ID: {source} | File: {f_path}")
        #print(f"{'='*50}\n")
        # ==========================================

        result_counter = len(results)

        for result in results:
            data = {k: v for k, v in result.items()}
            result_id = data["id"]

            result_counter -= 1
            print(f"Remaining: {result_counter} | ID: {result_id}")

            try:
                try:
                    # 🐛 Debugging für die Text-Extraktion
                    clean_text, extraction_error = self.extract_clean_text(data, helper)
                    if extraction_error:
                        print(f"⚠️ [DEBUG] Extraktions-Warnung für {result_id}: {extraction_error}")
                
                    indicators = self.get_indicators(data, helper)

                    if indicators:
                        for key, value in indicators.items():
                            if isinstance(value, (list, dict)):
                                value_str = json.dumps(value)
                            else:
                                value_str = str(value)
                            self.db.insert_indicator(key, value_str, self.classifier_id, result_id, self.job_server)
                            
                        if indicators.get('excluded'):
                            self.db.update_classification_result('excluded', result_id, self.classifier_id)
                            self.db.insert_indicator('exclusion_reason', indicators.get('reason', 'Unknown reason'),
                                                self.classifier_id, result_id, self.job_server)
                            continue
                            
                    classification_value = self.process_result(result, indicators)
                    print(f"✅ Classification result for {result_id}: {classification_value}")
                    self.db.update_classification_result(classification_value, result_id, self.classifier_id)

                except Exception as e:
                    print(f"❌ Error in classification logic: {str(e)}")
                    self.db.update_classification_result('error', result_id, self.classifier_id)

            except Exception as e:
                print(f"❌ General error processing result {result_id}: {str(e)}")
                self.db.update_classification_result('error', result_id, self.classifier_id)
    
    def process_result(self, result, indicators=None):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def get_indicators(self, result, helper) -> dict:
        indicators = {}
        return indicators