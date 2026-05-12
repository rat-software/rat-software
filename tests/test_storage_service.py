"""
Unit tests for rat-storage/storage_service.py

Covers:
  - /upload:  API-Key-Validierung, fehlende Datei, erfolgreicher Upload,
              Datei wird gespeichert, secure_filename sanitisiert Pfade
  - /view:    Ticket fehlt / ungültig / abgelaufen / falscher Dateiname,
              direktes PDF, ZIP-Extraktion (screenshot, HTML, PDF-in-ZIP,
              PDF-Stub-Fallback), Zieldatei fehlt im ZIP, beschädigtes ZIP
"""
import importlib.util
import io
import os
import sys
import shutil
import tempfile
import time as time_mod
import unittest
import zipfile
from unittest.mock import patch

from itsdangerous import URLSafeTimedSerializer

TEST_API_KEY = 'test-key-for-unit-tests'

# ── Load module ───────────────────────────────────────────────────────────────
_LIB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-storage', 'storage_service.py',
)
_spec = importlib.util.spec_from_file_location('storage_service', _LIB_PATH)
_mod = importlib.util.module_from_spec(_spec)
sys.modules['storage_service'] = _mod
_spec.loader.exec_module(_mod)

app = _mod.app
app.config['TESTING'] = True


def _make_ticket(filename, key=TEST_API_KEY):
    s = URLSafeTimedSerializer(key)
    return s.dumps({'filename': filename}, salt='source-view')


