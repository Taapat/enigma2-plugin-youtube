from enigma import eTimer, getDesktop
from Components.ActionMap import ActionMap
from Components.FileList import FileList
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Task import Task, Job, job_manager
from Screens.Screen import Screen
from Tools.Downloader import downloadWithProgress


class YouTubeDirBrowser(Screen):
	def __init__(self, session, downloadDir):
		Screen.__init__(self, session)
		self.skinName = ['YouTubeDirBrowser', 'FileBrowser']
		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('Use'))
		self.filelist = FileList(downloadDir, showFiles = False)
		self['filelist'] = self.filelist
		self['FilelistActions'] = ActionMap(['SetupActions', 'ColorActions'],
			{
				'cancel': self.cancel,
				'red': self.cancel,
				'ok': self.ok,
				'green': self.use
			}, -2)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('Please select the download directory'))

	def ok(self):
		if self.filelist.canDescent():
			self.filelist.descent()

	def use(self):
		currentDir = self['filelist'].getCurrentDirectory()
		dirName = self['filelist'].getFilename()
		if currentDir is None or \
			(self.filelist.canDescent() and dirName and len(dirName) > len(currentDir)):
			self.close(dirName)

	def cancel(self):
		self.close(False)


class downloadJob(Job):
	def __init__(self, url, outputfile, title):
		Job.__init__(self, title)
		downloadTask(self, url, outputfile)


class downloadTask(Task):
	def __init__(self, job, url, outputfile):
		Task.__init__(self, job, _('Downloading'))
		self.url = url
		self.outputfile = outputfile

	def run(self, callback):
		self.callback = callback
		self.download = downloadWithProgress(self.url, self.outputfile)
		self.download.addProgress(self.downloadProgress)
		self.download.start().addCallback(self.downloadFinished)\
			.addErrback(self.downloadFailed)

	def downloadProgress(self, currentbytes, totalbytes):
		self.progress = int(currentbytes / float(totalbytes) * 100)

	def downloadFinished(self, result):
		Task.processFinished(self, 0)

	def downloadFailed(self, failure_instance=None, error_message=''):
		print '[YouTube] Video download failed'
		if error_message == '' and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			print '[YouTube]', str(error_message)
		Task.processFinished(self, 1)


class YouTubeDownloadList(Screen):
	screenWidth = getDesktop(0).size().width()
	if screenWidth and screenWidth == 1920:
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
				<ePixmap position="center,484" size="210,60" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="center,485" zPosition="2" \
					size="210,60" valign="center" halign="center" font="Regular;33" transparent="1" />
				</screen>"""
	else:
		skin = """<screen position="center,center" size="630,370">
				<widget source="list" render="Listbox" position="center,30" size="600,270" \
					scrollbarMode="showOnDemand" >
					<convert type="TemplatedMultiContent" >
						{"template": [
							MultiContentEntryText(pos=(10,1), size=(210,22), \
								font=0, flags=RT_HALIGN_LEFT, text=1), # Title
							MultiContentEntryText(pos=(230,1), size=(150,22), \
								font=0, flags=RT_HALIGN_RIGHT, text=2), # State
							MultiContentEntryProgress(pos=(390,4), size=(100,22), \
								percent=-3), # Progress
							MultiContentEntryText(pos=(500,1), size=(80,22), \
								font=0, flags=RT_HALIGN_LEFT, text=4), # Percentage
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
		self['key_red'] = StaticText(_('Exit'))
		self['list'] = List([])
		self['actions'] = ActionMap(['SetupActions', 'ColorActions'],
			{
				'cancel': self.close,
				'ok': self.ok,
				'red': self.close
			}, -2)
		self.onLayoutFinish.append(self.layoutFinished)
		self.onClose.append(self.cleanVariables)
		self.progressTimer = eTimer()
		self.progressTimer.callback.append(self.updateDownloadList)

	def layoutFinished(self):
		self.setTitle(_('Active video downloads'))
		self.updateDownloadList()

	def cleanVariables(self):
		del self.progressTimer
		
	def updateDownloadList(self):
		self.progressTimer.stop()
		downloadList = []
		for job in job_manager.getPendingJobs():
			progress = job.progress / float(job.end) * 100
			downloadList.append((job, job.name, job.getStatustext(),
				int(progress), str(progress) + "%" ))
		self['list'].updateList(downloadList)
		if downloadList:
			self.progressTimer.startLongTimer(2)

	def ok(self):
		current = self['list'].getCurrent()
		if current:
			from Screens.TaskView import JobView
			self.session.open(JobView, current[0])

