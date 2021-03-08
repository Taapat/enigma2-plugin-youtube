from __future__ import print_function


RT_VALIGN_TOP = 0
RT_HALIGN_LEFT = 1
RT_HALIGN_RIGHT = 2
RT_HALIGN_CENTER = 4
RT_VALIGN_CENTER = 16
RT_VALIGN_BOTTOM = 32
RT_WRAP = 64
BT_SCALE = 4
BT_KEEP_ASPECT_RATIO = 8
BT_HALIGN_CENTER = 16
BT_VALIGN_CENTER = 64
BT_ALIGN_CENTER = BT_HALIGN_CENTER | BT_VALIGN_CENTER


class _eInstances:
	@classmethod
	def getInstance(self):
		return self.instance

	instance = None

	def __init__(self, *args):
		_eInstances.instance = self

	def __setattr__(self, name, value, *args):
		self.__dict__[name] = value

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default

	def get(self):
		return []


eAVSwitch = _eInstances()
eBackgroundFileEraser = _eInstances()
eDBoxLCD = _eInstances()
eDVBCIInterfaces = _eInstances()
eDVBDB = _eInstances()
eDVBFrontendParametersATSC = _eInstances()
eDVBFrontendParametersCable = _eInstances()
eDVBFrontendParametersSatellite = _eInstances()
eDVBFrontendParametersTerrestrial = _eInstances()
eDVBLocalTimeHandler = _eInstances()
eDVBResourceManager = _eInstances()
eDVBSatelliteDiseqcParameters = _eInstances()
eDVBSatelliteEquipmentControl = _eInstances()
eDVBSatelliteLNBParameters = _eInstances()
eDVBSatelliteRotorParameters = _eInstances()
eDVBSatelliteSwitchParameters = _eInstances()
eDVBServicePMTHandler = _eInstances()
eDVBVolumecontrol = _eInstances()
eListboxServiceContent = _eInstances()
eRCInput = _eInstances()
eRFmod = _eInstances()
eServiceCenter = _eInstances()
eServiceEvent = _eInstances()
eSlider = _eInstances()
eStreamServer = _eInstances()
fontRenderClass = _eInstances()
gMainDC = _eInstances()
iDVBFrontend = _eInstances()
iPlayableService = _eInstances()
iRdsDecoder = _eInstances()
iRecordableService = _eInstances()
Misc_Options = _eInstances()
eWindowStyleManager = _eInstances()
eButton = _eInstances()
iRecordableServicePtr = _eInstances()
iServiceInformation = _eInstances()
eRect = _eInstances()
eDVBCI_UI = _eInstances()
getBestPlayableServiceReference = _eInstances()
getPrevAsciiCode = _eInstances()
quitMainloop = _eInstances()
eServiceReferenceFS = _eInstances()
eDVBFrontend = _eInstances()
getBsodCounter = _eInstances()
resetBsodCounter = _eInstances()
ePythonOutput = _eInstances()
iPlayableServicePtr = _eInstances()


class eTimer:
	def __init__(self):
		self.callback = []
		self.timeout = _eInstances()
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

	def stop(self):
		self.callback_thread = None


class _eDVBResourceManager(_eInstances):
	def __init__(self, *args):
		self.frontendUseMaskChanged = _eInstances()


eDVBResourceManager = _eInstances()
eDVBResourceManager.getInstance = _eDVBResourceManager


class pNavigation(_eInstances):
	isRealRecording = 1
	isStreaming = 2
	isPseudoRecording = 4
	isUnknownRecording = 8
	isFromTimer = 0x10
	isFromInstantRecording = 0x20
	isFromEPGrefresh = 0x40
	isFromSpecialJumpFastZap = 0x80
	isAnyRecording = 0xFF

	def __init__(self, *args):
		self.m_event = _eInstances()
		self.m_record_event = _eInstances()

	def getCurrentService(self):
		return ''

	def getRecordings(self, *args):
		return ''


class eServiceReferenceDVB:
	invalid = -1,
	dTv = 0x01
	dRadio = 0x02
	tText = 0x03
	nvod = 0x04
	nvodTs = 0x05
	mosaic = 0x06
	radioFm = 0x07
	dvbSrm = 0x08
	dRadioAvc = 0x0A
	mosaicAvc = 0x0B
	datacast = 0x0C
	ci = 0x0D
	rcsMap = 0x0E
	rcsFls = 0x0F
	dvbMhp = 0x10
	mpeg2HdTv = 0x11
	avcSdTv = 0x16
	nvodAvcSdTs = 0x17
	nvodAvcSdRef = 0x18
	avcHdTv = 0x19
	nvodAvcHdTs = 0x1A
	nvodAvcHdRef = 0x1B
	avcHdStereo = 0x1C
	nvodAvcHdStereoTs = 0x1D
	nvodAvcHdStereoRef = 0x1E
	nvecTv = 0x1F
	user134 = 0x86
	user195 = 0xC


class eServiceReference:
	idInvalid = -1
	isDirectory = 1
	mustDescent = 2
	canDescent = 4
	flagDirectory = isDirectory | mustDescent | canDescent
	shouldSort = 8
	hasSortKey = 16
	sort1 = 32
	isMarker = 64
	isGroup = 128
	idDVB = None

	@classmethod
	def getInstance(self):
		return self.instance

	instance = None

	def __init__(self, ref_type=0, flags=0, data='', *args):
		eServiceReference.instance = self
		self._data = data
		self._name = ''

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default

	def setName(self, name):
		self._name = name

	def getName(self):
		return self._name

	def getPath(self):
		return self._data


