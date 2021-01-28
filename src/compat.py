from sys import version_info


if version_info[0] == 2:
	# Python 2
	compat_str = unicode

	from re import compile
	from urllib import _hextochr

	from urllib import urlencode as compat_urlencode
	from urllib import quote as compat_quote
	from urllib2 import urlopen as compat_urlopen
	from urllib2 import Request as compat_Request
	from urllib2 import HTTPError as compat_HTTPError
	from urllib2 import URLError as compat_URLError
	from urlparse import urljoin as compat_urljoin
	from urlparse import urlparse as compat_urlparse
	from urlparse import urlunparse as compat_urlunparse

	def _unquote_to_bytes(string):
		if not string:
			# Is it a string-like object?
			string.split
			return b''
		if isinstance(string, unicode):
			string = string.encode('utf-8')
		bits = string.split(b'%')
		if len(bits) == 1:
			return string
		res = [bits[0]]
		for item in bits[1:]:
			try:
				res.append(_hextochr[item[:2]])
				res.append(item[2:])
			except KeyError:
				res.append(b'%')
				res.append(item)
		return b''.join(res)

	def _unquote(string):
		if '%' not in string:
			string.split
			return string
		bits = compile(r'([\x00-\x7f]+)').split(string)
		res = [bits[0]]
		for i in range(1, len(bits), 2):
			res.append(_unquote_to_bytes(bits[i]).decode('utf-8', 'replace'))
			res.append(bits[i + 1])
		return ''.join(res)

	def _parse_qsl(qs):
		pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
		r = []
		for name_value in pairs:
			if not name_value:
				continue
			nv = name_value.split('=', 1)
			if len(nv) == 2 and len(nv[1]):
				name = unicode(_unquote(nv[0].replace('+', ' ')))
				value = unicode(_unquote(nv[1].replace('+', ' ')))
				r.append((name, value))
		return r

	def compat_parse_qs(qs):
		parsed_result = {}
		pairs = _parse_qsl(qs)
		for name, value in pairs:
			if name in parsed_result:
				parsed_result[name].append(value)
			else:
				parsed_result[name] = [value]
		return parsed_result

else:
	# Python 3
	compat_str = str

	from urllib.parse import urlencode as compat_urlencode
	from urllib.parse import quote as compat_quote
	from urllib.request import urlopen as compat_urlopen
	from urllib.request import Request as compat_Request
	from urllib.error import HTTPError as compat_HTTPError
	from urllib.error import URLError as compat_URLError
	from urllib.parse import urljoin as compat_urljoin
	from urllib.parse import urlparse as compat_urlparse
	from urllib.parse import parse_qs as compat_parse_qs
	from urllib.parse import urlunparse as compat_urlunparse


# Disable certificate verification on python 2.7.9
sslContext = None
if version_info >= (2, 7, 9):
	try:
		import ssl
		sslContext = ssl._create_unverified_context()
	except Exception as e:
		print('[YouTube] Error in set ssl context', e)


def compat_ssl_urlopen(url):
	if sslContext:
		return compat_urlopen(url, context=sslContext)
	else:
		return compat_urlopen(url)
