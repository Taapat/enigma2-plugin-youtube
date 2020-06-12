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


def compat_ssl_urlopen(url):
	if sslContext:
		return compat_urlopen(url, context=sslContext)
	else:
		return compat_urlopen(url)
