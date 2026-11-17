"""Explicit opt-in Sarvam text inference, independent of device authorization.

Server/owner-controlled Python runtime only. Never embed subscription keys in APKs.
Model text is untrusted data and is never executed by this module.
"""
import http.client
import json
import os

HOST = 'api.sarvam.ai'
PATH = '/v2/chat/completions'
MODELS = frozenset({'sarvam-105b', 'sarvam-105b-conversations'})
MAX_RESPONSE_BYTES = 1024 * 1024


class SarvamError(RuntimeError):
    """Content-free provider failure safe to display without leaking credentials."""


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate response key')
        result[key] = value
    return result


def generate_reply(prompt, *, cloud_opt_in=False, model='sarvam-105b', max_tokens=512):
    """Send one text prompt after trusted caller obtains explicit cloud opt-in.

    cloud_opt_in is application configuration, never model/request-supplied consent.
    It authorizes inference only, not phone actions. No retries or provider fallback.
    """
    if cloud_opt_in is not True:
        raise SarvamError('CLOUD_OPT_IN_REQUIRED')
    if type(prompt) is not str or not prompt.strip() or len(prompt) > 8192 or '\x00' in prompt:
        raise SarvamError('INVALID_PROMPT')
    if type(model) is not str or model not in MODELS:
        raise SarvamError('INVALID_MODEL')
    if type(max_tokens) is not int or not 1 <= max_tokens <= 2048:
        raise SarvamError('INVALID_TOKEN_LIMIT')
    key = os.environ.get('SARVAM_API_KEY', '')
    if not key or len(key) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in key):
        raise SarvamError('SARVAM_KEY_REQUIRED')
    payload = json.dumps({'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                          'max_tokens': max_tokens, 'stream': False}).encode('utf-8')
    connection = None
    try:
        # Default certificate verification; fixed host/path; no ambient proxies,
        # redirects, SDK telemetry, tools, hidden memory or automatic fallback.
        connection = http.client.HTTPSConnection(HOST, timeout=20)
        connection.request('POST', PATH, body=payload, headers={
            'Content-Type': 'application/json', 'Accept': 'application/json',
            'api-subscription-key': key})
        response = connection.getresponse()
        if response.status != 200:
            raise SarvamError('SARVAM_REQUEST_REJECTED')
        if response.getheader('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            raise SarvamError('INVALID_SARVAM_RESPONSE')
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise SarvamError('SARVAM_RESPONSE_TOO_LARGE')
        result = json.loads(raw, object_pairs_hook=_unique)
        if result.get('model') != model:
            raise SarvamError('SARVAM_MODEL_MISMATCH')
        choices = result['choices']
        if type(choices) is not list or len(choices) != 1:
            raise SarvamError('INVALID_SARVAM_RESPONSE')
        choice = choices[0]
        message = choice['message']
        if choice.get('finish_reason') != 'stop' or message.get('role') != 'assistant' or message.get('tool_calls'):
            raise SarvamError('SARVAM_RESPONSE_NOT_TEXT_COMPLETE')
        content = message['content']
        if type(content) is not str or not content.strip() or len(content) > 32768 or '\x00' in content:
            raise SarvamError('INVALID_SARVAM_RESPONSE')
        return content
    except SarvamError:
        raise
    except Exception:
        # Do not retain raw provider errors, response bodies, prompts or keys.
        raise SarvamError('SARVAM_PROVIDER_UNAVAILABLE') from None
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
