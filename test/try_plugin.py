""" Start test with PYTHONPATH=./test:./enigma2:./enigma2/lib/python python ./test/try_plugin.py """
from __future__ import print_function

import enigma


def try_plugin_screens_load():
	print('Try start session')
	session = enigma.start_session()

	print('Try YouTubeMain')
	from Plugins.Extensions.YouTube.YouTubeUi import YouTubeMain
	yt = session.open(YouTubeMain)
	yt.ok()
	yt.searchScreenCallback('video')
	yt.cancel()

	print('Try YouTubeSetup')
	from Plugins.Extensions.YouTube.YouTubeUi import YouTubeSetup
	yt = session.open(YouTubeSetup)
	yt.cancel()

	print('Try YouTubeDownloadList')
	from Plugins.Extensions.YouTube.YouTubeDownload import YouTubeDownloadList
	yt = session.open(YouTubeDownloadList)
	yt.close()


try_plugin_screens_load()
