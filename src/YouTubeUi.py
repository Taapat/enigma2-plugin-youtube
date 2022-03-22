from __future__ import print_function

import os
from copy import copy
from locale import LC_CTYPE, Error, getlocale, setlocale

from enigma import eServiceReference, eTimer, iPlayableService
from Components.ActionMap import ActionMap
from Components.config import config, ConfigDirectory, ConfigSelection, \
	ConfigSet, ConfigSubDict, ConfigSubsection, ConfigText, ConfigYesNo, \
	getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Converter.TemplatedMultiContent import TemplatedMultiContent
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
from Tools.LoadPixmap import LoadPixmap

from .compat import compat_urlretrieve

from . import _, screenwidth
from . import ngettext


try:
	from Tools.CountryCodes import ISO3166
except ImportError:
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
config.plugins.YouTube.onMovieEof = ConfigSelection(default='related', choices=[
	('related', _('Show related videos')),
	('quit', _('Return to list')), ('ask', _('Ask user')),
	('playnext', _('Play next')), ('repeat', _('Repeat')),
	('playprev', _('Play previous'))])
config.plugins.YouTube.onMovieStop = ConfigSelection(default='related', choices=[
	('related', _('Show related videos')),
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


FLAGS = ', flags=BT_SCALE'
try:
	TemplatedMultiContent('{"template": \
					[MultiContentEntryPixmapAlphaTest(flags=BT_SCALE)], \
			"fonts": [gFont("Regular",20)], \
			"itemHeight": 72}')
except (NameError, TypeError):
	# If MultiContent not support flags (BH, VTI)
	FLAGS = ''


class YouTubePlayer(MoviePlayer):
	def __init__(self, session, service, current):
		MoviePlayer.__init__(self, session, service)
		self.skinName = ['YouTubeMoviePlayer', 'MoviePlayer']
		self.current = current
		ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evStart: self.__serviceStart,
				iPlayableService.evVideoSizeChanged: self.__serviceStart})  # On exteplayer evStart not working
		self.servicelist = InfoBar.instance and InfoBar.instance.servicelist
		self.started = False
		self.lastPosition = []

	def __serviceStart(self):  # pragma: no cover
		if not self.started:
			self.started = True
			try:
				self.lastPosition = eval(config.plugins.YouTube.lastPosition.value)
			except SyntaxError:
				print('[YouTubePlayer] wrong last position config settings!')
				config.plugins.YouTube.lastPosition.value = '[]'
				config.plugins.YouTube.lastPosition.save()
				self.lastPosition = []

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
			if seek:  # pragma: no cover
				seek.seekTo(self.seekPosition)

	def leavePlayer(self):
		on_movie_stop = config.plugins.YouTube.onMovieStop.value
		if on_movie_stop == 'ask':
			title = _('Stop playing this movie?')
			clist = ((_('Yes, and return to list'), 'quit'),
					(_('Yes, and show related videos'), 'related'),
					(_('Yes, but play next video'), 'playnext'),
					(_('Yes, but play previous video'), 'playprev'),
					(_('No, but play video again'), 'repeat'),
					(_('No'), 'continue'))
			self.session.openWithCallback(self.leavePlayerConfirmed,
				ChoiceBox, title=title, list=clist)
		else:
			self.leavePlayerConfirmed([None, on_movie_stop])

	def leavePlayerConfirmed(self, answer):
		if answer and answer[1] != 'continue':
			service = self.session.nav.getCurrentService()
			seek = service and service.seek()
			if seek:  # pragma: no cover
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
		plist = []
		for p in plugins.getPlugins(where=PluginDescriptor.WHERE_EXTENSIONSMENU):
			if p.name != _('YouTube'):  # pragma: no cover
				plist.append(((boundFunction(self.getPluginName, p.name),
					boundFunction(self.runPlugin, p), lambda: True), None))
		return plist

	def openCurEventView(self):
		self.session.open(YouTubeInfo, current=self.current)

	def showSecondInfoBar(self):
		self.hide()
		self.hideTimer.stop()
		self.openCurEventView()

	def showMovies(self):
		pass  # Ignore this method

	def openServiceList(self):  # pragma: no cover
		if hasattr(self, 'toggleShow'):
			self.toggleShow()


