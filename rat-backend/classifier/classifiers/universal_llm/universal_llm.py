"""
Universal LLM Classifier for RAT
Final Release: Fully schema-compatible, optimized batch processing.
Includes robust timeout handling, prompt flexibility, dynamic support for Ollama & Cloud APIs.
Optimized for sequential execution to maximize GPU efficiency.
"""

import bs4
import hashlib
import requests
import openai
from openai import OpenAI
import os
import inspect
import sys

from datetime import datetime, timedelta

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(currentdir + "/libs/")
sys.path.append(currentdir + "/../")

from classifier import *
import json
import re

class UniversalLlm(Classifier):
    """Universal LLM Classifier for RAT"""
    
    def __init__(self, classifier_id: int = None, db=None, job_server: str = None):
        super().__init__(classifier_id, db, job_server)
        self.cached_configs = {}
        
        # Reset any tasks that were 'in process' on this server in case of a previous crash
        with self.db.connect_to_db() as conn:
            cur = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(minutes=10)
            
            cur.execute("""
                UPDATE classifier_result 
                SET value = 'error' 
                WHERE value = 'in process' AND job_server = %s AND classifier = %s
                AND created_at < %s
            """, (self.job_server, self.classifier_id, cutoff_time))
            
            cur.execute("""
                DELETE FROM classifier_indicator
                WHERE value = 'in process' AND job_server = %s AND classifier = %s
                AND created_at < %s
            """, (self.job_server, self.classifier_id, cutoff_time))
            # -----------------------------------------------------------------------------------------------
            conn.commit()

    def get_study_id(self, result_id):
        """Helper to extract the study_id dynamically based on the parsed composite ID."""
        fk_column, real_id = self.db._parse_id(result_id)
        with self.db.connect_to_db() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT study FROM {fk_column} WHERE id = %s", (real_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def to_int_id(self, val):
        """Helper function to extract the integer ID from composite keys."""
        if isinstance(val, str) and ':' in val:
            return int(val.split(':')[-1])
        return int(val)

    def classify_results(self, initial_results, helper):
        """
        Overrides the base class method to allow incremental batch processing,
        multiple LLM indicator saves per result, and continuous queue processing.
        Angepasst für Fair-Play (Round-Robin): Verarbeitet nur einen Batch und beendet sich dann.
        """
        results = initial_results
        
        if not results:
            return
            
        self.cached_configs = {} 
        
        # Pre-Load: Fetch existing indicators to avoid redundant API calls (RAM-Check)
        with self.db.connect_to_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT result, result_ai, result_chatbot, result_ai_source, indicator FROM classifier_indicator WHERE classifier = %s", (self.classifier_id,))
            existing_indicators = set()
            for row in cur.fetchall():
                r, rai, rc, ras, ind = row
                if r: existing_indicators.add((f"result:{r}", ind))
                if rai: existing_indicators.add((f"result_ai:{rai}", ind))
                if rc: existing_indicators.add((f"result_chatbot:{rc}", ind))
                if ras: existing_indicators.add((f"result_ai_source:{ras}", ind))
                if r: existing_indicators.add((str(r), ind))

        # Gruppiere Results nach Studie, um die LLM-Modelle effizient zu batchen
        results_by_study = {}
        for result in results:
            result_id = str(result['id'])
            study_id = self.get_study_id(result_id)
            if not study_id:
                self.db.update_classification_result('error_no_study', result_id, self.classifier_id)
                continue
            
            if study_id not in results_by_study:
                results_by_study[study_id] = []
            results_by_study[study_id].append(result)

        for study_id, study_results in results_by_study.items():
            if study_id not in self.cached_configs:
                config_str = self.db.get_study_llm_config(study_id)
                self.cached_configs[study_id] = json.loads(config_str) if config_str else []
                
            llm_tasks = self.cached_configs[study_id]
            if not llm_tasks:
                for r in study_results:
                    self.db.update_classification_result('error_no_config', str(r['id']), self.classifier_id)
                continue

            for task in llm_tasks:
                if not task.get('active', True):
                    continue
                    
                indicator_name = f"LLM_{task.get('display_name')}"
                model_name = task['model']
                task_display_name = task.get('display_name', 'Unknown Task') 
                
                items_to_process = []
                for result in study_results:
                    result_id = str(result['id'])
                    fk_column, _ = self.db._parse_id(result_id)
                    target_type = task.get('target_type', 'all')
                    
                    if target_type != 'all':
                        if target_type == 'organic' and fk_column != 'result': continue
                        if target_type == 'ai_overview' and fk_column != 'result_ai': continue
                        if target_type == 'ai_source' and fk_column != 'result_ai_source': continue
                        if target_type == 'chatbot' and fk_column != 'result_chatbot': continue

                    if (result_id, indicator_name) in existing_indicators or (str(self.to_int_id(result_id)), indicator_name) in existing_indicators:
                        continue
                        
                    if self.db.check_indicator_result(self.classifier_id, result_id, indicator_name, None):
                        continue  # Ein anderer Worker war in dieser Millisekunde schneller!

                    self.insert_indicator(indicator_name, "in process", result_id)
                    existing_indicators.add((result_id, indicator_name))
                        
                    items_to_process.append(result)
                    
                if not items_to_process:
                    continue
                # --------------------------------------------------------------------------------------
                
                base_url = task['base_url'].strip()
                base_url = base_url.replace("localhost", "127.0.0.1") 
                if not base_url.endswith('/v1'): 
                    base_url = base_url.rstrip('/') + '/v1'
                is_ollama = any(x in base_url.lower() for x in ['localhost', '127.0.0.1', '11434', 'ollama'])
                extra_headers = None if is_ollama else {"HTTP-Referer": "https://rat-software.org", "X-Title": "RAT Universal LLM"}
                
                # --- 2. API KEY DECRYPTION ---
                raw_key = task.get('api_key', '').strip()
                api_key = None
                
                if raw_key:
                    if raw_key.startswith('gAAAA'):
                        try:
                            import base64
                            from cryptography.fernet import Fernet
                            from dotenv import load_dotenv, find_dotenv
                            
                            load_dotenv(find_dotenv())
                            
                            master_key = os.environ.get('LLM_SECRET_KEY')
                            
                            if not master_key:
                                print("⚠️ WARNUNG: LLM_SECRET_KEY fehlt in der .env auf dem Worker-Server!")
                            else:
                                key_bytes = hashlib.sha256(master_key.encode('utf-8')).digest()
                                fernet_key = base64.urlsafe_b64encode(key_bytes)
                                
                                f = Fernet(fernet_key)
                                api_key = f.decrypt(raw_key.encode('utf-8')).decode('utf-8')
                            
                        except Exception as e:
                            print(f"⚠️ Standalone Entschlüsselungs-Fehler: {e}")
                            api_key = raw_key
                    else:
                        api_key = raw_key
                        
                if api_key and api_key.startswith('gAAAA'):
                    print(f"❌ KRITISCHER FEHLER: Standalone-Worker konnte den API-Key nicht entschlüsseln!")
                    api_key = "FEHLER_ENTSCHLUESSELUNG_FEHLGESCHLAGEN"

                if not api_key:
                    api_key = "ollama-dummy-key" if is_ollama else "FEHLER_KEY_FEHLT"

                key_prefix = api_key[:8] if api_key else 'NONE'
                print(f"🔍 DEBUG -> Task: '{task_display_name}' | Model: {model_name} | Key-Präfix: {key_prefix}")

                print(f"\n⚙️ Task: '{task_display_name}' | Loading Model: {model_name} (via {'Local/Ollama' if is_ollama else 'Cloud'}) for {len(items_to_process)} pending items...")

                client = OpenAI(base_url=base_url, api_key=api_key, default_headers=extra_headers)

                
                for result in items_to_process:
                    result_id = str(result['id'])
                    
                    # Dedup check
                    source_id = result.get('source')
                    if source_id:
                        found_duplicate = False
                        for r_id_dict in self.db.get_results_result_source(source_id):
                            raw_r_id = r_id_dict['result'] if isinstance(r_id_dict, dict) else r_id_dict[0]
                            if str(raw_r_id) == str(self.to_int_id(result_id)): continue
                            dup_composite_id = f"result:{raw_r_id}"
                            if self.db.check_indicator_result(self.classifier_id, dup_composite_id, indicator_name, None):
                                for ind in self.db.get_indicators(dup_composite_id):
                                    if ind['indicator'] == indicator_name:
                                        self.insert_indicator(indicator_name, ind['value'], result_id)
                                        found_duplicate = True
                                        break
                            if found_duplicate: break
                        if found_duplicate: continue

                    # Clean Text
                    if '_clean_text' not in result:
                        clean_text, error = self.extract_clean_text(result, helper)
                        if clean_text:
                            max_context = int(task.get('max_context', 3000))
                            result['_clean_text'] = clean_text[:max_context]
                        else:
                            result['_clean_text'] = ""
                            
                    if not result['_clean_text']:
                        continue

                    # Execute LLM API Call
                    max_tokens = int(task.get('max_tokens', 250))
                    custom_system = task.get('system_prompt', '').strip()
                    technical_guardrail = "Follow the user's instructions exactly. Output ONLY valid JSON. No greetings, no explanations, no conversational filler."

                    if custom_system:
                        final_system_prompt = f"{custom_system}\n\nCRITICAL SYSTEM INSTRUCTION:\n{technical_guardrail}"
                    else:
                        final_system_prompt = f"You are a strict data processor. {technical_guardrail}"

                    query_text = result.get('query', '')
                    if not query_text:
                        try:
                            query_text = result.get('query_', {}).get('query', '') if isinstance(result.get('query_'), dict) else getattr(result.get('query_'), 'query', '')
                        except:
                            query_text = "General Topic"

                    raw_prompt = task.get('prompt', '')
                    formatted_prompt = raw_prompt.replace('{query}', str(query_text))

                    max_retries = 3
                    final_answer = "error_api"
                    
                    for attempt in range(max_retries):
                        api_kwargs = {
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": final_system_prompt},
                                {"role": "user", "content": f"{formatted_prompt}\n\nText:\n{result.get('_clean_text', '')}"}
                            ],
                            "temperature": 0.1,
                            "timeout": 60,
                            "response_format": {"type": "json_object"},
                            "max_tokens": max_tokens
                        }

                        if is_ollama:
                            api_kwargs["extra_body"] = {"keep_alive": "5m"}

                        answer = ""
                        try:
                            response = client.chat.completions.create(**api_kwargs)
                            raw_content = response.choices[0].message.content
                            answer = raw_content.strip() if raw_content else ""
                            if not answer:
                                raise ValueError("Empty response (None) due to Moderation block or JSON-Mode/Tokenizer bug")

                        except (openai.BadRequestError, openai.APIConnectionError, openai.InternalServerError, ValueError) as e:
                            print(f"⚠️ [Fallback 1] JSON/Limit Bug oder leere Antwort. Versuche ohne 'response_format'...")
                            if "response_format" in api_kwargs: del api_kwargs["response_format"]
                            if "max_tokens" in api_kwargs: del api_kwargs["max_tokens"]
                            if is_ollama:
                                api_kwargs["extra_body"] = {"keep_alive": "5m", "options": {"num_predict": max_tokens}}

                            try:
                                response = client.chat.completions.create(**api_kwargs)
                                raw_content = response.choices[0].message.content
                                answer = raw_content.strip() if raw_content else ""
                                if not answer: raise ValueError("Empty response again")
                                    
                            except (openai.BadRequestError, openai.APIConnectionError, openai.InternalServerError, ValueError) as e2:
                                print(f"⚠️ [Fallback 2] Modell blockiert immer noch. Versuche komplett nackten Aufruf...")
                                if is_ollama: api_kwargs["extra_body"] = {"keep_alive": "5m"}
                                try:
                                    response = client.chat.completions.create(**api_kwargs)
                                    raw_content = response.choices[0].message.content
                                    answer = raw_content.strip() if raw_content else ""
                                except Exception as retry_e:
                                    print(f"❌ API Error for {model_name} on final retry: {retry_e}")
                                    answer = "error_api"
                                    
                            except openai.APITimeoutError:
                                answer = "error_timeout"
                                
                        except openai.APITimeoutError:
                            answer = "error_timeout"
                        except Exception as e:
                            print(f"❌ General API Error for model {model_name}: {e}")
                            answer = "error_api"
                        
                        if answer.startswith("```"):
                            answer = answer.replace("```json", "").replace("```", "").strip()
                            
                        if not answer or answer in ["error_api", "error_timeout"]:
                            if not answer: answer = "error_empty"
                            final_answer = answer
                            print(f"⚠️ Attempt {attempt+1}/{max_retries} failed with {final_answer}. Retrying...")
                            continue
                        
                        # --- STRICT JSON VALIDATION ---
                        try:
                            json.loads(answer)
                            final_answer = answer
                            break 
                        except ValueError:
                            m = re.search(r'\{.*\}', answer, re.DOTALL)
                            is_valid = False
                            if m:
                                try:
                                    json.loads(m.group(0))
                                    answer = m.group(0) 
                                    is_valid = True
                                except:
                                    pass
                            
                            if not is_valid:
                                print(f"⚠️ [JSON Error] Attempt {attempt+1}/{max_retries} failed (Truncated?) -> {answer[:50]}...")
                                final_answer = "error_invalid_json"
                                continue 
                            else:
                                final_answer = answer
                                break 
                    
                    self.insert_indicator(indicator_name, final_answer, result_id)
                    print(f"  └ {model_name} -> {result_id}: {answer[:40].replace(chr(10), ' ')}...")

                
                if is_ollama:
                    try:
                        requests.post(base_url.replace('/v1', '/api/generate'), json={"model": model_name, "keep_alive": 0}, timeout=10)
                    except: pass

            # Determine final status for all results in this study batch
            for result in study_results:
                result_id = str(result['id'])
                successful_count = self.db.count_indicators(result_id, self.classifier_id)
                
                fk_column, _ = self.db._parse_id(result_id)
                expected_tasks = 0
                for task in llm_tasks:
                    if not task.get('active', True):
                        continue
                    tt = task.get('target_type', 'all')
                    if tt == 'all': expected_tasks += 1
                    elif tt == 'organic' and fk_column == 'result': expected_tasks += 1
                    elif tt == 'ai_overview' and fk_column == 'result_ai': expected_tasks += 1
                    elif tt == 'ai_source' and fk_column == 'result_ai_source': expected_tasks += 1
                    elif tt == 'chatbot' and fk_column == 'result_chatbot': expected_tasks += 1
                
                status = f"Progress: {successful_count}/{expected_tasks}"
                
                if expected_tasks > 0 and successful_count >= expected_tasks:
                    status = "Finished"
                elif expected_tasks == 0:
                    status = "Finished"
                
                self.db.update_classification_result(status, result_id, self.classifier_id)

    def get_indicators(self, result, helper):
        """Not used in UniversalLlm due to custom classify_results override."""
        pass

    def process_result(self, result, indicators=None):
        """Not used in UniversalLlm due to custom classify_results override."""
        pass