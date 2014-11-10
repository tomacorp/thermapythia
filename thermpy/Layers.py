class Layers:
  def __init__(self):

# Field layers for double float values in mesh.field
    self.iso = 0
    self.heat = 1
    self.resis = 2
    self.deg = 3
    self.flux = 4
    self.isodeg = 5
    self.spicedeg = 6
    self.numdoublelayers = 7

# Field layers for integer values in mesh.ifield
    self.isonode = 0
    self.isoflag = 1
    self.spicenodenum = 2
    self.numintlayers = 3