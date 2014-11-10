import numpy as np
class Mesh3D:
  
  def __init__(self):
    self.width= 1.0
    self.height= 1.0
    self.thickness= .059
    self.layers= 2
    
  def addLayer(self, layerName, fileName):
    


    """
  Mesh3D: Square multilayer mesher class for multilayer planar thermal analysis
  
  Don't forget to order layer descriptions from top down.
  
  Input: 
    Layer Bitmaps
    Materials
    Stackup
  Output: 
    3D mesh of bricks with square bases.
    Spatial index
  
  Meshing is developed in passes with small amounts of functionality
  that can be integrated later. The first pass just loops through each
  simulation input to find the bounding simulation volume. Then the dimensions
  of the bricks are calculated, and then looped through, etc. Do things
  like load material properties that are actually used and count bricks.
  Eventually the passes result in a loaded simulation matrix.
  
  Like the 2D mesher, there is not an array of bricks with attributes.
  Instead, there are arrays of attributes that apply to the bricks that the
  array indexes. In 2D, this is a double subscripted array to make X and Y
  easier to deal with. In 3D, might just go to a single brick instance
  number and get X, Y lookup another way. This would save space because
  the empty space in the 2D array would not require storage.
  
  Each square has a X width.
  Each square has a Y height.
  Each layer has a Z thickness.
  
  In normal PC board layout display, positive X points right, positive Y points down.
  Coordinates follow the right-hand rule, so positive Z goes into the page.
  When the coordinates are rotated to see the stackup, positive z points down,
  x points right, and positive y comes out of the page.
  
  While meshing, there may be thermal islands detected. These would be an
  additional collection of connected cubes that are isolated from the first
  collection, with no joining faces. The additional islands are discarded
  and a log message warning is issued. There needs to be a starting point
  that is inside the first set of connected cubes. A good starting point
  would be a boundary condition, since there must be at least one boundary
  condition cube anyway. Except these are really decorations.
  
  The mesh has a spatial index:
    An ordered array of all possible X coordinates of brick centroids
    An ordered array of all possible Y coordinates of brick centroids
    An ordered array of all possible Z coordinates of brick centroids
    A bounding cube for all the bricks
    The number of xN, yN, and zN array entries
    A three dimensional array row(xSize,ySize,zSize)= Rn matrix row
    An array of brick locations indexed by matrix row loc(xN, yN, zN)= brick number
    A special value -1 of row(xSize,ySize,zSize) used as a flag to indicate that there
       is not a matrix row corresponding to the xN, yN, zN location.
    The X, Y, Z coordinates are rarely used, instead the indexes of the xN, yN, zN
      arrays are used to refer to a brick's location.
    The xN, yN, and zN are often not used. Instead, most data is indexed by the row.
  This is used for slicing space, and relating mechanical input and output to the bricks.
  
  The thermal resistance of a brick can be anisotropic. There are different
  numbers for thermal resistance in the X, Y, and Z directions.
  Each face of each brick is made of a uniform material and is at constant temperature.
  
  The brick does not know its own shape. It only knows its centroid.
  An adjacency list does not know its shape. It only knows about pairs of bricks.
  The challenge with adjacency is to make it efficient to loop through the matrix
  rows and find the adjacency relationships to the other rows.
  """
  
  
  """  
  Adjacency:
    A row offset to find six neighbor faces. There should only be need to store 3, 
      because the data would be rendundant with the same pair of nodes in the
      opposite order. Since the order is arbitrary, it could be stored as a sorted pair
      of rows. Since the matrix is Hermitian, never really need to sort it, because
      that part of the matrix doesn't need to be loaded anyway.
    If a brick needs to look up its neighbor, it will need to do so through the 
      spatial relationship, not the adjacency data structure.
    3D has six thermal resistances, (2D has 4), which correspond to the anisotropic thermal 
    resistances of the pair of mesh elements.
    Adjacency object is really three node/row offsets and three conductances, 
      and zero to two current sources per brick. It has a pair of materials indexes for
      each of the three conductances. It has an index.
    It has a method to create a description string from a node number
      which describes everything known about the adjacency.
    An array adjArray has the adjacency objects in it, one for each type of adjacency.
      Each brick/node/row stores the index to the adjArray for the brick's adjacencies.
    A method takes the pair of materials at the node offsets and computes the
      anisotropic conductances.
  
  An adjacency (neighbor) list:
    Has nAdj neighbors, nAdj > 0
    Bricks that would otherwise have nAdj == 0 are not stored. The 
      mesh.row(xN,yN,zN) value would be marked with -1
    The node number of each brick neighbor is stored in a list.
    If the adjacency list uses relative neighbor indexes, the values
      can be cached in an array, and the amount of adjacency data greatly reduced.
      This is probably the Stencil concept. The ability to have a small cache
      depends on the uniformity of the mesh, so it is good that it is
      meshing both space and material, and not trying to save space by
      only meshing material, for example.
    The thermal conductances can be stored in the adjacency list.
    The mesher handles the anisotropicity.
    
    An adjacency can be looked up with:
      Xn, Yn, Zn offsets
      Material pairs for the faces. In this case, the direction of the material in
      the anisotropic case is handled as a different material.
    Thermal conductivity is stored in for the adjacency
"""
  
