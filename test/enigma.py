from __future__ import print_function

from os import environ


RT_HALIGN_BIDI = 0
RT_HALIGN_LEFT = 1
RT_HALIGN_RIGHT = 2
RT_HALIGN_CENTER = 4
RT_HALIGN_BLOCK = 8
RT_VALIGN_TOP = 0
RT_VALIGN_CENTER = 16
RT_VALIGN_BOTTOM = 32
RT_WRAP = 64
BT_ALPHATEST = 1
BT_ALPHABLEND = 2
BT_SCALE = 4
BT_KEEP_ASPECT_RATIO = 8
BT_FIXRATIO = 8
BT_HALIGN_LEFT = 0
BT_HALIGN_CENTER = 16
BT_HALIGN_RIGHT = 32
BT_VALIGN_TOP = 0
BT_VALIGN_CENTER = 64
BT_VALIGN_BOTTOM = 128
BT_ALIGN_CENTER = BT_HALIGN_CENTER | BT_VALIGN_CENTER


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


class _einstances:
	@classmethod
	def getInstance(cls):
		return cls.instance

	instance = None

	def __init__(self, *args):
		_einstances.instance = self
		self.list = []

	def __setattr__(self, name, value, *args):
		self.__dict__[name] = value

	def __getattr__(self, attr):

		def default(*args):
			return 0

		if 'get' in attr.lower() or type(self).__name__ in ('_getDesktop', 'eConsoleAppContainer'):
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


eActionMap = _einstances()
eAVSwitch = _einstances()
eBackgroundFileEraser = _einstances()
eButton = _einstances()
eCableScan = _einstances()
eComponentScan = _einstances()
eDBoxLCD = _einstances()
eDVBCI_UI = _einstances()
eDVBCIInterfaces = _einstances()
eDVBDB = _einstances()
eDVBDiseqcCommand = _einstances()
eDVBFrontend = _einstances()
eDVBFrontendParameters = _einstances()
eDVBFrontendParametersATSC = _einstances()
eDVBFrontendParametersCable = _einstances()
eDVBFrontendParametersSatellite = _einstances()
eDVBFrontendParametersTerrestrial = _einstances()
eDVBLocalTimeHandler = _einstances()
eDVBResourceManager = _einstances()
eDVBSatelliteDiseqcParameters = _einstances()
eDVBSatelliteEquipmentControl = _einstances()
eDVBSatelliteLNBParameters = _einstances()
eDVBSatelliteRotorParameters = _einstances()
eDVBSatelliteSwitchParameters = _einstances()
eDVBServicePMTHandler = _einstances()
eDVBVolumecontrol = _einstances()
eFastScan = _einstances()
eHdmiCEC = _einstances()
eListboxServiceContent = _einstances()
ePythonOutput = _einstances()
ePositionGauge = _einstances()
eRCInput = _einstances()
eRect = _einstances()
eRFmod = _einstances()
eServiceCenter = _einstances()
eServiceEvent = _einstances()
eServiceEventEnums = _einstances()
eServiceReferenceDVB = _einstances()
eServiceReferenceFS = _einstances()
eSlider = _einstances()
eStreamServer = _einstances()
eWindowStyleManager = _einstances()
fontRenderClass = _einstances()
getBestPlayableServiceReference = _einstances()
getBsodCounter = _einstances()
getPrevAsciiCode = _einstances()
gMainDC = _einstances()
iDVBFrontend = _einstances()
iDVBMetaFile = _einstances()
iFrontendInformation = _einstances()
iPlayableService = _einstances()
iPlayableServicePtr = _einstances()
iRdsDecoder = _einstances()
iRecordableService = _einstances()
iRecordableServicePtr = _einstances()
iServiceInformation = _einstances()
iServiceKeys = _einstances()
Misc_Options = _einstances()
quitMainloop = _einstances()
resetBsodCounter = _einstances()


class eTimer:
	def __init__(self):
		self.callback = []
		self.timeout = _einstances()
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


