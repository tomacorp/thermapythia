#!/Users/toma/python278i/bin/python
# Tom Anderson
# Thermal simulation prototype
# Sun Jul 13 22:30:26 PDT 2014
#
# Thermonous pertains to stimulation by heat.
# The literal ancient Greek is hot minded.
#
# Thermonice is like spice. Thermospice.

# Thermapythia  Pythia is the oracle of Delphi. 

#   Therma is feminine, Thermos masculine, thermon nueter
#
# TODO:  
#        Make the spice netlist generation use a string buffer and a file.
#        Create test harness for sweeps of problem size.
#        Hook up HDF5 files.
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
import SimControl
import Profiler

def Main(sim):
  sim.loadModel()
  sim.solveModel()
  sim.loadView()
  sim.loadController()
  sim.launchController()   

# Program entry is here:
sim= SimControl.SimControl()

if sim.config['showProfile'] == 0:
  Main(sim) 
else:
  cProfile.run('Main(sim)', 'restats')
  prof= Profiler.Profiler(sim.config)

# Times without printing much.
# Printing overhead is probably about 10% in this case.
# 10000 iterations
# 100X100 12sec
# 200x200 69sec
# 300x300 154sec

# 1000 iterations
# 200x200 14secvias
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
# The TriSolver class
#   Loads the and calls the Trilinos solvers.
# The SpSolver class
#   Loads the and calls the Spice solver.
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
