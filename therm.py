#!/Users/toma/python278i/bin/python
# Tom Anderson
# Thermal simulation prototype
# Sun Jul 13 22:30:26 PDT 2014

import matplotlib.pyplot as plt
import numpy as np
from PyTrilinos import Epetra, AztecOO

# Construction


# Layers
class Layers:
  def __init__(self):
# Field layers for double float values in mesh.field
#
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
    self.nodecount = self.width * self.height

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

  def countIndepNodes(self, lyr):
    count= self.getNodeAtXY(self.width - 1, self.height - 1)
    for x in range(0, self.width):
      for y in range(0, self.height):
        if (self.ifield[x, y, lyr.isoflag] == 1):
          count = count + 1
          self.ifield[x, y, lyr.isonode] = count
    count = count + 1
    print "Number of independent nodes= ", count
    return count

class Matls:
  def __init__(self):
    self.copper= 10
    self.fr4cond= 0.1

# This can scale by using a PNG input
def defineproblem(lyr, mesh):

  mesh.field[:, :, lyr.heat]  = 0.0
  mesh.field[:, :, lyr.resis] = 100.0
  mesh.field[:, :, lyr.deg]   = 23
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
  mesh.field[0:mesh.width, cond1t:cond1b, lyr.resis] = 10.0
  mesh.field[cond1l:cond1r, 0:mesh.height, lyr.resis] = 10.0

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
    self.NumGlobalElements = mesh.countIndepNodes(lyr)
    self.Map               = Epetra.Map(self.NumGlobalElements, 0, self.Comm)
    self.A                 = Epetra.CrsMatrix(Epetra.Copy, self.Map, 0)
    self.NumMyElements     = self.Map.NumMyElements()
    self.MyGlobalElements  = self.Map.MyGlobalElements()
    self.b                 = Epetra.Vector(self.Map)
    self.debug             = False
    # Make a python shadow data structure that records what is inside the Epetra data structures.
    # This is a non-sparse version used for debugging.
    # This can be used to print out what is going on.
    # Without it, the data structure is hard to access.

  def setDebug(self, flag):
    if flag == True:
      self.As = np.zeros((self.NumGlobalElements, self.NumGlobalElements), dtype = 'double')
      self.bs = np.zeros(self.NumGlobalElements)
    self.debug = flag

  def loadMatrix(self, lyr, mesh):
    
    # A is the problem matrix
    # Modified nodal analysis
    # http://www.swarthmore.edu/NatSci/echeeve1/Ref/mna/MNA2.html

    # The field, away from the edges and corners.
    GBoundary= 10
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
        GNode= GRight + GUp + GLeft + GDown
        if (mesh.ifield[x, y, lyr.isoflag] == 1):
          GNode = GNode + GBoundary
          boundaryNode = mesh.ifield[x, y, lyr.isonode]
          print "Setting boundaryNode field ", boundaryNode, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
          self.b[boundaryNode]= mesh.field[x, y, lyr.isodeg]
          self.A[nodeThis, nodeThis]= GBoundary
          self.A[nodeThis, boundaryNode]= 1.0;
          self.A[boundaryNode, nodeThis]= 1.0;
          if self.debug == True:
            self.bs[boundaryNode]= mesh.field[x, y, lyr.isodeg]
            self.As[nodeThis, nodeThis]= GBoundary
            self.As[nodeThis, boundaryNode]= 1.0;
            self.As[boundaryNode, nodeThis]= 1.0;

