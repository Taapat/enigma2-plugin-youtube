from re import compile
from sys import version_info


if version_info[0] == 2:
	# Python 2
	compat_str = unicode
	from urllib import urlencode as compat_urlencode
	from urllib import quote as compat_quote
	from urllib import unquote as compat_unquote_to_bytes
	from urllib2 import urlopen as compat_urlopen
	from urllib2 import Request as compat_Request
	from urllib2 import URLError as compat_URLError
	from urlparse import urljoin as compat_urljoin
	from urlparse import urlparse as compat_urlparse
else:
	# Python 3
	compat_str = str
	from urllib.parse import urlencode as compat_urlencode
	from urllib.parse import quote as compat_quote
	from urllib.parse import unquote_to_bytes as compat_unquote_to_bytes
	from urllib.request import urlopen as compat_urlopen
	from urllib.request import Request as compat_Request
	from urllib.error import URLError as compat_URLError
	from urllib.parse import urljoin as compat_urljoin
	from urllib.parse import urlparse as compat_urlparse


# Disable certificate verification on python 2.7.9
if version_info >= (2, 7, 9):
	try:
		import ssl
		sslContext = ssl._create_unverified_context()
	except:
		sslContext = None


def _parse_qsl(qs):
	qs, _coerce_result = qs, compat_str
	pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
	r = []
	for name_value in pairs:
		if not name_value:
			continue
		nv = name_value.split('=', 1)
		if len(nv) != 2:
			# Handle case of a control-name with no equal sign
			continue
		if len(nv[1]):
			name = nv[0].replace('+', ' ')
			name = compat_urllib_parse_unquote(name)
			name = _coerce_result(name)
			value = nv[1].replace('+', ' ')
			value = compat_urllib_parse_unquote(value)
			value = _coerce_result(value)
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


def compat_ssl_urlopen(url):
	if sslContext:
		return compat_urlopen(url, context=sslContext)
	else:
		return compat_urlopen(url)


def compat_urllib_parse_unquote(string):
	if '%' not in string:
		string.split
		return string
	bits = compile(r'([\x00-\x7f]+)').split(string)
	res = [bits[0]]
	append = res.append
	for i in range(1, len(bits), 2):
		append(compat_unquote_to_bytes(bits[i]).decode('utf-8', 'replace'))
		append(bits[i + 1])
	return ''.join(res)
