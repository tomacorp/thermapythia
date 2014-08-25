#!/Users/toma/python278i/bin/python
# Tom Anderson
# Thermal simulation prototype
# Sun Jul 13 22:30:26 PDT 2014

# TODO: also output a spice deck for verification purposes.

import matplotlib.pyplot as plt
import numpy as np
from PyTrilinos import Epetra, AztecOO

# Construction


# Layers
class Layers:
  def __init__(self):

# Field layers for double float values in mesh.field
    self.iso = 0
    self.heat = 1
    self.resis = 2
    self.deg = 3
    self.flux = 4
    self.isodeg = 5
    self.numdoublelayers = 6

# Field layers for integer float values in mesh.ified
    self.isonode = 0
    self.isoflag = 1
    self.numintlayers = 2

# Convergence monitor
class Monitors:
  def __init__(self):
    self.maxtemp = -273
    self.powerin = 0
    self.powerout = 0
    self.verbose = 0

# Mesh the field
class Mesh:
  def __init__(self, w, h, lyr):
    self.width = w
    self.height = h
    self.field = np.zeros((self.width, self.height, lyr.numdoublelayers), dtype = 'double')
    self.ifield = np.zeros((self.width, self.height, lyr.numintlayers), dtype = 'int')
    self.xr, self.yr= np.mgrid[0:self.width+1, 0:self.height+1]
    self.nodeGcount = 0
    self.nodeDcount = 0
    self.nodeCount = 0
    self.nodeGBcount = 0
    self.nodeGFcount = 0

  def solveTemperatureNodeCount(self):
    # The node count is one more than the maximum index.
    # getNodeAtXY starts a 0
    count= self.getNodeAtXY(self.width - 1, self.height - 1) + 1
    return count

  def boundaryDirichletNodeCount(self, lyr):
    count = 0;
    for x in range(0, self.width):
      for y in range(0, self.height):
        if (self.ifield[x, y, lyr.isoflag] == 1):
          count = count + 1
    return count

  def getNodeAtXY(self, x, y):
    node= x + (y * self.width)
    return node

  def getXAtNode(self, node):
    if (node > self.width * self.height - 1):
      return ''
    x = node % self.width
    return x
  
  def getYAtNode(self, node):
    if (node > self.width * self.height - 1):
      return ''
    x = self.getXAtNode(node)
    y = node - x
    y = y / self.width
    return y

  def mapMeshToSolutionMatrix(self, lyr):
    #
    # A matrix is in sections:
    #   
    #       |  G   B  |
    #   A = |  C   D  |
    #      G transconductance matrix
    #      B sources, which in this case are just 1s
    #      C transpose of B
    #      D zeroes
    #   G is in two sections, which are the upper left GF (for field) and GB (for boundary)
    #   The analysis is of the form  Ax = b
    #   For rows in b corresponding to G,  
    #      b is the known value of the current (constant power in thermal circuits) sources
    #   For rows in b corresponding to D, (constant temperature boundary conditions) 
    #      b is the known value of temperature at the boundary.
    #   The number of rows in D is self.nodeDcount
    #   The number of rows in G is self.nodeGcount
    #   The number of rows in GF is self.nodeGFcount
    #   The number of rows in GB is self.nodeGBcount
    #   The total number of rows in A is self.nodeCount
    #
    #   The solution to the matrix is the vector x
    #   For rows in x corresponding to G, these are voltages (temperature)
    #   For rows in x corresponding to D, these are currents (power flow) in the boundary condition.
    #
    #   For energy balance in steady state, the current into the constant-temperature boundary condition 
    #   must equal the current from the constant-power thermal sources.
    # 
    #   The index of the last nodes in the G submatrix for the field plus one is the number
    #   of nodes in the field GF. Add the boundary nodes GB to G.
    #
    #   Also count the number of boundary sources, which is the size of the D matrix. 
    #   
    self.nodeGcount = self.getNodeAtXY(self.width - 1, self.height - 1)
    self.nodeCount = self.nodeGcount + 1
    self.nodeGFcount = self.nodeCount
    # Find the number of nodes in the submatrices
    for x in range(0, self.width):
      for y in range(0, self.height):
        if (self.ifield[x, y, lyr.isoflag] == 1):
          print "Mapping mesh isothermal node at (x, y) = (", x, ", ", y, ")"
          # Every boundary condition gets a new node
          self.nodeGcount = self.nodeGcount + 1
          self.nodeGBcount = self.nodeGBcount + 1
          self.nodeCount = self.nodeCount + 1
          # Every boundary condition gets a new voltage source
          self.nodeDcount = self.nodeDcount + 1
          self.ifield[x, y, lyr.isonode] = self.nodeGcount
          self.nodeCount = self.nodeCount + 1
    self.nodeGcount = self.nodeGcount + 1
    print "Number of independent nodes in G matrix= ", self.nodeGcount
    print "Number of independent nodes in GF matrix= ", self.nodeGFcount
    print "Number of independent nodes in GB matrix= ", self.nodeGBcount
    print "Number of independent nodes in D matrix= ", self.nodeDcount
    print "Total number of independent nodes= ", self.nodeCount

