import yaml
import argparse
import sys
import Layers
import Matls
import Vias
import Mesh2D
import Solver2D
import InteractivePlot
import Http
import Html

class SimControl:
  
  
  """
  TODO:
    Class cleanup.
    3D.
  """
  
  """
  ANALYSIS:
    There are different layer types:
      Physical, CAD
      Physical, BOM
      Physical, Simulation
      Simulation, Flag
      Simulation, Integer
      Simulation, Float
    The simulation layers are in Mesh2D.py and are data-driven constructors working from SimControl json configuration.
    The physical CAD layers are described in matls.js, layers.js, and vias.js.
    This description data is loaded in Matls.py, Layers.py, and Vias.py.
    To see them all at once and verify correctness, and HTML table is generated for each one, and is displayed by SimControl.py.
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
    roq/therm/onous/layers/layer1.png
  The main program should launch the controller in a location.
  The controller discovers that it is in an existing design and loads it,
  or it discovers that it is in a new location and initializes it.
  """
  
  def __init__(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('cfg', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    args = parser.parse_args()
    print "Config file is: " + str(args.cfg)   
    self.configJSON= args.cfg.read()
    self.config= yaml.load(self.configJSON)
    
  def loadModel(self):
    self.matls = Matls.Matls(self.config['matls_config'])
    # BOM Layers: Manufacturer's BOM, for example with three layers that stack to make a single core.
    # CAD Layers: Data from CAD source, could also include drills, for example.
    # Physical Layers: PhyLayers: 2D multilayer bitmap representation of the design. This is a solid model.
    # Thermal Simulation Layers: Thermapythia layers: Values used to load the matrix, flags, etc.
    self.lyr = Layers.Layers(self.config['layers_config'])
    self.via = Vias.Vias(self.config['vias_config'])
    self.createWebPage(self.config['webPageFileName'])
    
    # TODO: Consider refactoring to split mesh into geometry and mesh
    self.mesh = Mesh2D.Mesh(self.config['mesh_config'], self.lyr, self.matls)   
    return
  
  def createWebPage(self, webPageFileName):
    # np.set_printoptions(threshold='nan', linewidth=10000)
    f= open(webPageFileName, 'w')
    self.webpage()
    f.write(self.html)
    f.close()  

  def webpage(self):
    h = Html.Html()
    head  = h.title("Stackup")
    body  = h.h1("Materials")
    body += self.matls.genHTMLMatlTable(h)
    body += h.h1("Layers")
    body += self.lyr.genHTMLLayersTable(self.matls, h)
    body += h.h1("Vias")
    body += self.via.genHTMLViaTable(self.matls, self.lyr, h)
    self.html= h.html(h.head(head) + h.body(body))   
  
  def solveModel(self):
    self.solv = Solver2D.Solver2D(self.config['solver'], self.mesh.nodeCount)
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
  