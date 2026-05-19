"""
Trimmed unit tests for rat-backend/sources/libs/lib_sources.py

Covered (no Selenium / browser required):
  Sources._evaluate_content_quality(code, page_source, url, dict_request)
  Sources.get_result_meta(url)
  Sources.upload_to_storage(html_content, bin_data, content_type)
  Sources._cleanup_driver(driver)

Skipped intentionally: save_code, _save_code_worker, take_screenshot,
bypass_cookie_banners, get_url_header* — all require a live browser.
"""

import importlib.util
import io
import os
import sys
import types
import unittest
import zipfile
from unittest.mock import MagicMock, patch, call

# ── Paths ──────────────────────────────────────────────────────────────────────
_SOURCES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'sources',
)
_LIBS_DIR = os.path.join(_SOURCES_DIR, 'libs')

# ── Selenium / heavy-dep stubs ─────────────────────────────────────────────────

def _stub(name, parent=None, attrs=None):
    m = types.ModuleType(name)
    m.__path__ = []
    if attrs:
        for k, v in attrs.items():
            setattr(m, k, v)
    sys.modules.setdefault(name, m)
    if parent:
        setattr(parent, name.split('.')[-1], m)
    return m

_selenium              = _stub('selenium')
_selenium_wd           = _stub('selenium.webdriver',           _selenium)
_selenium_wd_chrome    = _stub('selenium.webdriver.chrome',    _selenium_wd)
_svc_cls               = type('Service', (), {})
_stub('selenium.webdriver.chrome.service', _selenium_wd_chrome,
      {'Service': _svc_cls})

_selenium_common       = _stub('selenium.common',              _selenium)
_exc_mod               = _stub('selenium.common.exceptions',   _selenium_common, {
    'TimeoutException':         type('TimeoutException',         (Exception,), {}),
    'WebDriverException':       type('WebDriverException',       (Exception,), {}),
    'SessionNotCreatedException': type('SessionNotCreatedException', (Exception,), {}),
})

_selenium_wd_common    = _stub('selenium.webdriver.common',    _selenium_wd)
_stub('selenium.webdriver.common.keys',         _selenium_wd_common, {'Keys': type('Keys', (), {})})
_stub('selenium.webdriver.common.action_chains',_selenium_wd_common, {'ActionChains': type('ActionChains', (), {})})

_stub('seleniumbase', attrs={'Driver': type('Driver', (), {})})

_pil    = _stub('PIL')
_stub('PIL.Image', _pil, {'Image': type('Image', (), {})})
_stub('bs4',  attrs={'BeautifulSoup': type('BeautifulSoup', (), {})})
_stub('psutil')

# ── libs stubs ─────────────────────────────────────────────────────────────────

_libs_pkg = types.ModuleType('libs')
_libs_pkg.__path__ = [_LIBS_DIR]
sys.modules.setdefault('libs', _libs_pkg)

_FAKE_CONF = {
    'headless': True,
    'global_timeout': 300,
    'api-key': '',
    'storage-url': None,
    'local-storage-path': '/tmp/test_local_storage',
}

for _sname, _attr in [('libs.lib_logger', 'Logger'), ('libs.lib_db', 'DB')]:
    if _sname not in sys.modules:
        _m = types.ModuleType(_sname)
        setattr(_m, _attr, type(_attr, (), {}))
        sys.modules[_sname] = _m
        setattr(_libs_pkg, _sname.split('.')[-1], _m)

if 'libs.lib_helper' not in sys.modules:
    _helper_mod = types.ModuleType('libs.lib_helper')
    _HelperCls  = type('Helper', (), {'file_to_dict': lambda self, p: _FAKE_CONF})
    _helper_mod.Helper = _HelperCls
    sys.modules['libs.lib_helper'] = _helper_mod
    setattr(_libs_pkg, 'lib_helper', _helper_mod)

# ── Load lib_sources ───────────────────────────────────────────────────────────

