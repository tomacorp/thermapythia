import Units
import Html
import yaml
from PCModel import PCModel

class Matls(PCModel):

  def __init__(self, fn):
    
    self.rowName= "material"
    self.colName= "property"   
    self.config_js_fn= fn
    
    with open (self.config_js_fn, "r") as jsonHandle:
      jsonContents= jsonHandle.read()
      
    self.matlConfig= yaml.load(jsonContents)
    # print yaml.dump(self.matlConfig)
    
    self.matls= self.matlConfig['Materials']

    self.setMatlTableCols()
    self.checkProperties(self.matls, self.tableCols)
    self.setMatlTableUnits()
    self.convertUnits(self.matls, self.tableCols, self.tableUnits)
    self.propDict= self.createTableDictionary(self.matls, self.tableCols)
    
    self.distributeIsotropicProperties()
    
# Materials
  
  def setMatlTableCols(self):
    self.tableCols= ['name', 'type', 'density', 'color', 'specific_heat', 'conductivity', 
                         'conductivityXX', 'conductivityYY', 'conductivityZZ', 'reflection_coeff', 
                         'emissivity', 'max_height', 'thickness']    

  def setMatlTableUnits(self):
    self.tableUnits= {'name':'', 'type':'', 'density':'gm/cc', 'color':'', 'specific_heat':'J/gm-K', 'conductivity':'W/m-K', 
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
    for prop in self.tableCols:
      row += h.tdh(prop)
    matlHtml += h.tr(row)
    
    row= ''
    for prop in self.tableCols:
      row += h.tdh(self.tableUnits[prop])
    matlHtml += h.tr(row)    
    
    for matl in self.matls:
      row= ''
      for prop in self.tableCols:
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
    Materials are specified in a JSON file with this format:
      {    
        "Materials": 
        [
          { 
            "name":"Cu", "conductivity":"385W/m-K", "specific_heat":"0.385J/gm-K", "type":"solid", 
            "emissivity":"0.15", "reflection_coeff":"0.63", "density":"8.93gm/cc", "specularity":"", 
            "color":"IndianRed"
          },
          { 
            "name":"Prepreg", "conductivity":"1.059W/m-K", "type":"deformable", "emissivity":"0.9", 
            "specularity":"", "color":"Lime"
          }
        ],
      }
   The filename of the JSON file is passed into the __init__ and a Matls object is returned.
    
    """

  
  # TODO:
  # The old code. This is tricky - by manipulating __dict__, properties are constructed,
  # and are therefore difficult to trace throughout the code base using the IDE.
  # Need a set of material properties to match the existing 2D code so that all this
  # can be replaced with the new loader.
  # There is very similar code in Layers.py.
  
  #def loadConfig(self, config):
    #for matl in config:
      #matlName= matl['name']
      #matlThickness= Units.Units.convertToMeters(matl['thickness'], matl['thickness_unit'])
      #if (matl['xcond_unit'] == 'W/mK'):
        #matlCond= matl['xcond']
      #else:
        #print 'Unknown units for material conductivity: ' + str(matl['xcond_unit'])
        #matlCond= float(NaN)
      #matlResistanceProp= matlName + 'ResistancePerSquare'
      #matlCondProp= matlName + 'Cond'
      #self.__dict__[matlResistanceProp]= 1.0 / (matlCond * matlThickness)
      #self.__dict__[matlCondProp]= matlCond
      #print matlResistanceProp + ": " + str(self.__dict__[matlResistanceProp])
      #print matlCondProp + ": " + str(matlCond)  