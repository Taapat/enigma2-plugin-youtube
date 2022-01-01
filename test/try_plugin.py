"""
Minimal plugin screens startup and functional testing on various enigma2 images.
Clone enigma2 image in folder ./enigma2 and start test with
PYTHONPATH=./test:./enigma2:./enigma2/lib/python python ./test/try_plugin.py
"""

from __future__ import print_function

import sys

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
	session.current_dialog.keyDown()
	session.current_dialog.keyUp()
	session.current_dialog.keyPageDown()
	session.current_dialog.keyPageUp()
	session.current_dialog.keyBottom()
	session.current_dialog.keyTop()
	session.current_dialog.setupCallback()
	# Choice 'videotest' in suggestions list
	session.current_dialog['list'].setList([('', None), ('videotest', None)])
	session.current_dialog['list'].setIndex(1)
	session.current_dialog.ok()
	# Open Menu ChoiceBox
	session.current_dialog['list'].setIndex(1)
	session.current_dialog.openMenu()
	# Close Menu ChoiceBox
	session.current_dialog.close(None)
	# Open YouTubeVirtualKeyBoard again with text
	session.current_dialog.keyText()
	# Close YouTubeVirtualKeyBoard
	session.current_dialog.close(None)
	session.current_dialog.searchValue.stopSuggestions()
	# Choice search phrase and close YouTubeSearch
	session.current_dialog.ok()
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
		from Components.config import config
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
	# Close search video
	yt.cancel()
	# Choice Public feeds
	yt['list'].setIndex(1)
	# Open Public feeds
	yt.ok()
	# Choice Most viewed
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
	# Close search video
	yt.cancel()
	# Open YouTubeSetup
	yt.openMenu()
	# Enable 'Login on startup:'
	session.current_dialog.keyLeft()
	# Cancel authentication
	session.current_dialog.cancel()
	# Choice YouTubeDirBrowser
	session.current_dialog['config'].setCurrentIndex(10)
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
	# Open Top rated
	yt.ok()
	# Open Menu ChoiceBox
	yt.openMenu()
	# Close Menu ChoiceBox
	session.current_dialog.close(False)
	# Close Public feeds
	yt.cancel()
	# Close YouTubeMain
	yt.cancel()


def test_plugin():
	try_plugin_screens_load()


if __name__ == '__main__':
	try_plugin_screens_load()
