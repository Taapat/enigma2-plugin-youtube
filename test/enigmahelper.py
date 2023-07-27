from __future__ import print_function

from os import environ
from sys import modules


def add_metaclass(metaclass):
	"""Class decorator for creating a class with a metaclass from six."""
	def wrapper(cls):
		orig_vars = cls.__dict__.copy()
		orig_vars.pop('__dict__', None)
		return metaclass(cls.__name__, cls.__bases__, orig_vars)
	return wrapper


class ClassVariables(type):
	def __getattr__(self, attr):
		return 1


class EnimaInstance:
	@classmethod
	def getInstance(cls):
		return cls.instance

	instance = None

	def __init__(self, *args):
		EnimaInstance.instance = self
		self.list = []

	def __setattr__(self, name, value, *args):
		self.__dict__[name] = value

	def __getattr__(self, attr):

		def default(*args):
			return 0

		if 'get' in attr.lower() or type(self).__name__ in ('EnigmaGetDesktop', 'eConsoleAppContainer'):
			return default
		elif 'default' in attr.lower() or attr[:2] == 'is' or attr.isupper():
			return 0
		else:
			return self

	def __call__(self, *args):
		return self

	def __coerce__(self, *args):
		return None

	def __hash__(self, *args):
		return 1

	def __int__(self):
		return 1

	def __len__(self):
		return 1

	def __nonzero__(self, *args):
		return 1

	def __str__(self, *args):
		return ''

	def get(self):
		return self.list


modules['enigma'] = EnimaInstance()


class eTimer:
	def __init__(self):
		self.callback = []

		def slot():
			pass
		self.timeout = slot
		self.timeout.callback = []
		self.callback_thread = None

	def start_callback(self, singleshot):
		for f in self.timeout.callback:
			f()
		for f in self.callback:
			if singleshot and f in self.callback:
				self.callback.remove(f)
			f()

	def start(self, msec, singleshot=False):
		if int(msec) == 1000:
			from threading import Thread
			self.callback_thread = Thread(target=self.start_callback,
					args=(singleshot,))
			self.callback_thread.start()
		else:
			self.start_callback(singleshot)

	def startLongTimer(self, sec):
		self.start_callback(True)

	def stop(self):
		self.callback_thread = None

	def isActive(self):
		return self.callback_thread


modules['enigma'].eTimer = eTimer


class EnigmaNavigation(EnimaInstance):
	def __init__(self, *args):
		EnimaInstance.__init__(self)
		self.m_event = EnimaInstance()
		self.m_record_event = EnimaInstance()

	def getCurrentService(self):
		return self

	def getPlayPosition(self):
		return (0, 100)

	def getRecordings(self, *args):
		return ''


pNavigation = EnigmaNavigation()
modules['enigma'].pNavigation = pNavigation


@add_metaclass(ClassVariables)
class eServiceReference(EnimaInstance, object):
	def __init__(self, ref_type=0, flags=0, data='', *args):
		eServiceReference.instance = self
		self._data = data
		self._name = ''

	def setName(self, name):
		self._name = name

	def getName(self):
		return self._name

	def getPath(self):
		return self._data


modules['enigma'].eServiceReference = eServiceReference


class ePicLoad(EnimaInstance):
	def __init__(self):
		ePicLoad.PictureData = self
		self._functions = []
		self._image = None

	def get(self):
		return self._functions

	def startDecode(self, image):
		print('ePicLoad decode', image)
		self._image = image
		for f in self._functions:
			self._functions.remove(f)
			f()

	def getData(self):
		return self


modules['enigma'].ePicLoad = ePicLoad

sel_index = 0


class eConsoleAppContainer(EnimaInstance):
	def __init__(self):
		self.dataAvail = []
		self.appClosed = []

	def execute(self, *cmd):
		if cmd and 'ffmpeg -i' in cmd[0]:
			with open('test.mkv', 'w') as fp:  # noqa: F841
				pass  # create empty mkv file
			return True


modules['enigma'].eConsoleAppContainer = eConsoleAppContainer