class YouTubeMain(Screen):
	if screenwidth == 'svg':
		skin = """<screen position="center,center" size="730*f,524*f">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube.svg" \
					position="15*f,0" zPosition="2" size="100*f,40*f" alphatest="blend" />
				<widget source="list" render="Listbox" position="15*f,42*f" size="700*f,432*f" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryPixmapAlphaBlend(pos=(0,0), \
								size=(100*f,72*f), flags=BT_SCALE, png=2), # Thumbnail
							MultiContentEntryText(pos=(110*f,1), size=(575*f,52*f), \
								font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_WRAP, text=3), # Title
							MultiContentEntryText(pos=(120*f, 50*f), size=(200*f,22*f), \
								font=1, flags=RT_HALIGN_LEFT, text=4), # Views
							MultiContentEntryText(pos=(360*f,50*f), size=(200*f,22*f), \
								font=1, flags=RT_HALIGN_LEFT, text=5), # Duration
							],
						"fonts": [gFont("Regular",20*f), gFont("Regular",16*f)],
						"itemHeight": 72*f}
					</convert>
				</widget>
				<widget name="info" position="50*f,489*f" size="35*f,25*f" pixmap="skin_default/buttons/key_info.svg" \
					transparent="1" alphatest="blend" />
				<widget name="red" position="215*f,477*f" size="140*f,40*f" pixmap="skin_default/buttons/red.svg" \
					transparent="1" alphatest="blend" />
				<widget name="green" position="375*f,477*f" size="140*f,40*f" pixmap="skin_default/buttons/green.svg" \
					transparent="1" alphatest="blend" />
				<widget source="key_red" render="Label" position="215*f,482*f" zPosition="2" size="140*f,30*f" \
					valign="center" halign="center" font="Regular;22*f" transparent="1" />
				<widget source="key_green" render="Label" position="375*f,482*f" zPosition="2" size="140*f,30*f" \
					valign="center" halign="center" font="Regular;22*f" transparent="1" />
				<widget name="menu" position="645*f,489*f" size="35*f,25*f" pixmap="skin_default/buttons/key_menu.svg" \
					transparent="1" alphatest="blend" />
				<widget name="thumbnail" position="0,0" size="100*f,72*f" /> # Thumbnail size in list
			</screen>"""
	elif screenwidth == 1280:
		skin = """<screen position="center,center" size="730,524">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_HD.png" \
					position="15,0" zPosition="2" size="100,40" alphatest="on" />
				<widget source="list" render="Listbox" position="15,42" size="700,432" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryPixmapAlphaTest(pos=(0,0), \
								size=(100,72), png=2 %s), # Thumbnail
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
			</screen>""" % FLAGS
	elif screenwidth == 1920:
		skin = """<screen position="center,center" size="1095,786">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_FHD.png" \
					position="22,0" zPosition="2" size="150,60" transparent="1" alphatest="on" />
				<widget source="list" render="Listbox" position="22,63" size="1050,648" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryPixmapAlphaTest(pos=(0,0), \
								size=(150,108), png=2 %s), # Thumbnail
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
			</screen>""" % (FLAGS, BUTTONS_FOLDER, BUTTONS_FOLDER)
	else:
		skin = """<screen position="center,center" size="630,380">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_HD.png" \
					position="15,0" zPosition="2" size="100,40" transparent="1" alphatest="on" />
				<widget source="list" render="Listbox" position="15,42" size="600,288" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryPixmapAlphaTest(pos=(0,0), \
								size=(100,72), png=2 %s), # Thumbnail
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
			</screen>""" % FLAGS

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
		self.title = _('YouTube starting. Please wait...')
		self['text'] = Label()  # For backward compatibility, removed after YouTube logo introduction
		self['text'].text = _('YouTube')  # Please use YouTube logo in skin instead of this
		self['list'] = List([])
		self['thumbnail'] = Pixmap()
		self['thumbnail'].hide()
		self.splitTaimer = eTimer()
		self.splitTaimer.timeout.callback.append(self.splitTaimerStop)
		self.active_downloads = 0
		self.is_auth = False
		self.search_result = config.plugins.YouTube.searchResult.value
		self.thumbnails = {}
		self.use_picload = True
		self.ytapi = None
		self.yts = [{}]
		self.onLayoutFinish.append(self.layoutFinish)
		self.onClose.append(self.cleanVariables)
		self.locale = getlocale(LC_CTYPE)
		if self.locale[0] not in (None, 'en_US'):
			# Workaround to fix ssl error unable to find public key parameters with some (turkish) LC_CTYPE
			try:
				setlocale(LC_CTYPE, locale=('en_US', 'UTF-8'))
			except Error as e:
				print('[YouTube] Error on set locale:', e)
				self.locale = (None, None)
		for p in plugins.getPlugins(where=PluginDescriptor.WHERE_MENU):
			if 'ServiceApp' in p.path:
				break
		else:
			config.plugins.YouTube.player.value = '4097'

	def layoutFinish(self):
		if FLAGS and hasattr(self, 'renderer'):
			for screen_renderer in self.renderer:
				text = str(screen_renderer.source)
				if 'EntryPixmap' in text and 'BT_SCALE' in text.split(
						'EntryPixmap')[1].split('#')[0]:
					self.use_picload = False
					break
		if self.use_picload:
			from Components.AVSwitch import AVSwitch
			self.sc = AVSwitch().getFramebufferScale()
			self.picloads = {}
		self.thumb_size = [self['thumbnail'].instance.size().width(),
				self['thumbnail'].instance.size().height()]
		if screenwidth == 'svg':
			self.thumbnails['default'] = LoadPixmap(
					resolveFilename(SCOPE_PLUGINS,
							'Extensions/YouTube/icons/icon.svg'),
					width=self.thumb_size[0],
					height=self.thumb_size[1])
		else:
			self.decodeThumbnail('default',
					resolveFilename(SCOPE_PLUGINS,
							'Extensions/YouTube/icons/icon.png'))
		# Import after config initialization
		from .YouTubeVideoUrl import YouTubeVideoUrl
		self.ytdl = YouTubeVideoUrl()
		self.createAuth()
		self.createMainList()
		for _ in job_manager.getPendingJobs():  # noqa: F402
			self.active_downloads += 1

	def cleanVariables(self):
		del self.splitTaimer
		self.picloads = None
		self.thumbnails = None
		self.ytapi = None
		self.ytdl = None
		if self.locale[0] not in (None, 'en_US'):
			setlocale(LC_CTYPE, locale=self.locale)

	def showButtons(self):
		self['red'].show()
		self['green'].show()
		self['menu'].show()
		self['key_red'].text = _('Exit')
		self['key_green'].text = _('Open')
		if self.yts[0]['list'] == 'videolist':
			self['info'].show()

	def createDefEntryList(self, entry_list, append=False):
		if not append:
			self.yts[0]['entry_list'] = []
		for ytid, title in entry_list:
			self.yts[0]['entry_list'].append((
					ytid,   # Id
					'',     # Thumbnail url
					None,   # Thumbnail
					title,  # Title
					'',     # Views
					'',     # Duration
					None,   # Video url
					None,   # Description
					None,   # Likes
					'',     # Big thumbnail url
					None,   # Channel Id
					''))    # Published

	def createMainList(self):
		self.yts[0]['list'] = 'main'
		self.yts[0]['title'] = _('Choose what you want to do')
		self.createDefEntryList([['Search', _('Search')],
				['PubFeeds', _('Public feeds')]])
		if self.is_auth:
			self.createDefEntryList([['MyFeeds', _('My feeds')]], True)
		self.showButtons()
		self.setEntryList()

	def createSearchList(self):
		self.yts[0]['list'] = 'search'
		self.yts[0]['title'] = _('Search')
		self.createDefEntryList([['Searchvideo', _('Search videos')],
				['Searchchannel', _('Search channels')],
				['Searchplaylist', _('Search playlists')],
				['Searchbroadcasts', _('Search live broadcasts')]])
		self.setEntryList()

	def createFeedList(self):
		self.yts[0]['list'] = 'feeds'
		self.yts[0]['title'] = _('Public feeds')
		self.createDefEntryList([['top_rated', _('Top rated')],
				['most_viewed', _('Most viewed')],
				['most_recent', _('Recent')],
				['HD_videos', _('HD videos')],
				['embedded_videos', _('Embedded in webpages')],
				['episodes', _('Shows')],
				['movies', _('Movies')]])
		self.setEntryList()

	def createMyFeedList(self):
		self.yts[0]['list'] = 'myfeeds'
		self.yts[0]['title'] = _('My feeds')
		self.createDefEntryList([['my_subscriptions', _('My Subscriptions')],
				['my_liked_videos', _('Liked videos')],
				['my_uploads', _('Uploads')],
				['my_playlists', _('Playlists')]])
		self.setEntryList()

	def screenCallback(self, text, action):
		self.yts[0]['title'] = text
		self.yts[0]['list'] = action
		if action == 'search':
			self.title = _('Download search results. Please wait...')
		elif action in ['playVideo', 'downloadVideo']:
			self.title = _('Extract video url. Please wait...')
		else:
			self.title = _('Download feed entries. Please wait...')
		self['list'].list = []
		self['key_red'].text = ''
		self['key_green'].text = ''
		self['red'].hide()
		self['green'].hide()
		self['menu'].hide()
		self['info'].hide()
		self.splitTaimer.start(0, True)

	def splitTaimerStop(self):
		if self.yts[0]['list'] in ['playVideo', 'downloadVideo']:
			current = self.yts[1]['entry_list'][self.yts[1]['index']]
			video_url = current[6]
			if not video_url:  # remember video url
				video_url, url_error = self.getVideoUrl(current[0])
				if url_error:
					self.session.open(MessageBox,
							_('There was an error in extract video url:\n%s') % url_error,
							MessageBox.TYPE_INFO, timeout=8)
				else:
					self.yts[1]['entry_list'][self.yts[1]['index']] = (
							current[0],  # Id
							current[1],  # Thumbnail url
							current[2],  # Thumbnail
							current[3],  # Title
							current[4],  # Views
							current[5],  # Duration
							video_url,  # Video url
							current[7],  # Description
							current[8],  # Likes
							current[9],  # Big thumbnail url
							current[10],  # Channel Id
							current[11])  # Published
					current = self.yts[1]['entry_list'][self.yts[1]['index']]

			if video_url:
				if self.yts[0]['list'] == 'playVideo':
					service = eServiceReference(int(config.plugins.YouTube.player.value), 0, video_url)
					service.setName(current[3])
					print('[YouTube] Play:', video_url)
					self.session.openWithCallback(self.playCallback,
						YouTubePlayer, service=service, current=current)
				else:
					self.videoDownload(video_url, current[3])
					self.yts.pop(0)
					self.setEntryList()
			else:
				self.yts.pop(0)
				self.setEntryList()
		else:
			entry_list = self.createEntryList()
			self.showButtons()
			if not entry_list:
				self.session.open(MessageBox,
						_('There was an error in creating entry list!\nMaybe try other feeds...'),
						MessageBox.TYPE_INFO, timeout=8)
				self.yts.pop(0)
				self.setEntryList()
			else:
				self.yts[0]['entry_list'] = entry_list
				self.setEntryList()

	def setEntryList(self):
		self.title = self.yts[0].get('title', '')
		self['list'].list = self.yts[0].get('entry_list', [])
		self['list'].index = (self.yts[0].get('index', 0))

		for entry in self.yts[0]['entry_list']:
			if entry[2]:  # If thumbnail created
				continue
			entry_id = entry[0]
			if entry_id in self.thumbnails:
				self.updateThumbnails(entry_id)
			else:
				url = entry[1]
				if not url:
					if screenwidth == 'svg':
						self.thumbnails[entry_id] = LoadPixmap(
								resolveFilename(SCOPE_PLUGINS,
										'Extensions/YouTube/icons/%s.svg' % entry_id),
								width=self.thumb_size[0],
								height=self.thumb_size[1])
						self.updateThumbnails(entry_id)
					else:
						self.decodeThumbnail(entry_id,
								resolveFilename(SCOPE_PLUGINS,
										'Extensions/YouTube/icons/%s.png' % entry_id))
				else:
					try:
						compat_urlretrieve(url, '/tmp/%s.jpg' % str(entry_id))
					except Exception as e:
						print('[YouTube] Thumbnail download error', e)
						self.decodeThumbnail(entry_id)
					else:
						self.decodeThumbnail(entry_id, '/tmp/%s.jpg' % str(entry_id))

	def decodeThumbnail(self, entry_id, image=None):
		if not image or not os.path.exists(image):
			print('[YouTube] Thumbnail not exists, use default for', entry_id)
			self.thumbnails[entry_id] = True
			self.updateThumbnails(entry_id, True)
		elif self.use_picload:
			from enigma import ePicLoad
			self.picloads[entry_id] = ePicLoad()
			self.picloads[entry_id].PictureData.get()\
					.append(boundFunction(self.finishDecode, entry_id, image))
			self.picloads[entry_id].setPara((
				self.thumb_size[0], self.thumb_size[1],
				self.sc[0], self.sc[1], False, 1, '#00000000'))
			self.picloads[entry_id].startDecode(image)
		else:
			self.thumbnails[entry_id] = LoadPixmap(image)
			if image[:4] == '/tmp':
				self.updateThumbnails(entry_id, True)
				os.remove(image)
			else:
				self.updateThumbnails(entry_id)

	def finishDecode(self, entry_id, image, picInfo=None):
		ptr = self.picloads[entry_id].getData()
		if ptr:
			self.thumbnails[entry_id] = ptr
			if image[:4] == '/tmp':
				self.updateThumbnails(entry_id, True)
				os.remove(image)
			else:
				self.updateThumbnails(entry_id)
			self.delPicloadTimer = eTimer()
			self.delPicloadTimer.callback.append(boundFunction(self.delPicload, entry_id))
			self.delPicloadTimer.start(1, True)

	def delPicload(self, entry_id):
		del self.picloads[entry_id]

	def updateThumbnails(self, entry_id, delete=False):
		for idx, entry in enumerate(self.yts[0].get('entry_list', [])):
			if entry[0] == entry_id and entry_id in self.thumbnails:
				thumbnail = self.thumbnails[entry_id]
				if thumbnail is True:
					thumbnail = self.thumbnails['default']
				self.yts[0]['entry_list'][idx] = (
						entry[0],  # Id
						entry[1],  # Thumbnail url
						copy(thumbnail),  # Thumbnail
						entry[3],  # Title
						entry[4],  # Views
						entry[5],  # Duration
						entry[6],  # Video url
						entry[7],  # Description
						entry[8],  # Likes
						entry[9],  # Big thumbnail url
						entry[10],  # Channel Id
						entry[11])  # Published
				if len(self.thumbnails) > 200 and delete:
					del self.thumbnails[entry_id]
				break
		else:
			return
		self['list'].updateList(self.yts[0]['entry_list'])

	def selectNext(self):
		if self['list'].index + 1 < self['list'].count():  # not last enrty in entry list
			self['list'].selectNext()
		else:
			if self.yts[0].get('nextPageToken'):  # call next serch results if it exist
				self.setNextEntries()
			else:
				self['list'].index = 0

	def selectPrevious(self):
		if self['list'].index > 0:  # not first enrty in entry list
			self['list'].selectPrevious()
		else:
			if self.yts[0].get('prevPageToken'):  # call previous serch results if it exist
				self.setPrevEntries()
			else:
				self['list'].index = self['list'].count() - 1

	def playCallback(self, action=None):
		self.yts.pop(0)
		self.setEntryList()
		if action:
			action = action[1]
			if action == 'quit':
				pass
			elif action == 'repeat':
				self.ok()
			elif action == 'ask':
				self.yts.insert(0, {})
				title = _('What do you want to do?')
				clist = ((_('Quit'), 'quit'),
						(_('Play next video'), 'playnext'),
						(_('Play previous video'), 'playprev'),
						(_('Play video again'), 'repeat'))
				self.session.openWithCallback(self.playCallback,
						ChoiceBox, title=title, list=clist)
			elif action == 'related':
				self.yts.pop(0)
				self.yts.insert(0, {})
				self.yts[0]['related'] = str(self['list'].getCurrent()[0])
				self.screenCallback('', 'search')
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

	def ok(self):
		current = self['list'].getCurrent()
		if current and current[0]:
			print('[YouTube] Selected:', current[0])
			self.yts[0]['index'] = self['list'].index
			self.yts.insert(0, {})
			if self.yts[1]['list'] == 'videolist':
				self.screenCallback('', 'playVideo')
			elif current[0] == 'Search':
				self.createSearchList()
			elif current[0] == 'PubFeeds':
				self.createFeedList()
			elif current[0] == 'MyFeeds':
				self.createMyFeedList()
			elif self.yts[1]['list'] == 'search':
				from .YouTubeSearch import YouTubeSearch
				self.session.openWithCallback(self.searchScreenCallback, YouTubeSearch, current[0])
			else:
				self.screenCallback(current[3], self.yts[1]['list'])

	def searchScreenCallback(self, search_value=None):
		if not search_value:  # cancel in search
			self.cancel()
		else:
			self.search_result = config.plugins.YouTube.searchResult.value
			self.screenCallback(search_value, 'search')

	def getVideoUrl(self, video_id):
		try:
			video_url = self.ytdl.extract(video_id)
		except Exception as e:
			print('[YouTube] Error in extract info:', e)
			return None, '%s\nVideo Id %s' % (e, str(video_id))
		if video_url:
			return video_url, None
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

	def createAuth(self):
		refresh_token = config.plugins.YouTube.refreshToken.value
		if not self.ytapi or (not self.is_auth and refresh_token and
				config.plugins.YouTube.login.value):
			from .YouTubeApi import YouTubeApi
			self.ytapi = YouTubeApi(refresh_token)
			if self.ytapi.access_token:
				self.is_auth = True
			else:
				self.is_auth = False

	def createEntryList(self):
		order = 'date'
		searchType = 'video'
		q = videoEmbeddable = videoDefinition = videoType = eventType = ''
		videos = []
		current = self.yts[1]['entry_list'][self.yts[1]['index']][0]

		if self.yts[0]['list'] == 'myfeeds':
			if not self.is_auth:
				return None
			elif current == 'my_liked_videos':
				playlist = 'likes'
			elif current == 'my_uploads':
				playlist = 'uploads'

			if current == 'my_subscriptions':
				self.yts[0]['list'] = 'playlist'
				search_response = self.ytapi.subscriptions_list(
						maxResults=self.search_result,
						pageToken=self.yts[0].get('pageToken', ''),
						subscriptOrder=config.plugins.YouTube.subscriptOrder.value)
				self.yts[0]['nextPageToken'] = search_response.get('nextPageToken', '')
				self.yts[0]['prevPageToken'] = search_response.get('prevPageToken', '')
				self.setSearchResults(search_response.get('pageInfo', {}).get('totalResults', 0))
				for result in search_response.get('items', []):
					Id = self._tryList(result, lambda x: x['snippet']['resourceId']['channelId'])
					Id = 'UU' + Id[2:] if Id else None
					videos.append((Id,
							self._tryStr(result, lambda x: x['snippet']['thumbnails']['high']['url']),  # Thumbnail url
							None,
							self._tryStr(result, lambda x: x['snippet']['title']),  # Title
							'', '',
							self._tryList(result, lambda x: x['id']),  # Subscription
							None, None, None, None, ''))
				if not self.yts[0].get('pageToken') and len(videos) > 1:
					videos.insert(0, ('recent_subscr', '', None, _('Recent'), '', '',
							None, None, None, None, None, ''))
				return videos

			elif current == 'my_playlists':
				self.yts[0]['list'] = 'playlist'
				search_response = self.ytapi.playlists_list(
						maxResults=self.search_result,
						pageToken=self.yts[0].get('pageToken', ''))
				self.yts[0]['nextPageToken'] = search_response.get('nextPageToken', '')
				self.yts[0]['prevPageToken'] = search_response.get('prevPageToken', '')
				self.setSearchResults(search_response.get('pageInfo', {}).get('totalResults', 0))
				for result in search_response.get('items', []):
					videos.append((
						self._tryList(result, lambda x: x['id']),  # Id
						self._tryStr(result, lambda x: x['snippet']['thumbnails']['default']['url']),  # Thumbnail url
						None,
						self._tryStr(result, lambda x: x['snippet']['title']),  # Title
						'', '', None, None, None, None, None, ''))
				return videos

			else:  # all other my data
				channel = ''
				search_response = self.ytapi.channels_list(
						maxResults=self.search_result,
						pageToken=self.yts[0].get('pageToken', ''))

				self.yts[0]['nextPageToken'] = search_response.get('nextPageToken', '')
				self.yts[0]['prevPageToken'] = search_response.get('prevPageToken', '')
				self.setSearchResults(search_response.get('pageInfo', {}).get('totalResults', 0))
				for result in search_response.get('items', []):
					try:
						channel = result['contentDetails']['relatedPlaylists'][playlist]
					except Exception as e:
						print('[YouTube] Error get playlist', e)

				videos = self.videoIdFromPlaylist(order, channel)
				return self.extractVideoIdList(videos)

		elif self.yts[0]['list'] == 'playlist':
			if current == 'recent_subscr':
				for subscription in self.yts[1]['entry_list']:
					if subscription[0] != 'recent_subscr':
						videos += self.videoIdFromPlaylist(order, subscription[0], False)
				if self.yts[0].get('nextPageToken'):
					for subscription in self.getAllSubscriptions():
						videos += self.videoIdFromPlaylist(order, subscription, False)
				if videos:
					videos = sorted(self.extractVideoIdList(videos), key=lambda k: k[11], reverse=True)  # sort by date
					del videos[int(self.search_result):]  # leaves only searchResult long list
					self.yts[0]['nextPageToken'] = ''
					self.setSearchResults(int(self.search_result))
				return videos
			else:
				videos = self.videoIdFromPlaylist(order, current)
				if not videos:  # if channel list from subscription
					search_response = self.ytapi.search_list(
							order=order,
							part='id,snippet',
							channelId='UC' + current[2:],
							maxResults=self.search_result,
							pageToken=self.yts[0].get('pageToken', ''))
					subscription = True if not self.yts[0].get('pageToken') else False
					return self.createList(search_response, subscription)
			return self.extractVideoIdList(videos)

		elif self.yts[0]['list'] == 'channel':
			videos = self.videoIdFromChannellist(current, order)
			return self.extractVideoIdList(videos)

		else:  # search or pub feeds
			related = self.yts[0].get('related', '')
			if related:
				self.yts[0]['title'] = _('Related videos')
			elif self.yts[0]['list'] == 'search':
				order = config.plugins.YouTube.searchOrder.value
				if current[6:] == 'broadcasts':
					eventType = 'live'
				else:
					searchType = current[6:]
				if '  (' in self.yts[0]['title']:
					self.yts[0]['title'] = self.yts[0]['title'].rsplit('  (', 1)[0]
				q = self.yts[0]['title']
			elif self.yts[0]['list'] == 'feeds':
				if current == 'top_rated':
					order = 'rating'
				elif current == 'most_viewed':
					order = 'viewCount'
				elif current == 'HD_videos':
					videoDefinition = 'high'
				elif current == 'embedded_videos':
					videoEmbeddable = 'true'
				elif current == 'episodes':
					videoType = 'episode'
				elif current == 'movies':
					videoType = 'movie'

			search_response = self.ytapi.search_list_full(
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
					relatedToVideoId=related,
					maxResults=self.search_result,
					pageToken=self.yts[0].get('pageToken', ''))

			if searchType != 'video':
				videos = self.createList(search_response, False)
				return videos

			self.yts[0]['nextPageToken'] = search_response.get('nextPageToken', '')
			self.yts[0]['prevPageToken'] = search_response.get('prevPageToken', '')
			self.setSearchResults(search_response.get('pageInfo', {}).get('totalResults', 0))
			for result in search_response.get('items', []):
				try:
					videos.append(result['id']['videoId'])
				except Exception as e:
					print('[YouTube] Error get videoId', e)
			return self.extractVideoIdList(videos)

	def getAllSubscriptions(self):
		subscriptions = []
		_nextPageToken = self.yts[0].get('nextPageToken', '')
		subscriptOrder = config.plugins.YouTube.subscriptOrder.getValue()
		while True:
			search_response = self.ytapi.subscriptions_list(
					maxResults='50',
					pageToken=_nextPageToken,
					subscriptOrder=subscriptOrder)
			for result in search_response.get('items', []):
				Id = self._tryList(result, lambda x: x['snippet']['resourceId']['channelId'])
				if Id:
					subscriptions.append('UU' + Id[2:])
			_nextPageToken = search_response.get('nextPageToken', '')
			if not _nextPageToken:
				break
		return subscriptions

	def extractVideoIdList(self, videos):
		if len(videos) == 0:
			return None
		self.yts[0]['list'] = 'videolist'

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
		search_response = self.ytapi.videos_list(v_id=','.join(videos))
		videos = []
		for result in search_response.get('items', []):
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
				self._tryStr(result, lambda x: x['snippet']['thumbnails']['medium']['url']),  # Big thumbnail url
				self._tryList(result, lambda x: x['snippet']['channelId']),  # Channel id
				PublishedAt)

			if self._tryList(result, lambda x: x['snippet']['liveBroadcastContent']) == 'live':
				videos.insert(0, videosInfo)  # if live broadcast insert in top of list
			else:
				videos.append(videosInfo)
		return videos

	def videoIdFromPlaylist(self, order, channel, getPageToken=True):
		videos = []
		search_response = self.ytapi.playlistItems_list(
				order=order,
				maxResults=self.search_result,
				playlistId=channel,
				pageToken=self.yts[0].get('pageToken', ''))
		if getPageToken:
			self.yts[0]['nextPageToken'] = search_response.get('nextPageToken', '')
			self.yts[0]['prevPageToken'] = search_response.get('prevPageToken', '')
			self.setSearchResults(search_response.get('pageInfo', {}).get('totalResults', 0))
		for result in search_response.get('items', []):
			try:
				videos.append(result['snippet']['resourceId']['videoId'])
			except Exception as e:
				print('[YouTube] Error get videoId from Playlist', e)
		return videos

	def videoIdFromChannellist(self, channel, order):
		videos = []
		search_response = self.ytapi.search_list(
				order=order,
				part='id',
				channelId=channel,
				maxResults=self.search_result,
				pageToken=self.yts[0].get('pageToken', ''))
		self.yts[0]['nextPageToken'] = search_response.get('nextPageToken', '')
		self.yts[0]['prevPageToken'] = search_response.get('prevPageToken', '')
		self.setSearchResults(search_response.get('pageInfo', {}).get('totalResults', 0))
		for result in search_response.get('items', []):
			try:
				videos.append(result['id']['videoId'])
			except Exception as e:
				print('[YouTube] Error get videoId from Channellist', e)
		return videos

	def createList(self, search_response, subscription):
		videos = []
		self.yts[0]['nextPageToken'] = search_response.get('nextPageToken', '')
		self.yts[0]['prevPageToken'] = search_response.get('prevPageToken', '')
		self.setSearchResults(search_response.get('pageInfo', {}).get('totalResults', 0))
		kind = self.yts[0]['list']
		for result in search_response.get('items', []):
			try:
				kind = result['id']['kind'].split('#')[1]
			except Exception:
				kind = self.yts[0]['list']
			videos.append((
				self._tryList(result, lambda x: x['id'][kind + 'Id']),  # Id
				self._tryStr(result, lambda x: x['snippet']['thumbnails']['default']['url']),  # Thumbnail url
				None,
				self._tryStr(result, lambda x: x['snippet']['title']),  # Title
				'', '', None, None, None, None, None, ''))
		if subscription and len(videos) > 1:
			videos.insert(0, ('recent_subscr', None, None, _('Recent'), '', '',
				None, None, None, None, None, ''))
		self.yts[0]['list'] = kind
		return videos

	def setSearchResults(self, total_results):
		if total_results > 0:
			page_index = self.yts[0].get('page_index', 1)
			page_end = page_index + int(self.search_result) - 1
			if page_end > total_results:
				page_end = total_results
			if '  (' in self.yts[0]['title']:
				self.yts[0]['title'] = self.yts[0]['title'].rsplit('  (', 1)[0]
			self.yts[0]['title'] = self.yts[0]['title'][:40] + _('  (%d-%d of %d)') %\
					(page_index, page_end, total_results)

	def cancel(self):
		if len(self.yts) == 1:
			self.close()
		else:
			self.yts.pop(0)
			if len(self.yts) == 1:
				# Authentication can be changes in setup in another list,
				# therefore always create a new main list
				self.createMainList()
			else:
				if self.yts[0]['list'] != 'videolist':
					self['info'].hide()
				self.setEntryList()

	def openMenu(self):
		if self.yts[0]['list'] == 'main':
			self.session.openWithCallback(self.configScreenCallback, YouTubeSetup)
		else:
			title = _('What do you want to do?')
			clist = ((_('YouTube setup'), 'setup'),)
			if self.yts[0].get('nextPageToken'):
				clist += ((ngettext('Next %s entry', 'Next %s entries',
						int(self.search_result)) % self.search_result, 'next'),)
			if self.yts[0].get('prevPageToken'):
				clist += ((ngettext('Previous %s entry', 'Previous %s entries',
						int(self.search_result)) % self.search_result, 'prev'),)
			if self.is_auth:
				if self.yts[0]['list'] == 'videolist':
					clist += ((_('Rate video'), 'rate'),
							(_('Subscribe this video channel'), 'subscribe_video'),)
				elif self.yts[0]['list'] == 'channel' and self.yts[1]['list'] != 'myfeeds':
					clist += ((_('Subscribe'), 'subscribe'),)
				elif self.yts[0]['list'] == 'playlist' and self.yts[1]['list'] == 'myfeeds' and \
						len(self.yts) == 3:
					clist += ((_('Unsubscribe'), 'unsubscribe'),)
			if self.yts[0]['list'] == 'videolist':
				clist += ((_('Search'), 'search'),
						(_('Download video'), 'download'),)
			if self.active_downloads > 0:
				clist += ((_('Active video downloads'), 'download_list'),)
			clist += ((_('Close YouTube'), 'close'),)
			self.session.openWithCallback(self.menuCallback,
					ChoiceBox, title=title, list=clist, keys=['menu'])

	def menuCallback(self, answer):
		if answer:
			answer = answer[1]
			msg = None
			clist = None
			if answer == 'setup':
				self.session.openWithCallback(self.configScreenCallback, YouTubeSetup)
			elif answer == 'next':
				self.setNextEntries()
			elif answer == 'prev':
				self.setPrevEntries()
			elif answer == 'rate':
				clist = ((_('I like this'), 'like'),
						(_('I dislike this'), 'dislike'),
						(_('Remove my rating'), 'none'),)
			elif answer == 'subscribe':
				current = self['list'].getCurrent()[0]
				msg = self.subscribeChannel(current)
			elif answer == 'subscribe_video':
				current = self['list'].getCurrent()[10]
				msg = self.subscribeChannel(current)
			elif answer == 'unsubscribe':
				msg = self.unsubscribeChannel()
			elif answer == 'search':
				clist = ((_('Search for similar'), 'similar'),
						(_('Videos from this video channel'), 'channel_videos'),)
			elif answer == 'similar':
				term = self['list'].getCurrent()[3][:40]
				self.screenCallback(term, 'search')
			elif answer == 'channel_videos':
				current = self['list'].getCurrent()
				self.screenCallback(current[3][:40], 'channel')
			elif answer == 'download':
				current = self['list'].getCurrent()
				if current[6]:
					self.videoDownload(current[6], current[3])
				else:
					self.yts[0]['index'] = self['list'].index
					self.yts.insert(0, {})
					self.screenCallback('', 'downloadVideo')
			elif answer == 'download_list':
				from .YouTubeDownload import YouTubeDownloadList
				self.session.open(YouTubeDownloadList)
			elif answer == 'close':
				self.close()
			else:
				msg = self.rateVideo(answer)
			if msg:
				self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=3)
			elif clist:
				title = _('What do you want to do?')
				self.session.openWithCallback(self.menuCallback,
						ChoiceBox, title=title, list=clist)

	def configScreenCallback(self, callback=None):
		self.search_result = config.plugins.YouTube.searchResult.value
		if self.is_auth != config.plugins.YouTube.login.value:
			self.is_auth = False
			self.createAuth()
			if self.yts[0]['list'] == 'main':
				self.createMainList()

	def subscribeChannel(self, channelId):
		if self.ytapi.subscriptions_insert(channelId=channelId):
			return _('Subscribed!')
		return _('There was an error!')

	def unsubscribeChannel(self):
		sub_id = self['list'].getCurrent()[6]
		if sub_id and self.ytapi.subscriptions_delete(sub_id):
			# update subscriptions list
			del self.yts[0]['entry_list'][self['list'].index]
			self['list'].updateList(self.yts[0].get('entry_list', []))
			return _('Unsubscribed!')
		return _('There was an error!')

	def rateVideo(self, rating):
		videoId = self['list'].getCurrent()[0]
		if self.ytapi.videos_rate(videoId=videoId, rating=rating):
			text = {'like': _('Liked!'),
				'dislike': _('Disliked!'),
				'none': _('Rating removed!')}
			# update liked video list
			if self.yts[1]['entry_list'][self.yts[1]['index']][0] == 'my_liked_videos':
				del self.yts[0]['entry_list'][self['list'].index]
				self['list'].updateList(self.yts[0].get('entry_list', []))
			return text[rating]
		else:
			return _('There was an error!')

	def showEventInfo(self):
		if self.yts[0]['list'] == 'videolist':
			current = self['list'].getCurrent()
			self.session.open(YouTubeInfo, current=current)

	def videoDownload(self, url, title):
		downloadDir = config.plugins.YouTube.downloadDir.value
		if downloadDir[0] == "'":
			downloadDir = downloadDir[2:-2]
		if not os.path.exists(downloadDir):
			msg = _('Sorry, download directory not exist!\nPlease specify in the settings existing directory.')
		else:
			if hasattr(title, 'decode'):  # python2
				job_title = title.decode('utf-8', 'ignore')[:20].encode('utf-8')
			else:
				job_title = title[:20]
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
							'%s audio' % job_title, self.downloadStop))
					self.active_downloads += 1
					url = url[0]
					outputfile = outputfile[:-4] + '_suburi.mp4'
				job_manager.AddJob(downloadJob(url, outputfile, job_title, self.downloadStop))
				self.active_downloads += 1
				msg = _('Video download started!')
		self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=5)

	def downloadStop(self):
		if hasattr(self, 'active_downloads'):
			self.active_downloads -= 1

	def setPrevEntries(self):
		page_token = self.yts[0].get('prevPageToken', '')
		page_index = self.yts[0].get('page_index', int(self.search_result) + 1) - int(self.search_result)
		self.usePageToken(page_token, page_index, True)

	def setNextEntries(self):
		page_token = self.yts[0].get('nextPageToken', '')
		page_index = self.yts[0].get('page_index', 1) + int(self.search_result)
		self.usePageToken(page_token, page_index)

	def usePageToken(self, page_token, page_index, last=False):
		related = self.yts[0].get('related')
		self.yts.pop(0)
		self.yts.insert(0, {})
		self.yts[0]['pageToken'] = page_token
		self.yts[0]['page_index'] = page_index
		if related:
			self.yts[0]['related'] = related
		if last:
			self.yts[0]['index'] = int(self.search_result) - 1
		self.screenCallback(self.title, self.yts[1]['list'])


