from PyTrilinos import Epetra, AztecOO, Anasazi, Amesos, EpetraExt

class TriSolver:  
  def __init__(self, nodeCount, mostCommonNonzeroEntriesPerRow, debug):
    
    """
    define the communicator (Serial or parallel, depending on your configure
    line), then initialize a distributed matrix.
    The matrix allocates mostCommonNonzeroEntriesPerRow, this makes the
    code run faster.
    `NumMyElements' is the number of rows that are locally hosted 
    by the calling processor; `MyGlobalElements' is the global ID of locally 
    hosted rows.
    """      

    self.debug= debug

    self.Comm              = Epetra.PyComm()
    self.NumGlobalElements = nodeCount
    self.Map               = Epetra.Map(self.NumGlobalElements, 0, self.Comm)
    self.A                 = Epetra.CrsMatrix(Epetra.Copy, self.Map, mostCommonNonzeroEntriesPerRow)
    self.NumMyElements     = self.Map.NumMyElements()
    self.MyGlobalElements  = self.Map.MyGlobalElements()
    self.b                 = Epetra.Vector(self.Map)
    self.mmPrefix          = "mm"
    self.mmExtension       = "mtx"
    

  def solveMatrixAmesos(self):
    """
    solveMatrixAmesos(Solver self)
    # self.x are the unknowns to be solved.
    # self.A is the sparse matrix describing the thermal matrix
    # self.b has the sources for heat and boundary conditions
    """
    iAmRoot = self.Comm.MyPID() == 0

    xmulti = Epetra.MultiVector(self.Map, 1, True)
    bmulti= Epetra.MultiVector(self.Map, 1, True)
    rowCount= self.A.NumGlobalRows()
    for row in range(0, rowCount):
      bmulti[0,row]= self.b[row]

    self.A.FillComplete()

    problem= Epetra.LinearProblem(self.A, xmulti, bmulti)
    solver= Amesos.Klu(problem)
    solver.SymbolicFactorization()
    solver.NumericFactorization()
    ierr = solver.Solve()

    xarr= Epetra.MultiVector.ExtractCopy(xmulti)
    xarrf= xarr.flatten()
    if iAmRoot:    
      print "Solver return status: " + str(ierr)    

    self.x = Epetra.Vector(xarrf)
    bCheck= Epetra.MultiVector(self.Map, 1)
    self.A.Multiply(False, self.x, bCheck)
    self.Comm.Barrier()

  def solveMatrixAztecOO(self, iterations):
    """
    solveMatrixAztecOO(Solver self, int iterations)
    Solve Ax=b with an interative solver.
    A is a sparse square matrix, x is a vector of unknowns, b is a vector of knowns
    This does not work very well as the main solver.
    Sometimes it converges very slowly.
    It might be useful for accuracy enhancement by doing one iteration
    after a direct solve, since it can get a better answer than numerical precision * condition number.
    """
    iAmRoot = self.Comm.MyPID() == 0

    self.x = Epetra.Vector(self.Map)

    try:
      self.A.FillComplete()     
    except:
      print "Oops can't fill self.A with: " + str(self.A)
      exit

    solver = AztecOO.AztecOO(self.A, self.x, self.b)
    solver.SetAztecOption(AztecOO.AZ_solver, AztecOO.AZ_cg_condnum)
    # This loads self.x with the solution to the problem
    ierr = solver.Iterate(iterations, 1e-10)

    if iAmRoot:
      print "Solver return status: " + str(ierr)
    self.Comm.Barrier()

  def solveEigen(self): 
    """
    solveEigen(Solver self)
    Solve for the largest and the smallest eigenvalues
    """
    iAmRoot = self.Comm.MyPID() == 0
    # Most that worked for 40x40 mesh: nev         = 30
    nev         = 2
    blockSize   = nev + 1
    numBlocks   = 2 * nev
    maxRestarts = 100000
    tol         = 1.0e-8

    print "Create the eigenproblem"
    self.A.FillComplete()    
    myProblem = Anasazi.BasicEigenproblem(self.A, self.b)

    print "Inform the eigenproblem that matrix is symmetric"
    myProblem.setHermitian(True)

    print "Set the number of eigenvalues requested"
    myProblem.setNEV(nev)

    print "All done defining problem"
    if not myProblem.setProblem():
      print "Anasazi.BasicEigenProblem.setProblem() returned an error"
      return -1

    smallEigenvaluesParameterList = {"Which" : "SM",   # Smallest magnitude
                                     "Block Size"            : blockSize,
                                     "Num Blocks"            : numBlocks,
                                     "Maximum Restarts"      : maxRestarts,
                                     "Convergence Tolerance" : tol,
                                     "Use Locking"           : True}

    smallestEigenvalue= 0.0
    largestEigenvalue= 0.0
    # The eigenvalue solver is unreliable, so handle exceptions.
    try:
      smSolverMgr = Anasazi.BlockDavidsonSolMgr(myProblem, smallEigenvaluesParameterList)
      smSolverMgr.solve()
      smallestEigenvalue= self.getFirstEigenvalue(myProblem, iAmRoot, nev, tol)
      if (smallestEigenvalue <= 0.0):
        print "zero or negative smallest eigenvalue"
    except:
      print "Oops no smallest eigenvalue"

    largeEigenvaluesParameterList = {"Which" : "LM",   # Largest magnitude
                                     "Block Size"            : blockSize,
                                     "Num Blocks"            : numBlocks,
                                     "Maximum Restarts"      : maxRestarts,
                                     "Convergence Tolerance" : tol,
                                     "Use Locking"           : True}

    # The eigenvalue solver is unreliable, so handle exceptions.
    try:
      lmSolverMgr = Anasazi.BlockDavidsonSolMgr(myProblem, largeEigenvaluesParameterList)
      lmSolverMgr.solve()
      largestEigenvalue= self.getFirstEigenvalue(myProblem, iAmRoot, nev, tol)
      if (largestEigenvalue <= 0.0):
        print "zero or negative largest eigenvalue"      
    except:
      print "Oops no largest eigenvalue"

    if ((largestEigenvalue != 0.0) & (smallestEigenvalue != 0.0)):
      print "Largest Eigenvalue: " + str(largestEigenvalue)
      print "Smallest Eigenvalue: " + str(smallestEigenvalue)
      condNumber= largestEigenvalue / smallestEigenvalue
      print "Condition number: " + str(condNumber)

  def getFirstEigenvalue(self, myProblem, iAmRoot, nev, tol):
    # Get the eigenvalues and eigenvectors
    sol = myProblem.getSolution()
    evals = sol.Evals()

    if (isinstance(evals, np.ndarray)):
      evecs = sol.Evecs()
      if (isinstance(evecs, Epetra.MultiVector)):
        index = sol.index
        if(isinstance(index, Anasazi.VectorInt)):    
          # Check the eigensolutions
          lhs = Epetra.MultiVector(self.Map, sol.numVecs)
          self.A.Apply(evecs, lhs)
          return evals[0].real
    return 0

  def saveMatrix(self):
    self.probFilename = self.mmPrefix + "A." + self.mmExtension
    self.rhsFilename = self.mmPrefix + "RHS." + self.mmExtension
    self.xFilename = self.mmPrefix + "x." + self.mmExtension

    EpetraExt.RowMatrixToMatrixMarketFile(self.probFilename, self.A)   
    EpetraExt.MultiVectorToMatrixMarketFile(self.rhsFilename, self.b)
    EpetraExt.MultiVectorToMatrixMarketFile(self.xFilename, self.x)