class EnigmaEnv:
	def resolve(self, path):
		path = path.replace('${datadir}/enigma2/po/', './enigma2/po/')
		path = path.replace('${datadir}/enigma2/', './enigma2/data/')
		path = path.replace('${datadir}/', './enigma2/data/')
		path = path.replace('${sysconfdir}/enigma2/', '/tmp/')
		path = path.replace('${sysconfdir}/', '/tmp/')
		path = path.replace('${libdir}/enigma2/', './enigma2/lib/')
		path = path.replace('${libdir}/', './enigma2/')
		path = path.replace('/media/', '/tmp/media/')
		return path


eEnv = EnigmaEnv()
modules['enigma'].eEnv = eEnv


class _getPicture(EnimaInstance):
	def height(self):
		return 60

	def width(self):
		return 100


class loadPNG:
	def __init__(self, path, *args):
		self.size = _getPicture
		self.return_path(path)

	def return_path(self, path):
		return path.replace('/usr/lib/enigma2', './enigma2/lib')


modules['enigma'].loadPNG = loadPNG
modules['enigma'].loadJPG = loadPNG
modules['enigma'].loadSVG = loadPNG
modules['enigma'].loadGIF = loadPNG

DESKTOP_SIZE = [1920, 1080]


def setDesktopSize(w, h):
	global DESKTOP_SIZE
	DESKTOP_SIZE = [w, h]


class EnigmaGetDesktop(EnimaInstance):
	def __init__(self, *args):
		pass  # Dummy method

	def height(self):
		return DESKTOP_SIZE[1]

	def width(self):
		return DESKTOP_SIZE[0]


eSize = EnigmaGetDesktop
modules['enigma'].eSize = eSize


class getDesktop(EnimaInstance):
	def __init__(self, *args):
		self.size = EnigmaGetDesktop

	def bounds(self):
		return EnigmaGetDesktop()

	def getStyleID(self):
		return 1


modules['enigma'].getDesktop = getDesktop


class EnigmaWidget(EnimaInstance):
	def __init__(self, *args):
		EnimaInstance.__init__(self)
		self.selectionChanged = EnimaInstance()
		self.getInstance = EnimaInstance
		self._index = 0

	def get(self):
		return []

	def position(self, *args):
		return self

	def size(self, *args):
		return EnigmaGetDesktop()

	def calculateSize(self):
		return EnigmaGetDesktop()

	def calculateTextSize(self, *args):
		return EnigmaGetDesktop()

	def moveSelectionTo(self, index):
		if index >= 0:
			global sel_index
			self._index = sel_index = index

	def getCurrentIndex(self):
		global sel_index
		sel_index = self._index
		return self._index

	def getTitle(self):
		return ''

	def x(self):
		return 0

	def y(self):
		return 0


eWidget = EnigmaWidget()
modules['enigma'].eWidget = eWidget
modules['enigma'].eLabel = eWidget
modules['enigma'].eListbox = eWidget
modules['enigma'].eWindow = eWidget
modules['enigma'].eVideoWidget = eWidget


class eWindowStyleSkinned(EnigmaWidget):
	colBackground = None
	colLabelForeground = None
	colListboxBackground = None
	colListboxForeground = None
	colListboxSelectedBackground = None
	colListboxSelectedForeground = None
	colListboxMarkedBackground = None
	colListboxMarkedForeground = None
	colListboxMarkedAndSelectedBackground = None
	colListboxMarkedAndSelectedForeground = None
	colWindowTitleForeground = None
	colWindowTitleBackground = None
	bsWindow = None
	bsListboxEntry = None
	bpTopLeft = None
	bpTop = None
	bpTopRight = None
	bpLeft = None
	bpBottomLeft = None
	bpBottom = None
	bpBottomRight = None
	bpRight = None


modules['enigma'].eWindowStyleSkinned = eWindowStyleSkinned


