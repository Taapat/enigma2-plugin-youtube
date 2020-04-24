from sys import version_info


# Disable certificate verification on python 2.7.9
sslContext = None
if version_info >= (2, 7, 9):
	try:
		import ssl
		sslContext = ssl._create_unverified_context()
	except:
		pass
