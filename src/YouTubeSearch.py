from httplib import HTTPConnection, CannotSendRequest, BadStatusLine
from threading import Lock, Thread
from urllib import quote
from xml.etree.cElementTree import fromstring

from enigma import ePythonMessagePump, getDesktop
from Screens.Screen import Screen
from Components.config import config, ConfigText, getConfigListEntry
from Components.config import KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText

from . import _


class YouTubeSearch(Screen, ConfigListScreen):
	screenWidth = getDesktop(0).size().width()
	if screenWidth and screenWidth == 1920:
		skin = """<screen position="center,100" size="945,555">
				<widget name="config" position="center,22" size="900,45" zPosition="2" \
					scrollbarMode="showNever" itemHeight="45" font="Regular;30" />
				<widget source="list" render="Listbox" position="center,75" size="900,409" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [MultiContentEntryText(pos=(15,1), size=(870,45), \
							font=0, flags=RT_HALIGN_LEFT, text=0)],
						"fonts": [gFont("Regular",30)],
						"itemHeight": 45}
					</convert>
				</widget>
				<ePixmap position="127,484" size="210,60" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<ePixmap position="center,484" size="210,60" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on" />
				<ePixmap position="608,484" size="210,60" pixmap="skin_default/buttons/yellow.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="127,485" zPosition="2" size="210,60" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
				<widget source="key_green" render="Label" position="center,485" zPosition="2" size="210,60" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
				<widget source="key_yellow" render="Label" position="608,485" zPosition="2" size="210,60" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
				<ePixmap position="847,502" size="53,38" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				</screen>"""
	else:
		skin = """<screen position="center,center" size="630,370">
				<widget name="config" position="center,15" size="600,30" zPosition="2" \
					scrollbarMode="showNever" />
				<widget source="list" render="Listbox" position="center,48" size="600,273" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [MultiContentEntryText(pos=(10,1), size=(580,30), \
							font=0, flags=RT_HALIGN_LEFT, text=0)],
						"fonts": [gFont("Regular",20)],
						"itemHeight": 30}
					</convert>
				</widget>
				<ePixmap position="85,323" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<ePixmap position="center,323" size="140,40" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on" />
				<ePixmap position="405,323" size="140,40" pixmap="skin_default/buttons/yellow.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="85,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget source="key_green" render="Label" position="center,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget source="key_yellow" render="Label" position="405,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<ePixmap position="565,335" size="35,25" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				</screen>"""

	def __init__(self, session, searchType):
		Screen.__init__(self, session)
		self.session = session
		self.searchType = searchType
		self.setTitle(_('YouTube search'))
		self['key_red'] = StaticText(_('Exit'))
		self['key_green'] = StaticText(_('Ok'))
		self['key_yellow'] = StaticText(_('Keyboard'))
		self['searchactions'] = ActionMap(['SetupActions', 'ColorActions', 'MenuActions'],
			{
				'cancel': self.close,
				'ok': self.ok,
				'red': self.close,
				'green': self.ok,
				'yellow': self.openKeyboard,
				'menu': self.openSetup
			}, -2)
		searchList = []
		ConfigListScreen.__init__(self, searchList, session)
		self.searchValue = GoogleSuggestionsConfigText(default = '', fixed_size = False,
			visible_width = False, updateSuggestions = self.updateSuggestions)
		self.setSearchEntry()
		self['list'] = List([])
		self.searchHistory = config.plugins.YouTube.searchHistory.value.split(',')
		for entry in self.searchHistory:
			searchList.append((entry, None))
		self['list'].setList(searchList)

	def setSearchEntry(self):
		searchEntry = [getConfigListEntry(_('Search'), self.searchValue)]
		self['config'].list = searchEntry
		self['config'].l.setList(searchEntry)
		self['config'].getCurrent()[1].getSuggestions()

	def updateSuggestions(self, suggestions):
		self['list'].setList(suggestions)
		self['list'].setIndex(0)

	def ok(self):
		selected = self['list'].getCurrent()[0]
		current = self['config'].getCurrent()[1]
		if selected:
			self['list'].setIndex(0)
			self.searchValue.value = selected
			self.setSearchEntry()
			current.getSuggestions()
		else:
			searchValue = self.searchValue.value
			print "[YouTube] Search:", searchValue
			if current.help_window.instance is not None:
				current.help_window.instance.hide()
			if searchValue != '' and config.plugins.YouTube.saveHistory.value:
				if searchValue in self.searchHistory:
					self.searchHistory.remove(searchValue)
				self.searchHistory.insert(1, searchValue)
				if len(self.searchHistory) > 20:
					self.searchHistory.pop()
				config.plugins.YouTube.searchHistory.value = ','.join(self.searchHistory)
				config.plugins.YouTube.searchHistory.save()
			self.close([self.searchType, searchValue, None], 'OpenSearch')

	def openSetup(self):
		from YouTubeUi import YouTubeSetup
		current = self['config'].getCurrent()[1]
		if current.help_window.instance is not None:
			current.help_window.instance.hide()
		self.session.openWithCallback(self.screenCallback, YouTubeSetup)

	def screenCallback(self, callback=None):
		current = self['config'].getCurrent()[1]
		if current.help_window.instance is not None:
			current.help_window.instance.show()

	def openKeyboard(self):
		from Screens.VirtualKeyBoard import VirtualKeyBoard
		self.session.openWithCallback(self.keyBoardCallback, VirtualKeyBoard,
			title = _("Search"), text = self.searchValue.value)

	def keyBoardCallback(self, name):
		if name:
			self.searchValue.value = name
			self['config'].getCurrent()[1].getSuggestions()