class eSubtitleWidget(EnigmaWidget):
	Subtitle_TTX = None
	Subtitle_Regular = None
	Subtitle_Bold = None
	Subtitle_Italic = None
	Subtitle_MAX = None

	@classmethod
	def setFontStyle(cls, *args):
		pass  # Dummy method


modules['enigma'].eSubtitleWidget = eSubtitleWidget


class ePixmap(EnigmaWidget):
	def size(self, *args):
		return _getPicture()


modules['enigma'].ePixmap = ePixmap


@add_metaclass(ClassVariables)
class eListboxPythonConfigContent(EnimaInstance, object):
	def __init__(self):
		EnimaInstance.__init__(self)
		self.__list = []
		self.getItemSize = EnigmaGetDesktop
		global sel_index
		sel_index = 0

	def getCurrentSelection(self):
		if self.__list:
			if len(self.__list) > sel_index:
				return self.__list[sel_index]
			else:
				return self.__list[0]

	def setList(self, _list):
		if _list:
			self.__list = _list
			try:
				_list[0][1].onSelect(_session)
			except (AttributeError, IndexError, TypeError):
				pass

	def getCurrentSelectionIndex(self):
		return sel_index


modules['enigma'].eListboxPythonConfigContent = eListboxPythonConfigContent
modules['enigma'].eListboxPythonStringContent = eListboxPythonConfigContent
modules['enigma'].eListboxPythonMultiContent = eListboxPythonConfigContent


class EnigmaEPGCache(EnimaInstance):
	def __init__(self):
		EnimaInstance.__init__(self)
		self.getInstance = EnimaInstance


eEPGCache = EnigmaEPGCache()
modules['enigma'].eEPGCache = eEPGCache


class EnigmaAVControl(EnimaInstance):
	def __init__(self):
		EnimaInstance.__init__(self)
		self.getInstance = self

	def getAvailableModes(self):
		return '480i60hz 576i50hz'

	def getPreferredModes(self, flags):
		return self.getAvailableModes()


eAVControl = EnigmaAVControl()
modules['enigma'].eAVControl = eAVControl

enigma_fonts = {}


def addFont(filename, name, *args):
	global enigma_fonts
	enigma_fonts[name] = filename


modules['enigma'].addFont = addFont


def getFontFaces():
	return enigma_fonts


modules['enigma'].getFontFaces = getFontFaces


def ngettext(singular, plural, n):
	return singular


def _(txt):
	return txt


globals()['__builtins__']['ngettext'] = ngettext
globals()['__builtins__']['_'] = _


class Session:
	def __init__(self, desktop=None, navigation=None):
		print('Session init')
		self.desktop = desktop
		self.nav = navigation
		self.current_dialog = None
		self.dialog_stack = []
		from Screens.SessionGlobals import SessionGlobals
		self.screen = SessionGlobals(self)

	def execBegin(self, first=True, do_show=True):
		print('Exec begin')
		c = self.current_dialog
		c.execBegin()

	def instantiateDialog(self, screen, *arguments, **kwargs):
		return self.doInstantiateDialog(screen, arguments, kwargs, self.desktop)

	def doInstantiateDialog(self, screen, arguments, kwargs, desktop):
		# create dialog
		dlg = screen(self, *arguments, **kwargs)
		# read skin data
		from skin import readSkin
		readSkin(dlg, None, dlg.skinName, desktop)
		# create GUI view of this dialog
		dlg.setDesktop(desktop)
		dlg.applySkin()
		return dlg

	def pushCurrent(self):
		if self.current_dialog is not None:
			self.dialog_stack.append((self.current_dialog, self.current_dialog.shown))
			self.current_dialog.execEnd()

	def openWithCallback(self, callback, screen, *arguments, **kwargs):
		print('OpenWithCallback ', end='')
		dlg = self.open(screen, *arguments, **kwargs)
		dlg.callback = callback
		return dlg

	def open(self, screen, *arguments, **kwargs):
		print('Session open ', screen)
		self.pushCurrent()
		dlg = self.current_dialog = self.instantiateDialog(screen,
						*arguments, **kwargs)

		dlg.callback = None
		self.execBegin()
		return dlg

	def close(self, screen, *retval):
		print('Session close', screen.__class__.__name__)
		assert screen == self.current_dialog
		self.current_dialog.execEnd()
		callback = self.current_dialog.callback
		del self.current_dialog.callback

		if self.dialog_stack:
			(self.current_dialog, do_show) = self.dialog_stack.pop()
			self.execBegin(first=False, do_show=do_show)
		else:
			self.current_dialog = None

		if callback is not None:
			callback(*retval)


