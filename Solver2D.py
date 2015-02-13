import numpy as np
from collections import Counter

import TriSolver
import SpSolver
import MatrixDiagnostic
import MatrixMarket as mm
import MMHtml


# Numpy solver documentation: 
# See http://docs.scipy.org/doc/numpy/reference/generated/numpy.linalg.solve.html#numpy.linalg.solve


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


class Solver2D:
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
    
    self.NumGlobalElements = nodeCount
    
    self.deck              = ''
    self.GDamping          = 0
    # self.GDamping          = 1e-12  # Various values such as 1e-12, 1e-10, and -1e-10 have worked or not!
                                    # Is only important to the iterative solver
    self.s                 = 'U'    # Delimiter between x and y values in spice netlist.
  
    self.BoundaryNodeCount          = 0
    # Make a python shadow data structure that records what is inside the Epetra data structures.
    # This is a non-sparse version used for debugging.
    # This can be used to print out what is going on.
    # Without it, the data structure is hard to access.
    self.bs= []
  
    # These are for keeping track of the boundary condition power in the Norton equivalent,
    # so that energy balance can be checked.
    self.boundaryCondVec = np.zeros(self.NumGlobalElements, dtype = 'double')
    self.boundaryCondMatl = np.zeros(self.NumGlobalElements, dtype = 'double')    

    self.useSpice          = False
    self.useAztec          = False
    self.useAmesos         = False
    self.useEigen          = False 
    self.useTrilinos       = False
    self.useNumpy          = False
    foundSolver= 0
    for solver in config['solvers']:
      if solver['active'] == 1:
        if (solver['solverName'] == "Eigen"):
          self.useEigen = True
          self.useTrilinos = True
        if (solver['solverName'] == "Aztec"):
          self.useAztec = True
          self.useTrilinos = True
        if (solver['solverName'] == "Amesos"):
          self.useAmesos = True
          self.useTrilinos = True
        if (solver['solverName'] == "Numpy"):
          self.useNumpy = True        
        if (solver['solverName'] == "Spice"):
          self.useSpice = True
          self.spice= SpSolver.SpSolver(solver['simbasename'])
          
    if (self.useSpice == False):
      self.spice= None       
  
    for solver in config['solverFlags']:
      self.__dict__[solver['flag']] = solver['setting']
      
    if self.useTrilinos == True:
      mostCommonNonzeroEntriesPerRow = 5
      self.solver= TriSolver.TriSolver(nodeCount, mostCommonNonzeroEntriesPerRow, self.debug)

    self.totalBoundaryCurrent = 0.0
    self.totalInjectedCurrent = 0.0

    if self.useNumpy == True:
      """
      Create a dense matrix As and a RHS bs.
      This data is used with a dense matrix Numpy solver.
      This is useful for debugging and might be faster for small problems.
      Numpy also has sparse matrices and solvers, and these may also be suitable.
      """    
      self.As = np.zeros((self.NumGlobalElements, self.NumGlobalElements), dtype = 'double')
      self.bs = np.zeros(self.NumGlobalElements)
      
    if self.webPage:
      self.debugWebPage= config['solverDebug']['debugWebPage']
      
    if self.matrixMarket:
      self.mmPrefix= config['solverDebug']['mmPrefix']

  def solve(self, lyr, mesh, matls):
    self.loadBoundaryCondition(lyr, mesh, matls)
    
    if (self.useSpice == True):
      self.loadSpiceNetwork(lyr, mesh, matls, self.spice)    
      self.loadSpiceHeatSources(lyr, mesh, self.spice)      
      self.solveSpice(mesh, lyr)
      
    if (self.useAztec == True):
      self.loadMatrix(lyr, mesh, matls, self.solver.A, self.solver.b)
      self.solveAztecOO(mesh, lyr)
      if (self.useEigen == True):
        print "Solving for eigenvalues"
        self.solveEigen()
        print "Finished solving for eigenvalues"      
      
    if (self.useAmesos == True):
      self.loadMatrix(lyr, mesh, matls, self.solver.A, self.solver.b)
      self.solveAmesos(mesh, lyr)  
      if (self.useEigen == True):
        print "Solving for eigenvalues"
        self.solveEigen()
        print "Finished solving for eigenvalues"      
      
    if (self.useNumpy == True):
      self.loadMatrix(lyr, mesh, matls, self.As, self.bs)
      self.solveNumpy(mesh, lyr)
      
    if (self.debug == True):
      self.printNumpy()
      
    if (self.webPage == True):
      self.createWebPage(lyr, mesh)
      
  # Boundary conditions are stored in Numpy arrays
  def loadBoundaryCondition(self, lyr, mesh, matls):
    for nodeThis in range(0, self.NumGlobalElements):
      x, y= mesh.nodeLocation(nodeThis)
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        # The node at x, y gets on-diagonal conductance incremented by the amount of conductance in the boundary.
        # The Norton equivalent current source I is V*R which is mesh.field[x, y, lyr.isodeg] * matls.boundCond        
        self.boundaryCondVec[nodeThis] = mesh.field[x, y, lyr.isodeg]
        self.boundaryCondMatl[nodeThis] = matls.boundCond  
        self.BoundaryNodeCount += 1
      else:
        self.boundaryCondVec[nodeThis] = -512.0
        self.boundaryCondMatl[nodeThis] = 0.0
      self.totalInjectedCurrent += mesh.field[x, y, lyr.heat]    

  # This is the bottleneck
  # RAM requirement is about 1kb/mesh element for solved Trilinos sparse matrix
  def loadMatrix(self, lyr, mesh, matls, A, b):
    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      nodeResis = mesh.field[x, y, lyr.resis]
      GNode= self.GDamping        

      nodeRight = mesh.getNodeAtXY(x+1, y)
      nodeUp = mesh.getNodeAtXY(x, y-1)
      nodeLeft = mesh.getNodeAtXY(x-1, y)
      nodeDown = mesh.getNodeAtXY(x, y+1)  

      if nodeRight >= 0:
        nodeRightResis= mesh.field[x+1, y, lyr.resis]
        GRight= 2.0/(nodeResis + nodeRightResis)
        GNode += GRight
        A[nodeThis, nodeRight]= -GRight
        A[nodeRight, nodeThis]= -GRight

      if nodeUp >= 0:
        nodeUpResis= mesh.field[x, y-1, lyr.resis]
        GUp= 2.0/(nodeResis + nodeUpResis)
        GNode += GUp
        A[nodeThis, nodeUp]= -GUp
        A[nodeUp, nodeThis]= -GUp

      if nodeLeft >= 0:
        nodeLeftResis=  mesh.field[x-1, y, lyr.resis]
        GLeft= 2.0/(nodeResis + nodeLeftResis)
        GNode += GLeft
        A[nodeThis, nodeLeft]= -GLeft
        A[nodeLeft, nodeThis]= -GLeft

      if nodeDown >= 0:
        nodeDownResis=  mesh.field[x, y+1, lyr.resis]        
        GDown= 2.0/(nodeResis + nodeDownResis)        
        GNode += GDown
        A[nodeThis, nodeDown]= -GDown
        A[nodeDown, nodeThis]= -GDown

      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        # The node at x, y gets on-diagonal conductance incremented by the amount of conductance in the boundary.
        # b is the RHS. It gets the current source which is mesh.field[x, y, lyr.isodeg] * matls.boundCond        
        GNode = GNode + matls.boundCond
        b[nodeThis] = mesh.field[x, y, lyr.isodeg] * matls.boundCond
      else:
        b[nodeThis] = 0.0

      A[nodeThis, nodeThis]= GNode 
      b[nodeThis] += mesh.field[x, y, lyr.heat]      

  def loadSpiceNetwork(self, lyr, mesh, matls, spice):

    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
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
        
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        thisSpiceNode=   "N" + str(x)   + self.s + str(y)
        # Norton equivalent boundary resistance and current source.
        thisIsoSource=   "I" + thisSpiceNode
      
        thisBoundaryNode=  "NDIRI" + self.s + str(x) + self.s + str(y)
        thisBoundaryResistor=  "RDIRI" + self.s + str(x) + self.s + str(y)
        thisBoundaryResistance= 1.0/matls.boundCond
      
        thisBoundaryCurrent= mesh.field[x, y, lyr.isodeg] * matls.boundCond
        spice.appendSpiceNetlist(thisIsoSource + " 0 " + thisSpiceNode + " DC " + str(thisBoundaryCurrent) + "\n")
        spice.appendSpiceNetlist(thisBoundaryResistor + " " + thisSpiceNode + " 0 " + str(thisBoundaryResistance) + "\n")  
        
  def loadSpiceHeatSources(self, lyr, mesh, spice):
    """
    Add spice current sources for injected heat.
    """
    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      if (mesh.field[x, y, lyr.heat] != 0.0):
        thisSpiceNode=   "N" + str(x) + self.s + str(y)
        thisHeatSource=   "I" + thisSpiceNode
        thisHeat= -mesh.field[x, y, lyr.heat]
        spice.appendSpiceNetlist(thisHeatSource + " " + thisSpiceNode + " 0 DC " + str(thisHeat) + "\n")
        
  #def loadSolutionIntoMesh(self, lyr, mesh):
    #"""
    #loadSolutionIntoMesh(Solver self, Layers lyr, Mesh mesh)
    #Load the solution back into a layer on the mesh
    #"""
    #for nodeThis in range(0, mesh.nodeCount):
      #x, y= mesh.nodeLocation(nodeThis)
      #mesh.field[x, y, lyr.deg] = self.solver.x[nodeThis]
      ## print "Temp x y t ", x, y, self.x[nodeThis]     
      
  def checkEnergyBalance(self, mesh, x, b):
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
    # nodecount= mesh.solveTemperatureNodeCount()
    for n in range(0, mesh.nodeCount):
      self.totalMatrixPower += b[n]
      if self.boundaryCondVec[n] == -512.0:
        self.totalBoundaryCurrent += b[n]
      else:
        self.boundaryPowerOut += (x[n] - self.boundaryCondVec[n]) * self.boundaryCondMatl[n]
      # print str(n) + ", " + str(self.x[n]) + ", " + str(self.b[n]) + ", " + str(self.boundaryCondVec[n]) + ", " + str(self.totalMatrixPower) + ", " + str(self.boundaryPowerOut)

    print "Total Injected Designed Power = " + str(self.totalInjectedCurrent)
    print "Total Injected Matrix Power = " + str(self.totalBoundaryCurrent)
    print "Total Boundary Power Including Norton current sources = ", self.totalMatrixPower
    print "Total Power Calculated from Boundary temperature rise = ", self.boundaryPowerOut

  def solveAmesos(self, mesh, lyr):
    self.solver.solveMatrixAmesos()
    self.loadSolutionIntoMesh(lyr.deg, mesh, self.solver.x)
    self.checkEnergyBalance(mesh, self.solver.x, self.solver.b)

  def solveAztecOO(self, mesh, lyr):
    self.solver.solveMatrixAztecOO(400000)
    self.loadSolutionIntoMesh(lyr.deg, mesh, self.solver.x)
    self.checkEnergyBalance(mesh, self.solver.x, self.solver.b)   

  def solveSpice(self, mesh, lyr):
    self.spice.solveSpice()
    self.spice.loadSolutionIntoMesh(lyr.spicedeg, mesh)
    # TODO: Need energy balance check here
    
  def solveNumpy(self, mesh, lyr):
    self.xs = np.linalg.solve(self.As, self.bs)
    self.loadSolutionIntoMesh(lyr.npdeg, mesh, self.xs)
    self.checkEnergyBalance(mesh, self.xs, self.bs)
      
  def loadSolutionIntoMesh(self, lyrIdx, mesh, xs):
    """
    loadSolutionIntoMesh(Solver self, Layers lyr, Mesh mesh)
    Load the solution back into a layer on the mesh
    """
    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      mesh.field[x, y, lyrIdx] = xs[nodeThis]
      # print "Temp x y t ", x, y, self.x[nodeThis]      
    
  def printNumpy(self):
    print "Debug: A " + str(self.As)
    print "Debug: b " + str(self.bs)
    print "Debug: x " + str(self.xs)
    
  def nonzeroMostCommonCount(self):
    """
    Find the most common number of nonzero elements in the A matrix.
    Loading this into the Trilinos solver speeds it up.
    Uses the Debug dense data structures.
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
      
  # Need another sub/flag for creating the matrix web page.
  def createWebPage(self, lyr, mesh):
    webpage = MatrixDiagnostic.MatrixDiagnosticWebpage(self, lyr, mesh)
    webpage.createWebPage()        
    self.debugMatrix()

  def debugMatrix(self):
    # TODO: Use config to name and position the matrix market and html files
    self.solver.saveMatrix()

    htmlFilename = self.mmPrefix + "AxRHS.html"

    MMHtmlWriter= MMHtml.MMHtml()
    MMReaderRHS= mm.MatrixMarket()
    MMRHS= MMReaderRHS.read(self.solver.rhsFilename) 

    MMReaderX= mm.MatrixMarket()
    MMX= MMReaderX.read(self.solver.xFilename)     

    MMReaderMMA= mm.MatrixMarket()     
    MMA= MMReaderMMA.read(self.solver.probFilename)
    MMHtmlWriter.writeHtml([MMA, MMX, MMRHS], htmlFilename)  
