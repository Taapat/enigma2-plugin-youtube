from __future__ import print_function


eSize = None
gFont = None
eWindowStyleManager = None
loadPNG = None
addFont = None
eWindowStyleSkinned = None
eButton = None
eListboxPythonStringContent = None
eSubtitleWidget = None
iRecordableServicePtr = None
iServiceInformation = None
eRect = None
getFontFaces = None
eDVBCI_UI = None
eVideoWidget = None
getBestPlayableServiceReference = None
getPrevAsciiCode = None
quitMainloop = None

eServiceReferenceFS = None
eDVBFrontend = None
getBsodCounter = None
resetBsodCounter = None


RT_HALIGN_LEFT = 1
RT_HALIGN_RIGHT = 2
RT_VALIGN_CENTER = 3
RT_VALIGN_TOP = 4
BT_SCALE = 5
RT_HALIGN_CENTER = 6
RT_VALIGN_BOTTOM = 7

BT_KEEP_ASPECT_RATIO = 8
RT_WRAP = 9


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
ePoint = _eAttr()

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
			if singleshot and x in self.timeout.callback:
				self.timeout.callback.remove(x)
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


def eGetEnigmaDebugLvl():
	return 6


def loadPNG(*x):
	pass


def loadJPG(*x):
	pass


def setPreferredTuner(x):
	pass


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


class eListbox:
	def __init__(self, *x):
		self.selectionChanged = _Instances()

	def setContent(self, x):
		pass

	def setWrapAround(self, x):
		pass


eListbox()


class eWindow:
	def __init__(self, *x):
		self.getInstance = _Instances

	def show(self):
		pass

	def hide(self):
		pass

	def size(self, x):
		pass

	def title(self, x):
		pass

	def position(self, x):
		pass


eWindow()


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


class eLabel:
	def __init__(self, *x):
		pass

	def setText(self, x):
		pass

	def font(self, x):
		pass

	def position(self, x):
		pass

	def size(self, x):
		pass


class eWidget:
	def __init__(self, x):
		pass

	def move(self, x):
		pass

	def resize(self, x):
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
		print('getCurrentSelection', self.__list[0])
		return self.__list and self.__list[0]

	def getCurrentSelectionIndex(self):
		return 0

	def invalidateEntry(self, x):
		pass

	def setList(self, x):
		self.__list = x


eListboxPythonStringContent = eListboxPythonConfigContent


class eListboxPythonMultiContent:
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
	evStart = 1
	evEnd = 2
	evUpdatedInfo = 3
	evVideoSizeChanged = 4
	evUpdatedEventInfo = 5
	evNewProgramInfo = 6
	evCuesheetChanged = 7
	evVideoGammaChanged = 8
	evHBBTVInfo = 9
	evTunedIn = 10


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


class ePixmapPosition:
	def x(self):
		return 0

	def y(self):
		return 0


class ePixmap:
	def __init__(self, x):
		self.size = _getDesktop

	def show(self):
		pass

	def hide(self):
		pass

	def position(self):
		return ePixmapPosition()


class _eEPGCache:
	MHW = 1
	VIRGIN_NOWNEXT = 2
	VIRGIN_SCHEDULE = 3
	OPENTV = 4

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
	isDirectory = 1
	mustDescent = 2
	canDescent = 4
	flagDirectory = isDirectory | mustDescent | canDescent
	shouldSort = 8
	hasSortKey = 16
	sort1 = 32
	isMarker = 64
	isGroup = 128
	idInvalid = 256

	idDVB = 512

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
	evEnd = 1
	evStart = 2

	def __init__(self, ref):
		self.getInstance = _Instances


class _eServiceCenter:
	def __init__(self):
		self.getInstance = _Instances

	def info(self, ref):
		return None


eServiceCenter = _eServiceCenter()


