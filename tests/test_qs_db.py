"""
Unit tests for rat-backend/query_sampler/db.py

All functions open a fresh psycopg2 connection, run one or more SQL
statements, commit, and close.  Tests verify:
  - psycopg2.connect is called (connection established)
  - the correct SQL is executed with the correct parameters
  - commit() and close() are always called
  - return values are forwarded unchanged
  - insert_keyword() skips the DB when keyword is falsy
  - reset_hanging_qs_jobs() executes exactly two UPDATE statements
"""

import importlib.util
import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, call, patch

# ── Stubs – must be in sys.modules before db.py is imported ──────────────────

_psycopg2 = types.ModuleType('psycopg2')
_psycopg2.__path__ = []
_psycopg2_extras = types.ModuleType('psycopg2.extras')
_psycopg2_extras.DictCursor     = object
_psycopg2_extras.RealDictCursor = object
_psycopg2_extras.execute_values = MagicMock()
_psycopg2.extras = _psycopg2_extras
_psycopg2.connect = MagicMock()

sys.modules.setdefault('psycopg2',        _psycopg2)
sys.modules.setdefault('psycopg2.extras', _psycopg2_extras)

_pd = types.ModuleType('pandas')
_pd.read_sql = MagicMock()
_pd.DataFrame = MagicMock()
sys.modules.setdefault('pandas',   _pd)
sys.modules.setdefault('warnings', sys.modules.get('warnings', types.ModuleType('warnings')))

# ── Load db.py via importlib so we can patch the config-file open() ──────────

_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'query_sampler', 'db.py',
)

_FAKE_CREDS = {
    "database": "testdb",
    "user":     "testuser",
    "password": "testpass",
    "host":     "localhost",
    "port":     "5432",
}

_spec = importlib.util.spec_from_file_location('qs_db', _DB_PATH)
_mod  = importlib.util.module_from_spec(_spec)

with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(_FAKE_CREDS))), \
     patch('json.load', return_value=_FAKE_CREDS):
    _spec.loader.exec_module(_mod)

sys.modules['qs_db'] = _mod
import qs_db


# ── Helper ────────────────────────────────────────────────────────────────────

def _mock_conn(fetchone=None, fetchall=None):
    """Return (mock_conn, mock_cursor) with pre-set fetch return values."""
    cur = MagicMock()
    cur.fetchone.return_value = fetchone
    cur.fetchall.return_value = fetchall if fetchall is not None else []

    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


# ═════════════════════════════════════════════════════════════════════════════
# Module-level credentials
# ═════════════════════════════════════════════════════════════════════════════

class TestModuleCredentials(unittest.TestCase):

    def test_database_loaded(self):
        self.assertEqual(qs_db.database, _FAKE_CREDS['database'])

    def test_user_loaded(self):
        self.assertEqual(qs_db.user, _FAKE_CREDS['user'])

    def test_password_loaded(self):
        self.assertEqual(qs_db.password, _FAKE_CREDS['password'])

    def test_host_loaded(self):
        self.assertEqual(qs_db.host, _FAKE_CREDS['host'])

    def test_port_loaded(self):
        self.assertEqual(qs_db.port, _FAKE_CREDS['port'])


# ═════════════════════════════════════════════════════════════════════════════
# get_studies
# ═════════════════════════════════════════════════════════════════════════════

