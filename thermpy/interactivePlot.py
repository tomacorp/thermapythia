import matplotlib.pyplot as plt
import Matls
import Layers

class interactivePlot:
  def __init__(self, lyr, mesh):
    self.lyr     = lyr
    self.mesh    = mesh  

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
    plt.draw()

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
    plt.draw()

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
    plt.draw()

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
    plt.draw()

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
    plt.draw()
    
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
  plots.plotSpicedeg() 
  plots.show()

if __name__ == '__main__':
  main()
