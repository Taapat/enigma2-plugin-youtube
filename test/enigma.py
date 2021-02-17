from __future__ import print_function


eWindowStyleManager = None
addFont = None
eWindowStyleSkinned = None
eButton = None
eSubtitleWidget = None
iRecordableServicePtr = None
iServiceInformation = None
eRect = None
eDVBCI_UI = None
eVideoWidget = None
getBestPlayableServiceReference = None
getPrevAsciiCode = None
quitMainloop = None

eServiceReferenceFS = None
eDVBFrontend = None
getBsodCounter = None
resetBsodCounter = None

ePythonOutput = None
iPlayableServicePtr = None


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


class _eAttr:
	def __init__(self, *x):
		pass

	def __setattr__(self, name, value, *x):
		self.__dict__[name] = value

	def __getattr__(self, attr):
		if attr in self.__dict__:
			return self.__dict__[attr]
		else:
			return ''


eDVBFrontendParametersSatellite = _eAttr()
eDVBSatelliteDiseqcParameters = _eAttr()
eDVBSatelliteSwitchParameters = _eAttr()
eDVBSatelliteRotorParameters = _eAttr()
eDVBFrontendParametersCable = _eAttr()
eDVBFrontendParametersTerrestrial = _eAttr()
eDVBFrontendParametersATSC = _eAttr()
iRdsDecoder = _eAttr()
eDVBServicePMTHandler = _eAttr()

eDVBSatelliteLNBParameters = _eAttr()
iDVBFrontend = _eAttr()


class eTimer:
	def __init__(self):
		self.callback = []
		self.timeout = _eAttr()
		self.timeout.callback = []
		print('new timer')

	def start(self, msec, singleshot=False):
		print('start timer', msec, singleshot)
		for x in self.timeout.callback:
			x()
		for x in self.callback:
			if singleshot and x in self.callback:
				self.callback.remove(x)
			x()

	def stop(self):
		print('stop timer')


class _Instances:
	def getNumOfSlots(self):
		return 1

	def getMaxLnbNum(self):
		return 1

	def __getattr__(self, attr):
		def default(*x):
			return 0
		return default

	def get(self):
		return []


class _eInstances(_eAttr):
	def __init__(self, *x):
		self.getInstance = _Instances


eDVBCIInterfaces = _eInstances()
Misc_Options = _eInstances()
eStreamServer = _eInstances()
eDVBDB = _eInstances()
eActionMap = _eInstances()
fontRenderClass = _eInstances()
eBackgroundFileEraser = _eInstances()
eDVBLocalTimeHandler = _eInstances()
eAVSwitch = _eInstances()
eDVBVolumecontrol = _eInstances()
eRCInput = _eInstances()
eRFmod = _eInstances()
eDBoxLCD = _eInstances()


def getFontFaces():
	return ''


def ePoint(x, y):
	pass


def eSize(x, y):
	pass


def eGetEnigmaDebugLvl():
	return 6


def setPreferredTuner(x):
	pass


def gFont(x, y):
	return ''


def gRGB(x):
	return ''


def setTunerTypePriorityOrder(x):
	pass


def setSpinnerOnOff(x):
	pass


def setEnableTtCachingOnOff(x):
	pass


class _eDVBResourceManager(_eAttr):
	def __init__(self, *x):
		self.frontendUseMaskChanged = _Instances()

	def __getattr__(self, attr):
		def default(*x):
			return 0
		return default


eDVBResourceManager = _eAttr()
eDVBResourceManager.getInstance = _eDVBResourceManager


class pNavigation:
	isRealRecording = 1
	isStreaming = 2
	isPseudoRecording = 4
	isUnknownRecording = 8
	isFromTimer = 0x10
	isFromInstantRecording = 0x20
	isFromEPGrefresh = 0x40
	isFromSpecialJumpFastZap = 0x80
	isAnyRecording = 0xFF

	def __init__(self, *x):
		self.m_event = _Instances()
		self.m_record_event = _Instances()

	def getCurrentService(self):
		return ''

	def getRecordings(self, *x):
		return ''


class _eServiceEvent:
	def setEPGLanguage(self, x):
		pass

	def setEPGLanguageAlternative(self, x):
		pass