class _Base(unittest.TestCase):
    """Sets up a temp storage dir and resets module constants before each test."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._patches = [
            patch.object(_mod, 'API_KEY', TEST_API_KEY),
            patch.object(_mod, 'STORAGE_FOLDER', self.tmpdir),
        ]
        for p in self._patches:
            p.start()
        self.client = app.test_client()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        shutil.rmtree(self.tmpdir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# Index
# ─────────────────────────────────────────────────────────────────────────────

class TestIndex(_Base):

    def test_returns_200(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_response_indicates_running(self):
        self.assertIn(b'running', self.client.get('/').data)


# ─────────────────────────────────────────────────────────────────────────────
# Upload — API-Key-Validierung
# ─────────────────────────────────────────────────────────────────────────────

class TestUploadAPIKey(_Base):

    def test_no_api_key_returns_401(self):
        resp = self.client.post('/upload')
        self.assertEqual(resp.status_code, 401)

    def test_wrong_api_key_returns_401(self):
        resp = self.client.post('/upload', headers={'X-API-Key': 'wrong'})
        self.assertEqual(resp.status_code, 401)

    def test_correct_api_key_passes_auth_check(self):
        # No file attached — should reach file-validation (400), not auth (401)
        resp = self.client.post('/upload', headers={'X-API-Key': TEST_API_KEY})
        self.assertEqual(resp.status_code, 400)

    def test_error_body_on_unauthorized(self):
        import json
        resp = self.client.post('/upload', headers={'X-API-Key': 'bad'})
        self.assertIn('error', json.loads(resp.data))


# ─────────────────────────────────────────────────────────────────────────────
# Upload — Datei-Upload
# ─────────────────────────────────────────────────────────────────────────────

class TestUploadFiles(_Base):

    def _upload(self, filename, content=b'data'):
        return self.client.post(
            '/upload',
            data={'file': (io.BytesIO(content), filename)},
            content_type='multipart/form-data',
            headers={'X-API-Key': TEST_API_KEY},
        )

    def test_no_file_part_returns_400(self):
        resp = self.client.post('/upload', headers={'X-API-Key': TEST_API_KEY})
        self.assertEqual(resp.status_code, 400)

    def test_successful_upload_returns_200(self):
        self.assertEqual(self._upload('report.zip').status_code, 200)

    def test_response_contains_filename(self):
        self.assertIn(b'report.zip', self._upload('report.zip').data)

    def test_file_is_written_to_storage_folder(self):
        self._upload('saved.txt', b'hello')
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'saved.txt')))

    def test_file_content_is_preserved(self):
        self._upload('data.bin', b'\x00\x01\x02')
        with open(os.path.join(self.tmpdir, 'data.bin'), 'rb') as f:
            self.assertEqual(f.read(), b'\x00\x01\x02')

    def test_secure_filename_strips_path_traversal(self):
        import json
        resp = self._upload('../../../etc/passwd', b'bad')
        filename = json.loads(resp.data).get('filename', '')
        self.assertNotIn('..', filename)
        self.assertNotIn('/', filename)


# ─────────────────────────────────────────────────────────────────────────────
# View — Ticket-Validierung
# ─────────────────────────────────────────────────────────────────────────────

class TestViewTicket(_Base):

    def test_missing_ticket_returns_401(self):
        resp = self.client.get('/view/file.zip/html')
        self.assertEqual(resp.status_code, 401)

    def test_invalid_token_returns_403(self):
        resp = self.client.get('/view/file.zip/html?ticket=notavalidtoken')
        self.assertEqual(resp.status_code, 403)

    def test_ticket_signed_with_wrong_key_returns_403(self):
        ticket = _make_ticket('file.zip', key='other-key')
        resp = self.client.get(f'/view/file.zip/html?ticket={ticket}')
        self.assertEqual(resp.status_code, 403)

    def test_ticket_for_different_filename_returns_403(self):
        ticket = _make_ticket('other.zip')
        resp = self.client.get(f'/view/file.zip/html?ticket={ticket}')
        self.assertEqual(resp.status_code, 403)

    def test_valid_ticket_passes_auth(self):
        # File doesn't exist → 404, but NOT 401/403
        ticket = _make_ticket('missing.zip')
        resp = self.client.get(f'/view/missing.zip/html?ticket={ticket}')
        self.assertEqual(resp.status_code, 404)


# ─────────────────────────────────────────────────────────────────────────────
# View — direktes PDF
# ─────────────────────────────────────────────────────────────────────────────

class TestViewDirectPDF(_Base):

    def setUp(self):
        super().setUp()
        self.pdf_bytes = b'%PDF-1.4 fake pdf content'
        with open(os.path.join(self.tmpdir, 'doc.pdf'), 'wb') as f:
            f.write(self.pdf_bytes)

    def test_pdf_returns_200(self):
        ticket = _make_ticket('doc.pdf')
        resp = self.client.get(f'/view/doc.pdf/html?ticket={ticket}')
        self.assertEqual(resp.status_code, 200)

    def test_pdf_content_type(self):
        ticket = _make_ticket('doc.pdf')
        resp = self.client.get(f'/view/doc.pdf/html?ticket={ticket}')
        self.assertIn('application/pdf', resp.content_type)

    def test_pdf_content_matches_file(self):
        ticket = _make_ticket('doc.pdf')
        resp = self.client.get(f'/view/doc.pdf/html?ticket={ticket}')
        self.assertEqual(resp.data, self.pdf_bytes)


# ─────────────────────────────────────────────────────────────────────────────
# View — ZIP-Extraktion
# ─────────────────────────────────────────────────────────────────────────────

class TestViewZIPExtraction(_Base):

    def _make_zip(self, name, files: dict) -> str:
        path = os.path.join(self.tmpdir, name)
        with zipfile.ZipFile(path, 'w') as zf:
            for fname, content in files.items():
                zf.writestr(fname, content)
        return path

    def _get(self, filename, file_type):
        ticket = _make_ticket(filename)
        return self.client.get(f'/view/{filename}/{file_type}?ticket={ticket}')

    def test_screenshot_returns_jpeg(self):
        self._make_zip('s.zip', {'screenshot.jpg': b'\xff\xd8\xff fake'})
        resp = self._get('s.zip', 'screenshot')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('image/jpeg', resp.content_type)

    def test_screenshot_content_correct(self):
        content = b'\xff\xd8\xff fake jpeg bytes'
        self._make_zip('s.zip', {'screenshot.jpg': content})
        self.assertEqual(self._get('s.zip', 'screenshot').data, content)

    def test_html_source_returned(self):
        self._make_zip('s.zip', {'source.html': b'<html>hello</html>'})
        resp = self._get('s.zip', 'html')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/html', resp.content_type)

    def test_html_content_correct(self):
        content = b'<html>test</html>'
        self._make_zip('s.zip', {'source.html': content})
        self.assertEqual(self._get('s.zip', 'html').data, content)

    def test_pdf_in_zip_preferred_over_html(self):
        self._make_zip('s.zip', {
            'source.pdf': b'%PDF content',
            'source.html': b'<html></html>',
        })
        resp = self._get('s.zip', 'html')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/pdf', resp.content_type)

    def test_pdf_stub_in_html_falls_back_to_screenshot(self):
        # source.html contains only b"pdf" → serve screenshot.jpg
        self._make_zip('s.zip', {
            'source.html': b'pdf',
            'screenshot.jpg': b'\xff\xd8\xff fallback',
        })
        resp = self._get('s.zip', 'html')
        self.assertEqual(resp.status_code, 200)

    def test_missing_screenshot_in_zip_returns_404(self):
        self._make_zip('s.zip', {'source.html': b'content'})
        resp = self._get('s.zip', 'screenshot')
        self.assertEqual(resp.status_code, 404)

    def test_missing_zip_file_returns_404(self):
        resp = self._get('nonexistent.zip', 'html')
        self.assertEqual(resp.status_code, 404)

    def test_corrupted_zip_returns_500(self):
        with open(os.path.join(self.tmpdir, 'bad.zip'), 'wb') as f:
            f.write(b'this is not a zip file at all')
        resp = self._get('bad.zip', 'html')
        self.assertEqual(resp.status_code, 500)


# ─────────────────────────────────────────────────────────────────────────────
# View — ungültige Tickets (erweitert)
# ─────────────────────────────────────────────────────────────────────────────

class TestViewInvalidTickets(_Base):

    def test_empty_string_ticket_returns_401(self):
        # Empty string is falsy → treated as missing ticket, not invalid
        resp = self.client.get('/view/file.zip/html?ticket=')
        self.assertEqual(resp.status_code, 401)

    def test_random_garbage_ticket_returns_403(self):
        resp = self.client.get('/view/file.zip/html?ticket=abc123xyz!!!')
        self.assertEqual(resp.status_code, 403)

    def test_tampered_ticket_returns_403(self):
        ticket = _make_ticket('file.zip')
        # Flip the last character to break the signature
        tampered = ticket[:-1] + ('A' if ticket[-1] != 'A' else 'B')
        resp = self.client.get(f'/view/file.zip/html?ticket={tampered}')
        self.assertEqual(resp.status_code, 403)

    def test_expired_ticket_returns_403(self):
        ticket = _make_ticket('file.zip')
        # Simulate 5 hours in the future — max_age is 4 h (14400 s)
        with patch('time.time', return_value=time_mod.time() + 5 * 3600):
            resp = self.client.get(f'/view/file.zip/html?ticket={ticket}')
        self.assertEqual(resp.status_code, 403)

    def test_ticket_for_wrong_filename_returns_403(self):
        ticket = _make_ticket('other.zip')
        resp = self.client.get(f'/view/file.zip/html?ticket={ticket}')
        self.assertEqual(resp.status_code, 403)

    def test_ticket_signed_with_wrong_key_returns_403(self):
        ticket = _make_ticket('file.zip', key='completely-different-key')
        resp = self.client.get(f'/view/file.zip/html?ticket={ticket}')
        self.assertEqual(resp.status_code, 403)


# ─────────────────────────────────────────────────────────────────────────────
# View — Datei-Auslieferung (Response-Details)
# ─────────────────────────────────────────────────────────────────────────────

class TestViewFileDelivery(_Base):

    def setUp(self):
        super().setUp()
        self.zip_name = 'page.zip'

    def _make_zip(self, files: dict):
        path = os.path.join(self.tmpdir, self.zip_name)
        with zipfile.ZipFile(path, 'w') as zf:
            for fname, content in files.items():
                zf.writestr(fname, content)

    def _get(self, file_type):
        ticket = _make_ticket(self.zip_name)
        return self.client.get(
            f'/view/{self.zip_name}/{file_type}?ticket={ticket}'
        )

    def test_html_content_type_includes_charset_utf8(self):
        self._make_zip({'source.html': b'<html>ok</html>'})
        resp = self._get('html')
        self.assertIn('charset=utf-8', resp.content_type)

    def test_html_body_matches_zip_content(self):
        content = b'<html><body>hello world</body></html>'
        self._make_zip({'source.html': content})
        self.assertEqual(self._get('html').data, content)

    def test_screenshot_body_matches_zip_content(self):
        content = b'\xff\xd8\xff exact jpeg bytes'
        self._make_zip({'screenshot.jpg': content})
        self.assertEqual(self._get('screenshot').data, content)

    def test_pdf_in_zip_body_matches_content(self):
        content = b'%PDF-1.4 exact pdf bytes'
        self._make_zip({'source.pdf': content})
        self.assertEqual(self._get('html').data, content)

    def test_screenshot_content_type_is_jpeg(self):
        self._make_zip({'screenshot.jpg': b'\xff\xd8\xff fake'})
        self.assertIn('image/jpeg', self._get('screenshot').content_type)

    def test_any_non_screenshot_type_serves_html(self):
        content = b'<html>test</html>'
        self._make_zip({'source.html': content})
        # file_type 'source' is not 'screenshot' → should serve HTML
        ticket = _make_ticket(self.zip_name)
        resp = self.client.get(
            f'/view/{self.zip_name}/source?ticket={ticket}'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/html', resp.content_type)


if __name__ == '__main__':
    unittest.main()