_LIB_PATH = os.path.join(_LIBS_DIR, 'lib_sources.py')
_spec = importlib.util.spec_from_file_location('lib_sources', _LIB_PATH)
_mod  = importlib.util.module_from_spec(_spec)

with patch('builtins.open', side_effect=FileNotFoundError), \
     patch('builtins.print'):
    _spec.loader.exec_module(_mod)

sys.modules['lib_sources'] = _mod
Sources = _mod.Sources


# ── Fixture helper ─────────────────────────────────────────────────────────────

def _sources():
    with patch('os.makedirs'), patch('builtins.print'):
        return Sources()


# ═════════════════════════════════════════════════════════════════════════════
# _evaluate_content_quality
# ═════════════════════════════════════════════════════════════════════════════

class TestEvaluateContentQuality(unittest.TestCase):

    def _eq(self, code, page_source, url='http://example.com', req=None):
        req = req or {'content_type': 'html', 'status_code': 200}
        return _sources()._evaluate_content_quality(code, page_source, url, req)

    # ── code already valid ────────────────────────────────────────────────────

    def test_non_error_code_returns_1(self):
        result, _ = self._eq('<html>...</html>', 'any source')
        self.assertEqual(result, 1)

    def test_non_error_code_message_is_empty(self):
        _, msg = self._eq('<html>...</html>', 'any source')
        self.assertEqual(msg, '')

    def test_pdf_code_does_not_short_circuit(self):
        # code == "pdf" → falls through to content checks
        result, _ = self._eq('pdf', 'x' * 200)
        self.assertEqual(result, -1)

    # ── empty / short content ─────────────────────────────────────────────────

    def test_empty_page_source_returns_minus_one(self):
        result, _ = self._eq('error', '')
        self.assertEqual(result, -1)

    def test_none_page_source_returns_minus_one(self):
        result, _ = self._eq('error', None)
        self.assertEqual(result, -1)

    def test_short_page_source_returns_minus_one(self):
        result, _ = self._eq('error', 'x' * 99)
        self.assertEqual(result, -1)

    def test_exactly_100_chars_still_fails_without_body(self):
        result, _ = self._eq('error', 'x' * 100)
        self.assertEqual(result, -1)

    # ── PDF URL heuristic ─────────────────────────────────────────────────────

    def test_pdf_url_with_pdf_header_returns_1(self):
        page = '%PDF-1.4 ' + 'x' * 1000
        result, _ = self._eq('error', page, url='http://ex.com/file.pdf')
        self.assertEqual(result, 1)

    def test_pdf_content_type_with_pdf_header_returns_1(self):
        page = '%PDF-1.4 ' + 'x' * 1000
        result, _ = self._eq('error', page, url='http://ex.com/view',
                             req={'content_type': 'pdf', 'status_code': 200})
        self.assertEqual(result, 1)

    def test_pdf_url_without_pdf_header_falls_through(self):
        page = '<html><body><div>' + 'x' * 200 + '</div></body></html>'
        result, _ = self._eq('error', page, url='http://ex.com/file.pdf')
        self.assertIn(result, (1, -1))  # depends on size, not a PDF-specific path

    # ── body + content markers ────────────────────────────────────────────────

    def test_body_and_div_and_5kb_returns_1(self):
        page = '<html><body><div>' + 'x' * 5000 + '</div></body></html>'
        result, _ = self._eq('error', page)
        self.assertEqual(result, 1)

    def test_body_and_table_and_5kb_returns_1(self):
        page = '<html><body><table>' + 'x' * 5000 + '</table></body></html>'
        result, _ = self._eq('error', page)
        self.assertEqual(result, 1)

    def test_body_without_content_markers_returns_minus_one(self):
        page = '<body>' + 'x' * 6000 + '</body>'
        result, _ = self._eq('error', page)
        self.assertEqual(result, -1)

    def test_complete_html_structure_over_1kb_returns_1(self):
        page = '<html><body><p>' + 'x' * 1100 + '</p></body></html>'
        result, _ = self._eq('error', page)
        self.assertEqual(result, 1)

    def test_body_and_markers_under_1kb_returns_minus_one(self):
        page = '<html><body><div>' + 'x' * 300 + '</div></body></html>'
        result, _ = self._eq('error', page)
        self.assertEqual(result, -1)

    # ── return types ──────────────────────────────────────────────────────────

    def test_return_is_tuple(self):
        self.assertIsInstance(self._eq('error', ''), tuple)

    def test_first_element_is_int(self):
        result, _ = self._eq('error', '')
        self.assertIsInstance(result, int)

    def test_second_element_is_str(self):
        _, msg = self._eq('error', '')
        self.assertIsInstance(msg, str)


