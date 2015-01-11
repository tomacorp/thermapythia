import matplotlib.pyplot as plt
import Matls
import Layers

"""
TODO: 

Integrate the plots with the debug web page.
Add the difference plots to the JSON config and debug web page.
Improve debug web page layout and ordering.
Add interactive plots from JSON.
Remove unused cruft from outputs JSON and the code.

""" 

class InteractivePlot:
  def __init__(self, config, solv, lyr, mesh):
    self.lyr     = lyr
    self.mesh    = mesh
    self.layertype= {}
    self.interactive = False
    self.png = True
    self.showPlots= True
    # self.loadConfig(config['outputs'])
    self.plotPNG(config, lyr)
    if (self.showPlots == True):
      self.simplePlot(solv, lyr)
    return

  def loadConfig(self, config):
    for output in config:
      self.__dict__[output['name']]= output['active']    
    return
  
  def plotPNG(self, config, lyr):
    for layer in config['simulation_layers']:
      self.layertype[layer['name']]= layer['type']
    for output in config['outputs']['png']:
      if self.layertype[output] == 'double':
        self.plotDoubleLayer(output, lyr.__dict__[output])
      if self.layertype[output] == 'int':
        self.plotIntLayer(output, lyr.__dict__[output])
        
  def plotDoubleLayer(self, output, layerIdx):
    print "Plot double layer " + output + " at layer index " + str(layerIdx)
    plt.figure(1)
    plotfield= self.mesh.field[:, :, layerIdx];
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad2= plt.pcolormesh(self.mesh.xr, self.mesh.yr, plotfield)
    plt.colorbar()
    plt.title(output + ' heat map')
    if self.interactive == True:
      plt.draw()
    if self.png == True:
      plt.savefig('thermpypng/' + output + '_heat_map.png')    
    return
  
  def plotIntLayer(self, output, layerIdx):
    print "Plot int layer" + output + " at layer index " + str(layerIdx)
    plt.figure(1)
    plotfield= self.mesh.ifield[:, :, layerIdx];
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad2= plt.pcolormesh(self.mesh.xr, self.mesh.yr, plotfield)
    plt.colorbar()
    plt.title(output + ' heat map')
    if self.interactive == True:
      plt.draw()
    if self.png == True:
      plt.savefig('thermpypng/' + output + '_heat_map.png')    
    return
  
  def simplePlot(self, solv, lyr):
    self.plotTemperature()
    if (solv.useSpice == True):
      self.plotSpicedeg()
      self.plotLayerDifference(lyr.spicedeg, lyr.deg)
    if self.interactive == True:
      self.show()  

  def show(self):
    plt.show()

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
    if self.interactive == True:
      plt.draw()
    if self.png == True:
      plt.savefig('thermpypng/aztecOO_heat_map.png')
    
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
    if self.interactive == True:
      print "Interactive plot for Spicedeg"
      plt.draw() 
    if self.png == True:
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
    if self.interactive == True:
      plt.draw() 
      print "Interactive plot for layer difference"
    if self.png == True:
      plt.savefig('thermpypng/difference_heat_map.png')

def main():
  import numpy as np
  print "This is a test program for interactivePlot. It draws mesh plots on the screen."
  w= 4
  h= 3
  field= np.zeros((w, h), dtype='double')
  xr, yr= np.mgrid[0:w+1, 0:h+1]
  for x in range(0,w):
    for y in range(0,h):
      field[x,y] += x*y + x/2.0 + y/2.0
    
  plt.subplot(1, 1, 1)
  plt.pcolormesh(xr, yr, field)
  plt.title('pcolormesh test plot')
  # set the limits of the plot to the limits of the data
  plt.axis([xr.min(), xr.max(), yr.min(), yr.max()])
  plt.colorbar()  
  plt.draw()
  plt.show()    

  # make these smaller to increase the resolution
  dx, dy = 0.5, 0.5
  
  # generate 2 2d grids for the x & y bounds
  y, x = np.mgrid[slice(-3, 3 + dy, dy),
                  slice(-3, 3 + dx, dx)]
  z = (1 - x / 2. + x ** 5 + y ** 3) * np.exp(-x ** 2 - y ** 2)

  plt.subplot(1, 1, 1)
  plt.pcolormesh(x, y, z)
  plt.title('pcolormesh test plot')
  plt.axis([x.min(), x.max(), y.min(), y.max()])
  plt.colorbar()  
  plt.draw()
  plt.show()  

if __name__ == '__main__':
  main()
