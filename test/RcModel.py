class RcModel:
	RcModels = {}

	def rcIsDefault(self):
		return True

	def getRcFile(self, ext=''):
		return ext

	def getRcFolder(self, GetDefault=True):
		return 'enigma2/data/'

	def getRcImg(self):
		return self.getRcFile('enigma2/data/rc.png')

	def getRcPositions(self):
		return self.getRcFile('enigma2/data/rcpositions.xml')

	def getRcLocation(self):
		return self.getRcFile('enigma2/data/')


rc_model = RcModel()