eServiceEvent = _eServiceEvent()


class ePicLoad:
	def __init__(self):
		self.PictureData = _Instances()

	def setPara(self, x):
		pass

	def startDecode(self, x):
		pass

	def getData(self):
		pass


class eSlider:
	def __init__(self, x):
		self.orVertical = 1


class eListboxPythonConfigContent:
	def __init__(self):
		self.__list = []

	def setSeperation(self, x):
		pass

	def setSlider(self, *x):
		pass

	def getCurrentSelection(self):
		return self.__list and self.__list[0]

	def getCurrentSelectionIndex(self):
		return 0

	def invalidateEntry(self, x):
		pass

	def setList(self, _list):
		if _list:
			self.__list = _list
			_list[0][1].onSelect(_session)


eListboxPythonStringContent = eListboxPythonConfigContent


class eListboxPythonMultiContent:
	TYPE_PIXMAP_ALPHATEST = None
	TYPE_TEXT = None
	TYPE_PROGRESS = None

	def __init__(self):
		self.getItemSize = _getDesktop

	def invalidateEntry(self, x):
		pass

	def setFont(self, *x):
		pass

	def setItemHeight(self, x):
		pass

	def getCurrentSelectionIndex(self):
		return 0

	def getCurrentSelection(self):
		return ''

	def setBuildFunc(self, x):
		pass

	def setList(self, x):
		pass

	def setTemplate(self, x):
		pass


class _eDVBSatelliteEquipmentControl(_eInstances):
	def __init__(self):
		_eInstances.__init__(self)

	def setParam(self, *x):
		pass


eDVBSatelliteEquipmentControl = _eDVBSatelliteEquipmentControl()


class eListboxServiceContent(_eInstances):
	def __init__(self):
		_eInstances.__init__(self)

	def LoadPixmap(self, *x):
		pass


class iPlayableService:
	evStart = None
	evEnd = None
	evUpdatedInfo = None
	evVideoSizeChanged = None
	evUpdatedEventInfo = None
	evNewProgramInfo = None
	evCuesheetChanged = None
	evVideoGammaChanged = None
	evHBBTVInfo = None
	evTunedIn = None


class eConsoleAppContainer:
	def __init__(self):
		self.dataAvail = []
		self.appClosed = []

	def execute(self, *x):
		pass

	def getPID(self):
		pass


class _eEnv:
	def resolve(self, x):
		x = x.replace('${datadir}/enigma2/po/', './enigma2/po/')
		x = x.replace('${datadir}/enigma2/', './enigma2/data/')
		x = x.replace('${sysconfdir}/enigma2/', '/tmp/')
		x = x.replace('${sysconfdir}/', '/tmp/')
		x = x.replace('${libdir}/enigma2/', './enigma2/lib/')
		x = x.replace('${libdir}/', './enigma2/')
		x = x.replace('/media/', '/tmp/media/')
		return x


eEnv = _eEnv()


class _getPicture:
	def height(self):
		return 60

	def width(self):
		return 100

	def left(self):
		return 0

	def top(self):
		return 0


class loadPNG:
	def __init__(self, path, *x):
		self.size = _getPicture
		self.return_path(path)

	def return_path(self, path):
		return path.replace('/usr/lib/enigma2', './enigma2/lib')


class loadJPG:
	def __init__(self, path, *x):
		self.size = _getPicture
		self.return_path(path)

	def return_path(self, path):
		return path.replace('/usr/lib/enigma2', './enigma2/lib')


class _getDesktop:
	def height(self):
		return 720

	def width(self):
		return 1280

	def left(self):
		return 0

	def top(self):
		return 0


class getDesktop:
	def __init__(self, x):
		self.size = _getDesktop

	def bounds(self):
		return _getDesktop()

	def makeCompatiblePixmap(self, x):
		pass

	def getStyleID(self):
		return 1


class ePixmapPosition:
	def x(self):
		return 0

	def y(self):
		return 0