#       print x, y, nodeThis
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

    # The top edge
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
      GNode= GRight + GLeft + GDown
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        GNode = GNode + GBoundary
        boundaryNode = mesh.ifield[x, y, lyr.isonode]
        print "Setting boundaryNode te", boundaryNode, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        self.b[boundaryNode]= mesh.field[x, y, lyr.isodeg]
        self.A[nodeThis, nodeThis]= GBoundary
        self.A[nodeThis, boundaryNode]= 1.0;
        self.A[boundaryNode, nodeThis]= 1.0;
        if self.debug == True:
          self.bs[boundaryNode]= mesh.field[x, y, lyr.isodeg]
          self.As[nodeThis, nodeThis]= GBoundary
          self.As[nodeThis, boundaryNode]= 1.0;
          self.As[boundaryNode, nodeThis]= 1.0;
 
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

    # The right edge
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
      GNode= GUp + GLeft + GDown
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        GNode = GNode + GBoundary
        boundaryNode = mesh.ifield[x, y, lyr.isonode]
        print "Setting boundaryNode re", boundaryNode, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        self.b[boundaryNode]= mesh.field[x, y, lyr.isodeg]
        self.A[nodeThis, nodeThis]= GBoundary
        self.A[nodeThis, boundaryNode]= 1.0
        self.A[boundaryNode, nodeThis]= 1.0
        if self.debug == True:
          self.bs[boundaryNode]= mesh.field[x, y, lyr.isodeg]
          self.As[nodeThis, nodeThis]= GBoundary
          self.As[nodeThis, boundaryNode]= 1.0;
          self.As[boundaryNode, nodeThis]= 1.0;

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
    
    # The bottom edge
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
      GNode= GRight + GUp + GLeft
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        GNode = GNode + GBoundary
        boundaryNode = mesh.ifield[x, y, lyr.isonode]
        print "Setting boundaryNode be", boundaryNode, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        self.b[boundaryNode]= mesh.field[x, y, lyr.isodeg]
        self.A[nodeThis, nodeThis]= GBoundary
        self.A[nodeThis, boundaryNode]= 1.0
        self.A[boundaryNode, nodeThis]= 1.0
        if self.debug == True:
          self.bs[boundaryNode]= mesh.field[x, y, lyr.isodeg]
          self.As[nodeThis, nodeThis]= GBoundary
          self.As[nodeThis, boundaryNode]= 1.0;
          self.As[boundaryNode, nodeThis]= 1.0;

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

    # The left edge
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
      GNode= GRight + GUp + GDown
      if (mesh.ifield[x, y, lyr.isoflag] == 1):
        GNode = GNode + GBoundary
        boundaryNode = mesh.ifield[x, y, lyr.isonode]
        print "Setting boundaryNode le", boundaryNode, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
        self.b[boundaryNode]= mesh.field[x, y, lyr.isodeg]
        self.A[nodeThis, nodeThis]= GBoundary
        self.A[nodeThis, boundaryNode]= 1.0
        self.A[boundaryNode, nodeThis]= 1.0
        if self.debug == True:
          self.bs[boundaryNode]= mesh.field[x, y, lyr.isodeg]
          self.As[nodeThis, nodeThis]= GBoundary
          self.As[nodeThis, boundaryNode]= 1.0;
          self.As[boundaryNode, nodeThis]= 1.0;

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

    # The top left corner
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
    GNode= GRight + GDown
    if (mesh.ifield[x, y, lyr.isoflag] == 1):
      GNode = GNode + GBoundary
      boundaryNode = mesh.ifield[x, y, lyr.isonode]
      print "Setting boundaryNode tlc", boundaryNode, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
      self.b[boundaryNode]= mesh.field[x, y, lyr.isodeg]
      self.A[nodeThis, nodeThis]= GBoundary
      self.A[nodeThis, boundaryNode]= 1.0
      self.A[boundaryNode, nodeThis]= 1.0
      if self.debug == True:
        self.bs[boundaryNode]= mesh.field[x, y, lyr.isodeg]
        self.As[nodeThis, nodeThis]= GBoundary
        self.As[nodeThis, boundaryNode]= 1.0;
        self.As[boundaryNode, nodeThis]= 1.0;

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

    # The top right corner
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
    GNode= GLeft + GDown
    if (mesh.ifield[x, y, lyr.isoflag] == 1):
      GNode = GNode + GBoundary
      boundaryNode = mesh.ifield[x, y, lyr.isonode]
      print "Setting boundaryNode trc", boundaryNode, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
      self.b[boundaryNode]= mesh.field[x, y, lyr.isodeg]
      self.A[nodeThis, nodeThis]= GBoundary
      self.A[nodeThis, boundaryNode]= 1.0
      self.A[boundaryNode, nodeThis]= 1.0
      if self.debug == True:
        self.bs[boundaryNode]= mesh.field[x, y, lyr.isodeg]
        self.As[nodeThis, nodeThis]= GBoundary
        self.As[nodeThis, boundaryNode]= 1.0;
        self.As[boundaryNode, nodeThis]= 1.0;

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

    # The bottom right corner
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
    GNode= GUp + GLeft
    if (mesh.ifield[x, y, lyr.isoflag] == 1):
      GNode = GNode + GBoundary
      boundaryNode = mesh.ifield[x, y, lyr.isonode]
      print "Setting boundaryNode brc", boundaryNode, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
      self.b[boundaryNode]= mesh.field[x, y, lyr.isodeg]
      self.A[nodeThis, nodeThis]= GBoundary
      self.A[nodeThis, boundaryNode]= 1.0
      self.A[boundaryNode, nodeThis]= 1.0
      if self.debug == True:
        self.bs[boundaryNode]= mesh.field[x, y, lyr.isodeg]
        self.As[nodeThis, nodeThis]= GBoundary
        self.As[nodeThis, boundaryNode]= 1.0;
        self.As[boundaryNode, nodeThis]= 1.0;

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

    # The bottom left corner
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
    GNode= GRight + GUp
    if (mesh.ifield[x, y, lyr.isoflag] == 1):
      GNode = GNode + GBoundary
      boundaryNode = mesh.ifield[x, y, lyr.isonode]
      print "Setting boundaryNode blc", boundaryNode, " at ",x,",",y,", to temp", mesh.field[x, y, lyr.isodeg]
      self.b[boundaryNode]= mesh.field[x, y, lyr.isodeg]
      self.A[nodeThis, nodeThis]= GBoundary
      self.A[nodeThis, boundaryNode]= 1.0
      self.A[boundaryNode, nodeThis]= 1.0
      if self.debug == True:
        self.bs[boundaryNode]= mesh.field[x, y, lyr.isodeg]
        self.As[nodeThis, nodeThis]= GBoundary
        self.As[nodeThis, boundaryNode]= 1.0;
        self.As[boundaryNode, nodeThis]= 1.0;
      
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

    # b is the RHS, which are current sources for injected heat and voltage sources for 
    #   boundary condition.

    # Add the boundary conditions.
    # Heat sources
    for x in range(0, mesh.width):
      for y in range(0, mesh.height):
        nodeThis= mesh.getNodeAtXY(x, y)
        self.b[nodeThis]= mesh.field[x, y, lyr.heat]
        if self.debug == True:
          self.bs[nodeThis]= mesh.field[x, y, lyr.heat]

  def solveMatrix(self, lyr, mesh, iterations):
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
    dirichletStartNode= temperatureEndNode
    dirichletEndNode= dirichletStartNode + mesh.boundaryDirichletNodeCount(lyr)
    print "deg Start Node= ", temperatureStartNode
    print "deg End Node= ", temperatureEndNode
    print "dirichlet Start Node= ", dirichletStartNode
    print "dirichlet End Node= ", dirichletEndNode
    powerIn = 0
    powerOut = 0
    for n in range(temperatureStartNode, temperatureEndNode):
      powerIn = powerIn + self.bs[n]
    for n in range(dirichletStartNode, dirichletEndNode):
      powerOut = powerOut + self.x[n]
    print "Power In = ", powerIn
    print "Power Out = ", powerOut

    # Debugging output
    if (self.debug == 1):
      np.set_printoptions(threshold='nan', linewidth=10000)
      f= open('result.html', 'w')
      f.write(self.webpage(mesh, lyr))
      f.close()

