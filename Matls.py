import Units
import Html
import yaml
from PCModel import PCModel

# TODO: REFACTOR: This isn't really materials, since it also has geometry and layer
# information. It is actually the PC board model class, and should be renamed.
# There might be another class for materials.

# TODO: The code has to understand that:
#  component height varies, and is specified in the IDF file
#  thermal pad displaces air
#  solder displaces air and the thermal pad
#  solder mask displaces air, thermal pad, and solder
#  copper displaces prepreg
#  solder mask coats the top layer and the top layer copper

# TODO: Handle coatings
# TODO: Handle thermal pads - 
#         Is the way that thermal pads expand and flow easy to model?
#         Are MEs already able to do this?
#         If not, would they be interested in a tool that does this?
# TODO: Handle attached parts with maximum size
# TODO: Display graphical visualization of the stackup that is in the matls.js file.

# TODO: Attached parts, especially resistors, might be handled with
# vias for electrodes, alumina layer, metal resistance material layer.
# The idea would be to get a picture of the oval hotspot on the top of the part.
# In this case the layer thickness would vary with different part sizes.

# TODO: Look at using SQLite for storing all this

class Matls(PCModel):

  def __init__(self, config, stackup_config):
    
    # The old code
    self.loadConfig(config)
    
    # The new code
    self.stackup_js_fn= stackup_config['stackup_config']
    with open (self.stackup_js_fn, "r") as jsonHandle:
      jsonContents= jsonHandle.read()
      
    self.stackup= yaml.load(jsonContents)
    # print yaml.dump(self.stackup)
    
    self.matls= self.stackup['Materials']

    self.setMatlTableCols()
    self.checkProperties(self.matls, self.matlTableCols)
    self.setMatlTableUnits()
    self.convertUnits(self.matls, self.matlTableCols, self.matlTableUnits)
    self.matlDict= self.createTableDictionary(self.matls, self.matlTableCols)
    
    self.distributeIsotropicProperties()
    
    
# Materials
  
  def setMatlTableCols(self):
    self.matlTableCols= ['name', 'type', 'density', 'color', 'specific_heat', 'conductivity', 'conductivityXX', 'conductivityYY', 'conductivityZZ', 'reflection_coeff', 'emissivity', 'max_height', 'thickness']    

  def setMatlTableUnits(self):
    self.matlTableUnits= {'name':'', 'type':'', 'density':'gm/cc', 'color':'', 'specific_heat':'J/gm-K', 'conductivity':'W/m-K', 
                          'conductivityXX':'W/m-K', 'conductivityYY':'W/m-K', 'conductivityZZ':'W/m-K', 'reflection_coeff':'', 
                          'emissivity':'', 'max_height':'m', 'thickness':'m'}
         
  def distributeIsotropicProperties(self):
    for matl in self.matls:
      if 'conductivity' in matl and str(matl['conductivity']) != '-':
        matl['conductivityXX'] = matl['conductivity']
        matl['conductivityYY'] = matl['conductivity']
        matl['conductivityZZ'] = matl['conductivity']
    
# HTML Generation
  
  def genHTMLMatlTable(self, h):        
    out= h.h3('Properties')
    matlHtml= ''

    row= ''
    for prop in self.matlTableCols:
      row += h.tdh(prop)
    matlHtml += h.tr(row)
    
    row= ''
    for prop in self.matlTableCols:
      row += h.tdh(self.matlTableUnits[prop])
    matlHtml += h.tr(row)    
    
    for matl in self.matls:
      row= ''
      for prop in self.matlTableCols:
        if prop in matl:
          if prop == 'name':
            row += h.tdh(matl[prop])
          elif prop == 'color':
            row += h.tdc(matl[prop], matl[prop])
          else:
            row += h.td(matl[prop])
        else:
          row += h.td('&nbsp;')
      matlHtml += h.tr(row)
      
    return out + h.table(matlHtml)

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
  
  # TODO:
  # The old code. This is tricky - by manipulating __dict__, properties are constructed,
  # and are therefore difficult to trace throughout the code base using the IDE.
  # Need a set of material properties to match the existing 2D code so that all this
  # can be replaced with the new loader.
  # There is very similar code in Layers.py.
  
  def loadConfig(self, config):
    for matl in config:
      matlName= matl['name']
      matlThickness= Units.Units.convertToMeters(matl['thickness'], matl['thickness_unit'])
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