class _pNavigation(_einstances):
	def __init__(self, *args):
		_einstances.__init__(self)
		self.m_event = _einstances()
		self.m_record_event = _einstances()

	def getCurrentService(self):
		return self

	def getPlayPosition(self):
		return (0, 100)

	def getRecordings(self, *args):
		return ''


pNavigation = _pNavigation()


@add_metaclass(ClassVariables)
class eServiceReference(_einstances, object):
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


class ePicLoad(_einstances):
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


sel_index = 0


class eConsoleAppContainer(_einstances):
	def __init__(self):
		self.dataAvail = []
		self.appClosed = []

	def execute(self, *cmd):
		if cmd and 'ffmpeg -i' in cmd[0]:
			with open('test.mkv', 'w') as fp:  # noqa: F841
				pass  # create empty mkv file
			return True


class _eEnv:
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


eEnv = _eEnv()


class _getPicture(_einstances):
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


loadJPG = loadPNG
loadSVG = loadPNG
loadGIF = loadPNG


DESKTOP_SIZE = [1920, 1080]


def setDesktopSize(w, h):
	global DESKTOP_SIZE
	DESKTOP_SIZE = [w, h]


class _getDesktop(_einstances):
	def __init__(self, *args):
		pass  # Dummy method

	def height(self):
		return DESKTOP_SIZE[1]

	def width(self):
		return DESKTOP_SIZE[0]


eSize = _getDesktop


class getDesktop(_einstances):
	def __init__(self, *args):
		self.size = _getDesktop

	def bounds(self):
		return _getDesktop()

	def getStyleID(self):
		return 1


class _eWidget(_einstances):
	def __init__(self, *args):
		_einstances.__init__(self)
		self.selectionChanged = _einstances()
		self.getInstance = _einstances
		self._index = 0

	def get(self):
		return []

	def position(self, *args):
		return self

	def size(self, *args):
		return _getDesktop()

	def calculateSize(self):
		return _getDesktop()

	def calculateTextSize(self, *args):
		return _getDesktop()

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


eWidget = _eWidget()
eLabel = eWidget
eListbox = eWidget
eWindow = eWidget
eVideoWidget = eWidget


class eWindowStyleSkinned(_eWidget):
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


class eSubtitleWidget(_eWidget):
	Subtitle_TTX = None
	Subtitle_Regular = None
	Subtitle_Bold = None
	Subtitle_Italic = None
	Subtitle_MAX = None

	@classmethod
	def setFontStyle(cls, *args):
		pass  # Dummy method


class ePixmap(_eWidget):
	def size(self, *args):
		return _getPicture()


@add_metaclass(ClassVariables)
class eListboxPythonConfigContent(_einstances, object):
	def __init__(self):
		_einstances.__init__(self)
		self.__list = []
		self.getItemSize = _getDesktop
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


eListboxPythonStringContent = eListboxPythonConfigContent
eListboxPythonMultiContent = eListboxPythonConfigContent


class _eEPGCache(_einstances):
	def __init__(self):
		_einstances.__init__(self)
		self.getInstance = _einstances


eEPGCache = _eEPGCache()


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


enigma_fonts = {}


def addFont(filename, name, *args):
	global enigma_fonts
	enigma_fonts[name] = filename


def getFontFaces():
	return enigma_fonts


def ePoint(*args):
	pass  # Dummy function


def eGetEnigmaDebugLvl():
	return 6


def setPreferredTuner(*args):
	pass  # Dummy function


def gFont(*args):
	return ''


def gRGB(*args):
	return ''


def setTunerTypePriorityOrder(*args):
	pass  # Dummy function


def setSpinnerOnOff(*args):
	pass  # Dummy function


def setEnableTtCachingOnOff(*args):
	pass  # Dummy function


def setListBoxScrollbarStyle(*args):
	pass  # Dummy function


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


def ngettext(singular, plural, n):
	return singular


globals()['__builtins__']['ngettext'] = ngettext


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
	Components.ParentalControl.InitParentalControl()

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