class ePicLoad:
	@classmethod
	def getInstance(self):
		return self.instance

	instance = None

	def __init__(self):
		ePicLoad.PictureData = self
		self._functions = []
		self._image = None

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default

	def get(self):
		return self._functions

	def startDecode(self, image):
		print('ePicLoad decode', image)
		self._image = image
		for f in self._functions:
			self._functions.remove(f)
			f()

	def getData(self):
		return self._image


sel_index = 0


class eListboxPythonConfigContent:
	def __init__(self):
		self.__list = []
		global sel_index
		sel_index = 0

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default

	def getCurrentSelection(self):
		if self.__list:
			if len(self.__list) >= sel_index:
				return self.__list[sel_index]
			else:
				return self.__list[0]

	def setList(self, _list):
		if _list:
			self.__list = _list
			try:
				_list[0][1].onSelect(_session)
			except AttributeError:
				pass


eListboxPythonStringContent = eListboxPythonConfigContent


class eListboxPythonMultiContent:
	TYPE_TEXT = None
	TYPE_PROGRESS = None
	TYPE_PIXMAP = None
	TYPE_PIXMAP_ALPHATEST = None
	TYPE_PIXMAP_ALPHABLEND = None
	TYPE_PROGRESS_PIXMAP = None

	def __init__(self):
		self.getItemSize = _getDesktop

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default

	def getCurrentSelectionIndex(self):
		return 0

	def getCurrentSelection(self):
		return ''


class eConsoleAppContainer:
	def __init__(self):
		self.dataAvail = []
		self.appClosed = []

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default


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


class _getPicture:
	def height(self):
		return 60

	def width(self):
		return 100

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default


class loadPNG:
	def __init__(self, path, *args):
		self.size = _getPicture
		self.return_path(path)

	def return_path(self, path):
		return path.replace('/usr/lib/enigma2', './enigma2/lib')


class loadJPG:
	def __init__(self, path, *args):
		self.size = _getPicture
		self.return_path(path)

	def return_path(self, path):
		return path.replace('/usr/lib/enigma2', './enigma2/lib')


class _getDesktop:
	def __init__(self, *args):
		pass

	def height(self):
		return 720

	def width(self):
		return 1280

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default


eSize = _getDesktop


class getDesktop:
	def __init__(self, *args):
		self.size = _getDesktop

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default

	def bounds(self):
		return _getDesktop()

	def getStyleID(self):
		return 1


class ePixmapPosition:
	def x(self):
		return 0

	def y(self):
		return 0


class eWidget:
	wfNoBorder = None

	def __init__(self, *args):
		self.selectionChanged = _eInstances()
		self.getInstance = _eInstances
		self._index = 0

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default

	def get(self):
		return []

	def position(self, *args):
		return ePixmapPosition()

	def size(self, *args):
		return _getDesktop()

	def calculateSize(self):
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


eLabel = eWidget
eListbox = eWidget
eWindow = eWidget
eVideoWidget = eWidget


class eWindowStyleSkinned(eWidget):
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


class eSubtitleWidget:
	Subtitle_TTX = None
	Subtitle_Regular = None
	Subtitle_Bold = None
	Subtitle_Italic = None
	Subtitle_MAX = None

	@classmethod
	def setFontStyle(self, *args):
		pass


class ePixmap(eWidget):
	def size(self, *args):
		return _getPicture()


class _eEPGCache:
	MHW = 8
	VIRGIN_NOWNEXT = 2048
	VIRGIN_SCHEDULE = 4096
	OPENTV = 16384

	def __init__(self):
		self.getInstance = _eInstances

	def __getattr__(self, attr):
		def default(*args):
			return 0
		return default


eEPGCache = _eEPGCache()


class eActionMap:
	@classmethod
	def getInstance(self):
		return self.instance

	instance = None

	def __init__(self):
		eActionMap.instance = self

	def bindKey(self, *args):
		pass

	def bindToggle(self, *args):
		pass

	def bindTranslation(self, *args):
		pass

	def bindAction(self, *args):
		pass

	def unbindAction(self, *args):
		pass


eActionMap()


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
	pass


def eGetEnigmaDebugLvl():
	return 6


def setPreferredTuner(*args):
	pass


def gFont(*args):
	return ''


def gRGB(*args):
	return ''


def setTunerTypePriorityOrder(*args):
	pass


def setSpinnerOnOff(*args):
	pass


def setEnableTtCachingOnOff(*args):
	pass


def new_activateLanguage(self, index):
	if index not in self.lang:
		print('Selected language does not exist, fallback to de_DE!')
		index = 'de_DE'
	self.lang[index] = ('Deutsch', 'de', 'DE', 'ISO-8859-15')
	self.activeLanguage = index
	print('Activating language de_DE')


def new_index(self, value):
	try:
		return self.__list__().index(value)
	except (ValueError, IndexError):
		return 0


from Screens.Screen import Screen


class new_MoviePlayer(Screen):
	def __init__(self, session, service, *args):
		Screen.__init__(self, session)
		print('[MoviePlayer] service:', service.getName())


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
	Language.activateLanguage = new_activateLanguage
	language.activateLanguage('de_DE')

	try:  # OpenVix
		import Components.ClientMode
	except ImportError:
		pass
	else:
		print('init client mode')
		Components.ClientMode.InitClientMode()

	print('init simple summary')
	from Screens import InfoBar
	InfoBar.MoviePlayer = new_MoviePlayer
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

	# ATV
	print('init setup devices')
	import Components.SetupDevices
	Components.SetupDevices.InitSetupDevices()

	try:  # OpenVix
		import Components.EpgConfig
	except ImportError:
		pass
	else:
		print('init epg config')
		Components.EpgConfig.InitEPGConfig()

	print('init usage')
	import Components.UsageConfig
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