class Session:
	def __init__(self, desktop=None, summary_desktop=None, navigation=None):
		print('Session init')
		self.desktop = desktop
		self.summary_desktop = summary_desktop
		self.nav = navigation
		self.current_dialog = None
		self.dialog_stack = []
		self.summary_stack = []
		self.summary = None
		self.in_exec = False
		from Screens.SessionGlobals import SessionGlobals
		self.screen = SessionGlobals(self)

	def execBegin(self, first=True, do_show=True):
		print('Session execBegin')
		assert not self.in_exec
		self.in_exec = True
		c = self.current_dialog

		# when this is an execbegin after a execend of a "higher" dialog,
		# popSummary already did the right thing.
		if first:
			self.instantiateSummaryDialog(c)

		c.saveKeyboardMode()
		c.execBegin()

		# when execBegin opened a new dialog, don't bother showing the old one.
		if c == self.current_dialog and do_show:
			c.show()

	def execEnd(self, last=True):
		print('Session execEnd')
		assert self.in_exec
		self.in_exec = False

		self.current_dialog.execEnd()
		self.current_dialog.restoreKeyboardMode()
		self.current_dialog.hide()

	def instantiateDialog(self, screen, *arguments, **kwargs):
		print('Session instantiateDialog')
		return self.doInstantiateDialog(screen, arguments, kwargs, self.desktop)

	def instantiateSummaryDialog(self, screen, **kwargs):
		print('Session instantiateSummaryDialog')
		if self.summary_desktop is not None:
			self.pushSummary()
			from Screens.SimpleSummary import SimpleSummary
			summary = screen.createSummary() or SimpleSummary
			arguments = (screen,)
			self.summary = self.doInstantiateDialog(summary, arguments, kwargs, self.summary_desktop)
			self.summary.show()
			screen.addSummary(self.summary)

	def doInstantiateDialog(self, screen, arguments, kwargs, desktop):
		print('Session doInstantiateDialog')
		# create dialog
		dlg = screen(self, *arguments, **kwargs)
		if dlg is None:
			return
		# read skin data
		from skin import readSkin
		readSkin(dlg, None, dlg.skinName, desktop)
		# create GUI view of this dialog
		dlg.setDesktop(desktop)
		dlg.applySkin()
		return dlg

	def pushCurrent(self):
		print('Session pushCurrent')
		if self.current_dialog is not None:
			self.dialog_stack.append((self.current_dialog, self.current_dialog.shown))
			self.execEnd(last=False)

	def openWithCallback(self, callback, screen, *arguments, **kwargs):
		print('Session openWithCallback')
		dlg = self.open(screen, *arguments, **kwargs)
		dlg.callback = callback
		return dlg

	def open(self, screen, *arguments, **kwargs):
		print('Session open')
		if self.dialog_stack and not self.in_exec:
			raise RuntimeError("modal open are allowed only from a screen which is modal!")
			# ...unless it's the very first screen.

		self.pushCurrent()
		dlg = self.current_dialog = self.instantiateDialog(screen, *arguments, **kwargs)
		dlg.isTmp = True
		dlg.callback = None
		self.execBegin()
		return dlg

	def pushSummary(self):
		print('Session pushSummary')
		if self.summary:
			self.summary.hide()
			self.summary_stack.append(self.summary)
			self.summary = None


def new_activateLanguage(self, index):
	if index not in self.lang:
		print('Selected language %s does not exist, fallback to de_DE!' % index)
		index = 'de_DE'
	self.lang[index] = ('Deutsch', 'de', 'DE', 'ISO-8859-15')
	lang = self.lang[index]
	self.activeLanguage = index
	print('Activating language', lang)


def new_getCurrent(self):
	return self._List__list and self._List__list[0]


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
	from Components.Language import Language
	Language.activateLanguage = new_activateLanguage
	Language().activateLanguage(0)

	print('init simple summary')
	from Screens import InfoBar
	from Screens.SimpleSummary import SimpleSummary

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

	print('change list')
	from Components.Sources.List import List
	List.getCurrent = new_getCurrent

	_session = Session(getDesktop(1), getDesktop(2), Navigation())

	return _session
