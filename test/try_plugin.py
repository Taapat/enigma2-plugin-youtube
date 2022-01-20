"""
Minimal plugin screens startup and functional testing on various enigma2 images.
Clone enigma2 image in folder ./enigma2 and start test with
PYTHONPATH=./test:./enigma2:./enigma2/lib/python python ./test/try_plugin.py
"""

from __future__ import print_function

import sys
from os import environ

import enigma


if sys.version_info[0] == 2:
	reload(sys)
	sys.setdefaultencoding('utf-8')


def try_plugin_screens_load():
	print('Try start session')
	session = enigma.start_session()

	print('=========================================================')
	print('               Try YouTube screens load')
	print('=========================================================')
	from Plugins.Extensions.YouTube.YouTubeUi import YouTubeMain
	from Components.config import config
	config.plugins.YouTube.refreshToken.value = environ['YOUTUBE_PLUGIN_TOKEN']
	config.plugins.YouTube.subscriptOrder.value = 'alphabetical'
	config.plugins.YouTube.downloadDir.value = './'
	# Open YouTubeMain
	yt = session.open(YouTubeMain)
	# Choice search
	yt.ok()
	# Choice search video, open YouTubeSearch
	yt.ok()
	# Choice YouTubeVirtualKeyBoard
	session.current_dialog.keyText()
	# Open YouTubeVirtualKeyBoard
	from Screens.VirtualKeyBoard import VirtualKeyBoard
	if hasattr(session.current_dialog, 'selectAsciiKey') and hasattr(VirtualKeyBoard, 'processSelect'):
		# Try YouTubeVirtualKeyBoard methods for code coverage
		session.current_dialog.backSelected()
		session.current_dialog.forwardSelected()
		session.current_dialog.eraseAll()
		from Components.config import KEY_DELETE
		session.current_dialog.searchValue.handleKey(KEY_DELETE)
		# Choice 'vide' in virtual keyboard
		session.current_dialog.selectAsciiKey('v')
		session.current_dialog.processSelect()
		session.current_dialog.selectAsciiKey('i')
		session.current_dialog.processSelect()
		session.current_dialog.selectAsciiKey('d')
		session.current_dialog.processSelect()
		session.current_dialog.selectAsciiKey('e')
		session.current_dialog.processSelect()
		session.current_dialog.save()
	else:  # On old enigma2 choice only '9'
		session.current_dialog.left()
		session.current_dialog.left()
		session.current_dialog.left()
		try:
			session.current_dialog.okClicked()
			session.current_dialog.ok()
		except AttributeError:
			session.current_dialog.processSelect()
			session.current_dialog.save()
	# Move the cursor in suggestions list
	session.current_dialog['list'].selectNext()
	session.current_dialog['list'].selectPrevious()
	from Components.Sources.List import List
	if hasattr(List, 'down'):
		session.current_dialog.keyDown()
		session.current_dialog.keyUp()
		session.current_dialog.keyPageDown()
		session.current_dialog.keyPageUp()
		session.current_dialog.keyBottom()
		session.current_dialog.keyTop()
	session.current_dialog.setupCallback()
	# Choice 'videotest' in suggestions list
	session.current_dialog.updateSuggestions([('', None), ('videotest', None)])
	session.current_dialog['list'].setIndex(1)
	session.current_dialog.ok()
	# Open YouTubeVirtualKeyBoard again with text
	session.current_dialog.keyText()
	# Close YouTubeVirtualKeyBoard
	session.current_dialog.close(None)
	session.current_dialog.searchValue.stopSuggestions()
	# Choice search phrase and close YouTubeSearch
	session.current_dialog.ok()
	# Open YouTubeInfo
	yt.showEventInfo()
	session.current_dialog.close()
	# Open YouTubePlayer
	yt.ok()
	# If open YouTubePlayer
	if hasattr(session.current_dialog, 'leavePlayer'):
		# Try YouTubePlayer methods for code coverage
		session.current_dialog.getPluginList()
		session.current_dialog.messageBoxCallback(True)
		session.current_dialog.showMovies()
		# Open YouTubeInfo
		from enigma import eTimer
		session.current_dialog.hideTimer = eTimer()
		session.current_dialog.showSecondInfoBar()
		# Close YouTubeInfo
		session.current_dialog.close()
		# Stop playback with ChoiceBox
		config.plugins.YouTube.onMovieStop.value = 'ask'
		session.current_dialog.leavePlayer()
		# Repeat playback on YouTubePlayer
		session.current_dialog.close(('Repeat', 'repeat'))
		# Close YouTubePlayer
		session.current_dialog.leavePlayer()
		session.current_dialog.close(('Ask', 'ask'))
		# Play next with ChoiceBox
		session.current_dialog.close(('Play next', 'playnext'))
	elif session.current_dialog:
		# Close MessageBox if exist
		session.current_dialog.close()
	# If open YouTubePlayer
	if hasattr(session.current_dialog, 'leavePlayer'):
		# Close YouTubePlayer
		session.current_dialog.leavePlayer()
		session.current_dialog.close(('Ask', 'ask'))
		# Play previous with ChoiceBox
		session.current_dialog.close(('Play previous', 'playprev'))
	elif session.current_dialog:
		# Close MessageBox if exist
		session.current_dialog.close()
	# If open YouTubePlayer
	if hasattr(session.current_dialog, 'leavePlayer'):
		# Close YouTubePlayer
		config.plugins.YouTube.onMovieStop.value = 'related'
		session.current_dialog.leavePlayer()
		session.current_dialog.close(('Quit', 'quit'))
	elif session.current_dialog:
		# Close MessageBox if exist
		session.current_dialog.close()
	# Try YouTubeMain methods for code coverage
	yt.setNextEntries()
	yt.setPrevEntries()
	# Close video list
	yt.cancel()
	# Open search channels
	yt['list'].setIndex(1)
	yt.ok()
	# Choice 'ello' in suggestions list
	session.current_dialog.updateSuggestions([('', None), ('ello', None)])
	session.current_dialog['list'].setIndex(1)
	session.current_dialog.ok()
	session.current_dialog.ok()
	yt.ok()
	# Like video, remove rating
	yt.rateVideo('like')
	yt.rateVideo('none')
	yt.close()
	# Subscribe to channel ELLO
	print(yt.subscribeChannel('UCXdLsO-b4Xjf0f9xtD_YHzg'))
	# Close channels list
	yt.cancel()
	yt.cancel()
	# Open search playlists
	yt['list'].setIndex(2)
	yt.ok()
	# Choice 'hdvideo' in suggestions list
	session.current_dialog.updateSuggestions([('', None), ('hdvideo', None)])
	session.current_dialog['list'].setIndex(1)
	session.current_dialog.ok()
	# Close playlists list
	yt.cancel()
	# Open search live broadcasts
	yt['list'].setIndex(3)
	yt.ok()
	# Choice '112' in suggestions list
	session.current_dialog.updateSuggestions([('', None), ('112', None)])
	session.current_dialog['list'].setIndex(1)
	session.current_dialog.ok()
	# Close live broadcasts list
	yt.cancel()
	# Close search
	yt.cancel()
	# Open Public feeds
	yt['list'].setIndex(1)
	yt.ok()
	# Choice Most viewed
	yt['list'].setIndex(1)
	yt.ok()
	# Open YouTubePlayer
	yt.ok()
	# If open YouTubePlayer
	if hasattr(session.current_dialog, 'doEofInternal'):
		# Stop playback with doEofInternal
		session.current_dialog.doEofInternal('quit')
	elif session.current_dialog:
		# Close MessageBox if exist
		session.current_dialog.close()
	# Close Most viewed
	yt.cancel()
	# Open top rated feeds
	yt['list'].setIndex(0)
	yt.ok()
	yt.cancel()
	# Open recent feeds
	yt['list'].setIndex(2)
	yt.ok()
	yt.cancel()
	# Open HD videos feeds
	yt['list'].setIndex(3)
	yt.ok()
	yt.cancel()
	# Open embedded feeds
	yt['list'].setIndex(4)
	yt.ok()
	yt.cancel()
	# Open shows feeds
	yt['list'].setIndex(5)
	yt.ok()
	yt.cancel()
	# Open movies feeds
	yt['list'].setIndex(6)
	yt.ok()
	yt.cancel()
	# Close Public feeds
	yt.cancel()
	# Open my feeds
	yt['list'].setIndex(2)
	# Open my subscriptions
	yt.ok()
	# Open recent subscriptions
	yt['list'].setIndex(0)
	yt.ok()
	# Unsubscribe channel ELLO
	yt['list'].setIndex(2)
	if yt['list'].getCurrent()[3] == 'ELLO':
		print(yt.unsubscribeChannel())
	yt.ok()
	yt.cancel()
	yt.cancel()
	# Open liked videos
	yt['list'].setIndex(1)
	yt.ok()
	yt.cancel()
	# Open uploads
	yt['list'].setIndex(2)
	yt.ok()
	# Download test video
	yt['list'].setIndex(0)
	yt.menuCallback(('download', 'download'))
	session.current_dialog.close()
	yt.cancel()
	# Open playlists
	yt['list'].setIndex(3)
	yt.ok()
	yt['list'].setIndex(0)
	yt.ok()
	yt.cancel()
	yt.cancel()
	# Close my subscriptions
	yt.cancel()
	# Open YouTubeSetup
	yt.openMenu()
	# Try updateDescription
	if hasattr(session.current_dialog, 'getCurrentDescription'):
		session.current_dialog.updateDescription()
	# Disable 'Login on startup:'
	session.current_dialog.keyLeft()
	# Cancel update access data
	session.current_dialog.cancel()
	# Choice YouTubeDirBrowser
	config.plugins.YouTube.downloadDir.value = '/media/hdd/movie/'
	session.current_dialog['config'].setCurrentIndex(11)
	# Open YouTubeDirBrowser
	session.current_dialog.ok()
	# Close YouTubeDirBrowser
	session.current_dialog.cancel()
	# Close YouTubeSetup
	session.current_dialog.cancel()
	# Open YouTubeDownloadList
	yt.menuCallback(('', 'download_list'))
	# Close YouTubeDownloadList
	session.current_dialog.close()
	# Open Public feeds
	yt.createFeedList()
	# Open recent
	yt.ok()
	# Open Menu ChoiceBox
	yt.openMenu()
	# Close Menu ChoiceBox
	session.current_dialog.close(False)
	# Close Public feeds
	yt.cancel()
	# Close YouTubeMain
	yt.cleanVariables()
	yt.cancel()
	# Try plugin for code coverage
	from Plugins.Extensions.YouTube.plugin import main, Plugins
	Plugins()
	main(session)


def test_plugin():
	try_plugin_screens_load()


if __name__ == '__main__':
	try_plugin_screens_load()
