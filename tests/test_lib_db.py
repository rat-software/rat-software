"""
Unit tests for rat-backend/sources/libs/lib_db.py

Testschwerpunkte:
  - INSERT/UPDATE/SELECT: SQL wird abgesetzt, commit + close werden aufgerufen,
    Rückgabewerte werden korrekt weitergeleitet
  - SQL-Parametrisierung: User-Daten landen im Parameter-Tuple, nicht im SQL-String
  - Verbindungsfehler: connect_to_db propagiert Exceptions,
    check_db_connection fängt sie ab und gibt False zurück
"""
import importlib.util
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

# ── Modul laden ───────────────────────────────────────────────────────────────
_LIB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'sources', 'libs', 'lib_db.py',
)
_spec = importlib.util.spec_from_file_location('lib_db', _LIB_PATH)
_mod  = importlib.util.module_from_spec(_spec)
sys.modules['lib_db'] = _mod
_spec.loader.exec_module(_mod)

DB = _mod.DB

_CNF        = {'host': 'localhost', 'dbname': 'test', 'user': 'u', 'password': 'p'}
_JOB_SERVER = 'worker-1'
_REFRESH    = 48


# ── Hilfsfunktion ─────────────────────────────────────────────────────────────

def _mock_db(fetchone=None, fetchall=None):
    """Erstellt DB-Instanz + vollständig gemockten psycopg2-Cursor."""
    cur = MagicMock()
    cur.fetchone.return_value  = fetchone
    cur.fetchall.return_value  = fetchall if fetchall is not None else []

    conn = MagicMock()
    conn.cursor.return_value = cur

    db = DB(_CNF, _JOB_SERVER, _REFRESH)
    return db, conn, cur


# ─────────────────────────────────────────────────────────────────────────────
# Verbindung
# ─────────────────────────────────────────────────────────────────────────────

class TestDBConnection(unittest.TestCase):

    def test_connect_to_db_passes_config_to_psycopg2(self):
        db = DB(_CNF, _JOB_SERVER, _REFRESH)
        with patch('lib_db.psycopg2.connect', return_value=MagicMock()) as mock_connect:
            db.connect_to_db()
            mock_connect.assert_called_once_with(**_CNF)

    def test_check_db_connection_returns_true_on_success(self):
        db, conn, _ = _mock_db()
        with patch('lib_db.psycopg2.connect', return_value=conn):
            self.assertTrue(db.check_db_connection())

    def test_check_db_connection_returns_false_on_error(self):
        import psycopg2
        db = DB(_CNF, _JOB_SERVER, _REFRESH)
        with patch('lib_db.psycopg2.connect',
                   side_effect=psycopg2.OperationalError('refused')):
            self.assertFalse(db.check_db_connection())

    def test_check_db_connection_closes_connection_on_success(self):
        db, conn, _ = _mock_db()
        with patch('lib_db.psycopg2.connect', return_value=conn):
            db.check_db_connection()
            conn.close.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# INSERT
# ─────────────────────────────────────────────────────────────────────────────

class TestInsertResultSource(unittest.TestCase):

    def setUp(self):
        self.db, self.conn, self.cur = _mock_db()
        self.patcher = patch('lib_db.psycopg2.connect', return_value=self.conn)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_execute_called_with_four_params(self):
        now = datetime.now()
        self.db.insert_result_source(42, 2, now, _JOB_SERVER)
        sql, params = self.cur.execute.call_args[0]
        self.assertEqual(len(params), 4)

    def test_params_contain_result_id(self):
        now = datetime.now()
        self.db.insert_result_source(99, 2, now, _JOB_SERVER)
        _, params = self.cur.execute.call_args[0]
        self.assertIn(99, params)

    def test_sql_uses_placeholders_not_values(self):
        self.db.insert_result_source(42, 2, datetime.now(), _JOB_SERVER)
        sql, _ = self.cur.execute.call_args[0]
        self.assertIn('%s', sql)
        self.assertNotIn('42', sql)

    def test_commit_called(self):
        self.db.insert_result_source(1, 2, datetime.now(), _JOB_SERVER)
        self.conn.commit.assert_called_once()

    def test_connection_closed(self):
        self.db.insert_result_source(1, 2, datetime.now(), _JOB_SERVER)
        self.conn.close.assert_called_once()


