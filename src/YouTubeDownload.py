from __future__ import print_function

import os

from enigma import eTimer
from Components.config import config
from Components.ActionMap import ActionMap
from Components.FileList import FileList
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Task import Task, Job, job_manager
from Screens.Screen import Screen
from Tools.Downloader import downloadWithProgress

from . import _, screenwidth
from .YouTubeUi import BUTTONS_FOLDER


class YouTubeDirBrowser(Screen):
	def __init__(self, session, download_dir):
		Screen.__init__(self, session)
		self.skinName = ['YouTubeDirBrowser', 'FileBrowser']
		self.title = _('Please select the download directory')
		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('Use'))
		if not os.path.exists(download_dir):
			download_dir = '/'
		self.filelist = FileList(download_dir, showFiles=False)
		self['filelist'] = self.filelist
		self['FilelistActions'] = ActionMap(['SetupActions', 'ColorActions'], {
				'cancel': self.cancel,
				'red': self.cancel,
				'ok': self.ok,
				'green': self.use}, -2)

	def ok(self):
		if self.filelist.canDescent():
			self.filelist.descent()

	def use(self):
		current_dir = self['filelist'].getCurrentDirectory()
		dir_name = self['filelist'].getFilename()
		if current_dir is None or \
			(self.filelist.canDescent() and dir_name and len(dir_name) > len(current_dir)):
			self.close(dir_name)

	def cancel(self):
		self.close(False)


class DownloadJob(Job):
	def __init__(self, url, outputfile, title, download_stop):
		Job.__init__(self, title)
		DownloadTask(self, url, outputfile, download_stop)


class DownloadTask(Task):
	def __init__(self, job, url, outputfile, download_stop):
		Task.__init__(self, job, _('Downloading'))
		self.url = url
		self.outputfile = outputfile
		self.downloadStop = download_stop
		self.totalSize = 0

	def run(self, callback):
		self.callback = callback
		self.download = downloadWithProgress(self.url, self.outputfile)
		self.download.addProgress(self.downloadProgress)
		self.download.start().addCallback(self.downloadFinished)\
			.addErrback(self.downloadFailed)

	def downloadProgress(self, currentbytes, totalbytes):
		self.progress = int(currentbytes / float(totalbytes) * 100)
		self.totalSize = totalbytes

	def downloadFinished(self, result):
		Task.processFinished(self, 0)
		self.downloadStop()
		if '_suburi.mp4' in self.outputfile and \
			config.plugins.YouTube.mergeFiles.value and \
			os.path.exists('%s.m4a' % self.outputfile[:-11]) and \
			not os.path.exists('%s.mkv' % self.outputfile[:-11]):
			from Components.Console import Console
			Console().ePopen('ffmpeg -i "%s" -i "%s.m4a" -c copy "%s.mkv"' % (self.outputfile,
				self.outputfile[:-11], self.outputfile[:-11]), self.mergeCompleted)

	def mergeCompleted(self, result, retval, extra_args):
		if os.path.exists('%s.mkv' % self.outputfile[:-11]):
			try:
				os.remove(self.outputfile)
				os.remove('%s.m4a' % self.outputfile[:-11])
			except Exception as e:
				print('[YouTubeDownload] Error delete file', e)

	def downloadFailed(self, failure_instance=None, error_message=''):
		print('[YouTubeDownload] Video download failed')
		if error_message == '' and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			print('[YouTubeDownload] error', str(error_message))
		Task.processFinished(self, 1)
		self.downloadStop()