class Matls:
  def __init__(self):
    self.fr4Cond    = 1
    self.copperCond = 10
    self.boundCond = 100

# This can scale by using a PNG input instead of code
def defineproblem(lyr, mesh, matls):

  mesh.field[:, :, lyr.heat]  = 0.0
  mesh.field[:, :, lyr.resis] = matls.copperCond
  mesh.field[:, :, lyr.deg]   = 20
  mesh.field[:, :, lyr.flux]  = 0.0
  mesh.field[:, :, lyr.isodeg] = 0.0
  mesh.ifield[:, :, lyr.isoflag] = 0
  mesh.ifield[:, :, lyr.isonode] = 0
  
  # Heat source
  hsx= 0.5
  hsy= 0.5
  hswidth= 0.25
  hsheight= 0.25
  heat= 1.0
  srcl= round(mesh.width*(hsx-hswidth*0.5))
  srcr= round(mesh.width*(hsx+hswidth*0.5))
  srct= round(mesh.height*(hsy-hsheight*0.5))
  srcb= round(mesh.height*(hsy+hsheight*0.5))
  numHeatCells= (srcr - srcl)*(srcb-srct)
  heatPerCell= heat/numHeatCells
  print "Heat per cell = ", heatPerCell
  mesh.field[srcl:srcr, srct:srcb, lyr.heat] = heatPerCell
  mesh.field[srcl:srcr, srct:srcb, lyr.resis] = 1.0
  
  # Boundary conditions
  mesh.field[0, 0:mesh.height, lyr.isodeg] = 25.0
  mesh.field[mesh.width-1, 0:mesh.height, lyr.isodeg] = 25.0
  mesh.field[0:mesh.width, 0, lyr.isodeg] = 25.0
  mesh.field[0:mesh.width, mesh.height-1, lyr.isodeg] = 25.0
  mesh.ifield[0, 0:mesh.height, lyr.isoflag] = 1
  mesh.ifield[mesh.width-1, 0:mesh.height, lyr.isoflag] = 1
  mesh.ifield[0:mesh.width, 0, lyr.isoflag] = 1
  mesh.ifield[0:mesh.width, mesh.height-1, lyr.isoflag] = 1
  
  # Thermal conductors
  condwidth= 0.05
  cond1l= round(mesh.width*hsx - mesh.width*condwidth*0.5)
  cond1r= round(mesh.width*hsx + mesh.width*condwidth*0.5)
  cond1t= round(mesh.height*hsy - mesh.height*condwidth*0.5)
  cond1b= round(mesh.height*hsy + mesh.height*condwidth*0.5)
  mesh.field[0:mesh.width, cond1t:cond1b, lyr.resis] = matls.copperCond
  mesh.field[cond1l:cond1r, 0:mesh.height, lyr.resis] = matls.copperCond

# This can scale by using a PNG output
    # Mesh defaults at the input
    # mesh.field[:, :, lyr.heat]  = 0.0
    # mesh.field[:, :, lyr.resis] = 100
    # mesh.field[:, :, lyr.isodeg]  = 0.0
    # mesh.field[:, :, lyr.isoflag] = 0
    # mesh.field[:, :, lyr.deg]   = 23
    # mesh.field[:, :, lyr.flux]  = 0.0

