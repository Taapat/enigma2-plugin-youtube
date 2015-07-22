import os
from twisted.web.client import downloadPage

from enigma import ePicLoad, ePoint, eServiceReference, eTimer, getDesktop
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.config import config, ConfigDirectory, ConfigSelection, \
	ConfigSubsection, ConfigText, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_HDD, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap

from . import _


config.plugins.YouTube = ConfigSubsection()
config.plugins.YouTube.saveHistory = ConfigYesNo(default = True)
config.plugins.YouTube.searchResult = ConfigSelection(
	[('4', '4'),
	('8', '8'),
	('16', '16'),
	('24', '24'),
	('50', '50')
	], '24')
config.plugins.YouTube.searchRegion = ConfigSelection(
	[('', _('All')),
	('AU', _('Australia')),
	('BR', _('Brazil')),
	('CA', _('Canada')),
	('CZ', _('Czech Republic')),
	('FR', _('France')),
	('DE', _('Germany')),
	('GB', _('Great Britain')),
	('NL', _('Holland')),
	('HK', _('Hong Kong')),
	('IN', _('India')),
	('IE', _('Ireland')),
	('IL', _('Israel')),
	('IT', _('Italy')),
	('JP', _('Japan')),
	('LV', _('Latvia')),
	('MX', _('Mexico')),
	('NZ', _('New Zealand')),
	('PL', _('Poland')),
	('RU', _('Russia')),
	('KR', _('South Korea')),
	('ES', _('Spain')),
	('SE', _('Sweden')),
	('TW', _('Taiwan')),
	('US', _('United States'))
	], None)
config.plugins.YouTube.searchLanguage = ConfigSelection(
	[('', _('All')),
	('au', _('Australia')),
	('br', _('Brazil')),
	('ca', _('Canada')),
	('cz', _('Czech Republic')),
	('fr', _('France')),
	('de', _('Germany')),
	('gb', _('Great Britain')),
	('nl', _('Holland')),
	('hk', _('Hong Kong')),
	('in', _('India')),
	('ie', _('Ireland')),
	('il', _('Israel')),
	('it', _('Italy')),
	('jp', _('Japan')),
	('lv', _('Latvia')),
	('mx', _('Mexico')),
	('nz', _('New Zealand')),
	('pl', _('Poland')),
	('ru', _('Russia')),
	('kr', _('South Korea')),
	('es', _('Spain')),
	('se', _('Sweden')),
	('tw', _('Taiwan')),
	('us', _('United States'))
	], None)
config.plugins.YouTube.searchOrder = ConfigSelection(
	[('relevance', _('Relevance')),
	('date', _('Created date')),
	('rating', _('Rating')),
	('title', _('Title')),
	('viewCount', _('View count'))
	], 'relevance')
config.plugins.YouTube.safeSearch = ConfigSelection(default = 'moderate', choices = [
	('moderate', _('Moderate')), ('none', _('No')), ('strict', _('Yes'))])
config.plugins.YouTube.maxResolution = ConfigSelection(default = '22', choices = [
	('38', '3072p'), ('37', '1080p'), ('22', '720p'), ('35', '480p'), 
	('18', '360p'), ('5', '240p'), ('17', '144p')])
config.plugins.YouTube.onMovieEof = ConfigSelection(default = 'quit', choices = [
	('quit', _('Return to list')), ('ask', _('Ask user')),
	('playnext', _('Play next')), ('repeat', _('Repeat'))])
config.plugins.YouTube.onMovieStop = ConfigSelection(default = 'ask', choices = [
	('ask', _('Ask user')), ('quit', _('Return to list'))])
config.plugins.YouTube.login = ConfigYesNo(default = False)
config.plugins.YouTube.downloadDir = ConfigDirectory(default=resolveFilename(SCOPE_HDD))

config.plugins.YouTube.searchHistory = ConfigText(default='')
config.plugins.YouTube.refreshToken = ConfigText(default='')

API_KEY = 'AIzaSyCyIlbb0FIwoieEZ9RTShMVkRMisu-ZX0k'
YOUTUBE_API_CLIENT_ID = '411447027255-vbgs05u1o3m8mpjs2vcd04afrg60drba.apps.googleusercontent.com'
YOUTUBE_API_CLIENT_SECRET = 'fYE-8T3qf4DrLPLv3NTgvjna'


