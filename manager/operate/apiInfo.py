"""This module provides functions for dumping information about responses."""
import collections
from urllib import parse

from requests import compat

HTTP_VERSIONS = {
	9: b'0.9',
	10: b'1.0',
	11: b'1.1',
}

_PrefixSettings = collections.namedtuple('PrefixSettings', ['request', 'response'])


class PrefixSettings(_PrefixSettings):
	def __new__(cls, request, response):
		request = _coerce_to_bytes(request)
		response = _coerce_to_bytes(response)
		return super(PrefixSettings, cls).__new__(cls, request, response)





def _format_header(name, value):
	return (_coerce_to_bytes(name) + b': ' + _coerce_to_bytes(value) + b'\r\n')


def _build_request_path(url):
	uri = compat.urlparse(url)
	request_path = _coerce_to_bytes(uri.path)
	if uri.query:
		request_path += b'?' + _coerce_to_bytes(uri.query)

	return request_path, uri


def _dump_request_data(request, prefixes, bytearr):
	prefix = prefixes.request
	method = _coerce_to_bytes(request.method)
	request_path, uri = _build_request_path(request.url)
	bytearr.extend(prefix + method + b' ' + request_path + b' HTTP/1.1\r\n')

	headers = request.headers.copy()
	host_header = _coerce_to_bytes(headers.pop('Host', uri.netloc))
	bytearr.extend(prefix + b'Host: ' + host_header + b'\r\n')

	for name, value in headers.items():
		bytearr.extend(prefix + _format_header(name, value))

	bytearr.extend(prefix + b'\r\n')
	if request.body:
		body = request.body
		if isinstance(body,bytes):
			try:
				body = parse.unquote(body.decode('utf-8'))
			except:
				body = body
		else:
			body = parse.unquote(body)
		if isinstance(body, compat.basestring):
			bytearr.extend(prefix + _coerce_to_bytes(body))
		else:
			bytearr.extend(b'<< Request body is not a string-like type >>')
	bytearr.extend(b'\r\n')


def _dump_response_data(response, prefixes, bytearr):
	prefix = prefixes.response
	raw = response.raw

	version_str = HTTP_VERSIONS.get(raw.version, b'?')

	bytearr.extend(prefix + b'HTTP/' + version_str + b' ' +
	               str(raw.status).encode('ascii') + b' ' +
	               _coerce_to_bytes(response.reason) + b'\r\n')

	headers = raw.headers
	for name in headers.keys():
		for value in headers.getlist(name):
			bytearr.extend(prefix + _format_header(name, value))

	bytearr.extend(prefix + b'\r\n')

	bytearr.extend(response.content)


def _coerce_to_bytes(data):
	if not isinstance(data, bytes) and hasattr(data, 'encode'):
		data = data.encode('utf-8')
	return data if data is not None else b''


def dump_response(response, request_prefix=b'', response_prefix=b''):
	request_data = bytearray()
	response_data = bytearray()
	prefixes = PrefixSettings(request_prefix, response_prefix)

	if not hasattr(response, 'request'):
		raise ValueError('Response has no associated request')

	_dump_request_data(response.request, prefixes, request_data)
	_dump_response_data(response, prefixes, response_data)

	return request_data.decode('utf-8'),response_data.decode('utf-8')


def dump_request(response, request_prefix=b'', response_prefix=b''):
	request_data = bytearray()
	prefixes = PrefixSettings(request_prefix, response_prefix)

	if not hasattr(response, 'request'):
		raise ValueError('Response has no associated request')

	_dump_request_data(response.request, prefixes, request_data)
	
	try:
		r = request_data.decode('utf-8')
	except:
		r ="请求成功，但结果打印失败"
	return r