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
    self.mesh = Mesh2D.Mesh(self.config['mesh'], self.lyr, self.matls)   
    return
  
  def solveModel(self):
    self.solv = Solver2D.Solver(self.config['solvers'], self.lyr, self.mesh)
    self.solv.solveFlags(self.config['solverFlags'])
    self.solv.solve(self.config['solverDebug'], self.lyr, self.mesh, self.matls)    
    return  
    
  def loadView(self):
    self.plots= InteractivePlot.InteractivePlot(self.config, self.solv, self.lyr, self.mesh)
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
  