def new_activate_language(self, index):
	if index not in self.lang:
		print('Selected language does not exist, fallback to de_DE!')
		index = 'de_DE'
	self.lang[index] = ('Deutsch', 'de', 'DE', 'ISO-8859-15')
	self.activeLanguage = index
	environ["LANGUAGE2"] = 'de_DE'  # OpenVix
	print('Activating language de_DE')


def new_index(self, value):
	try:
		return self.__list__().index(value)
	except (ValueError, IndexError):
		return 0


from Screens.Screen import Screen


class new_movie_player(Screen):
	def __init__(self, session, service, *args):
		Screen.__init__(self, session)
		print('[MoviePlayer] service:', service.getName())

	def getPluginName(self, name):
		return name

	def runPlugin(self, plugin):
		pass  # Dummy method

	def toggleShow(self):
		pass  # Dummy method


_session = None


def start_session():
	print('init session')
	global _session
	if _session is not None:
		return _session

	print('init language')
	from Components.Language import Language, language
	Language.activateLanguage = new_activate_language
	language.activateLanguage('de_DE')

	try:  # OpenVix
		import Components.ClientMode
	except ImportError:
		pass
	else:
		print('init client mode')
		Components.ClientMode.InitClientMode()

	print('init simple summary')
	try:
		from Screens import InfoBar
	except AttributeError:  # ATV-7.0
		from Components.config import config, ConfigSubsection, ConfigYesNo
		config.crash = ConfigSubsection()
		config.crash.debugActionMaps = ConfigYesNo(default=False)
		config.crash.debugKeyboards = ConfigYesNo(default=False)
		config.crash.debugTimers = ConfigYesNo(default=False)
		config.plugins = ConfigSubsection()
		from Screens import InfoBar
	InfoBar.MoviePlayer = new_movie_player
	try:
		from Screens.SimpleSummary import SimpleSummary
	except ImportError:
		pass

	print('init parental')
	import Components.ParentalControl
	try:
		Components.ParentalControl.InitParentalControl()
	except AttributeError:  # ATV-7.3
		pass

	print('init nav')
	from Navigation import Navigation

	# ATV-6.5
	print('change index')
	from Components.config import choicesList
	choicesList.index = new_index

	try:  # OpenVix
		import Components.EpgConfig
	except ImportError:
		pass
	else:
		print('init epg config')
		Components.EpgConfig.InitEPGConfig()

	print('init usage')
	import Components.UsageConfig
	try:
		Components.UsageConfig.InitUsageConfig()
	except AttributeError:  # ATV
		from Components.config import config, ConfigSubsection, ConfigText
		config.osd = ConfigSubsection()
		config.osd.language = ConfigText(default="de_DE")
		Components.UsageConfig.InitUsageConfig()

	print('init skin')
	import skin
	try:
		skin.loadSkinData(getDesktop(0))
	except AttributeError:  # ATV
		pass

	print('init av')
	import Components.AVSwitch
	Components.AVSwitch.InitAVSwitch()

	print('init misc')
	from Components.config import config, ConfigYesNo, ConfigInteger
	config.misc.RestartUI = ConfigYesNo(default=False)
	config.misc.prev_wakeup_time = ConfigInteger(default=0)
	config.misc.prev_wakeup_time_type = ConfigInteger(default=0)

	print('init keymapparser')
	import keymapparser
	keymapparser.readKeymap(config.usage.keymap.value)

	_session = Session(getDesktop(1), Navigation())

	return _session