def plotsolution(lyr, mesh):
  z1= mesh.field[:, :, lyr.resis];
  z2= mesh.field[:, :, lyr.deg];
  z3= mesh.field[:, :, lyr.isodeg];
  z4= mesh.field[:, :, lyr.heat];
  z5= mesh.ifield[:, :, lyr.isoflag];

  plt.figure(1)
  plt.subplot(1,1,1)
  plt.axes(aspect=1)
  quad1= plt.pcolormesh(mesh.xr, mesh.yr, z1)
  plt.colorbar()
  plt.draw()
  
  plt.figure(2)
  plt.subplot(1,1,1)
  plt.axes(aspect=1)
  quad2= plt.pcolormesh(mesh.xr, mesh.yr, z2)
  plt.colorbar()
  plt.draw()
  
  plt.figure(3)
  plt.subplot(1,1,1)
  plt.axes(aspect=1)
  quad3= plt.pcolormesh(mesh.xr, mesh.yr, z3)
  plt.colorbar()
  plt.draw()
  
  plt.figure(4)
  plt.subplot(1,1,1)
  plt.axes(aspect=1)
  quad4= plt.pcolormesh(mesh.xr, mesh.yr, z4)
  plt.colorbar()
  plt.draw()

  plt.figure(5)
  plt.subplot(1,1,1)
  plt.axes(aspect=1)
  quad4= plt.pcolormesh(mesh.xr, mesh.yr, z5)
  plt.colorbar()
  plt.draw()

  plt.show()

