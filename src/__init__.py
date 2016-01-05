from sys import version_info
from os import environ
from gettext import bindtextdomain, dgettext, gettext

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS


def localeInit():
	environ["LANGUAGE"] = language.getLanguage()[:2]
	bindtextdomain("YouTube", resolveFilename(SCOPE_PLUGINS, \
		"Extensions/YouTube/locale"))


def _(txt):
	t = dgettext("YouTube", txt)
	if t == txt:
		t = gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

# Disable certificate verification on python 2.7.9
sslContext = None
if version_info >= (2, 7, 9):
	try:
		import ssl
		sslContext = ssl._create_unverified_context()
	except:
		pass

