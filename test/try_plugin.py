""" Start test with PYTHONPATH=./test:./enigma2:./enigma2/lib/python python ./test/try_plugin.py """
from __future__ import print_function

import enigma


def try_plugin_screens_load():
	print('Try start session')
	session = enigma.start_session()

	print('Try YouTube screens load')
	from Plugins.Extensions.YouTube.YouTubeUi import YouTubeMain
	yt = session.open(YouTubeMain)
	yt.ok()
	yt.ok()
	session.current_dialog.close('video')
	yt.cancel()
	yt.cancel()
	yt.openMenu()
	session.current_dialog.cancel()
	yt.menuCallback(('', 'download_list'))
	session.current_dialog.close()
	yt.cancel()


try_plugin_screens_load()
