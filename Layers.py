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
    