import Matrix

class Planta:

	def __init__(self):
		self.A = Matrix.Matrix([[-0.003749,0],[-0.003749,0.003749]])
		self.B = Matrix.Matrix([[0.2964],[0]])
		self.C = Matrix.Matrix([[0,1]])
		self.G = Matrix.Matrix([[0.99342173,0],[0.00655658,0.99342173]])
		self.H = Matrix.Matrix([[0.029634444],[0.029645556]])
		self.V = Matrix.Matrix([[1,1],[-0.003749,0]])
	def getA(self):
		return self.A
	def getB(self):
		return self.B
	def getC(self):
		return self.C
	def getG(self):
		return self.G
	def getH(self):
		return self.H
	def getV(self):
		return self.V
	def getVinv():
		return self.V.inverse()