class YouTubeDownloadList(Screen):
	if screenwidth == 'svg':
		skin = """<screen position="center,center" size="720*f,370*f">
				<widget source="list" render="Listbox" position="center,30*f" size="690*f,270*f" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryText(pos=(5*f,1), size=(270*f,22*f), \
								font=0, flags=RT_HALIGN_LEFT, text=1),  # Title
							MultiContentEntryText(pos=(280*f,1), size=(120*f,22*f), \
								font=0, flags=RT_HALIGN_RIGHT, text=2),  # State
							MultiContentEntryProgress(pos=(410*f,4*f), size=(100*f,22*f), \
								percent=-3), # Progress
							MultiContentEntryText(pos=(520*f,1), size=(80*f,22*f), \
								font=0, flags=RT_HALIGN_LEFT, text=4),  # Percentage
							MultiContentEntryText(pos=(600*f,1), size=(86*f,22*f), \
								font=0, flags=RT_HALIGN_RIGHT, text=5),  # Size
							],
						"fonts": [gFont("Regular",20*f)],
						"itemHeight": 30*f}
					</convert>
				</widget>
				<ePixmap position="center,323*f" size="140*f,40*f" pixmap="skin_default/buttons/red.svg" \
					transparent="1" alphatest="blend" />
				<widget source="key_red" render="Label" position="center,328*f" zPosition="2" \
					size="140*f,30*f" valign="center" halign="center" font="Regular;22*f" transparent="1" />
				</screen>"""
	elif screenwidth == 1920:
		skin = """<screen position="center,center" size="945,555">
				<widget source="list" render="Listbox" position="center,45" size="900,405" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryText(pos=(15,1), size=(465,33), \
								font=0, flags=RT_HALIGN_LEFT, text=1), # Title
							MultiContentEntryText(pos=(345,1), size=(225,33), \
								font=0, flags=RT_HALIGN_RIGHT, text=2), # State
							MultiContentEntryProgress(pos=(585,6), size=(150,33), \
								percent=-3), # Progress
							MultiContentEntryText(pos=(750,1), size=(120,33), \
								font=0, flags=RT_HALIGN_LEFT, text=4), # Percentage
							],
						"fonts": [gFont("Regular",30)],
						"itemHeight": 45}
					</convert>
				</widget>
				<ePixmap position="center,484" size="210,60" pixmap="%s/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="center,485" zPosition="2" \
					size="210,60" valign="center" halign="center" font="Regular;33" transparent="1" />
				</screen>""" % BUTTONS_FOLDER
	else:
		skin = """<screen position="center,center" size="720,370">
				<widget source="list" render="Listbox" position="center,30" size="690,270" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryText(pos=(5,1), size=(270,22), \
								font=0, flags=RT_HALIGN_LEFT, text=1),  # Title
							MultiContentEntryText(pos=(280,1), size=(120,22), \
								font=0, flags=RT_HALIGN_RIGHT, text=2),  # State
							MultiContentEntryProgress(pos=(410,4), size=(100,22), \
								percent=-3), # Progress
							MultiContentEntryText(pos=(520,1), size=(80,22), \
								font=0, flags=RT_HALIGN_LEFT, text=4),  # Percentage
							MultiContentEntryText(pos=(600,1), size=(86,22), \
								font=0, flags=RT_HALIGN_RIGHT, text=5),  # Size
							],
						"fonts": [gFont("Regular",20)],
						"itemHeight": 30}
					</convert>
				</widget>
				<ePixmap position="center,323" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="center,328" zPosition="2" \
					size="140,30" valign="center" halign="center" font="Regular;22" transparent="1" />
				</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _('Active video downloads')
		self['key_red'] = StaticText(_('Exit'))
		self['list'] = List([])
		self['actions'] = ActionMap(['SetupActions', 'ColorActions'], {
				'cancel': self.close,
				'ok': self.ok,
				'red': self.close}, -2)
		self.onLayoutFinish.append(self.updateDownloadList)
		self.onClose.append(self.cleanVariables)
		self.progressTimer = eTimer()
		self.progressTimer.callback.append(self.updateDownloadList)

	def cleanVariables(self):
		del self.progressTimer

	def updateDownloadList(self):
		self.progressTimer.stop()
		download_list = []
		for job in job_manager.getPendingJobs():
			task = job.tasks[job.current_task]
			total_size = ''
			if hasattr(task, 'totalSize') and task.totalSize > 0:
				total_size = _('%.1fMB') % (task.totalSize / 1000000.0)
			download_list.append((job, '%s ...' % job.name, job.getStatustext(),
				int(task.progress), '%s%%' % str(task.progress), total_size))
		self['list'].list = download_list
		if download_list:
			self.progressTimer.startLongTimer(1)

	def ok(self):
		current = self['list'].getCurrent()
		if current:
			from Screens.TaskView import JobView
			self.session.open(JobView, current[0])