class TestInsertSource(unittest.TestCase):

    def setUp(self):
        self.db, self.conn, self.cur = _mock_db(fetchone=(7,))
        self.patcher = patch('lib_db.psycopg2.connect', return_value=self.conn)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_returns_new_id(self):
        result = self.db.insert_source('http://x.com', 2, datetime.now(),
                                       _JOB_SERVER, 'US')
        self.assertEqual(result, (7,))

    def test_sql_contains_returning(self):
        self.db.insert_source('http://x.com', 2, datetime.now(), _JOB_SERVER, 'US')
        sql, _ = self.cur.execute.call_args[0]
        self.assertIn('RETURNING', sql.upper())

    def test_url_in_params_not_in_sql(self):
        url = 'http://example.com/page'
        self.db.insert_source(url, 2, datetime.now(), _JOB_SERVER, 'US')
        sql, params = self.cur.execute.call_args[0]
        self.assertNotIn(url, sql)
        self.assertIn(url, params)

    def test_five_params_passed(self):
        self.db.insert_source('http://x.com', 2, datetime.now(), _JOB_SERVER, 'DE')
        _, params = self.cur.execute.call_args[0]
        self.assertEqual(len(params), 5)

    def test_commit_and_close_called(self):
        self.db.insert_source('http://x.com', 2, datetime.now(), _JOB_SERVER, 'US')
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateSource(unittest.TestCase):

    def setUp(self):
        self.db, self.conn, self.cur = _mock_db()
        self.patcher = patch('lib_db.psycopg2.connect', return_value=self.conn)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_source_id_in_params(self):
        self.db.update_source(55, '/path/file', 1, 'text/html',
                              None, 200, datetime.now(), '{}')
        _, params = self.cur.execute.call_args[0]
        self.assertIn(55, params)

    def test_eight_params_passed(self):
        self.db.update_source(1, '/p', 1, 'text/html', None, 200, datetime.now(), '{}')
        _, params = self.cur.execute.call_args[0]
        self.assertEqual(len(params), 8)

    def test_commit_and_close_called(self):
        self.db.update_source(1, '/p', 1, 'text/html', None, 200, datetime.now(), '{}')
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


class TestUpdateResult(unittest.TestCase):

    def setUp(self):
        self.db, self.conn, self.cur = _mock_db()
        self.patcher = patch('lib_db.psycopg2.connect', return_value=self.conn)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_four_params_in_correct_order(self):
        self.db.update_result(10, '1.2.3.4', 'example.com', 'http://example.com/final')
        _, params = self.cur.execute.call_args[0]
        # ip, main, final_url, result_id — result_id last (WHERE clause)
        self.assertEqual(params, ('1.2.3.4', 'example.com', 'http://example.com/final', 10))

    def test_main_domain_in_params_not_sql(self):
        domain = 'sensitive-domain.org'
        self.db.update_result(1, '0.0.0.0', domain, 'http://x.com')
        sql, params = self.cur.execute.call_args[0]
        self.assertNotIn(domain, sql)
        self.assertIn(domain, params)

    def test_commit_and_close_called(self):
        self.db.update_result(1, '0.0.0.0', 'x.com', 'http://x.com')
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


class TestUpdateResultSource(unittest.TestCase):

    def setUp(self):
        self.db, self.conn, self.cur = _mock_db()
        self.patcher = patch('lib_db.psycopg2.connect', return_value=self.conn)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_six_params_passed(self):
        self.db.update_result_source(1, 2, 1, 3, datetime.now(), _JOB_SERVER)
        _, params = self.cur.execute.call_args[0]
        self.assertEqual(len(params), 6)

    def test_commit_and_close_called(self):
        self.db.update_result_source(1, 2, 1, 3, datetime.now(), _JOB_SERVER)
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()


class TestReplaceBin(unittest.TestCase):

    def test_bin_and_id_in_params(self):
        db, conn, cur = _mock_db()
        with patch('lib_db.psycopg2.connect', return_value=conn):
            db.replace_source_bin(5, b'\x89PNG')
            _, params = cur.execute.call_args[0]
            self.assertEqual(params, (b'\x89PNG', 5))