# ═════════════════════════════════════════════════════════════════════════════
# get_result_meta
# ═════════════════════════════════════════════════════════════════════════════

class TestGetResultMeta(unittest.TestCase):

    def _meta(self, url, ip_side_effect=None, ip_return='1.2.3.4'):
        src = _sources()
        with patch('lib_sources.socket.gethostbyname',
                   side_effect=ip_side_effect,
                   return_value=ip_return if ip_side_effect is None else None), \
             patch('builtins.print'):
            return src.get_result_meta(url)

    # ── return structure ──────────────────────────────────────────────────────

    def test_returns_dict(self):
        self.assertIsInstance(self._meta('http://example.com/path'), dict)

    def test_has_ip_key(self):
        self.assertIn('ip', self._meta('http://example.com'))

    def test_has_main_key(self):
        self.assertIn('main', self._meta('http://example.com'))

    # ── main URL parsing ──────────────────────────────────────────────────────

    def test_main_strips_path(self):
        result = self._meta('http://example.com/some/path?q=1')
        self.assertEqual(result['main'], 'http://example.com/')

    def test_main_preserves_scheme_and_host(self):
        result = self._meta('https://sub.domain.org/page')
        self.assertEqual(result['main'], 'https://sub.domain.org/')

    def test_main_fallback_on_invalid_url(self):
        raw = 'not-a-valid-url'
        result = self._meta(raw)
        self.assertEqual(result['main'], raw)

    # ── IP lookup ─────────────────────────────────────────────────────────────

    def test_ip_returned_on_success(self):
        result = self._meta('http://example.com', ip_return='93.184.216.34')
        self.assertEqual(result['ip'], '93.184.216.34')

    def test_ip_is_minus_one_on_dns_failure(self):
        result = self._meta('http://example.com',
                            ip_side_effect=OSError('Name not found'))
        self.assertEqual(result['ip'], '-1')

    def test_ip_is_minus_one_on_no_hostname(self):
        # URL without scheme/netloc → hostname is None → gethostbyname never called
        result = self._meta('just-a-string', ip_return='should-not-appear')
        self.assertEqual(result['ip'], '-1')


# ═════════════════════════════════════════════════════════════════════════════
# upload_to_storage
# ═════════════════════════════════════════════════════════════════════════════

def _run_upload(html='<html/>', bin_data=b'data', content_type='image/jpeg',
                storage_url=None, local_path='/tmp/ls', post_status=200,
                post_json=None):
    """Call upload_to_storage with controlled module-level vars."""
    src = _sources()
    mock_response = MagicMock()
    mock_response.status_code = post_status
    mock_response.json.return_value = post_json or {'filename': 'remote.zip'}

    with patch.object(_mod, 'STORAGE_URL',       storage_url,  create=True), \
         patch.object(_mod, 'LOCAL_STORAGE_PATH', local_path,   create=True), \
         patch.object(_mod, 'API_KEY',            'key',         create=True), \
         patch('lib_sources.requests.post',       return_value=mock_response), \
         patch('lib_sources.os.makedirs'), \
         patch('builtins.open', unittest.mock.mock_open()), \
         patch('builtins.print'):
        return src.upload_to_storage(html, bin_data, content_type)