class SuggestionsQueryThread(Thread):
	def __init__(self, query, param, callback, errorback):
		Thread.__init__(self)
		self.query = query
		self.param = param
		self.callback = callback
		self.errorback = errorback
		self.canceled = False
		self.messages = ThreadQueue()
		self.messagePump = ePythonMessagePump()
		self.messagePump.recv_msg.get().append(self.finished)

	def cancel(self):
		self.canceled = True

	def run(self):
		if self.param:
			try:
				suggestions = self.query.getSuggestions(self.param)
				self.messages.push((suggestions, self.callback))
				self.messagePump.send(0)
			except Exception, ex:
				self.messages.push((ex, self.errorback))
				self.messagePump.send(0)

	def finished(self, val):
		if not self.canceled:
			message = self.messages.pop()
			message[1](message[0])


class GoogleSuggestionsConfigText(ConfigText):
	def __init__(self, default, fixed_size, visible_width, updateSuggestions):
		ConfigText.__init__(self, default, fixed_size, visible_width)
		self.updateSuggestions = updateSuggestions
		self.suggestions = GoogleSuggestions()
		if config.plugins.YouTube.searchRegion.value:
			self.suggestions.hl = config.plugins.YouTube.searchRegion.value.lower()
		self.suggestionsThread = None
		self.suggestionsThreadRunning = False

	def cancelSuggestionsThread(self):
		if self.suggestionsThread is not None:
			self.suggestionsThread.cancel()
		self.suggestionsThreadRunning = False

	def propagateSuggestions(self, suggestionsList):
		self.cancelSuggestionsThread()
		if suggestionsList and len(suggestionsList) > 0:
			suggestionsList = fromstring(suggestionsList)
			if suggestionsList:
				suggestions = [('', None)]
				for suggestion in suggestionsList.findall('CompleteSuggestion'):
					for element in suggestion:
						if element.attrib.has_key('data'):
							name = element.attrib['data'].encode('UTF-8')
						if name:
							suggestions.append((name, None))
				if len(suggestions) > 1:
					self.updateSuggestions(suggestions)

	def gotSuggestionsError(self, val):
		print "[YouTube] Error in get suggestions:", val

	def getSuggestions(self):
		if self.suggestionsThreadRunning:
			self.cancelSuggestionsThread()
		self.suggestionsThreadRunning = True
		self.suggestionsThread = SuggestionsQueryThread(self.suggestions,
			self.value, self.propagateSuggestions, self.gotSuggestionsError)
		self.suggestionsThread.start()

	def handleKey(self, key):
		ConfigText.handleKey(self, key)
		if key in [KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT]:
			self.getSuggestions()

	def onSelect(self, session):
		ConfigText.onSelect(self, session)
		self.getSuggestions()

	def onDeselect(self, session):
		self.cancelSuggestionsThread()
		ConfigText.onDeselect(self, session)


class GoogleSuggestions():
	def __init__(self):
		self.hl = 'en'

	def getSuggestions(self, queryString):
		if not queryString:
			return None
		else:
			query = '/complete/search?output=toolbar&client=youtube&xml=true&ds=yt'
			if self.hl:
				query += '&hl=' + self.hl
			query += '&jsonp=self.getSuggestions&q=' + quote(queryString)
			try:
				connection = HTTPConnection('google.com')
				connection.request('GET', query, '', {'Accept-Encoding': 'UTF-8'})
			except (CannotSendRequest, gaierror, error):
				print "[YouTube] Can not send request for suggestions"
			else:
				try:
					response = connection.getresponse()
				except BadStatusLine:
					print "[YouTube] Can not get a response from google"
				else:
					if response.status == 200:
						data = response.read()
						try:
							charset = response.getheader('Content-Type',
								'text/xml; charset=ISO-8859-1').rsplit('=')[1]
						except:
							charset = 'ISO-8859-1'
						connection.close()
						return data.decode(charset).encode('utf-8')
			if connection:
				connection.close()
			return None


class ThreadQueue:
	def __init__(self):
		self.__list = [ ]
		self.__lock = Lock()

	def push(self, val):
		lock = self.__lock
		lock.acquire()
		self.__list.append(val)
		lock.release()

	def pop(self):
		lock = self.__lock
		lock.acquire()
		ret = self.__list.pop()
		lock.release()
		return ret