# ─────────────────────────────────────────────────────────────────────────────
# SELECT
# ─────────────────────────────────────────────────────────────────────────────

class TestSelectMethods(unittest.TestCase):

    def _run(self, method, *args, fetchone=None, fetchall=None):
        db, conn, cur = _mock_db(fetchone=fetchone, fetchall=fetchall)
        with patch('lib_db.psycopg2.connect', return_value=conn):
            result = getattr(db, method)(*args)
        return result, cur

    def test_get_sources_pending_returns_fetchall(self):
        rows = [{'id': 1, 'source': 2, 'result': 3}]
        result, _ = self._run('get_sources_pending', _JOB_SERVER, fetchall=rows)
        self.assertEqual(result, rows)

    def test_get_sources_pending_passes_job_server_as_param(self):
        _, cur = self._run('get_sources_pending', _JOB_SERVER)
        sql, params = cur.execute.call_args[0]
        self.assertNotIn(_JOB_SERVER, sql)
        self.assertIn(_JOB_SERVER, params)

    def test_get_source_check_by_result_id_returns_fetchone(self):
        result, _ = self._run('get_source_check_by_result_id', 42, fetchone=(10,))
        self.assertEqual(result, (10,))

    def test_get_source_check_by_result_id_passes_id_as_param(self):
        _, cur = self._run('get_source_check_by_result_id', 42)
        sql, params = cur.execute.call_args[0]
        self.assertNotIn('42', sql)
        self.assertIn(42, params)

    def test_get_result_source_returns_fetchone(self):
        result, _ = self._run('get_result_source', 7, fetchone=(3,))
        self.assertEqual(result, (3,))

    def test_get_result_source_returns_none_when_not_found(self):
        result, _ = self._run('get_result_source', 99, fetchone=None)
        self.assertIsNone(result)

    def test_get_result_content_returns_fetchone(self):
        row = ('192.168.1.1', 'example.com', 'http://example.com')
        result, _ = self._run('get_result_content', 5, fetchone=row)
        self.assertEqual(result, row)


# ─────────────────────────────────────────────────────────────────────────────
# get_source_check — Zeit-Logik
# ─────────────────────────────────────────────────────────────────────────────

class TestGetSourceCheck(unittest.TestCase):

    def _run(self, created_at, fetchone_row):
        db, conn, _ = _mock_db(fetchone=fetchone_row)
        with patch('lib_db.psycopg2.connect', return_value=conn):
            return db.get_source_check('http://x.com', 'US')

    def test_fresh_source_returns_source_id(self):
        # created_at just now → diff < refresh_time (48h)
        result = self._run(datetime.now(), (42, datetime.now()))
        self.assertEqual(result, 42)

    def test_stale_source_returns_false(self):
        # created_at 100 hours ago → diff > 48h
        old = datetime.now() - timedelta(hours=100)
        result = self._run(old, (42, old))
        self.assertFalse(result)

    def test_no_source_returns_false(self):
        result = self._run(None, None)
        self.assertFalse(result)

    def test_url_and_country_passed_as_params(self):
        db, conn, cur = _mock_db(fetchone=None)
        with patch('lib_db.psycopg2.connect', return_value=conn):
            db.get_source_check('http://secret.com', 'DE')
        sql, params = cur.execute.call_args[0]
        self.assertNotIn('http://secret.com', sql)
        self.assertIn('http://secret.com', params)
        self.assertIn('DE', params)


# ─────────────────────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────────────────────

class TestDeleteMethods(unittest.TestCase):

    def setUp(self):
        self.db, self.conn, self.cur = _mock_db()
        self.patcher = patch('lib_db.psycopg2.connect', return_value=self.conn)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_delete_result_source_pending_passes_id_as_param(self):
        self.db.delete_result_source_pending(77)
        sql, params = self.cur.execute.call_args[0]
        self.assertIn('DELETE', sql.upper())
        self.assertNotIn('77', sql)
        self.assertIn(77, params)

    def test_delete_result_source_pending_commit_and_close(self):
        self.db.delete_result_source_pending(1)
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()

    def test_delete_source_pending_uses_update_not_delete(self):
        # "delete_source_pending" sets progress=0, does not physically DELETE
        self.db.delete_source_pending(5, 0, datetime.now())
        sql, _ = self.cur.execute.call_args[0]
        self.assertIn('UPDATE', sql.upper())

    def test_delete_source_pending_id_in_params_not_sql(self):
        self.db.delete_source_pending(123, 0, datetime.now())
        sql, params = self.cur.execute.call_args[0]
        self.assertNotIn('123', sql)
        self.assertIn(123, params)