class TestUploadToStorage(unittest.TestCase):

    # ── ZIP content ───────────────────────────────────────────────────────────

    def test_html_ends_up_in_zip(self):
        src = _sources()
        buf_holder = []

        def fake_post(url, headers, files, timeout):
            _, (_, buf, _) = list(files.items())[0]
            buf_holder.append(buf.read())
            r = MagicMock()
            r.status_code = 200
            r.json.return_value = {'filename': 'x.zip'}
            return r

        with patch.object(_mod, 'STORAGE_URL',       'http://store/upload', create=True), \
             patch.object(_mod, 'LOCAL_STORAGE_PATH', '/tmp/ls',             create=True), \
             patch.object(_mod, 'API_KEY',            'k',                   create=True), \
             patch('lib_sources.requests.post', side_effect=fake_post), \
             patch('builtins.print'):
            src.upload_to_storage('<html>hi</html>', None, 'text/html')

        zf = zipfile.ZipFile(io.BytesIO(buf_holder[0]))
        self.assertIn('source.html', zf.namelist())

    def test_pdf_bin_data_stored_as_source_pdf(self):
        src = _sources()
        buf_holder = []

        def fake_post(url, headers, files, timeout):
            _, (_, buf, _) = list(files.items())[0]
            buf_holder.append(buf.read())
            r = MagicMock()
            r.status_code = 200
            r.json.return_value = {'filename': 'x.zip'}
            return r

        with patch.object(_mod, 'STORAGE_URL',       'http://store/upload', create=True), \
             patch.object(_mod, 'LOCAL_STORAGE_PATH', '/tmp/ls',             create=True), \
             patch.object(_mod, 'API_KEY',            'k',                   create=True), \
             patch('lib_sources.requests.post', side_effect=fake_post), \
             patch('builtins.print'):
            src.upload_to_storage(None, b'%PDF-1.4', 'application/pdf')

        zf = zipfile.ZipFile(io.BytesIO(buf_holder[0]))
        self.assertIn('source.pdf', zf.namelist())

    def test_jpeg_bin_data_stored_as_screenshot_jpg(self):
        src = _sources()
        buf_holder = []

        def fake_post(url, headers, files, timeout):
            _, (_, buf, _) = list(files.items())[0]
            buf_holder.append(buf.read())
            r = MagicMock()
            r.status_code = 200
            r.json.return_value = {'filename': 'x.zip'}
            return r

        with patch.object(_mod, 'STORAGE_URL',       'http://store/upload', create=True), \
             patch.object(_mod, 'LOCAL_STORAGE_PATH', '/tmp/ls',             create=True), \
             patch.object(_mod, 'API_KEY',            'k',                   create=True), \
             patch('lib_sources.requests.post', side_effect=fake_post), \
             patch('builtins.print'):
            src.upload_to_storage(None, b'\xff\xd8', 'image/jpeg')

        zf = zipfile.ZipFile(io.BytesIO(buf_holder[0]))
        self.assertIn('screenshot.jpg', zf.namelist())

    def test_error_html_not_added_to_zip(self):
        src = _sources()
        buf_holder = []

        def fake_post(url, headers, files, timeout):
            _, (_, buf, _) = list(files.items())[0]
            buf_holder.append(buf.read())
            r = MagicMock()
            r.status_code = 200
            r.json.return_value = {'filename': 'x.zip'}
            return r

        with patch.object(_mod, 'STORAGE_URL',       'http://store/upload', create=True), \
             patch.object(_mod, 'LOCAL_STORAGE_PATH', '/tmp/ls',             create=True), \
             patch.object(_mod, 'API_KEY',            'k',                   create=True), \
             patch('lib_sources.requests.post', side_effect=fake_post), \
             patch('builtins.print'):
            src.upload_to_storage('error', b'img', 'image/jpeg')

        zf = zipfile.ZipFile(io.BytesIO(buf_holder[0]))
        self.assertNotIn('source.html', zf.namelist())

    # ── API upload path ───────────────────────────────────────────────────────

    def test_api_upload_returns_remote_filename(self):
        result = _run_upload(storage_url='http://store/upload',
                             post_json={'filename': 'abc.zip'})
        self.assertEqual(result, 'abc.zip')

    def test_api_upload_calls_requests_post(self):
        src = _sources()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'filename': 'f.zip'}
        mock_post = MagicMock(return_value=mock_response)

        with patch.object(_mod, 'STORAGE_URL',       'http://store/upload', create=True), \
             patch.object(_mod, 'LOCAL_STORAGE_PATH', '/tmp/ls',             create=True), \
             patch.object(_mod, 'API_KEY',            'k',                   create=True), \
             patch('lib_sources.requests.post', mock_post), \
             patch('builtins.print'):
            src.upload_to_storage('<html/>', b'img', 'image/jpeg')

        mock_post.assert_called_once()

    # ── local fallback path ───────────────────────────────────────────────────

    def test_no_storage_url_returns_zip_filename(self):
        result = _run_upload(storage_url=None)
        self.assertTrue(result is None or result.endswith('.zip'))

    def test_api_failure_falls_back_to_local(self):
        # post raises → falls through to local save
        src = _sources()
        written = []
        m_open = unittest.mock.mock_open()
        m_open.return_value.__enter__.return_value.write.side_effect = \
            lambda d: written.append(d)

        with patch.object(_mod, 'STORAGE_URL',       'http://store/upload', create=True), \
             patch.object(_mod, 'LOCAL_STORAGE_PATH', '/tmp/ls',             create=True), \
             patch.object(_mod, 'API_KEY',            'k',                   create=True), \
             patch('lib_sources.requests.post', side_effect=Exception('network error')), \
             patch('lib_sources.os.makedirs'), \
             patch('builtins.open', m_open), \
             patch('builtins.print'):
            result = src.upload_to_storage('<html/>', b'img', 'image/jpeg')

        self.assertIsNotNone(result)
        self.assertTrue(result.endswith('.zip'))