#
#
#  TODO   Check conservation of energy in solution
#         The matrix does not match Swathmore. The boundaries should create two nodes, not one.
#

  def webpage(self, mesh, lyr):
    matrix= ''
    rhsStr= ''
    xhtml= ''
    col= 0
    cols= ''

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

    # Create web page
    head  = "<title>Matrix output</title>"
    body  = "<h1>Ax = b</h1>"
    body += "<h3>A Matrix</h3>"
    body += "<pre>" + matrix + "</pre>"
    body += "<h3>Vectors</h3>"
    body += "<pre>" + vectors + "</pre>"
    html= "<html><head>" + head + "</head><body>" + body + "</body></html>"

    return html

def Main():
  lyr = Layers()
  monitor = Monitors()
  #  Minimal problem to confirm operation:
  #    mesh = Mesh(5, 5, lyr)
  #  Maximal problem shows steady state in field near zero
  #    mesh = Mesh(1000, 1000, lyr), iterations= 400000 (needs 93965 iterations in 28662 seconds solve time)
  #    real	372m26.483s
  #    user	477m34.471s
  #    sys	1m48.083s
  mesh = Mesh(3, 3, lyr)
  matls = Matls()

  defineproblem(lyr, mesh)
# gsitersolve(lyr, mesh, monitor)
# plotsolution(lyr, mesh)

  solv = Solver(lyr, mesh)
  solv.setDebug(True)
  solv.loadMatrix(lyr, mesh)
  solv.solveMatrix(lyr, mesh, 400000)
