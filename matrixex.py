#!/Users/toma/python278i/bin/python

from PyTrilinos import Epetra, AztecOO

def main():

  # define the communicator (Serial or parallel, depending on your configure
  # line), then initialize a distributed matrix of size 4. The matrix is empty,
  # `0' means to allocate for 0 elements on each row (better estimates make the
  # code faster). `NumMyElements' is the number of rows that are locally hosted 
  # by the calling processor; `MyGlobalElements' is the global ID of locally 
  # hosted rows.
  Comm              = Epetra.PyComm()
  NumGlobalElements = 5
  Map               = Epetra.Map(NumGlobalElements, 0, Comm)
  A                 = Epetra.CrsMatrix(Epetra.Copy, Map, 0)
  NumMyElements     = Map.NumMyElements()
  MyGlobalElements  = Map.MyGlobalElements()
  print "MyGlobalElements =", MyGlobalElements

  # Solution for voltage source: 10, 4.1803, 1.7213,  1.475
  # Solution for current source:  0, 1.475,  5.901,   9.344
  # Total solution:              10, 5.656,  7.6133, 10.819

  R1 = 10.0
  R2 = 10.0
  R3 = 15.0
  R4 = 15.0
  R5 = 5.0
  R6 = 30.0

  # A is the problem matrix
  # Modified nodal analysis
  # http://www.swarthmore.edu/NatSci/echeeve1/Ref/mna/MNA2.html
  # node 0
  A[0, 0] = 1/R1
  # node 1
  A[1, 1] = 1/R1 + 1/R2 + 1/R3
  # node 2
  A[2, 2] = 1/R3 + 1/R4 + 1/R5
  # node 3
  A[3, 3] = 1/R5 + 1/R6
  # Common node impedances
  A[0, 1] = -1/R1
  A[1, 0] = -1/R1
  A[1, 2] = -1/R3
  A[2, 1] = -1/R3
  A[2, 3] = -1/R5
  A[3, 2] = -1/R5
  # Independent voltage source into node 0
  A[0, 4] = 1
  A[4, 0] = 1

  # b is the RHS
  b = Epetra.Vector(Map)
  b[0] = 0
  b[1] = 0
  b[2] = 0
  # This is the only term for a 1A current source injected into node 3
  b[3] = 1
  # This is the 10V voltage source going into node 0.
  # Current going in to the arrow of this source is in the solution as x[4]
  # In this example, the current flows in the direction of the arrow on the current source,
  # so the solution to the current is negative.
  b[4] = 10

  # x are the unknowns to be solved.
  x = Epetra.Vector(Map)
  
  A.FillComplete()

  solver = AztecOO.AztecOO(A, x, b)

  # This loads x with the solution to the problem
  solver.Iterate(1550, 1e-5)

  Comm.Barrier()

  for i in MyGlobalElements:
    print "PE%d: %d %e" % (Comm.MyPID(), i, x[i])
  
  # synchronize processors
  Comm.Barrier()

  if Comm.MyPID() == 0: print "End Result: TEST PASSED"

# This is a standard Python construct.  Put the code to be executed in a
# function [typically main()] and then use the following logic to call the
# function if the script has been called as an executable from the UNIX
# command
# line.  This also allows, for example, this file to be imported from a python
# debugger and main() called from there.
if __name__ == "__main__":
  main()
