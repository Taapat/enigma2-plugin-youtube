from httplib import HTTPConnection
from threading import Thread
from urllib import quote
from xml.etree.cElementTree import fromstring

from enigma import ePoint, getDesktop
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.config import config, ConfigText, getConfigListEntry
from Components.config import KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText

from . import _


class YouTubeVirtualKeyBoard(VirtualKeyBoard):
	def __init__(self, session, text):
		if text:
			title = text
		else:
			title = _('Search')
		VirtualKeyBoard.__init__(self, session, title=title, text=text)
		self.skinName = ['YouTubeVirtualKeyBoard', 'VirtualKeyBoard']
		self.searchValue = GoogleSuggestionsConfigText(default=text,
			updateSuggestions=self.updateSuggestions)

	#  Replace okClicked on OpenPLi develop
	def processSelect(self):
		VirtualKeyBoard.processSelect(self)
		self.tryGetSuggestions()

	def okClicked(self):
		VirtualKeyBoard.okClicked(self)
		self.tryGetSuggestions()

	def tryGetSuggestions(self):
		newSearchValue = self['text'].getText()
		if self.searchValue.value != newSearchValue:
			self.searchValue.value = newSearchValue
			self.searchValue.getSuggestions()

	def updateSuggestions(self, suggestions):
		if 'prompt' in self:
			if len(suggestions) > 1:
				self['prompt'].setText(', '.join(x[0] for x in suggestions[1:]))
			else:
				self['prompt'].setText('')
		elif 'header' in self:
			if len(suggestions) > 1:
				self['header'].setText(', '.join(x[0] for x in suggestions[1:]))
			else:
				self['header'].setText('')


class YouTubeSearch(Screen, ConfigListScreen):
	screenWidth = getDesktop(0).size().width()
	if screenWidth and screenWidth == 1280:
		skin = """<screen position="center,150" size="630,370">
				<widget name="config" position="15,15" size="600,30" zPosition="2" \
					scrollbarMode="showNever" />
				<widget source="list" render="Listbox" position="15,48" size="600,273" \
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
				<ePixmap position="245,323" size="140,40" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on" />
				<ePixmap position="405,323" size="140,40" pixmap="skin_default/buttons/yellow.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="85,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget source="key_green" render="Label" position="245,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget source="key_yellow" render="Label" position="405,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<ePixmap position="565,335" size="35,25" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				<widget name="HelpWindow" position="400,540" size="1,1" zPosition="5" \
					pixmap="skin_default/vkey_icon.png" transparent="1" alphatest="on" />
			</screen>"""
	elif screenWidth and screenWidth == 1920:
		skin = """<screen position="center,225" size="945,555">
				<widget name="config" position="22,22" size="900,45" zPosition="2" \
					scrollbarMode="showNever" itemHeight="45" font="Regular;30" />
				<widget source="list" render="Listbox" position="22,75" size="900,409" \
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
				<ePixmap position="367,484" size="210,60" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on" />
				<ePixmap position="608,484" size="210,60" pixmap="skin_default/buttons/yellow.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="127,485" zPosition="2" size="210,60" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
				<widget source="key_green" render="Label" position="367,485" zPosition="2" size="210,60" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
				<widget source="key_yellow" render="Label" position="608,485" zPosition="2" size="210,60" \
					valign="center" halign="center" font="Regular;33" transparent="1" />
				<ePixmap position="847,502" size="53,38" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				<widget name="HelpWindow" position="600,810" size="1,1" zPosition="5" \
					pixmap="skin_default/vkey_icon.png" transparent="1" alphatest="on" />
			</screen>"""
	else:
		skin = """<screen position="center,55" size="630,370">
				<widget name="config" position="15,15" size="600,30" zPosition="2" \
					scrollbarMode="showNever" />
				<widget source="list" render="Listbox" position="15,48" size="600,273" \
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
				<ePixmap position="245,323" size="140,40" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on" />
				<ePixmap position="405,323" size="140,40" pixmap="skin_default/buttons/yellow.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="85,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget source="key_green" render="Label" position="245,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<widget source="key_yellow" render="Label" position="405,328" zPosition="2" size="140,30" \
					valign="center" halign="center" font="Regular;22" transparent="1" />
				<ePixmap position="565,335" size="35,25" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				<widget name="HelpWindow" position="160,440" size="1,1" zPosition="5" \
					pixmap="skin_default/vkey_icon.png" transparent="1" alphatest="on" />
			</screen>"""

	def __init__(self, session, curList):
		Screen.__init__(self, session)
		self.session = session
		self.curList = curList
		self.setTitle(_('YouTube search'))
		self['key_red'] = StaticText(_('Exit'))
		self['key_green'] = StaticText(_('Ok'))
		self['key_yellow'] = StaticText(_('Keyboard'))
		self['HelpWindow'] = Pixmap()
		self['searchactions'] = ActionMap(['SetupActions', 'ColorActions', 'MenuActions'],
			{
				'cancel': self.close,
				'ok': self.ok,
				'red': self.close,
				'green': self.ok,
				'yellow': self.openKeyboard,
				'menu': self.openMenu
			}, -2)
		searchList = []
		ConfigListScreen.__init__(self, searchList, session)
		self.searchValue = GoogleSuggestionsConfigText(default='',
			updateSuggestions=self.updateSuggestions)
		self.setSearchEntry()
		self['list'] = List([])
		self.searchHistory = config.plugins.YouTube.searchHistoryDict[self.curList].value
		for entry in self.searchHistory:
			searchList.append((entry, None))
		if not searchList:
			searchList = [('', None)]
		self['list'].setList(searchList)
		self.onLayoutFinish.append(self.moveHelpWindow)

	def moveHelpWindow(self):
		helpwindowpos = self["HelpWindow"].getPosition()
		self['config'].getCurrent()[1].help_window.instance.move(ePoint(helpwindowpos[0],
			helpwindowpos[1]))

	def setSearchEntry(self):
		searchEntry = [getConfigListEntry(_('Search'), self.searchValue)]
		self['config'].list = searchEntry
		self['config'].l.setList(searchEntry)

	def updateSuggestions(self, suggestions):
		self['list'].setList(suggestions)
		self['list'].setIndex(0)

	def ok(self):
		selected = self['list'].getCurrent()[0]
		if selected:
			self['list'].setIndex(0)
			self.searchValue.value = selected
			self.setSearchEntry()
			self['config'].getCurrent()[1].getSuggestions()
			self.moveHelpWindow()
		else:
			searchValue = self.searchValue.value
			print "[YouTube] Search:", searchValue
			self['config'].getCurrent()[1].help_window.instance.hide()
			if searchValue != '' and config.plugins.YouTube.saveHistory.value:
				if searchValue in self.searchHistory:
					self.searchHistory.remove(searchValue)
				self.searchHistory.insert(0, searchValue)
				if len(self.searchHistory) > 41:
					self.searchHistory.pop()
				config.plugins.YouTube.searchHistoryDict[self.curList].value = self.searchHistory
				config.plugins.YouTube.searchHistoryDict.save()
			self.close(searchValue)

	def openMenu(self):
		self['config'].getCurrent()[1].help_window.instance.hide()
		if self['list'].getCurrent()[0]:
			title = _('What do you want to do?')
			sellist = ((_('YouTube setup'), 'setup'),
					(_('Delete this entry'), 'delete'),)
			self.session.openWithCallback(self.menuCallback,
				ChoiceBox, title=title, list=sellist)
		else:
			self.menuCallback('setup')

	def menuCallback(self, answer):
		if not answer:
			self['config'].getCurrent()[1].help_window.instance.show()
		else:
			if answer[1] == 'delete':
				self.searchHistory.remove(self['list'].getCurrent()[0])
				searchList = []
				for entry in self.searchHistory:
					searchList.append((entry, None))
				if not searchList:
					searchList = [('', None)]
				self['list'].updateList(searchList)
				config.plugins.YouTube.searchHistoryDict[self.curList].value = self.searchHistory
				config.plugins.YouTube.searchHistoryDict.save()
				self['config'].getCurrent()[1].help_window.instance.show()
			else:
				from YouTubeUi import YouTubeSetup
				self.session.openWithCallback(self.setupCallback, YouTubeSetup)

	def setupCallback(self, callback=None):
		self['config'].getCurrent()[1].help_window.instance.show()

	def openKeyboard(self):
		self['config'].getCurrent()[1].help_window.instance.hide()
		self.session.openWithCallback(self.keyBoardCallback, YouTubeVirtualKeyBoard,
			text = self.searchValue.value)

	def keyBoardCallback(self, name):
		config = self['config'].getCurrent()[1]
		config.help_window.instance.show()
		if name:
			self.searchValue.value = name
			config.getSuggestions()


