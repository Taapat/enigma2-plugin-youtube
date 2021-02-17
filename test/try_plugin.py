""" Start test with PYTHONPATH=./test:./enigma2:./enigma2/lib/python python ./test/try_plugin.py """
from __future__ import print_function

import enigma


def try_plugin_screens_load():
	print('Try start session')
	session = enigma.start_session()

	print('Try YouTube screens load')
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
	if hasattr('YouTubeVirtualKeyBoard', 'selectAsciiKey') and hasattr('YouTubeVirtualKeyBoard', 'processSelect'):
		session.current_dialog.selectAsciiKey('v')
		session.current_dialog.processSelect()
		session.current_dialog.selectAsciiKey('i')
		session.current_dialog.processSelect()
		session.current_dialog.selectAsciiKey('d')
		session.current_dialog.processSelect()
		session.current_dialog.selectAsciiKey('e')
		session.current_dialog.processSelect()
	else:  # On old enigma2 choice only '9'
		session.current_dialog.left()
		session.current_dialog.left()
		session.current_dialog.left()
		try:
			session.current_dialog.okClicked()
		except AttributeError:
			session.current_dialog.processSelect()
	# Close YouTubeVirtualKeyBoard
	session.current_dialog.close('video')
	# Close YouTubeSearch
	session.current_dialog.close('video')
	# Close video list
	yt.cancel()
	# Close search video
	yt.cancel()
	# Open YouTubeSetup
	yt.openMenu()
	# Close YouTubeSetup
	session.current_dialog.cancel()
	# Open YouTubeDownloadList
	yt.menuCallback(('', 'download_list'))
	# Close YouTubeDownloadList
	session.current_dialog.close()
	# Close YouTubeMain
	yt.cancel()


try_plugin_screens_load()