class YouTubePlayer(MoviePlayer):
	def __init__(self, session, service, current):
		MoviePlayer.__init__(self, session, service)
		self.skinName = 'MoviePlayer'
		self.current = current
		self.servicelist = InfoBar.instance and InfoBar.instance.servicelist

	def leavePlayer(self):
		if config.plugins.YouTube.onMovieStop.value == 'ask':
			title = _('Stop playing this movie?')
			list = (
					(_('Yes'), 'quit'),
					(_('Yes, but play next video'), 'playnext'),
					(_('Yes, but play previous video'), 'playprev'),
					(_('No, but play video again'), 'repeat'),
					(_('No'), 'continue')
				)
			self.session.openWithCallback(self.leavePlayerConfirmed,
				ChoiceBox, title = title, list = list)
		else:
			self.close()

	def leavePlayerConfirmed(self, answer):
		if answer and answer[1] != 'continue':
			self.close(answer)

	def doEofInternal(self, playing):
		self.close([None, config.plugins.YouTube.onMovieEof.value])

	def getPluginList(self):
		from Components.PluginComponent import plugins
		list = []
		for p in plugins.getPlugins(where = PluginDescriptor.WHERE_EXTENSIONSMENU):
			if p.name != _('YouTube'):
				list.append(((boundFunction(self.getPluginName, p.name),
					boundFunction(self.runPlugin, p), lambda: True), None))
		return list

	def openCurEventView(self):
		self.session.open(YouTubeInfo, current = self.current)

	def showMovies(self):
		pass

	def openServiceList(self):
		if hasattr(self, "toggleShow"):
			self.toggleShow()


