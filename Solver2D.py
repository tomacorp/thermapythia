import numpy as np
from collections import Counter

import TriSolver
import SpSolver
import MatrixDiagnostic
import MatrixMarket as mm
import MMHtml

# TODO REFACTOR: The solvers should all be loaded the same way.
# There should be one generic solver middle end that is loaded
# with the same set of function calls, so that a pure Python,
# Trilinos, or spice solver can be called without needeing
# conditionals in this code.

# TODO: Keep implementing debug and spice solver separation.
# Don't want the overhead or code clutter of the conditionals all over the place.
# Might want the debug, spice, and trilinos 2D loaders in separate classes.

# TODO: Add non-sparse numpy solver. Might be better than Trilinos for small systems. 
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
    self.GDamping          = 1e-12  # Various values such as 1e-12, 1e-10, and -1e-10 have worked or not!
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

    if self.debug == True:
      """
      Create a shadow matrix as a duplicate of A and a shadow RHS as duplicate of b.
      These are easier to access than self.A and self.b, which are opaque when MPI is used.
      """
      self.initDebug(config)
  
  def initDebug(self, config):
    """
    Create a non-sparse matrix As and a RHS bs.
    These can be used with dense matrix solvers.
    This is useful for debugging and might be faster for small problems.
    """    
    self.As = np.zeros((self.NumGlobalElements, self.NumGlobalElements), dtype = 'double')
    self.bs = np.zeros(self.NumGlobalElements)
    self.debugWebPage= config['solverDebug']['debugWebPage']
    self.mmPrefix= config['solverDebug']['mmPrefix']

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

  def solve(self, lyr, mesh, matls):
    self.loadBoundaryCondition(lyr, mesh, matls)
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
      print "Debug: A " + str(self.As)
      print "Debug: b " + str(self.bs)
      x = np.linalg.solve(self.As, self.bs)
      print "Debug: x " + str(x)
      webpage = MatrixDiagnostic.MatrixDiagnosticWebpage(self, lyr, mesh)
      webpage.createWebPage()        
      self.debugMatrix()
      
  def loadBoundaryCondition(self, lyr, mesh, matls):
    for nodeThis in range(0, self.NumGlobalElements):
      x, y= mesh.nodeLocation(nodeThis)
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        # The node at x, y gets on-diagonal conductance incremented by the amount of conductance in the boundary.
        # b is the RHS. It gets the current source which is mesh.field[x, y, lyr.isodeg] * matls.boundCond        
        self.boundaryCondVec[nodeThis] = mesh.field[x, y, lyr.isodeg]
        self.boundaryCondMatl[nodeThis] = matls.boundCond  
        self.BoundaryNodeCount += 1
      else:
        self.boundaryCondVec[nodeThis] = -512.0
        self.boundaryCondMatl[nodeThis] = 0.0
      self.totalInjectedCurrent += mesh.field[x, y, lyr.heat]    
          
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

  def loadMatrix(self, lyr, mesh, matls, spice):
    if self.useAmesos == True or self.useAztec == True:
      self.loadMatrixSolver(lyr, mesh, spice, matls) 
      self.loadMatrixHeatSources(lyr, mesh)
      
    if self.debug == True:
      self.loadDebugMatrix(lyr, mesh, matls)  
      self.loadDebugMatrixHeatSources(lyr, mesh)
      
    if self.useSpice == True:
      self.loadSpiceNetwork(lyr, mesh, matls, spice)    
      self.loadSpiceHeatSources(lyr, mesh, spice)

  def loadMatrixHeatSources(self, lyr, mesh):
    """
    b is the RHS, which are current sources for injected heat.
    This routine takes heat sources from the field and puts them in the matrix RHS.
    """
    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      self.solver.b[nodeThis] += mesh.field[x, y, lyr.heat]
            
  def loadDebugMatrixHeatSources(self, lyr, mesh):
    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      self.bs[nodeThis] += mesh.field[x, y, lyr.heat]
  
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

  def loadMatrixSolver(self, lyr, mesh, spice, matls):
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
        self.solver.A[nodeThis, nodeRight]= -GRight
        self.solver.A[nodeRight, nodeThis]= -GRight

      if nodeUp >= 0:
        nodeUpResis= mesh.field[x, y-1, lyr.resis]
        GUp= 2.0/(nodeResis + nodeUpResis)
        GNode += GUp
        self.solver.A[nodeThis, nodeUp]= -GUp
        self.solver.A[nodeUp, nodeThis]= -GUp

      if nodeLeft >= 0:
        nodeLeftResis=  mesh.field[x-1, y, lyr.resis]
        GLeft= 2.0/(nodeResis + nodeLeftResis)
        GNode += GLeft
        self.solver.A[nodeThis, nodeLeft]= -GLeft
        self.solver.A[nodeLeft, nodeThis]= -GLeft
      
      if nodeDown >= 0:
        nodeDownResis=  mesh.field[x, y+1, lyr.resis]        
        GDown= 2.0/(nodeResis + nodeDownResis)        
        GNode += GDown
        self.solver.A[nodeThis, nodeDown]= -GDown
        self.solver.A[nodeDown, nodeThis]= -GDown

      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        # The node at x, y gets on-diagonal conductance incremented by the amount of conductance in the boundary.
        # b is the RHS. It gets the current source which is mesh.field[x, y, lyr.isodeg] * matls.boundCond        
        GNode = GNode + matls.boundCond
        self.solver.b[nodeThis] = mesh.field[x, y, lyr.isodeg] * matls.boundCond
      else:
        self.solver.b[nodeThis] = 0.0
        
      self.solver.A[nodeThis, nodeThis]= GNode
      
  def loadDebugMatrix(self, lyr, mesh, matls):
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
        self.As[nodeThis, nodeRight]= -GRight
        self.As[nodeRight, nodeThis]= -GRight
  
      if nodeUp >= 0:
        nodeUpResis= mesh.field[x, y-1, lyr.resis]
        GUp= 2.0/(nodeResis + nodeUpResis)
        GNode += GUp
        self.As[nodeThis, nodeUp]= -GUp
        self.As[nodeUp, nodeThis]= -GUp
  
      if nodeLeft >= 0:
        nodeLeftResis=  mesh.field[x-1, y,   lyr.resis]
        GLeft= 2.0/(nodeResis + nodeLeftResis)
        GNode += GLeft
        self.As[nodeThis, nodeLeft]= -GLeft
        self.As[nodeLeft, nodeThis]= -GLeft
     
      if nodeDown >= 0:
        nodeDownResis=  mesh.field[x, y+1, lyr.resis]        
        GDown= 2.0/(nodeResis + nodeDownResis)        
        GNode += GDown
        self.As[nodeThis, nodeDown]= -GDown
        self.As[nodeDown, nodeThis]= -GDown
  
      #if (mesh.ifield[x, y, lyr.isoflag] == 1):
        #print "Setting boundaryNode body", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        # The node at x, y gets on-diagonal conductance incremented by the amount of conductance in the boundary.
        # b is the RHS. It gets the current source which is mesh.field[x, y, lyr.isodeg] * matls.boundCond        
        GNode = GNode + matls.boundCond
        self.bs[nodeThis] += mesh.field[x, y, lyr.isodeg] * matls.boundCond
        
        # TODO Factor this out so that the trilinos solver is not required to set these.
        
        #self.boundaryCondVec[nodeThis] = mesh.field[x, y, lyr.isodeg]
        #self.boundaryCondMatl[nodeThis] = matls.boundCond 
        #self.BoundaryNodeCount += 1
      else:
        self.bs[nodeThis] = 0.0
    
      self.As[nodeThis, nodeThis]= GNode        
  
  
  #def loadMatrixBodyWithHoles(self, lyr, mesh, spice, matls):
    #for nodeThis in range(0, mesh.nodeCount):
      #x, y= mesh.nodeLocation(nodeThis)
      #nodeResis = mesh.field[x, y, lyr.resis]
      #GNode= self.GDamping        
      
      #nodeRight = mesh.getNodeAtXY(x+1, y)
      #if nodeRight >= 0:
        #nodeRightResis= mesh.field[x+1, y, lyr.resis]
        #GRight= 2.0/(nodeResis + nodeRightResis)
        #GNode += GRight
        #if (self.useAztec == True) or (self.useAmesos == True):
          #self.solver.A[nodeThis, nodeRight]= -GRight
          #self.solver.A[nodeRight, nodeThis]= -GRight
        #if self.debug == True:
          #self.As[nodeThis, nodeRight]= -GRight
          #self.As[nodeRight, nodeThis]= -GRight
      
      #nodeUp = mesh.getNodeAtXY(x, y-1)
      #if nodeUp >= 0:
        #nodeUpResis= mesh.field[x, y-1, lyr.resis]
        #GUp= 2.0/(nodeResis + nodeUpResis)
        #GNode += GUp
        #if (self.useAztec == True) or (self.useAmesos == True):
          #self.solver.A[nodeThis, nodeUp]= -GUp
          #self.solver.A[nodeUp, nodeThis]= -GUp
        #if self.debug == True:
          #self.As[nodeThis, nodeUp]= -GUp
          #self.As[nodeUp, nodeThis]= -GUp
      
      #nodeLeft = mesh.getNodeAtXY(x-1, y)
      #if nodeLeft >= 0:
        #nodeLeftResis=  mesh.field[x-1, y,   lyr.resis]
        #GLeft= 2.0/(nodeResis + nodeLeftResis)
        #GNode += GLeft
        #if (self.useAztec == True) or (self.useAmesos == True):
          #self.solver.A[nodeThis, nodeLeft]= -GLeft
          #self.solver.A[nodeLeft, nodeThis]= -GLeft
        #if self.debug == True:
          #self.As[nodeThis, nodeLeft]= -GLeft
          #self.As[nodeLeft, nodeThis]= -GLeft
      
      #nodeDown = mesh.getNodeAtXY(x, y+1)        
      #if nodeDown >= 0:
        #nodeDownResis=  mesh.field[x, y+1, lyr.resis]        
        #GDown= 2.0/(nodeResis + nodeDownResis)        
        #GNode += GDown
        #if (self.useAztec == True) or (self.useAmesos == True):
          #self.solver.A[nodeThis, nodeDown]= -GDown
          #self.solver.A[nodeDown, nodeThis]= -GDown
        #if self.debug == True:
          #self.As[nodeThis, nodeDown]= -GDown
          #self.As[nodeDown, nodeThis]= -GDown

      #if (mesh.ifield[x, y, lyr.isoflag] == 1):
        #if self.debug == True:
          #print "Setting boundaryNode body", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        #GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)

      #if (self.useAztec == True) or (self.useAmesos == True):
        #self.solver.A[nodeThis, nodeThis]= GNode
        
      #if self.debug == True:
        #self.As[nodeThis, nodeThis]= GNode

  def loadSpiceNetwork(self, lyr, mesh, matls, spice):

    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      # nodeThis = mesh.ifield[x, y, lyr.holeflag]
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
      
        thisBoundaryCurrent= mesh.field[x, y, lyr.isodeg]/thisBoundaryResistance
        spice.appendSpiceNetlist(thisIsoSource + " 0 " + thisSpiceNode + " DC " + str(thisBoundaryCurrent) + "\n")
        spice.appendSpiceNetlist(thisBoundaryResistor + " " + thisSpiceNode + " 0 " + str(thisBoundaryResistance) + "\n")        
        
        

  #def addIsoNode(self, lyr, mesh, spice, matls, nodeThis, x, y, GNode):
    #"""
    #The node at x, y gets on-diagonal conductance incremented by the amount of conductance in the boundary.
    #b is the RHS. It gets the current source which is mesh.field[x, y, lyr.isodeg] * matls.boundCond    
    #"""
    #GNode = GNode + matls.boundCond
    #self.solver.A[nodeThis, nodeThis] = GNode
    
    #if mesh.ifield[x, y, lyr.isoflag] == 1:
      #self.solver.b[nodeThis] = mesh.field[x, y, lyr.isodeg] * matls.boundCond
      #self.boundaryCondVec[nodeThis] = mesh.field[x, y, lyr.isodeg]
      #self.boundaryCondMatl[nodeThis] = matls.boundCond
    #else:
      #self.solver.b[nodeThis] = 0.0

    #if self.debug == True:
      #self.As[nodeThis, nodeThis]= GNode 
      #if mesh.ifield[x, y, lyr.isoflag] == 1:
        #self.solver.bs[nodeThis] = mesh.field[x, y, lyr.isodeg] * matls.boundCond
        #self.boundaryCondVec[nodeThis] = mesh.field[x, y, lyr.isodeg]
        #self.boundaryCondMatl[nodeThis] = matls.boundCond
      #else:
        #self.solver.bs[nodeThis] = 0.0
      
    #if self.useSpice == True:
      #thisSpiceNode=   "N" + str(x)   + self.s + str(y)
      ## Norton equivalent boundary resistance and current source.
      #thisIsoSource=   "I" + thisSpiceNode
      
      #thisBoundaryNode=  "NDIRI" + self.s + str(x) + self.s + str(y)
      #thisBoundaryResistor=  "RDIRI" + self.s + str(x) + self.s + str(y)
      #thisBoundaryResistance= 1.0/matls.boundCond
      
      #thisBoundaryCurrent= mesh.field[x, y, lyr.isodeg]/thisBoundaryResistance
      #spice.appendSpiceNetlist(thisIsoSource + " 0 " + thisSpiceNode + " DC " + str(thisBoundaryCurrent) + "\n")
      #spice.appendSpiceNetlist(thisBoundaryResistor + " " + thisSpiceNode + " 0 " + str(thisBoundaryResistance) + "\n")

    #self.BoundaryNodeCount += 1
    #return GNode
            
  def loadSolutionIntoMesh(self, lyr, mesh):
    """
    loadSolutionIntoMesh(Solver self, Layers lyr, Mesh mesh)
    Load the solution back into a layer on the mesh
    """
    for nodeThis in range(0, mesh.nodeCount):
      x, y= mesh.nodeLocation(nodeThis)
      mesh.field[x, y, lyr.deg] = self.solver.x[nodeThis]
      # print "Temp x y t ", x, y, self.x[nodeThis]     
      
      
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
      self.totalMatrixPower += self.solver.b[n]
      if self.boundaryCondVec[n] == -512.0:
        self.totalBoundaryCurrent += self.solver.b[n]
      else:
        self.boundaryPowerOut += (self.solver.x[n] - self.boundaryCondVec[n]) * self.boundaryCondMatl[n]
      # print str(n) + ", " + str(self.x[n]) + ", " + str(self.b[n]) + ", " + str(self.boundaryCondVec[n]) + ", " + str(self.totalMatrixPower) + ", " + str(self.boundaryPowerOut)

    print "Total Injected Designed Power = " + str(self.totalInjectedCurrent)
    print "Total Injected Matrix Power = " + str(self.totalBoundaryCurrent)
    print "Total Boundary Power Including Norton current sources = ", self.totalMatrixPower
    print "Total Power Calculated from Boundary temperature rise = ", self.boundaryPowerOut

  def solveAmesos(self, mesh, lyr):
    self.solver.solveMatrixAmesos()
    self.loadSolutionIntoMesh(lyr, mesh)
    self.checkEnergyBalance(lyr, mesh)

  def solveAztecOO(self, mesh, lyr):
    self.solver.solveMatrixAztecOO(400000)
    self.loadSolutionIntoMesh(lyr, mesh)
    self.checkEnergyBalance(lyr, mesh)   

  def solveSpice(self, mesh, lyr):
    self.spice.finishSpiceNetlist()
    proc= self.spice.runSpiceNetlist()
    proc.wait()
    self.spice.readSpiceRawFile(lyr, mesh)     
            