import numpy
import sys

from PyTrilinos import Epetra, Galeri, Anasazi

def main():


   comm = Epetra.PyComm()
   iAmRoot = comm.MyPID() == 0




   nx = 10
   ny = nx
   galeriList = {"n"  : nx * ny,  # for Linear map
                 "nx" : nx,       # for Laplace2D, which requires nx
                 "ny" : ny        # and ny
                 }
   # Galeri is a package for creating systems with known properties for test purposes.
   # It creates matrix and map data structures.
   # The map maps nodes onto the Epetra cluster.  In this case all are local.
   # the matrix in this example is sparse, hermitian, positive semi-definite.
   # That is, it is symmetric, and all rows and columns add up to zero.
   # The different types of maps are documented in:
   # https://github.com/trilinos/trilinos/blob/master/packages/galeri/doc/matrices.doc
   map    = Galeri.CreateMap("Linear", comm, galeriList)
   name   = "Laplace2D"
   matrix = Galeri.CreateCrsMatrix(name, map, galeriList)
   if iAmRoot: 
      print "Problem name: %s\n" % name
      print "Map:\n" + str(map)
      print "Matrix:\n" + str(matrix)




   # printer = Anasazi.BasicOutputManager()

   nev         = 4
   blockSize   = 5
   numBlocks   = 8
   maxRestarts = 100
   tol         = 1.0e-8
   ivec = Epetra.MultiVector(map, blockSize)
   ivec.Random()

   # Create the eigenproblem
   myProblem = Anasazi.BasicEigenproblem(matrix, ivec)

   # Inform the eigenproblem that matrix is symmetric
   myProblem.setHermitian(True)

   # Set the number of eigenvalues requested
   myProblem.setNEV(nev)

   # All done defining problem
   if not myProblem.setProblem():
      print "Anasazi.BasicEigenProblem.setProblem() returned an error"
      return -1

   # Define the parameter list
   myPL = {"Which"                 : "LM",
           "Block Size"            : blockSize,
           "Num Blocks"            : numBlocks,
           "Maximum Restarts"      : maxRestarts,
           "Convergence Tolerance" : tol }

   # Create the solver manager
   mySolverMgr = Anasazi.BlockDavidsonSolMgr(myProblem, myPL)

   # Solve the problem
   returnCode = mySolverMgr.solve()

   # Get the eigenvalues and eigenvectors
   sol = myProblem.getSolution()
   evals = sol.Evals()
   assert(isinstance(evals, numpy.ndarray))
   evecs = sol.Evecs()
   assert(isinstance(evecs, Epetra.MultiVector))
   index = sol.index
   assert(isinstance(index, Anasazi.VectorInt))

   # Check the eigensolutions
   lhs = Epetra.MultiVector(map, sol.numVecs)
   matrix.Apply(evecs, lhs)
   if iAmRoot:
      print "Eig#  Value     Error"
      print "----  --------  ----------"
   failures = 0
   for i in range(nev):
      # Verify that the eigensolution is non-complex
      assert(index[i] == 0)
      rhs   = evecs[i] * evals[i].real
      diff  = lhs[i] - rhs
      diff.Scale(1.0/abs(evals[i].real))
      error = diff.Norm2()[0]
      if iAmRoot:
         print "%4d%10.4f  %10.4e" % (i, evals[i].real, error)
      if (error > tol):
         failures += 1

   totalFailures = comm.SumAll(failures)
   return totalFailures

################################################################################

if __name__ == "__main__":

   comm     = Epetra.PyComm()
   iAmRoot  = comm.MyPID() == 0
   failures = main()
   if iAmRoot:
      print
      if failures == 0:
         print "End Result: TEST PASSED"
      else:
         print "Eigensolution errors are too large"
         print "End Result: TEST FAILED"
