from __future__ import print_function

from os import path as os_path

from threading import Thread
from json import loads

from enigma import ePoint
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.config import config, ConfigText
from Components.config import KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.Sources.Boolean import Boolean
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText

from . import _, screenwidth
from .compat import compat_quote
from .compat import compat_urlopen


# Workaround to keep compatibility broken with changes in new images
DEFAULT_BUTTONS = 'skin_default/buttons'
if os_path.exists('/usr/share/enigma2/skin_default/vkey_icon.png'):
	DEFAULT_BUTTONS = 'skin_default'


class YouTubeVirtualKeyBoard(VirtualKeyBoard):
	def __init__(self, session, text):
		if text:
			title = text
		else:
			title = _('Search')
		VirtualKeyBoard.__init__(self, session, title=title, text=text)
		self.skinName = ['YouTubeVirtualKeyBoard', 'VirtualKeyBoard']
		self.searchValue = GoogleSuggestionsConfigText(default=text,
				update_suggestions=self.updateSuggestions)
		self.onClose.append(self.searchValue.stopSuggestions)
		if text:
			# Force a search by setting the old search value to ""
			self.searchValue.value = ""
			self.tryGetSuggestions()

	# Replace okClicked on OpenPLi develop
	def processSelect(self):
		VirtualKeyBoard.processSelect(self)
		self.tryGetSuggestions()

	def okClicked(self):
		VirtualKeyBoard.okClicked(self)
		self.tryGetSuggestions()

	def backSelected(self):
		VirtualKeyBoard.backSelected(self)
		self.tryGetSuggestions()

	def forwardSelected(self):
		VirtualKeyBoard.forwardSelected(self)
		self.tryGetSuggestions()

	def eraseAll(self):
		VirtualKeyBoard.eraseAll(self)
		self.tryGetSuggestions()

	def tryGetSuggestions(self):
		new_search_value = self['text'].getText()
		if self.searchValue.value != new_search_value:
			self.searchValue.value = new_search_value
			self.searchValue.getSuggestions()

	def updateSuggestions(self, suggestions):
		if 'prompt' in self:
			if len(suggestions) > 1:
				self['prompt'].text = ', '.join(x[0] for x in suggestions[1:])
			else:
				self['prompt'].text = ''
		elif 'header' in self:
			if len(suggestions) > 1:
				self['header'].text = ', '.join(x[0] for x in suggestions[1:])
			else:
				self['header'].text = ''


