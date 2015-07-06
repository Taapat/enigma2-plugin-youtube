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