"""  
  A brick has: 
    A uniform but anisotropic material. The material has a material number nMat.
    A spans of one or more layers, and the spanning pair is a pair of layer numbers.
    A temperature that corresponds to the solution of the problem.
    A map to one row of the matrix, and this row is a row number.
    An xN, yN, and zN location, which are indexes to the floating point coordinates 
      of the centroid.
    The same xSize and ySize. 
    zSize, which is based on the spanning layers pair.
    (s) One node in a spice simulation, and the node name is a string sNode
    A index heatN is the index of the heat source for the brick. A special value -1
      indicates that there is no heat source.
    A index boundN is the index of the boundary heat source for the brick.  
      A special value -1 indicates that there is no heat source.
"""

"""    
  The heat source has:
    An index heatN for the port/pin that the heat is coming from.
    (s) A spice string sHeat for the name of the current source.
    A current fHeat, which corresponds to input power into this brick.
    Need to experiment with the heat source. It could be one current
    source that is a supernode that all the cells hook up to, or it
    could be a lot of distributed currents sources with a distribution
    that is the solution to the problem where the heat probably mostly
    flows around the outer surface, because the heat inside would otherwise
    build up in an unrealistic way. On the other hand, if it is a via-in-pad
    layout, the heat can go right down into the via in the center of the pad.

"""
"""
  The boundary heat source has:
    An index heatPinN for the heatBoundary that the heat is coming from.
    An index heatBoundN for the port that the heat is going to.
    (s) A spice string sBound for the name of the boundary
    A current, which is the Norton equivalent current of the boundary temperature.
    A resistor, which is the Norton equivalent thermal resistance of the boundary.
"""
"""    
  A heatBoundary has
    An index boundN for the port that the heat is going to.
    A name for the boundary nameBound
"""
"""  
  A heatPin has
    An index heatPinN for the pin that the heat is coming from.
"""
"""          
  Need lumped models such as for resistors, which there are at least four thermal
  resistances.
      
  A layer has a
    name
    layer artwork bitmap
    thickness
    material
    
  Layer artwork bitmaps have flags that modulate the presence or absence of materials in a layer.
  For example, a layer could alternately have
    hole
    dielectric
    conductor
  And could in addition have
    boundary current source
    heat source
    
  A stackup is needed to relate the materials and layers to the bricks.    
  A stackup has
    A list of layers
      List of materials
  
  There is a layer for current sources, holes, conductors, substrate material.
  Holes can be one or more layers, allowing for blind vias or milling, for example.
  
  (s) Optional fields for when spice is in use.
  """