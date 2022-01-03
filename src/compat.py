from sys import version_info


if version_info[0] == 2:
	# Python 2
	compat_str = unicode

	from urllib import urlencode as compat_urlencode
	from urllib import quote as compat_quote
	from urllib2 import urlopen as compat_urlopen
	from urllib2 import Request as compat_Request
	from urllib2 import HTTPError as compat_HTTPError
	from urllib2 import URLError as compat_URLError
else:
	# Python 3
	compat_str = str

	from urllib.parse import urlencode as compat_urlencode
	from urllib.parse import quote as compat_quote
	from urllib.request import urlopen as compat_urlopen
	from urllib.request import Request as compat_Request
	from urllib.error import HTTPError as compat_HTTPError
	from urllib.error import URLError as compat_URLError
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
