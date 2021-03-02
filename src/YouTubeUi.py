from __future__ import print_function

import os
from twisted.web.client import downloadPage

from enigma import ePicLoad, eServiceReference, eTimer, getDesktop, iPlayableService
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.config import config, ConfigDirectory, ConfigSelection, \
	ConfigSet, ConfigSubDict, ConfigSubsection, ConfigText, ConfigYesNo, \
	getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Language import language
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Task import job_manager
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_HDD, SCOPE_PLUGINS

from . import _
from . import ngettext


try:
	from Tools.CountryCodes import ISO3166
except Exception:
	# Workaround if CountryCodes not exist (BH, VTI)
	ISO3166 = [(x[1][0], x[1][2]) for x in language.getLanguageList() if x[1][2] != 'EN']


config.plugins.YouTube = ConfigSubsection()
config.plugins.YouTube.saveHistory = ConfigYesNo(default=True)
config.plugins.YouTube.searchResult = ConfigSelection(default='24',
	choices=[('4', '4'),
		('8', '8'),
		('16', '16'),
		('24', '24'),
		('50', '50')])
config.plugins.YouTube.searchRegion = ConfigSelection(
	default=language.getLanguage().split('_')[1] if language.getLanguage().split('_')[1] != 'EN' else '',
	choices=[('', _('All'))] + [(x[1], x[0]) for x in ISO3166])
config.plugins.YouTube.searchLanguage = ConfigSelection(
	default=language.getLanguage().split('_')[0],
	choices=[('', _('All'))] + [(x[1][1], x[1][0]) for x in language.getLanguageList()])
config.plugins.YouTube.searchOrder = ConfigSelection(default='relevance',
	choices=[('relevance', _('Relevance')),
		('date', _('Created date')),
		('rating', _('Rating')),
		('title', _('Title')),
		('viewCount', _('View count'))])
config.plugins.YouTube.subscriptOrder = ConfigSelection(default='relevance',
	choices=[('relevance', _('By relevance')),
		('unread', _('By activity')),
		('alphabetical', _('Alphabetically'))])
config.plugins.YouTube.safeSearch = ConfigSelection(default='moderate', choices=[
	('moderate', _('Moderate')), ('none', _('No')), ('strict', _('Yes'))])
config.plugins.YouTube.maxResolution = ConfigSelection(default='22', choices=[
	('38', '4096x3072'), ('37', '1920x1080'), ('22', '1280x720'), ('35', '854x480'),
	('18', '640x360'), ('5', '400x240'), ('17', '176x144')])
config.plugins.YouTube.onMovieEof = ConfigSelection(default='quit', choices=[
	('quit', _('Return to list')), ('ask', _('Ask user')),
	('playnext', _('Play next')), ('repeat', _('Repeat')),
	('playprev', _('Play previous'))])
config.plugins.YouTube.onMovieStop = ConfigSelection(default='ask', choices=[
	('ask', _('Ask user')), ('quit', _('Return to list'))])
config.plugins.YouTube.login = ConfigYesNo(default=False)
config.plugins.YouTube.downloadDir = ConfigDirectory(default=resolveFilename(SCOPE_HDD))
config.plugins.YouTube.useDashMP4 = ConfigYesNo(default=True)
config.plugins.YouTube.mergeFiles = ConfigYesNo(default=False)
config.plugins.YouTube.player = ConfigSelection(default='4097', choices=[
	('4097', _('Default')), ('5002', _('Exteplayer')), ('5001', _('Gstplayer'))])

# Dublicate entry list in createSearchList
config.plugins.YouTube.searchHistoryDict = ConfigSubDict()
config.plugins.YouTube.searchHistoryDict['Searchvideo'] = ConfigSet(choices=[])
config.plugins.YouTube.searchHistoryDict['Searchchannel'] = ConfigSet(choices=[])
config.plugins.YouTube.searchHistoryDict['Searchplaylist'] = ConfigSet(choices=[])
config.plugins.YouTube.searchHistoryDict['Searchbroadcasts'] = ConfigSet(choices=[])

config.plugins.YouTube.refreshToken = ConfigText()
config.plugins.YouTube.lastPosition = ConfigText(default='[]')


# Workaround to keep compatibility broken once again on OpenPLi develop
BUTTONS_FOLDER = 'skin_default'
if os.path.exists('/usr/share/enigma2/skin_fallback_1080/buttons/red.png'):
	BUTTONS_FOLDER = 'skin_fallback_1080'


class YouTubePlayer(MoviePlayer):
	def __init__(self, session, service, current):
		MoviePlayer.__init__(self, session, service)
		self.skinName = ['YouTubeMoviePlayer', 'MoviePlayer']
		self.current = current
		self.__youtube_event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evStart: self.__serviceStart,
				iPlayableService.evVideoSizeChanged: self.__serviceStart})  # On exteplayer evStart not working
		self.servicelist = InfoBar.instance and InfoBar.instance.servicelist
		self.started = False
		self.lastPosition = []

	def __serviceStart(self):
		if not self.started:
			self.started = True
			self.lastPosition = eval(config.plugins.YouTube.lastPosition.value)
			if self.current[0] in self.lastPosition:
				idx = self.lastPosition.index(self.current[0])
				self.lastPosition.pop(idx)
				self.seekPosition = self.lastPosition[idx]
				self.lastPosition.pop(idx)
				config.plugins.YouTube.lastPosition.value = str(self.lastPosition)
				config.plugins.YouTube.lastPosition.save()
				if '&suburi=' not in self.current[6] or \
						config.plugins.YouTube.player.value == '5002':
					self.session.openWithCallback(self.messageBoxCallback, MessageBox,
							text=_('Resume playback from the previous position?'), timeout=5)

	def messageBoxCallback(self, answer):
		if answer:
			service = self.session.nav.getCurrentService()
			seek = service and service.seek()
			if seek:
				seek.seekTo(self.seekPosition)

	def leavePlayer(self):
		if config.plugins.YouTube.onMovieStop.value == 'ask':
			title = _('Stop playing this movie?')
			list = ((_('Yes'), 'quit'),
					(_('Yes, but play next video'), 'playnext'),
					(_('Yes, but play previous video'), 'playprev'),
					(_('No, but play video again'), 'repeat'),
					(_('No'), 'continue'))
			self.session.openWithCallback(self.leavePlayerConfirmed,
				ChoiceBox, title=title, list=list)
		else:
			self.leavePlayerConfirmed([None, 'quit'])

	def leavePlayerConfirmed(self, answer):
		if answer and answer[1] != 'continue':
			service = self.session.nav.getCurrentService()
			seek = service and service.seek()
			if seek:
				if len(self.lastPosition) > 20:
					self.lastPosition.pop(0)
					self.lastPosition.pop(0)
				self.lastPosition.append(self.current[0])
				self.lastPosition.append(seek.getPlayPosition()[1])
				config.plugins.YouTube.lastPosition.value = str(self.lastPosition)
				config.plugins.YouTube.lastPosition.save()
			self.close(answer)

	def doEofInternal(self, playing):
		self.close([None, config.plugins.YouTube.onMovieEof.value])

	def getPluginList(self):
		list = []
		for p in plugins.getPlugins(where=PluginDescriptor.WHERE_EXTENSIONSMENU):
			if p.name != _('YouTube'):
				list.append(((boundFunction(self.getPluginName, p.name),
					boundFunction(self.runPlugin, p), lambda: True), None))
		return list

	def openCurEventView(self):
		self.session.open(YouTubeInfo, current=self.current)

	def showSecondInfoBar(self):
		self.hide()
		self.hideTimer.stop()
		self.openCurEventView()

	def showMovies(self):
		pass

	def openServiceList(self):
		if hasattr(self, 'toggleShow'):
			self.toggleShow()