class YouTubeSearch(Screen, ConfigListScreen):
	if screenwidth == 'svg':
		skin = """<screen position="center,150*f" size="630*f,370*f">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube.svg" \
					position="15*f,6*f" size="100*f,40*f" transparent="1" alphatest="blend" />
				<widget name="config" position="130*f,15*f" size="485*f,30*f" zPosition="2" \
					scrollbarMode="showNever" itemHeight="25*f" font="Regular;20*f" />
				<widget source="list" render="Listbox" position="15*f,48*f" size="600*f,273*f" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [MultiContentEntryText(pos=(10*f,1), size=(580*f,30*f), \
							font=0, flags=RT_HALIGN_LEFT, text=0)],
						"fonts": [gFont("Regular",20*f)],
						"itemHeight": 30*f}
					</convert>
				</widget>
				<ePixmap position="30*f,335*f" size="35*f,25*f" pixmap="skin_default/buttons/key_text.svg" \
					transparent="1" alphatest="blend" />
				<ePixmap position="85*f,323*f" size="140*f,40*f" pixmap="skin_default/buttons/red.svg" \
					transparent="1" alphatest="blend" />
				<ePixmap position="245*f,323*f" size="140*f,40*f" pixmap="skin_default/buttons/green.svg" \
					transparent="1" alphatest="blend" />
				<ePixmap position="405*f,323*f" size="140*f,40*f" pixmap="skin_default/buttons/yellow.svg" \
					transparent="1" alphatest="blend" />
				<widget source="key_red" render="Label" position="85*f,328*f" zPosition="2" size="140*f,30*f" \
					valign="center" halign="center" font="Regular;22*f" transparent="1" />
				<widget source="key_green" render="Label" position="245*f,328*f" zPosition="2" size="140*f,30*f" \
					valign="center" halign="center" font="Regular;22*f" transparent="1" />
				<widget source="key_yellow" render="Label" position="405*f,328*f" zPosition="2" size="140*f,30*f" \
					valign="center" halign="center" font="Regular;22*f" transparent="1" />
				<ePixmap position="565*f,335*f" size="35*f,25*f" pixmap="skin_default/buttons/key_menu.svg" \
					transparent="1" alphatest="blend" />
				<widget name="HelpWindow" position="400*f,540*f" size="1,1" zPosition="5" \
					pixmap="skin_default/buttons/vkey_icon.svg" transparent="1" alphatest="blend" />
			</screen>"""
	elif screenwidth == 1280:
		skin = """<screen position="center,150" size="630,370">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_HD.png" \
					position="15,6" size="100,40" transparent="1" alphatest="on" />
				<widget name="config" position="130,15" size="485,30" zPosition="2" \
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
				<ePixmap position="30,335" size="35,25" pixmap="skin_default/buttons/key_text.png" \
					transparent="1" alphatest="on" />
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
					pixmap="%s/vkey_icon.png" transparent="1" alphatest="on" />
			</screen>""" % DEFAULT_BUTTONS
	elif screenwidth == 1920:
		skin = """<screen position="center,225" size="945,555">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_FHD.png" \
					position="22,15" size="150,60" transparent="1" alphatest="on" />
				<widget name="config" position="182,22" size="740,45" zPosition="2" \
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
				<ePixmap position="43,507" size="53,38" pixmap="skin_default/buttons/key_text.png" \
					transparent="1" alphatest="on" />
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
				<ePixmap position="849,507" size="53,38" pixmap="skin_default/buttons/key_menu.png" \
					transparent="1" alphatest="on" />
				<widget name="HelpWindow" position="600,810" size="1,1" zPosition="5" \
					pixmap="%s/vkey_icon.png" transparent="1" alphatest="on" />
			</screen>""" % DEFAULT_BUTTONS
	else:
		skin = """<screen position="center,150" size="630,370">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/YouTube/YouTube_HD.png" \
					position="15,6" size="100,40" transparent="1" alphatest="on" />
				<widget name="config" position="130,15" size="485,30" zPosition="2" \
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
				<ePixmap position="30,335" size="35,25" pixmap="skin_default/buttons/key_text.png" \
					transparent="1" alphatest="on" />
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
					pixmap="%s/vkey_icon.png" transparent="1" alphatest="on" />
			</screen>""" % (DEFAULT_BUTTONS)

	def __init__(self, session, cur_list):
		Screen.__init__(self, session)
		self.session = session
		self.curList = cur_list
		self.title = _('Search')
		self['key_red'] = StaticText(_('Exit'))
		self['key_green'] = StaticText(_('OK'))
		self['key_yellow'] = StaticText(_('Keyboard'))
		self['HelpWindow'] = Pixmap()
		self['VKeyIcon'] = Boolean(False)
		self['searchactions'] = ActionMap(['SetupActions', 'ColorActions', 'MenuActions'], {
				'cancel': self.close,
				'save': self.ok,
				'ok': self.ok,
				'yellow': self.openKeyboard,
				'menu': self.openMenu}, -2)
		ConfigListScreen.__init__(self, [], session)
		self.searchValue = GoogleSuggestionsConfigText(default='',
			update_suggestions=self.updateSuggestions)
		self.setSearchEntry()
		self['list'] = List([])
		self.searchHistory = config.plugins.YouTube.searchHistoryDict[self.curList].value
		search_list = [('', None)]
		for entry in self.searchHistory:
			search_list.append((entry, None))
		self['list'].list = search_list
		self.onLayoutFinish.append(self.moveHelpWindow)
		self.onClose.append(self.searchValue.stopSuggestions)

	def moveHelpWindow(self):
		helpwindowpos = self["HelpWindow"].getPosition()
		self['config'].getCurrent()[1].help_window.instance.move(ePoint(helpwindowpos[0],
				helpwindowpos[1]))

	def setSearchEntry(self):
		self['config'].list = [(_('Search'), self.searchValue)]

	def updateSuggestions(self, suggestions):
		if 'list' in self:
			self['list'].list = suggestions
			self['list'].index = 0

	def ok(self):
		selected = self['list'].getCurrent()[0]
		if selected and self.searchValue.value != selected:
			self['list'].index = 0
			self.searchValue.value = selected
			self.setSearchEntry()
			self['config'].getCurrent()[1].getSuggestions()
			self.moveHelpWindow()
		else:
			search_value = self.searchValue.value
			print('[YouTubeSearch] Search:', search_value)
			self['config'].getCurrent()[1].help_window.instance.hide()
			if search_value != '' and config.plugins.YouTube.saveHistory.value:
				if search_value in self.searchHistory:
					self.searchHistory.remove(search_value)
				self.searchHistory.insert(0, search_value)
				if len(self.searchHistory) > 41:
					self.searchHistory.pop()
				config.plugins.YouTube.searchHistoryDict[self.curList].value = self.searchHistory
				config.plugins.YouTube.searchHistoryDict[self.curList].save()
			self.close(search_value)

	def noNativeKeys(self):
		ConfigListScreen.noNativeKeys(self)
		renderer = self['list']
		while renderer.master:
			renderer = renderer.master
		try:
			renderer.instance.allowNativeKeys(False)
		except AttributeError:
			pass

	def keyText(self):
		self.openKeyboard()

	def keyTop(self):
		self['list'].index = 0

	def keyPageUp(self):
		self['list'].pageUp()

	def keyUp(self):
		self['list'].up()

	def keyDown(self):
		self['list'].down()

	def keyPageDown(self):
		self['list'].pageDown()

	def keyBottom(self):
		self['list'].index = max(0, self['list'].count() - 1)

	def openMenu(self):  # pragma: no cover
		self['config'].getCurrent()[1].help_window.instance.hide()
		if self['list'].getCurrent()[0]:
			title = _('What do you want to do?')
			sellist = ((_('YouTube setup'), 'setup'),
					(_('Delete this entry'), 'delete'),)
			self.session.openWithCallback(self.menuCallback,
					ChoiceBox, title=title, list=sellist)
		else:
			self.menuCallback('setup')

	def menuCallback(self, answer):  # pragma: no cover
		if not answer:
			self['config'].getCurrent()[1].help_window.instance.show()
		else:
			if answer[1] == 'delete':
				self.searchHistory.remove(self['list'].getCurrent()[0])
				search_list = []
				for entry in self.searchHistory:
					search_list.append((entry, None))
				if not search_list:
					search_list = [('', None)]
				self['list'].updateList(search_list)
				config.plugins.YouTube.searchHistoryDict[self.curList].value = self.searchHistory
				config.plugins.YouTube.searchHistoryDict[self.curList].save()
				self['config'].getCurrent()[1].help_window.instance.show()
			else:
				from .YouTubeUi import YouTubeSetup
				self.session.openWithCallback(self.setupCallback, YouTubeSetup)

	def setupCallback(self, callback=None):
		self['config'].getCurrent()[1].help_window.instance.show()

	def openKeyboard(self):
		self['config'].getCurrent()[1].help_window.instance.hide()
		self.session.openWithCallback(self.keyBoardCallback, YouTubeVirtualKeyBoard,
				text=self.searchValue.value)

	def keyBoardCallback(self, name):
		config = self['config'].getCurrent()[1]
		config.help_window.instance.show()
		if name:
			self.searchValue.value = name
			config.getSuggestions()


