"""
Unit tests for rat-backend/query_sampler/generate_user_credentials.py

Three functions are tested:

  parse_raw_query_params(data)
      Decodes a raw HTTP GET request and returns a {key: value} dict.

  get_authorization_code(passthrough_val)
      Opens a local socket, reads one request, validates code + state,
      sends an HTTP response, and returns the authorization code.
      Calls sys.exit(1) on validation failure.

  main(client_secrets_path, scopes)
      Orchestrates the OAuth2 flow: creates a Flow, opens the auth URL,
      waits for the callback, fetches a token, and prints the refresh token.
"""

import importlib.util
import os
import sys
import socket
import types
import unittest
from unittest.mock import MagicMock, call, patch

# ── Path ──────────────────────────────────────────────────────────────────────
_QS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'rat-backend', 'query_sampler',
)
_GUC_PATH = os.path.join(_QS_DIR, 'generate_user_credentials.py')

# ── Stub google_auth_oauthlib ─────────────────────────────────────────────────
_flow_pkg = types.ModuleType('google_auth_oauthlib')
_flow_pkg.__path__ = []
_flow_mod  = types.ModuleType('google_auth_oauthlib.flow')
_flow_mod.Flow = MagicMock()
sys.modules.setdefault('google_auth_oauthlib',      _flow_pkg)
sys.modules.setdefault('google_auth_oauthlib.flow', _flow_mod)

# ── Load module ───────────────────────────────────────────────────────────────
_spec = importlib.util.spec_from_file_location('generate_user_credentials', _GUC_PATH)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
sys.modules['generate_user_credentials'] = _mod

import generate_user_credentials as guc


# ── Socket helpers ────────────────────────────────────────────────────────────

def _make_socket_stack(raw_data: bytes):
    """Return (patched socket class, connection mock) for get_authorization_code tests."""
    conn = MagicMock()
    conn.recv.return_value = raw_data

    sock_instance = MagicMock()
    sock_instance.accept.return_value = (conn, ('127.0.0.1', 54321))

    sock_class = MagicMock(return_value=sock_instance)
    return sock_class, conn


def _raw_request(code=None, state='tok', error=None):
    """Build a minimal raw GET query string as bytes."""
    pairs = []
    if code:
        pairs.append(f'code={code}')
    if error:
        pairs.append(f'error={error}')
    pairs.append(f'state={state}')
    qs = '&'.join(pairs)
    return f'GET /?{qs} HTTP/1.1\r\n'.encode()


# ═════════════════════════════════════════════════════════════════════════════
# Module-level constants
# ═════════════════════════════════════════════════════════════════════════════

class TestModuleConstants(unittest.TestCase):

    def test_scope_contains_adwords(self):
        self.assertIn('adwords', guc._SCOPE)

    def test_scope_is_googleapis_url(self):
        self.assertTrue(guc._SCOPE.startswith('https://www.googleapis.com/'))

    def test_server_is_localhost(self):
        self.assertEqual(guc._SERVER, '127.0.0.1')

    def test_port_is_integer(self):
        self.assertIsInstance(guc._PORT, int)

    def test_port_is_8080(self):
        self.assertEqual(guc._PORT, 8080)

    def test_redirect_uri_contains_server(self):
        self.assertIn(guc._SERVER, guc._REDIRECT_URI)

    def test_redirect_uri_contains_port(self):
        self.assertIn(str(guc._PORT), guc._REDIRECT_URI)

    def test_redirect_uri_is_http(self):
        self.assertTrue(guc._REDIRECT_URI.startswith('http://'))


# ═════════════════════════════════════════════════════════════════════════════
# parse_raw_query_params
# ═════════════════════════════════════════════════════════════════════════════

class TestParseRawQueryParams(unittest.TestCase):

    def _parse(self, qs_string):
        raw = f'GET /?{qs_string} HTTP/1.1\r\n'.encode()
        return guc.parse_raw_query_params(raw)

    def test_returns_dict(self):
        result = self._parse('code=abc&state=xyz')
        self.assertIsInstance(result, dict)

    def test_extracts_code(self):
        result = self._parse('code=abc123&state=xyz')
        self.assertEqual(result['code'], 'abc123')

    def test_extracts_state(self):
        result = self._parse('code=abc&state=mytoken')
        self.assertEqual(result['state'], 'mytoken')

    def test_extracts_error_param(self):
        result = self._parse('error=access_denied&state=xyz')
        self.assertEqual(result['error'], 'access_denied')

    def test_single_param(self):
        result = self._parse('code=only')
        self.assertEqual(result['code'], 'only')

    def test_multiple_params_all_present(self):
        result = self._parse('a=1&b=2&c=3')
        self.assertEqual(result, {'a': '1', 'b': '2', 'c': '3'})

    def test_result_has_correct_number_of_keys(self):
        result = self._parse('code=x&state=y')
        self.assertEqual(len(result), 2)