class TestGetStudies(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchall=[{'id': 1}])

    def test_returns_fetchall_result(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.get_studies()
        self.assertEqual(result, [{'id': 1}])

    def test_queries_qs_study_table(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_studies()
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('qs_study', sql)

    def test_commit_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_studies()
        self.conn.commit.assert_called_once()

    def test_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_studies()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# insert_study
# ═════════════════════════════════════════════════════════════════════════════

class TestInsertStudy(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchone={'id': 42})

    def test_returns_fetchone_result(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.insert_study('My Study')
        self.assertEqual(result, {'id': 42})

    def test_sql_contains_insert_into_qs_study(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_study('My Study')
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('INSERT INTO qs_study', sql)

    def test_name_passed_as_parameter(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_study('My Study')
        params = self.cur.execute.call_args[0][1]
        self.assertIn('My Study', params)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_study('X')
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# get_study
# ═════════════════════════════════════════════════════════════════════════════

class TestGetStudy(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchone={'id': 7, 'name': 'Test'})

    def test_returns_fetchone_result(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.get_study(7)
        self.assertEqual(result, {'id': 7, 'name': 'Test'})

    def test_id_passed_as_parameter(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_study(7)
        params = self.cur.execute.call_args[0][1]
        self.assertIn(7, params)

    def test_queries_qs_study_table(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_study(7)
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('qs_study', sql)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_study(1)
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# get_regions
# ═════════════════════════════════════════════════════════════════════════════

class TestGetRegions(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchall=[{'name': 'Germany', 'criterion_id': 2276}])

    def test_returns_fetchall_result(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.get_regions()
        self.assertEqual(result, [{'name': 'Germany', 'criterion_id': 2276}])

    def test_filters_by_country(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_regions()
        sql = self.cur.execute.call_args[0][0]
        self.assertIn("'Country'", sql)

    def test_orders_by_name_asc(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_regions()
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('ORDER BY name ASC', sql)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_regions()
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# get_languages
# ═════════════════════════════════════════════════════════════════════════════

class TestGetLanguages(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchall=[{'name': 'German', 'criterion_id': 1001}])

    def test_returns_fetchall_result(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.get_languages()
        self.assertEqual(result, [{'name': 'German', 'criterion_id': 1001}])

    def test_queries_qs_language_code_table(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_languages()
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('qs_language_code', sql)

    def test_orders_by_name_asc(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_languages()
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('ORDER BY name ASC', sql)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_languages()
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# get_keywords
# ═════════════════════════════════════════════════════════════════════════════

class TestGetKeywords(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchall=[{'keyword': 'berlin'}])

    def test_returns_fetchall_result(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.get_keywords(3)
        self.assertEqual(result, [{'keyword': 'berlin'}])

    def test_study_id_passed_as_parameter(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keywords(3)
        params = self.cur.execute.call_args[0][1]
        self.assertIn(3, params)

    def test_queries_qs_keyword_table(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keywords(3)
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('qs_keyword', sql)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keywords(1)
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# get_keywords_bg
# ═════════════════════════════════════════════════════════════════════════════

class TestGetKeywordsBg(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchall=[{'keyword': 'test', 'study_id': 1}])

    def test_returns_fetchall_result(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.get_keywords_bg()
        self.assertEqual(result, [{'keyword': 'test', 'study_id': 1}])

    def test_filters_by_status_zero(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keywords_bg()
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('status = 0', sql)

    def test_excludes_empty_keywords(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keywords_bg()
        sql = self.cur.execute.call_args[0][0]
        self.assertIn("keyword !=''", sql)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keywords_bg()
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# get_keyword_ideas
# ═════════════════════════════════════════════════════════════════════════════

class TestGetKeywordIdeas(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchall=[{'keyword_idea': 'berlin trip'}])

    def test_returns_fetchall_result(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.get_keyword_ideas(5)
        self.assertEqual(result, [{'keyword_idea': 'berlin trip'}])

    def test_study_id_passed_as_parameter(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keyword_ideas(5)
        params = self.cur.execute.call_args[0][1]
        self.assertIn(5, params)

    def test_queries_qs_keyword_idea_table(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keyword_ideas(5)
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('qs_keyword_idea', sql)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keyword_ideas(1)
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# insert_keyword
# ═════════════════════════════════════════════════════════════════════════════

class TestInsertKeyword(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn()

    def test_inserts_when_keyword_is_provided(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_keyword(1, 2276, 1001, 'berlin')
        self.cur.execute.assert_called_once()

    def test_skips_db_when_keyword_is_empty_string(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_keyword(1, 2276, 1001, '')
        _psycopg2.connect.assert_not_called()

    def test_skips_db_when_keyword_is_none(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_keyword(1, 2276, 1001, None)
        _psycopg2.connect.assert_not_called()

    def test_all_params_passed_to_execute(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_keyword(1, 2276, 1001, 'berlin')
        params = self.cur.execute.call_args[0][1]
        self.assertIn(1,      params)
        self.assertIn(2276,   params)
        self.assertIn(1001,   params)
        self.assertIn('berlin', params)

    def test_sql_is_insert_into_qs_keyword(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_keyword(1, 2276, 1001, 'berlin')
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('INSERT INTO qs_keyword', sql)

    def test_commit_and_close_called_on_insert(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_keyword(1, 2276, 1001, 'berlin')
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# check_keyword
# ═════════════════════════════════════════════════════════════════════════════

class TestCheckKeyword(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchall=[])

    def test_returns_fetchall_result(self):
        self.cur.fetchall.return_value = [{'id': 9}]
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.check_keyword(1, 2276, 1001, 'berlin')
        self.assertEqual(result, [{'id': 9}])

    def test_all_params_in_execute(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.check_keyword(1, 2276, 1001, 'berlin')
        params = self.cur.execute.call_args[0][1]
        self.assertIn(1,        params)
        self.assertIn(2276,     params)
        self.assertIn(1001,     params)
        self.assertIn('berlin', params)

    def test_filters_by_status_zero(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.check_keyword(1, 2276, 1001, 'berlin')
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('status = 0', sql)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.check_keyword(1, 2276, 1001, 'berlin')
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# get_keyword_status_study
# ═════════════════════════════════════════════════════════════════════════════

class TestGetKeywordStatusStudy(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchone={'id': 1, 'status': 0})

    def test_returns_fetchone_result(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.get_keyword_status_study(3)
        self.assertEqual(result, {'id': 1, 'status': 0})

    def test_study_id_passed_as_parameter(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keyword_status_study(3)
        params = self.cur.execute.call_args[0][1]
        self.assertIn(3, params)

    def test_filters_by_status_zero(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keyword_status_study(3)
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('status = 0', sql)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keyword_status_study(1)
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# get_keyword_status
# ═════════════════════════════════════════════════════════════════════════════

class TestGetKeywordStatus(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn(fetchone={'id': 10, 'status': 1})

    def test_returns_fetchone_result(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            result = qs_db.get_keyword_status(10, 1)
        self.assertEqual(result, {'id': 10, 'status': 1})

    def test_keyword_id_and_status_passed_as_parameters(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keyword_status(10, 1)
        params = self.cur.execute.call_args[0][1]
        self.assertIn(10, params)
        self.assertIn(1,  params)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.get_keyword_status(10, 1)
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# update_keyword_status
# ═════════════════════════════════════════════════════════════════════════════

class TestUpdateKeywordStatus(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn()

    def test_sql_is_update_qs_keyword(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.update_keyword_status(1, 10)
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('UPDATE qs_keyword', sql)

    def test_status_and_keyword_id_passed_as_parameters(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.update_keyword_status(1, 10)
        params = self.cur.execute.call_args[0][1]
        self.assertIn(1,  params)
        self.assertIn(10, params)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.update_keyword_status(1, 10)
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# insert_keyword_idea
# ═════════════════════════════════════════════════════════════════════════════

class TestInsertKeywordIdea(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn()

    def test_sql_is_insert_into_qs_keyword_idea(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_keyword_idea(1, 10, 'berlin tour', 5000, 0.3)
        sql = self.cur.execute.call_args[0][0]
        self.assertIn('INSERT INTO qs_keyword_idea', sql)

    def test_all_params_passed_to_execute(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_keyword_idea(1, 10, 'berlin tour', 5000, 0.3)
        params = self.cur.execute.call_args[0][1]
        self.assertIn(1,            params)
        self.assertIn(10,           params)
        self.assertIn('berlin tour', params)
        self.assertIn(5000,         params)
        self.assertIn(0.3,          params)

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.insert_keyword_idea(1, 10, 'x', 100, 0.1)
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# select_keywords_ideas
# ═════════════════════════════════════════════════════════════════════════════

class TestSelectKeywordsIdeas(unittest.TestCase):

    def test_calls_pd_read_sql_with_study_id(self):
        conn = MagicMock()
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__  = MagicMock(return_value=False)
        conn.cursor.return_value.__enter__ = MagicMock()
        conn.cursor.return_value.__exit__  = MagicMock(return_value=False)

        fake_df = MagicMock()
        fake_df.dropna.return_value = fake_df

        with patch('qs_db.psycopg2.connect', return_value=conn), \
             patch('qs_db.pd.read_sql', return_value=fake_df) as mock_read_sql:
            result = qs_db.select_keywords_ideas(7)

        sql_arg = mock_read_sql.call_args[0][0]
        self.assertIn('7', sql_arg)

    def test_returns_dataframe_after_dropna(self):
        conn = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock()
        conn.cursor.return_value.__exit__  = MagicMock(return_value=False)

        fake_df = MagicMock()
        fake_df.dropna.return_value = fake_df

        with patch('qs_db.psycopg2.connect', return_value=conn), \
             patch('qs_db.pd.read_sql', return_value=fake_df):
            result = qs_db.select_keywords_ideas(7)

        fake_df.dropna.assert_called_once()
        self.assertIs(result, fake_df)


# ═════════════════════════════════════════════════════════════════════════════
# reset_hanging_qs_jobs
# ═════════════════════════════════════════════════════════════════════════════

class TestResetHangingQsJobs(unittest.TestCase):

    def setUp(self):
        self.conn, self.cur = _mock_conn()

    def test_executes_exactly_two_statements(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.reset_hanging_qs_jobs()
        self.assertEqual(self.cur.execute.call_count, 2)

    def test_resets_qs_keyword_status(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.reset_hanging_qs_jobs()
        calls = [c[0][0] for c in self.cur.execute.call_args_list]
        self.assertTrue(any('qs_keyword' in sql and 'status = 0' in sql for sql in calls))

    def test_resets_qs_study_status(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.reset_hanging_qs_jobs()
        calls = [c[0][0] for c in self.cur.execute.call_args_list]
        self.assertTrue(any('qs_study' in sql and 'status = 0' in sql for sql in calls))

    def test_resets_from_status_2(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.reset_hanging_qs_jobs()
        calls = [c[0][0] for c in self.cur.execute.call_args_list]
        self.assertTrue(all('status = 2' in sql for sql in calls))

    def test_commit_and_close_called(self):
        with patch('qs_db.psycopg2.connect', return_value=self.conn):
            qs_db.reset_hanging_qs_jobs()
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