class Solver:

  def __init__(self, lyr, mesh):
    # define the communicator (Serial or parallel, depending on your configure
    # line), then initialize a distributed matrix of size 4. The matrix is empty,
    # `0' means to allocate for 0 elements on each row (better estimates make the
    # code faster). `NumMyElements' is the number of rows that are locally hosted 
    # by the calling processor; `MyGlobalElements' is the global ID of locally 
    # hosted rows.
    self.Comm              = Epetra.PyComm()
    self.NumGlobalElements = mesh.nodeCount
    self.Map               = Epetra.Map(self.NumGlobalElements, 0, self.Comm)
    self.A                 = Epetra.CrsMatrix(Epetra.Copy, self.Map, 0)
    self.NumMyElements     = self.Map.NumMyElements()
    self.MyGlobalElements  = self.Map.MyGlobalElements()
    self.b                 = Epetra.Vector(self.Map)
    self.isoIdx            = 0
    self.debug             = False
    self.spice             = True
    self.deck              = ''
    self.GDamping          = 1e-12
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
  def setDebug(self, flag):
    if flag == True:
      self.As = np.zeros((self.NumGlobalElements, self.NumGlobalElements), dtype = 'double')
      self.bs = np.zeros(self.NumGlobalElements)
    self.debug = flag

  # The field transconductance matrix GF is in nine sections:
  #   
  #     top left corner           top edge           top right corner
  #     left edge                 body               right edge
  #     bottom right corner       bottom edge        bottom right corner
  #
    
  # A is the problem matrix
  # Modified nodal analysis
  # http://www.swarthmore.edu/NatSci/echeeve1/Ref/mna/MNA2.html

  def loadMatrix(self, lyr, mesh, matls):
    self.isoIdx = mesh.nodeGFcount
    print "Starting iso nodes at ", self.isoIdx
    self.loadMatrixBody(lyr, mesh, matls)
    self.loadMatrixTopEdge(lyr, mesh, matls)
    self.loadMatrixRightEdge(lyr, mesh, matls)
    self.loadMatrixBottomEdge(lyr, mesh, matls)
    self.loadMatrixLeftEdge(lyr, mesh, matls)
    self.loadMatrixTopLeftCorner(lyr, mesh, matls)
    self.loadMatrixTopRightCorner(lyr, mesh, matls)
    self.loadMatrixBottomRightCorner(lyr, mesh, matls)
    self.loadMatrixBottomLeftCorner(lyr, mesh, matls)
    self.loadMatrixHeatSources(lyr, mesh)
    # b is the RHS, which are current sources for injected heat and voltage sources for 
    #   dirichlet boundary conditions.

  def loadMatrixHeatSources(self, lyr, mesh):
    # Add the injected heat sources.
    for x in range(0, mesh.width):
      for y in range(0, mesh.height):
        nodeThis= mesh.getNodeAtXY(x, y)
        self.b[nodeThis]= mesh.field[x, y, lyr.heat]
        if self.debug == True:
          self.bs[nodeThis]= mesh.field[x, y, lyr.heat]
        if self.spice == True:
          if (mesh.field[x, y, lyr.heat] > 0.0):
            thisSpiceNode=   "N" + str(x) + "_" + str(y)
            thisHeatSource=   "I" + thisSpiceNode
            thisHeat= -mesh.field[x, y, lyr.heat]
            self.deck += thisHeatSource + " " + thisSpiceNode + " 0 DC " + str(thisHeat) + "\n"

  def loadMatrixBody(self, lyr, mesh, matls):
    GBoundary= matls.boundCond
    for x in range(1, mesh.width-1):
      for y in range(1, mesh.height-1):
        nodeThis  = mesh.getNodeAtXY(x,   y)
        nodeRight = mesh.getNodeAtXY(x+1, y)
        nodeUp    = mesh.getNodeAtXY(x,   y-1)
        nodeLeft  = mesh.getNodeAtXY(x-1, y)
        nodeDown  = mesh.getNodeAtXY(x,   y+1)

        nodeResis=      mesh.field[x,   y,   lyr.resis]
        nodeRightResis= mesh.field[x+1, y,   lyr.resis]
        nodeUpResis=    mesh.field[x,   y-1, lyr.resis]
        nodeLeftResis=  mesh.field[x-1, y,   lyr.resis]
        nodeDownResis=  mesh.field[x,   y+1, lyr.resis]
        GRight= 2.0/(nodeResis + nodeRightResis)
        GUp=    2.0/(nodeResis + nodeUpResis)
        GLeft=  2.0/(nodeResis + nodeLeftResis)
        GDown=  2.0/(nodeResis + nodeDownResis)
        GNode= GRight + GUp + GLeft + GDown + self.GDamping
        self.BodyNodeCount += 1
        if (mesh.ifield[x, y, lyr.isoflag] == 1):
          if self.debug == True:
            print "Setting boundaryNode body", nodeThis, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
          GNode = self.addIsoNode(lyr, mesh, matls, nodeThis, x, y, GNode)

        self.A[nodeThis, nodeThis]= GNode
        self.A[nodeThis, nodeRight]= -GRight
        self.A[nodeRight, nodeThis]= -GRight
        self.A[nodeThis, nodeUp]= -GUp
        self.A[nodeUp, nodeThis]= -GUp
        self.A[nodeThis, nodeLeft]= -GLeft
        self.A[nodeLeft, nodeThis]= -GLeft
        self.A[nodeThis, nodeDown]= -GDown
        self.A[nodeDown, nodeThis]= -GDown
        if self.debug == True:
          self.As[nodeThis, nodeThis]= GNode
          self.As[nodeThis, nodeRight]= -GRight
          self.As[nodeRight, nodeThis]= -GRight
          self.As[nodeThis, nodeUp]= -GUp
          self.As[nodeUp, nodeThis]= -GUp
          self.As[nodeThis, nodeLeft]= -GLeft
          self.As[nodeLeft, nodeThis]= -GLeft
          self.As[nodeThis, nodeDown]= -GDown
          self.As[nodeDown, nodeThis]= -GDown
        if self.spice == True:
          thisSpiceNode=   "N" + str(x)   + "_" + str(y)
          spiceNodeRight=  "N" + str(x+1) + "_" + str(y)
          spiceNodeDown=   "N" + str(x)   + "_" + str(y+1)
          RRight= 1.0/GRight
          RDown=  1.0/GDown
          self.deck += "RFR" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n"
          self.deck += "RFD" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n"

  def loadMatrixTopEdge(self, lyr, mesh, matls):
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
        GNode = self.addIsoNode(lyr, mesh, matls, nodeThis, x, y, GNode)
 
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
      if self.spice == True:
        thisSpiceNode=   "N" + str(x)   + "_" + str(y)
        spiceNodeRight=  "N" + str(x+1) + "_" + str(y)
        spiceNodeDown=   "N" + str(x)   + "_" + str(y+1)
        RRight= 1.0/GRight
        RDown=  1.0/GDown
        self.deck += "RTER" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n"
        self.deck += "RTED" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n"

  def loadMatrixRightEdge(self, lyr, mesh, matls):
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
        GNode = self.addIsoNode(lyr, mesh, matls, nodeThis, x, y, GNode)

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
      if self.spice == True:
        thisSpiceNode=   "N" + str(x)   + "_" + str(y)
        spiceNodeDown=   "N" + str(x)   + "_" + str(y+1)
        RDown=  1.0/GDown
        self.deck += "RRED" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n"
    
  def loadMatrixBottomEdge(self, lyr, mesh, matls):
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
        GNode = self.addIsoNode(lyr, mesh, matls, nodeThis, x, y, GNode)

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
      if self.spice == True:
        thisSpiceNode=   "N" + str(x)   + "_" + str(y)
        spiceNodeRight=  "N" + str(x+1) + "_" + str(y)
        RRight= 1.0/GRight
        self.deck += "RBER" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n"

  def loadMatrixLeftEdge(self, lyr, mesh, matls):
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
        GNode = self.addIsoNode(lyr, mesh, matls, nodeThis, x, y, GNode)

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
      if self.spice == True:
        thisSpiceNode=   "N" + str(x)   + "_" + str(y)
        spiceNodeRight=  "N" + str(x+1) + "_" + str(y)
        spiceNodeDown=   "N" + str(x)   + "_" + str(y+1)
        RRight= 1.0/GRight
        RDown=  1.0/GDown
        self.deck += "RLER" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n"
        self.deck += "RLED" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n"

  def loadMatrixTopLeftCorner(self, lyr, mesh, matls):
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
      GNode = self.addIsoNode(lyr, mesh, matls, nodeThis, x, y, GNode)

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
    if self.spice == True:
      thisSpiceNode=   "N" + str(x)   + "_" + str(y)
      spiceNodeRight=  "N" + str(x+1) + "_" + str(y)
      spiceNodeDown=   "N" + str(x)   + "_" + str(y+1)
      RRight= 1.0/GRight
      RDown=  1.0/GDown
      self.deck += "RTLCR" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n"
      self.deck += "RTLCD" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n"

  def loadMatrixTopRightCorner(self, lyr, mesh, matls):
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
      GNode = self.addIsoNode(lyr, mesh, matls, nodeThis, x, y, GNode)

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
    if self.spice == True:
      thisSpiceNode=   "N" + str(x)   + "_" + str(y)
      spiceNodeDown=   "N" + str(x)   + "_" + str(y+1)
      RDown=  1.0/GDown
      self.deck += "RTRCD" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeDown + " " + str(RDown) + "\n"

  def loadMatrixBottomRightCorner(self, lyr, mesh, matls):
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
      GNode = self.addIsoNode(lyr, mesh, matls, nodeThis, x, y, GNode)

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
    # No output for self.spice here

  def loadMatrixBottomLeftCorner(self, lyr, mesh, matls):
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
      GNode = self.addIsoNode(lyr, mesh, matls, nodeThis, x, y, GNode)
      
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
    if self.spice == True:
      thisSpiceNode=   "N" + str(x)   + "_" + str(y)
      spiceNodeRight=  "N" + str(x+1) + "_" + str(y)
      RRight= 1.0/GRight
      self.deck += "RBLCR" + thisSpiceNode + " " + thisSpiceNode + " " + spiceNodeRight + " " + str(RRight) + "\n"

  def addIsoNode(self, lyr, mesh, matls, nodeThis, x, y, GNode):
    GNode = GNode + matls.boundCond
    boundaryNode = mesh.ifield[x, y, lyr.isonode]
    self.b[self.isoIdx + mesh.nodeDcount]= mesh.field[x, y, lyr.isodeg]
    self.A[nodeThis, nodeThis]= GNode
    self.A[boundaryNode, self.isoIdx + mesh.nodeDcount]= 1.0
    self.A[self.isoIdx + mesh.nodeDcount, boundaryNode]= 1.0
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
    if self.spice == True:
      thisSpiceNode=   "N" + str(x)   + "_" + str(y)
      thisIsoSource=   "V" + thisSpiceNode
      thisBoundaryNode=  "NDIRI_" + str(x) + "_" + str(y)
      thisBoundaryResistor=  "RDIRI_" + str(x) + "_" + str(y)
      thisBoundaryResistance= 1.0/matls.boundCond
      self.deck += thisIsoSource + " " + thisBoundaryNode + " 0 DC " + str(mesh.field[x, y, lyr.isodeg]) + "\n"
      self.deck += thisBoundaryResistor + " " + thisSpiceNode + " " + thisBoundaryNode + " " + str(thisBoundaryResistance) + "\n"
   
    self.isoIdx = self.isoIdx + 1
    self.BoundaryNodeCount += 1
    return GNode

  def solveMatrix(self, lyr, mesh, iterations):

    # Debugging output
    if (self.debug == True):
      print "Creating web page"
      np.set_printoptions(threshold='nan', linewidth=10000)
      f= open('result.html', 'w')
      f.write(self.webpage(mesh, lyr))
      f.close()

    if (self.spice == True):
