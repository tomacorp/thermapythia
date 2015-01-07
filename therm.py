#!/Users/toma/python278i/bin/python
# Tom Anderson
# Thermal simulation prototype
# Sun Jul 13 22:30:26 PDT 2014
#
# Thermonous pertains to stimulation by heat.
# The literal ancient Greek is hot minded.
#
# Thermonice is like spice. Thermospice.
#
# TODO:  
#        Make the spice netlist generation use a string buffer and a file.
#        Create test harness for sweeps of problem size.
#        Hook up PNG files.
#        Hook up HDF5 files
#
#        Create ASCII files for layers, materials, and mesh parameters
#        Create master simulation file to include problem description, solvers,
#          solver parameters, geometry parameters, input png image file names, etc.
#        Create master simulation output file to include matrix descriptions,
#          spice netlist, output file names, output png images, etc.
#
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
import StringIO
import cProfile
import Layers
import Matls
import Mesh2D
import Solver2D
import ParseSimFile
import interactivePlot
import yaml
import Http

def Main(simConfig):
  lyr = Layers.Layers(simConfig['simulation_layers'])
  matls = Matls.Matls(simConfig['layer_matl'])
  # TODO: Consider refactoring to split mesh into geometry and mesh
  mesh = Mesh2D.Mesh(simConfig['mesh'], lyr, matls)
  solv = Solver2D.Solver(simConfig['solvers'], lyr, mesh)
  solv.solveFlags(simConfig['solverFlags'])
  solv.solve(simConfig['solverDebug'], lyr, mesh, matls) 
  plots= interactivePlot.interactivePlot(simConfig['outputs'], solv, lyr, mesh)
  
  
  # TODO: Generate web pages for static (not interactive) plots
  http = Http.Http(simConfig)  
  # This works from the command line to open a page:
  # open "http://localhost:8880/htmlfile/diri_AxRHS.html"


simConfigFile= ParseSimFile.ParseSimFile()
simConfigJSON= simConfigFile.exampleJSON()
simConfig= yaml.load(simConfigJSON)

if simConfig['showProfile'] == 1:
  cProfile.run('Main(simConfig)', 'restats')
  
  # TODO: Move this code into Profile.py and 
  # make methods for extracting the data for use in reports.
  # High level data such as overall time and detailed function data.
  
  stream = StringIO.StringIO()
  stats = pstats.Stats('restats', stream=stream)
  stats.sort_stats('cumulative').dump_stats('restats')
  stats.print_stats()
  profileFile = open(simConfig['profileFilename'], "w")
  profileFile.write(stream.getvalue())
  profileFile.close()

else:
  Main(simConfig)

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