class YouTubeInfo(Screen):
	if screenwidth == 'svg':
		skin = """<screen position="center,center" size="730*f,424*f">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube.svg" \
					position="15*f,0" size="100*f,40*f" transparent="1" alphatest="blend" />
				<widget name="title" position="115*f,0" size="600*f,60*f" halign="center" font="Regular;24*f" />
				<widget name="pic" position="20*f,70*f" size="320*f,180*f" transparent="1" alphatest="on" />
				<widget name="description" position="360*f,70*f" size="360*f,300*f" font="Regular;16*f" />
				<widget name="views" position="30*f,270*f" size="150*f,20*f" font="Regular;16*f" />
				<widget name="duration" position="200*f,270*f" size="150*f,20*f" font="Regular;16*f" />
				<widget name="likes" position="30*f,300*f" size="150*f,20*f" font="Regular;16*f" />
				<widget name="published" position="30*f,330*f" size="300*f,20*f" font="Regular;16*f" />
				<ePixmap position="295*f,377*f" size="140*f,40*f" pixmap="skin_default/buttons/red.svg" \
					transparent="1" alphatest="blend" />
				<widget source="key_red" render="Label" position="center,382*f" zPosition="2" size="140*f,30*f" \
					valign="center" halign="center" font="Regular;22*f" transparent="1" />
			</screen>"""
	elif screenwidth == 1280:
		skin = """<screen position="center,center" size="730,424">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_HD.png" \
					position="15,0" size="100,40" transparent="1" alphatest="on" />
				<widget name="title" position="115,0" size="600,60" halign="center" font="Regular;24" />
				<widget name="pic" position="20,70" size="320,180" transparent="1" alphatest="on" />
				<widget name="description" position="360,70" size="360,300" font="Regular;16" />
				<widget name="views" position="30,270" size="150,20" font="Regular;16" />
				<widget name="duration" position="200,270" size="150,20" font="Regular;16" />
				<widget name="likes" position="30,300" size="150,20" font="Regular;16" />
				<widget name="published" position="30,330" size="300,20" font="Regular;16" />
				<ePixmap position="295,377" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="center,382" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
			</screen>"""
	elif screenwidth == 1920:
		skin = """<screen position="center,center" size="1095,636">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_FHD.png" \
					position="15,0" size="150,60" transparent="1" alphatest="on" />
				<widget name="title" position="172,0" size="900,90" halign="center" font="Regular;36" />
				<widget name="pic" position="30,105" size="320,180" transparent="1" alphatest="on" />
				<widget name="description" position="380,105" size="670,453" font="Regular;24" />
				<widget name="views" position="45,305" size="225,30" font="Regular;24" />
				<widget name="duration" position="45,355" size="225,30" font="Regular;24" />
				<widget name="likes" position="45,405" size="225,30" font="Regular;24" />
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
				<widget name="published" position="360,300" size="260,20" font="Regular;16" />
				<ePixmap position="245,323" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="245,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
			</screen>"""

	def __init__(self, session, current):
		Screen.__init__(self, session)
		self.title = _('Info')
		self['key_red'] = StaticText(_('Exit'))
		self['title'] = Label(current[3])
		self['pic'] = Pixmap()
		self['description'] = ScrollLabel(current[7])
		self['views'] = Label(current[4])
		self['duration'] = Label(current[5])
		self['likes'] = Label(current[8])
		self['dislikes'] = Label()  # For backward compatibility, YouTube make dislike count private
		self['published'] = Label(current[11])
		self['actions'] = ActionMap(['ColorActions',
			'InfobarShowHideActions', 'DirectionActions'], {
				'red': self.close,
				'toggleShow': self.close,
				'hide': self.close,
				'infoButton': self.close,
				'up': self['description'].pageUp,
				'down': self['description'].pageDown}, -2)
		self.thumbnail_url = current[9]
		self.onLayoutFinish.append(self.LayoutFinish)

	def LayoutFinish(self):
		if self.thumbnail_url:
			image = '/tmp/hqdefault.jpg'
			try:
				compat_urlretrieve(self.thumbnail_url, image)
			except Exception as e:
				print('[YouTube] Medium thumbnail download error', e)
			else:
				self['pic'].instance.setScale(1)
				self['pic'].instance.setPixmap(LoadPixmap(image))
				os.remove(image)


