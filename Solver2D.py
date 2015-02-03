import numpy as np
from collections import Counter
from PyTrilinos import Epetra, AztecOO, Anasazi, Amesos, EpetraExt
import Spice2D
import MatrixDiagnostic
import MatrixMarket as mm
import MMHtml

#
# DELAY REFACTORING: After holes are implemented, a lot of this class
# will go away, which will make refactoring much easier.
# TODO: Methods here should be in four stages:
#   Mesh by loading layers from PNG
#     Board outline
#     Drilled holes
#     Via holes
#     Routed holes and cutouts
#     Via copper
#     Copper layers and prepreg/air
#     Cores
#     Thermal pads
#     Shields/boundary conditions 
#   Create Matrix Market problem file
#   Solve Matrix
#   Check energy balance
#   Create Matrix Market solution file
#   Unload solution back into mesh
# Might need to move some routines from here back into the mesh class.
# The Matrix loader also loads the shadow matrix.
# The solver should only have access to the matrix, not the mesh or layers.
# 
# Right now it is a bit messy that Spice, for example, would be spread
# across multiple classes. Might need a dispatch loader, solver, and unloader
# to implement independent classes for these different approaches.
#
# Refactor for separate debug flags for printing details, shadowing the matrix,
# creating Matrix Market files, and HTML matrix creation.
#


