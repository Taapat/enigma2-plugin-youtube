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
		self['searchactions'] = ActionMap(['WizardActions', 'ColorActions', 'MenuActions'],
			{
				'back': self.close,
				'ok': self.ok,
				'red': self.close,
				'green': self.ok,
				'yellow': self.openKeyboard,
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
		searchEntry = [getConfigListEntry(_('Search'), self.searchValue)]
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
			print "[YouTube] Search:", searchValue
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
			self.close([self.searchType, searchValue, None], 'OpenSearch')

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
	def __init__(self, default = '', fixed_size = True, visible_width = False):
		ConfigText.__init__(self, default, fixed_size, visible_width)
		self.suggestions = GoogleSuggestions()
		self.suggestionsThread = None
		self.suggestionsThreadRunning = False
		self.suggestionsListActivated = False

	def suggestionsThreadStarted(self):
		if self.suggestionsThreadRunning:
			self.cancelSuggestionsThread()
		self.suggestionsThreadRunning = True

	def cancelSuggestionsThread(self):
		if self.suggestionsThread is not None:
			self.suggestionsThread.cancel()
		self.suggestionsThreadRunning = False

	def propagateSuggestions(self, suggestionsList):
		self.suggestionsListActivated = True
		self.cancelSuggestionsThread()
		if self.suggestionsWindow:
			self.suggestionsWindow.update(suggestionsList)

	def gotSuggestionsError(self, val):
		print "[YouTube] Error in get suggestions:", val

	def getSuggestions(self):
		if config.plugins.YouTube.searchRegion.value:
			self.suggestions.hl = config.plugins.YouTube.searchRegion.value
		self.suggestionsThreadStarted()
		self.suggestionsThread = SuggestionsQueryThread(self.suggestions, 
			self.value, self.propagateSuggestions, self.gotSuggestionsError)
		self.suggestionsThread.start()

	def handleKey(self, key):
		ConfigText.handleKey(self, key)
		if key in [KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT]:
			self.getSuggestions()

	def onSelect(self, session):
		ConfigText.onSelect(self, session)
		if session is not None:
			self.suggestionsWindow = session.instantiateDialog(YouTubeSuggestionsList, self)
			self.suggestionsWindow.getSelection()
			self.suggestionsWindow.hide()
		self.getSuggestions()

	def onDeselect(self, session):
		self.cancelSuggestionsThread()
		ConfigText.onDeselect(self, session)
		if self.suggestionsWindow:
			session.deleteDialog(self.suggestionsWindow)
			self.suggestionsWindow = None

	def suggestionListUp(self):
		if self.suggestionsWindow.getlistlenght() > 0:
			self.value = self.suggestionsWindow.up()

	def suggestionListDown(self):
		if self.suggestionsWindow.getlistlenght() > 0:
			self.value = self.suggestionsWindow.down()

	def deactivateSuggestionList(self):
		ret = False
		if self.suggestionsWindow is not None:
			self.suggestionsWindow.getSelection()
			self.getSuggestions()
			self.allmarked = True
			ret = True
		return ret


class YouTubeSuggestionsList(Screen):
	screenWidth = getDesktop(0).size().width()
	if screenWidth and screenWidth == 1920:
		skin = """<screen name="YouTubeSuggestionsList" position="center,175" size="900,409" \
				flags="wfNoBorder" zPosition="6" >
				<widget source="suggestionslist" render="Listbox" position="center,center" \
					size="900,409" scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent">
						{"template": [MultiContentEntryText(pos=(15,1), size=(870,45), \
							font=0, flags=RT_HALIGN_LEFT, text=0)],
						"fonts": [gFont("Regular",30)],
						"itemHeight": 45}
					</convert>
				</widget>
			</screen>"""
	else:
		skin = """<screen name="YouTubeSuggestionsList" position="center,center" size="600,273" \
				flags="wfNoBorder" zPosition="6" >
				<widget source="suggestionslist" render="Listbox" position="center,center" \
					size="600,273" scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent">
						{"template": [MultiContentEntryText(pos=(10,1), size=(580,30), \
							font=0, flags=RT_HALIGN_LEFT, text=0)],
						"fonts": [gFont("Regular",20)],
						"itemHeight": 30}
					</convert>
				</widget>
			</screen>"""

	def __init__(self, session, configTextWithGoogleSuggestion):
		Screen.__init__(self, session)
		self.list = []
		self['suggestionslist'] = List(self.list)
		self.configTextWithSuggestion = configTextWithGoogleSuggestion

	def update(self, suggestions):
		if suggestions and len(suggestions) > 0:
			if not self.shown:
				self.show()
			suggestions = fromstring(suggestions)
			if suggestions:
				self.list = []
				for suggestion in suggestions.findall('CompleteSuggestion'):
					name = None
					for element in suggestion:
						if element.attrib.has_key('data'):
							name = element.attrib['data'].encode('UTF-8')
						if name:
							self.list.append((name, None))
				if self.list:
					self['suggestionslist'].setList(self.list)
					self['suggestionslist'].setIndex(0)
		else:
			self.hide()

	def getlistlenght(self):
		return len(self.list)

	def up(self):
		if self.list and len(self.list) > 0:
			self['suggestionslist'].selectPrevious()
			return self.getSelection()

	def down(self):
		if self.list and len(self.list) > 0:
			self['suggestionslist'].selectNext()
			return self.getSelection()

	def getSelection(self):
		if self['suggestionslist'].getCurrent() is None:
			return None
		return self['suggestionslist'].getCurrent()[0]


class GoogleSuggestions():
	def __init__(self):
		self.hl = 'en'

	def getSuggestions(self, queryString):
		if not queryString:
			return None
		else:
			prepQuerry = '/complete/search?output=toolbar&client=youtube&xml=true&ds=yt&'
			if self.hl:
				prepQuerry = prepQuerry + 'hl=' + self.hl + '&'
			prepQuerry = prepQuerry + 'jsonp=self.getSuggestions&q='
			query = prepQuerry + quote(queryString)
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
						header = response.getheader('Content-Type',
							'text/xml; charset=ISO-8859-1')
						try:
							charset = header.split(';')[1].split('=')[1]
						except:
							charset = 'ISO-8859-1'
						data = data.decode(charset).encode('utf-8')
						connection.close()
						return data
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