class YouTubeMain(Screen):
	screenWidth = getDesktop(0).size().width()
	if screenWidth and screenWidth == 1280:
		skin = """<screen position="center,center" size="730,514">
				<widget name="text" position="center,0" size="700,30" halign="center" font="Regular;24" />
				<widget source="list" render="Listbox" position="center,32" size="700,432" \
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
				<widget name="info" position="50,479" size="35,25" pixmap="skin_default/buttons/key_info.png" \
					transparent="1" alphatest="on" />
				<widget name="red" position="215,467" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget name="green" position="375,467" size="140,40" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="215,472" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget source="key_green" render="Label" position="375,472" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget name="menu" position="645,479" size="35,25" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				<widget name="thumbnail" position="0,0" size="100,72" /> # Thumbnail size in list
			</screen>"""
	elif screenWidth and screenWidth == 1920:
		skin = """<screen position="center,center" size="1095,771">
				<widget name="text" position="center,0" size="1050,45" halign="center" font="Regular;36" />
				<widget source="list" render="Listbox" position="center,48" size="1050,648" \
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
				<widget name="info" position="75,718" size="53,38" pixmap="skin_default/buttons/key_info.png" \
					transparent="1" alphatest="on" />
				<widget name="red" position="322,707" size="210,60" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget name="green" position="563,707" size="210,60" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="322,714" zPosition="2" size="210,45" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
				<widget source="key_green" render="Label" position="563,714" zPosition="2" size="210,45" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
				<widget name="menu" position="968,718" size="53,38" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				<widget name="thumbnail" position="0,0" size="150,108" /> # Thumbnail size in list
			</screen>"""
	else:
		skin = """<screen position="center,center" size="630,370">
				<widget name="text" position="center,0" size="600,30" halign="center" font="Regular;24" />
				<widget source="list" render="Listbox" position="center,32" size="600,288" \
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
				<widget name="info" position="30,335" size="35,25" pixmap="skin_default/buttons/key_info.png" \
					transparent="1" alphatest="on" />
				<widget name="red" position="114,323" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget name="green" position="374,323" size="140,40" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="114,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget source="key_green" render="Label" position="374,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget name="menu" position="565,335" size="35,25" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				<widget name="thumbnail" position="0,0" size="100,72" /> # Thumbnail size in list
			</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_('YouTube'))
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
		self['actions'] = ActionMap(['SetupActions', 'ColorActions', 'MovieSelectionActions'],
			{
				'cancel': self.cancel,
				'ok': self.ok,
				'red': self.cancel,
				'green': self.ok,
				'contextMenu': self.openMenu,
				'showEventInfo': self.showEventInfo
			}, -2)
		text = _('YouTube starting. Please wait...')
		self['text'] = Label()
		self['text'].setText(text)
		self['list'] = List([])
		self['thumbnail'] = Pixmap()
		self['thumbnail'].hide()
		self.splitTaimer = eTimer()
		self.splitTaimer.timeout.callback.append(self.splitTaimerStop)
		self.thumbnailTaimer = eTimer()
		self.thumbnailTaimer.timeout.callback.append(self.updateThumbnails)
		self.picloads = {}
		self.thumbnails = {}
		self.list = 'main'
		self.action = 'startup'
		self.value = [None, None, None]
		self.prevIndex = []
		self.prevEntryList = []
		self.entryList = []
		self.ytdl = None
		self.youtube = None
		self.isAuth = False
		self.eventInfo = [None]
		self.onLayoutFinish.append(self.layoutFinish)
		self.onClose.append(self.cleanVariables)

	def layoutFinish(self):
		defThumbnail = resolveFilename(SCOPE_PLUGINS,
			'Extensions/YouTube/icons/icon.png')
		self.decodeThumbnail('default', defThumbnail)
		self.splitTaimer.start(1)

	def cleanVariables(self):
		del self.thumbnailTaimer
		del self.splitTaimer
		self.ytdl = None
		self.youtube = None
		self.thumbnails = None
		self.entryList = None
		self.prevEntryList = None
		self.eventInfo = None

	def createMainList(self):
		self.list = 'main'
		self.value = [None, None, None]
		self.text = _('Choose what you want to do')
		self.entryList = [(
				'Search',           # Id
				None,               # Thumbnail url
				None,               # Thumbnail
				_('Search'),        # Title
				'',                 # Views
				'',                 # Duration
				None,               # Video url
				None,               # Description
				None,               # Likes
				None,               # Dislikes
				None                # Big thumbnail url
			),(
				'PubFeeds', None, None,
				_('Public feeds'), '', '', None,
				None, None, None, None
			)]
		if config.plugins.YouTube.login.value and \
			config.plugins.YouTube.refreshToken.value != '':
			self.entryList.append(('MyFeeds', None, None,
				_('My feeds'), '', '', None, None, None, None, None))
		self.setEntryList()

	def createSearchList(self):
		self.list = 'search'
		self.value = [None, None, None]
		self.text = _('Search')
		self.entryList = [(
				'Searchvideo', None, None,
				_('Search videos'), '', '', None,
				None, None, None, None
			),(
				'Searchchannel', None, None,
				_('Search channels'), '', '', None,
				None, None, None, None
			),(
				'Searchplaylist', None, None,
				_('Search playlists'), '', '', None,
				None, None, None, None
			)]
		self.setEntryList()

	def createFeedList(self):
		self.list = 'feeds'
		self.value = [None, None, None]
		self.text = _('Public feeds')
		self.entryList = [(
				'top_rated', None, None,
				_('Top rated'), '', '', None,
				None, None, None, None
			),(
				'most_viewed', None, None,
				_('Most viewed'), '', '', None,
				None, None, None, None
			),(
				'most_recent', None, None,
				_('Recent'), '', '', None,
				None, None, None, None
			),(
				'HD_videos', None, None,
				_('HD videos'), '', '', None,
				None, None, None, None
			),(
				'embedded_videos', None, None,
				_('Embedded in webpages'), '', '', None,
				None, None, None, None
			),(
				'episodes', None, None,
				_('Shows'), '', '', None,
				None, None, None, None
			),(
				'movies', None, None,
				_('Movies'), '', '', None,
				None, None, None, None
			)]
		self.setEntryList()

	def createMyFeedList(self):
		self.list = 'myfeeds'
		self.value = [None, None, None]
		self.text = _('My feeds')
		self.entryList = [(
				'my_subscriptions', None, None,
				_('My Subscriptions'), '', '', None,
				None, None, None, None
			),(
				'my_watch_later', None, None,
				_('Watch Later'), '', '', None,
				None, None, None, None
			),(
				'my_history', None, None,
				_('History'), '', '', None,
				None, None, None, None
			),(
				'my_liked_videos', None, None,
				_('Liked videos'), '', '', None,
				None, None, None, None
			),(
				'my_favorites', None, None,
				_('Favorites'), '', '', None,
				None, None, None, None
			),(
				'my_uploads', None, None,
				_('Uploads'), '', '', None,
				None, None, None, None
			),(
				'my_playlists', None, None,
				_('Playlists'), '', '', None,
				None, None, None, None
			)]
		self.setEntryList()

	def screenCallback(self, value = None, action = None):
		if not action: # cancel in search
			self.cancel()
		else:
			self.value = value
			self.action = action
			if action == 'OpenSearch':
				text = _('Download search results. Please wait...')
			elif action in ['playVideo', 'downloadVideo']:
				text = _('Extract video url. Please wait...')
			else:
				text = _('Download feed entries. Please wait...')
			self['text'].setText(text)
			self['list'].setList([])
			self['key_red'].setText('')
			self['key_green'].setText('')
			self['red'].hide()
			self['green'].hide()
			self['menu'].hide()
			self['info'].hide()
			self.splitTaimer.start(1)

	def splitTaimerStop(self):
		self.splitTaimer.stop()
		if self.action == 'startup':
			from YouTubeVideoUrl import YouTubeVideoUrl
			self.ytdl = YouTubeVideoUrl()
			self.createBuild()
			self.createMainList()
		elif self.action in ['playVideo', 'downloadVideo']:
			videoUrl = self.value[6]
			if not videoUrl: # remember video url
				videoUrl, urlError = self.getVideoUrl()
				if urlError:
					self.session.open(MessageBox,
						_('There was an error in extract video url:\n%s') % urlError, 
						MessageBox.TYPE_INFO, timeout = 8)
				else:
					count = 0
					for entry in self.entryList:
						if entry[0] == self.value[0]:
							entryList = entry
							self.entryList[count] = (
									entryList[0], # Id
									entryList[1], # Thumbnail url
									entryList[2], # Thumbnail
									entryList[3], # Title
									entryList[4], # Views
									entryList[5], # Duration
									videoUrl,     # Video url
									entryList[7], # Description
									entryList[8], # Likes
									entryList[9], # Dislikes
									entryList[10] # Big thumbnail url
								)
							break
						count += 1
			if videoUrl:
				if self.action == 'playVideo':
					service = eServiceReference(4097, 0, videoUrl)
					service.setName(self.value[3])
					current = [self.value[3], self.value[4], self.value[5], self.value[7],
						self.value[8], self.value[9], self.value[10]]
					print "[YouTube] Play:", videoUrl
					self.session.openWithCallback(self.playCallback,\
						YouTubePlayer, service = service, current = current)
				else:
					self.videoDownload(videoUrl, self.value[3])
					self.setEntryList()
					self.setPreviousList()
			else:
				self.setEntryList()
				self.setPreviousList()
		else:
			entryList = self.createEntryList()
			if not entryList:
				self.session.open(MessageBox,
					_('There was an error in creating entry list!\nMaybe try other feeds...'), 
					MessageBox.TYPE_INFO, timeout = 8)
				self.setEntryList()
				self.setPreviousList()
				self.prevEntryList.pop()
			else:
				self.entryList = entryList
				self.text = self.value[1]
				self.setEntryList()

	def setEntryList(self):
		self['text'].setText(self.text)
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
			if entry[2]: # If thumbnail created
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
					downloadPage(url, image)\
						.addCallback(boundFunction(self.downloadFinished, entryId))\
						.addErrback(boundFunction(self.downloadFailed, entryId))

	def downloadFinished(self, entryId, result):
		image = os.path.join('/tmp/', str(entryId) + '.jpg')
		self.decodeThumbnail(entryId, image)

	def downloadFailed(self, entryId, result):
		print "[YouTube] Thumbnail download failed, use default for", entryId
		self.decodeThumbnail(entryId)

	def decodeThumbnail(self, entryId, image = None):
		if not image or not os.path.exists(image):
			print "[YouTube] Thumbnail not exists, use default for", entryId
			self.thumbnails[entryId] = True
			self.thumbnailTaimer.start(1)
		else:
			sc = AVSwitch().getFramebufferScale()
			self.picloads[entryId] = ePicLoad()
			self.picloads[entryId].PictureData.get()\
				.append(boundFunction(self.FinishDecode, entryId, image))
			self.picloads[entryId].setPara((
				self['thumbnail'].instance.size().width(),
				self['thumbnail'].instance.size().height(),
				sc[0], sc[1], False, 1, '#00000000'))
			self.picloads[entryId].startDecode(image)

	def FinishDecode(self, entryId, image, picInfo = None):
		ptr = self.picloads[entryId].getData()
		if ptr:
			self.thumbnails[entryId] = ptr
			del self.picloads[entryId]
			if image[:4] == '/tmp':
				os.remove(image)
			self.thumbnailTaimer.start(1)

	def updateThumbnails(self):
		self.thumbnailTaimer.stop()
		if len(self.picloads) != 0:
			self.thumbnailTaimer.start(1)
		else:
			count = 0
			for entry in self.entryList:
				entryId = entry[0]
				if not entry[2] and entryId in self.thumbnails:
					entryList = entry
					thumbnailData = self.thumbnails[entryId]
					if thumbnailData == True:
						thumbnail = self.thumbnails['default']
					else:
						thumbnail = self.thumbnails[entryId]
					self.entryList[count] = (
							entryList[0], # Id
							entryList[1], # Thumbnail url
							thumbnail,    # Thumbnail
							entryList[3], # Title
							entryList[4], # Views
							entryList[5], # Duration
							entryList[6], # Video url
							entryList[7], # Description
							entryList[8], # Likes
							entryList[9], # Dislikes
							entryList[10] # Big thumbnail url
						)
				count += 1
			self['list'].updateList(self.entryList)

	def playCallback(self, action=None):
		self.setEntryList()
		self.setPreviousList()
		if action:
			action = action[1]
		if action == 'playnext':
			l = self['list'].index + 1
			if l < len(self.entryList):
				self['list'].selectNext()
				self.ok()
		elif action == 'playprev':
			l = self['list'].index - 1
			if l >= 0:
				self['list'].selectPrevious()
				self.ok()
		elif action == 'repeat':
			self.ok()
		elif action == 'ask':
			self.rememberCurList()
			title = _('What do you want to do?')
			list = (
					(_('Quit'), 'quit'),
					(_('Play next video'), 'playnext'),
					(_('Play previous video'), 'playprev'),
					(_('Play video again'), 'repeat')
				)
			self.session.openWithCallback(self.playCallback,
				ChoiceBox, title = title, list = list)

	def setPreviousList(self):
		lastInex = self.prevIndex[len(self.prevIndex) - 1]
		self['list'].setIndex(lastInex[0])
		self.list = lastInex[1]
		self.text = lastInex[2]
		self['text'].setText(self.text)
		self.prevIndex.pop()

	def rememberCurList(self):
		self.prevIndex.append([self['list'].index, self.list, self.text])

	def ok(self):
		current = self['list'].getCurrent()
		if current:
			print "[YouTube] Selected:", current[0]
			self.rememberCurList()
			if self.list == 'videolist':
				self.screenCallback(current, 'playVideo')
			else:
				self.prevEntryList.append(self.entryList)
				if current[0] == 'Search':
					self.createSearchList()
				elif current[0] == 'PubFeeds':
					self.createFeedList()
				elif current[0] == 'MyFeeds':
					self.createMyFeedList()
				elif self.list == 'search':
					from YouTubeSearch import YouTubeSearch
					self.session.openWithCallback(self.screenCallback, YouTubeSearch, current[0][6:])
				elif self.list == 'feeds':
					self.screenCallback([current[0], current[3], current[6]], 'OpenFeeds')
				elif self.list == 'myfeeds':
					self.screenCallback([current[0], current[3], current[6]], 'OpenMyFeeds')
				elif self.list == 'playlist':
					self.screenCallback([current[0], current[3], current[6]], 'OpenPlayList')
				elif self.list == 'channel':
					self.screenCallback([current[0], current[3], current[6]], 'OpenChannelList')

	def getVideoUrl(self):
		try:
			videoUrl = self.ytdl.extract(self.value[0])
		except Exception as e:
			print '[YouTube] Error in extract info:', e
			return None, e
		if videoUrl:
			return videoUrl, None
		print '[YouTube] Video url not found'
		return None, ' '

	def convertDate(self, duration):
		time = ':' + duration.replace('P', '')\
			.replace('W', '-').replace('D', ' ').replace('T', '')\
			.replace('H', ':').replace('M', ':').replace('S', '')
		if not 'S' in duration:
			time += '00'
		elif time[-2] == ':':
			time = time[:-1] + '0' + time[-1]
		if not 'M' in duration:
			time = time[:-2] + '00' + time[-3:]
		elif time[-5] == ':':
			time = time[:-4] + '0' + time[-4:]
		return time[1:]

	def createBuild(self):
		refreshToken = config.plugins.YouTube.refreshToken.value
		if not self.youtube or (not self.isAuth and \
			refreshToken and config.plugins.YouTube.login.value):
			from YouTubeApi import YouTubeApi
			self.youtube = YouTubeApi(
				client_id = YOUTUBE_API_CLIENT_ID,
				client_secret = YOUTUBE_API_CLIENT_SECRET,
				developer_key = API_KEY,
				refresh_token = refreshToken)
			if self.youtube.access_token:
				self.isAuth = True
			else:
				self.isAuth = False

	def createEntryList(self):
		self.createBuild()
		order = 'date'
		searchType = 'video'
		q = ''
		videoEmbeddable = videoDefinition = videoType = ''

		if self.action == 'OpenSearch':
			order = config.plugins.YouTube.searchOrder.value
			searchType = self.value[0]
			q = self.value[1]
		elif self.action == 'OpenFeeds':
			if self.value[0] == 'top_rated':
				order = 'rating'
			elif self.value[0] == 'most_viewed':
				order = 'viewCount'
			elif self.value[0] == 'HD_videos':
				videoDefinition = 'high'
			elif self.value[0] == 'embedded_videos':
				videoEmbeddable = 'true'
			elif self.value[0] == 'episodes':
				videoType = 'episode'
			elif self.value[0] == 'movies':
				videoType = 'movie'
		elif self.action == 'OpenMyFeeds':
			if not self.isAuth:
				return None
			elif self.value[0] == 'my_watch_later':
				playlist = 'watchLater'
			elif self.value[0] == 'my_history':
				playlist = 'watchHistory'
			elif self.value[0] == 'my_liked_videos':
				playlist = 'likes'
			elif self.value[0] == 'my_favorites':
				playlist = 'favorites'
			elif self.value[0] == 'my_uploads':
				playlist = 'uploads'

		videos = []

		if self.action == 'OpenMyFeeds':
			channels = []
			if self.value[0] == 'my_subscriptions':
				self.list = 'playlist'
				searchResponse = self.youtube.subscriptions_list(
						maxResults = config.plugins.YouTube.searchResult.value
					)
				for result in searchResponse:
					try:
						Id = 'UU' + result['snippet']['resourceId']['channelId'][2:]
					except:
						Id = None
					try:
						Thumbnail = str(result['snippet']['thumbnails']['high']['url'])
					except:
						Thumbnail = None
					try:
						Title = str(result['snippet']['title'])
					except:
						Title = ''
					try:
						Subscription = result['id']
					except:
						Subscription = ''
					videos.append((Id, Thumbnail, None, Title, '', '', Subscription,
						None, None, None, None))
				return videos

			elif self.value[0] == 'my_playlists':
				self.list = 'playlist'
				searchResponse = self.youtube.playlists_list()
				for result in searchResponse:
					try:
						Id = result['id']
					except:
						Id = None
					try:
						Thumbnail = str(result['snippet']['thumbnails']['default']['url'])
					except:
						Thumbnail = None
					try:
						Title = str(result['snippet']['title'])
					except:
						Title = ''
					videos.append((Id, Thumbnail, None, Title, '', '', None,
						None, None, None, None))
				return videos

			else: # all other my data
				searchResponse = self.youtube.channels_list()
				for result in searchResponse:
					channel = result['contentDetails']['relatedPlaylists'][playlist]

				videos = self.videoIdFromPlaylist(channel)
				return self.extractVideoIdList(videos)

		elif self.action == 'OpenPlayList':
			videos = self.videoIdFromPlaylist(self.value[0])
			if not videos: # if channel list from subscription
				searchResponse = self.youtube.search_list(
						part = 'id,snippet',
						channelId = 'UC' + self.value[0][2:],
						maxResults = config.plugins.YouTube.searchResult.value
					)
				return self.createList(searchResponse, 'playlist')
			return self.extractVideoIdList(videos)

		elif self.action == 'OpenChannelList':
			videos = self.videoIdFromChannellist(self.value[0])
			return self.extractVideoIdList(videos)

		else: # search or pub feeds
			searchResponse = self.youtube.search_list_full(
					videoEmbeddable = videoEmbeddable,
					safeSearch = config.plugins.YouTube.safeSearch.value,
					videoType = videoType,
					videoDefinition = videoDefinition,
					order = order,
					part = 'id,snippet',
					q = q,
					relevanceLanguage = config.plugins.YouTube.searchLanguage.value,
					s_type = searchType,
					regionCode = config.plugins.YouTube.searchRegion.value,
					maxResults = config.plugins.YouTube.searchResult.value
				)

			if searchType != 'video':
				videos = self.createList(searchResponse, searchType)
				self.list = searchType
				return videos

			for result in searchResponse:
				videos.append(result['id']['videoId'])
			return self.extractVideoIdList(videos)

	def extractVideoIdList(self, videos):
		if len(videos) == 0:
			return None
		self.list = 'videolist'

		searchResponse = self.youtube.videos_list(v_id=','.join(videos))
		videos = []
		for result in searchResponse:
			try:
				Id = result['id']
			except:
				Id = None
			try:
				Thumbnail = str(result['snippet']['thumbnails']['default']['url'])
			except:
				Thumbnail = None
			try:
				Title = str(result['snippet']['title'])
			except:
				Title = ''
			try:
				Views = str(result['statistics']['viewCount']) + _(' views')
			except:
				Views = ''
			try:
				Duration = _('Duration: ') + self.convertDate(str(result['contentDetails']['duration']))
			except:
				Duration = ''
			try:
				Description = str(result['snippet']['description'])
			except:
				Description = ''
			try:
				Likes = str(result['statistics']['likeCount']) + _(' likes')
			except:
				Likes = ''
			try:
				Dislikes = str(result['statistics']['dislikeCount']) + _(' dislikes')
			except:
				Dislikes = ''
			try:
				ThumbnailUrl = str(result['snippet']['thumbnails']['medium']['url'])
			except:
				ThumbnailUrl = None

			videos.append((Id, Thumbnail, None, Title, Views, Duration, None, 
				Description, Likes, Dislikes, ThumbnailUrl))
		return videos

	def videoIdFromPlaylist(self, channel):
		videos = []
		searchResponse = self.youtube.playlistItems_list(
				maxResults = config.plugins.YouTube.searchResult.value,
				playlistId = channel
			)
		for result in searchResponse:
			try:
				videos.append(result['snippet']['resourceId']['videoId'])
			except:
				pass
		return videos

	def videoIdFromChannellist(self, channel):
		videos = []
		searchResponse = self.youtube.search_list(
				part = 'id',
				channelId = channel,
				maxResults = config.plugins.YouTube.searchResult.value
			)
		for result in searchResponse:
			try:
				videos.append(result['id']['videoId'])
			except:
				pass
		return videos

	def createList(self, searchResponse, listType):
		videos = []
		for result in searchResponse:
			try:
				Id = result['id'][listType + 'Id']
			except:
				Id = None
			try:
				Thumbnail = str(result['snippet']['thumbnails']['default']['url'])
			except:
				Thumbnail = None
			try:
				Title = str(result['snippet']['title'])
			except:
				Title = ''
			videos.append((Id, Thumbnail, None, Title, '', '', None,
				None, None, None, None))
		return videos

	def cancel(self):
		entryListIndex = len(self.prevEntryList) - 1
		if len(self.prevIndex) == 0 or entryListIndex < 0:
			self.close()
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
			list = ((_('YouTube setup'), 'setup'),
					(_('Close YouTube'), 'close'),)
			if self.isAuth:
				if self.list == 'videolist':
					list += ((_('I like this'), 'like'),
							(_('I dislike this'), 'dislike'),
							(_('Remove my rating'), 'none'),
							(_('Search for similar'), 'similar'),
							(_('Download video'), 'download'),)
				elif self.list == 'channel' and self.prevIndex[1][1] != 'myfeeds':
					list += ((_('Subscribe'), 'subscribe'),)
				elif self.list == 'playlist' and self.prevIndex[1][1] == 'myfeeds' and \
					len(self.prevIndex) == 2:
					list += ((_('Unsubscribe'), 'unsubscribe'),)
			list += ((_('Active video downloads'), 'download_list'),)
			self.session.openWithCallback(self.menuCallback,
				ChoiceBox, title = title, list = list)

	def menuCallback(self, answer):
		if answer:
			msg = None
			if answer[1] == 'close':
				self.close()
			elif answer[1] == 'setup':
				self.session.openWithCallback(self.configScreenCallback, YouTubeSetup)
			elif answer[1] == 'subscribe':
				msg = self.subscribeChannel()
			elif answer[1] == 'unsubscribe':
				msg = self.unsubscribeChannel()
			elif answer[1] == 'similar':
				term = self['list'].getCurrent()[3][:20]
				self.screenCallback(['video', term, None], 'OpenSearch')
			elif answer[1] == 'download':
				current = self['list'].getCurrent()
				if current[6]:
					self.videoDownload(current[6], current[3])
				else:
					self.rememberCurList()
					self.screenCallback(current, 'downloadVideo')
			elif answer[1] == 'download_list':
				from YouTubeDownload import YouTubeDownloadList
				self.session.open(YouTubeDownloadList)
			else:
				msg = self.rateVideo(answer[1])
			if msg:
				self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout = 3)

	def configScreenCallback(self, callback=None):
		if self.list == 'main': # if autentification changed
			self.createMainList()

	def subscribeChannel(self):
		channelId = self['list'].getCurrent()[0]
		if self.youtube.subscriptions_insert(channelId = channelId):
			return _('Subscribed!')
		return _('There was an error in subscribe!')

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
		return _('There was an error in unsubscribe!')

	def rateVideo(self, rating):
		videoId = self['list'].getCurrent()[0]
		if self.youtube.videos_rate(videoId = videoId, rating = rating):
			text = {
				'like': _('Liked!'),
				'dislike': _('Disliked!'),
				'none': _('Rating removed!')
				}
			return text[rating]
		else:
			return _('There was an error in rating!')

	def showEventInfo(self):
		if self.list == 'videolist':
			current = self['list'].getCurrent()
			current = [current[3], current[4], current[5], current[7],
				current[8], current[9], current[10]]
			self.session.open(YouTubeInfo, current = current)

	def videoDownload(self, url, title):
		outputfile = config.plugins.YouTube.downloadDir.value[2:-2] + title + '.mp4'
		if os.path.exists(outputfile):
			msg = _('Sorry, this file already exists:\n%s') % title
		else:
			from YouTubeDownload import downloadJob
			from Components.Task import job_manager
			job_manager.AddJob(downloadJob(url, outputfile, title[:20]))
			msg = _('Video download started!')
		self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout = 5)


class YouTubeInfo(Screen):
	screenWidth = getDesktop(0).size().width()
	if screenWidth and screenWidth == 1280:
		skin = """<screen position="center,center" size="730,424">
				<widget name="title" position="center,0" size="700,60" halign="center" font="Regular;24" />
				<widget name="pic" position="20,70" size="320,180" transparent="1" alphatest="on" />
				<widget name="description" position="360,70" size="360,302" font="Regular;16" />
				<widget name="views" position="30,270" size="150,20" font="Regular;16" />
				<widget name="duration" position="200,270" size="150,20" font="Regular;16" />
				<widget name="likes" position="30,300" size="150,20" font="Regular;16" />
				<widget name="dislikes" position="200,300" size="150,20" font="Regular;16" />
				<ePixmap position="center,377" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="center,382" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
			</screen>"""
	elif screenWidth and screenWidth == 1920:
		skin = """<screen position="center,center" size="1095,636">
				<widget name="title" position="center,0" size="1050,90" halign="center" font="Regular;36" />
				<widget name="pic" position="30,105" size="320,180" transparent="1" alphatest="on" />
				<widget name="description" position="380,105" size="670,453" font="Regular;24" />
				<widget name="views" position="45,305" size="225,30" font="Regular;24" />
				<widget name="duration" position="45,355" size="225,30" font="Regular;24" />
				<widget name="likes" position="45,405" size="225,30" font="Regular;24" />
				<widget name="dislikes" position="45,455" size="225,30" font="Regular;24" />
				<ePixmap position="center,565" size="210,60" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="center,563" zPosition="2" size="210,60" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
			</screen>"""
	else:
		skin = """<screen position="center,center" size="630,370">
				<widget name="title" position="center,0" size="600,60" halign="center" font="Regular;24" />
				<widget name="pic" position="20,70" size="320,180" transparent="1" alphatest="on" />
				<widget name="description" position="360,70" size="260,248" font="Regular;16" />
				<widget name="views" position="30,270" size="150,20" font="Regular;16" />
				<widget name="duration" position="200,270" size="150,20" font="Regular;16" />
				<widget name="likes" position="30,300" size="150,20" font="Regular;16" />
				<widget name="dislikes" position="200,300" size="150,20" font="Regular;16" />
				<ePixmap position="center,323" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="center,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
			</screen>"""

	def __init__(self, session, current):
		Screen.__init__(self, session)
		self.setTitle(_('YouTube info'))
		self['key_red'] = StaticText(_('Exit'))
		self['actions'] = ActionMap(['ColorActions', 'InfobarShowHideActions'],
			{
				'red': self.close,
				'toggleShow': self.close,
				'hide': self.close,
				'infoButton': self.close
			}, -2)
		self['title'] = Label(current[0])
		self['pic'] = Pixmap()
		self['description'] = Label(current[3])
		self['views'] = Label(current[1])
		self['duration'] = Label(current[2])
		self['likes'] = Label(current[4])
		self['dislikes'] = Label(current[5])
		self.picloads = None
		self.ThumbnailUrl = current[6]
		self.onLayoutFinish.append(self.LayoutFinish)

	def LayoutFinish(self):
		if self.ThumbnailUrl:
			downloadPage(self.ThumbnailUrl, '/tmp/hqdefault.jpg')\
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

	def FinishDecode(self, picInfo = None):
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
		self['key_green'] = StaticText(_('Ok'))
		self['description'] = Label('')
		self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'],
			{
				'cancel': self.keyCancel,
				'red': self.keyCancel,
				'ok': self.ok,
				'green': self.ok
			}, -2)
		self.mbox = None
		self.login = config.plugins.YouTube.login.value
		configlist = []
		ConfigListScreen.__init__(self, configlist, session=session,
			on_change = self.checkLoginSatus)

		configlist.append(getConfigListEntry(_('Save search result:'),
			config.plugins.YouTube.saveHistory,
			_('Save your search result in the history, when search completed.')))
		configlist.append(getConfigListEntry(_('Search results:'),
			config.plugins.YouTube.searchResult,
			_('How many search results will be returned.\nIf greater value then longer time will be needed for thumbnail download.')))
		configlist.append(getConfigListEntry(_('Search region:'),
			config.plugins.YouTube.searchRegion,
			 _('Return search results for the specified country.')))
		configlist.append(getConfigListEntry(_('Search language:'),
			config.plugins.YouTube.searchLanguage,
			 _('Return search results that are most relevant to the specified language.')))
		configlist.append(getConfigListEntry(_('Sort search results by:'),
			config.plugins.YouTube.searchOrder,
			_('Order in which search results will be displayed.')))
		configlist.append(getConfigListEntry(_('Exclude restricted content:'),
			config.plugins.YouTube.safeSearch,
			_('Try to exclude all restricted content from the search result.')))
		configlist.append(getConfigListEntry(_('Maximum video resolution:'),
		config.plugins.YouTube.maxResolution,
			_('What maximum resolution used when playing video, if available.\nIf you have a slow Internet connection, you can use a lower resolution.')))
		configlist.append(getConfigListEntry(_('When video ends:'),
			config.plugins.YouTube.onMovieEof,
			_('What to do when the video ends.')))
		configlist.append(getConfigListEntry(_('When playback stop:'),
			config.plugins.YouTube.onMovieStop,
			_('What to do when stop playback in videoplayer.')))
		configlist.append(getConfigListEntry(_('Login on startup:'),
			config.plugins.YouTube.login,
			 _('Log in to your YouTube account when plugin starts.\nThis needs to approve in the Google home page!')))
		configlist.append(getConfigListEntry(_('Download directory:'),
			config.plugins.YouTube.downloadDir,
			 _('Specify the directory where save downloaded video files.')))

		self['config'].list = configlist
		self['config'].l.setList(configlist)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('YouTube setup'))

	def ok(self):
		if self["config"].getCurrent()[1] == config.plugins.YouTube.downloadDir:
			from YouTubeDownload import YouTubeDirBrowser
			self.session.openWithCallback(self.downloadPath, YouTubeDirBrowser, 
				config.plugins.YouTube.downloadDir.value[2:-2])
		else:
			self.keySave()

	def downloadPath(self, res):
		if res:
			config.plugins.YouTube.downloadDir.setValue("'[" + res + "]'")

	def checkLoginSatus(self):
		if self.login != config.plugins.YouTube.login.value:
			self.login = config.plugins.YouTube.login.value
			if self.login:
				self.startAutentification()

	def startAutentification(self):
		if config.plugins.YouTube.refreshToken.value != '':
			self.session.openWithCallback(self.startupCallback,
			MessageBox, _('You already authorized access for this plugin to your YouTube account.\nDo you want to do it again to update access data?'))
		else:
			self.startupCallback(True)

	def startupCallback(self, answer):
		if answer:
			self.session.openWithCallback(self.warningCallback,
				MessageBox, _('To perform authentication will need in a web browser open Google home page, and enter the code!\nDo you currently have Internet access on the other device and we can continue?'))

	def warningCallback(self, answer):
		if not answer:
			self.login = config.plugins.YouTube.login.value = False
		else:
			from OAuth import OAuth
			self.splitTaimer = eTimer()
			self.splitTaimer.timeout.callback.append(self.splitTaimerStop)
			self.oauth = OAuth(YOUTUBE_API_CLIENT_ID, YOUTUBE_API_CLIENT_SECRET)
			userCode = str(self.oauth.get_user_code())
			msg = _('Go to %s\nAnd enter the code %s') % (str(self.oauth.verification_url), userCode)
			print "[YouTube] ", msg
			self.mbox = self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)
			self.splitTaimer.start(9000)

	def splitTaimerStop(self):
		self.splitTaimer.stop()
		# Here we waiting until the user enter a code
		refreshToken, retryInterval = self.oauth.get_new_token()
		if not refreshToken:
			self.splitTaimer.start(retryInterval * 1000)
		else:
			print "[YouTube] Get refresh token"
			if self.mbox:
				self.mbox.close()
			config.plugins.YouTube.refreshToken.value = refreshToken
			config.plugins.YouTube.refreshToken.save()
			del self.splitTaimer
			self.mbox = None
			self.oauth = None

