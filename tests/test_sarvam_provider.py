import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location('sarvam', Path(__file__).resolve().parents[1] / 'core/sarvam_provider.py')
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


class SarvamTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(provider.os.environ, {'SARVAM_API_KEY': 'synthetic-key'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.factory = patch.object(provider.http.client, 'HTTPSConnection')
        self.connect = self.factory.start()
        self.addCleanup(self.factory.stop)
        self.conn = self.connect.return_value
        self.response = self.conn.getresponse.return_value
        self.response.status = 200
        self.response.getheader.return_value = 'application/json; charset=utf-8'
        self.result = {'model': 'sarvam-105b', 'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': 'Synthetic reply'}}]}
        self.set_response()

    def set_response(self):
        self.response.read.return_value = json.dumps(self.result).encode()

    def call(self, **kwargs):
        return provider.generate_reply('synthetic prompt', cloud_opt_in=True, **kwargs)

    def test_fixed_tls_request(self):
        self.assertEqual(self.call(), 'Synthetic reply')
        self.connect.assert_called_once_with('api.sarvam.ai', timeout=20)
        args, kw = self.conn.request.call_args
        self.assertEqual(args, ('POST', '/v2/chat/completions'))
        body = json.loads(kw['body'])
        self.assertFalse(body['stream'])
        self.assertNotIn('tools', body)
        self.assertEqual(kw['headers']['api-subscription-key'], 'synthetic-key')
        self.conn.close.assert_called_once()

    def test_explicit_opt_in_before_network(self):
        for value in (False, None, 1, 'true'):
            with self.subTest(value=value), self.assertRaises(provider.SarvamError):
                provider.generate_reply('test', cloud_opt_in=value)
        self.connect.assert_not_called()

    def test_key_missing_or_header_injection(self):
        for value in ('', 'key\r\nInjected: true', 'key with space'):
            with patch.dict(provider.os.environ, {'SARVAM_API_KEY': value}), self.assertRaises(provider.SarvamError):
                self.call()
        self.connect.assert_not_called()

    def test_validation_before_network(self):
        for value in ('', ' ', 'x' * 8193, '\x00', None):
            with self.assertRaises(provider.SarvamError):
                provider.generate_reply(value, cloud_opt_in=True)
        for value in (True, 0, 2049):
            with self.assertRaises(provider.SarvamError):
                self.call(max_tokens=value)
        with self.assertRaises(provider.SarvamError):
            self.call(model='sarvam-m')
        self.connect.assert_not_called()

    def test_status_no_redirect_retry_or_error_body(self):
        for status in (301, 403, 429, 500):
            self.response.status = status
            with self.assertRaisesRegex(provider.SarvamError, '^SARVAM_REQUEST_REJECTED$'):
                self.call()
        self.assertEqual(self.conn.request.call_count, 4)
        self.response.read.assert_not_called()

    def test_bounded_json(self):
        for value in (b'x' * (provider.MAX_RESPONSE_BYTES + 1), b'{', b'{"model":1,"model":2}'):
            self.response.read.return_value = value
            with self.assertRaises(provider.SarvamError):
                self.call()

    def test_wrong_model_rejected(self):
        self.result['model'] = 'other'
        self.set_response()
        with self.assertRaises(provider.SarvamError):
            self.call()

    def test_tools_truncation_and_empty_rejected(self):
        for finish, content, tools in [('length', 'partial', None), ('tool_calls', 'text', [{}]), ('stop', '', None)]:
            choice = self.result['choices'][0]
            choice['finish_reason'] = finish
            choice['message'].update(content=content, tool_calls=tools)
            self.set_response()
            with self.assertRaises(provider.SarvamError):
                self.call()

    def test_exception_redacted(self):
        self.conn.request.side_effect = OSError('synthetic-key synthetic prompt')
        with self.assertRaises(provider.SarvamError) as caught:
            self.call()
        self.assertEqual(str(caught.exception), 'SARVAM_PROVIDER_UNAVAILABLE')
        self.conn.close.assert_called_once()

    def test_content_type_rejected(self):
        self.response.getheader.return_value = 'text/html'
        with self.assertRaises(provider.SarvamError):
            self.call()
        self.response.read.assert_not_called()
