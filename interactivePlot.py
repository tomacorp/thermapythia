import matplotlib.pyplot as plt
from itertools import izip
import numpy as np
import Matls
import Layers

"""
TODO:

Improve debug web page layout and ordering.
Add style to debug web page output.

Put solutions into separate directories based on problem name.
Make a static index page for all the problems and solutions.

Rename InteractivePlot - git still thinks it is lower case.

""" 

class InteractivePlot:
  def __init__(self, config, solv, lyr, mesh):
    self.lyr     = lyr
    self.mesh    = mesh
    self.config  = config
    self.layertype= {}
    self.filename= {}
    return
  
  def pairwise(self, iterable):
      "s -> (s0,s1), (s2,s3), (s4, s5), ..."
      a = iter(iterable)
      return izip(a, a)  
  
  def plotAll(self):
    for layer in self.config['simulation_layers']:
      self.layertype[layer['name']]= layer['type']
    
    for device in self.config['outputs']['mesh']:
      for output in self.config['outputs']['mesh'][device]:
        if self.layertype[output] == 'double':
          self.plotDoubleLayer(output, self.lyr.__dict__[output], device)
        if self.layertype[output] == 'int':
          self.plotIntLayer(output, self.lyr.__dict__[output], device)
    # Plot deltas     
    for device in self.config['outputs']['deltamesh']:
      for out1, out2 in self.pairwise(self.config['outputs']['deltamesh'][device]):
        lyr1= self.lyr.__dict__[out1]
        lyr2= self.lyr.__dict__[out2]
        plotName= device + '_' + out1 + '_' + out2
        self.plotDeltaDoubleLayer(plotName, lyr1, lyr2, device)
        
  def plotDoubleLayer(self, output, layerIdx, device):
    print "Plot double layer " + output + " at layer index " + str(layerIdx)
    plt.figure(1)
    plotfield= self.mesh.field[:, :, layerIdx];
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad2= plt.pcolormesh(self.mesh.xr, self.mesh.yr, plotfield)
    plt.colorbar()
    plt.title(output + ' heat map')
    if device == 'interactive':
      plt.draw()
      plt.show()
    if device == 'png':
      self.filename[output]= self.config['outputs']['outputDirectory'] + '/' + output + '_heat_map.png'
      plt.savefig(self.filename[output])    
    return
  
  def plotIntLayer(self, output, layerIdx, device):
    print "Plot int layer" + output + " at layer index " + str(layerIdx)
    plt.figure(1)
    plotfield= self.mesh.ifield[:, :, layerIdx];
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad2= plt.pcolormesh(self.mesh.xr, self.mesh.yr, plotfield)
    plt.colorbar()
    plt.title(output + ' heat map')
    if device == 'interactive':
      plt.draw()
      plt.show()
    if device == 'png':
      self.filename[output]= self.config['outputs']['outputDirectory'] + '/' + output + '_heat_map.png'
      plt.savefig(self.filename[output])    
    return
  
  def plotDeltaDoubleLayer(self, output, layerIdx1, layerIdx2, device):
    z1= self.mesh.field[:, :, layerIdx1];
    z2= self.mesh.field[:, :, layerIdx2];
    plotfield= z1 - z2
    allclose= np.allclose(z1, z2, rtol=1e-05, atol=1e-08)
    if allclose:
      print "Layer " + str(layerIdx1) + " is close to " + str(layerIdx2)
    else:
      print "Layer " + str(layerIdx1) + " differs from " + str(layerIdx2)
    plt.figure(1)
    plt.subplot(1,1,1)
    plt.axes(aspect=1)
    quad2= plt.pcolormesh(self.mesh.xr, self.mesh.yr, plotfield)
    plt.colorbar()
    plt.title(output + ' heat map')
    if device == 'interactive':
      plt.draw()
      plt.show()
    if device == 'png':
      self.filename[output]= self.config['outputs']['outputDirectory'] + '/' + output + '_heat_map.png'
      plt.savefig(self.filename[output])      
    return

def main():
  import numpy as np
  print "This is a test program for InteractivePlot. It draws mesh plots on the screen."
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
