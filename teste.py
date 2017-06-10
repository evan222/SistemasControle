import Matrix

A = Matrix.Matrix([[1,1],[2,2]])
B = Matrix.Matrix([[1,3],[1,1]])
M = Matrix.Matrix([[0,1]]).transpose()


C = A-B
D = A*B
E = C*D*M


print A-B
print A*B
print 2*A
print C
print C+D
print C*D*M
print E