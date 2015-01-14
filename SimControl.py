import yaml
import argparse
import sys
import Layers
import Matls
import Mesh2D
import Solver2D
import InteractivePlot
import Http

class SimControl:
  
  
  """
  TODO:
  Question: are things clean enough that NORTON and HOLES can be implemented
  A/B with conditionals? For example, diff two otherwise identical 
  config json files.
  Refactorings: 
    NORTON boundary conditions.
    HOLES.
    Class cleanup.
    3D.
  """
  
  """
  TODO:
  Need clean structure of the JSON with:
    Simulation controls: HTTP server, settings
    Input data: geometry, materials, layers, components, power inputs, boundary conditions
    Intermediate data: mesh, solver, matrix in, matrix out
    Output raw data: HDF5, Spice, and PNG specifications, basically
    Visualization: What to create, where to put it
  Need a higher level for reports, which can have a collection of simulations.
  These can show design tradeoffs such as what-if thicker copper or larger vias.
  They can also show benchmarks from a test set of simulations.
  """
  
  """
  TODO:
  There needs to be a top level directory for program outputs.
  Directories, such as for PNG files, go beneath this level.
  Directories that do not exist need to be created.
  These names should all go in the JSON config file.
  """
  
  def __init__(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('cfg', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    args = parser.parse_args()
    # print "Config file is: " + str(args.cfg)   
    self.configJSON= args.cfg.read()
    self.config= yaml.load(self.configJSON) 
    
  def loadModel(self):
    self.lyr = Layers.Layers(self.config['simulation_layers'])
    self.matls = Matls.Matls(self.config['layer_matl'])
    # TODO: Consider refactoring to split mesh into geometry and mesh
    # DELAY REFACTORING: Implement holes first.
    self.mesh = Mesh2D.Mesh(self.config['mesh'], self.lyr, self.matls)   
    return
  
  def solveModel(self):
    self.solv = Solver2D.Solver(self.config['solver'], self.mesh.nodeCount)
    self.solv.solve(self.lyr, self.mesh, self.matls)    
    return
    
  def loadView(self):
    self.plots= InteractivePlot.InteractivePlot(self.config, self.solv, self.lyr, self.mesh)
    self.plots.plotAll()
    return
  
  def loadController(self):
    self.http = Http.Http(self.config)
    self.http.openWebBrowser(1)
    return  
    
  def launchController(self):
    # This does not return until the web server is stopped.
    self.http.startServer()
    return
    
def Main():
  print "Loaded class SimControl - OK"
  
if __name__ == '__main__':
  Main()
  