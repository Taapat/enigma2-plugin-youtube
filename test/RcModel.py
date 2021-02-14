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


rc_model = RcModel()