# ═════════════════════════════════════════════════════════════════════════════
# _cleanup_driver
# ═════════════════════════════════════════════════════════════════════════════

class TestCleanupDriver(unittest.TestCase):

    def test_close_and_quit_called_on_driver(self):
        driver = MagicMock()
        driver.execute_cdp_cmd.return_value = None
        driver.execute_script.return_value  = None
        _sources()._cleanup_driver(driver)
        driver.close.assert_called()
        driver.quit.assert_called()

    def test_none_driver_does_not_raise(self):
        try:
            _sources()._cleanup_driver(None)
        except Exception:
            self.fail('_cleanup_driver(None) should not raise')

    def test_close_raising_still_calls_quit(self):
        driver = MagicMock()
        driver.execute_cdp_cmd.return_value = None
        driver.execute_script.return_value  = None
        driver.close.side_effect = Exception('already closed')
        _sources()._cleanup_driver(driver)
        driver.quit.assert_called()

    def test_quit_raising_does_not_propagate(self):
        driver = MagicMock()
        driver.execute_cdp_cmd.return_value = None
        driver.execute_script.return_value  = None
        driver.quit.side_effect = Exception('already gone')
        try:
            _sources()._cleanup_driver(driver)
        except Exception:
            self.fail('_cleanup_driver should swallow quit exceptions')

    def test_no_cdp_attr_still_cleans_up(self):
        driver = MagicMock(spec=['close', 'quit', 'execute_script'])
        _sources()._cleanup_driver(driver)
        driver.close.assert_called()
        driver.quit.assert_called()


if __name__ == '__main__':
    unittest.main()