class Solver:
  """
  The Solver class loads a matrix and solves it.
  It also optionally loads a spice netlist and a debugging structure.
  
    The analysis is of the form  Ax = b
    The rows in b are the known value of the current (constant power in thermal circuits) sources

    The total number of rows in A is self.nodeCount
  
    The solution to the matrix is the vector x. These are voltages (temperature)
  
    For energy balance in steady state, the current into the constant-temperature boundary condition 
    must equal the current from the constant-power thermal sources.

  """

  def __init__(self, config, nodeCount):
    
    self.initEpetra(nodeCount)
    
    self.useSpice          = False
    self.useAztec          = False
    self.useAmesos         = False
    self.useEigen          = False 
    foundSolver= 0
    for solver in config['solvers']:
      if solver['active'] == 1:
        if (solver['solverName'] == "Eigen"):
          self.useEigen = True
        if (solver['solverName'] == "Aztec"):
          self.useAztec = True
        if (solver['solverName'] == "Amesos"):
          self.useAmesos = True  
        if (solver['solverName'] == "Spice"):
          self.useSpice = True
          self.spice= Spice2D.Spice(solver['simbasename'])
    if (self.useSpice == False):
      self.spice= None       
  
    for solver in config['solverFlags']:
      self.__dict__[solver['flag']] = solver['setting']

    self.totalBoundaryCurrent = 0.0
    self.totalInjectedCurrent = 0.0

    if self.debug == True:
      """
      Create a shadow matrix as a duplicate of A and a shadow RHS as duplicate of b.
      These are easier to access than self.A and self.b, which are opaque.
      """
      self.As = np.zeros((self.NumGlobalElements, self.NumGlobalElements), dtype = 'double')
      self.bs = np.zeros(self.NumGlobalElements)
      self.debugWebPage= config['solverDebug']['debugWebPage']
      self.mmPrefix= config['solverDebug']['mmPrefix']

    
  def initEpetra(self, nodeCount):
    """
    define the communicator (Serial or parallel, depending on your configure
    line), then initialize a distributed matrix of size 4. The matrix is empty,
    `0' means to allocate for 0 elements on each row (better estimates make the
    code faster). `NumMyElements' is the number of rows that are locally hosted 
    by the calling processor; `MyGlobalElements' is the global ID of locally 
    hosted rows.
    """     

    mostCommonNonzeroEntriesPerRow = 5
    self.Comm              = Epetra.PyComm()
    self.NumGlobalElements = nodeCount
    self.Map               = Epetra.Map(self.NumGlobalElements, 0, self.Comm)
    self.A                 = Epetra.CrsMatrix(Epetra.Copy, self.Map, mostCommonNonzeroEntriesPerRow)
    self.NumMyElements     = self.Map.NumMyElements()
    self.MyGlobalElements  = self.Map.MyGlobalElements()
    self.b                 = Epetra.Vector(self.Map)
    self.boundaryCondVec   = Epetra.Vector(self.Map)
    self.boundaryCondMatl  = Epetra.Vector(self.Map)

    self.deck              = ''
    self.GDamping          = 1e-12 # Various values such as 1e-12, 1e-10, and -1e-10 have worked or not!
                                   # Is only important to the iterative solver
    self.s                 = 'U'   # Delimiter between x and y values in spice netlist.
    
    self.BodyNodeCount              = 0
    self.TopEdgeNodeCount           = 0
    self.RightEdgeNodeCount         = 0
    self.BottomEdgeNodeCount        = 0
    self.LeftEdgeNodeCount          = 0
    self.TopLeftCornerNodeCount     = 0
    self.TopRightCornerNodeCount    = 0
    self.BottomRightCornerNodeCount = 0
    self.BottomLeftCornerNodeCount  = 0
    self.BoundaryNodeCount          = 0
    # Make a python shadow data structure that records what is inside the Epetra data structures.
    # This is a non-sparse version used for debugging.
    # This can be used to print out what is going on.
    # Without it, the data structure is hard to access.
    self.bs= []
    self.x= []    

  def solve(self, lyr, mesh, matls):
    for nodeThis in range(0, self.NumGlobalElements):
      self.boundaryCondVec[nodeThis] = -512.0
      self.boundaryCondMatl[nodeThis] = 0.0
      
    self.loadMatrix(lyr, mesh, matls, self.spice)
    
    if (self.useEigen == True):
      print "Solving for eigenvalues"
      self.solveEigen()
      print "Finished solving for eigenvalues"
    
    if (self.useSpice == True):
      self.solveSpice(mesh, lyr)
      
    if (self.useAztec == True):
      self.solveAztecOO(mesh, lyr)
      
    if (self.useAmesos == True):
      self.solveAmesos(mesh, lyr)  
      
    if (self.debug == True):
      webpage = MatrixDiagnostic.MatrixDiagnosticWebpage(self, lyr, mesh)
      webpage.createWebPage()        
      self.debugMatrix()

  def debugMatrix(self):
    # TODO: Use config to name and position these 4 files:

    probFilename = self.mmPrefix + "A.mm"
    rhsFilename = self.mmPrefix + "RHS.mm"
    xFilename = self.mmPrefix + "x.mm"
    htmlFilename = self.mmPrefix + "AxRHS.html"
    #if options.verbose:
        #print "Creating files " + probFilename + " " + rhsFilename + " " + xFilename
    EpetraExt.RowMatrixToMatrixMarketFile(probFilename, self.A)   
    EpetraExt.MultiVectorToMatrixMarketFile(rhsFilename, self.b)
    EpetraExt.MultiVectorToMatrixMarketFile(xFilename, self.x)
    
    MMHtmlWriter= MMHtml.MMHtml()
    MMReaderRHS= mm.MatrixMarket()
    MMRHS= MMReaderRHS.read(rhsFilename) 
    
    MMReaderX= mm.MatrixMarket()
    MMX= MMReaderX.read(xFilename)     
    
    MMReaderMMA= mm.MatrixMarket()     
    MMA= MMReaderMMA.read(probFilename)
    MMHtmlWriter.writeHtml([MMA, MMX, MMRHS], htmlFilename)     

  def loadMatrix(self, lyr, mesh, matls, spice):
    """
    The field transconductance matrix A is in nine sections:
      
        top left corner      |     top edge      |     top right corner
        left edge            |     body          |     right edge
        bottom left corner   |     bottom edge   |     bottom right corner
    
    """

    self.loadMatrixBodyWithHoles(lyr, mesh, spice, matls)  
    self.loadMatrixHeatSources(lyr, mesh)
    
    if self.useSpice == True:
      self.loadBodySpiceWithHoles(lyr, mesh, spice)    
      self.loadSpiceHeatSources(lyr, mesh, spice)

  def loadMatrixHeatSources(self, lyr, mesh):
    """
    b is the RHS, which are current sources for injected heat.
    This routine takes heat sources from the field and puts them in the matrix RHS.
    """
    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      self.b[nodeThis] += mesh.field[x, y, lyr.heat]
      self.totalInjectedCurrent += mesh.field[x, y, lyr.heat]
      if self.debug == True:
        self.bs[nodeThis]= mesh.field[x, y, lyr.heat]
            
  def loadSpiceHeatSources(self, lyr, mesh, spice):
    """
    Add spice current sources for injected heat
    """
    if self.useSpice == False:
      return
    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      if (mesh.field[x, y, lyr.heat] != 0.0):
        thisSpiceNode=   "N" + str(x) + self.s + str(y)
        thisHeatSource=   "I" + thisSpiceNode
        thisHeat= -mesh.field[x, y, lyr.heat]
        spice.appendSpiceNetlist(thisHeatSource + " " + thisSpiceNode + " 0 DC " + str(thisHeat) + "\n")


  # This is the bottleneck
  # RAM requirement is about 1kb/mesh element.
  
  def loadMatrixBodyWithHoles(self, lyr, mesh, spice, matls):
    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      nodeResis = mesh.field[x, y, lyr.resis]
      GNode= self.GDamping        
      
      nodeRight = mesh.getNodeAtXY(x+1, y)
      if nodeRight >= 0:
        nodeRightResis= mesh.field[x+1, y, lyr.resis]
        GRight= 2.0/(nodeResis + nodeRightResis)
        GNode += GRight
        if (self.useAztec == True) or (self.useAmesos == True):
          self.A[nodeThis, nodeRight]= -GRight
          self.A[nodeRight, nodeThis]= -GRight
        if self.debug == True:
          self.As[nodeThis, nodeRight]= -GRight
          self.As[nodeRight, nodeThis]= -GRight
      
      nodeUp = mesh.getNodeAtXY(x, y-1)
      if nodeUp >= 0:
        nodeUpResis= mesh.field[x, y-1, lyr.resis]
        GUp= 2.0/(nodeResis + nodeUpResis)
        GNode += GUp
        if (self.useAztec == True) or (self.useAmesos == True):
          self.A[nodeThis, nodeUp]= -GUp
          self.A[nodeUp, nodeThis]= -GUp
        if self.debug == True:
          self.As[nodeThis, nodeUp]= -GUp
          self.As[nodeUp, nodeThis]= -GUp
      
      nodeLeft = mesh.getNodeAtXY(x-1, y)
      if nodeLeft >= 0:
        nodeLeftResis=  mesh.field[x-1, y,   lyr.resis]
        GLeft= 2.0/(nodeResis + nodeLeftResis)
        GNode += GLeft
        if (self.useAztec == True) or (self.useAmesos == True):
          self.A[nodeThis, nodeLeft]= -GLeft
          self.A[nodeLeft, nodeThis]= -GLeft
        if self.debug == True:
          self.As[nodeThis, nodeLeft]= -GLeft
          self.As[nodeLeft, nodeThis]= -GLeft
      
      nodeDown = mesh.getNodeAtXY(x, y+1)        
      if nodeDown >= 0:
        nodeDownResis=  mesh.field[x, y+1, lyr.resis]        
        GDown= 2.0/(nodeResis + nodeDownResis)        
        GNode += GDown
        if (self.useAztec == True) or (self.useAmesos == True):
          self.A[nodeThis, nodeDown]= -GDown
          self.A[nodeDown, nodeThis]= -GDown
        if self.debug == True:
          self.As[nodeThis, nodeDown]= -GDown
          self.As[nodeDown, nodeThis]= -GDown

      self.BodyNodeCount += 1
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        if self.debug == True:
          print "Setting boundaryNode body", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)

      if (self.useAztec == True) or (self.useAmesos == True):
        self.A[nodeThis, nodeThis]= GNode
        
      if self.debug == True:
        self.As[nodeThis, nodeThis]= GNode

  def loadBodySpiceWithHoles(self, lyr, mesh, spice):

    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      nodeThis = mesh.ifield[x, y, lyr.holeflag]
      nodeResis = mesh.field[x, y, lyr.resis]
      GNode= self.GDamping        
      
      thisSpiceNode=   "N" + str(x)   + self.s + str(y)
      mesh.spiceNodeXName[thisSpiceNode] = x
      mesh.spiceNodeYName[thisSpiceNode] = y      
    
      nodeRight = mesh.getNodeAtXY(x+1, y)
      if nodeRight >= 0:
        nodeRightResis= mesh.field[x+1, y, lyr.resis]
        RRight= (nodeResis + nodeRightResis)/2.0
        spiceNodeRight=  "N" + str(x+1) + self.s + str(y)
        nodeRightResis= mesh.field[x+1, y,   lyr.resis]
        spice.appendSpiceNetlist("RFR" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n")
        
      nodeDown = mesh.getNodeAtXY(x, y+1)        
      if nodeDown >= 0:
        nodeDownResis=  mesh.field[x, y+1, lyr.resis]                  
        RDown=  (nodeResis + nodeDownResis)/2.0
        spiceNodeDown=   "N" + str(x)   + self.s + str(y+1)
        nodeDownResis=  mesh.field[x,   y+1, lyr.resis]
        spice.appendSpiceNetlist("RFD" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n")

  def addIsoNode(self, lyr, mesh, spice, matls, nodeThis, x, y, GNode):
    """
    The node at x, y gets on-diagonal conductance incremented by the amount of conductance in the boundary.
    b is the RHS. It gets the current source which is mesh.field[x, y, lyr.isodeg] * matls.boundCond    
    """
    GNode = GNode + matls.boundCond
    self.A[nodeThis, nodeThis] = GNode
    
    if mesh.ifield[x, y, lyr.isoflag] == 1:
      self.b[nodeThis] = mesh.field[x, y, lyr.isodeg] * matls.boundCond
      self.boundaryCondVec[nodeThis] = mesh.field[x, y, lyr.isodeg]
      self.boundaryCondMatl[nodeThis] = matls.boundCond
    else:
      self.b[nodeThis] = 0.0

    if self.debug == True:
      self.bs[nodeThis]= self.b[nodeThis]
      self.As[nodeThis, nodeThis]= GNode    
      
    if self.useSpice == True:
      thisSpiceNode=   "N" + str(x)   + self.s + str(y)
      # Norton equivalent boundary resistance and current source.
      thisIsoSource=   "I" + thisSpiceNode
      
      thisBoundaryNode=  "NDIRI" + self.s + str(x) + self.s + str(y)
      thisBoundaryResistor=  "RDIRI" + self.s + str(x) + self.s + str(y)
      thisBoundaryResistance= 1.0/matls.boundCond
      
      thisBoundaryCurrent= mesh.field[x, y, lyr.isodeg]/thisBoundaryResistance
      spice.appendSpiceNetlist(thisIsoSource + " 0 " + thisSpiceNode + " DC " + str(thisBoundaryCurrent) + "\n")
      spice.appendSpiceNetlist(thisBoundaryResistor + " " + thisSpiceNode + " 0 " + str(thisBoundaryResistance) + "\n")

    self.BoundaryNodeCount += 1
    return GNode
            
  def loadSolutionIntoMesh(self, lyr, mesh):
    """
    loadSolutionIntoMesh(Solver self, Layers lyr, Mesh mesh)
    Load the solution back into a layer on the mesh
    """
    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      mesh.field[x, y, lyr.deg] = self.x[nodeThis]
      # print "Temp x y t ", x, y, self.x[nodeThis]               
            
# Below this point the methods don't know if the mesh is 2D  
# This module is too long, and could be broken into loaders, solvers, and unloaders.
# The solvers should be shared with 3D code, also.
            
            
  def nonzeroMostCommonCount(self):
    """
    Find the most common number of nonzero elements in the A matrix.
    Loading this into the Trilinos solver speeds it up.
    """
     
    rowCountHist = Counter()    
    mat= self.As
    rowCount, colCount= mat.shape
    rowIndex= 0
    for row in range(0, rowCount-1): 
      row = np.array(self.As[row])
      nonzero = np.count_nonzero(row)
      rowCountHist[nonzero] += 1
      # print "Nonzero elts in row " + str(rowIndex) + " = " + str(nonzero)
      rowIndex += 1
    mostCommon= rowCountHist.most_common(1)
    mostCommonValue= mostCommon[0][0]
#   print str(rowCountHist)
#   print str(mostCommonValue)
    return mostCommonValue
  
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
      # print "row: " + str(row) + " " + str(self.b[row])
      
    # print "LHS: " + str(xmulti)
    # print "RHS: " + str(bmulti)
    self.A.FillComplete()
    # print "Matrix: " + str(self.A)

    problem= Epetra.LinearProblem(self.A, xmulti, bmulti)
    # print "Problem: " + str(problem)
    solver= Amesos.Klu(problem)
    # print "Solver before solve: " + str(solver)
    solver.SymbolicFactorization()
    solver.NumericFactorization()
    ierr = solver.Solve()
    # print "Solver after solve: " + str(solver)
     
    xarr= Epetra.MultiVector.ExtractCopy(xmulti)
    xarrf= xarr.flatten()
    if iAmRoot:    
      print "Solver return status: " + str(ierr)    
      # print "xmulti, raw" + str(xmulti)
      # print "xmulti. flattened" + str(xarrf)
    
    self.x = Epetra.Vector(xarrf)
    # At this point multiply by self.A to see if it matches self.b
    bCheck= Epetra.MultiVector(self.Map, 1)
    self.A.Multiply(False, self.x, bCheck)
    # print "bCheck: " + str(bCheck)
    # print "x result:" + str(self.x)
    self.Comm.Barrier()

  def solveMatrixAztecOO(self, iterations):
    """
    solveMatrixAztecOO(Solver self, int iterations)
    Solve Ax=b with an interative solver.
    This does not work very well as the main solver.
    Sometimes it converges very slowly.
    It might be useful for accuracy enhancement by doing one iteration
    after a direct solve, since it can get a better answer than numerical precision * condition number.
    """
    # x are the unknowns to be solved.
    # A is the sparse matrix describing the thermal matrix
    # b has the current sources for heat and Dirichlet boundary conditions
    iAmRoot = self.Comm.MyPID() == 0
    
    self.x = Epetra.Vector(self.Map)
    
    try:
      self.A.FillComplete()     
    except:
      print "Oops can't fill self.A with: " + str(self.A)
      exit
    
    # self.A.FillComplete()
    solver = AztecOO.AztecOO(self.A, self.x, self.b)
    solver.SetAztecOption(AztecOO.AZ_solver, AztecOO.AZ_cg_condnum)
    # This loads x with the solution to the problem
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
    # print "evals: " + str(evals)
    if (isinstance(evals, np.ndarray)):
      evecs = sol.Evecs()
      # print "evecs: " + str(evecs)
      if (isinstance(evecs, Epetra.MultiVector)):
        index = sol.index
        if(isinstance(index, Anasazi.VectorInt)):    
          # Check the eigensolutions
          lhs = Epetra.MultiVector(self.Map, sol.numVecs)
          self.A.Apply(evecs, lhs)
          return evals[0].real
    return 0

  def checkEnergyBalance(self, lyr, mesh):
    """
    checkEnergyBalance(Solver self, Layers lyr, Mesh mesh)
    Compare the power input of the simulation to the power output.
    The power input is from the current sources and the 
    power output is into the boundary conditions.
    """
    # boundaryPowerOut is the current in the boundary resistors that are not due to the boundary current source.
    self.totalMatrixPower = 0.0
    self.boundaryPowerOut = 0.0    
          
    print "n, x, b, bcCond, totalMatrixPower, boundaryPowerOut"              
    nodecount= mesh.solveTemperatureNodeCount()
    for n in range(0, nodecount):
      self.totalMatrixPower += self.b[n]
      if self.boundaryCondVec[n] == -512.0:
        self.totalBoundaryCurrent += self.b[n]
      else:
        self.boundaryPowerOut += (self.x[n] - self.boundaryCondVec[n]) * self.boundaryCondMatl[n]
      # print str(n) + ", " + str(self.x[n]) + ", " + str(self.b[n]) + ", " + str(self.boundaryCondVec[n]) + ", " + str(self.totalMatrixPower) + ", " + str(self.boundaryPowerOut)
    
    print "Total Injected Designed Power = " + str(self.totalInjectedCurrent)
    print "Total Injected Matrix Power = " + str(self.totalBoundaryCurrent)
    print "Total Boundary Power Including Norton current sources = ", self.totalMatrixPower
    print "Total Power Calculated from Boundary temperature rise = ", self.boundaryPowerOut

  def solveAmesos(self, mesh, lyr):
    self.solveMatrixAmesos()
    self.loadSolutionIntoMesh(lyr, mesh)
    self.checkEnergyBalance(lyr, mesh)
    
  def solveAztecOO(self, mesh, lyr):
    self.solveMatrixAztecOO(400000)
    self.loadSolutionIntoMesh(lyr, mesh)
    self.checkEnergyBalance(lyr, mesh)   

  def solveSpice(self, mesh, lyr):
    self.spice.finishSpiceNetlist()
    proc= self.spice.runSpiceNetlist()
    proc.wait()
    self.spice.readSpiceRawFile(lyr, mesh)       
      
    