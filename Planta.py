import math
import types
import operator
from numpy.linalg import inv
from numpy.linalg import eigvals
import numpy as np

class Planta:

	def __init__(self):
		self.A = np.array([[-0.003749,0],[-0.003749,0.003749]])
		self.B = np.array([[0.2964],[0.0]])
		self.C = np.array([[0.0,1.0]])
		self.G = np.array([[0.99342173,0.0],[0.00655658,0.99342173]])
		self.H = np.array([[0.029634444],[0.029645556]])
		self.V = np.array([[1.0,1.0],[-0.003749,0.0]])
		self.GA = np.array([[0.99342173,0.0,0.029634444],[0.00655658,0.99342173,0.029645556],[0.0,0.0,0.0]])
		self.HA = np.array([[0.0],[0.0],[1.0]])
		self.W = np.array([[0,0.0295461,0.0293528],[0,0.0000968713,0.000288922],[1.0,0.0,0.0]])
		self.P = np.array([[-0.00655658,0.0,0.0286709],[0.00655658,-0.00655658,0.0009718],[1.0,0.99344031,0.0296437]])
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
	def getGA(self):
		return self.GA
	def getHA(self):
		return self.HA
	def getW(self):
		return self.W
	def getP(self):
		return self.P
	def getVinv(self):
		return np.linalg.inv(self.V)
	def getWinv(self):
		return np.linalg.inv(self.W)
	def getPinv(self):
		return np.linalg.inv(self.P)