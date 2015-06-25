import os
from twisted.web.client import downloadPage
from httplib2 import Http

from enigma import ePicLoad, eServiceReference, eTimer
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.config import config, ConfigSelection, ConfigSubsection, \
	ConfigText, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from . import _
from GoogleSuggestions import GoogleSuggestionsConfigText


YouTube_build = None
YouTube_OAuth2Credentials = None
YouTube_YoutubeDL = None

config.plugins.YouTube = ConfigSubsection()
config.plugins.YouTube.login = ConfigYesNo(default = False)
config.plugins.YouTube.searchRegion = ConfigSelection(
	[(None, _('All')),
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
config.plugins.YouTube.safeSearch = ConfigYesNo(default = False)
config.plugins.YouTube.saveHistory = ConfigYesNo(default = True)
config.plugins.YouTube.onMovieEof = ConfigSelection(default = 'quit', choices = [
	('quit', _('Return to list')), ('ask', _('Ask user')),
	('playnext', _('Play next')), ('repeat', _('Repeat'))])
config.plugins.YouTube.onMovieStop = ConfigSelection(default = 'ask', choices = [
	('ask', _('Ask user')), ('quit', _('Return to list'))])

config.plugins.YouTube.searchHistory = ConfigText(default='')
config.plugins.YouTube.refreshToken = ConfigText(default='')

API_KEY = 'AIzaSyCyIlbb0FIwoieEZ9RTShMVkRMisu-ZX0k'
YOUTUBE_API_CLIENT_ID = '411447027255-vbgs05u1o3m8mpjs2vcd04afrg60drba.apps.googleusercontent.com'
YOUTUBE_API_CLIENT_SECRET = 'fYE-8T3qf4DrLPLv3NTgvjna'


class YouTubePlayer(MoviePlayer):
	def __init__(self, session, service):
		MoviePlayer.__init__(self, session, service)
		self.skinName = 'MoviePlayer'

	def leavePlayer(self):
		if config.plugins.YouTube.onMovieStop.value == 'ask':
			title = _('Stop playing this movie?')
			list = (
					(_('Yes'), 'quit'),
					(_('Yes, but play next video'), 'playnext'),
					(_('Yes, but play previous video'), 'playprev'),
					(_('No, but play video again'), 'repeat'),
					(_('No'), 'continue'),
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

	def showMovies(self):
		pass


class YouTubeMain(Screen):
	skin = """
		<screen position="center,center" size="630,370">
			<widget name="text" position="center,0" size="600,30" halign="center" font="Regular;24" />
			<widget source="list" render="Listbox" position="center,32" size="600,288" \
				scrollbarMode="showOnDemand" >
				<convert type="TemplatedMultiContent" >
				{
					"template": [
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
					"itemHeight": 72
				}
				</convert>
			</widget>
			<ePixmap position="114,323" size="140,40" pixmap="skin_default/buttons/red.png" \
				transparent="1" alphatest="on" />
			<ePixmap position="374,323" size="140,40" pixmap="skin_default/buttons/green.png" \
				transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="114,328" zPosition="2" size="140,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
			<widget source="key_green" render="Label" position="374,328" zPosition="2" size="140,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
			<widget name="thumbnail" position="0,0" size="100,72" /> # Thumbnail size in list
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_('YouTube'))
		self['key_red'] = StaticText('')
		self['key_green'] = StaticText('')
		self['actions'] = ActionMap(['SetupActions', 'ColorActions', 'MenuActions'],
			{
				'cancel': self.cancel,
				'ok': self.ok,
				'red': self.cancel,
				'green': self.ok,
				'menu': self.openSetup
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
		self.value = [None, None]
		self.selectedIndex = None
		self.youtube = None
		self.subscriptionsIndex = None
		self.subscriptionsList = None
		self.isAuth = False
		self.onLayoutFinish.append(self.layoutFinish)
		self.onClose.append(self.cleanVariables)

	def layoutFinish(self):
		defThumbnail = resolveFilename(SCOPE_PLUGINS,
			'Extensions/YouTube/icon.png')
		self.decodeThumbnail('default', defThumbnail)
		self.splitTaimer.start(1)

	def cleanVariables(self):
		del self.thumbnailTaimer
		del self.splitTaimer
		self.youtube = None
		self.thumbnails = None
		self.entryList = None
		self.subscriptionsList = None

	def createMainList(self):
		self.list = 'main'
		self.value = [None, None]
		self.text = _('Choose what you want to do')
		self.entryList = [(
				'Search',           # Id
				None,               # Thumbnail url
				None,               # Thumbnail
				_('Search videos'), # Title
				'',                 # Views
				''                  # Duration
			),(
				'PubFeeds', None, None,
				_('Public feeds'), '', ''
			)]
		if config.plugins.YouTube.login.value and config.plugins.YouTube.refreshToken.value != '':
			self.entryList.append(('MyFeeds', None, None,
				_('My feeds'), '', ''))
		self.setEntryList()

	def createFeedList(self):
		self.list = 'feeds'
		self.value = [None, None]
		self.text = _('Public feeds')
		self.entryList = [(
				'top rated', None, None,
				_('Top rated feeds'), '', ''
			),(
				'most viewed', None, None,
				_('Most viewed feeds'), '', ''
			),(
				'most recent', None, None,
				_('Most recent feeds'), '', ''
			),(
				'HD videos', None, None,
				_('HD videos feeds'), '', ''
			),(
				'embedded videos', None, None,
				_('Embedded videos feeds'), '', ''
			),(
				'episodes of shows', None, None,
				_('Episodes of shows'), '', ''
			),(
				'movies', None, None,
				_('Movies feeds'), '', ''
			)]
		self.setEntryList()

	def createMyFeedList(self):
		self.list = 'myfeeds'
		self.value = [None, None]
		self.text = _('My feeds')
		self.entryList = [(
				'my subscriptions', None, None,
				_('My subscriptions'), '', ''
			),(
				'my watch later', None, None,
				_('My watch later'), '', ''
			),(
				'my watch history', None, None,
				_('My watch history'), '', ''
			),(
				'my liked videos', None, None,
				_('My liked videos'), '', ''
			),(
				'my favorites', None, None,
				_('My favorites'), '', ''
			),(
				'my uploads', None, None,
				_('My uploads'), '', ''
			)]
		self.setEntryList()

	def screenCallback(self, value = None, action = None):
		if not action:
			self.list = 'main'
		else:
			self.value = value
			self.action = action
			if action == 'createSearchEntryList':
				text = _('Download search results. Please wait...')
			elif action in ('OpenFeeds', 'OpenMyFeeds', 'OpenSubscription'):
				text = _('Download feed entries. Please wait...')
			else: # play video
				text = _('Extract video url. Please wait...')
			self['text'].setText(text)
			self['list'].setList([])
			self['key_red'].setText('')
			self['key_green'].setText('')
			self.splitTaimer.start(1)

	def splitTaimerStop(self):
		self.splitTaimer.stop()
		if self.action == 'startup':
			global YouTube_build, YouTube_OAuth2Credentials, YouTube_YoutubeDL
			from apiclient.discovery import build as YouTube_build
			from oauth2client.client import OAuth2Credentials as YouTube_OAuth2Credentials
			from youtube_dl import YoutubeDL as YouTube_YoutubeDL
			self.createMainList()
		elif self.action == 'playVideo':
			videoUrl = self.getVideoUrl()
			if videoUrl:
				ref = eServiceReference(4097, 0, videoUrl)
				ref.setName(self.value[1])
				print "[YouTube] Play:", videoUrl
				self.session.openWithCallback(self.playCallback, YouTubePlayer, ref)
		else:
			entryList = self.createEntryList()
			if not entryList:
				self.session.open(MessageBox, 
					_('Not found any entry!\nMaybe try change the settings?'), 
					MessageBox.TYPE_INFO, timeout = 5)
				self.createMainList()
			else:
				if self.action == 'OpenSubscription':
					self.subscriptionsList = self.entryList
				self.entryList = entryList
				if self.action == 'createSearchEntryList':
					self.list = 'search'
					self.text = self.value[1]
					self.setEntryList()
				elif self.action == 'OpenFeeds':
					self.list = 'openfeeds'
					self.text = self.value[1]
					self.setEntryList()	
				elif self.action == 'OpenMyFeeds':
					self.list = 'openmyfeeds'
					self.text = self.value[1]
					self.setEntryList()
				elif self.action == 'OpenSubscription':
					self.list = 'opensubscription'
					self.text = self.value[1]
					self.setEntryList()

	def setEntryList(self):
		self['text'].setText(self.text)
		self['list'].setList(self.entryList)
		if self.selectedIndex:
			self['list'].setIndex(self.selectedIndex)
		self['key_red'].setText(_('Exit'))
		self['key_green'].setText(_('Open'))
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
						'Extensions/YouTube/' + entryId + '.png')
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
					entryList = self.entryList[count]
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
							entryList[5]  # Duration
						)
				count += 1
			self['list'].updateList(self.entryList)

	def playCallback(self, action=None):
		self.setEntryList()
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
			title = _('What do you want to do?')
			list = (
					(_('Quit'), 'quit'),
					(_('Play next video'), 'playnext'),
					(_('Play previous video'), 'playprev'),
					(_('Play video again'), 'repeat'),
				)
			self.session.openWithCallback(self.playCallback,
				ChoiceBox, title = title, list = list)

	def ok(self):
		current = self['list'].getCurrent()
		if current:
			print "[YouTube] Selected:", current[0]
			if current[0] == 'Search':
				self.session.openWithCallback(self.screenCallback, YouTubeSearch)
			elif current[0] == 'PubFeeds':
				self.createFeedList()
			elif current[0] == 'MyFeeds':
				self.createMyFeedList()
			elif self.list == 'feeds':
				self.screenCallback([current[0], current[3]], 'OpenFeeds')
			elif self.list == 'myfeeds':
				self.screenCallback([current[0], current[3]], 'OpenMyFeeds')
			elif self.list == 'openmyfeeds':
				self.subscriptionsIndex = self['list'].index
				self.screenCallback([current[0], current[3]], 'OpenSubscription')
			else: # Play video
				self.selectedIndex = self['list'].index
				self.screenCallback([current[0], current[3]], 'playVideo')

	def getVideoUrl(self):
		VIDEO_FMT_PRIORITY_MAP = {
				1 : '38', #MP4 Original (HD)
				2 : '37', #MP4 1080p (HD)
				3 : '22', #MP4 720p (HD)
				4 : '18', #MP4 360p
				5 : '35', #FLV 480p
				6 : '34' #FLV 360p
 			}
		watch_url = 'http://www.youtube.com/watch?v=%s' % self.value[0]

		ytdl = YouTube_YoutubeDL(params = {
				'youtube_include_dash_manifest': False, 
				'format': '/'.join(VIDEO_FMT_PRIORITY_MAP.itervalues()), 
				'nocheckcertificate': True
			})

		try:
			entry = ytdl.extract_info(watch_url, download=False, ie_key='Youtube')
		except:
			print "[YouTube] Error in extract info"
			return None

		if 'entries' in entry: # Can be a playlist or a list of videos
			entry = entry['entries'][0] #TODO handle properly
		return str(entry.get('url'))

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

	def createEntryList(self):
		refreshToken = config.plugins.YouTube.refreshToken.value
		if not self.youtube or (not self.isAuth and \
			refreshToken and config.plugins.YouTube.login.value):
			if refreshToken:
				httpCredentials = YouTube_OAuth2Credentials(
						access_token = None,
						client_id = YOUTUBE_API_CLIENT_ID,
						client_secret = YOUTUBE_API_CLIENT_SECRET,
						refresh_token = refreshToken,
						token_expiry = None,
						token_uri = 'https://accounts.google.com/o/oauth2/token',
						user_agent = None
					).authorize(Http())
				try:
					self.youtube = YouTube_build('youtube', 'v3', 
						developerKey = API_KEY, http = httpCredentials)
					self.isAuth = True
				except:
					self.youtube = YouTube_build('youtube', 'v3', developerKey = API_KEY)
					self.isAuth = False
			else:
				self.youtube = YouTube_build('youtube', 'v3', developerKey = API_KEY)

		order = 'date'
		q = ''
		videoDefinition = videoEmbeddable = videoType = 'any'

		if self.action == 'createSearchEntryList':
			order = config.plugins.YouTube.searchOrder.value
			q = self.value[1]
		elif self.action == 'OpenFeeds':
			if self.value[0] == 'top rated':
				order = 'rating'
			elif self.value[0] == 'most viewed':
				order = 'viewCount'
			elif self.value[0] == 'HD videos':
				videoDefinition = 'high'
			elif self.value[0] == 'embedded videos':
				videoEmbeddable = 'true'
			elif self.value[0] == 'episodes of shows':
				videoType = 'episode'
			elif self.value[0] == 'movies':
				videoType = 'movie'
		elif self.action == 'OpenMyFeeds':
			if not self.isAuth:
				return None
			elif self.value[0] == 'my watch later':
				playlist = 'watchLater'
			elif self.value[0] == 'my watch history':
				playlist = 'watchHistory'
			elif self.value[0] == 'my liked videos':
				playlist = 'likes'
			elif self.value[0] == 'my favorites':
				playlist = 'favorites'
			elif self.value[0] == 'my uploads':
				playlist = 'uploads'
		elif self.action == 'OpenSubscription':
			channel = self.value[0]

		if config.plugins.YouTube.safeSearch.value:
			safeSearch = 'strict'
		else:
			safeSearch = 'none'
		videos = []

		if self.action in ('OpenMyFeeds', 'OpenSubscription'):
			channels = []
			if self.value[0] == 'my subscriptions':
				searchResponse = self.youtube.subscriptions().list(
						mine=True,
						part='snippet'
					).execute()
				for result in searchResponse.get('items', []):
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
					videos.append((Id, Thumbnail, None, Title, '', ''))
				return videos

			elif self.action != 'OpenSubscription':
				searchResponse = self.youtube.channels().list(
						mine=True,
						part='contentDetails'
					).execute()
				for result in searchResponse.get('items', []):
					channel = result['contentDetails']['relatedPlaylists'][playlist]

			if len(channel) == 0:
				return None
			try:
				searchResponse = self.youtube.playlistItems().list(
						playlistId=channel,
						part='snippet',
						maxResults = 24
					).execute()
			except:
				return None
			for result in searchResponse.get('items', []):
				videos.append(result['snippet']['resourceId']['videoId'])

		else:
			searchResponse = self.youtube.search().list(
					part = 'id',
					maxResults = 24,
					order = order,
					q = q,
					regionCode = config.plugins.YouTube.searchRegion.value,
					safeSearch = safeSearch,
					type = 'video',
					videoDefinition = videoDefinition,
					videoEmbeddable = videoEmbeddable,
					videoType = videoType
				).execute()
			for result in searchResponse.get('items', []):
				videos.append(result['id']['videoId'])

		if len(videos) == 0:
			return None

		searchResponse = self.youtube.videos().list(
			id=','.join(videos),
			part='id,snippet,statistics,contentDetails'
			).execute()

		videos = []
		for result in searchResponse.get('items', []):
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
			videos.append((Id, Thumbnail, None, Title, Views, Duration))
		return videos

	def cancel(self):
		self.selectedIndex = None
		if self.list == 'openfeeds':
			self.createFeedList()
		elif self.list == 'openmyfeeds':
			self.createMyFeedList()
		elif self.list == 'opensubscription':
			self.selectedIndex = self.subscriptionsIndex
			self.entryList = self.subscriptionsList
			self.list = 'openmyfeeds'
			self.setEntryList()
		elif self.list != 'main':
			self.createMainList()
		else:
			self.close()

	def openSetup(self):
		self.session.openWithCallback(self.configScreenCallback, YouTubeSetup)

	def configScreenCallback(self, callback=None):
		if self.list == 'main':
			self.createMainList()

class YouTubeSearch(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="630,370">
			<widget source="list" render="Listbox" position="center,50" size="600,273" \
				scrollbarMode="showOnDemand" >
				<convert type="TemplatedMultiContent" >
				{
					"template": [MultiContentEntryText(pos=(10, 1), size=(580, 30), \
							font=0, flags=RT_HALIGN_LEFT, text=0)],
					"fonts": [gFont("Regular",20)],
					"itemHeight": 30
				}
				</convert>
			</widget>
			<widget name="config" position="center,15" size="600,30" zPosition="2" \
				scrollbarMode="showNever" />
			<ePixmap position="114,323" size="140,40" pixmap="skin_default/buttons/red.png" \
				transparent="1" alphatest="on" />
			<ePixmap position="374,323" size="140,40" pixmap="skin_default/buttons/green.png" \
				transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="114,328" zPosition="2" size="140,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
			<widget source="key_green" render="Label" position="374,328" zPosition="2" size="140,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.setTitle(_('YouTube serch'))
		self['key_red'] = StaticText(_('Exit'))
		self['key_green'] = StaticText(_('Ok'))
		self['searchactions'] = ActionMap(['WizardActions', 'ColorActions', 'MenuActions'],
			{
				'back': self.close,
				'ok': self.ok,
				'red': self.close,
				'green': self.ok,
				'up': self.keyUp,
				'down': self.keyDown,
				'menu': self.openSetup
			}, -2)
		searchList = []
		ConfigListScreen.__init__(self, searchList, session)
		self.searchValue = GoogleSuggestionsConfigText(default = '', fixed_size = False)
		self.setSearchEntry()
		self['list'] = List([])
		self.searchHistory = config.plugins.YouTube.searchHistory.value.split(',')
		for entry in self.searchHistory:
			searchList.append((entry, None))
		self['list'].setList(searchList)

	def setSearchEntry(self):
		searchEntry = [getConfigListEntry(_('Search term'), self.searchValue)]
		self['config'].list = searchEntry
		self['config'].l.setList(searchEntry)
		self['config'].getCurrent()[1].getSuggestions()

	def keyUp(self):
		if self['config'].getCurrent()[1].suggestionsListActivated:
			self['config'].getCurrent()[1].suggestionListUp()
			self['config'].invalidateCurrent()
		else:
			self['list'].selectPrevious()

	def keyDown(self):
		if self['config'].getCurrent()[1].suggestionsListActivated:
			self['config'].getCurrent()[1].suggestionListDown()
			self['config'].invalidateCurrent()
		else:
			self['list'].selectNext()

	def ok(self):
		selected = self['list'].getCurrent()
		if selected[0]:
			self['list'].setIndex(0)
			self.searchValue.value = selected[0]
			self.setSearchEntry()
		else:
			searchValue = self.searchValue.value
			print "[YouTube] Selected:", searchValue
			current = self['config'].getCurrent()[1]
			if current.help_window.instance is not None:
				current.help_window.instance.hide()
			if current.suggestionsWindow.instance is not None:
				current.suggestionsWindow.instance.hide()
			if searchValue != '' and config.plugins.YouTube.saveHistory.value:
				if searchValue in self.searchHistory:
					self.searchHistory.remove(searchValue)
				self.searchHistory.insert(1, searchValue)
				if len(self.searchHistory) > 20:
					self.searchHistory.pop()
				config.plugins.YouTube.searchHistory.value = ','.join(self.searchHistory)
				config.plugins.YouTube.searchHistory.save()
			self.close([None, searchValue], 'createSearchEntryList')

	def openSetup(self):
		current = self['config'].getCurrent()[1]
		if current.help_window.instance is not None:
			current.help_window.instance.hide()
		if current.suggestionsWindow.instance is not None:
			current.suggestionsWindow.instance.hide()
		self.session.openWithCallback(self.screenCallback, YouTubeSetup)

	def screenCallback(self, callback=None):
		current = self['config'].getCurrent()[1]
		if current.help_window.instance is not None:
			current.help_window.instance.show()
		if current.suggestionsWindow.instance is not None:
			current.suggestionsWindow.instance.show()

class YouTubeSetup(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.skinName = ['YouTubeSetup', 'Setup']
		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('Save'))
		self['description'] = Label('')
		self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'],
			{
				'cancel': self.keyCancel,
				'red': self.keyCancel,
				'ok': self.keySave,
				'green': self.keySave
			}, -2)
		self.mbox = None
		self.login = config.plugins.YouTube.login.value
		configlist = []
		ConfigListScreen.__init__(self, configlist, session=session,
			on_change = self.checkLoginSatus)

		configlist.append(getConfigListEntry(_('Login on startup:'),
			config.plugins.YouTube.login,
			 _('Log in to your YouTube account when plugin starts.\nThis needs to approve in the Google home page!')))
		configlist.append(getConfigListEntry(_('Search region:'),
			config.plugins.YouTube.searchRegion,
			 _('Return search results for the specified country.')))
		configlist.append(getConfigListEntry(_('Sort search results by:'),
			config.plugins.YouTube.searchOrder,
			_('Order in which search results will be displayed.')))
		configlist.append(getConfigListEntry(_('Exclude restricted content:'),
			config.plugins.YouTube.safeSearch,
			_('Try to exclude all restricted content from the search result.')))
		configlist.append(getConfigListEntry(_('Save search history:'),
			config.plugins.YouTube.saveHistory, 
			_('Save your search value in the history, when search completed.')))
		configlist.append(getConfigListEntry(_('When video ends:'),
			config.plugins.YouTube.onMovieEof, 
			_('What to do when the video ends.')))
		configlist.append(getConfigListEntry(_('When playback stop:'),
			config.plugins.YouTube.onMovieStop, 
			_('What to do when stop playback in videoplayer.')))

		self['config'].list = configlist
		self['config'].l.setList(configlist)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('YouTube setup'))

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
				MessageBox, _('To perform authentication will need in a web browser open Google home page, and enter the code!\nIf you continue, then you can not stop until the authentication will not be complete!\nDo you currently have Internet access on the other device and we can continue?'))

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
		# Here we waiting until the user enter a code
		self.splitTaimer.stop()
		refreshToken = self.oauth.get_new_token()
		print "[YouTube] Get refresh token"
		if self.mbox:
			self.mbox.close()
		config.plugins.YouTube.refreshToken.value = refreshToken
		config.plugins.YouTube.refreshToken.save()
		del self.splitTaimer
		self.mbox = None
		self.oauth = None

