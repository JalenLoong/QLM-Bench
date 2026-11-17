"""Bounded, lossless JSON RPC over localhost TCP; no simulator or model imports.

A connection carries one request and one response. Retries use exactly the same
request identity. A single-threaded server serializes model mutations and caches
both responses and failures before replying, including after a disconnected client.
"""
from __future__ import annotations

import base64
from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
import math
import socket
import socketserver
import struct
import time

PROTOCOL = 'qlm-live-v1'
MAX_FRAME_BYTES = 64 * 1024 * 1024
MAX_IMAGE_BYTES = 8 * 1024 * 1024


class ProtocolError(ValueError):
    pass


class RemoteError(RuntimeError):
    pass


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError('Duplicate JSON object key')
        result[key] = value
    return result


def _encode(value):
    if hasattr(value, 'dtype') and hasattr(value, 'shape') and hasattr(value, 'tobytes'):
        if str(value.dtype) != 'uint8' or len(value.shape) != 3 or value.shape[-1] != 3:
            raise ProtocolError('Only uint8 HWC RGB arrays may cross the public transport')
        if any(type(int(n)) is not int or n < 1 for n in value.shape):
            raise ProtocolError('Invalid RGB shape')
        raw = value.tobytes(order='C')
        if len(raw) > MAX_IMAGE_BYTES:
            raise ProtocolError('RGB image exceeds transport limit')
        return {'__qlm_rgb__': 1, 'shape': list(value.shape), 'dtype': 'uint8',
                'data': base64.b64encode(raw).decode('ascii')}
    if isinstance(value, dict):
        if '__qlm_rgb__' in value:
            raise ProtocolError('Reserved RGB marker')
        if not all(isinstance(k, str) for k in value):
            raise ProtocolError('JSON object keys must be strings')
        return {key: _encode(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    raise ProtocolError('Unsupported or nonfinite public transport value')


def _decode(value):
    if isinstance(value, list):
        return [_decode(item) for item in value]
    if isinstance(value, dict):
        if '__qlm_rgb__' in value:
            if set(value) != {'__qlm_rgb__', 'shape', 'dtype', 'data'} or value['__qlm_rgb__'] != 1:
                raise ProtocolError('Invalid RGB envelope')
            shape = value['shape']
            if value['dtype'] != 'uint8' or not isinstance(shape, list) or len(shape) != 3 or \
                    any(type(n) is not int or n < 1 for n in shape) or shape[-1] != 3:
                raise ProtocolError('Invalid RGB shape/dtype')
            size = math.prod(shape)
            if size > MAX_IMAGE_BYTES or not isinstance(value['data'], str) or \
                    len(value['data']) != 4 * ((size + 2) // 3):
                raise ProtocolError('Invalid or excessive RGB payload size')
            try:
                raw = base64.b64decode(value['data'], validate=True)
            except (ValueError, TypeError) as error:
                raise ProtocolError('Invalid base64 RGB payload') from error
            if len(raw) != size:
                raise ProtocolError('RGB payload and shape disagree')
            import numpy as np  # Optional live extra; ordinary core import remains lightweight.
            result = np.frombuffer(raw, dtype=np.uint8).reshape(shape)
            result.setflags(write=False)
            return result
        return {key: _decode(item) for key, item in value.items()}
    if type(value) is float and not math.isfinite(value):
        raise ProtocolError("Nonfinite JSON numeric value")
    return value


def dumps(value):
    return json.dumps(_encode(value), sort_keys=True, separators=(',', ':'),
                      allow_nan=False, ensure_ascii=False).encode('utf-8')


def loads(raw):
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique,
                           parse_constant=lambda _: (_ for _ in ()).throw(ProtocolError('Nonfinite JSON')))
        return _decode(value)
    except (UnicodeError, ValueError, TypeError, RecursionError) as error:
        if isinstance(error, ProtocolError):
            raise
        raise ProtocolError('Malformed public JSON frame') from error


def _recv_exact(connection, length, deadline=None):
    chunks = bytearray()
    while len(chunks) < length:
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Frame receive deadline exceeded')
            connection.settimeout(remaining)
        part = connection.recv(min(length - len(chunks), 1024 * 1024))
        if not part:
            raise EOFError('Connection closed before complete frame')
        chunks.extend(part)
    return bytes(chunks)


def receive(connection, limit=MAX_FRAME_BYTES):
    timeout = connection.gettimeout()
    deadline = None if timeout is None else time.monotonic() + timeout
    length = struct.unpack('!I', _recv_exact(connection, 4, deadline))[0]
    if not 0 < length <= limit:
        raise ProtocolError('Frame length outside configured bound')
    return loads(_recv_exact(connection, length, deadline))


def send(connection, value, limit=MAX_FRAME_BYTES):
    raw = dumps(value)
    if not 0 < len(raw) <= limit:
        raise ProtocolError('Frame exceeds configured bound')
    connection.sendall(struct.pack('!I', len(raw)) + raw)


def validate_request(request):
    keys = {'protocol', 'method', 'request_id', 'session_id', 'episode_id', 'reset_epoch', 'payload'}
    if not isinstance(request, dict) or set(request) != keys or request['protocol'] != PROTOCOL:
        raise ProtocolError('Unsupported live request envelope')
    if request['method'] not in ('reset', 'predict', 'feedback', 'end'):
        raise ProtocolError('Unsupported live operation')
    for key in ('request_id', 'session_id', 'episode_id'):
        if not isinstance(request[key], str) or not request[key] or len(request[key]) > 256:
            raise ProtocolError('Invalid live identity: ' + key)
    if type(request['reset_epoch']) is not int or not 0 <= request['reset_epoch'] < 2**63 or \
            not isinstance(request['payload'], dict):
        raise ProtocolError('Invalid reset epoch or payload')
    # Nested compatibility messages must share the outer identity.
    for key in ('reset', 'ack'):
        value = request['payload'].get(key)
        if value is not None and any(value.get(k) != request[k]
                                     for k in ('session_id', 'episode_id', 'reset_epoch')):
            raise ProtocolError('Envelope and compatibility identity disagree')
    observation = request['payload'].get('observation')
    if observation is not None:
        value = observation.get('observation', {})
        if any(value.get(k) != request[k] for k in ('session_id', 'episode_id', 'reset_epoch')):
            raise ProtocolError('Observation and RPC identity disagree')
    return request


class RPCServer:
    """Single-policy service. Cache full results, retain all accepted IDs until reset.

    Cache eviction retains fingerprints and rejects expired response retries, never
    calls the handler again. max_requests bounds a live epoch instead of silently
    evicting the identities needed for exactly-once model mutation.
    """
    def __init__(self, handler, host='127.0.0.1', port=8765, *, timeout_s=600.,
                 max_frame_bytes=MAX_FRAME_BYTES, max_cached_bytes=128*1024*1024,
                 max_requests=10000):
        if host not in ('127.0.0.1', 'localhost', '::1'):
            raise ValueError('Unauthenticated live RPC is localhost-only')
        if not math.isfinite(timeout_s) or timeout_s <= 0 or max_frame_bytes < 1 or \
                max_cached_bytes < 1 or max_requests < 1:
            raise ValueError('Positive finite transport limits required')
        self.handler = handler
        self.timeout_s = timeout_s
        self.max_frame_bytes = max_frame_bytes
        self.max_cached_bytes = max_cached_bytes
        self.max_requests = max_requests
        self.identity = None
        self._seen = {}
        self._responses = OrderedDict()
        self._cached_bytes = 0
        self._retired_sessions = set()
        self._poisoned = False
        owner = self
        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                self.request.settimeout(owner.timeout_s)
                try:
                    request = receive(self.request, owner.max_frame_bytes)
                    response = owner.dispatch(request)
                except Exception as error:
                    response = {'ok': False, 'error_type': type(error).__name__, 'error': str(error)}
                try:
                    send(self.request, response, owner.max_frame_bytes)
                except (OSError, EOFError):
                    pass  # dispatch retained the result before the socket write.
        class Server(socketserver.TCPServer):
            allow_reuse_address = True
            address_family = socket.AF_INET6 if host == "::1" else socket.AF_INET
        self._server = Server((host, port), Handler)
        self.address = self._server.server_address

    def dispatch(self, request):
        validate_request(request)
        ident = tuple(request[k] for k in ('session_id', 'episode_id', 'reset_epoch'))
        if request['method'] != 'reset' and ident != self.identity:
            raise ProtocolError('Stale reset epoch or uninitialized service')
        if request['method'] == 'reset' and ident != self.identity:
            if self.identity is not None:
                old = self.identity
                if ident[0] == old[0] and ident[2] <= old[2] or ident[0] in self._retired_sessions:
                    raise ProtocolError('Reset epoch must advance; retired sessions cannot return')
                if ident[0] != old[0]:
                    if len(self._retired_sessions) >= self.max_requests:
                        raise ProtocolError('Service session budget exhausted; restart required')
                    self._retired_sessions.add(old[0])
            self.identity = ident
            self._seen.clear()
            self._responses.clear()
            self._cached_bytes = 0
            self._poisoned = False
        key = (ident, request['request_id'])
        sha = hashlib.sha256(dumps(request)).hexdigest()
        if key in self._seen:
            if self._seen[key] != sha:
                raise ProtocolError('Conflicting request with reused identity')
            if key not in self._responses:
                raise ProtocolError('Response expired; execution state remains known, reset required')
            return loads(self._responses[key])
        if self._poisoned and request['method'] != 'end':
            raise ProtocolError('Previous handler failure may have mutated state; new reset required')
        if len(self._seen) >= self.max_requests:
            raise ProtocolError('Epoch request budget exhausted; reset required')
        # Reserve before user code. Even a partially mutating error is never retried.
        self._seen[key] = sha
        try:
            result = self.handler(deepcopy(request))
            response = {'ok': True, 'result': result}
            raw = dumps(response)
            if len(raw) > self.max_frame_bytes:
                raise ProtocolError('Handler response exceeds frame bound')
        except Exception as error:
            self._poisoned = True
            response = {'ok': False, 'error_type': type(error).__name__, 'error': str(error)}
            raw = dumps(response)
        self._responses[key] = raw
        self._cached_bytes += len(raw)
        while self._cached_bytes > self.max_cached_bytes and len(self._responses) > 1:
            _, evicted = self._responses.popitem(last=False)
            self._cached_bytes -= len(evicted)
        return response

    def serve_forever(self):
        self._server.serve_forever(poll_interval=.1)

    def shutdown(self):
        self._server.shutdown()

    def close(self):
        self._server.server_close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class RPCClient:
    def __init__(self, host='127.0.0.1', port=8765, *, timeout_s=600., retries=1,
                 max_frame_bytes=MAX_FRAME_BYTES):
        if host not in ('127.0.0.1', 'localhost', '::1'):
            raise ValueError('Unauthenticated live RPC is localhost-only')
        if not math.isfinite(timeout_s) or timeout_s <= 0 or type(retries) is not int or retries < 0:
            raise ValueError('Finite positive timeout and nonnegative retry count required')
        self.address = (host, port)
        self.timeout_s = timeout_s
        self.retries = retries
        self.max_frame_bytes = max_frame_bytes

    def call(self, method, payload, *, request_id, session_id, episode_id, reset_epoch):
        request = validate_request(dict(protocol=PROTOCOL, method=method, payload=payload,
                                       request_id=request_id, session_id=session_id,
                                       episode_id=episode_id, reset_epoch=reset_epoch))
        for attempt in range(self.retries + 1):
            try:
                with socket.create_connection(self.address, timeout=self.timeout_s) as connection:
                    connection.settimeout(self.timeout_s)
                    send(connection, request, self.max_frame_bytes)
                    response = receive(connection, self.max_frame_bytes)
                if not isinstance(response, dict) or type(response.get('ok')) is not bool:
                    raise ProtocolError('Malformed live response')
                if not response['ok']:
                    raise RemoteError(str(response.get('error_type')) + ': ' + str(response.get('error')))
                return response['result']
            except (OSError, EOFError):
                if attempt == self.retries:
                    raise
        raise AssertionError('Unreachable retry state')