# PATH=/usr/local/Xyce-Release-6.1.0-OPENSOURCE/bin:$PATH
# runxyce therm.cki -a -r therm.asc -l therm.txt
      f= open('therm.cki', 'w')
      f.write("* Thermal network\n")
      f.write(self.deck)
      f.write(".tran .1 .1\n")
      f.write(".print tran\n")
      f.write(".end\n")
      f.close()

    # x are the unknowns to be solved.
    # This set works:
    self.x = Epetra.Vector(self.Map)
    self.A.FillComplete()
    solver = AztecOO.AztecOO(self.A, self.x, self.b)

    # This is from http://trilinos.sandia.gov/packages/pytrilinos/UsersGuide.pdf pg 20
#   self.x = Epetra.Vector(self.Map)
#   self.A.FillComplete()

#   MLList = {
#     "max levels" : 3,
#     "output" : 10,
#     "smoother: type" : "symmetric Gauss-Seidel", 
#     "aggregation: type" : "Uncoupled"
#   };
#   # Then, we create the preconditioner and compute it,
#   Prec = ML.MultiLevelPreconditioner(self.A, False)
#   Prec.SetParameterList(MLList)
#   Prec.ComputePreconditioner()

#   # Finally, we set up the solver, and specifies to use Prec as preconditioner:

