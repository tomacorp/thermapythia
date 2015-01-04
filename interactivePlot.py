import matplotlib.pyplot as plt
import Matls
import Layers

"""
TODO: 

Integrate the plots with the debug web page.
Use the titles on the plots

""" 

class interactivePlot:
  def __init__(self, config, solv, lyr, mesh):
    self.lyr     = lyr
    self.mesh    = mesh
    self.interative = True
    self.png = True
    self.loadConfig(config)
    if (self.showPlots == True):
      self.simplePlot(solv, lyr)
    return

  def loadConfig(self, config):
    for output in config:
      self.__dict__[output['name']]= output['active']    
    return
  
  def simplePlot(self, solv, lyr):
    self.plotTemperature()
    if (solv.useSpice == True):
      self.plotSpicedeg()
      self.plotLayerDifference(lyr.spicedeg, lyr.deg)
    self.show()  

  def plotSolution(self):
    """
    plotsolution(interactivePlot self)
    Plot the problem grids and also the solution grid.
    """
    self.plotResistance()
    self.plotTemperature()
    self.plotDirichlet()
    self.plotHeatSources()
    self.plotSpicedeg()
    self.plotIsotherm()
    self.show()

  def show(self):
    plt.show()

  def plotIsotherm(self):
    """
    Make a plot that shows which nodes have Dirichlet boundary conditions
    attached to them through a resistor
    """
    z5= self.mesh.ifield[:, :, self.lyr.isoflag]; 
    plt.figure(5)
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad4= plt.pcolormesh(self.mesh.xr, self.mesh.yr, z5)
    plt.colorbar()
    plt.title('Nodes with Dirichlet boundary conditions map')
    if self.interative == True:
      plt.draw()
    if self.png == True:
      plt.savefig('thermpypng/dirichlet_map.png')

  def plotHeatSources(self):
    """
    Make a plot that shows which nodes have heat sources attached.
    """
    z4= self.mesh.field[:, :, self.lyr.heat];
    plt.figure(4)
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad4= plt.pcolormesh(self.mesh.xr, self.mesh.yr, z4)
    plt.colorbar()
    plt.title('Heat sources map')
    if self.interative == True:
      plt.draw()
    if self.png == True:
      plt.savefig('thermpypng/heat_sources_map.png')

  def plotDirichlet(self):
    """
    Make a plot that shows the relative temperature of the Dirichlet
    boundary condition nodes.
    """
    z3= self.mesh.field[:, :, self.lyr.isodeg];
    plt.figure(3)
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad3= plt.pcolormesh(self.mesh.xr, self.mesh.yr, z3)
    plt.colorbar()
    plt.title('Dirichlet boundary conditions temperature map')
    if self.interative == True:
      plt.draw()
    if self.png == True:
      plt.savefig('thermpypng/dirichlet_temperature_map.png')

  def plotTemperature(self):
    """
    Make a plot that shows the temperature of the mesh nodes.
    """
    plt.figure(2)
    z2= self.mesh.field[:, :, self.lyr.deg];
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad2= plt.pcolormesh(self.mesh.xr, self.mesh.yr, z2)
    plt.colorbar()
    plt.title('AztecOO heat map')
    if self.interative == True:
      plt.draw()
    if self.png == True:
      plt.savefig('thermpypng/aztecOO_heat_map.png')

  def plotResistance(self):
    """
    Make a plot that shows the thermal resistance of the materials in the mesh nodes.
    """
    z1= self.mesh.field[:, :, self.lyr.resis];
    plt.figure(1)
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad1= plt.pcolormesh(self.mesh.xr, self.mesh.yr, z1)
    plt.colorbar()
    plt.title('Thermal resistance map')
    if self.interative == True:
      plt.draw()
    if self.png == True:
      plt.savefig('thermpypng/thermal_res_map.png')
    
  def plotSpicedeg(self):
    """
    Make a plot that shows the temperature of the mesh nodes as simulated by Xyce.
    """
    z1= self.mesh.field[:, :, self.lyr.spicedeg];
    plt.figure(1)
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad1= plt.pcolormesh(self.mesh.xr, self.mesh.yr, z1)
    plt.colorbar()
    plt.title('Spice heat map')
    plt.draw() 
    plt.savefig('thermpypng/spice_heat_map.png')
    
  def plotLayerDifference(self, layer1, layer2):
    """
    Make a plot that shows the difference between two values in the mesh.
    """
    z1= self.mesh.field[:, :, layer1];
    z2= self.mesh.field[:, :, layer2];
    z3= z1 - z2
    plt.figure(1)
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad1= plt.pcolormesh(self.mesh.xr, self.mesh.yr, z3)
    plt.colorbar()
    plt.title('Difference heat map')
    plt.draw()
    plt.savefig('thermpypng/difference_heat_map.png')

def main():
  print "This is a test program for interactivePlot. It draws a graph on the screen."
  import Layers
  import Mesh2D
  lyr = Layers.Layers()
  matls = Matls.Matls()  
  mesh = Mesh2D.Mesh(3, 3, lyr, matls)
  
  for x in range(0,3):
    for y in range(0,3):
      mesh.field[x, y, lyr.spicedeg] = (x+1) * ((y+1) + 1)

  plots= interactivePlot(lyr, mesh)
  plots.png= True
  plots.interative= True
  plots.plotSpicedeg() 
  plots.show()


if __name__ == '__main__':
  main()
