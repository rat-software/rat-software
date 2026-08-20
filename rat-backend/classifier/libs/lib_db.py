import psycopg2
from psycopg2.extras import execute_values, RealDictCursor, DictCursor
from datetime import datetime
import hashlib
import json

class DB:
    """
    Database class to handle various database operations.

    Attributes:
        db_cnf (dict): Dictionary containing database configuration.
    """
    db_cnf: dict

    def __init__(self, db_cnf: dict, job_server: str = "unknown_server", refresh_time: int = 48, max_counter: int = 3):
        """
        Initialize the DB object with database configuration.

        Args:
            db_cnf (dict): Database configuration dictionary.
            job_server (str): Identifier of the processing server.
            refresh_time (int): Refresh interval.
            max_counter (int): Maximum retry counter for dead sources.
        """
        self.db_cnf = db_cnf
        self.job_server = job_server
        self.refresh_time = refresh_time
        self.max_counter = max_counter

    def __del__(self):
        """Destroy Database object and print a message."""
        print('DB object destroyed')

    def connect_to_db(self):
        """
        Context manager for database connection.

        Returns:
            ConnectionManager: A context manager for database connections.
        """
        class ConnectionManager:
            def __init__(self, db_cnf):
                self.db_cnf = db_cnf
                self.conn = None

            def __enter__(self):
                self.conn = psycopg2.connect(**self.db_cnf)
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.conn:
                    self.conn.close()

        return ConnectionManager(self.db_cnf)
        
    def _parse_id(self, composite_id):
        # Debugging: Was kommt hier an?
        
        if isinstance(composite_id, str) and ':' in composite_id:
            fk_column, real_id = composite_id.split(':')
            return fk_column, int(real_id)
        
        # Wenn wir hier landen, ist die ID kein "Typ:ID"-String
        return 'result', int(composite_id)
    

    def get_classifiers(self):
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT classifier.id, classifier.name, classifier_study.study 
                FROM classifier
                JOIN classifier_study ON classifier.id = classifier_study.classifier
                LEFT JOIN study ON classifier_study.study = study.id
                WHERE (
                
                -- === 1. ALTE LOGIK FÜR NORMALE CLASSIFIER (Bleibt komplett unangetastet) ===
                (classifier.name != 'universal_llm' AND (
                    EXISTS (
                        SELECT 1 
                        FROM result
                        JOIN result_source ON result_source.result = result.id
                        JOIN source ON result_source.source = source.id
                        LEFT JOIN classifier_result cr ON cr.result = result.id AND cr.classifier = classifier.id
                        WHERE result.study = classifier_study.study
                          AND (
                              (source.progress = 1 AND (cr.id IS NULL OR cr.value IN ('skipped_timeout', 'error')))
                              OR
                              (source.progress = -1 AND result_source.counter >= %s AND (cr.value IS NULL OR cr.value IN ('error', 'classifier_error', 'in process', 'skipped_timeout')))
                          )
                    ) OR EXISTS (
                        SELECT 1 FROM result_ai
                        LEFT JOIN classifier_result cr ON cr.result_ai = result_ai.id AND cr.classifier = classifier.id
                        WHERE result_ai.study = classifier_study.study 
                          AND (cr.id IS NULL OR cr.value IN ('skipped_timeout', 'error'))
                    ) OR EXISTS (
                        SELECT 1 FROM result_chatbot
                        LEFT JOIN classifier_result cr ON cr.result_chatbot = result_chatbot.id AND cr.classifier = classifier.id
                        WHERE result_chatbot.study = classifier_study.study 
                          AND (cr.id IS NULL OR cr.value IN ('skipped_timeout', 'error'))
                    ) OR EXISTS (
                        SELECT 1 
                        FROM result_ai_source ras
                        LEFT JOIN source ON ras.source = source.id
                        LEFT JOIN classifier_result cr ON cr.result_ai_source = ras.id AND cr.classifier = classifier.id
                        WHERE ras.study = classifier_study.study
                        AND (
                            (ras.progress = 1 AND (cr.id IS NULL OR cr.value IN ('skipped_timeout', 'error')))
                            OR
                            (ras.progress = -1 AND ras.counter >= %s AND (cr.value IS NULL OR cr.value IN ('error', 'classifier_error', 'in process', 'skipped_timeout')))
                        )
                    )
                ))

                -- === 2. NEUE LOGIK FÜR DEN UNIVERSAL LLM ===
                OR (classifier.name = 'universal_llm' AND (
                    (
                        EXISTS (SELECT 1 FROM json_array_elements(CASE WHEN study.llm_classifiers_json IS NULL OR study.llm_classifiers_json = '' THEN '[]' ELSE study.llm_classifiers_json END::json) AS j WHERE (j->>'target_type' IN ('all', 'organic') OR j->>'target_type' IS NULL) AND COALESCE((j->>'active')::boolean, true) = true)
                        AND EXISTS (
                            SELECT 1 FROM result r
                            JOIN result_source rs ON rs.result = r.id
                            JOIN source s ON rs.source = s.id
                            WHERE r.study = classifier_study.study AND s.progress = 1
                            AND (SELECT COUNT(*) FROM classifier_indicator ci WHERE ci.classifier = classifier.id AND ci.result = r.id) < (SELECT COUNT(*) FROM json_array_elements(CASE WHEN study.llm_classifiers_json IS NULL OR study.llm_classifiers_json = '' THEN '[]' ELSE study.llm_classifiers_json END::json) AS j WHERE (j->>'target_type' IN ('all', 'organic') OR j->>'target_type' IS NULL) AND COALESCE((j->>'active')::boolean, true) = true)
                        )
                    ) OR (
                        EXISTS (SELECT 1 FROM json_array_elements(CASE WHEN study.llm_classifiers_json IS NULL OR study.llm_classifiers_json = '' THEN '[]' ELSE study.llm_classifiers_json END::json) AS j WHERE (j->>'target_type' IN ('all', 'ai_overview') OR j->>'target_type' IS NULL) AND COALESCE((j->>'active')::boolean, true) = true)
                        AND EXISTS (
                            SELECT 1 FROM result_ai rai
                            WHERE rai.study = classifier_study.study
                            AND (SELECT COUNT(*) FROM classifier_indicator ci WHERE ci.classifier = classifier.id AND ci.result_ai = rai.id) < (SELECT COUNT(*) FROM json_array_elements(CASE WHEN study.llm_classifiers_json IS NULL OR study.llm_classifiers_json = '' THEN '[]' ELSE study.llm_classifiers_json END::json) AS j WHERE (j->>'target_type' IN ('all', 'ai_overview') OR j->>'target_type' IS NULL) AND COALESCE((j->>'active')::boolean, true) = true)
                        )
                    ) OR (
                        EXISTS (SELECT 1 FROM json_array_elements(CASE WHEN study.llm_classifiers_json IS NULL OR study.llm_classifiers_json = '' THEN '[]' ELSE study.llm_classifiers_json END::json) AS j WHERE (j->>'target_type' IN ('all', 'chatbot') OR j->>'target_type' IS NULL) AND COALESCE((j->>'active')::boolean, true) = true)
                        AND EXISTS (
                            SELECT 1 FROM result_chatbot rcb
                            WHERE rcb.study = classifier_study.study
                            AND (SELECT COUNT(*) FROM classifier_indicator ci WHERE ci.classifier = classifier.id AND ci.result_chatbot = rcb.id) < (SELECT COUNT(*) FROM json_array_elements(CASE WHEN study.llm_classifiers_json IS NULL OR study.llm_classifiers_json = '' THEN '[]' ELSE study.llm_classifiers_json END::json) AS j WHERE (j->>'target_type' IN ('all', 'chatbot') OR j->>'target_type' IS NULL) AND COALESCE((j->>'active')::boolean, true) = true)
                        )
                    ) OR (
                        EXISTS (SELECT 1 FROM json_array_elements(CASE WHEN study.llm_classifiers_json IS NULL OR study.llm_classifiers_json = '' THEN '[]' ELSE study.llm_classifiers_json END::json) AS j WHERE (j->>'target_type' IN ('all', 'ai_source') OR j->>'target_type' IS NULL) AND COALESCE((j->>'active')::boolean, true) = true)
                        AND EXISTS (
                            SELECT 1 FROM result_ai_source ras
                            JOIN source s ON ras.source = s.id
                            WHERE ras.study = classifier_study.study AND s.progress = 1
                            AND (SELECT COUNT(*) FROM classifier_indicator ci WHERE ci.classifier = classifier.id AND ci.result_ai_source = ras.id) < (SELECT COUNT(*) FROM json_array_elements(CASE WHEN study.llm_classifiers_json IS NULL OR study.llm_classifiers_json = '' THEN '[]' ELSE study.llm_classifiers_json END::json) AS j WHERE (j->>'target_type' IN ('all', 'ai_source') OR j->>'target_type' IS NULL) AND COALESCE((j->>'active')::boolean, true) = true)
                        )
                    )
                ))
                )
                ANd classifier_study.study > 760
                ORDER BY RANDOM()
            """, (self.max_counter, self.max_counter))
            conn.commit()
            classifiers = cur.fetchall()
        return classifiers

    def get_search_engines(self, results):
        """
        Get search engines for results dynamically matching the correct tables
        using the new denormalized 'engine_text' column.
        """
        # Whitelist der erlaubten Tabellen zur Sicherheit (verhindert SQL-Injection durch String-Formatierung)
        allowed_tables = ['result', 'result_ai', 'result_ai_source', 'result_chatbot', 'serp']
        
        with self.connect_to_db() as conn:
            for result in results:
                fk_column, real_id = self._parse_id(result['id'])
                
                if fk_column not in allowed_tables:
                    result['searchengine'] = "N/A"
                    continue
                    
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                try:
                    # Wir lesen das Feld 'engine_text' direkt aus der passenden Tabelle
                    query = f"SELECT engine_text FROM {fk_column} WHERE id = %s"
                    cur.execute(query, (real_id,))
                    row = cur.fetchone()
                    
                    if row and row['engine_text']:
                        # Weist den String (z.B. "google_us_en") direkt zu
                        result['searchengine'] = row['engine_text']
                    else:
                        result['searchengine'] = "N/A"
                        
                except Exception as e:
                    print(f"Warning: Could not fetch engine_text for {fk_column}:{real_id} - {e}")
                    result['searchengine'] = "N/A"
                    
        return results

    def get_results(self, classifier_id, study_id):  
        from psycopg2.extras import RealDictCursor
        
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # 1. Classifier-Typ prüfen
            cur.execute("SELECT name FROM classifier WHERE id = %s", (classifier_id,))
            clf_row = cur.fetchone()
            is_llm = clf_row and clf_row['name'] == 'universal_llm'
            
            if is_llm:
                config_str = self.get_study_llm_config(study_id)
                llm_tasks = json.loads(config_str) if config_str else []
                
                num_organic = sum(1 for t in llm_tasks if t.get('target_type', 'all') in ('all', 'organic', None) and t.get('active', True))
                num_source = sum(1 for t in llm_tasks if t.get('target_type', 'all') in ('all', 'ai_source') and t.get('active', True))
                num_ai = sum(1 for t in llm_tasks if t.get('target_type', 'all') in ('all', 'ai_overview') and t.get('active', True))
                num_chatbot = sum(1 for t in llm_tasks if t.get('target_type', 'all') in ('all', 'chatbot') and t.get('active', True))
                
                filter_r = f"AND (SELECT COUNT(*) FROM classifier_indicator ci WHERE ci.classifier = {classifier_id} AND ci.result = r.id) < {num_organic}" if num_organic > 0 else "AND FALSE"
                filter_ras = f"AND (SELECT COUNT(*) FROM classifier_indicator ci WHERE ci.classifier = {classifier_id} AND ci.result_ai_source = ras.id) < {num_source}" if num_source > 0 else "AND FALSE"
                filter_rai = f"AND (SELECT COUNT(*) FROM classifier_indicator ci WHERE ci.classifier = {classifier_id} AND ci.result_ai = rai.id) < {num_ai}" if num_ai > 0 else "AND FALSE"
                filter_rcb = f"AND (SELECT COUNT(*) FROM classifier_indicator ci WHERE ci.classifier = {classifier_id} AND ci.result_chatbot = rcb.id) < {num_chatbot}" if num_chatbot > 0 else "AND FALSE"
                
                check_organic = "AND TRUE"
                check_source = "AND TRUE"
                check_ai = "AND TRUE"
                check_chatbot = "AND TRUE"
            else:
                # WICHTIGER FIX: Erlaubt auch Retrys bei abgebrochenen Klassifizierungen!
                filter_r = filter_ras = filter_rai = filter_rcb = "AND (cr.id IS NULL OR cr.value IN ('error', 'skipped_timeout', 'classifier_error'))"
                
                check_organic = "AND EXISTS (SELECT 1 FROM allowed_types WHERE type_name = 'organic')"
                check_source  = "AND EXISTS (SELECT 1 FROM allowed_types WHERE type_name = 'ai sources')"
                check_ai      = "AND EXISTS (SELECT 1 FROM allowed_types WHERE type_name = 'ai')"
                check_chatbot = "AND EXISTS (SELECT 1 FROM allowed_types WHERE type_name = 'chatbot')"
                        
            # 3. SQL UNION Query (Maximaler Performance-Modus ohne JEDES Sortieren!)
            query = f"""
                    WITH allowed_types AS (
                        SELECT TRIM(LOWER(rt.name)) as type_name
                        FROM classifier_resulttype crt
                        JOIN resulttype rt ON crt.resulttype = rt.id
                        WHERE crt.classifier = %s
                    )
                    SELECT * FROM (
                        
                        (SELECT r.id, r.url, r.main, r.position, r.title, r.description, r.ip, r.final_url,
                            s.file_path, s.content_type, s.error_code, s.status_code, 
                            rs.source, r.result_type_text, NULL as answer, 'result' as fk_column, r.created_at,
                            q.query
                        FROM result r
                        JOIN result_source rs ON rs.result = r.id
                        JOIN source s ON rs.source = s.id
                        LEFT JOIN classifier_result cr ON cr.result = r.id AND cr.classifier = %s
                        LEFT JOIN query q ON r.query = q.id
                        WHERE r.study = %s AND s.progress = 1 
                        {filter_r}
                        {check_organic}
                        LIMIT 10)
                        
                        UNION ALL
                        
                        (SELECT ras.id, ras.url, ras.main, ras.position, ras.title, ras.description, ras.ip, ras.final_url,
                            s.file_path, s.content_type, s.error_code, s.status_code, 
                            ras.source, ras.result_type_text, NULL as answer, 'result_ai_source' as fk_column, ras.created_at,
                            q.query
                        FROM result_ai_source ras
                        JOIN source s ON ras.source = s.id
                        LEFT JOIN classifier_result cr ON cr.result_ai_source = ras.id AND cr.classifier = %s
                        LEFT JOIN query q ON ras.query = q.id
                        WHERE ras.study = %s AND ras.progress = 1
                        {filter_ras}
                        {check_source}
                        LIMIT 10)
                        
                        UNION ALL
                                          
                        (SELECT rai.id, 'ai://overview' as url, NULL as main, NULL as position, NULL as title, NULL as description, NULL as ip, NULL as final_url,
                            'DB_TEXT:' || COALESCE(rai.answer, '') as file_path, 'text/html' as content_type, NULL as error_code, 200 as status_code,
                            NULL as source, rai.result_type_text, rai.answer, 'result_ai' as fk_column, rai.created_at,
                            q.query
                        FROM result_ai rai
                        LEFT JOIN classifier_result cr ON cr.result_ai = rai.id AND cr.classifier = %s
                        LEFT JOIN query q ON rai.query = q.id
                        WHERE rai.study = %s
                        {filter_rai}
                        {check_ai}
                        LIMIT 10)
                        
                        UNION ALL
                        
                        (SELECT rcb.id, 'ai://chatbot' as url, NULL as main, NULL as position, NULL as title, NULL as description, NULL as ip, NULL as final_url,
                            'DB_TEXT:' || COALESCE(rcb.answer, '') as file_path, 'text/html' as content_type, NULL as error_code, 200 as status_code,
                            NULL as source, rcb.result_type_text, rcb.answer, 'result_chatbot' as fk_column, rcb.created_at,
                            q.query
                        FROM result_chatbot rcb
                        LEFT JOIN classifier_result cr ON cr.result_chatbot = rcb.id AND cr.classifier = %s
                        LEFT JOIN query q ON rcb.query = q.id
                        WHERE rcb.study = %s
                        {filter_rcb}
                        {check_chatbot}
                        LIMIT 10)
                        
                    ) AS combined_results
                    LIMIT 10
                """
            
            cur.execute(query, (
                classifier_id, 
                classifier_id, study_id, 
                classifier_id, study_id, 
                classifier_id, study_id, 
                classifier_id, study_id
            ))
            raw_results = cur.fetchall()
            
            # --- AUTO-LOCKING FIX FÜR LLM ---
            locked_results = []
            for r in raw_results:
                fk_column = r['fk_column']
                real_id = r['id']
                composite_id = f"{fk_column}:{real_id}"
                
                if not is_llm:
                    cur.execute(f"SELECT id, value FROM classifier_result WHERE classifier = %s AND {fk_column} = %s FOR UPDATE", (classifier_id, real_id))
                    row = cur.fetchone()
                    
                    locked = False
                    if row:
                        if row['value'] != 'in process':
                            cur.execute("UPDATE classifier_result SET value = 'in process', created_at = %s, job_server = %s WHERE id = %s RETURNING id", (datetime.now(), self.job_server, row['id']))
                            if cur.fetchone(): locked = True
                    else:
                        cur.execute(f"INSERT INTO classifier_result (classifier, value, {fk_column}, created_at, job_server, study) VALUES (%s, 'in process', %s, %s, %s, %s) RETURNING id", (classifier_id, real_id, datetime.now(), self.job_server, study_id))
                        if cur.fetchone(): locked = True
                        
                    if locked:
                        r['id'] = composite_id
                        locked_results.append(r)
                else:
                    r['id'] = composite_id
                    locked_results.append(r)
                    
            conn.commit()
            
        if hasattr(self, 'get_search_engines'):
            locked_results = self.get_search_engines(locked_results)
            
        return locked_results

    def insert_classification_result(self, classifier_id, value, result, job_server):
        fk_column, real_id = self._parse_id(result)
        try:
            created_at = datetime.now()
            with self.connect_to_db() as conn:
                cur = conn.cursor()
                cur.execute(f"UPDATE classifier_result SET value = %s, created_at = %s, job_server = %s WHERE classifier = %s AND {fk_column} = %s AND value IN ('in process', 'skipped_timeout', 'error', 'source_failed') RETURNING id", (value, created_at, job_server, classifier_id, real_id))
                if not cur.fetchone():
                    cur.execute(f"SELECT id FROM classifier_result WHERE classifier = %s AND {fk_column} = %s", (classifier_id, real_id))
                    if not cur.fetchone():
                        cur.execute(f"INSERT INTO classifier_result (classifier, value, {fk_column}, created_at, job_server, study) VALUES (%s, %s, %s, %s, %s, (SELECT study FROM {fk_column} WHERE id = %s))", (classifier_id, value, real_id, created_at, job_server, real_id))
                conn.commit()
            return True 
        except Exception as e:
            print(f"Error inserting classification result: {e}")
            return False

    def insert_indicator(self, indicator, value, classifier_id, result, job_server):
        fk_column, real_id = self._parse_id(result)
        try:
            created_at = datetime.now()
            with self.connect_to_db() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                cur.execute(f"SELECT id FROM classifier_indicator WHERE classifier = %s AND {fk_column} = %s AND indicator = %s", (classifier_id, real_id, indicator))
                if cur.fetchone():
                    cur.execute(f"UPDATE classifier_indicator SET value = %s, created_at = %s WHERE classifier = %s AND {fk_column} = %s AND indicator = %s", (value, created_at, classifier_id, real_id, indicator))
                else:
                    cur.execute(f"INSERT INTO classifier_indicator (indicator, value, classifier, {fk_column}, created_at, job_server, study) VALUES (%s, %s, %s, %s, %s, %s, (SELECT study FROM {fk_column} WHERE id = %s))", (indicator, value, classifier_id, real_id, created_at, job_server, real_id))
                conn.commit()
        except Exception as e:
            print(f"Error inserting indicator: {e}")
            
    def update_classification_result(self, value, composite_id, classifier_id):
        fk_column, real_id = self._parse_id(composite_id)
        try:
            created_at = datetime.now()
            with self.connect_to_db() as conn:
                cur = conn.cursor()
                
                # 1. Versuche das Update durchzuführen und lass dir die ID zurückgeben (RETURNING id)
                query = f"UPDATE classifier_result SET value=%s, created_at=%s WHERE {fk_column} = %s AND classifier = %s RETURNING id"
                cur.execute(query, (value, created_at, real_id, classifier_id))
                
                # 2. NEU: Wenn kein Datensatz zum Updaten gefunden wurde (fetchone ist None), lege ihn an!
                if not cur.fetchone():
                    insert_query = f"INSERT INTO classifier_result (classifier, value, {fk_column}, created_at, job_server, study) VALUES (%s, %s, %s, %s, %s, (SELECT study FROM {fk_column} WHERE id = %s))"
                    cur.execute(insert_query, (classifier_id, value, real_id, created_at, getattr(self, 'job_server', 'unknown_server'), real_id))
                    
                conn.commit()
        except Exception as e:
            print(f"Error updating classification result: {e}")
            
    def reset_classifiers(self, result):
        """
        Reset the classifiers for a given result.

        Args:
            result (int): ID of the result.

        Returns:
            None
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("DELETE FROM classifier_indicator WHERE result = %s AND value = 'in process'", (result,))
            cur.execute("DELETE FROM classifier_result WHERE result = %s", (result,))
            cur.execute("DELETE FROM classifier_result WHERE value = 'in process' AND result = %s", (result,))
            conn.commit()

    def reset(self, job_server):
        """
        Reset any unfinished classifiers in the database.
        Cleans up deadlocks and crashed jobs globally if they are stuck 'in process' for too long,
        or explicitly resets local jobs for the current server.
        """
        from datetime import datetime, timedelta
        
        # Wir killen alle Tasks, die seit über 30 Minuten hängen (egal von welchem Server!)
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        try:
            with self.connect_to_db() as conn:
                cur = conn.cursor()
                
                # 1. Globale Leichenentsorgung für Classic Classifiers
                cur.execute("""
                    DELETE FROM classifier_result 
                    WHERE value = 'in process' AND (created_at < %s OR job_server = %s)
                """, (cutoff_time, job_server))
                
                # 2. Globale Leichenentsorgung für LLM-Indikatoren (Über ALLE Quellentypen hinweg!)
                cur.execute("""
                    DELETE FROM classifier_indicator 
                    WHERE value = 'in process' AND (created_at < %s OR job_server = %s)
                """, (cutoff_time, job_server))
                
                # 3. Synchronisation: Wenn wir LLM-Indikatoren gelöscht haben, müssen wir den Haupt-Status wieder öffnen
                cur.execute("""
                    UPDATE classifier_result 
                    SET value = 'error', created_at = NOW()
                    WHERE value LIKE 'Progress: %'
                      AND NOT EXISTS (
                          SELECT 1 FROM classifier_indicator ci 
                          WHERE ci.classifier = classifier_result.classifier 
                            AND (ci.result = classifier_result.result OR ci.result IS NULL)
                            AND (ci.result_ai = classifier_result.result_ai OR ci.result_ai IS NULL)
                            AND (ci.result_chatbot = classifier_result.result_chatbot OR ci.result_chatbot IS NULL)
                            AND (ci.result_ai_source = classifier_result.result_ai_source OR ci.result_ai_source IS NULL)
                            AND (ci.result_image = classifier_result.result_image OR ci.result_image IS NULL)
                      )
                """)
                
                conn.commit()
                print(f"🧹 Datenbank-Reset erfolgreich durchgeführt. Tote 'in process' Tasks wurden entfernt.")
        except Exception as e:
            print(f"❌ Fehler beim Datenbank-Reset: {e}")

    def check_classification_result(self, classifier, result):
        fk_column, real_id = self._parse_id(result)
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute(f"SELECT id FROM classifier_result WHERE classifier = %s AND {fk_column} = %s", (classifier, real_id))
            conn.commit()
            return bool(cur.fetchall())
    
    def check_classification_result_not_in_process(self, classifier, result):
        """
        Check if a result is already declared as a scraping job.

        Args:
            classifier (int): ID of the classifier.
            result (int/str): ID of the result (can be composite like 'result:477').

        Returns:
            list: List of dictionaries containing the ID if found.
        """
        # NEU: Parse die zusammengesetzte ID
        fk_column, real_id = self._parse_id(result)
        
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            # NEU: Nutze {fk_column} dynamisch und übergebe real_id
            cur.execute(f"SELECT id FROM classifier_result WHERE classifier = %s AND {fk_column} = %s AND value !='in process'", 
                        (classifier, real_id))
            conn.commit()
            check_progress = cur.fetchall()
        return check_progress

    def check_indicator_result(self, classifier, result, indicator, value):
        fk_column, real_id = self._parse_id(result)
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            if value is None:
                cur.execute(f"SELECT id FROM classifier_indicator WHERE classifier = %s AND {fk_column} = %s AND indicator = %s", (classifier, real_id, indicator))
            else:
                cur.execute(f"SELECT id FROM classifier_indicator WHERE classifier = %s AND {fk_column} = %s AND indicator = %s AND value = %s", (classifier, real_id, indicator, value))
            conn.commit()
            return bool(cur.fetchall())

    def check_source_duplicates(self, source):
        """
        Check for duplicate sources in the database.

        Args:
            source (int): ID of the source.

        Returns:
            list: List of duplicate sources.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT * FROM result_source WHERE source = %s", (source,))
            conn.commit()
            check_source = cur.fetchall()
        return check_source

    def get_results_result_source(self, source):
        """
        Get results for a given source.

        Args:
            source (int): ID of the source.

        Returns:
            list: List of results for the given source.
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT result FROM result_source WHERE source = %s", (source,))
            conn.commit()
            result_ids = cur.fetchall()
        return result_ids

    def get_classifier_result(self, result):
        """
        Get the classifier result for a given result ID.
        """
        fk_column, real_id = self._parse_id(result)
        
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute(f"SELECT value FROM classifier_result WHERE {fk_column} = %s and value !='in process'", 
                        (real_id,))
            conn.commit()
            result_sources = cur.fetchall()
        return result_sources

    def get_indicators(self, composite_id):
        # 1. Spalte und ID extrahieren (z.B. "result_ai", 30)
        fk_column, real_id = self._parse_id(composite_id)
        
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            # 2. Dynamisch in der korrekten Spalte suchen
            query = f"SELECT * FROM classifier_indicator WHERE {fk_column} = %s"
            cur.execute(query, (real_id,))
            conn.commit()
            return cur.fetchall()

    def deleteClassifierDuplicates(self):
        """
        Delete duplicate classifier results.

        Returns:
            None
        """
        with self.connect_to_db() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("""
                DELETE FROM classifier_result 
                WHERE id IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (PARTITION BY result, classifier_result.classifier ORDER BY id) AS row_num 
                        FROM classifier_result
                    ) t WHERE t.row_num > 1
                );
            """)
            conn.commit()


    def flag_dead_sources(self, classifier_id, study_id, job_server):
        try:
            with self.connect_to_db() as conn:
                cur = conn.cursor()
                
                # ==========================================
                # 1. Dead Organic Sources
                # ==========================================
                
                # A) Existierende Einträge updaten
                cur.execute('''
                    UPDATE classifier_result 
                    SET value = 'source_failed', created_at = NOW(), job_server = %s
                    WHERE classifier = %s 
                      AND value IN ('error', 'classifier_error', 'in process')
                      AND result IN (
                          SELECT result.id 
                          FROM result
                          JOIN result_source ON result_source.result = result.id
                          JOIN source ON result_source.source = source.id
                          WHERE result.study = %s AND source.progress = -1 AND result_source.counter >= %s
                      )
                ''', (job_server, classifier_id, study_id, self.max_counter))
                
                # B) Neue Einträge einfügen (mit Type Casting ::integer / ::varchar)
                cur.execute('''
                    INSERT INTO classifier_result (classifier, value, result, created_at, job_server, study)
                    SELECT %s::integer, 'source_failed', result.id, NOW(), %s::varchar, result.study
                    FROM result
                    JOIN result_source ON result_source.result = result.id
                    JOIN source ON result_source.source = source.id
                    WHERE result.study = %s AND source.progress = -1 AND result_source.counter >= %s
                      AND NOT EXISTS (
                          SELECT 1 FROM classifier_result cr 
                          WHERE cr.classifier = %s AND cr.result = result.id
                      )
                ''', (classifier_id, job_server, study_id, self.max_counter, classifier_id))

                # ==========================================
                # 2. Dead AI Sources
                # ==========================================
                
                # A) Existierende Einträge updaten
                cur.execute('''
                    UPDATE classifier_result 
                    SET value = 'source_failed', created_at = NOW(), job_server = %s
                    WHERE classifier = %s 
                      AND value IN ('error', 'classifier_error', 'in process')
                      AND result_ai_source IN (
                          SELECT ras.id 
                          FROM result_ai_source ras
                          LEFT JOIN source ON ras.source = source.id
                          WHERE ras.study = %s AND ras.counter >= %s
                            AND (source.progress = -1)
                      )
                ''', (job_server, classifier_id, study_id, self.max_counter))
                
                # B) Neue Einträge einfügen (mit Type Casting ::integer / ::varchar)
                cur.execute('''
                    INSERT INTO classifier_result (classifier, value, result_ai_source, created_at, job_server, study)
                    SELECT %s::integer, 'source_failed', ras.id, NOW(), %s::varchar, ras.study
                    FROM result_ai_source ras
                    LEFT JOIN source ON ras.source = source.id
                    WHERE ras.study = %s AND ras.counter >= %s
                      AND (source.progress = -1)
                      AND NOT EXISTS (
                          SELECT 1 FROM classifier_result cr 
                          WHERE cr.classifier = %s AND cr.result_ai_source = ras.id
                      )
                ''', (classifier_id, job_server, study_id, self.max_counter, classifier_id))
                
                conn.commit()
                
        except Exception as e:
            # Jetzt wird der Fehler geworfen und im Log angezeigt, statt das Programm stumm sterben zu lassen
            print(f"❌ Error in flag_dead_sources: {str(e)}")

    def check_db_connection(self):
        """
        Test the database connection.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            with self.connect_to_db():
                return True
        except Exception as e:
            print(f"Error checking DB connection: {e}")
            return False
            
    def get_study_llm_config(self, study_id):
            """
            Lädt die LLM JSON-Konfiguration für eine spezifische Studie aus der Datenbank.
            Wird von universal_llm.py benötigt, um die Tasks und Prompts zu kennen.
            """
            from psycopg2.extras import DictCursor
            try:
                with self.connect_to_db() as conn:
                    cur = conn.cursor(cursor_factory=DictCursor)
                    cur.execute("SELECT llm_classifiers_json FROM study WHERE id = %s", (study_id,))
                    row = cur.fetchone()
                    
                    if row and row['llm_classifiers_json']:
                        return row['llm_classifiers_json']
                    return None
            except Exception as e:
                print(f"Error fetching LLM config for study {study_id}: {e}")
                return None
                
                
            
    def count_indicators(self, result_id, classifier_id):
        fk_column, real_id = self._parse_id(result_id)
        with self.connect_to_db() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT count(*) FROM classifier_indicator WHERE {fk_column} = %s AND classifier = %s", (real_id, classifier_id))
            return cur.fetchone()[0]

    def get_ai_segment_text_for_source(self, source_id):
            """
            Lädt den Text des AI-Segments, das mit dieser Quelle verknüpft ist.
            """
            # Sicherstellen, dass wir die echte ID haben (falls "result_ai_source:123" übergeben wird)
            fk_column, real_id = self._parse_id(source_id)
            
            try:
                with self.connect_to_db() as conn:
                    cur = conn.cursor(cursor_factory=DictCursor)
                    # Holt den Text über die Many-to-Many Zuordnungstabelle
                    cur.execute("""
                        SELECT ras.text 
                        FROM result_ai_segment ras
                        JOIN ai_segment_source ass ON ras.id = ass.segment_id
                        WHERE ass.source_id = %s
                        LIMIT 1
                    """, (real_id,))
                    row = cur.fetchone()
                    return row['text'] if row and row['text'] else ""
            except Exception as e:
                print(f"Error fetching AI segment text: {e}")
                return ""

    def get_sibling_sources_for_segment(self, source_id):
        """
        Sucht andere AI-Quellen (Siblings), die mit demselben Text-Segment verknüpft sind.
        Gibt deren IDs und den Dateipfad zum HTML-Quellcode zurück.
        """
        fk_column, real_id = self._parse_id(source_id)
        
        try:
            with self.connect_to_db() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                # Sucht nach allen Quellen, die am selben Segment hängen, außer sich selbst
                cur.execute("""
                    SELECT ras.id, src.file_path
                    FROM result_ai_source ras
                    JOIN source src ON ras.source = src.id
                    JOIN ai_segment_source ass ON ras.id = ass.source_id
                    WHERE ass.segment_id IN (
                        SELECT segment_id FROM ai_segment_source WHERE source_id = %s
                    )
                    AND ras.id != %s
                """, (real_id, real_id))
                
                # Wir geben eine Liste von Dictionaries zurück
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching sibling sources: {e}")
            return []

    def lock_llm_indicator(self, indicator, classifier_id, result_id, job_server):
            """
            Versucht einen LLM-Task atomar (kugelsicher gegen andere Server) zu reservieren.
            Gibt True zurück, wenn dieser Server den Task gewonnen hat.
            Gibt False zurück, wenn ein anderer Server schneller war.
            """
            fk_column, real_id = self._parse_id(result_id)
            try:
                with self.connect_to_db() as conn:
                    cur = conn.cursor()
                    
                    # 1. Fall: Es gab vorher einen Fehler (z.B. API Timeout). Wir sichern uns den Retry.
                    cur.execute(f"""
                        UPDATE classifier_indicator 
                        SET value = 'in process', job_server = %s, created_at = NOW() 
                        WHERE classifier = %s AND {fk_column} = %s AND indicator = %s 
                        AND value IN ('error', 'error_api', 'error_timeout', 'error_invalid_json', 'error_empty') 
                        RETURNING id
                    """, (job_server, classifier_id, real_id, indicator))
                    
                    if cur.fetchone():
                        conn.commit()
                        return True
                    
                    # 2. Fall: Der Task ist komplett neu. Wir fügen ihn nur ein, wenn er noch NICHT existiert (Atomar!)
                    cur.execute(f"""
                        INSERT INTO classifier_indicator (indicator, value, classifier, {fk_column}, created_at, job_server, study)
                        SELECT %s, 'in process', %s, %s, NOW(), %s, (SELECT study FROM {fk_column} WHERE id = %s)
                        WHERE NOT EXISTS (
                            SELECT 1 FROM classifier_indicator 
                            WHERE classifier = %s AND {fk_column} = %s AND indicator = %s
                        ) 
                        RETURNING id
                    """, (indicator, classifier_id, real_id, job_server, real_id, classifier_id, real_id, indicator))
                    
                    if cur.fetchone():
                        conn.commit()
                        return True
                    
                    # Wenn wir hier landen, hat ein anderer Server in genau dieser Millisekunde den Task weggeschnappt!
                    return False
            except Exception as e:
                print(f"Lock Error: {e}")
                return False