#   solver = AztecOO.AztecOO(self.A, self.x, self.b)
#   solver.SetPrecOperator(Prec)
#   solver.SetAztecOption(AztecOO.AZ_solver, AztecOO.AZ_cg); 
#   solver.SetAztecOption(AztecOO.AZ_output, 16);
#   solver.Iterate(1550, 1e-5)

    # This segfaults:
    # solver.SetAztecOption(AztecOO.AZ_precond, AztecOO.AZ_dom_decomp)

    # This does not fail but the solution says that there is no preconditioner
    # solver.SetAztecOption(AztecOO.AZ_subdomain_solve, AztecOO.AZ_ilu)

    # Complains and fails
    # solver.SetParameters({"precond": "dom_decomp",
    #                       "subdomain_solve": "ilu",
    #                       "overlap": 1,
    #                       "graph_fill": 1})

    # This complains and fails
    # solver.SetAztecOption(AztecOO.AZ_solver, AztecOO.AZ_cg)

    # This is incredibly fast but complains some:
    solver.SetAztecOption(AztecOO.AZ_solver, AztecOO.AZ_cg_condnum)

    # This appears to be the default and it works:
    # solver.SetAztecOption(AztecOO.AZ_output, AztecOO.AZ_none)

    # This loads x with the solution to the problem
    solver.Iterate(iterations, 1e-5)

    self.Comm.Barrier()

