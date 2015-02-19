from PIL import Image, ImageDraw
import numpy as np
class Mesh:

  """
  Mesh: Square mesher class for thermal analysis.
  
  The mesher takes a number of squares in the x and y direction and creates
  a square mesh from it.
  
  Creates a bidirectional mapping from the integer X,Y 2D space to the 1D node list
  that is used for solving the sparse matrix.
  
  This uses a two-pass approach. The first pass counts the number of nodes
  needed to describe the problem so that memory can be allocated in advance. The second
  pass loads the mesh data structure with the problem. Then the matrix is solved, and
  the solution data is loaded into the output, which could be the mesh, or could be
  a new data structure.
  
  TODO: Stackup editor for web.
  Styles:
    Altium - good drawing, alternating left/right labels, 3D look. Shows embedding.
    Hyperlynx - to scale, cross section, distinctive colors. Shows embedding.
    Polar - design tool for stackups, looks like Altium. Doesn't show embedding.
    Whatever - http://3.bp.blogspot.com/-G71R0kDY0Jk/T2t8rIId46I/AAAAAAAAAls/wlLCATtc8Js/s1600/index2.png
    Cadence - http://community.cadence.com/cadence_technology_forums/f/27/t/22556
    
    Using IPC-2581 with Altium to do stackup editing:
      http://bethesignal.com/wp/wp-content/uploads/2014/01/ECEN5224_Lecture-02_2014-01-27.pdf
    
    SI Lecture - http://bethesignal.com/wp/wp-content/uploads/2014/01/ECEN5224_Lecture-02_2014-01-27.pdf
    
    File format for stackup could be XML from IPC-2581B standard
    
    
  
  """
  
  # In the 3D case, there will be an offset into the big matrix for each layer.
  # There will be an offset into the layer for each occupied boxel X,Y.
  # Referencing a cell above is done by calculating the layer above, getting
  # the offset for the layer, checking to see that the boxel is occupied,
  # then getting the layer-relative offset for the occupied X,Y, and adding it to the layer
  # offset.
  #
  # The layer-relative offsets for a given bitmap input can be computed in parallel.
  # They can be named or labelled with the checksum of the bitmap and cached.
  # The offsets can be stored in a matrix market format (probably) or perhaps spatial sqlite?
  # When the layer calculations are complete, the offsets can be calculated, then
  # they can be brought together pairwise for parallel calculation of the
  # coupling terms between the pairs.
  #

  def __init__(self, config, lyr, matls):
    self.nodeCount = 0
    # Field name dictionary to map self.spicenodenum layer to string values
    # The key is the spicenodename and the value is the spicenodenum.
    self.spiceNodeName = {}
    # Dictionary that maps a node name string to the X and Y coordinates in the mesh.
    self.spiceNodeXName = {}
    self.spiceNodeYName = {}
    # Array where the index is the spicenodenum and the values are the x and y of in the mesh.
    # This allows a sequence of ordered nodes in the spice raw file output to be loaded directly back into
    # a layer in the mesh. Nodes start at 1. The first variable is time.
    self.spiceNodeX = []
    self.spiceNodeY = []
    
    self.nodeX= []
    self.nodeY= []
    
    self.defineProblem(config, lyr, matls)
    self.mapMeshToSolutionMatrix(lyr)
    # TODO: Doesn't make sense that the mesh doesn't have a copy of all of lyr.
    # Refactor it out of other calls.
    self.lyr= lyr
    
  def setMeshSize(self, w, h, lyr, matls):
    """
    __init__(Mesh self, int w, int h, Layers lyr, Matls matls)
    Create a square mesh of size w by h.
    The mesh data structure is in self.field, which holds double precision numbers,
    and self.ifield, which holds integers.
    """    
    self.width = w
    self.height = h
    self.field = np.zeros((self.width, self.height, lyr.numdoublelayers), dtype = 'double')
    self.ifield = np.zeros((self.width, self.height, lyr.numintlayers), dtype = 'int')
    self.xr, self.yr= np.mgrid[0:self.width+1, 0:self.height+1]
    
  def solveTemperatureNodeCount(self):
    """ 
    solveTemperatureNodeCount(Mesh self)
    Returns the count of cells in the square mesh.
    """
    # The node count is one more than the maximum index.
    return self.nodeCount

  # Return -1 for hole locations or out-of-bounds.
  def getNodeAtXY(self, x, y):
    """
    getNodeAtXY(Mesh self, int x, int y)
    Given an integer x and y argument, find the corresponding node number
    """
    if (x < 0 or y < 0 or x >= self.width or y >= self.height):
      return -1
    if (self.ifield[x, y, self.lyr.holeflag] == 1):
      return -1
    return self.ifield[x, y, self.lyr.holeflag]

  def mapMeshToSolutionMatrix(self, lyr):
    """
    mapMeshToSolutionMatrix(Mesh self, Layers lyr)
    Based on the mesh, find the number of the different types of nodes
    that will be in the matrix A. These numbers need to be known in
    advance of constructing the matrix.
    The input is the width and height of the mesh.
    """
    # Problem must be at least 1 cell by 1 cell.
    if self.width <= 0:
      print "Error: Width:" + str(self.width)
    if self.height <= 0:
      print "Error: Height:" + str(self.height)      
    self.nodeCount= 0;
    for xn in range(0,self.width):
      for yn in range(0, self.height): 
        if (self.ifield[xn, yn, lyr.holeflag] >= 0):
          self.ifield[xn, yn, lyr.holeflag]= self.nodeCount
          self.nodeCount += 1
    self.nodeXn = np.zeros(self.nodeCount, dtype = 'int')
    self.nodeYn = np.zeros(self.nodeCount, dtype = 'int')
    for xn in range(0,self.width):
      for yn in range(0, self.height):
        nodeThis= self.ifield[xn, yn, lyr.holeflag]
        if (nodeThis >= 0):
          self.nodeXn[nodeThis]= xn
          self.nodeYn[nodeThis]= yn   
    # self.nodeCount = self.getNodeAtXY(self.width - 1, self.height - 1) + 1
    print "Total number of independent nodes= ", self.nodeCount
    
  def nodeLocation(self, node):
    if node < 0 or node >= self.nodeCount:
      print "Node " + str(node) + " lookup is out-of-bounds from 0 to " + self.nodeCount
    return (self.nodeXn[node], self.nodeYn[node])
  
  def getNodeAtXY(self, x, y):
    if x < 0 or x >= self.width or y < 0 or y >= self.height:
      return -1
    return self.ifield[x, y, self.lyr.holeflag]
    
  # This can scale by using a PNG input instead of code
  def defineScalableProblem(self, lyr, matls, x, y):
    """
    defineScalableProblem(Layer lyr, Mesh mesh, Matls matls, int xsize, int ysize)
    Create a sample test problem for thermal analysis that can scale
    to a wide variety of sizes.
    It initializes the mesh based on fractions of the size of the mesh.
    The conductivities in the problem are based on the material properties
    in the matls object.
    """
    self.setMeshSize(x, y, lyr, matls)
    self.field[:, :, lyr.resis] = matls.fr4ResistancePerSquare
    
    # Heat source
    hsx= 0.5
    hsy= 0.5
    hswidth= 0.25
    hsheight= 0.25
    heat= 10.0
    srcl= round(self.width*(hsx-hswidth*0.5))
    srcr= round(self.width*(hsx+hswidth*0.5))
    srct= round(self.height*(hsy-hsheight*0.5))
    srcb= round(self.height*(hsy+hsheight*0.5))
    numHeatCells= (srcr - srcl)*(srcb-srct)
    heatPerCell= heat/numHeatCells
    print "Heat per cell = ", heatPerCell
    self.field[srcl:srcr, srct:srcb, lyr.heat] = heatPerCell
    self.field[srcl:srcr, srct:srcb, lyr.resis] = matls.copperResistancePerSquare
    
    # Boundary conditions
    self.field[0, 0:self.height, lyr.isodeg] = 25.0
    self.field[self.width-1, 0:self.height, lyr.isodeg] = 25.0
    self.field[0:self.width, 0, lyr.isodeg] = 25.0
    self.field[0:self.width, self.height-1, lyr.isodeg] = 25.0
    self.ifield[0, 0:self.height, lyr.isoflag] = 1
    self.ifield[self.width-1, 0:self.height, lyr.isoflag] = 1
    self.ifield[0:self.width, 0, lyr.isoflag] = 1
    self.ifield[0:self.width, self.height-1, lyr.isoflag] = 1
    
    # Thermal conductors
    condwidth= 0.05
    cond1l= round(self.width*hsx - self.width*condwidth*0.5)
    cond1r= round(self.width*hsx + self.width*condwidth*0.5)
    cond1t= round(self.height*hsy - self.height*condwidth*0.5)
    cond1b= round(self.height*hsy + self.height*condwidth*0.5)
    self.field[0:self.width, cond1t:cond1b, lyr.resis] = matls.copperResistancePerSquare
    self.field[cond1l:cond1r, 0:self.height, lyr.resis] = matls.copperResistancePerSquare
    
    # Holes
    self.ifield[1, 1, lyr.holeflag]= -1
    self.ifield[1, 1, lyr.isoflag]= 0
    self.field[1, 1, lyr.heat]= 0.0
  
  def definePNGProblem(self, fn, lyr, matls):
    """
    Read a PNG file and load the data structure
    """
    heatPerCell= 48e-6
    pngproblem = Image.open(fn, mode='r')
    xysize= pngproblem.size
    width= xysize[0]
    height= xysize[1]
    print "Width: " + str(width) + " Height: " + str(height)
  
    self.setMeshSize(width, height, lyr, matls)
    self.field[:, :, lyr.isodeg] = 25.0
    self.field[:, :, lyr.resis] = matls.fr4ResistancePerSquare
  
    pix = pngproblem.load()
    copperCellCount=0
    heatCellCount=0
    isoCellCount=0
    fr4CellCount=0
    holeCellCount=0
    for xn in range(0,width):
      for tyn in range(0, height):
        # Graphing package has +y up, png has it down
        yn= height - 1 - tyn
        if pix[xn,yn][0] == 255 and pix[xn,yn][1] == 0 and pix[xn,yn][2]== 0: 
          self.field[xn, tyn, lyr.resis] = matls.copperResistancePerSquare
          self.field[xn, tyn, lyr.heat] = heatPerCell
          copperCellCount += 1
          heatCellCount += 1
        elif pix[xn,yn][0] == 0 and pix[xn,yn][1] == 255 and pix[xn,yn][2]== 0:
          self.field[xn, tyn, lyr.resis] = matls.copperResistancePerSquare
          copperCellCount += 1
        elif pix[xn,yn][0] == 0 and pix[xn,yn][1] == 0 and pix[xn,yn][2]== 255:
          self.ifield[xn, tyn, lyr.isoflag] = 1
          self.field[xn, tyn, lyr.resis] = matls.copperResistancePerSquare
          self.field[xn, tyn, lyr.isodeg] = 25.0
          isoCellCount += 1
          copperCellCount += 1
        elif pix[xn,yn][0] == 255 and pix[xn,yn][1] == 255 and pix[xn,yn][2]== 0:
          self.field[xn, tyn, lyr.resis] = matls.fr4ResistancePerSquare
          fr4CellCount += 1
        elif pix[xn,yn][0] == 255 and pix[xn,yn][1] == 255 and pix[xn,yn][2]== 255:
          self.ifield[xn, tyn, lyr.holeflag] = -1
          holeCellCount += 1
        else:
          print 'Unrecognized color: (' + str(pix[xn,yn][0]) + "," + str(pix[xn,yn][1]) + "," + str(pix[xn,yn][2]) + ') at: ' + str(xn) + ", " + str(yn)
          
    print "Copper px: " + str(copperCellCount) + " Heat px: " + str(heatCellCount) + " Iso px: " + str(isoCellCount)
    print "FR4 px: " + str(fr4CellCount) + " Hole px: " + str(holeCellCount)
    
  def defineTinyProblem(self, lyr, matls):
    """ 
    defineTinyProblem(Layer lyr, Mesh mesh, Matls matls)
    Create a tiny test problem.
    """
    self.setMeshSize(3, 3, lyr, matls)
    self.field[:, :, lyr.resis] = matls.fr4ResistancePerSquare
    
    self.ifield[0:3, 0, lyr.isoflag] = 1
    self.field[1, 1, lyr.heat]    = 2.0
    print "Mesh: " + str(self)
    
  def defineProblem(self, config, lyr, matls):
    foundProblem= False
    for problem in config:
      if problem['active'] == 1:
        if (problem['type'] == "tiny"):
          self.defineTinyProblem(lyr, matls)
          foundProblem= True
        if (problem['type'] == "png"):
          self.definePNGProblem(problem['inputFile'], lyr, matls)
          foundProblem= True
        if (problem['type'] == "scalable"):
          self.defineScalableProblem(lyr, matls, problem['xsize'], problem['ysize'])
          foundProblem= True
    if foundProblem == False:
      print "Problem not specified or not found in configuration"
          