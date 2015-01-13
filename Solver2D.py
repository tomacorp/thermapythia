import numpy as np
from collections import Counter
from PyTrilinos import Epetra, AztecOO, Anasazi, Amesos, EpetraExt
import Spice2D
import MatrixDiagnostic
import MatrixMarket as mm
import MMHtml

# TODO: Methods here should be in four stages:
#   Mesh
#   Load Matrix
#   Solve Matrix
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
# DELAY REFACTORING: After holes are implemented, a lot of this class
# will go away, which will make refactoring much easier.

class Solver:
  """
  The Solver class loads a matrix and solves it.
  It also optionally loads a spice netlist and a debugging structure.
  
  A matrix is in sections:
    
        |  G   B  |
    A = |  C   D  |
       G transconductance matrix
       B sources, which in this case are just 1s
       C transpose of B
       D zeroes
    G is in two sections, which are the upper left GF (for field) and GB (for boundary)
    The analysis is of the form  Ax = b
    For rows in b corresponding to G,  
       b is the known value of the current (constant power in thermal circuits) sources
    For rows in b corresponding to D, (constant temperature boundary conditions) 
       b is the known value of temperature at the boundary.
    The number of rows in D is self.nodeDcount
    The number of rows in G is self.nodeGcount
    The number of rows in GF is self.nodeGFcount
    The number of rows in GB is self.nodeGBcount
    The total number of rows in A is self.nodeCount
  
    The solution to the matrix is the vector x
    For rows in x corresponding to G, these are voltages (temperature)
    For rows in x corresponding to D, these are currents (power flow) in the boundary condition.
  
    For energy balance in steady state, the current into the constant-temperature boundary condition 
    must equal the current from the constant-power thermal sources.
  
    The index of the last nodes in the G submatrix for the field plus one is the number
    of nodes in the field GF. Add the boundary nodes GB to G.
  
    Also count the number of boundary sources, which is the size of the D matrix.   
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
      
    self.isoIdx            = 0

    self.deck              = ''
    self.GDamping          = 0.0   # Various values such as 1e-12, 1e-10, and -1e-10 have worked or not!
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
    The field transconductance matrix GF is in nine sections:
      
        top left corner      |     top edge      |     top right corner
        left edge            |     body          |     right edge
        bottom left corner   |     bottom edge   |     bottom right corner
    
    A is the problem matrix
    Modified nodal analysis formulation is from:
    http://www.swarthmore.edu/NatSci/echeeve1/Ref/mna/MNA2.html
    
    This needs to change to a pure nodal implementation without voltage sources.
    The voltage sources cause the matrix to be a saddle point matrix, which is
    bad for iterative amd eigen-value solvers.
    """
    self.isoIdx = mesh.nodeGFcount
    print "Starting iso nodes at ", self.isoIdx
    
    self.loadMatrixBottomLeftCorner(lyr, mesh, spice, matls)
    self.loadMatrixBottomRightCorner(lyr, mesh, spice, matls)
    self.loadMatrixBottomEdge(lyr, mesh, spice, matls)
    self.loadMatrixTopRightCorner(lyr, mesh, spice, matls)
    self.loadMatrixTopLeftCorner(lyr, mesh, spice, matls) 
    self.loadMatrixRightEdge(lyr, mesh, spice, matls)
    self.loadMatrixTopEdge(lyr, mesh, spice, matls)
    self.loadMatrixLeftEdge(lyr, mesh, spice, matls)
    self.loadMatrixBody(lyr, mesh, spice, matls)  
    self.loadMatrixHeatSources(lyr, mesh)
    
    if self.useSpice == True:
      self.loadBodySpice(lyr, mesh, spice)    
      self.loadSpiceHeatSources(lyr, mesh, spice)

  def loadMatrixHeatSources(self, lyr, mesh):
    """
    b is the RHS, which are current sources for injected heat.
    """
    # Add the injected heat sources.
    # NORTON equivalent heat sources need to be accounted for here.
    # Just add the mesh.field entries to the b instead of setting them.
    # If adding isn't possible due to mpi, keep track of them another way.
    # Look up in iso layer to see if a Norton current source is needed.
    # If it is, then add the current needed to maintain the temperature
    # for the boundary conductance.
    for x in range(0, mesh.width):
      for y in range(0, mesh.height):
        nodeThis= mesh.getNodeAtXY(x, y)
        # local variable with mesh.field[x, y, lyr.heat] current
        # Check x,y for iso condition
        #   If it exists, compute the current and add it to the local variable.
        # set self.b[nodeThis] to the local variable
        self.b[nodeThis]= mesh.field[x, y, lyr.heat]
        if self.debug == True:
          self.bs[nodeThis]= mesh.field[x, y, lyr.heat]
            
  def loadSpiceHeatSources(self, lyr, mesh, spice):
    """
    Add spice current sources for injected heat
    """
    if self.useSpice == False:
      return
    for x in range(0, mesh.width):
      for y in range(0, mesh.height):
        nodeThis= mesh.getNodeAtXY(x, y)
        if (mesh.field[x, y, lyr.heat] != 0.0):
          thisSpiceNode=   "N" + str(x) + self.s + str(y)
          thisHeatSource=   "I" + thisSpiceNode
          thisHeat= -mesh.field[x, y, lyr.heat]
          spice.appendSpiceNetlist(thisHeatSource + " " + thisSpiceNode + " 0 DC " + str(thisHeat) + "\n")

  # This is the bottleneck
  # RAM requirement is about 1kb/mesh element.
  def loadMatrixBody(self, lyr, mesh, spice, matls):
    if (mesh.height < 3) or (mesh.width < 3):
      return
    for x in range(1, mesh.width-1):
      for y in range(1, mesh.height-1):
        
        # 2.067s
        nodeThis, nodeRight, nodeUp, nodeLeft, nodeDown = \
          self.getNeighborNodeNumbers(y, x, mesh)
        
        # 0.747s
        nodeResis, nodeRightResis, nodeUpResis, nodeLeftResis, nodeDownResis = \
        self.rnodeCalc(y, x, mesh, lyr)
        
        # 1.022s
        GRight, GUp, GLeft, GDown, GNode = \
        self.gnodeCalc(nodeResis, nodeRightResis, nodeUpResis, nodeLeftResis, nodeDownResis)
        
        self.BodyNodeCount += 1
        if (mesh.ifield[x, y, lyr.isoflag] == 1):
          if self.debug == True:
            print "Setting boundaryNode body", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
          GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)
        
        if (self.useAztec == True) or (self.useAmesos == True):
          # 6.074s
          self.loadBodyA(nodeThis, GNode, GRight, nodeRight, GUp, nodeUp, nodeLeft, GLeft, GDown, nodeDown)
          
        if self.debug == True:
          self.loadBodyAShadow(nodeThis, GNode, GRight, nodeRight, GUp, nodeUp, nodeLeft, GLeft, GDown, nodeDown)

  def loadBodySpice(self, lyr, mesh, spice):
    if (mesh.height < 3) or (mesh.width < 3):
      return
    for x in range(1, mesh.width-1):
      for y in range(1, mesh.height-1):    
        thisSpiceNode=   "N" + str(x)   + self.s + str(y)
        spiceNodeRight=  "N" + str(x+1) + self.s + str(y)
        spiceNodeDown=   "N" + str(x)   + self.s + str(y+1)
    
        mesh.spiceNodeXName[thisSpiceNode] = x
        mesh.spiceNodeYName[thisSpiceNode] = y
        
        nodeResis=      mesh.field[x,   y,   lyr.resis]
        nodeRightResis= mesh.field[x+1, y,   lyr.resis]
        nodeDownResis=  mesh.field[x,   y+1, lyr.resis]    
    
        RRight= (nodeResis + nodeRightResis)/2.0
        RDown=  (nodeResis + nodeDownResis)/2.0       
    
        # Need to change this to write to a buffer and then flush to a file.
        # Appending the string is taking way long.
        spice.appendSpiceNetlist("RFR" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n")
        spice.appendSpiceNetlist("RFD" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n")

  def loadBodyAShadow(self, nodeThis, GNode, GRight, nodeRight, GUp, nodeUp, nodeLeft, GLeft, GDown, nodeDown):
    self.As[nodeThis, nodeThis]= GNode
    self.As[nodeThis, nodeRight]= -GRight
    self.As[nodeRight, nodeThis]= -GRight
    self.As[nodeThis, nodeUp]= -GUp
    self.As[nodeUp, nodeThis]= -GUp
    self.As[nodeThis, nodeLeft]= -GLeft
    self.As[nodeLeft, nodeThis]= -GLeft
    self.As[nodeThis, nodeDown]= -GDown
    self.As[nodeDown, nodeThis]= -GDown

  def loadBodyA(self, nodeThis, GNode, GRight, nodeRight, GUp, nodeUp, nodeLeft, GLeft, GDown, nodeDown):
    self.A[nodeThis, nodeThis]= GNode
    self.A[nodeThis, nodeRight]= -GRight
    self.A[nodeRight, nodeThis]= -GRight
    self.A[nodeThis, nodeUp]= -GUp
    self.A[nodeUp, nodeThis]= -GUp
    self.A[nodeThis, nodeLeft]= -GLeft
    self.A[nodeLeft, nodeThis]= -GLeft
    self.A[nodeThis, nodeDown]= -GDown
    self.A[nodeDown, nodeThis]= -GDown

  def getNeighborNodeNumbers(self, y, x, mesh):
    nodeThis  = mesh.getNodeAtXY(x,   y)
    nodeRight = mesh.getNodeAtXY(x+1, y)
    nodeUp    = mesh.getNodeAtXY(x,   y-1)
    nodeLeft  = mesh.getNodeAtXY(x-1, y)
    nodeDown  = mesh.getNodeAtXY(x,   y+1)
    return nodeThis, nodeRight, nodeUp, nodeLeft, nodeDown

  def rnodeCalc(self, y, x, mesh, lyr):
    nodeResis=      mesh.field[x,   y,   lyr.resis]
    nodeRightResis= mesh.field[x+1, y,   lyr.resis]
    nodeUpResis=    mesh.field[x,   y-1, lyr.resis]
    nodeLeftResis=  mesh.field[x-1, y,   lyr.resis]
    nodeDownResis=  mesh.field[x,   y+1, lyr.resis]
    return nodeResis, nodeRightResis, nodeUpResis, nodeLeftResis, nodeDownResis

  def gnodeCalc(self, nodeResis, nodeRightResis, nodeUpResis, nodeLeftResis, nodeDownResis):
    GRight= 2.0/(nodeResis + nodeRightResis)
    GUp=    2.0/(nodeResis + nodeUpResis)
    GLeft=  2.0/(nodeResis + nodeLeftResis)
    GDown=  2.0/(nodeResis + nodeDownResis)        
    GNode= GRight + GUp + GLeft + GDown + self.GDamping
    return GRight, GUp, GLeft, GDown, GNode

  def loadMatrixTopEdge(self, lyr, mesh, spice, matls):
    if (mesh.width < 3) or (mesh.height < 2):
      return
    GBoundary= matls.boundCond
    for x in range(1, mesh.width-1):
      y = 0
      nodeThis= mesh.getNodeAtXY(x, y)
      nodeRight= mesh.getNodeAtXY(x+1, y)
      nodeLeft= mesh.getNodeAtXY(x-1, y)
      nodeDown= mesh.getNodeAtXY(x, y+1)
      
      nodeResis= mesh.field[x, y, lyr.resis]
      nodeRightResis= mesh.field[x+1, y, lyr.resis]
      nodeLeftResis= mesh.field[x-1, y, lyr.resis]
      nodeDownResis= mesh.field[x, y+1, lyr.resis]
      GRight= 2.0/(nodeResis + nodeRightResis)
      GLeft= 2.0/(nodeResis + nodeLeftResis)
      GDown= 2.0/(nodeResis + nodeDownResis)
      GNode= GRight + GLeft + GDown + self.GDamping
      self.TopEdgeNodeCount += 1

      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        if self.debug == True:
          print "Setting boundaryNode te", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)
 
      self.A[nodeThis, nodeThis]= GNode
      self.A[nodeThis, nodeRight]= -GRight
      self.A[nodeRight, nodeThis]= -GRight
      self.A[nodeThis, nodeLeft]= -GLeft
      self.A[nodeLeft, nodeThis]= -GLeft
      self.A[nodeThis, nodeDown]= -GDown
      self.A[nodeDown, nodeThis]= -GDown
      if self.debug == True:
        self.As[nodeThis, nodeThis]= GNode
        self.As[nodeThis, nodeRight]= -GRight
        self.As[nodeRight, nodeThis]= -GRight
        self.As[nodeThis, nodeLeft]= -GLeft
        self.As[nodeLeft, nodeThis]= -GLeft
        self.As[nodeThis, nodeDown]= -GDown
        self.As[nodeDown, nodeThis]= -GDown
      if self.useSpice == True:
        thisSpiceNode=   "N" + str(x)   + self.s + str(y)
        spiceNodeRight=  "N" + str(x+1) + self.s + str(y)
        spiceNodeDown=   "N" + str(x)   + self.s + str(y+1)
        mesh.spiceNodeXName[thisSpiceNode] = x
        mesh.spiceNodeYName[thisSpiceNode] = y        
        RRight= 1.0/GRight
        RDown=  1.0/GDown
        spice.appendSpiceNetlist("RTER" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n")
        spice.appendSpiceNetlist("RTED" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n")

  def loadMatrixRightEdge(self, lyr, mesh, spice, matls):
    if (mesh.width < 2) or (mesh.height < 3):
      return
    GBoundary= matls.boundCond
    for y in range(1, mesh.height-1):
      x= mesh.width-1
      nodeThis= mesh.getNodeAtXY(x, y)
      nodeUp= mesh.getNodeAtXY(x, y-1)
      nodeLeft= mesh.getNodeAtXY(x-1, y)
      nodeDown= mesh.getNodeAtXY(x, y+1)

      nodeResis= mesh.field[x, y, lyr.resis]
      nodeUpResis= mesh.field[x, y-1, lyr.resis]
      nodeLeftResis= mesh.field[x-1, y, lyr.resis]
      nodeDownResis= mesh.field[x, y+1, lyr.resis]
      GUp= 2.0/(nodeResis + nodeUpResis)
      GLeft= 2.0/(nodeResis + nodeLeftResis)
      GDown= 2.0/(nodeResis + nodeDownResis)
      GNode= GUp + GLeft + GDown + self.GDamping
      self.RightEdgeNodeCount += 1
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        if self.debug == True:
          print "Setting boundaryNode re", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)

      self.A[nodeThis, nodeThis]= GNode
      self.A[nodeThis, nodeUp]= -GUp
      self.A[nodeUp, nodeThis]= -GUp
      self.A[nodeThis, nodeLeft]= -GLeft
      self.A[nodeLeft, nodeThis]= -GLeft
      self.A[nodeThis, nodeDown]= -GDown
      self.A[nodeDown, nodeThis]= -GDown
      if self.debug == True:
        self.As[nodeThis, nodeThis]= GNode
        self.As[nodeThis, nodeUp]= -GUp
        self.As[nodeUp, nodeThis]= -GUp
        self.As[nodeThis, nodeLeft]= -GLeft
        self.As[nodeLeft, nodeThis]= -GLeft
        self.As[nodeThis, nodeDown]= -GDown
        self.As[nodeDown, nodeThis]= -GDown
      if self.useSpice == True:
        thisSpiceNode=   "N" + str(x)   + self.s + str(y)
        spiceNodeDown=   "N" + str(x)   + self.s + str(y+1)
        mesh.spiceNodeXName[thisSpiceNode] = x
        mesh.spiceNodeYName[thisSpiceNode] = y        
        RDown=  1.0/GDown
        spice.appendSpiceNetlist("RRED" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n")
    
  def loadMatrixBottomEdge(self, lyr, mesh, spice, matls):
    if (mesh.width < 3) or (mesh.height < 2):
      return
    GBoundary= matls.boundCond
    for x in range(1, mesh.width-1):
      y= mesh.height-1
      nodeThis= mesh.getNodeAtXY(x, y)
      nodeRight= mesh.getNodeAtXY(x+1, y)
      nodeUp= mesh.getNodeAtXY(x, y-1)
      nodeLeft= mesh.getNodeAtXY(x-1, y)

      nodeResis= mesh.field[x, y, lyr.resis]
      nodeRightResis= mesh.field[x+1, y, lyr.resis]
      nodeUpResis= mesh.field[x, y-1, lyr.resis]
      nodeLeftResis= mesh.field[x-1, y, lyr.resis]
      GRight= 2.0/(nodeResis + nodeRightResis)
      GUp= 2.0/(nodeResis + nodeUpResis)
      GLeft= 2.0/(nodeResis + nodeLeftResis)
      GNode= GRight + GUp + GLeft + self.GDamping
      self.BottomEdgeNodeCount += 1
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        if self.debug == True:
          print "Setting boundaryNode be", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)

      self.A[nodeThis, nodeThis]= GNode
      self.A[nodeThis, nodeRight]= -GRight
      self.A[nodeRight, nodeThis]= -GRight
      self.A[nodeThis, nodeUp]= -GUp
      self.A[nodeUp, nodeThis]= -GUp
      self.A[nodeThis, nodeLeft]= -GLeft
      self.A[nodeLeft, nodeThis]= -GLeft
      if self.debug == True:
        self.As[nodeThis, nodeThis]= GNode
        self.As[nodeThis, nodeRight]= -GRight
        self.As[nodeRight, nodeThis]= -GRight
        self.As[nodeThis, nodeUp]= -GUp
        self.As[nodeUp, nodeThis]= -GUp
        self.As[nodeThis, nodeLeft]= -GLeft
        self.As[nodeLeft, nodeThis]= -GLeft
      if self.useSpice == True:
        thisSpiceNode=   "N" + str(x)   + self.s + str(y)
        spiceNodeRight=  "N" + str(x+1) + self.s + str(y)
        mesh.spiceNodeXName[thisSpiceNode] = x
        mesh.spiceNodeYName[thisSpiceNode] = y        
        RRight= 1.0/GRight
        spice.appendSpiceNetlist("RBER" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n")

  def loadMatrixLeftEdge(self, lyr, mesh, spice, matls):
    if (mesh.width < 2) or (mesh.height < 3):
      return
    GBoundary= matls.boundCond
    for y in range(1, mesh.height-1):
      x= 0
      nodeThis= mesh.getNodeAtXY(x, y)
      nodeRight= mesh.getNodeAtXY(x+1, y)
      nodeUp= mesh.getNodeAtXY(x, y-1)
      nodeDown= mesh.getNodeAtXY(x, y+1)

      nodeResis= mesh.field[x, y, lyr.resis]
      nodeRightResis= mesh.field[x+1, y, lyr.resis]
      nodeUpResis= mesh.field[x, y-1, lyr.resis]
      nodeDownResis= mesh.field[x, y+1, lyr.resis]
      GRight= 2.0/(nodeResis + nodeRightResis)
      GUp= 2.0/(nodeResis + nodeUpResis)
      GDown= 2.0/(nodeResis + nodeDownResis)
      GNode= GRight + GUp + GDown + self.GDamping
      self.LeftEdgeNodeCount += 1
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        if self.debug == True:
          print "Setting boundaryNode le", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)

      self.A[nodeThis, nodeThis]= GNode
      self.A[nodeThis, nodeRight]= -GRight
      self.A[nodeRight, nodeThis]= -GRight
      self.A[nodeThis, nodeUp]= -GUp
      self.A[nodeUp, nodeThis]= -GUp
      self.A[nodeThis, nodeDown]= -GDown
      self.A[nodeDown, nodeThis]= -GDown
      if self.debug == True:
        self.As[nodeThis, nodeThis]= GNode
        self.As[nodeThis, nodeRight]= -GRight
        self.As[nodeRight, nodeThis]= -GRight
        self.As[nodeThis, nodeUp]= -GUp
        self.As[nodeUp, nodeThis]= -GUp
        self.As[nodeThis, nodeDown]= -GDown
        self.As[nodeDown, nodeThis]= -GDown
      if self.useSpice == True:
        thisSpiceNode=   "N" + str(x)   + self.s + str(y)
        spiceNodeRight=  "N" + str(x+1) + self.s + str(y)
        spiceNodeDown=   "N" + str(x)   + self.s + str(y+1)
        mesh.spiceNodeXName[thisSpiceNode] = x
        mesh.spiceNodeYName[thisSpiceNode] = y        
        RRight= 1.0/GRight
        RDown=  1.0/GDown
        spice.appendSpiceNetlist("RLER" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n")
        spice.appendSpiceNetlist("RLED" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n")

  def loadMatrixTopLeftCorner(self, lyr, mesh, spice, matls):
    if (mesh.width < 2) or (mesh.height < 2):
      return
    GBoundary= matls.boundCond
    y = 0
    x = 0
    nodeThis= mesh.getNodeAtXY(x, y)
    nodeRight= mesh.getNodeAtXY(x+1, y)
    nodeDown= mesh.getNodeAtXY(x, y+1)

    nodeResis= mesh.field[x, y, lyr.resis]
    nodeRightResis= mesh.field[x+1, y, lyr.resis]
    nodeDownResis= mesh.field[x, y+1, lyr.resis]
    GRight= 2.0/(nodeResis + nodeRightResis)
    GDown= 2.0/(nodeResis + nodeDownResis)
    GNode= GRight + GDown + self.GDamping
    self.TopLeftCornerNodeCount += 1
    if (mesh.ifield[x, y, lyr.isoflag] == 1):
      if self.debug == True:
        print "Setting boundaryNode tlc", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
      GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)

    self.A[nodeThis, nodeThis]= GNode
    self.A[nodeThis, nodeRight]= -GRight
    self.A[nodeRight, nodeThis]= -GRight
    self.A[nodeThis, nodeDown]= -GDown
    self.A[nodeDown, nodeThis]= -GDown
    if self.debug == True:
      self.As[nodeThis, nodeThis]= GNode
      self.As[nodeThis, nodeRight]= -GRight
      self.As[nodeRight, nodeThis]= -GRight
      self.As[nodeThis, nodeDown]= -GDown
      self.As[nodeDown, nodeThis]= -GDown
    if self.useSpice == True:
      thisSpiceNode=   "N" + str(x)   + self.s + str(y)
      spiceNodeRight=  "N" + str(x+1) + self.s + str(y)
      spiceNodeDown=   "N" + str(x)   + self.s + str(y+1)
      mesh.spiceNodeXName[thisSpiceNode] = x
      mesh.spiceNodeYName[thisSpiceNode] = y      
      RRight= 1.0/GRight
      RDown=  1.0/GDown
      spice.appendSpiceNetlist("RTLCR" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n")
      spice.appendSpiceNetlist("RTLCD" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n")

  def loadMatrixTopRightCorner(self, lyr, mesh, spice, matls):
    if ((mesh.width < 2) or (mesh.height < 2)):
      return
    GBoundary= matls.boundCond
    x= mesh.width-1
    y= 0
    nodeThis= mesh.getNodeAtXY(x, y)
    nodeLeft= mesh.getNodeAtXY(x-1, y)
    nodeDown= mesh.getNodeAtXY(x, y+1)

    nodeResis= mesh.field[x, y, lyr.resis]
    nodeLeftResis= mesh.field[x-1, y, lyr.resis]
    nodeDownResis= mesh.field[x, y+1, lyr.resis]
    GLeft= 2.0/(nodeResis + nodeLeftResis)
    GDown= 2.0/(nodeResis + nodeDownResis)
    GNode= GLeft + GDown + self.GDamping
    self.TopRightCornerNodeCount += 1
    if (mesh.ifield[x, y, lyr.isoflag] == 1):
      if self.debug == True:
        print "Setting boundaryNode trc", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
      GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)

    self.A[nodeThis, nodeThis]= GNode
    self.A[nodeThis, nodeLeft]= -GLeft
    self.A[nodeLeft, nodeThis]= -GLeft
    self.A[nodeThis, nodeDown]= -GDown
    self.A[nodeDown, nodeThis]= -GDown
    if self.debug == True:
      self.As[nodeThis, nodeThis]= GNode
      self.As[nodeThis, nodeLeft]= -GLeft
      self.As[nodeLeft, nodeThis]= -GLeft
      self.As[nodeThis, nodeDown]= -GDown
      self.As[nodeDown, nodeThis]= -GDown
    if self.useSpice == True:
      thisSpiceNode=   "N" + str(x)   + self.s + str(y)
      spiceNodeDown=   "N" + str(x)   + self.s + str(y+1)
      mesh.spiceNodeXName[thisSpiceNode] = x
      mesh.spiceNodeYName[thisSpiceNode] = y      
      RDown=  1.0/GDown
      spice.appendSpiceNetlist("RTRCD" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n")

  def loadMatrixBottomRightCorner(self, lyr, mesh, spice, matls):
    if (mesh.width < 2) or (mesh.height < 2):
      return
    GBoundary= matls.boundCond
    x= mesh.width-1
    y= mesh.height-1
    nodeThis= mesh.getNodeAtXY(x, y)
    nodeUp= mesh.getNodeAtXY(x, y-1)
    nodeLeft= mesh.getNodeAtXY(x-1, y)

    nodeResis= mesh.field[x, y, lyr.resis]
    nodeUpResis= mesh.field[x, y-1, lyr.resis]
    nodeLeftResis= mesh.field[x-1, y, lyr.resis]
    GUp= 2.0/(nodeResis + nodeUpResis)
    GLeft= 2.0/(nodeResis + nodeLeftResis)
    GNode= GUp + GLeft + self.GDamping
    self.BottomRightCornerNodeCount += 1
    if (mesh.ifield[x, y, lyr.isoflag] == 1):
      if self.debug == True:
        print "Setting boundaryNode trc", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
      GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)

    self.A[nodeThis, nodeThis]= GNode
    self.A[nodeThis, nodeUp]= -GUp
    self.A[nodeUp, nodeThis]= -GUp
    self.A[nodeThis, nodeLeft]= -GLeft
    self.A[nodeLeft, nodeThis]= -GLeft
    if self.debug == True:
      self.As[nodeThis, nodeThis]= GNode
      self.As[nodeThis, nodeUp]= -GUp
      self.As[nodeUp, nodeThis]= -GUp
      self.As[nodeThis, nodeLeft]= -GLeft
      self.As[nodeLeft, nodeThis]= -GLeft
    if self.useSpice == True:
      thisSpiceNode=   "N" + str(x)   + self.s + str(y)
      spiceNodeDown=   "N" + str(x)   + self.s + str(y+1)
      mesh.spiceNodeXName[thisSpiceNode] = x
      mesh.spiceNodeYName[thisSpiceNode] = y      

  def loadMatrixBottomLeftCorner(self, lyr, mesh, spice, matls):
    if (mesh.height < 2) or (mesh.width < 2):
      return
    GBoundary= matls.boundCond
    x= 0
    y= mesh.height-1
    nodeThis= mesh.getNodeAtXY(x, y)
    nodeRight= mesh.getNodeAtXY(x+1, y)
    nodeUp= mesh.getNodeAtXY(x, y-1)

    nodeResis= mesh.field[x, y, lyr.resis]
    nodeRightResis= mesh.field[x+1, y, lyr.resis]
    nodeUpResis= mesh.field[x, y-1, lyr.resis]
    GRight= 2.0/(nodeResis + nodeRightResis)
    GUp= 2.0/(nodeResis + nodeUpResis)
    GNode= GRight + GUp + self.GDamping
    self.BottomLeftCornerNodeCount += 1
    if (mesh.ifield[x, y, lyr.isoflag] == 1):
      if self.debug == True:
        print "Setting boundaryNode blc", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
      GNode = self.addIsoNode(lyr, mesh, spice, matls, nodeThis, x, y, GNode)
      
    self.A[nodeThis, nodeThis]= GNode
    self.A[nodeThis, nodeRight]= -GRight
    self.A[nodeRight, nodeThis]= -GRight
    self.A[nodeThis, nodeUp]= -GUp
    self.A[nodeUp, nodeThis]= -GUp
    if self.debug == True:
      self.As[nodeThis, nodeThis]= GNode
      self.As[nodeThis, nodeRight]= -GRight
      self.As[nodeRight, nodeThis]= -GRight
      self.As[nodeThis, nodeUp]= -GUp
      self.As[nodeUp, nodeThis]= -GUp
    if self.useSpice == True:
      thisSpiceNode=   "N" + str(x)   + self.s + str(y)
      spiceNodeRight=  "N" + str(x+1) + self.s + str(y)
      mesh.spiceNodeXName[thisSpiceNode] = x
      mesh.spiceNodeYName[thisSpiceNode] = y      
      RRight= 1.0/GRight
      spice.appendSpiceNetlist("RBLCR" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n")

  # NORTON: Remove extra node initialization from here.
  # There are fewer nodes in the NORTON version.
  # There is no isonode layer in the NORTON.
  def addIsoNode(self, lyr, mesh, spice, matls, nodeThis, x, y, GNode):
    GNode = GNode + matls.boundCond
    # boundaryNode is not generated, so this variable is not in NORTON
    boundaryNode = mesh.ifield[x, y, lyr.isonode]
    
    # In NORTON the isoIdx does not position the self.b row, instead it is just the node at x, y
    # that gets incremented by the amount of current in the boundary,
    # which is mesh.field[x, y, lyr.isodeg] * matls.boundCond
    # Or, maybe it needs to go in a local array and all of this is taken care of at once.
    # There may be problems retrieving values from self.b due to the complexity of the Trilinos map,
    # which can go across mpi boundaries.
    # The real problem is doing a thread-safe += operation across processors.
    self.b[self.isoIdx + mesh.nodeDcount]= mesh.field[x, y, lyr.isodeg]
    self.A[nodeThis, nodeThis]= GNode

    # This is the B and C matrix, not needed in NORTON
    self.A[boundaryNode, self.isoIdx + mesh.nodeDcount]= 1.0
    self.A[self.isoIdx + mesh.nodeDcount, boundaryNode]= 1.0
    
    # There is no diagonal term on the boundary conductivity, so these are not in NORTON
    self.A[boundaryNode, boundaryNode]= matls.boundCond
    self.A[boundaryNode, nodeThis]= -matls.boundCond
    self.A[nodeThis, boundaryNode]= -matls.boundCond

    if self.debug == True:
      self.bs[self.isoIdx + mesh.nodeDcount]= mesh.field[x, y, lyr.isodeg]
      self.As[nodeThis, nodeThis]= GNode
      self.As[boundaryNode, self.isoIdx + mesh.nodeDcount]= 1.0
      self.As[self.isoIdx + mesh.nodeDcount, boundaryNode]= 1.0
      self.As[boundaryNode, boundaryNode]= self.GDamping
      self.As[boundaryNode, boundaryNode]= matls.boundCond
      self.As[boundaryNode, nodeThis]= -matls.boundCond
      self.As[nodeThis, boundaryNode]= -matls.boundCond
      print "  source vector idx= ", self.isoIdx
      print "  node with thermal source attached= ", nodeThis
      print "  node for boundary source= ", boundaryNode
      print "  row for source vector 1 multiplier= ", self.isoIdx + mesh.nodeDcount
      
    if self.useSpice == True:
      thisSpiceNode=   "N" + str(x)   + self.s + str(y)
      
      # Norton equivalent boundary resistance and current source.
      if self.useNorton == True:
        thisIsoSource=   "I" + thisSpiceNode
      else:
        thisIsoSource=   "V" + thisSpiceNode
      
      thisBoundaryNode=  "NDIRI" + self.s + str(x) + self.s + str(y)
      thisBoundaryResistor=  "RDIRI" + self.s + str(x) + self.s + str(y)
      thisBoundaryResistance= 1.0/matls.boundCond
      
      if self.useNorton == True:
        thisBoundaryCurrent= mesh.field[x, y, lyr.isodeg]/thisBoundaryResistance
        spice.appendSpiceNetlist(thisIsoSource + " 0 " + thisSpiceNode + " DC " + str(thisBoundaryCurrent) + "\n")
        spice.appendSpiceNetlist(thisBoundaryResistor + " " + thisSpiceNode + " 0 " + str(thisBoundaryResistance) + "\n")
      else:  
        spice.appendSpiceNetlist(thisIsoSource + " " + thisBoundaryNode + " 0 DC " + str(mesh.field[x, y, lyr.isodeg]) + "\n")
        spice.appendSpiceNetlist(thisBoundaryResistor + " " + thisSpiceNode + " " + thisBoundaryNode + " " + str(thisBoundaryResistance) + "\n") 
   
    self.isoIdx = self.isoIdx + 1
    self.BoundaryNodeCount += 1
    return GNode
            
  def loadSolutionIntoMesh(self, lyr, mesh):
    """
    loadSolutionIntoMesh(Solver self, Layers lyr, Mesh mesh)
    Load the solution back into a layer on the mesh
    """
    for x in range(0, mesh.width):
      for y in range(0, mesh.height):
        nodeThis= mesh.getNodeAtXY(x, y)
        mesh.field[x, y, lyr.deg] = self.x[nodeThis]
        # print "Temp x y t ", x, y, self.x[nodeThis]   

  def totalNodeCount(self):
    """
    totalNodeCount(Solver self)
    This is used for matrix diagnostic output
    """
    # For NORTON the self.BoundaryNodeCount will need to be removed.
    totalNodeCount = self.BodyNodeCount + self.TopEdgeNodeCount + self.RightEdgeNodeCount + self.BottomEdgeNodeCount + self.LeftEdgeNodeCount + self.TopLeftCornerNodeCount + self.TopRightCornerNodeCount + self.BottomRightCornerNodeCount + self.BottomLeftCornerNodeCount + self.BoundaryNodeCount
    return totalNodeCount        
            
            
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
    solveMatrixAztecOO(Solver self)
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
    ierr = solver.Iterate(iterations, 1e-8)
    
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
    temperatureStartNode, temperatureEndNode, dirichletStartNode, dirichletEndNode = self.getNodeCounts(mesh, lyr)   
    powerIn = 0
    powerOut = 0
    for n in range(temperatureStartNode, temperatureEndNode):
      powerIn = powerIn + self.b[n]
    # For NORTON equivalent formulation this will need to change. The dirichletNodes do not exist.
    # Power out is the current in the boundary resistors that are not due to the boundary current source.
    for n in range(dirichletStartNode, dirichletEndNode):
      powerOut = powerOut + self.x[n]
    print "Power In = ", powerIn
    print "Power Out = ", powerOut

  def getNodeCounts(self, mesh, lyr):
    """
    getNodeCounts(Solver self, Mesh mesh, Layers lyr)
    Finds indexes of regions within the Solver A matrix corresponding to different parts of the problem description.
    Return values:
    temperatureStartNode - first node number corresponding to nodes added by problem description
    temperatureEndNode - last node number corresponding to nodes added by problem description
    dirichletStartNode - first node number corresponding to extra nodes added due to Dirichlet boundary conditions
    dirichletEndNode - last node number corresponding to extra nodes added due to Dirichlet boundary conditions    
    """
    temperatureStartNode= 0
    temperatureEndNode= mesh.solveTemperatureNodeCount()
    # For NORTON equivalent formulation these dirichlet nodes will not exist.
    dirichletStartNode= temperatureEndNode + mesh.nodeDcount
    dirichletEndNode= dirichletStartNode + mesh.boundaryDirichletNodeCount(lyr)
    if self.debug == True:
      print "deg Start Node= ", temperatureStartNode
      print "deg End Node= ", temperatureEndNode
      print "dirichlet Start Node= ", dirichletStartNode
      print "dirichlet End Node= ", dirichletEndNode
    return temperatureStartNode, temperatureEndNode, dirichletStartNode, dirichletEndNode

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
      
    