#   for i in self.MyGlobalElements:
#     print "PE%d: %d %e" % (self.Comm.MyPID(), i, self.x[i])
  
    # synchronize processors
    self.Comm.Barrier()
    if self.Comm.MyPID() == 0: print "End Result: TEST PASSED"

    # Load the solution back into the mesh
    for x in range(0, mesh.width):
      for y in range(0, mesh.height):
        nodeThis= mesh.getNodeAtXY(x, y)
        mesh.field[x, y, lyr.deg] = self.x[nodeThis]
        # print "Temp x y t ", x, y, self.x[nodeThis]

    # Check boundary conditions
    temperatureStartNode= 0
    temperatureEndNode= mesh.solveTemperatureNodeCount()
    dirichletStartNode= temperatureEndNode + mesh.nodeDcount
    dirichletEndNode= dirichletStartNode + mesh.boundaryDirichletNodeCount(lyr)
    print "deg Start Node= ", temperatureStartNode
    print "deg End Node= ", temperatureEndNode
    print "dirichlet Start Node= ", dirichletStartNode
    print "dirichlet End Node= ", dirichletEndNode
    powerIn = 0
    powerOut = 0
    for n in range(temperatureStartNode, temperatureEndNode):
      powerIn = powerIn + self.b[n]
    for n in range(dirichletStartNode, dirichletEndNode):
      powerOut = powerOut + self.x[n]
    print "Power In = ", powerIn
    print "Power Out = ", powerOut

  def totalNodeCount(self):
    totalNodeCount = self.BodyNodeCount + self.TopEdgeNodeCount + self.RightEdgeNodeCount + self.BottomEdgeNodeCount + self.LeftEdgeNodeCount + self.TopLeftCornerNodeCount + self.TopRightCornerNodeCount + self.BottomRightCornerNodeCount + self.BottomLeftCornerNodeCount + self.BoundaryNodeCount
    return totalNodeCount

  def webpage(self, mesh, lyr):
    matrix= ''
    rhsStr= ''
    xhtml= ''
    col= 0
    cols= '* '

    temperatureStartNode= 0
    temperatureEndNode= mesh.solveTemperatureNodeCount()
    dirichletStartNode= temperatureEndNode
    dirichletEndNode= dirichletStartNode + mesh.boundaryDirichletNodeCount(lyr)

    rowType = ''
    for n in range(0, self.NumGlobalElements):
      nodeType= '?'
      if ((n >= temperatureStartNode) and (n < temperatureEndNode)):
        nodeType= 'matl'
      else:
        if ((n >= dirichletStartNode) and (n < dirichletEndNode)):
          nodeType = 'diri'
      rowType = rowType + "<td>" + nodeType + "</td>"

    rowX = ''
    for n in range(0, self.NumGlobalElements):
      x = mesh.getXAtNode(n)
      rowX = rowX + "<td>" + str(x) + "</td>"
    rowY = ''
    for n in range(0, self.NumGlobalElements):
      y = mesh.getYAtNode(n)
      rowY = rowY + "<td>" + str(y) + "</td>"

    # Create matrix table
    for x in range(0, self.NumGlobalElements):
      rhsStr = rhsStr + "<td>" + str("%.3f" % self.bs[x]) + "</td>"
      xhtml = xhtml + "<td>" + str("%.3f" % self.x[x]) + "</td>"
      matrix_row = ''
      for y in range(0, self.NumGlobalElements):
        if self.As[x,y] != 0.0:
          elt= str("%.3f" % self.As[x,y])
        else:
          elt= '.'
        matrix_row = matrix_row + "<td>" + elt + "</td>"
      matrix= matrix + "<tr>" + matrix_row + "</tr>"
      cols = cols + "<td>" + str(col) + "</td>"
      col = col + 1
    matrix = "<table>" + matrix + "</table>"

    # Create vector table
    vectors =           "<tr><td><b>col</b></td>" + cols + "</tr>"
    vectors = vectors + "<tr><td><b>X</b></td>" + rowX + "</tr>"
    vectors = vectors + "<tr><td><b>Y</b></td>" + rowY + "</tr>"
    vectors = vectors + "<tr><td><b>Type</b></td>" + rowType + "</tr>"
    vectors = vectors + "<tr><td><b>rhs</b></td>" + rhsStr + "</tr>"
    vectors = vectors + "<tr><td><b>lhs</b></td>" + xhtml + "</tr>"
    vectors = "<table>" + vectors + "</table>"

    # Counts
    counts = "<tr><td>BodyNodeCount</td><td>" + str(self.BodyNodeCount) + "</td></tr>"
    counts += "<tr><td>TopEdgeNodeCount</td><td>" + str(self.TopEdgeNodeCount) + "</td></tr>"
    counts += "<tr><td>RightEdgeNodeCount</td><td>" + str(self.RightEdgeNodeCount) + "</td></tr>"
    counts += "<tr><td>BottomEdgeNodeCount</td><td>" + str(self.BottomEdgeNodeCount) + "</td></tr>"
    counts += "<tr><td>LeftEdgeNodeCount</td><td>" + str(self.LeftEdgeNodeCount) + "</td></tr>"
    counts += "<tr><td>TopLeftCornerNodeCount</td><td>" + str(self.TopLeftCornerNodeCount) + "</td></tr>"
    counts += "<tr><td>TopRightCornerNodeCount</td><td>" + str(self.TopRightCornerNodeCount) + "</td></tr>"
    counts += "<tr><td>BottomRightCornerNodeCount</td><td>" + str(self.BottomRightCornerNodeCount) + "</td></tr>"
    counts += "<tr><td>BoundaryNodeCount</td><td>" + str(self.BoundaryNodeCount) + "</td></tr>"
    counts += "<tr><td>Total NodeCount</td><td>" + str(self.totalNodeCount()) + "</td></tr>"
    counts += "<tr><td>Matrix Size</td><td>" + str(self.NumGlobalElements) + "</td></tr>"

    counts += "Number of independent nodes in G matrix= " + str(mesh.nodeGcount) + "<br/>"
    counts += "Number of independent nodes in GF matrix= " + str(mesh.nodeGFcount) + "<br/>"
    counts += "Number of independent nodes in GB matrix= " + str(mesh.nodeGBcount) + "<br/>"
    counts += "Number of independent nodes in D matrix= " + str(mesh.nodeDcount) + "<br/>"
    counts += "Total number of independent nodes= " + str(mesh.nodeCount) + "<br/>"
    counts = "<table>" + counts + "</table>"

    # Create web page
    head  = "<title>Matrix output</title>"
    body  = "<h1>Ax = b</h1>"
    body += "<h3>A Matrix</h3>"
    body += "<pre>" + matrix + "</pre>"
    body += "<h3>Vectors</h3>"
    body += "<pre>" + vectors + "</pre>"
    body += "<h3>Counts</h3>"
    body += "<pre>" + counts + "</pre>"
    html= "<html><head>" + head + "</head><body>" + body + "</body></html>"

    return html

