"""
DB

This class provides database operations for the application.

Attributes:
    db_cnf (dict): Dictionary for the database connection.
    job_server (str): Name of the job server.
    refresh_time (int): Hours for refreshing scraped sources.
"""
# load required libs
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
    """Hours to refresh scraped sources"""

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
        Splits Composite-IDs (e.g., 'result_ai_source:42' or 'result_image:15').
        """
        if isinstance(composite_id, str) and ':' in composite_id:
            fk_column, real_id = composite_id.split(':')
            return fk_column, int(real_id)
        # Fallback for old numeric IDs
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
        Get all pending sources from ALL tables (progress = 2 or progress = -1)
        OPTIMIZED: 'progress = -1' gets retried instantly, 'progress = 2' gets a 5-minute grace period.
        CRITICAL FIX 1: Uses 'result' instead of 'id' for result_source to match composite ID logic!
        CRITICAL FIX 2: Removed job_server restriction so ANY active server can clean up dead jobs globally.
        """
        conn = self.connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT 'result:' || result AS composite_rs_id, source 
            FROM result_source 
            WHERE (
                (progress = 2 AND created_at < now() - interval '5 minutes') 
                OR progress = -1
            ) AND counter < 3
            
            UNION ALL
            
            SELECT 'result_ai_source:' || id AS composite_rs_id, source 
            FROM result_ai_source 
            WHERE (
                (progress = 2 AND created_at < now() - interval '5 minutes') 
                OR progress = -1
            ) AND counter < 3
            
            UNION ALL
            
            SELECT 'result_image:' || id AS composite_rs_id, source 
            FROM result_image 
            WHERE (
                (progress = 2 AND created_at < now() - interval '5 minutes') 
                OR progress = -1
            ) AND counter < 3
        """)
        
        sources_pending = cur.fetchall()
        conn.commit()
        conn.close()
        return sources_pending

    def update_sources_failed(self, job_server):
        """
        Get all finally failed sources (Counter >= 3) across ALL tables.
        CRITICAL FIX 1: Only touches progress 0 or 2. Protects progress 1 (Success) from being overwritten!
        CRITICAL FIX 2: Removed job_server restriction to allow global cleanup of dead servers.
        """
        from datetime import datetime, timedelta
        
        conn = self.connect_to_db()
        cur = conn.cursor()
        
        # Changed from 10 to 5 minutes to speed up the failure detection
        threshold_time = datetime.now() - timedelta(minutes=5)
        
        try:
            cur.execute("SET lock_timeout = '10s';")
            
            cur.execute("""
                UPDATE result_source
                SET progress = -1
                WHERE counter >= 3 
                  AND progress IN (0, 2) 
                  AND created_at < %s;
            """, (threshold_time,))
            
            cur.execute("""
                UPDATE result_ai_source
                SET progress = -1
                WHERE counter >= 3 
                  AND progress IN (0, 2) 
                  AND created_at < %s;
            """, (threshold_time,))
            
            cur.execute("""
                UPDATE result_image
                SET progress = -1
                WHERE counter >= 3 
                  AND progress IN (0, 2) 
                  AND created_at < %s;
            """, (threshold_time,))
            
            conn.commit()
        except Exception as e:
            print(f"Notice: Could not bulk-update failed sources. Details: {e}")
            conn.rollback()
        finally:
            conn.close()

    def expire_old_pending_sources(self):
        """
        Aggressively mark ALL uncompleted sources associated with studies older than 14 days 
        as permanently failed (progress = -1, counter = 3).
        CRITICAL FIX: Ignores progress = 1 so we do not delete successful scrapes!
        """
        conn = self.connect_to_db()
        cur = conn.cursor()
        
        try:
            cur.execute("SET lock_timeout = '10s';")
            
            # 1. Update AI Sources
            print("Expiring uncompleted AI sources > 14 days...")
            cur.execute("""
                UPDATE result_ai_source
                SET progress = -1, counter = 3
                FROM study s
                WHERE result_ai_source.study = s.id 
                AND s.created_at < now() - interval '14 days'
                AND (result_ai_source.progress IS NULL OR result_ai_source.progress IN (0, 2));
            """)
            
            # 2. Update Image Sources
            print("Expiring uncompleted Image sources > 14 days...")
            cur.execute("""
                UPDATE result_image
                SET progress = -1, counter = 3
                FROM study s
                WHERE result_image.study = s.id 
                AND s.created_at < now() - interval '14 days'
                AND (result_image.progress IS NULL OR result_image.progress IN (0, 2));
            """)
            
            # 3. Update Organic Sources
            print("Expiring uncompleted Organic sources > 14 days...")
            cur.execute("""
                UPDATE result_source
                SET progress = -1, counter = 3
                FROM result r
                JOIN study s ON r.study = s.id
                WHERE result_source.result = r.id
                AND s.created_at < now() - interval '14 days'
                AND (result_source.progress IS NULL OR result_source.progress IN (0, 2));
            """)
            
            # 4. Insert dummy records for untouched Organic Sources
            print("Generating ghost records for un-attempted Organic sources > 14 days...")
            cur.execute("""
                INSERT INTO result_source (result, progress, counter, created_at, job_server)
                SELECT r.id, -1, 3, now(), 'expired_14_days'
                FROM result r
                JOIN study s ON r.study = s.id
                LEFT JOIN result_source rs ON rs.result = r.id
                WHERE s.created_at < now() - interval '14 days'
                AND rs.id IS NULL;
            """)
            
            conn.commit()
            print("✅ Expiration of 14-day old sources complete.")
        except Exception as e:
            print(f"❌ Error expiring old sources. Details: {e}")
            conn.rollback()
        finally:
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
            pass # Image results have no redirect/IP/main
            
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
        Accepts optional 'job_server' to save the server name when locking!
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
            self.reset_result_source(progress, 0, created_at, source_id)

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
                -- 1. Organic results
                SELECT 
                    'result:' || r.id AS composite_id, r.url, c.name AS country_name, c.code, s.created_at as study_date,
                    ROW_NUMBER() OVER(PARTITION BY r.study ORDER BY r.id ASC) as rank_within_study
                FROM result r 
                JOIN study s ON r.study = s.id 
                LEFT JOIN country c ON r.country = c.id 
                LEFT JOIN result_source rs ON rs.result = r.id 
                WHERE (rs.id IS NULL OR (rs.progress = 0 AND rs.counter < 3))
                AND s.live_link_mode = FALSE
                AND s.created_at >= CURRENT_DATE - INTERVAL '14 days'
                
                UNION ALL
                
                -- 2. AI Sources
                SELECT 
                    'result_ai_source:' || ras.id AS composite_id, ras.url, c.name AS country_name, c.code, s.created_at as study_date,
                    ROW_NUMBER() OVER(PARTITION BY ras.study ORDER BY ras.id ASC) as rank_within_study
                FROM result_ai_source ras
                JOIN study s ON ras.study = s.id
                LEFT JOIN country c ON ras.country = c.id
                WHERE (ras.progress IS NULL OR (ras.progress = 0 AND ras.counter < 3))
                AND s.live_link_mode = FALSE
                AND s.created_at >= CURRENT_DATE - INTERVAL '14 days'
                
                UNION ALL
                
                -- 3. Image results (Direct download)
                SELECT 
                    'result_image:' || ri.id AS composite_id, ri.image_url as url, c.name AS country_name, c.code, s.created_at as study_date,
                    ROW_NUMBER() OVER(PARTITION BY ri.study ORDER BY ri.id ASC) as rank_within_study
                FROM result_image ri
                JOIN study s ON ri.study = s.id
                LEFT JOIN country c ON ri.country = c.id
                WHERE (ri.progress IS NULL OR (ri.progress = 0 AND ri.counter < 3))
                AND s.live_link_mode = FALSE
                AND s.created_at >= CURRENT_DATE - INTERVAL '14 days'
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