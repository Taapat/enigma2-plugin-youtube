from httplib import HTTPConnection, CannotSendRequest, BadStatusLine
from threading import Lock, Thread
from urllib import quote
from xml.etree.cElementTree import fromstring as cet_fromstring

from enigma import ePythonMessagePump
from Screens.Screen import Screen
from Components.config import config, ConfigText
from Components.config import KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT
from Components.Sources.List import List


class SuggestionsQueryThread(Thread):
	def __init__(self, query, param, callback, errorback):
		Thread.__init__(self)
		self.messagePump = ePythonMessagePump()
		self.messages = ThreadQueue()
		self.query = query
		self.param = param
		self.callback = callback
		self.errorback = errorback
		self.canceled = False
		self.messagePump.recv_msg.get().append(self.finished)

	def cancel(self):
		self.canceled = True

	def run(self):
		if self.param not in (None, ''):
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
		self.suggestionsThread = SuggestionsQueryThread(self.suggestions, self.value, self.propagateSuggestions, self.gotSuggestionsError)
		self.suggestionsThread.start()

	def handleKey(self, key):
		ConfigText.handleKey(self, key)
		if key in [KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT]:
			self.getSuggestions()

	def onSelect(self, session):
		ConfigText.onSelect(self, session)
		if session is not None:
			self.suggestionsWindow = session.instantiateDialog(SuggestionsList, self)
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

	def suggestionListPageDown(self):
		if self.suggestionsWindow.getlistlenght() > 0:
			self.value = self.suggestionsWindow.pageDown()

	def suggestionListPageUp(self):
		if self.suggestionsWindow.getlistlenght() > 0:
			self.value = self.suggestionsWindow.pageUp()

	def deactivateSuggestionList(self):
		ret = False
		if self.suggestionsWindow is not None:
			self.suggestionsWindow.getSelection()
			self.getSuggestions()
			self.allmarked = True
			ret = True
		return ret


class SuggestionsList(Screen):
	skin = """
		<screen name="SuggestionsList" position="center,center" size="600,280" \
			flags="wfNoBorder" zPosition="6" >
			<widget source="suggestionslist" render="Listbox" position="center,center" \
				size="600,280" scrollbarMode="showOnDemand" >
				<convert type="TemplatedMultiContent">
				{
					"template": [MultiContentEntryText(pos=(10,1), size=(340,24), \
						font=0, flags=RT_HALIGN_LEFT, text=0)],
					"fonts": [gFont("Regular",20), gFont("Regular",18)],
					"itemHeight": 25
				}
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
			suggestions_tree = cet_fromstring( suggestions )
			if suggestions_tree:
				self.list = []
				suggestlist = []
				for suggestion in suggestions_tree.findall('CompleteSuggestion'):
					name = None
					for subelement in suggestion:
						if subelement.attrib.has_key('data'):
							name = subelement.attrib['data'].encode('UTF-8')
						if name:
							suggestlist.append(name)
				if len(suggestlist):
					for entry in suggestlist:
						self.list.append((entry, None))
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

	def pageUp(self):
		if self.list and len(self.list) > 0:
			self['suggestionslist'].selectPrevious()
			return self.getSelection()

	def pageDown(self):
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
		self.conn = None

	def getSuggestions(self, queryString):
		prepQuerry = '/complete/search?output=toolbar&client=youtube&xml=true&ds=yt&'
		if self.hl is not None:
			prepQuerry = prepQuerry + 'hl=' + self.hl + '&'
		prepQuerry = prepQuerry + 'jsonp=self.getSuggestions&q='
		if queryString is not '':
			query = prepQuerry + quote(queryString)
			try:
				self.conn = HTTPConnection('google.com')
				self.conn.request('GET', query, '', {'Accept-Encoding': 'UTF-8'})
			except (CannotSendRequest, gaierror, error):
				self.conn.close()
				print "[YouTube] Can not send request for suggestions"
				return None
			else:
				try:
					response = self.conn.getresponse()
				except BadStatusLine:
					self.conn.close()
					print "[YouTube] Can not get a response from google"
					return None
				else:
					if response.status == 200:
						data = response.read()
						header = response.getheader('Content-Type', 'text/xml; charset=ISO-8859-1')
						charset = 'ISO-8859-1'
						try:
							charset = header.split(';')[1].split('=')[1]
						except:
							pass
						data = data.decode(charset).encode('utf-8')
						self.conn.close()
						return data
					else:
						self.conn.close()
						return None
		else:
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