# ─────────────────────────────────────────────────────────────────────────────
# Verbindungsfehler — Propagation
# ─────────────────────────────────────────────────────────────────────────────

class TestConnectionErrors(unittest.TestCase):

    def _error(self):
        import psycopg2
        return psycopg2.OperationalError('connection refused')

    def test_insert_source_propagates_connection_error(self):
        import psycopg2
        db = DB(_CNF, _JOB_SERVER, _REFRESH)
        with patch('lib_db.psycopg2.connect', side_effect=self._error()):
            with self.assertRaises(psycopg2.OperationalError):
                db.insert_source('http://x.com', 2, datetime.now(), _JOB_SERVER, 'US')

    def test_update_result_propagates_connection_error(self):
        import psycopg2
        db = DB(_CNF, _JOB_SERVER, _REFRESH)
        with patch('lib_db.psycopg2.connect', side_effect=self._error()):
            with self.assertRaises(psycopg2.OperationalError):
                db.update_result(1, '0.0.0.0', 'x.com', 'http://x.com')

    def test_get_result_source_propagates_connection_error(self):
        import psycopg2
        db = DB(_CNF, _JOB_SERVER, _REFRESH)
        with patch('lib_db.psycopg2.connect', side_effect=self._error()):
            with self.assertRaises(psycopg2.OperationalError):
                db.get_result_source(1)

    def test_check_db_connection_catches_all_exceptions(self):
        db = DB(_CNF, _JOB_SERVER, _REFRESH)
        with patch('lib_db.psycopg2.connect', side_effect=Exception('unexpected')):
            self.assertFalse(db.check_db_connection())


# ─────────────────────────────────────────────────────────────────────────────
# SQL-Parametrisierung — kein Injection-Risiko
# ─────────────────────────────────────────────────────────────────────────────

class TestSQLParameterization(unittest.TestCase):
    """Stellt sicher dass User-Daten immer als %s-Parameter übergeben werden."""

    def _capture(self, method, *args, fetchone=None, fetchall=None):
        db, conn, cur = _mock_db(fetchone=fetchone, fetchall=fetchall)
        with patch('lib_db.psycopg2.connect', return_value=conn):
            getattr(db, method)(*args)
        return cur.execute.call_args[0]  # (sql, params)

    def test_insert_result_source_no_literal_values_in_sql(self):
        now = datetime.now()
        sql, params = self._capture('insert_result_source', 42, 2, now, 'server-x')
        self.assertNotIn('42', sql)
        self.assertNotIn('server-x', sql)
        self.assertIn('%s', sql)

    def test_insert_source_url_never_in_sql(self):
        url = "'; DROP TABLE source; --"
        sql, params = self._capture('insert_source', url, 2, datetime.now(), _JOB_SERVER, 'US')
        self.assertNotIn(url, sql)
        self.assertIn(url, params)

    def test_update_result_ip_never_in_sql(self):
        ip = '999.999.999.999'
        sql, params = self._capture('update_result', 1, ip, 'x.com', 'http://x.com')
        self.assertNotIn(ip, sql)
        self.assertIn(ip, params)

    def test_get_source_check_by_result_id_uses_tuple_param(self):
        sql, params = self._capture('get_source_check_by_result_id', 88)
        self.assertIsInstance(params, tuple)
        self.assertEqual(params, (88,))

    def test_replace_source_bin_binary_data_in_params_not_sql(self):
        data = b'\x00\x01\x02\x03'
        sql, params = self._capture('replace_source_bin', 3, data)
        self.assertIn(data, params)


if __name__ == '__main__':
    unittest.main()