# ═════════════════════════════════════════════════════════════════════════════
# get_authorization_code
# ═════════════════════════════════════════════════════════════════════════════

class TestGetAuthorizationCode(unittest.TestCase):

    # ── Success path ──────────────────────────────────────────────────────────

    def test_returns_authorization_code_on_success(self):
        sock_cls, conn = _make_socket_stack(_raw_request(code='mycode', state='tok'))
        with patch('generate_user_credentials.socket.socket', sock_cls):
            result = guc.get_authorization_code('tok')
        self.assertEqual(result, 'mycode')

    def test_sends_http_200_response(self):
        sock_cls, conn = _make_socket_stack(_raw_request(code='c', state='s'))
        with patch('generate_user_credentials.socket.socket', sock_cls):
            guc.get_authorization_code('s')
        sent = conn.sendall.call_args[0][0].decode()
        self.assertIn('HTTP/1.1 200 OK', sent)

    def test_response_contains_success_message(self):
        sock_cls, conn = _make_socket_stack(_raw_request(code='c', state='s'))
        with patch('generate_user_credentials.socket.socket', sock_cls):
            guc.get_authorization_code('s')
        sent = conn.sendall.call_args[0][0].decode()
        self.assertIn('Authorization code was successfully retrieved', sent)

    def test_connection_is_closed_on_success(self):
        sock_cls, conn = _make_socket_stack(_raw_request(code='c', state='s'))
        with patch('generate_user_credentials.socket.socket', sock_cls):
            guc.get_authorization_code('s')
        conn.close.assert_called_once()

    def test_socket_configured_with_reuse_addr(self):
        sock_cls, conn = _make_socket_stack(_raw_request(code='c', state='s'))
        with patch('generate_user_credentials.socket.socket', sock_cls):
            guc.get_authorization_code('s')
        sock_instance = sock_cls.return_value
        sock_instance.setsockopt.assert_called_once_with(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )

    def test_socket_bound_to_correct_address(self):
        sock_cls, conn = _make_socket_stack(_raw_request(code='c', state='s'))
        with patch('generate_user_credentials.socket.socket', sock_cls):
            guc.get_authorization_code('s')
        sock_instance = sock_cls.return_value
        sock_instance.bind.assert_called_once_with((guc._SERVER, guc._PORT))

    # ── Missing code ──────────────────────────────────────────────────────────

    def test_calls_sys_exit_when_no_code(self):
        sock_cls, conn = _make_socket_stack(_raw_request(error='access_denied', state='s'))
        with patch('generate_user_credentials.socket.socket', sock_cls), \
             patch('generate_user_credentials.sys.exit') as mock_exit:
            guc.get_authorization_code('s')
        mock_exit.assert_called_once_with(1)

    def test_response_sent_even_when_no_code(self):
        sock_cls, conn = _make_socket_stack(_raw_request(error='access_denied', state='s'))
        with patch('generate_user_credentials.socket.socket', sock_cls), \
             patch('generate_user_credentials.sys.exit'):
            guc.get_authorization_code('s')
        conn.sendall.assert_called_once()

    def test_connection_closed_even_when_no_code(self):
        sock_cls, conn = _make_socket_stack(_raw_request(error='access_denied', state='s'))
        with patch('generate_user_credentials.socket.socket', sock_cls), \
             patch('generate_user_credentials.sys.exit'):
            guc.get_authorization_code('s')
        conn.close.assert_called_once()

    def test_error_message_in_response_when_no_code(self):
        sock_cls, conn = _make_socket_stack(_raw_request(error='access_denied', state='s'))
        with patch('generate_user_credentials.socket.socket', sock_cls), \
             patch('generate_user_credentials.sys.exit'):
            guc.get_authorization_code('s')
        sent = conn.sendall.call_args[0][0].decode()
        self.assertIn('Failed to retrieve authorization code', sent)

    # ── State mismatch ────────────────────────────────────────────────────────

    def test_calls_sys_exit_when_state_mismatch(self):
        sock_cls, conn = _make_socket_stack(_raw_request(code='c', state='wrong'))
        with patch('generate_user_credentials.socket.socket', sock_cls), \
             patch('generate_user_credentials.sys.exit') as mock_exit:
            guc.get_authorization_code('expected')
        mock_exit.assert_called_once_with(1)

    def test_state_mismatch_message_in_response(self):
        sock_cls, conn = _make_socket_stack(_raw_request(code='c', state='wrong'))
        with patch('generate_user_credentials.socket.socket', sock_cls), \
             patch('generate_user_credentials.sys.exit'):
            guc.get_authorization_code('expected')
        sent = conn.sendall.call_args[0][0].decode()
        self.assertIn('State token does not match', sent)

    def test_connection_closed_on_state_mismatch(self):
        sock_cls, conn = _make_socket_stack(_raw_request(code='c', state='wrong'))
        with patch('generate_user_credentials.socket.socket', sock_cls), \
             patch('generate_user_credentials.sys.exit'):
            guc.get_authorization_code('expected')
        conn.close.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# main