class eWidget:
	def __init__(self, x):
		pass

	def show(self):
		pass

	def hide(self):
		pass

	def position(self, *x):
		return ePixmapPosition()

	def resize(self, x):
		pass

	def move(self, x):
		pass

	def size(self, *x):
		return _getDesktop()

	def setZPosition(self, x):
		pass

	def setTransparent(self, x):
		pass


class eLabel(eWidget):
	def __init__(self, *x):
		pass

	def setText(self, x):
		pass

	def font(self, x):
		pass

	def setHAlign(self, x):
		pass

	def alignLeft(self):
		pass

	def alignCenter(self):
		pass

	def alignRight(self):
		pass

	def alignBlock(self):
		pass

	def setVAlign(self, x):
		pass

	def alignTop(self):
		pass

	def alignBottom(self):
		pass

	def setFont(self, x):
		pass

	def getNoWrap(self):
		pass

	def setNoWrap(self, x):
		pass

	def calculateSize(self):
		return _getDesktop()

	def setMarkedPos(self, x):
		pass


class eListbox(eWidget):
	def __init__(self, *x):
		self.selectionChanged = _Instances()

	def get(self):
		return []

	def setContent(self, x):
		pass

	def setWrapAround(self, x):
		pass

	def allowNativeKeys(self, x):
		pass

	def setSelectionEnable(self, x):
		pass

	def setScrollbarMode(self, x):
		pass

	def getCurrentIndex(self):
		return 0

	def moveSelectionTo(self, x):
		pass

	def showOnDemand(self):
		pass

	def showAlways(self):
		pass

	def showNever(self):
		pass

	def showLeft(self):
		pass


class eWindow(eWidget):
	def __init__(self, *x):
		self.getInstance = _Instances
		self.size = _getDesktop

	def title(self, x):
		pass

	def setTitle(self, x):
		pass

	def setAnimationMode(self, x):
		pass


class ePixmap(eWidget):
	def __init__(self, x):
		self.size = _getPicture

	def setAlphatest(self, x):
		pass

	def setPixmap(self, x):
		pass


class _eEPGCache:
	MHW = 8
	VIRGIN_NOWNEXT = 2048
	VIRGIN_SCHEDULE = 4096
	OPENTV = 16384

	def __init__(self):
		self.getInstance = _Instances

	def lookupEventTime(self, ref, query):
		return None

	def setEpgSources(self, mask):
		pass

	def setEpgHistorySeconds(self, s):
		pass

	def timeUpdated(self):
		pass


eEPGCache = _eEPGCache()


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


class eServiceReference(_eAttr):
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

	def __init__(self, *x):
		self.getInstance = _Instances

	def setName(self, x):
		pass

	def setPath(self, x):
		pass

	def getPath(self):
		return ''

	def toString(self):
		return ''


class iRecordableService(_eAttr):
	evStart = None
	evEnd = None
	evTunedIn = None
	evTuneFailed = None
	evRecordRunning = None
	evRecordStopped = None
	evNewProgramInfo = None
	evRecordFailed = None
	evRecordWriteError = None
	evNewEventInfo = None
	evRecordAborted = None
	evGstRecordEnded = None

	def __init__(self, ref):
		self.getInstance = _Instances


class _eServiceCenter:
	def __init__(self):
		self.getInstance = _Instances

	def info(self, ref):
		return None


eServiceCenter = _eServiceCenter()


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
		print('Session exec begin')
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
		print('Session openWithCallback')
		dlg = self.open(screen, *arguments, **kwargs)
		dlg.callback = callback
		return dlg

	def open(self, screen, *arguments, **kwargs):
		print('Session open ', screen)
		self.pushCurrent()
		dlg = self.current_dialog = self.instantiateDialog(screen, *arguments, **kwargs)
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


def ngettext(a, b, i):
	return a


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

	print('init av')
	import Components.AVSwitch
	Components.AVSwitch.InitAVSwitch()

	print('init misc')
	from Components.config import config, ConfigYesNo, ConfigInteger
	config.misc.RestartUI = ConfigYesNo(default=False)
	config.misc.prev_wakeup_time = ConfigInteger(default=0)
	config.misc.prev_wakeup_time_type = ConfigInteger(default=0)

	_session = Session(getDesktop(1), Navigation())

	return _session
