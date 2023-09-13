"""
Minimal plugin screens startup and functional testing on various enigma2 images.
Clone enigma2 image in folder ./enigma2 and start test with
PYTHONPATH=./test:./enigma2:./enigma2/lib/python python ./test/try_plugin.py
"""

from __future__ import print_function

import os
import sys

import enigmahelper


if sys.version_info[0] == 2:
	reload(sys)  # noqa: F821
	sys.setdefaultencoding('utf-8')


class FailureInstance:
	def getErrorMessage(self):
		return 'download failed'


def try_plugin_screens_load():
	print('Try start session')
	e2_version = os.environ['E2_VERSION']
	if e2_version == 'Taapat':
		enigmahelper.setDesktopSize(720, 576)
	elif e2_version == 'OpenPLi':
		enigmahelper.setDesktopSize(1280, 720)
	session = enigmahelper.start_session()

	from Plugins.Plugin import PluginDescriptor
	from Components.PluginComponent import plugins
	from Plugins.Extensions.YouTube.plugin import Plugins
	plugins.addPlugin(Plugins()[0])
	p = PluginDescriptor(
		name='ServiceApp',
		where=[
			PluginDescriptor.WHERE_MENU,
			PluginDescriptor.WHERE_EXTENSIONSMENU
		]
	)
	p.path = 'ServiceApp'
	plugins.addPlugin(p)

	print('=' * 57)
	print(' ' * 15 + 'Try YouTube screens load')
	print('=' * 57)
	from Plugins.Extensions.YouTube.YouTubeUi import YouTubeMain
	from Components.config import config
	config.plugins.YouTube.refreshToken.value = os.environ['YOUTUBE_PLUGIN_TOKEN']
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
	# Select next serch results page
	yt.selectNext()
	yt['list'].setIndex(23)
	yt.selectNext()
	# Select previous serch results page
	yt.selectPrevious()
	yt.selectPrevious()
	# Open YouTubePlayer
	yt.ok()
	# If open YouTubePlayer
	if hasattr(session.current_dialog, 'leavePlayer'):
		# Try YouTubePlayer __serviceStart
		from Components.ServiceEventTracker import ServiceEventTracker
		func = list(ServiceEventTracker.EventMap.values())[0][0][2]
		config.plugins.YouTube.lastPosition.value = '["%s", 1]' % session.current_dialog.current[0]
		func()
		session.current_dialog.close(True)
		session.current_dialog.started = False
		config.plugins.YouTube.lastPosition.value = ''
		func()
		session.current_dialog.lastPosition = [x for x in range(21)]
		# Try others YouTubePlayer methods for code coverage
		session.current_dialog.getPluginList()
		session.current_dialog.showMovies()
		session.current_dialog.openServiceList()
		# Open YouTubeInfo
		from enigmahelper import eTimer
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
	# Select last entry in page
	yt['list'].setIndex(23)
	yt.selectNext()
	# Select first entry in page
	yt.selectPrevious()
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
	session.current_dialog.ok()
	# Open YouTubePlayer
	yt.ok()
	# If open YouTubePlayer
	if hasattr(session.current_dialog, 'doEofInternal'):
		# Stop playback with doEofInternal
		session.current_dialog.doEofInternal(None)
	elif session.current_dialog:
		# Close MessageBox if exist
		session.current_dialog.close()
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
		config.plugins.YouTube.onMovieEof.value = 'quit'
		session.current_dialog.doEofInternal(None)
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
	yt.ok()
	# Open my subscriptions
	yt['list'].setIndex(0)
	yt.ok()
	# Open recent subscriptions
	yt.ok()
	yt.getAllSubscriptions()
	yt.cancel()
	# Unsubscribe channel ELLO
	for x in range(2, 23):
		yt['list'].setIndex(x)
		if yt['list'].getCurrent()[3] == 'ELLO':
			print(yt.unsubscribeChannel())
			break
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
	# Start test video download
	yt['list'].setIndex(0)
	yt.menuCallback(('download', 'download'))
	session.current_dialog.close()
	# Try DownloadTask methods
	from Components.Task import job_manager
	if job_manager.active_job:
		task = job_manager.active_job.tasks[0]
		task.downloadProgress(10, 100)
	# Open YouTubeDownloadList
	yt.menuCallback(('', 'download_list'))
	# Try YouTubeDownloadList methods
	session.current_dialog.ok()
	# Close JobView or YouTubeDownloadList
	session.current_dialog.close()
	# If closed JobView try YouTubeDownloadList methods
	if hasattr(session.current_dialog, 'cleanVariables'):
		session.current_dialog.cleanVariables()
		# Close YouTubeDownloadList
		session.current_dialog.close()
	# Try merge video files
	config.plugins.YouTube.mergeFiles.value = True
	task.outputfile = 'test_suburi.mp4'
	with open(task.outputfile, 'w') as fp:  # noqa: F841
		pass  # create empty mp4 file
	with open('test.m4a', 'w') as fp:  # noqa: F841
		pass  # create empty m4a file
	task.downloadFinished(None)
	try:
		os.remove('test.mkv')
	except OSError:
		pass  # if mkv file not created
	try:
		task.downloadFailed(FailureInstance(), '')
	except IndexError:
		pass  # expected error in Task
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
	# Open YouTubeDirBrowser again to test all other methods
	session.current_dialog['config'].setCurrentIndex(11)
	session.current_dialog.ok()
	session.current_dialog.ok()
	session.current_dialog.use()
	# Test removeCallback
	config.plugins.YouTube.mergeFiles.value = False
	session.current_dialog['config'].setCurrentIndex(1)
	session.current_dialog.ok()
	session.current_dialog.close(True)
	session.current_dialog.cancel()
	# Open YouTubeSetup to test installCallback
	yt.openMenu()
	config.plugins.YouTube.mergeFiles.value = True
	session.current_dialog.ok()
	session.current_dialog.close(False)
	config.plugins.YouTube.mergeFiles.value = True
	session.current_dialog.ok()
	session.current_dialog.close(True)
	session.current_dialog.cancel()
	# Open YouTubeSetup to test keySave
	yt.openMenu()
	session.current_dialog.ok()
	# Open Public feeds
	yt.createFeedList()
	# Open recent
	yt.ok()
	# Open Menu ChoiceBox
	yt.openMenu()
	# Close Menu ChoiceBox
	session.current_dialog.close(False)
	# Test error in extract video url
	current = (
		'vrong_ID', '', '', '', '', '', '', '', '', '', '', ''
	)
	yt.yts[1]['entry_list'][yt.yts[1]['index']] = current
	yt.useVideoUrl()
	yt.cancel()
	# Close Public feeds
	yt.cancel()
	# Close YouTubeMain
	yt.cleanVariables()
	yt.cancel()
	# Try plugin main for code coverage
	from Plugins.Extensions.YouTube.plugin import main
	main(session)


def test_plugin():
	try_plugin_screens_load()


if __name__ == '__main__':
	try:
		try_plugin_screens_load()
	except TypeError as ex:
		print('Error %s, try second time' % str(ex))
		from time import sleep
		sleep(10)
		try_plugin_screens_load()
