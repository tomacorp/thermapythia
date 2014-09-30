import numpy as np
class Mesh3D:
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
  that can be integrated later. The first passes just loops through each
  simulation input to find the simulation volume. Then the dimensions
  of the bricks are calculated, and the looped through, etc. Do things
  like load material properties that are actually used and count bricks.
  Eventually the passes yield a simulation matrix.
  
  Like the 2D mesher, there is not an array of bricks with attributes.
  Instead, there are arrays of attributes that apply to the bricks that the
  array indexes. In 2D, this is a double subscripted array to make X and Y
  easier to deal with. In 3D, might just go to a single brick instance
  number and get X, Y lookup another way. This would save space because
  the empty space in the 2D array would not require storage.
  
  Each square has a X width.
  Each square has a Y height.
  Each layer has a Z thickness.
  
  In normal display, positive X points right, positive Y points down.
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
    A three dimensional array row(xSize,ySize,zSize)= Rn matrix row.
    A special value -1 of row(xSize,ySize,zSize) used as a flag to indicate that there
       is not a matrix row corresponding to the xN, yN, zN location.
    The X, Y, Z coordinates are rarely used, instead the indexes of the xN, yN, zN
    arrays are used to refer to a brick.
  This is used for slicing space, and relating mechanical input and output to the bricks.
  
  The thermal resistance of a brick can be anisotropic. There are different
  numbers for thermal resistance in the X, Y, and Z directions.
  Each face of each brick is made of a uniform material and is at constant temperature.
  
  The brick does not know its own shape. It only knows its centroid.
  An adjacency list does not know its shape. It only knows about pairs of bricks.
  
  An adjacency (neighbor) list:
    Has nAdj neighbors, nAdj > 0
    Bricks that would otherwise have nAdj == 0 are not stored. The 
      mesh.rowrow(xN,yN,zN) value would be marked with -1
    The node number of each brick neighbor is stored in a list.
    If the adjacency list uses relative neighbor indexes, the values
      can be cached, and the amount of adjacency data greatly reduced.
      This is probably the Stencil concept.

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
  
  The boundary heat source has:
    An index heatPinN for the heatBoundary that the heat is coming from.
    An index heatBoundN for the port that the heat is going to.
    (s) A spice string sBound for the name of the boundary
    A current, which is the Norton equivalent current of the boundary temperature.
    A resistor, which is the Norton equivalent thermal resistance of the boundary.
    
  A heatBoundary has
    An index boundN for the port that the heat is going to.
    A name for the boundary nameBound
  
  A heatPin has
    An index heatPinN for the pin that the heat is coming from.
      

      
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