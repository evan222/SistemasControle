import math
import types
import operator
from numpy.linalg import inv
from numpy.linalg import eigvals
import numpy as np

class Planta:

	def __init__(self):
		self.A = np.array([[-0.0655969,0],[0.0655969,-0.0655969]])
		self.B = np.array([[0.2964],[0]])
		self.C = np.array([[1,1]])
		self.G = np.array([[0.99342173,0],[0.00655658,0.99342173]])
		self.H = np.array([[0.0286709],[0.0009718]])
		self.V = np.array([[1,1],[0,-0.0655969]])
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
	def getVinv(self):
		return np.linalg.inv(self.V)
