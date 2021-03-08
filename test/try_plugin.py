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
	session.current_dialog.openKeyboard()
	# Choice 'vide' in virtual keyboard
	if hasattr(session.current_dialog, 'selectAsciiKey') and hasattr(session.current_dialog, 'processSelect'):
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
	# Choice search phrase and close YouTubeSearch
	session.current_dialog.ok()
	# Open YouTubePlayer
	yt.ok()
	# If open YouTubePlayer
	if hasattr(session.current_dialog, 'leavePlayer'):
		# Stop playback with ChoiceBox
		session.current_dialog.leavePlayer()
		# Close YouTubePlayer
		session.current_dialog.close(('Yes', 'quit'))
	elif session.current_dialog:
		# Close MessageBox if exist
		session.current_dialog.close()
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


try_plugin_screens_load()