class GoogleSuggestionsConfigText(ConfigText):
	def __init__(self, default, update_suggestions):
		ConfigText.__init__(self, default, fixed_size=False, visible_width=False)
		self.updateSuggestions = update_suggestions
		self.use_suggestions = False

		gl = config.plugins.YouTube.searchRegion.value
		hl = config.plugins.YouTube.searchLanguage.value
		self.url = 'https://www.google.com/complete/search?output=toolbar&client=youtube&json=true&ds=yt{}{}&q='.format(
				gl and '&gl=%s' % gl,
				hl and '&hl=%s' % hl)

	def getGoogleSuggestions(self):
		suggestions_list = None
		suggestions = [('', None)]
		query_value = self.value
		try:
			response = compat_urlopen(self.url + compat_quote(query_value), timeout=3)
			content_type = response.headers.get('Content-Type', '')
			if 'charset=' in content_type:
				charset = content_type.split('charset=', 1)[1]
			else:
				charset = 'ISO-8859-1'
			suggestions_list = loads(response.read().decode(charset).encode('utf-8'))
			response.close()
		except Exception as e:
			print('[YouTubeSearch] Error in get suggestions from google', e)
		if self.use_suggestions:
			if suggestions_list:
				suggestions.extend([(str(s), None) for s in suggestions_list[1] if s])
			self.updateSuggestions(suggestions)
			if query_value != self.value:
				self.getGoogleSuggestions()
			else:
				self.use_suggestions = False

	def getSuggestions(self):
		if self.value and not self.use_suggestions:
			self.use_suggestions = True
			Thread(target=self.getGoogleSuggestions).start()

	def stopSuggestions(self):
		self.use_suggestions = False

	def handleKey(self, key, callback=None):
		if callback:
			ConfigText.handleKey(self, key, callback)
		else:
			ConfigText.handleKey(self, key)
		if key in (KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT):
			self.getSuggestions()

	def onSelect(self, session):
		ConfigText.onSelect(self, session)
		self.getSuggestions()