# TODO: 
#        Read Xyce source code to see their matrix algorithms.
#        Create test harness for sweeps of problem size.
#        Hook up PNG files.
#        Do a DC analysis instead of TRAN, check memory usage

def Main():
  lyr = Layers()
  monitor = Monitors()
  #  Minimal problem to confirm operation:
  #    mesh = Mesh(5, 5, lyr)
  #  Maximal problem shows steady state in field near zero
  #    mesh = Mesh(1000, 1000, lyr), iterations= 400000 (needs 93965 iterations in 28662 seconds solve time)
  #    rea l372m26.483s
  #    user 477m34.471s
  #    sys 1m48.083s
  showPlots= True
  mesh = Mesh(250, 250, lyr)
  matls = Matls()

  defineproblem(lyr, mesh, matls)
  mesh.mapMeshToSolutionMatrix(lyr)

  solv = Solver(lyr, mesh)
  solv.setDebug(False)
  solv.loadMatrix(lyr, mesh, matls)
  solv.solveMatrix(lyr, mesh, 400000)
  if (showPlots == True):
    plotsolution(lyr, mesh)

# Times without printing much.
# Printing overhead is probably about 10% in this case.
# 10000 iterations
# 100X100 12sec
# 200x200 69sec
# 300x300 154sec

# 1000 iterations
# 200x200 14sec
# 300x300 34 sec
# 
# Design notes:
# The Mesh class 
#   Has a rectangular Numpy field that represents the problem geometry.
#   The Mesh elements are squares in a layered 2D field.
#   The field has layers that are describe by the Layers object.
#   The layers represent details about the geometry of the materials and boundary conditions.
#   Has the size of the problem, such as length, width, and the number of elements.
#   Is decorated with material properties from Matls.
#   Is decorated with the solution to the problem.
# The Layer class
#   Has enumerations that describe the layers in the Mesh
# The Map class
#   Includes a Numpy grid that is the size of the Solver.
#   Is used to access Solver information 
#   Because the solver information is not always available on the local node,
#     the Map class has a local copy of the Solver input data. Some of this
#     data is only needed for debugging and can be turned off to save space.
# The Solver class
#   Loads the and calls the Trilinos solvers.
#

Main()

def gsitersolve(lyr, mesh, monitor):
  finished = 0
  iter = 0
  while ((iter < 1200) and (finished == 0)):
    monitor.powerout = 0
    monitor.powerin = 0
    delta= simstep(iter, lyr, mesh, monitor)
    print iter, delta, monitor.maxtemp, monitor.powerin, monitor.powerout
    powerbalance= (monitor.powerout - monitor.powerin)/(monitor.powerout+monitor.powerin)
    if ((iter > 10) and (abs(powerbalance) < .005)):
      finished = 1
    iter = iter + 1
