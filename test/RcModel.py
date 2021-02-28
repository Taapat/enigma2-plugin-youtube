class RcModel:
	RcModels = {}

	def rcIsDefault(self):
		return None

	def getRcFile(self, ext):
		return ''

	def getRcImg(self):
		return self.getRcFile('png')

	def getRcPositions(self):
		return self.getRcFile('xml')

	def getRcFolder(self, GetDefault=True, *args):
		return 'enigma2/data/'


rc_model = RcModel()
