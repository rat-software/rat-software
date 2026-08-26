"""
DB

This class provides database operations for the application.

Attributes:
    db_cnf (dict): Dictionary for the database connection.
    job_server (str): Name of the job server.
    refresh_time (int): Hours for refreshing scraped sources.
"""
#load required libs
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

class DB:
    """Database class"""
    db_cnf: dict
    """Dictionary for the database connection"""
    job_server: str
    """Name of the job server"""
    refresh_time: int
    """Hours for refreh scraped sources"""

    def __init__(self, db_cnf: dict, job_server: str, refresh_time: int):
        self.db_cnf = db_cnf
        self.job_server = job_server
        self.refresh_time = refresh_time

    def __del__(self):
        """Destroy Database object"""
        print('DB object destroyed')

    def connect_to_db(self):
        """
        Connect to the database using psycopg2
        """
        conn = psycopg2.connect(**self.db_cnf)
        return conn
        
    def _parse_id(self, composite_id):
        """
        Splittet Composite-IDs (z.B. 'result_ai_source:42' oder 'result_image:15').
        """
        if isinstance(composite_id, str) and ':' in composite_id:
            fk_column, real_id = composite_id.split(':')
            return fk_column, int(real_id)
        # Fallback für alte numerische IDs
        return 'result', int(composite_id)        

    def insert_result_source(self, result_id, progress, created_at, job_server):
        fk_column, real_id = self._parse_id(result_id)
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if fk_column == 'result':
            cur.execute("INSERT INTO result_source (result, progress, created_at, job_server) VALUES (%s, %s, %s, %s);", (real_id, progress, created_at, job_server))
        elif fk_column == 'result_ai_source':
            cur.execute("UPDATE result_ai_source SET progress = %s, job_server = %s WHERE id = %s", (progress, job_server, real_id))
        elif fk_column == 'result_image':
            cur.execute("UPDATE result_image SET progress = %s, created_at = %s, job_server = %s WHERE id = %s", (progress, created_at, job_server, real_id))
            
        conn.commit()
        conn.close()

    def get_sources_pending(self, job_server):
        """
        Get all failed sources from ALL tables (progress = 2 or progress = -1)
        BUGFIX: Akzeptiert jetzt auch NULL-Werte für job_server, um alte fehlerhafte Locks zu retten!
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT 'result:' || id AS composite_rs_id, source 
            FROM result_source 
            WHERE (progress = 2 OR progress = -1) AND counter < 3 AND (job_server = %s OR job_server IS NULL) AND created_at < now() - interval '10 minutes'
            
            UNION ALL
            
            SELECT 'result_ai_source:' || id AS composite_rs_id, source 
            FROM result_ai_source 
            WHERE (progress = 2 OR progress = -1) AND counter < 3 AND (job_server = %s OR job_server IS NULL) AND created_at < now() - interval '10 minutes'
            
            UNION ALL
            
            SELECT 'result_image:' || id AS composite_rs_id, source 
            FROM result_image 
            WHERE (progress = 2 OR progress = -1) AND counter < 3 AND (job_server = %s OR job_server IS NULL) AND created_at < now() - interval '10 minutes'
        """, (job_server, job_server, job_server))
        
        sources_pending = cur.fetchall()
        conn.commit()
        conn.close()
        return sources_pending

    def update_sources_failed(self, job_server):
        """
        Get all finally failed sources (Counter >= 3) across ALL tables.
        """
        from datetime import datetime, timedelta
        
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        threshold_time = datetime.now() - timedelta(minutes=10)
        
        sql = """
            SELECT 'result:' || id AS composite_rs_id, source 
            FROM result_source 
            WHERE counter >= 3 AND (job_server = %s OR job_server IS NULL) AND (progress = -1 OR (progress IN (0, 2) AND created_at < %s))
            
            UNION ALL
            
            SELECT 'result_ai_source:' || id AS composite_rs_id, source 
            FROM result_ai_source 
            WHERE counter >= 3 AND (job_server = %s OR job_server IS NULL) AND (progress = -1 OR (progress IN (0, 2) AND created_at < %s))
            
            UNION ALL
            
            SELECT 'result_image:' || id AS composite_rs_id, source 
            FROM result_image 
            WHERE counter >= 3 AND (job_server = %s OR job_server IS NULL) AND (progress = -1 OR (progress IN (0, 2) AND created_at < %s))
        """
        cur.execute(sql, (job_server, threshold_time, job_server, threshold_time, job_server, threshold_time))
        sources_failed = cur.fetchall()

        for s in sources_failed:
            composite_rs_id = s[0]
            source_id = s[1]
            fk_column, real_id = self._parse_id(composite_rs_id)
            
            # 1. Update Brücken-Tabellen basierend auf dem Composite-String
            if fk_column == 'result':
                cur.execute("UPDATE result_source SET progress=-1 WHERE id = %s", (real_id,))
            elif fk_column == 'result_ai_source':
                cur.execute("UPDATE result_ai_source SET progress=-1 WHERE id = %s", (real_id,))
            elif fk_column == 'result_image':
                cur.execute("UPDATE result_image SET progress=-1 WHERE id = %s", (real_id,))
            
            # 2. Update Source Tabelle
            if source_id:
                cur.execute("UPDATE source SET progress=-1 WHERE id = %s", (source_id,))
                
        conn.commit()                   
        conn.close()

    def get_source_check(self, url, country):
        """
        Read a scraped source by URL
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id, created_at from source where progress = 1 and url=%s and country=%s ORDER by created_at DESC",(url, country))
        conn.commit()
        sc = cur.fetchone()
        conn.close()

        if sc:
            timestamp = datetime.now()
            source_id = sc[0]
            created_at = sc[1]
            diff = timestamp - created_at
            diff_in_hours = diff.total_seconds() / 3600

            if diff_in_hours < self.refresh_time:
                print(diff_in_hours)
                return source_id
            else:
                return False
        else:
            return False

    def get_source_check_by_result_id(self, result_id):
        fk_column, real_id = self._parse_id(result_id)
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if fk_column == 'result':
            cur.execute("SELECT id from result_source where result = %s AND progress = 2", (real_id,))
        elif fk_column == 'result_ai_source':
            cur.execute("SELECT id from result_ai_source where id = %s AND progress = 2", (real_id,))
        elif fk_column == 'result_image':
            cur.execute("SELECT id from result_image where id = %s AND progress = 2", (real_id,))
            
        scr = cur.fetchone()
        conn.commit()
        conn.close()
        return scr

    def get_result_content(self, source_id):
        """
        Get content from an existing result to copy its content to a source with the same URL
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT result.ip, result.main, result.final_url from result, result_source where result.id = result_source.result and result_source.source =%s",(source_id,))
        conn.commit()
        rc = cur.fetchone()
        conn.close()
        return rc

    def insert_source(self, url, progress, created_at, job_server, country):
        """
        Insert a new source to the database
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO source (url, progress, created_at, job_server, country) VALUES (%s, %s, %s, %s, %s) RETURNING id;", (url, progress, created_at, job_server, country))
        lastrowid = cur.fetchone()
        conn.commit()
        conn.close()
        return lastrowid

    def check_progress(self, url, result_id):
        fk_column, real_id = self._parse_id(result_id)
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if fk_column == 'result':
            cur.execute("SELECT result_source.id FROM result_source, source WHERE result_source.source = source.id AND source.url = %s AND source.progress = 2 AND result_source.result = %s", (url, real_id))
        elif fk_column == 'result_ai_source':
            cur.execute("SELECT result_ai_source.id FROM result_ai_source, source WHERE result_ai_source.source = source.id AND source.url = %s AND source.progress = 2 AND result_ai_source.id = %s", (url, real_id))
        elif fk_column == 'result_image':
            cur.execute("SELECT result_image.id FROM result_image, source WHERE result_image.source = source.id AND source.url = %s AND source.progress = 2 AND result_image.id = %s", (url, real_id))
            
        check_progress = cur.fetchall()
        conn.commit()
        conn.close()
        return bool(check_progress)

    def update_source(self, source_id, file_path, progress, content_type, error_code, status_code, created_at, content_dict):
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        sql = """
            UPDATE source 
            SET file_path=%s, progress=%s, content_type=%s, 
                error_code=%s, status_code=%s, created_at=%s, 
                content_dict=%s 
            WHERE id = %s
        """
        cur.execute(sql, (file_path, progress, content_type, error_code, status_code, created_at, content_dict, source_id))
        conn.commit()
        conn.close()

    def replace_source_bin(self, source_id, bin):
        """
        Update source content when scraping job is done
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update source SET bin=%s WHERE id = %s", (bin, source_id))
        conn.commit()
        conn.close()

    def update_result(self, result_id, ip, main, final_url):
        fk_column, real_id = self._parse_id(result_id)
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if fk_column == 'result':
            cur.execute("UPDATE result SET ip=%s, main=%s, final_url=%s WHERE id=%s", (ip, main, final_url, real_id))
        elif fk_column == 'result_ai_source':
            cur.execute("UPDATE result_ai_source SET ip=%s, main=%s, final_url=%s WHERE id=%s", (ip, main, final_url, real_id))
        elif fk_column == 'result_image':
            pass # Bild-Ergebnisse haben kein Redirect/IP/Main in dem Sinne
            
        conn.commit()
        conn.close()

    def get_source_counter_result(self, result_id):
        fk_column, real_id = self._parse_id(result_id)
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if fk_column == 'result':
            cur.execute("SELECT counter FROM result_source WHERE result = %s", (real_id,))
        elif fk_column == 'result_ai_source':
            cur.execute("SELECT counter FROM result_ai_source WHERE id = %s", (real_id,))
        elif fk_column == 'result_image':
            cur.execute("SELECT counter FROM result_image WHERE id = %s", (real_id,))
            
        counter = cur.fetchall()
        conn.commit()
        conn.close()
        return counter[0][0] if counter else 0

    def update_result_source(self, result_id, source_id, progress, counter, created_at, job_server):
        fk_column, real_id = self._parse_id(result_id)
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if fk_column == 'result':
            cur.execute("UPDATE result_source SET source=%s, progress=%s, counter=%s, created_at=%s, job_server=%s WHERE result=%s", (source_id, progress, counter, created_at, job_server, real_id))
        elif fk_column == 'result_ai_source':
            cur.execute("UPDATE result_ai_source SET source=%s, progress=%s, counter=%s, created_at=%s, job_server=%s WHERE id=%s", (source_id, progress, counter, created_at, job_server, real_id))
        elif fk_column == 'result_image':
            cur.execute("UPDATE result_image SET source=%s, progress=%s, counter=%s, created_at=%s, job_server=%s WHERE id=%s", (source_id, progress, counter, created_at, job_server, real_id))
            
        conn.commit()
        conn.close()

    def update_result_source_result(self, result_id, progress, counter, created_at, job_server=None):
        """
        BUGFIX: Akzeptiert jetzt optional 'job_server', um den Servernamen beim Locking zu speichern!
        """
        fk_column, real_id = self._parse_id(result_id)
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if job_server is not None:
            if fk_column == 'result':
                cur.execute("UPDATE result_source SET progress = %s, counter = %s, created_at = %s, job_server = %s WHERE result = %s", (progress, counter, created_at, job_server, real_id))
            elif fk_column == 'result_ai_source':
                cur.execute("UPDATE result_ai_source SET progress = %s, counter = %s, created_at = %s, job_server = %s WHERE id = %s", (progress, counter, created_at, job_server, real_id))
            elif fk_column == 'result_image':
                cur.execute("UPDATE result_image SET progress = %s, counter = %s, created_at = %s, job_server = %s WHERE id = %s", (progress, counter, created_at, job_server, real_id))
        else:
            if fk_column == 'result':
                cur.execute("UPDATE result_source SET progress = %s, counter = %s, created_at = %s WHERE result = %s", (progress, counter, created_at, real_id))
            elif fk_column == 'result_ai_source':
                cur.execute("UPDATE result_ai_source SET progress = %s, counter = %s, created_at = %s WHERE id = %s", (progress, counter, created_at, real_id))
            elif fk_column == 'result_image':
                cur.execute("UPDATE result_image SET progress = %s, counter = %s, created_at = %s WHERE id = %s", (progress, counter, created_at, real_id))
            
        conn.commit()
        conn.close()

    def delete_source_pending(self, source_id, progress, created_at):
        """
        Delete pending sources
        """
        conn = DB.connect_to_db(self)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("Update source SET progress = %s, created_at =%s WHERE id = %s", (progress, created_at, source_id))
        conn.commit()
        conn.close()

    def reset_result_source(self, progress, counter, created_at, source_id):
        """
        Reset a source in all result tables.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        created_at = datetime.now()
        
        cur.execute("UPDATE result_source SET progress = %s, counter = %s, created_at = %s WHERE source = %s", 
                    (progress, counter, created_at, source_id))
        cur.execute("UPDATE result_ai_source SET progress = %s, counter = %s, created_at = %s WHERE source = %s", 
                    (progress, counter, created_at, source_id))
        cur.execute("UPDATE result_image SET progress = %s, counter = %s, created_at = %s WHERE source = %s", 
                    (progress, counter, created_at, source_id))
                    
        conn.commit()
        conn.close()

    def delete_result_source_pending(self, composite_id):
        """
        Delete pending sources from the correct table based on composite_id.
        """
        fk_column, real_id = self._parse_id(composite_id)
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if fk_column == 'result':
            cur.execute("DELETE FROM result_source WHERE id = %s", (real_id,))
        elif fk_column == 'result_ai_source':
            cur.execute("DELETE FROM result_ai_source WHERE id = %s", (real_id,))
        elif fk_column == 'result_image':
            cur.execute("DELETE FROM result_image WHERE id = %s", (real_id,))
            
        conn.commit()
        conn.close()

    def reset(self, job_server):
        """
        Call reset when the sources_controller stops and delete pending sources
        """
        sources_pending = self.get_sources_pending(job_server)
        for sources_pending in sources_pending:
            source_id = sources_pending[0]
            progress = 0
            created_at = datetime.now()
            self.delete_source_pending(source_id, progress, created_at)
            self.reset_result_source(progress, counter, created_at, source_id)

    def get_result_source(self, result_id):
        fk_column, real_id = self._parse_id(result_id)
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if fk_column == 'result':
            cur.execute("SELECT id from result_source where result = %s", (real_id,))
        elif fk_column == 'result_ai_source':
            cur.execute("SELECT id from result_ai_source where id = %s", (real_id,))
        elif fk_column == 'result_image':
            cur.execute("SELECT id from result_image where id = %s", (real_id,))
            
        scr = cur.fetchone()
        conn.commit()
        conn.close()
        return scr

    def get_result_source_source(self, result_id):
        fk_column, real_id = self._parse_id(result_id)
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if fk_column == 'result':
            cur.execute("SELECT source from result_source where result = %s", (real_id,))
        elif fk_column == 'result_ai_source':
            cur.execute("SELECT source from result_ai_source where id = %s", (real_id,))
        elif fk_column == 'result_image':
            cur.execute("SELECT source from result_image where id = %s", (real_id,))
            
        scr = cur.fetchone()
        conn.commit()
        conn.close()
        return scr[0] if scr else None

    def get_sources(self, job_server):
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        sql = """
            WITH RankedSources AS (
                -- 1. Organische Ergebnisse
                SELECT 
                    'result:' || r.id AS composite_id, r.url, c.name AS country_name, c.code, s.created_at as study_date,
                    ROW_NUMBER() OVER(PARTITION BY r.study ORDER BY r.id ASC) as rank_within_study
                FROM result r 
                JOIN study s ON r.study = s.id 
                LEFT JOIN country c ON r.country = c.id 
                LEFT JOIN result_source rs ON rs.result = r.id 
                WHERE (rs.source IS NULL OR (rs.progress = 0 AND rs.counter < 3))
                AND s.live_link_mode = FALSE
                
                UNION ALL
                
                -- 2. AI Sources
                SELECT 
                    'result_ai_source:' || ras.id AS composite_id, ras.url, c.name AS country_name, c.code, s.created_at as study_date,
                    ROW_NUMBER() OVER(PARTITION BY ras.study ORDER BY ras.id ASC) as rank_within_study
                FROM result_ai_source ras
                JOIN study s ON ras.study = s.id
                LEFT JOIN country c ON ras.country = c.id
                WHERE (ras.source IS NULL OR (ras.progress = 0 AND ras.counter < 3))
                AND s.live_link_mode = FALSE
                
                
                UNION ALL
                
                -- 3. Bilder-Ergebnisse (Direkter Download)
                SELECT 
                    'result_image:' || ri.id AS composite_id, ri.image_url as url, c.name AS country_name, c.code, s.created_at as study_date,
                    ROW_NUMBER() OVER(PARTITION BY ri.study ORDER BY ri.id ASC) as rank_within_study
                FROM result_image ri
                JOIN study s ON ri.study = s.id
                LEFT JOIN country c ON ri.country = c.id
                WHERE (ri.source IS NULL OR (ri.progress = 0 AND ri.counter < 3))
                AND s.live_link_mode = FALSE
            )
            SELECT composite_id, url, country_name, code
            FROM RankedSources
            ORDER BY rank_within_study ASC, study_date DESC
            LIMIT 20;
        """
        cur.execute(sql)
        sources = cur.fetchall()
        conn.commit()
        conn.close()

        sources_list = []
        for s in sources:
            progress = 2
            result_id = s[0] 
            result_url = s[1]
            result_country = s[2]
            country_code = s[3]

            if self.get_result_source(result_id):
                counter = self.get_source_counter_result(result_id)
                counter = counter + 1
                created_at = datetime.now()
                # BUGFIX: Übergabe von job_server, damit die Zeile korrekt reserviert wird!
                self.update_result_source_result(result_id, progress, counter, created_at, job_server)
            else:
                created_at = datetime.now()
                self.insert_result_source(result_id, progress, created_at, job_server)

            sources_list.append([result_id, result_url, result_country, country_code])

        return sources_list

    def check_db_connection(self):
        """
        Test the database connection
        """
        try:
            conn = self.connect_to_db()
            conn.close()
            return True
        except:
            return False