class YouTubeSetup(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _('YouTube setup')
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
			if 'ServiceApp' in p.path:  # pragma: no cover
				self.list.append(getConfigListEntry(_('Media player:'),
					config.plugins.YouTube.player,
					_('Specify the player which will be used for YouTube media playback.')))
				break
		self['config'].list = self.list

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
		elif self.mergeFiles != config.plugins.YouTube.mergeFiles.value:  # pragma: no cover
			if self.mergeFiles:
				self.session.openWithCallback(self.removeCallback,
					MessageBox, _('You have disabled downloaded file merge.\nInstalled FFmpeg is no longer necessary.\nDo you want to remove FFmpeg?'))
			else:
				self.session.openWithCallback(self.installCallback,
					MessageBox, _('To merge downloaded files FFmpeg will be installed.\nFFmpeg can take a lot of space!\nDo you want to continue?'))
		else:  # pragma: no cover
			self.keySave()

	def removeCallback(self, answer):  # pragma: no cover
		if answer:
			from Screens.Console import Console
			self.session.open(Console, cmdlist=['opkg remove --autoremove ffmpeg'])
		self.keySave()

	def installCallback(self, answer):  # pragma: no cover
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

	def warningCallback(self, answer):  # pragma: no cover
		if not answer:
			self.login = config.plugins.YouTube.login.value = False
		else:
			from .OAuth import OAuth
			self.splitTaimer = eTimer()
			self.splitTaimer.timeout.callback.append(self.splitTaimerStop)
			self.oauth = OAuth()
			url, user_code = self.oauth.get_user_code()
			if user_code:
				msg = _('Go to %s\nAnd enter the code %s') % (url, user_code)
				print('[YouTube] ', msg)
				self.mbox = self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)
				self.splitTaimer.start(9000, True)
			else:
				print('[YouTube] Error in OAuth!')
				self.session.open(MessageBox, 'There was an error!', MessageBox.TYPE_INFO, timeout=5)

	def splitTaimerStop(self):  # pragma: no cover
		# Here we waiting until the user enter a code
		refresh_token, retry_interval = self.oauth.get_new_token()
		if not refresh_token:
			self.splitTaimer.start(retry_interval * 1000, True)
		else:
			print('[YouTube] Get refresh token')
			if self.mbox:
				self.mbox.close()
			config.plugins.YouTube.refreshToken.value = refresh_token
			config.plugins.YouTube.refreshToken.save()
			del self.splitTaimer
			self.mbox = None
			self.oauth = None
