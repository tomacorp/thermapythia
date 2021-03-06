#!/Users/toma/python278i/bin/python
# Tom Anderson
# Thermal simulation prototype
# Sun Jul 13 22:30:26 PDT 2014
#
# Thermonous pertains to stimulation by heat.
# The literal ancient Greek is hot minded.
# If you need a name for it, "ephippion" is the ancient Greek word for saddle blanket
# and in Latin is "ephippia".  "Ephippos" means on horseback.
# 
#
# TODO:  
#        Make the spice netlist generation use a string buffer and a file.
#        Create test harness for sweeps of problem size.
#        Hook up PNG files.
#        Hook up HDF5 files
#        Create ASCII files for layers, materials, and mesh parameters
#        Make problem 3D
#        Make tests for 2D, put modules into separate files so that code is 
#          shared with 3D.
#        Separate the 2D-specific code in Solver2D.py.
#        Separate the 2D-specific code in Spice2D.py.
#        Create test harnesses for each module
#        Measure xyce memory usage with 
#          http://stackoverflow.com/questions/13607391/subprocess-memory-usage-in-python

# Xyce uses about 7-10 times the memory and takes about 3 times as long as the raw matrix.
# 826M
# 26 seconds to 108 seconds by adding Xyce.

import subprocess, os
import pstats
import cProfile
import numpy as np
import Layers
import Matls
import Mesh2D
import Solver2D
import Spice2D
import MatrixDiagnostic
import interactivePlot

# This can scale by using a PNG input instead of code
def defineScalableProblem(lyr, matls, x, y):
  """
  defineScalableProblem(Layer lyr, Mesh mesh, Matls matls, int xsize, int ysize)
  Create a sample test problem for thermal analysis that can scale
  to a wide variety of sizes.
  It initializes the mesh based on fractions of the size of the mesh.
  The conductivities in the problem are based on the material properties
  in the matls object.
  """
  mesh = Mesh2D.Mesh(x, y, lyr, matls)
  
  # Heat source
  hsx= 0.5
  hsy= 0.5
  hswidth= 0.25
  hsheight= 0.25
  heat= 10.0
  srcl= round(mesh.width*(hsx-hswidth*0.5))
  srcr= round(mesh.width*(hsx+hswidth*0.5))
  srct= round(mesh.height*(hsy-hsheight*0.5))
  srcb= round(mesh.height*(hsy+hsheight*0.5))
  numHeatCells= (srcr - srcl)*(srcb-srct)
  heatPerCell= heat/numHeatCells
  print "Heat per cell = ", heatPerCell
  mesh.field[srcl:srcr, srct:srcb, lyr.heat] = heatPerCell
  mesh.field[srcl:srcr, srct:srcb, lyr.resis] = matls.copperCond
  
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
  return mesh
  
def defineTinyProblem(lyr, matls):
  """ 
  defineTinyProblem(Layer lyr, Mesh mesh, Matls matls)
  Create a tiny test problem.
  """
  mesh = Mesh2D.Mesh(3, 3, lyr, matls)
  
  mesh.ifield[0:3, 0, lyr.isoflag] = 1
  mesh.field[1, 1, lyr.heat]    = 2.0
  print "Mesh: " + str(mesh)
  return mesh


def solveAmesos(solv, mesh, lyr):
  solv.solveMatrixAmesos()
  solv.loadSolutionIntoMesh(lyr, mesh)
  solv.checkEnergyBalance(lyr, mesh)

def solveSpice(spice, mesh, lyr):
  spice.finishSpiceNetlist()
  proc= spice.runSpiceNetlist()
  proc.wait()
  spice.readSpiceRawFile(lyr, mesh)

def Main():
  lyr = Layers.Layers()
  matls = Matls.Matls()
  spice= Spice2D.Spice()
  
  showPlots= False
  useTinyProblem= False

  if useTinyProblem:
    mesh = defineTinyProblem(lyr, matls)
  else:
    mesh = defineScalableProblem(lyr, matls, 5, 5)

  mesh.mapMeshToSolutionMatrix(lyr)

  solv = Solver2D.Solver(lyr, mesh)
  solv.debug             = True
  solv.useSpice          = False
  solv.aztec             = True
  solv.amesos            = False
  solv.eigen             = False  
  
  if (solv.useSpice == True):
    solv.spiceSim= Spice2D.Spice()
  
  solv.initDebug()
  solv.loadMatrix(lyr, mesh, matls, spice)
  
  if (solv.eigen == True):
    print "Solving for eigenvalues"
    solv.solveEigen()
    print "Finished solving for eigenvalues"
  
  if (solv.useSpice == True):
    solveSpice(spice, mesh, lyr)
    
  if (solv.aztec == True):
    solv.solveMatrixAztecOO(400000)
    solv.loadSolutionIntoMesh(lyr, mesh)
    solv.checkEnergyBalance(lyr, mesh) 
    
  if (solv.amesos == True):
    solveAmesos(solv, mesh, lyr)
  
  if (solv.debug == True):
    webpage = MatrixDiagnostic.MatrixDiagnosticWebpage(solv, lyr, mesh)
    webpage.createWebPage()
  
  if (showPlots == True):
    plots= interactivePlot.interactivePlot(lyr, mesh)
    plots.plotTemperature()
    if (solv.useSpice == True):
      plots.plotSpicedeg()
      plots.plotLayerDifference(lyr.spicedeg, lyr.deg)
    plots.show()


showProfile= True
if showProfile == True:
  cProfile.run('Main()', 'restats')
  p = pstats.Stats('restats')
  p.sort_stats('cumulative').print_stats(30)
else:
  Main()

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


# This appears to be the default and it works:
# solver.SetAztecOption(AztecOO.AZ_output, AztecOO.AZ_none)

# Solutions on infinite resistor grids:
# http://www.mathpages.com/home/kmath668/kmath668.htm

# Example slides, interesting python code:
# http://trilinos.org/oldsite/packages/pytrilinos/PyTrilinosTutorial.pdf
