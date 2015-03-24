from PIL import Image, ImageDraw
import yaml
import numpy as np
class Mesh:

  """
  Mesh: Square mesher class for thermal analysis.
  
  Each entry corresponds to a 2D array with one entry per pixel.
  There are two data types, flags and double.
  
  The mesher takes a number of squares in the x and y direction and creates
  a square mesh from it.
  
  Creates a bidirectional mapping from the integer X,Y 2D space to the 1D node list
  that is used for solving the sparse matrix.
  
  This uses a two-pass approach. The first pass counts the number of nodes
  needed to describe the problem so that memory can be allocated in advance. The second
  pass loads the mesh data structure with the problem. Then the matrix is solved, and
  the solution data is loaded into the output, which could be the mesh, or could be
  a new data structure.
  
  TODO:
  For this test code, especially the 2D test code, need to be able to specify the JSON
  or otherwise initialize Matls, Layers, and Vias without using a JSON file.
  Instead have the JSON or other calls inline.
  
  TODO:
  A nonzero boundary conductivity can be used instead of the flag self._isodeg.
  
  TODO:
  It seems like a good idea to to specify a layer as having a % copper instead of detailed traces,
  and except for holes. Then there is the problem of thermal relief, unattached via relief, etc.
  
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
    
    
  TODO: 3D meshing
    1. Figure out how many layers there will be in the analysis.
    The logical layers have more than one value per design or physical physical layer.

    Input layer PNGs are mapped to boxels.
    The loader first pass just counts to get the layer offsets.
    The loader second pass loads the solver matrix.
    The matrix solver runs.
    The unloader loads the solution back into PNG files, matplotlib, or hdf5.

    Each boxel is in a 2D XY array of boxels.
    These arrays can be shipped to different computers to split up a problem.
      material identifier
      temperature from Spice solver
      temperature from Trilinos solver
      temperature from Numpy solver
      node number
      index into array of X, Y, and Z coordinates
      layer number

    Some physical layers have a
      boundary condition flag
      boundary condition temperature
      boundary condition conductivity
    
    Ultimately there are six types of layers:
                      int/bitfied      float
      input
      intermediate
      output
    The input is fabrication artwork, power inputs, etc.
    Most of the input layers are bitfields, and it is possible to pack them efficiently.
    Need access routines to make packing and unpacking easy.
    The intermediate and output are mostly floats for numeric calculations.
    The output could also be rendered as int/bitfield pictures.
    
    Could use png->hdf5->packed data structures
    
  """
  
  # In the 3D case, there will be an offset into the big matrix for each layer.
  # There will be an offset into the layer for each occupied boxel X,Y.
  # Referencing a cell above is done by calculating the layer above, getting
  # the offset for the layer, checking to see that the boxel is occupied,
  # then getting the layer-relative offset for the occupied X,Y, and adding it to the layer
  # offset.
  #
  # The layer-relative offset-less matrices for a given bitmap input can be computed in parallel.
  # They can be named or labelled with the checksum of the bitmap and cached.
  # The layers, without the offsets, can be stored in a matrix market format (probably) or perhaps spatial sqlite?
  # When the layer calculations are complete, the offsets can be calculated, then
  # they can be brought together pairwise for parallel calculation of the
  # coupling terms between the pairs.
  #

  def __init__(self, fn, lyr, matls):
    
    self.config_js_fn= fn
    
    with open (self.config_js_fn, "r") as jsonHandle:
      jsonContents= jsonHandle.read()
      
    config= yaml.load(jsonContents)
    
    # TODO: This shouldn't be needed but the plot routine uses mesh.config
    self.config= config
    
    self.loadConfig(config)
      
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
    
    self.defineProblem(config['mesh'], lyr, matls)
    self.mapMeshToSolutionMatrix(lyr)
    
    # TODO: Doesn't make sense that the mesh doesn't have a copy of all of lyr.
    # Refactor it out of other calls.
    self.lyr= lyr
    
  def setMeshSize(self, w, h):
    """
    __init__(Mesh self, int w, int h, Matls matls)
    Create a square mesh of size w by h.
    The mesh data structure is in self.field, which holds double precision numbers,
    and self.ifield, which holds integers.
    """    
    self.width = w
    self.height = h
    self.field = np.zeros((self.width, self.height, self.numdoublelayers), dtype = 'double')
    self.ifield = np.zeros((self.width, self.height, self.numintlayers), dtype = 'int')
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
    if (self.ifield[x, y, self._holeflag] == 1):
      return -1
    return self.ifield[x, y, self._holeflag]

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
        if (self.ifield[xn, yn, self._holeflag] >= 0):
          self.ifield[xn, yn, self._holeflag]= self.nodeCount
          self.nodeCount += 1
    self.nodeXn = np.zeros(self.nodeCount, dtype = 'int')
    self.nodeYn = np.zeros(self.nodeCount, dtype = 'int')
    for xn in range(0,self.width):
      for yn in range(0, self.height):
        nodeThis= self.ifield[xn, yn, self._holeflag]
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
    return self.ifield[x, y, self._holeflag]
    
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
    #
    # TODO: Physical layers get used properly just below here.
    
    # For the other uses,
    # need to split use of lyr into the mesh layers, which are things like self._resis,
    # and these layers should be initialized and managed in the mesh object here,
    # not in the Layers class, where it is magically created now by messing with
    # the object hash. Also there is the counting of the layers that happens there.
    #
    # The easy way to do this is to move the magic from Layers.py to this class,
    # and change self.lyr.magic to self.magic, or in the cases where lyr is passed
    # as a variable, change lyr.magic to self.magic.
    # 
    fr4cond= matls.getProp('Core', 'conductivityXX')
    fr4thick= lyr.getProp('core1', 'thickness')
    fr4condUnits= matls.getUnits('conductivityXX')
    fr4thickUnits= lyr.getUnits('thickness')
    print "FR-4 Cond: " + str(fr4cond) + str(fr4condUnits)
    print "FR-4 Thickness: " + str(fr4thick) + str(fr4thickUnits)
    fr4res= 1.0/(fr4cond * fr4thick)
    print "FR-4 Resistance per square: " + str(fr4res)  
    
    cucond= matls.getProp('Cu', 'conductivity')
    cuthick= lyr.getProp('topside_cu', 'thickness')
    cucondUnits= matls.getUnits('conductivity')
    cuthickUnits= lyr.getUnits('thickness')
    print "Cu Cond: " + str(cucond) + str(cucondUnits)
    print "Cu Thickness: " + str(cuthick) + str(cuthickUnits)
    cures= 1.0/(cucond * cuthick)
    print "Cu Resistance per square: " + str(cures)      
    
    self.setMeshSize(x, y)
    self.field[:, :, self._resis] = fr4res
    
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
    self.field[srcl:srcr, srct:srcb, self._heat] = heatPerCell
    self.field[srcl:srcr, srct:srcb, self._resis] = cures
    
    # Boundary conditions
    self.field[0, 0:self.height, self._isodeg] = 25.0
    self.field[self.width-1, 0:self.height, self._isodeg] = 25.0
    self.field[0:self.width, 0, self._isodeg] = 25.0
    self.field[0:self.width, self.height-1, self._isodeg] = 25.0
    
    self.ifield[0, 0:self.height, self._isoflag] = 1
    self.ifield[self.width-1, 0:self.height, self._isoflag] = 1
    self.ifield[0:self.width, 0, self._isoflag] = 1
    self.ifield[0:self.width, self.height-1, self._isoflag] = 1
    
    self.field[0, 0:self.height, self._boundCond] = cucond
    self.field[self.width-1, 0:self.height, self._boundCond] = cucond
    self.field[0:self.width, 0, self._boundCond] = cucond
    self.field[0:self.width, self.height-1, self._boundCond] = cucond    
    
    # Thermal conductors
    condwidth= 0.05
    cond1l= round(self.width*hsx - self.width*condwidth*0.5)
    cond1r= round(self.width*hsx + self.width*condwidth*0.5)
    cond1t= round(self.height*hsy - self.height*condwidth*0.5)
    cond1b= round(self.height*hsy + self.height*condwidth*0.5)
    self.field[0:self.width, cond1t:cond1b, self._resis] = cures
    self.field[cond1l:cond1r, 0:self.height, self._resis] = cures
    
    # Holes
    self.ifield[1, 1, self._holeflag]= -1
    self.ifield[1, 1, self._isoflag]= 0
    self.field[1, 1, self._heat]= 0.0
  
  def definePNGProblem(self, fn, lyr, matls):
    """
    Read a PNG file and load the data structure
    pix from Image module is getting mapped into field and ifield 2D layer structs.

    """
    heatPerCell= 48e-6
    pngproblem = Image.open(fn, mode='r')
    xysize= pngproblem.size
    width= xysize[0]
    height= xysize[1]
    print "Width: " + str(width) + " Height: " + str(height)
    
    fr4cond= matls.getProp('Core', 'conductivityXX')
    fr4thick= lyr.getProp('core1', 'thickness')
    fr4condUnits= matls.getUnits('conductivityXX')
    fr4thickUnits= lyr.getUnits('thickness')
    print "FR-4 Cond: " + str(fr4cond) + str(fr4condUnits)
    print "FR-4 Thickness: " + str(fr4thick) + str(fr4thickUnits)
    fr4res= 1.0/(fr4cond * fr4thick)
    print "FR-4 Resistance per square: " + str(fr4res)
    
    cucond= matls.getProp('Cu', 'conductivity')
    cuthick= lyr.getProp('topside_cu', 'thickness')
    cucondUnits= matls.getUnits('conductivity')
    cuthickUnits= lyr.getUnits('thickness')
    print "Cu Cond: " + str(cucond) + str(cucondUnits)
    print "Cu Thickness: " + str(cuthick) + str(cuthickUnits)
    cures= 1.0/(cucond * cuthick)
    print "Cu Resistance per square: " + str(cures)    
      
    self.setMeshSize(width, height)
    self.field[:, :, self._isodeg] = 25.0
    self.field[:, :, self._resis] = fr4res
    self.field[:, :, self._boundCond] = 0.0
      
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
          self.field[xn, tyn, self._resis] = cures
          self.field[xn, tyn, self._heat] = heatPerCell
          copperCellCount += 1
          heatCellCount += 1
        elif pix[xn,yn][0] == 0 and pix[xn,yn][1] == 255 and pix[xn,yn][2]== 0:
          self.field[xn, tyn, self._resis] = cures
          copperCellCount += 1
        elif pix[xn,yn][0] == 0 and pix[xn,yn][1] == 0 and pix[xn,yn][2]== 255:
          self.ifield[xn, tyn, self._isoflag] = 1
          self.field[xn, tyn, self._resis] = cures
          self.field[xn, tyn, self._isodeg] = 25.0
          self.field[xn, tyn, self._boundCond] = cucond
          isoCellCount += 1
          copperCellCount += 1
        elif pix[xn,yn][0] == 255 and pix[xn,yn][1] == 255 and pix[xn,yn][2]== 0:
          self.field[xn, tyn, self._resis] = fr4res
          fr4CellCount += 1
        elif pix[xn,yn][0] == 255 and pix[xn,yn][1] == 255 and pix[xn,yn][2]== 255:
          self.ifield[xn, tyn, self._holeflag] = -1
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
    self.setMeshSize(3, 3)
    self.field[:, :, self._resis] = 400.0
    
    self.ifield[0:3, 0, self._isoflag] = 1
    self.field[0:3, 0, self._boundCond] = 400.0
    self.field[1, 1, self._heat]    = 2.0
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
      
  def loadConfig(self, config):
    self.numdoublelayers= 0
    self.numintlayers= 0
    for lyr in config['simulation_layers']:
      self.__dict__['_' + lyr['name']]= lyr['index']
      if (lyr['type'] == 'double'):
        self.numdoublelayers = self.numdoublelayers + 1
      if (lyr['type'] == 'int'):
        self.numintlayers = self.numintlayers + 1 
    print "Number of double layers = " + str(self.numdoublelayers)
    print "Number of int layers = " + str(self.numintlayers)
          