class YouTubeMain(Screen):
	screenWidth = getDesktop(0).size().width()
	if screenWidth and screenWidth == 1280:
		skin = """<screen position="center,center" size="730,524">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_HD.png" \
					position="15,0" zPosition="2" size="100,40" alphatest="on" />
				<widget source="list" render="Listbox" position="15,42" size="700,432" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryPixmapAlphaTest(pos=(0,0), \
								size=(100,72), png=2), # Thumbnail
							MultiContentEntryText(pos=(110,1), size=(575,52), \
								font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_WRAP, text=3), # Title
							MultiContentEntryText(pos=(120, 50), size=(200,22), \
								font=1, flags=RT_HALIGN_LEFT, text=4), # Views
							MultiContentEntryText(pos=(360,50), size=(200,22), \
								font=1, flags=RT_HALIGN_LEFT, text=5), # Duration
							],
						"fonts": [gFont("Regular",20), gFont("Regular",16)],
						"itemHeight": 72}
					</convert>
				</widget>
				<widget name="info" position="50,489" size="35,25" pixmap="skin_default/buttons/key_info.png" \
					transparent="1" alphatest="on" />
				<widget name="red" position="215,477" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget name="green" position="375,477" size="140,40" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="215,482" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget source="key_green" render="Label" position="375,482" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget name="menu" position="645,489" size="35,25" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				<widget name="thumbnail" position="0,0" size="100,72" /> # Thumbnail size in list
			</screen>"""
	elif screenWidth and screenWidth == 1920:
		skin = """<screen position="center,center" size="1095,786">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_FHD.png" \
					position="22,0" zPosition="2" size="150,60" transparent="1" alphatest="on" />
				<widget source="list" render="Listbox" position="22,63" size="1050,648" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryPixmapAlphaTest(pos=(0,0), \
								size=(150,108), png=2), # Thumbnail
							MultiContentEntryText(pos=(165,1), size=(862,78), \
								font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_WRAP, text=3), # Title
							MultiContentEntryText(pos=(180, 75), size=(300,33), \
								font=1, flags=RT_HALIGN_LEFT, text=4), # Views
							MultiContentEntryText(pos=(540,75), size=(300,33), \
								font=1, flags=RT_HALIGN_LEFT, text=5), # Duration
							],
						"fonts": [gFont("Regular",30), gFont("Regular",24)],
						"itemHeight": 108}
					</convert>
				</widget>
				<widget name="red" position="322,722" size="210,60" pixmap="%s/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget name="green" position="563,722" size="210,60" pixmap="%s/buttons/green.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="322,729" zPosition="2" size="210,45" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
				<widget source="key_green" render="Label" position="563,729" zPosition="2" size="210,45" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
				<widget name="thumbnail" position="0,0" size="150,108" /> # Thumbnail size in list
			</screen>""" % (BUTTONS_FOLDER, BUTTONS_FOLDER)
	else:
		skin = """<screen position="center,center" size="630,380">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_HD.png" \
					position="15,0" zPosition="2" size="100,40" transparent="1" alphatest="on" />
				<widget source="list" render="Listbox" position="15,42" size="600,288" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryPixmapAlphaTest(pos=(0,0), \
								size=(100,72), png=2), # Thumbnail
							MultiContentEntryText(pos=(110,1), size=(475,52), \
								font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_WRAP, text=3), # Title
							MultiContentEntryText(pos=(120, 50), size=(200,22), \
								font=1, flags=RT_HALIGN_LEFT, text=4), # Views
							MultiContentEntryText(pos=(360,50), size=(200,22), \
								font=1, flags=RT_HALIGN_RIGHT, text=5), # Duration
							],
						"fonts": [gFont("Regular",20), gFont("Regular",16)],
						"itemHeight": 72}
					</convert>
				</widget>
				<widget name="info" position="30,345" size="35,25" pixmap="skin_default/buttons/key_info.png" \
					transparent="1" alphatest="on" />
				<widget name="red" position="114,333" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget name="green" position="374,333" size="140,40" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="114,338" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget source="key_green" render="Label" position="374,338" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget name="menu" position="565,345" size="35,25" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				<widget name="thumbnail" position="0,0" size="100,72" /> # Thumbnail size in list
			</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self['info'] = Pixmap()
		self['info'].hide()
		self['red'] = Pixmap()
		self['red'].hide()
		self['green'] = Pixmap()
		self['green'].hide()
		self['menu'] = Pixmap()
		self['menu'].hide()
		self['key_red'] = StaticText('')
		self['key_green'] = StaticText('')
		self['actions'] = ActionMap(['WizardActions', 'ColorActions', 'MovieSelectionActions'], {
				'back': self.cancel,
				'ok': self.ok,
				'red': self.cancel,
				'green': self.ok,
				'up': self.selectPrevious,
				'down': self.selectNext,
				'contextMenu': self.openMenu,
				'showEventInfo': self.showEventInfo}, -2)
		text = _('YouTube starting. Please wait...')
		self.setTitle(text)
		self['text'] = Label()  # For backward compatibility, removed after YouTube logo introduction
		self['text'].setText(_('YouTube'))  # Please use YouTube logo in skin instead of this
		self['list'] = List([])
		self['thumbnail'] = Pixmap()
		self['thumbnail'].hide()
		self.splitTaimer = eTimer()
		self.splitTaimer.timeout.callback.append(self.splitTaimerStop)
		self.picloads = {}
		self.thumbnails = {}
		self.sc = AVSwitch().getFramebufferScale()
		self.list = 'main'
		self.action = 'startup'
		self.current = []
		self.text = ''
		self.prevIndex = []
		self.prevEntryList = []
		self.entryList = []
		self.ytdl = None
		self.youtube = None
		self.nextPageToken = None
		self.prevPageToken = None
		self.pageToken = ''
		self.isAuth = False
		self.activeDownloads = 0
		self.searchResult = config.plugins.YouTube.searchResult.value
		self.pageIndex = 1
		self.onLayoutFinish.append(self.layoutFinish)
		self.onClose.append(self.cleanVariables)
		for p in plugins.getPlugins(where=PluginDescriptor.WHERE_MENU):
			# TRANSLATORS: Don't translate this! It is used as a variable, so it must be equal to the translation in the plugin!
			if p.name == _("ServiceApp"):
				break
		else:
			config.plugins.YouTube.player.value = '4097'

	def layoutFinish(self):
		self.thumbSize = [self['thumbnail'].instance.size().width(),
			self['thumbnail'].instance.size().height()]
		defThumbnail = resolveFilename(SCOPE_PLUGINS,
			'Extensions/YouTube/icons/icon.png')
		self.decodeThumbnail('default', defThumbnail)
		self.splitTaimer.start(1, True)

	def cleanVariables(self):
		del self.splitTaimer
		self.ytdl = None
		self.youtube = None
		self.thumbnails = None
		self.entryList = None
		self.prevEntryList = None

	def createDefEntryList(self, entry_list, append):
		self.current = []
		self.text = ''
		self.pageToken = ''
		if not append:
			self.entryList = []
		for Id, Title in entry_list:
			self.entryList.append((
					Id,     # Id
					'',     # Thumbnail url
					None,   # Thumbnail
					Title,  # Title
					'',     # Views
					'',     # Duration
					None,   # Video url
					None,   # Description
					None,   # Likes
					None,   # Dislikes
					'',     # Big thumbnail url
					None,   # Channel Id
					''))     # Published

	def createMainList(self):
		self.list = 'main'
		title = _('Choose what you want to do')
		self.createDefEntryList([['Search', _('Search')],
				['PubFeeds', _('Public feeds')]], False)
		if self.isAuth:
			self.createDefEntryList([['MyFeeds', _('My feeds')]], True)
		self.setEntryList(title)

	def createSearchList(self):
		self.list = 'search'
		title = _('Search')
		self.createDefEntryList([['Searchvideo', _('Search videos')],
				['Searchchannel', _('Search channels')],
				['Searchplaylist', _('Search playlists')],
				['Searchbroadcasts', _('Search live broadcasts')]], False)
		self.setEntryList(title)

	def createFeedList(self):
		self.list = 'feeds'
		title = _('Public feeds')
		self.createDefEntryList([['top_rated', _('Top rated')],
				['most_viewed', _('Most viewed')],
				['most_recent', _('Recent')],
				['HD_videos', _('HD videos')],
				['embedded_videos', _('Embedded in webpages')],
				['episodes', _('Shows')],
				['movies', _('Movies')]], False)
		self.setEntryList(title)

	def createMyFeedList(self):
		self.list = 'myfeeds'
		title = _('My feeds')
		self.createDefEntryList([['my_subscriptions', _('My Subscriptions')],
				['my_liked_videos', _('Liked videos')],
				['my_uploads', _('Uploads')],
				['my_playlists', _('Playlists')]], False)
		self.setEntryList(title)

	def screenCallback(self, current, text, action):
		self.current = current
		self.text = text
		self.action = action
		if action == 'OpenSearch':
			text = _('Download search results. Please wait...')
		elif action in ['playVideo', 'downloadVideo']:
			text = _('Extract video url. Please wait...')
		else:
			text = _('Download feed entries. Please wait...')
		self.setTitle(text)
		self['list'].setList([])
		self['key_red'].setText('')
		self['key_green'].setText('')
		self['red'].hide()
		self['green'].hide()
		self['menu'].hide()
		self['info'].hide()
		self.splitTaimer.start(1, True)

	def splitTaimerStop(self):
		if self.action == 'startup':
			from .YouTubeVideoUrl import YouTubeVideoUrl
			self.ytdl = YouTubeVideoUrl()
			self.createBuild()
			self.createMainList()
			for job in job_manager.getPendingJobs():
				self.activeDownloads += 1
		elif self.action in ['playVideo', 'downloadVideo']:
			videoUrl = self.current[6]
			if not videoUrl:  # remember video url
				videoUrl, urlError = self.getVideoUrl()
				if urlError:
					self.session.open(MessageBox,
							_('There was an error in extract video url:\n%s') % urlError,
							MessageBox.TYPE_INFO, timeout=8)
				else:
					count = 0
					for entry in self.entryList:
						if entry[0] == self.current[0]:
							self.entryList[count] = (
									entry[0],  # Id
									entry[1],  # Thumbnail url
									entry[2],  # Thumbnail
									entry[3],  # Title
									entry[4],  # Views
									entry[5],  # Duration
									videoUrl,  # Video url
									entry[7],  # Description
									entry[8],  # Likes
									entry[9],  # Dislikes
									entry[10],  # Big thumbnail url
									entry[11],  # Channel Id
									entry[12])  # Published
							self.current = self.entryList[count]
							break
						count += 1
			if videoUrl:
				if self.action == 'playVideo':
					service = eServiceReference(int(config.plugins.YouTube.player.value), 0, videoUrl)
					service.setName(self.current[3])
					print("[YouTube] Play:", videoUrl)
					self.session.openWithCallback(self.playCallback,
						YouTubePlayer, service=service, current=self.current)
				else:
					self.videoDownload(videoUrl, self.current[3])
					self.setEntryList()
					self.setPreviousList()
			else:
				self.setEntryList()
				self.setPreviousList()
			self.current = None
			self.text = ''
			self.pageToken = ''
		else:
			entryList = self.createEntryList()
			self.pageToken = ''
			if not entryList:
				self.session.open(MessageBox,
					_('There was an error in creating entry list!\nMaybe try other feeds...'),
					MessageBox.TYPE_INFO, timeout=8)
				self.setEntryList()
				self.setPreviousList()
				self.prevEntryList.pop()
			else:
				self.entryList = entryList
				self.setEntryList(self.text)

	def setEntryList(self, title=None):
		if title:
			self.setTitle(title)
		self['list'].setList(self.entryList)
		self['red'].show()
		self['green'].show()
		self['menu'].show()
		self['key_red'].setText(_('Exit'))
		self['key_green'].setText(_('Open'))
		if self.list == 'videolist':
			self['info'].show()
		self.createThumbnails()

	def createThumbnails(self):
		for entry in self.entryList:
			if entry[2]:  # If thumbnail created
				continue
			entryId = entry[0]
			if entryId in self.thumbnails:
				self.updateThumbnails()
			else:
				url = entry[1]
				if not url:
					image = resolveFilename(SCOPE_PLUGINS,
						'Extensions/YouTube/icons/' + entryId + '.png')
					self.decodeThumbnail(entryId, image)
				else:
					image = os.path.join('/tmp/', str(entryId) + '.jpg')
					downloadPage(url.encode(), image)\
						.addCallback(boundFunction(self.downloadFinished, entryId))\
						.addErrback(boundFunction(self.downloadFailed, entryId))

	def downloadFinished(self, entryId, result):
		image = os.path.join('/tmp/', str(entryId) + '.jpg')
		self.decodeThumbnail(entryId, image)

	def downloadFailed(self, entryId, result):
		print("[YouTube] Thumbnail download failed, use default for", entryId)
		self.decodeThumbnail(entryId)

	def decodeThumbnail(self, entryId, image=None):
		if not image or not os.path.exists(image):
			print("[YouTube] Thumbnail not exists, use default for", entryId)
			self.thumbnails[entryId] = True
			self.updateThumbnails()
		else:
			self.picloads[entryId] = ePicLoad()
			self.picloads[entryId].PictureData.get()\
				.append(boundFunction(self.FinishDecode, entryId, image))
			self.picloads[entryId].setPara((
				self.thumbSize[0], self.thumbSize[1],
				self.sc[0], self.sc[1], False, 1, '#00000000'))
			self.picloads[entryId].startDecode(image)

	def FinishDecode(self, entryId, image, picInfo=None):
		ptr = self.picloads[entryId].getData()
		if ptr:
			self.thumbnails[entryId] = ptr
			self.updateThumbnails()
			if image[:4] == '/tmp':
				os.remove(image)
			self.delPicloadTimer = eTimer()
			self.delPicloadTimer.callback.append(boundFunction(self.delPicload, entryId))
			self.delPicloadTimer.start(1, True)

	def updateThumbnails(self):
		count = 0
		for entry in self.entryList:
			if not entry[2] and entry[0] in self.thumbnails:
				thumbnail = self.thumbnails[entry[0]]
				if thumbnail is True:
					thumbnail = self.thumbnails['default']
				self.entryList[count] = (
						entry[0],  # Id
						entry[1],  # Thumbnail url
						thumbnail,  # Thumbnail
						entry[3],  # Title
						entry[4],  # Views
						entry[5],  # Duration
						entry[6],  # Video url
						entry[7],  # Description
						entry[8],  # Likes
						entry[9],  # Dislikes
						entry[10],  # Big thumbnail url
						entry[11],  # Channel Id
						entry[12])  # Published
			count += 1
		self['list'].updateList(self.entryList)

	def delPicload(self, entryId):
		del self.picloads[entryId]

	def selectNext(self):
		if self['list'].index + 1 < len(self.entryList):  # not last enrty in entry list
			self['list'].selectNext()
		else:
			if self.nextPageToken:  # call next serch results if it exist
				self.pageIndex += int(self.searchResult)
				self.setNextEntries()
			else:
				self['list'].setIndex(0)

	def selectPrevious(self):
		if self['list'].index > 0:  # not first enrty in entry list
			self['list'].selectPrevious()
		else:
			if self.prevPageToken:  # call previous serch results if it exist
				self.pageIndex -= int(self.searchResult)
				self.setPrevEntries()
			else:
				self['list'].setIndex(len(self.entryList) - 1)

	def playCallback(self, action=None):
		self.setEntryList()
		self.setPreviousList()
		if action:
			action = action[1]
			if action == 'quit':
				pass
			elif action == 'repeat':
				self.ok()
			elif action == 'ask':
				self.rememberCurList()
				title = _('What do you want to do?')
				list = ((_('Quit'), 'quit'),
						(_('Play next video'), 'playnext'),
						(_('Play previous video'), 'playprev'),
						(_('Play video again'), 'repeat'))
				self.session.openWithCallback(self.playCallback,
					ChoiceBox, title=title, list=list)
			else:
				if action == 'playnext':
					self.selectNext()
				elif action == 'playprev':
					self.selectPrevious()
				self.playTaimer = eTimer()
				self.playTaimer.timeout.callback.append(self.playTaimerStop)
				self.playTaimer.start(1, True)

	def playTaimerStop(self):
		del self.playTaimer
		self.ok()

	def setPreviousList(self):
		lastInex = self.prevIndex[len(self.prevIndex) - 1]
		self['list'].setIndex(lastInex[0])
		self.list = lastInex[1]
		self.nextPageToken = lastInex[3]
		self.prevPageToken = lastInex[4]
		self.setTitle(lastInex[2])
		self.prevIndex.pop()

	def rememberCurList(self):
		title = self.getTitle()
		self.prevIndex.append([self['list'].index,
			self.list, title, self.nextPageToken, self.prevPageToken])

	def ok(self):
		current = self['list'].getCurrent()
		if current and current[0]:
			print("[YouTube] Selected:", current[0])
			self.rememberCurList()
			if self.list == 'videolist':
				self.screenCallback(current, '', 'playVideo')
			else:
				self.prevEntryList.append(self.entryList)
				if current[0] == 'Search':
					self.createSearchList()
				elif current[0] == 'PubFeeds':
					self.createFeedList()
				elif current[0] == 'MyFeeds':
					self.createMyFeedList()
				elif self.list == 'search':
					from .YouTubeSearch import YouTubeSearch
					self.session.openWithCallback(self.searchScreenCallback, YouTubeSearch, current[0])
				elif self.list == 'feeds':
					self.screenCallback(current[0], current[3], 'OpenFeeds')
				elif self.list == 'myfeeds':
					self.screenCallback(current[0], current[3], 'OpenMyFeeds')
				elif self.list == 'playlist':
					self.screenCallback(current[0], current[3], 'OpenPlayList')
				elif self.list == 'channel':
					self.screenCallback(current[0], current[3], 'OpenChannelList')

	def searchScreenCallback(self, searchValue=None):
		if not searchValue:  # cancel in search
			self.cancel()
		else:
			self.searchResult = config.plugins.YouTube.searchResult.value
			self.screenCallback(self['list'].getCurrent()[0][6:], searchValue, 'OpenSearch')

	def getVideoUrl(self):
		try:
			videoUrl = self.ytdl.extract(self.current[0])
		except Exception as e:
			print('[YouTube] Error in extract info:', e)
			return None, '%s\nVideo Id %s' % (e, str(self.current))
		if videoUrl:
			return videoUrl, None
		print('[YouTube] Video url not found')
		return None, 'Video url not found!'

	@staticmethod
	def _convertDate(duration):
		time = ':' + duration.replace('P', '')\
			.replace('W', '-').replace('D', ' ').replace('T', '')\
			.replace('H', ':').replace('M', ':').replace('S', '')
		if 'S' not in duration:
			time += '00'
		elif time[-2] == ':':
			time = time[:-1] + '0' + time[-1]
		if 'M' not in duration:
			time = time[:-2] + '00' + time[-3:]
		elif time[-5] == ':':
			time = time[:-4] + '0' + time[-4:]
		return time[1:]

	@staticmethod
	def _tryList(result, getter):
		for get in [getter]:
			try:
				v = get(result)
			except Exception as e:
				print('[YouTube] Error in try List', e)
			else:
				return v
		return None

	@staticmethod
	def _tryStr(result, getter):
		for get in [getter]:
			try:
				return str(get(result))
			except KeyError:
				print('[YouTube] Key Error in try String')
			except Exception as e:
				print('[YouTube] Error in try String', e)
				try:  # Workaround if image have str() problems (GOS)
					return get(result).encode('utf-8', 'ignore')
				except Exception as e:
					print('[YouTube] Error in try String encode utf-8', e)
		return ''

	def _tryComplStr(self, result, getter, after):
		v = self._tryStr(result, getter)
		if v:
			return v + after
		return ''

	def createBuild(self):
		refreshToken = config.plugins.YouTube.refreshToken.value
		if not self.youtube or (not self.isAuth and refreshToken and
				config.plugins.YouTube.login.value):
			from .YouTubeApi import YouTubeApi
			self.youtube = YouTubeApi(refreshToken)
			if self.youtube.access_token:
				self.isAuth = True
			else:
				self.isAuth = False

	def createEntryList(self):
		self.createBuild()
		order = 'date'
		searchType = 'video'
		q = videoEmbeddable = videoDefinition = videoType = eventType = ''
		videos = []

		if self.action == 'OpenMyFeeds':
			if not self.isAuth:
				return None
			elif self.current == 'my_liked_videos':
				playlist = 'likes'
			elif self.current == 'my_uploads':
				playlist = 'uploads'

			if self.current == 'my_subscriptions':
				self.list = 'playlist'
				searchResponse = self.youtube.subscriptions_list(
						maxResults=self.searchResult,
						pageToken=self.pageToken,
						subscriptOrder=config.plugins.YouTube.subscriptOrder.value)
				self.nextPageToken = searchResponse.get('nextPageToken')
				self.prevPageToken = searchResponse.get('prevPageToken')
				self.setSearchResults(searchResponse.get('pageInfo', {}).get('totalResults', 0))
				for result in searchResponse.get('items', []):
					Id = self._tryList(result, lambda x: x['snippet']['resourceId']['channelId'])
					Id = 'UU' + Id[2:] if Id else None
					videos.append((
						Id,
						self._tryStr(result, lambda x: x['snippet']['thumbnails']['high']['url']),  # Thumbnail url
						None,
						self._tryStr(result, lambda x: x['snippet']['title']),  # Title
						'', '',
						self._tryList(result, lambda x: x['id']),  # Subscription
						None, None, None, None, None, ''))
				if len(videos) > 1:
					videos.insert(0, ('recent_subscr', '', None, _('Recent'), '', '',
						None, None, None, None, None, None, ''))
				return videos

			elif self.current == 'my_playlists':
				self.list = 'playlist'
				searchResponse = self.youtube.playlists_list(
						maxResults=self.searchResult,
						pageToken=self.pageToken)
				self.nextPageToken = searchResponse.get('nextPageToken')
				self.prevPageToken = searchResponse.get('prevPageToken')
				self.setSearchResults(searchResponse.get('pageInfo', {}).get('totalResults', 0))
				for result in searchResponse.get('items', []):
					videos.append((
						self._tryList(result, lambda x: x['id']),  # Id
						self._tryStr(result, lambda x: x['snippet']['thumbnails']['default']['url']),  # Thumbnail url
						None,
						self._tryStr(result, lambda x: x['snippet']['title']),  # Title
						'', '', None, None, None, None, None, None, ''))
				return videos

			else:  # all other my data
				channel = ''
				searchResponse = self.youtube.channels_list(
						maxResults=self.searchResult,
						pageToken=self.pageToken)

				self.nextPageToken = searchResponse.get('nextPageToken')
				self.prevPageToken = searchResponse.get('prevPageToken')
				self.setSearchResults(searchResponse.get('pageInfo', {}).get('totalResults', 0))
				for result in searchResponse.get('items', []):
					try:
						channel = result['contentDetails']['relatedPlaylists'][playlist]
					except Exception as e:
						print('[YouTube] Error get playlist', e)

				videos = self.videoIdFromPlaylist(order, channel)
				return self.extractVideoIdList(videos)

		elif self.action == 'OpenPlayList':
			if self.current == 'recent_subscr':
				for subscription in self.entryList:
					if subscription[0] != 'recent_subscr':
						videos += self.videoIdFromPlaylist('unread', subscription[0])
				if videos:
					videos = sorted(self.extractVideoIdList(videos), key=lambda k: k[12], reverse=True)  # sort by date
					del videos[int(self.searchResult):]  # leaves only searchResult long list
					self.nextPageToken = ''
					self.prevPageToken = ''
					self.setSearchResults(int(self.searchResult))
				return videos
			else:
				videos = self.videoIdFromPlaylist(order, self.current)
				if not videos:  # if channel list from subscription
					searchResponse = self.youtube.search_list(
							order=order,
							part='id,snippet',
							channelId='UC' + self.current[2:],
							maxResults=self.searchResult,
							pageToken=self.pageToken)
					return self.createList(searchResponse, True)
			return self.extractVideoIdList(videos)

		elif self.action == 'OpenChannelList':
			videos = self.videoIdFromChannellist(self.current, order)
			return self.extractVideoIdList(videos)

		else:  # search or pub feeds
			if self.action == 'OpenSearch':
				order = config.plugins.YouTube.searchOrder.value
				if self.current == 'broadcasts':
					eventType = 'live'
				else:
					searchType = self.current
				if '  (' in self.text:
					self.text = self.text.rsplit('  (', 1)[0]
				q = self.text
			elif self.action == 'OpenFeeds':
				if self.current == 'top_rated':
					order = 'rating'
				elif self.current == 'most_viewed':
					order = 'viewCount'
				elif self.current == 'HD_videos':
					videoDefinition = 'high'
				elif self.current == 'embedded_videos':
					videoEmbeddable = 'true'
				elif self.current == 'episodes':
					videoType = 'episode'
				elif self.current == 'movies':
					videoType = 'movie'

			searchResponse = self.youtube.search_list_full(
					videoEmbeddable=videoEmbeddable,
					safeSearch=config.plugins.YouTube.safeSearch.value,
					eventType=eventType,
					videoType=videoType,
					videoDefinition=videoDefinition,
					order=order,
					part='id,snippet',
					q=q,
					relevanceLanguage=config.plugins.YouTube.searchLanguage.value,
					s_type=searchType,
					regionCode=config.plugins.YouTube.searchRegion.value,
					maxResults=self.searchResult,
					pageToken=self.pageToken)

			if searchType != 'video':
				videos = self.createList(searchResponse, False)
				return videos

			self.nextPageToken = searchResponse.get('nextPageToken')
			self.prevPageToken = searchResponse.get('prevPageToken')
			self.setSearchResults(searchResponse.get('pageInfo', {}).get('totalResults', 0))
			for result in searchResponse.get('items', []):
				try:
					videos.append(result['id']['videoId'])
				except Exception as e:
					print('[YouTube] Error get videoId', e)
			return self.extractVideoIdList(videos)

	def extractVideoIdList(self, videos):
		if len(videos) == 0:
			return None
		self.list = 'videolist'

		# No more than 50 of videos at a time for videos list extraction
		limited_videos = []
		vx = 50
		while True:
			limited_videos += self.extractLimitedVideoIdList(videos[vx - 50:vx])
			if len(videos) > vx:
				vx += 50
			else:
				break
		return limited_videos

	def extractLimitedVideoIdList(self, videos):
		searchResponse = self.youtube.videos_list(v_id=','.join(videos))
		videos = []
		for result in searchResponse.get('items', []):
			Duration = self._tryStr(result, lambda x: x['contentDetails']['duration'])
			if Duration:
				Duration = _('Duration: ') + self._convertDate(Duration) if Duration != 'P0D' else _('Live broadcast')
			PublishedAt = self._tryStr(result, lambda x: x['snippet']['publishedAt'])
			PublishedAt = _('Published at: ') + PublishedAt.replace('T', ' ')\
					.replace('Z', '').split('.')[0] if PublishedAt else ''
			videosInfo = (
				self._tryList(result, lambda x: x['id']),  # Id
				self._tryStr(result, lambda x: x['snippet']['thumbnails']['default']['url']),  # Thumbnail url
				None,
				self._tryStr(result, lambda x: x['snippet']['title']),  # Title
				self._tryComplStr(result, lambda x: x['statistics']['viewCount'], _(' views')),  # Views
				Duration,
				None,
				self._tryStr(result, lambda x: x['snippet']['description']),  # Description
				self._tryComplStr(result, lambda x: x['statistics']['likeCount'], _(' likes')),  # Likes
				self._tryComplStr(result, lambda x: x['statistics']['dislikeCount'], _(' dislikes')),  # Dislikes
				self._tryStr(result, lambda x: x['snippet']['thumbnails']['medium']['url']),  # Big thumbnail url
				self._tryList(result, lambda x: x['snippet']['channelId']),  # Channel id
				PublishedAt)

			if self._tryList(result, lambda x: x['snippet']['liveBroadcastContent']) == 'live':
				videos.insert(0, videosInfo)  # if live broadcast insert in top of list
			else:
				videos.append(videosInfo)
		return videos

	def videoIdFromPlaylist(self, order, channel):
		videos = []
		searchResponse = self.youtube.playlistItems_list(
				order=order,
				maxResults=self.searchResult,
				playlistId=channel,
				pageToken=self.pageToken)
		self.nextPageToken = searchResponse.get('nextPageToken')
		self.prevPageToken = searchResponse.get('prevPageToken')
		self.setSearchResults(searchResponse.get('pageInfo', {}).get('totalResults', 0))
		for result in searchResponse.get('items', []):
			try:
				videos.append(result['snippet']['resourceId']['videoId'])
			except Exception as e:
				print('[YouTube] Error get videoId from Playlist', e)
		return videos

	def videoIdFromChannellist(self, channel, order):
		videos = []
		searchResponse = self.youtube.search_list(
				order=order,
				part='id',
				channelId=channel,
				maxResults=self.searchResult,
				pageToken=self.pageToken)
		self.nextPageToken = searchResponse.get('nextPageToken')
		self.prevPageToken = searchResponse.get('prevPageToken')
		self.setSearchResults(searchResponse.get('pageInfo', {}).get('totalResults', 0))
		for result in searchResponse.get('items', []):
			try:
				videos.append(result['id']['videoId'])
			except Exception as e:
				print('[YouTube] Error get videoId from Channellist', e)
		return videos

	def createList(self, searchResponse, subscription):
		videos = []
		self.nextPageToken = searchResponse.get('nextPageToken')
		self.prevPageToken = searchResponse.get('prevPageToken')
		self.setSearchResults(searchResponse.get('pageInfo', {}).get('totalResults', 0))
		kind = self.list
		for result in searchResponse.get('items', []):
			try:
				kind = result['id']['kind'].split('#')[1]
			except Exception:
				kind = self.list
			videos.append((
				self._tryList(result, lambda x: x['id'][kind + 'Id']),  # Id
				self._tryStr(result, lambda x: x['snippet']['thumbnails']['default']['url']),  # Thumbnail url
				None,
				self._tryStr(result, lambda x: x['snippet']['title']),  # Title
				'', '', None, None, None, None, None, None, ''))
		if subscription and len(videos) > 1:
			videos.insert(0, ('recent_subscr', None, None, _('Recent'), '', '',
				None, None, None, None, None, None, ''))
		self.list = kind
		return videos

	def setSearchResults(self, totalResults):
		if not self.prevPageToken:
			self.pageIndex = 1
		if totalResults > 0:
			page_end = self.pageIndex + int(self.searchResult) - 1
			if page_end > totalResults:
				page_end = totalResults
			if '  (' in self.text:
				self.text = self.text.rsplit('  (', 1)[0]
			self.text = self.text[:40] + _('  (%d-%d of %d)') % \
				(self.pageIndex, page_end, totalResults)

	def cancel(self):
		entryListIndex = len(self.prevEntryList) - 1
		if len(self.prevIndex) == 0 or entryListIndex < 0:
			self.close()
		elif len(self.prevIndex) == 1:
			# Authentication can be changes in setup in another list,
			# therefore always create a new main list
			self.prevEntryList = []
			self.createMainList()
			self.setPreviousList()
		else:
			self.entryList = self.prevEntryList[entryListIndex]
			self.prevEntryList.pop()
			self.setEntryList()
			self.setPreviousList()
			self['info'].hide()

	def openMenu(self):
		if self.list == 'main':
			self.session.openWithCallback(self.configScreenCallback, YouTubeSetup)
		else:
			title = _('What do you want to do?')
			clist = ((_('YouTube setup'), 'setup'),)
			if self.nextPageToken:
				clist += ((ngettext('Next %s entry', 'Next %s entries',
					int(self.searchResult)) % self.searchResult, 'next'),)
			if self.prevPageToken:
				clist += ((ngettext('Previous %s entry', 'Previous %s entries',
					int(self.searchResult)) % self.searchResult, 'prev'),)
			if self.isAuth:
				if self.list == 'videolist':
					clist += ((_('Rate video'), 'rate'),
							(_('Subscribe this video channel'), 'subscribe_video'),)
				elif self.list == 'channel' and self.prevIndex[1][1] != 'myfeeds':
					clist += ((_('Subscribe'), 'subscribe'),)
				elif self.list == 'playlist' and self.prevIndex[1][1] == 'myfeeds' and \
					len(self.prevIndex) == 2:
					clist += ((_('Unsubscribe'), 'unsubscribe'),)
			if self.list == 'videolist':
				clist += ((_('Search'), 'search'),
					(_('Download video'), 'download'),)
			if self.activeDownloads > 0:
				clist += ((_('Active video downloads'), 'download_list'),)
			clist += ((_('Close YouTube'), 'close'),)
			self.session.openWithCallback(self.menuCallback,
				ChoiceBox, title=title, list=clist, keys=['menu'])

	def menuCallback(self, answer):
		if answer:
			msg = None
			clist = None
			if answer[1] == 'setup':
				self.session.openWithCallback(self.configScreenCallback, YouTubeSetup)
			elif answer[1] == 'next':
				self.setNextEntries()
			elif answer[1] == 'prev':
				self.setPrevEntries()
			elif answer[1] == 'rate':
				clist = ((_('I like this'), 'like'),
						(_('I dislike this'), 'dislike'),
						(_('Remove my rating'), 'none'),)
			elif answer[1] == 'subscribe':
				current = self['list'].getCurrent()[0]
				msg = self.subscribeChannel(current)
			elif answer[1] == 'subscribe_video':
				current = self['list'].getCurrent()[11]
				msg = self.subscribeChannel(current)
			elif answer[1] == 'unsubscribe':
				msg = self.unsubscribeChannel()
			elif answer[1] == 'search':
				clist = ((_('Search for similar'), 'similar'),
						(_('Videos from this video channel'), 'channel_videos'),)
			elif answer[1] == 'similar':
				term = self['list'].getCurrent()[3][:40]
				self.screenCallback('video', term, 'OpenSearch')
			elif answer[1] == 'channel_videos':
				current = self['list'].getCurrent()
				self.screenCallback(current[11], current[3][:40],
						'OpenChannelList')
			elif answer[1] == 'download':
				current = self['list'].getCurrent()
				if current[6]:
					self.videoDownload(current[6], current[3])
				else:
					self.rememberCurList()
					self.screenCallback(current, '', 'downloadVideo')
			elif answer[1] == 'download_list':
				from .YouTubeDownload import YouTubeDownloadList
				self.session.open(YouTubeDownloadList)
			elif answer[1] == 'close':
				self.close()
			else:
				msg = self.rateVideo(answer[1])
			if msg:
				self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=3)
			elif clist:
				title = _('What do you want to do?')
				self.session.openWithCallback(self.menuCallback,
						ChoiceBox, title=title, list=clist)

	def configScreenCallback(self, callback=None):
		self.searchResult = config.plugins.YouTube.searchResult.value
		if self.isAuth != config.plugins.YouTube.login.value:
			self.isAuth = False
			self.createBuild()
			if self.list == 'main':
				self.createMainList()

	def subscribeChannel(self, channelId):
		if self.youtube.subscriptions_insert(channelId=channelId):
			return _('Subscribed!')
		return _('There was an error!')

	def unsubscribeChannel(self):
		subscribtionId = self['list'].getCurrent()[6]
		if subscribtionId and self.youtube.subscriptions_delete(subscribtionId):
			# update subscriptions list
			newEntryList = []
			for entry in self.entryList:
				if entry[6] != subscribtionId:
					newEntryList.append(entry)
			self.entryList = newEntryList
			self['list'].updateList(self.entryList)
			return _('Unsubscribed!')
		return _('There was an error!')

	def rateVideo(self, rating):
		videoId = self['list'].getCurrent()[0]
		if self.youtube.videos_rate(videoId=videoId, rating=rating):
			text = {'like': _('Liked!'),
				'dislike': _('Disliked!'),
				'none': _('Rating removed!')}
			return text[rating]
		else:
			return _('There was an error!')

	def showEventInfo(self):
		if self.list == 'videolist':
			current = self['list'].getCurrent()
			self.session.open(YouTubeInfo, current=current)

	def videoDownload(self, url, title):
		downloadDir = config.plugins.YouTube.downloadDir.value
		if downloadDir[0] == "'":
			downloadDir = downloadDir[2:-2]
		if not os.path.exists(downloadDir):
			msg = _('Sorry, download directory not exist!\nPlease specify in the settings existing directory.')
		else:
			outputfile = os.path.join(downloadDir, title.replace('/', '') + '.mp4')
			if os.path.exists(outputfile) or \
				os.path.exists('%s.m4a' % outputfile[:-4]) or \
				os.path.exists('%s_suburi.mp4' % outputfile[:-4]) or \
				os.path.exists('%s.mkv' % outputfile[:-4]):
				msg = _('Sorry, this file already exists:\n%s') % title
			else:
				from .YouTubeDownload import downloadJob
				if '&suburi=' in url:  # download DASH MP4 video and audio
					url = url.split('&suburi=', 1)
					job_manager.AddJob(downloadJob(url[1], '%s.m4a' % outputfile[:-4],
						'%s audio' % title[:20], self.downloadStop))
					self.activeDownloads += 1
					url = url[0]
					outputfile = outputfile[:-4] + '_suburi.mp4'
				job_manager.AddJob(downloadJob(url, outputfile, title[:20], self.downloadStop))
				self.activeDownloads += 1
				msg = _('Video download started!')
		self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=5)

	def downloadStop(self):
		if hasattr(self, 'activeDownloads'):
			self.activeDownloads -= 1

	def setPrevEntries(self):
		self.pageToken = self.prevPageToken
		self.usePageToken()

	def setNextEntries(self):
		self.pageToken = self.nextPageToken
		self.usePageToken()

	def usePageToken(self):
		title = self.getTitle()
		self.cancel()
		if self.list == 'search':
			self.rememberCurList()
			self.prevEntryList.append(self.entryList)
			self.screenCallback(self['list'].getCurrent()[0][6:],
					title, 'OpenSearch')
		else:
			self.ok()


class YouTubeInfo(Screen):
	screenWidth = getDesktop(0).size().width()
	if screenWidth and screenWidth == 1280:
		skin = """<screen position="center,center" size="730,424">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_HD.png" \
					position="15,0" size="100,40" transparent="1" alphatest="on" />
				<widget name="title" position="115,0" size="600,60" halign="center" font="Regular;24" />
				<widget name="pic" position="20,70" size="320,180" transparent="1" alphatest="on" />
				<widget name="description" position="360,70" size="360,300" font="Regular;16" />
				<widget name="views" position="30,270" size="150,20" font="Regular;16" />
				<widget name="duration" position="200,270" size="150,20" font="Regular;16" />
				<widget name="likes" position="30,300" size="150,20" font="Regular;16" />
				<widget name="dislikes" position="200,300" size="150,20" font="Regular;16" />
				<widget name="published" position="30,330" size="300,20" font="Regular;16" />
				<ePixmap position="295,377" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="center,382" zPosition="2" size="140,30" \
					valign="295" halign="center" font="Regular;22" transparent="1" />
			</screen>"""
	elif screenWidth and screenWidth == 1920:
		skin = """<screen position="center,center" size="1095,636">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_FHD.png" \
					position="15,0" size="150,60" transparent="1" alphatest="on" />
				<widget name="title" position="172,0" size="900,90" halign="center" font="Regular;36" />
				<widget name="pic" position="30,105" size="320,180" transparent="1" alphatest="on" />
				<widget name="description" position="380,105" size="670,453" font="Regular;24" />
				<widget name="views" position="45,305" size="225,30" font="Regular;24" />
				<widget name="duration" position="45,355" size="225,30" font="Regular;24" />
				<widget name="likes" position="45,405" size="225,30" font="Regular;24" />
				<widget name="dislikes" position="45,455" size="225,30" font="Regular;24" />
				<widget name="published" position="45,505" size="335,30" font="Regular;24" />
				<ePixmap position="442,565" size="210,60" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="442,563" zPosition="2" size="210,60" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
			</screen>"""
	else:
		skin = """<screen position="center,center" size="630,370">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_HD.png" \
					position="15,0" size="100,40" transparent="1" alphatest="on" />
				<widget name="title" position="115,0" size="500,60" halign="center" font="Regular;24" />
				<widget name="pic" position="20,70" size="320,180" transparent="1" alphatest="on" />
				<widget name="description" position="360,70" size="260,225" font="Regular;16" />
				<widget name="views" position="30,270" size="150,20" font="Regular;16" />
				<widget name="duration" position="200,270" size="150,20" font="Regular;16" />
				<widget name="likes" position="30,300" size="150,20" font="Regular;16" />
				<widget name="dislikes" position="200,300" size="150,20" font="Regular;16" />
				<widget name="published" position="360,300" size="260,20" font="Regular;16" />
				<ePixmap position="245,323" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="245,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
			</screen>"""

	def __init__(self, session, current):
		Screen.__init__(self, session)
		self.setTitle(_('Info'))
		self['key_red'] = StaticText(_('Exit'))
		self['title'] = Label(current[3])
		self['pic'] = Pixmap()
		self['description'] = ScrollLabel(current[7])
		self['views'] = Label(current[4])
		self['duration'] = Label(current[5])
		self['likes'] = Label(current[8])
		self['dislikes'] = Label(current[9])
		self['published'] = Label(current[12])
		self['actions'] = ActionMap(['ColorActions',
			'InfobarShowHideActions', 'DirectionActions'], {
				'red': self.close,
				'toggleShow': self.close,
				'hide': self.close,
				'infoButton': self.close,
				'up': self['description'].pageUp,
				'down': self['description'].pageDown}, -2)
		self.picloads = None
		self.ThumbnailUrl = current[10]
		self.onLayoutFinish.append(self.LayoutFinish)

	def LayoutFinish(self):
		if self.ThumbnailUrl:
			downloadPage(self.ThumbnailUrl.encode(), '/tmp/hqdefault.jpg')\
				.addCallback(self.downloadFinished)

	def downloadFinished(self, result):
		image = '/tmp/hqdefault.jpg'
		if os.path.exists(image):
			sc = AVSwitch().getFramebufferScale()
			self.picloads = ePicLoad()
			self.picloads.PictureData.get().append(self.FinishDecode)
			self.picloads.setPara((
				self['pic'].instance.size().width(),
				self['pic'].instance.size().height(),
				sc[0], sc[1], False, 1, '#00000000'))
			self.picloads.startDecode(image)

	def FinishDecode(self, picInfo=None):
		ptr = self.picloads.getData()
		if ptr:
			self["pic"].instance.setPixmap(ptr.__deref__())
			del self.picloads
			os.remove('/tmp/hqdefault.jpg')


class YouTubeSetup(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.skinName = ['YouTubeSetup', 'Setup']
		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('OK'))
		self['description'] = Label('')
		self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'], {
				'cancel': self.cancel,
				'red': self.cancel,
				'ok': self.ok,
				'green': self.ok}, -2)
		self.mbox = None
		self.login = config.plugins.YouTube.login.value
		self.mergeFiles = config.plugins.YouTube.mergeFiles.value
		ConfigListScreen.__init__(self, [], session=session)
		self.setConfigList()
		config.plugins.YouTube.login.addNotifier(self.checkLoginSatus,
				initial_call=False)
		config.plugins.YouTube.useDashMP4.addNotifier(self.setConfigList,
				initial_call=False)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		title = _('YouTube setup')
		self.setTitle(title)

	def checkLoginSatus(self, configElement):
		if 'config' in self and self.login is not None:
			self.setConfigList()
			if self.login != config.plugins.YouTube.login.value:
				self.login = config.plugins.YouTube.login.value
				if self.login:
					if config.plugins.YouTube.refreshToken.value != '':
						self.session.openWithCallback(self.startupCallback,
								MessageBox, _('You already authorized access for this plugin to your YouTube account.\nDo you want to do it again to update access data?'))
					else:
						self.startupCallback(True)

	def setConfigList(self, configElement=None):
		if 'config' not in self:
			return
		self.list = []
		self.list.append(getConfigListEntry(_('Login on startup:'),
			config.plugins.YouTube.login,
			_('Log in to your YouTube account when plugin starts.\nThis needs to approve in the Google home page!')))
		self.list.append(getConfigListEntry(_('Save search result:'),
			config.plugins.YouTube.saveHistory,
			_('Save your search result in the history, when search completed.')))
		self.list.append(getConfigListEntry(_('Search results:'),
			config.plugins.YouTube.searchResult,
			_('How many search results will be returned.\nIf greater value then longer time will be needed for thumbnail download.')))
		self.list.append(getConfigListEntry(_('Search region:'),
			config.plugins.YouTube.searchRegion,
			_('Return search results for the specified country.')))
		self.list.append(getConfigListEntry(_('Search language:'),
			config.plugins.YouTube.searchLanguage,
			_('Return search results that are most relevant to the specified language.')))
		self.list.append(getConfigListEntry(_('Sort search results by:'),
			config.plugins.YouTube.searchOrder,
			_('Order in which search results will be displayed.')))
		if config.plugins.YouTube.login.value:
			self.list.append(getConfigListEntry(_('Sort subscriptions:'),
				config.plugins.YouTube.subscriptOrder,
				_('Order in which subscriptions results will be displayed.')))
		self.list.append(getConfigListEntry(_('Exclude restricted content:'),
			config.plugins.YouTube.safeSearch,
			_('Try to exclude all restricted content from the search result.')))
		self.list.append(getConfigListEntry(_('Maximum video resolution:'),
		config.plugins.YouTube.maxResolution,
			_('What maximum resolution used when playing video, if available.\nIf you have a slow Internet connection, you can use a lower resolution.')))
		self.list.append(getConfigListEntry(_('When video ends:'),
			config.plugins.YouTube.onMovieEof,
			_('What to do when the video ends.')))
		self.list.append(getConfigListEntry(_('When playback stop:'),
			config.plugins.YouTube.onMovieStop,
			_('What to do when stop playback in videoplayer.')))
		self.list.append(getConfigListEntry(_('Download directory:'),
			config.plugins.YouTube.downloadDir,
			_('Specify the directory where save downloaded video files.')))
		self.list.append(getConfigListEntry(_('Use DASH MP4 format:'),
			config.plugins.YouTube.useDashMP4,
			_('Specify or you want to use DASH MP4 format streams if available.\nThis requires playing two streams together and may cause problems for some receivers.')))
		if config.plugins.YouTube.useDashMP4.value:
			self.list.append(getConfigListEntry(_('Merge downloaded files:'),
				config.plugins.YouTube.mergeFiles,
				_('FFmpeg will be used to merge downloaded DASH video and audio files.\nFFmpeg will be installed if necessary.')))
		for p in plugins.getPlugins(where=PluginDescriptor.WHERE_MENU):
			# TRANSLATORS: Don't translate this! It is used as a variable, so it must be equal to the translation in the plugin!
			if p.name == _("ServiceApp"):
				self.list.append(getConfigListEntry(_('Media player:'),
					config.plugins.YouTube.player,
					_('Specify the player which will be used for YouTube media playback.')))
				break
		self['config'].setList(self.list)

	def cancel(self):
		self.login = None
		self.keyCancel()

	def ok(self):
		if self['config'].getCurrent()[1] == config.plugins.YouTube.downloadDir:
			from .YouTubeDownload import YouTubeDirBrowser
			downloadDir = config.plugins.YouTube.downloadDir.value
			if downloadDir[0] == "'":
				downloadDir = downloadDir[2:-2]
			self.session.openWithCallback(self.downloadPath,
				YouTubeDirBrowser, downloadDir)
		elif self.mergeFiles != config.plugins.YouTube.mergeFiles.value:
			if self.mergeFiles:
				self.session.openWithCallback(self.removeCallback,
					MessageBox, _('You have disabled downloaded file merge.\nInstalled FFmpeg is no longer necessary.\nDo you want to remove FFmpeg?'))
			else:
				self.session.openWithCallback(self.installCallback,
					MessageBox, _('To merge downloaded files FFmpeg will be installed.\nFFmpeg can take a lot of space!\nDo you want to continue?'))
		else:
			self.keySave()

	def removeCallback(self, answer):
		if answer:
			from Screens.Console import Console
			self.session.open(Console, cmdlist=['opkg remove --autoremove ffmpeg'])
		self.keySave()

	def installCallback(self, answer):
		if answer:
			from Screens.Console import Console
			self.session.open(Console, cmdlist=['opkg update && opkg install ffmpeg'])
			self.keySave()
		else:
			config.plugins.YouTube.mergeFiles.value = False

	def downloadPath(self, res):
		self['config'].setCurrentIndex(0)
		if res:
			config.plugins.YouTube.downloadDir.value = res

	def startupCallback(self, answer):
		if answer:
			self.session.openWithCallback(self.warningCallback,
				MessageBox, _('To perform authentication will need in a web browser open Google home page, and enter the code!\nDo you currently have Internet access on the other device and we can continue?'))

	def warningCallback(self, answer):
		if not answer:
			self.login = config.plugins.YouTube.login.value = False
		else:
			from .OAuth import OAuth
			self.splitTaimer = eTimer()
			self.splitTaimer.timeout.callback.append(self.splitTaimerStop)
			self.oauth = OAuth()
			url, userCode = self.oauth.get_user_code()
			if userCode:
				msg = _('Go to %s\nAnd enter the code %s') % (url, userCode)
				print("[YouTube] ", msg)
				self.mbox = self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)
				self.splitTaimer.start(9000, True)
			else:
				print("[YouTube] Error in OAuth!")
				self.session.open(MessageBox, 'There was an error!', MessageBox.TYPE_INFO, timeout=5)

	def splitTaimerStop(self):
		# Here we waiting until the user enter a code
		refreshToken, retryInterval = self.oauth.get_new_token()
		if not refreshToken:
			self.splitTaimer.start(retryInterval * 1000, True)
		else:
			print("[YouTube] Get refresh token")
			if self.mbox:
				self.mbox.close()
			config.plugins.YouTube.refreshToken.value = refreshToken
			config.plugins.YouTube.refreshToken.save()
			del self.splitTaimer
			self.mbox = None
			self.oauth = None
