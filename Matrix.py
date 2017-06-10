import math
import types
import operator
from numpy.linalg import inv
from numpy.linalg import eigvals
import numpy as np

class Matrix:
	null_element = 0
	identity_element = 1
	inverse_element = -1

	def __init__(self, *args):
		self.m = np.array(args[0])

	def __str__(self):
		s = ""
		for row in self.m:
			s += "%s\n" % row
		return s

	def __add__(self, other):
		"""Add matrix self+other
		"""
		return self.m+other

	def __neg__(self):
		"""Negate the current matrix
		"""
		return self.inverse_element*self.m

	def __sub__(self, other):
		"""Subtract matrix self-other
		"""
		return self.m+(self.inverse_element*other)

	def __mul__(self, other):
		"""Multiply matrix self*other

		other can be another matrix or a scalar.
		"""
		if isinstance(other,float) or isinstance(other,int):
			return self.scalar_multiply(other)
		return self.m*other

	def __rmul__(self, scalar):
		"""Multiply other*self

		This is only called if other.__add__ is not defined, so assume that
		other is a scalar.
		"""
		return scalar*self.m

	def scalar_multiply(self,scalar):
		return scalar*self.m

	def transpose(self):
		"""The transpose of the matrix
		"""
		r = np.transpose(self.m)
		return r

	def determinant(self):
		"""The determinant of the matrix
		"""
		return np.det(self.m)

	def inverse(self):
		"""The inverse of the matrix
		"""
		return np.linalg.inv(self.m)
	def autovalores(self):
		"""The eigenvalues of the matrix
		"""
		return np.linalg.eigvals(self.m)


def unit_matrix(n):
	"""Creates an nxn unit matirx

	The unit matrix is a diagonal matrix whose diagonal is composed of 
	identity elements.  For example, unit_matrix(3) returns the matrix

		1 0 0
		0 1 0
		0 0 1
	"""
	m = np.eye(n)
	return m

def row_vector(v):
	"""Creates a row vector.

	v is a list of the column values
	"""
	if not isinstance(v, types.ListType):
		raise TypeError("Row vector data must be a list")
	return Matrix([v])

def column_vector(v):
	"""Creates a column vector.

	v is a list of the row values
	"""
	if not isinstance(v, types.ListType):
		raise TypeError("Column vector data must be a list")
	return Matrix(map(lambda x: [x], v))
def print_matrix(A):
	print A