# ═════════════════════════════════════════════════════════════════════════════

class TestMain(unittest.TestCase):

    def _run_main(self, code='refresh-code-123', refresh_token='rt-xyz'):
        """Run main() with full mocks; return (mock_flow, mock_get_code)."""
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ('https://auth.example.com', 'state-val')
        mock_flow.credentials.refresh_token = refresh_token

        with patch('generate_user_credentials.Flow') as mock_Flow, \
             patch('generate_user_credentials.get_authorization_code', return_value=code) as mock_gc, \
             patch('builtins.print'):
            mock_Flow.from_client_secrets_file.return_value = mock_flow
            guc.main('/path/to/secrets.json', ['https://scope.example.com'])

        return mock_flow, mock_gc, mock_Flow

    # ── Flow setup ────────────────────────────────────────────────────────────

    def test_loads_flow_from_client_secrets_file(self):
        _, _, mock_Flow = self._run_main()
        mock_Flow.from_client_secrets_file.assert_called_once()

    def test_passes_correct_path_to_flow(self):
        _, _, mock_Flow = self._run_main()
        args = mock_Flow.from_client_secrets_file.call_args
        self.assertIn('/path/to/secrets.json', args[0])

    def test_passes_scopes_to_flow(self):
        _, _, mock_Flow = self._run_main()
        args = mock_Flow.from_client_secrets_file.call_args
        self.assertIn('https://scope.example.com', args[1]['scopes'])

    def test_sets_redirect_uri_on_flow(self):
        mock_flow, _, _ = self._run_main()
        self.assertEqual(mock_flow.redirect_uri, guc._REDIRECT_URI)

    # ── Authorization URL ─────────────────────────────────────────────────────

    def test_calls_authorization_url(self):
        mock_flow, _, _ = self._run_main()
        mock_flow.authorization_url.assert_called_once()

    def test_authorization_url_uses_offline_access(self):
        mock_flow, _, _ = self._run_main()
        kwargs = mock_flow.authorization_url.call_args[1]
        self.assertEqual(kwargs.get('access_type'), 'offline')

    def test_authorization_url_prompts_consent(self):
        mock_flow, _, _ = self._run_main()
        kwargs = mock_flow.authorization_url.call_args[1]
        self.assertEqual(kwargs.get('prompt'), 'consent')

    def test_authorization_url_includes_granted_scopes(self):
        mock_flow, _, _ = self._run_main()
        kwargs = mock_flow.authorization_url.call_args[1]
        self.assertEqual(kwargs.get('include_granted_scopes'), 'true')

    # ── Token exchange ────────────────────────────────────────────────────────

    def test_get_authorization_code_called_once(self):
        _, mock_gc, _ = self._run_main()
        mock_gc.assert_called_once()

    def test_fetch_token_called_with_code(self):
        mock_flow, _, _ = self._run_main(code='the-auth-code')
        mock_flow.fetch_token.assert_called_once_with(code='the-auth-code')

    def test_prints_refresh_token(self):
        with patch('generate_user_credentials.Flow') as mock_Flow, \
             patch('generate_user_credentials.get_authorization_code', return_value='code'), \
             patch('builtins.print') as mock_print:
            mock_flow = MagicMock()
            mock_flow.authorization_url.return_value = ('https://url', 'state')
            mock_flow.credentials.refresh_token = 'secret-refresh-token'
            mock_Flow.from_client_secrets_file.return_value = mock_flow

            guc.main('/path/to/secrets.json', ['scope'])

        printed = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('secret-refresh-token', printed)


if __name__ == '__main__':
    unittest.main()
