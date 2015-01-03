import Units

class Matls:

  def __init__(self, config):
    self.loadConfig(config)
    return

  def loadConfig(self, config):
    units= Units.Units()
    for matl in config:
      matlName= matl['name']
      matlThickness= units.convertToMeters(matl['thickness'], matl['thickness_unit'])
      if (matl['xcond_unit'] == 'W/mK'):
        matlCond= matl['xcond']
      else:
        print 'Unknown units for material conductivity: ' + str(matl['xcond_unit'])
        matlCond= float(NaN)
      matlResistanceProp= matlName + 'ResistancePerSquare'
      matlCondProp= matlName + 'Cond'
      self.__dict__[matlResistanceProp]= 1.0 / (matlCond * matlThickness)
      self.__dict__[matlCondProp]= matlCond
      print matlResistanceProp + ": " + str(self.__dict__[matlResistanceProp])
      print matlCondProp + ": " + str(matlCond)
    
  def convertMilToMeters(self, mil):
    inches= mil / 1000.0 
    centimeters= inches * 2.54
    meters = centimeters / 100.0 
    return meters
  
  def reportConfig(self, config):
    lines= []
    for matl in config:
      lines.append('Material: ' + matl['name'])
      for key in matl.keys():
        lines.append('  ' + key + ' ' + str(matl[key]))
      lines.append('---------')
    out= "\n".join(lines)
    return out  
    
  def helpString(self):  
    return """ 
    
        Cu thermal conductivity: 401 W/(m degK)
        Cu thickness 1.2mil
        FR-4 thermal conductivity: 1W/(m degK)
        FR-4 thickness 59mil
        
        Thermal resistance
        
    Need units conversion, and to account for thicknesses of layers.
    
    """
  
  """
  "layer_matl": [
    { "name": "fr4",
      "type": "solid",
      "xcond": 1.0,
      "xcond_unit": "W/mK",
      "ycond": 1.0,
      "ycond_unit": "W/mK",
      "thickness": 59.0,
      "thickness_unit": "mil"
    },  
  """
  
  """ TODO: Thicknesses could come from layerMatlProps, 
  which would be a new class that has per-layer material properties. 
  """