# These are data layers. Each entry corresponds to a 2D array with one entry per pixel.

class Layers:
  def __init__(self, config):
    self.loadConfig(config)
    return

  def loadConfig(self, config):
    self.numdoublelayers= 0
    self.numintlayers= 0
    for lyr in config:
      self.__dict__[lyr['name']]= lyr['index']
      if (lyr['type'] == 'double'):
        self.numdoublelayers = self.numdoublelayers + 1
      if (lyr['type'] == 'int'):
        self.numintlayers = self.numintlayers + 1
      
  def reportConfig(self):
    lines= []
    for layer in config:
      lines.append('Layer: ' + layer['name'])
      for key in layer.keys():
        lines.append('  ' + key + ' ' + str(layer[key]))
      lines.append('---------')
    out= "\n".join(lines)
    return out

"""
The configuration for the layers is sent in a structure like this:
[
    { "index": 0, "type":"double", "name": "iso" },
    { "index": 1, "type":"double", "name": "heat" }
]
"""

# This is the old way of initializing layers:
## Field layers for double float values in mesh.field
    #self.iso = 0
    #self.heat = 1
    #self.resis = 2
    #self.deg = 3
    #self.flux = 4
    #self.isodeg = 5
    #self.spicedeg = 6
    #self.numdoublelayers = 7

## Field layers for integer values in mesh.ifield
    #self.isonode = 0
    #self.isoflag = 1
    #self.spicenodenum = 2
    #self.numintlayers = 3

    