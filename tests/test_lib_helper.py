"""
Unit tests for rat-backend/sources/libs/lib_helper.py

Covers Helper.file_to_dict:
  - valid JSON (flat, nested, list, unicode, empty object)
  - missing file  → FileNotFoundError
  - invalid JSON  → json.JSONDecodeError
  - empty file    → json.JSONDecodeError
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest

# Load lib_helper.py directly so no package setup is required
_LIB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'sources', 'libs', 'lib_helper.py',
)
_spec = importlib.util.spec_from_file_location('lib_helper', _LIB_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

Helper = _mod.Helper


def _write_tmp(content: str, suffix='.json') -> str:
    """Write content to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile(mode='w', suffix=suffix,
                                    encoding='utf-8', delete=False)
    f.write(content)
    f.close()
    return f.name


class TestFileToDictValidJson(unittest.TestCase):

    def setUp(self):
        self.h = Helper()
        self._files = []

    def tearDown(self):
        for p in self._files:
            os.unlink(p)

    def _tmp(self, content):
        p = _write_tmp(content)
        self._files.append(p)
        return p

    def test_flat_dict(self):
        path = self._tmp('{"key": "value", "number": 42}')
        result = self.h.file_to_dict(path)
        self.assertEqual(result, {"key": "value", "number": 42})

    def test_nested_dict(self):
        data = {"outer": {"inner": [1, 2, 3]}}
        path = self._tmp(json.dumps(data))
        self.assertEqual(self.h.file_to_dict(path), data)

    def test_top_level_list(self):
        path = self._tmp('[1, 2, 3]')
        self.assertEqual(self.h.file_to_dict(path), [1, 2, 3])

    def test_empty_object(self):
        path = self._tmp('{}')
        self.assertEqual(self.h.file_to_dict(path), {})

    def test_unicode_values(self):
        data = {"city": "München", "emoji": "☕"}
        path = self._tmp(json.dumps(data, ensure_ascii=False))
        self.assertEqual(self.h.file_to_dict(path), data)

    def test_boolean_and_null_values(self):
        data = {"active": True, "value": None, "count": 0}
        path = self._tmp(json.dumps(data))
        self.assertEqual(self.h.file_to_dict(path), data)

    def test_returns_dict_type(self):
        path = self._tmp('{"x": 1}')
        self.assertIsInstance(self.h.file_to_dict(path), dict)


class TestFileToDictMissingFile(unittest.TestCase):

    def setUp(self):
        self.h = Helper()

    def test_nonexistent_path_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.h.file_to_dict('/nonexistent/path/file.json')

    def test_empty_path_raises(self):
        with self.assertRaises((FileNotFoundError, OSError)):
            self.h.file_to_dict('')


class TestFileToDictInvalidContent(unittest.TestCase):

    def setUp(self):
        self.h = Helper()
        self._files = []

    def tearDown(self):
        for p in self._files:
            os.unlink(p)

    def _tmp(self, content):
        p = _write_tmp(content)
        self._files.append(p)
        return p

    def test_plain_text_raises_json_decode_error(self):
        path = self._tmp('this is not json')
        with self.assertRaises(json.JSONDecodeError):
            self.h.file_to_dict(path)

    def test_truncated_json_raises_json_decode_error(self):
        path = self._tmp('{"key": "val')
        with self.assertRaises(json.JSONDecodeError):
            self.h.file_to_dict(path)

    def test_single_quotes_raises_json_decode_error(self):
        path = self._tmp("{'key': 'value'}")
        with self.assertRaises(json.JSONDecodeError):
            self.h.file_to_dict(path)

    def test_trailing_comma_raises_json_decode_error(self):
        path = self._tmp('{"key": "value",}')
        with self.assertRaises(json.JSONDecodeError):
            self.h.file_to_dict(path)

    def test_empty_file_raises_json_decode_error(self):
        path = self._tmp('')
        with self.assertRaises(json.JSONDecodeError):
            self.h.file_to_dict(path)

    def test_whitespace_only_raises_json_decode_error(self):
        path = self._tmp('   \n\t  ')
        with self.assertRaises(json.JSONDecodeError):
            self.h.file_to_dict(path)

    def test_html_content_raises_json_decode_error(self):
        path = self._tmp('<html><body>hello</body></html>')
        with self.assertRaises(json.JSONDecodeError):
            self.h.file_to_dict(path)


if __name__ == '__main__':
    unittest.main()