# plotsolution(lyr, mesh)

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

Main()

def loadMatrix2(self):
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
    self.A[0, 0] = 1/R1
    # node 1
    self.A[1, 1] = 1/R1 + 1/R2 + 1/R3
    # node 2
    self.A[2, 2] = 1/R3 + 1/R4 + 1/R5
    # node 3
    self.A[3, 3] = 1/R5 + 1/R6
    # Common node impedances
    self.A[0, 1] = -1/R1
    self.A[1, 0] = -1/R1
    self.A[1, 2] = -1/R3
    self.A[2, 1] = -1/R3
    self.A[2, 3] = -1/R5
    self.A[3, 2] = -1/R5
    # Independent voltage source into node 0
    self.A[0, 4] = 1
    self.A[4, 0] = 1

    # b is the RHS, which are current sources for injected heat and voltage sources for 
    #   boundar condition.
    self.b[0] = 0
    self.b[1] = 0
    self.b[2] = 0
    # This is the only term for a 1A current source injected into node 3
    self.b[3] = 1
    # This is the 10V voltage source going into node 0.
    # Current going in to the arrow of this source is in the solution as x[4]
    # In this example, the current flows in the direction of the arrow on the current source,
    # so the solution to the current is negative.
    self.b[4] = 10

#
# This will become a pytrilinos solver
#
def simstep(iter, lyr, mesh, monitor):
  maxdelta= 0;
  mesh.field[:, :, lyr.flux] = 0.0
  for x in range(1, mesh.width-1):
    for y in range(1, mesh.height-1):
      if (mesh.field[x , y, lyr.iso] != 1.0):
        resisl= mesh.field[x - 1, y, lyr.resis]
        resisr= mesh.field[x + 1, y, lyr.resis]
        resisu= mesh.field[x, y - 1, lyr.resis]
        resisd= mesh.field[x, y + 1, lyr.resis]
        tresis= resisl+resisr+resisu+resisd
        degl= mesh.field[x - 1, y, lyr.deg]
        degr= mesh.field[x + 1, y, lyr.deg]
        degu= mesh.field[x, y - 1, lyr.deg]
        degd= mesh.field[x, y + 1, lyr.deg]
        
        if (tresis > 0):
          prevdeg = mesh.field[x, y, lyr.deg]
          powerincell = mesh.field[x, y, lyr.heat]
          monitor.powerin = monitor.powerin + powerincell
          newdeg = (powerincell + ( degl*resisl + degr*resisr + degu*resisu + degd*resisd ))/tresis

          poweroutcell = 0.0
          fluxl= (prevdeg - degl) * resisl
          fluxr= (prevdeg - degr) * resisr
          fluxu= (prevdeg - degu) * resisu
          fluxd= (prevdeg - degd) * resisd

          if (mesh.field[x - 1 , y, lyr.iso] == 1.0):
            poweroutcell = poweroutcell + fluxl
          if (mesh.field[x + 1 , y, lyr.iso] == 1.0):
            poweroutcell = poweroutcell + fluxr
          if (mesh.field[x , y - 1, lyr.iso] == 1.0):
            poweroutcell = poweroutcell + fluxu
          if (mesh.field[x , y + 1, lyr.iso] == 1.0):
            poweroutcell = poweroutcell + fluxd

          mesh.field[x - 1 , y, lyr.flux] += abs(fluxl)
          mesh.field[x + 1 , y, lyr.flux] += abs(fluxr)
          mesh.field[x, y - 1, lyr.flux] += abs(fluxu)
          mesh.field[x, y + 1, lyr.flux] += abs(fluxd)
          
          mesh.field[x, y, lyr.deg]= newdeg;

          if (maxdelta < abs(prevdeg - newdeg)):
            maxdelta = abs(prevdeg - newdeg)
          if (monitor.maxtemp < newdeg):
            monitor.maxtemp = newdeg

          monitor.powerout = monitor.powerout + poweroutcell
  return maxdelta

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