class GoogleSuggestionsConfigText(ConfigText):
	def __init__(self, default, updateSuggestions):
		ConfigText.__init__(self, default, fixed_size=False, visible_width=False)
		self.updateSuggestions = updateSuggestions
		self.suggestionsThread = None
		self.suggestionsThreadRunning = False

		gl = config.plugins.YouTube.searchRegion.value
		hl = config.plugins.YouTube.searchLanguage.value
		self.queryString = '/complete/search?output=toolbar&client=youtube&xml=true&ds=yt'
		if gl:
			self.queryString += '&gl=' + gl
		if hl:
			self.queryString += '&hl=' + hl
		self.queryString += '&jsonp=self.getSuggestions&q='

	def getGoogleSuggestions(self):
		suggestionsList = None
		connection = None
		suggestions = [('', None)]
		queryValue = self.value
		try:
			connection = HTTPConnection('google.com')
			connection.request('GET', self.queryString+quote(queryValue), '', {'Accept-Encoding': 'UTF-8'})
		except Exception as e:
			print "[YouTube] Can not send request for suggestions:", e
		else:
			try:
				response = connection.getresponse()
			except Exception as e:
				print "[YouTube] Can not get a response from google:", e
			else:
				if response.status == 200:
					data = response.read()
					try:
						charset = response.getheader('Content-Type',
							'text/xml; charset=ISO-8859-1').rsplit('=')[1]
					except:
						charset = 'ISO-8859-1'
					suggestionsList = data.decode(charset).encode('utf-8')
		if connection:
			connection.close()

		if suggestionsList and len(suggestionsList) > 0:
			suggestionsList = fromstring(suggestionsList)
			if suggestionsList:
				for suggestion in suggestionsList.findall('CompleteSuggestion'):
					for element in suggestion:
						if 'data' in element.attrib:
							name = element.attrib['data'].encode('UTF-8')
							if name:
								suggestions.append((name, None))
		self.updateSuggestions(suggestions)
		if queryValue != self.value:
			self.getGoogleSuggestions()
		else:
			self.suggestionsThreadRunning = False

	def getSuggestions(self):
		if self.value and not self.suggestionsThreadRunning:
			self.suggestionsThreadRunning = True
			self.suggestionsThread = Thread(target=self.getGoogleSuggestions)
			self.suggestionsThread.start()

	def handleKey(self, key):
		ConfigText.handleKey(self, key)
		if key in [KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT]:
			self.getSuggestions()

	def onSelect(self, session):
		ConfigText.onSelect(self, session)
		self.getSuggestions()
