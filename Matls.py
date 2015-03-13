import Units
import Html
import yaml
from sets import Set
from pint import UnitRegistry
#from pygraph.classes.graph import graph
#from pygraph.algorithms.minmax import shortest_path
#from sets import Set

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

# TODO: Look at using SQLite for storing all this

class Matls:

  def __init__(self, config, stackup_config):
    
    # The old code
    self.loadConfig(config)
    
    # The new code
    self.stackup_js_fn= stackup_config['stackup_config']
    with open (self.stackup_js_fn, "r") as jsonHandle:
      jsonContents= jsonHandle.read()
      
    self.stackup= yaml.load(jsonContents)
    # print yaml.dump(self.stackup)

    self.setMatlTableCols()
    self.checkProperties('Materials', self.matlTableCols)
    self.setMatlTableUnits()
    self.convertUnits('Materials', self.matlTableCols, self.matlTableUnits)
    self.matlDict= self.createTableDictionary('Materials', self.matlTableCols)
    
    self.setLayerTableCols()
    self.checkProperties('Stackup', self.layerTableCols)
    self.setLayerTableUnits()
    self.convertUnits('Stackup', self.layerTableCols, self.layerTableUnits)
    self.layerDict= self.createTableDictionary('Stackup', self.layerTableCols)
    
    self.setViaTableCols()
    self.checkProperties('Vias', self.viaTableCols)
    self.setViaTableUnits()
    self.convertUnits('Vias', self.viaTableCols, self.viaTableUnits)
    self.viaDict= self.createTableDictionary('Vias', self.viaTableCols)
    
    self.distributeIsotropicProperties()
    self.calculateBoardThickness()
    self.calculateLayerZCoords()    
    
    if (stackup_config['debug'] == 1):
      self.createWebPage(stackup_config['webPageFileName'])
    
    
# Materials
  
  def setMatlTableCols(self):
    self.matlTableCols= ['name', 'type', 'density', 'color', 'specific_heat', 'conductivity', 'conductivityXX', 'conductivityYY', 'conductivityZZ', 'reflection_coeff', 'emissivity', 'max_height', 'thickness']    

  def setMatlTableUnits(self):
    self.matlTableUnits= {'name':'', 'type':'', 'density':'gm/cc', 'color':'', 'specific_heat':'J/gm-K', 'conductivity':'W/m-K', 
                          'conductivityXX':'W/m-K', 'conductivityYY':'W/m-K', 'conductivityZZ':'W/m-K', 'reflection_coeff':'', 
                          'emissivity':'', 'max_height':'m', 'thickness':'m'}
         
  def distributeIsotropicProperties(self):
    for matl in self.stackup['Materials']:
      if 'conductivity' in matl and str(matl['conductivity']) != '-':
        matl['conductivityXX'] = matl['conductivity']
        matl['conductivityYY'] = matl['conductivity']
        matl['conductivityZZ'] = matl['conductivity']
        
# Layers

  def setLayerTableCols(self):
    self.layerTableCols= ['name', 'matl', 'type', 'thickness', 'displaces', 'coverage',
                          'z_bottom', 'z_top', 'adheres_to']
    
  def setLayerTableUnits(self):
    self.layerTableUnits= {'name':'', 'matl':'', 'type':'', 'thickness':'m', 'displaces':'', 'coverage':'',
                           'start':'', 'stop':'', 'z_bottom':'m', 'z_top':'m', 'adheres_to':'' }
          
  def calculateBoardThickness(self):
    # Store coverage and thickness for adjacent fill layer calculations
    coverage= []
    thickness= []
    for layer in self.stackup['Stackup']:
      cov= 1.0
      if layer['coverage'] != '-':
        cov= float(layer['coverage'])
      coverage.append(cov)
      thickness.append(layer['thickness'])
     
    # Calculate amounts of fill due to embeddeding prepreg into adjacent layers,
    # which contain a variable coverage of copper (0 to 100%)
    layerIdx=0
    fillFromAbove=[]
    fillFromBelow=[]
    fillLayer=[]
    for layer in self.stackup['Stackup']:
      if layer['type'] == 'Fill':
        fillAbove= 0.0
        if layerIdx > 0:
          fillAbove= (1.0 - coverage[layerIdx-1]) * thickness[layerIdx-1]
        fillBelow= 0.0
        if layerIdx < len(coverage) - 1:
          fillBelow= (1.0 - coverage[layerIdx+1]) * thickness[layerIdx+1]
        fillFromBelow.append(fillBelow)
        fillFromAbove.append(fillAbove)
        fillLayer.append(layerIdx)
      layerIdx= layerIdx + 1

    # Calculate laminated thickness of prepreg layers due to being embedded into an
    # adjacent trace layer with less than 100% coverage.
    # Modify the layer table to reflect new calculated thickness, 
    # which is just for the material between the copper layers. 
    # This prepreg thickness does not include the thickness of the copper layers.
    fillIdx=0
    for layerIdx in fillLayer:
      layer= self.stackup['Stackup'][layerIdx]
      laminatedThickness= layer['thickness'] - fillFromAbove[fillIdx] - fillFromBelow[fillIdx]
      # print "Fill Layer Name: " + str(layer['name'])
      # print "  Unlaminated layer Thickness: " + str(layer['thickness'])
      # print "  Fill from above: " + str(fillFromAbove[fillIdx])
      # print "  Fill from below: " + str(fillFromBelow[fillIdx])
      # print "  Laminated thickness: " + str(laminatedThickness) + "\n"
      layer['thickness']= laminatedThickness
      fillIdx = fillIdx + 1
      
    # Board thickness with embedding
    self.boardThickness=0
    for layer in self.stackup['Stackup']:
      self.boardThickness= self.boardThickness + layer['thickness']      
      
    return
          
  def calculateLayerZCoords(self):
    height= self.boardThickness
    for layer in self.stackup['Stackup']:
      layer['z_top']= height
      height= height - layer['thickness']  
      layer['z_bottom']= height
    return
    
# Vias
      
  def setViaTableCols(self):
    self.viaTableCols= ['name', 'matl', 'to', 'from']
    return
    
  def setViaTableUnits(self):
    self.viaTableUnits= {'name':'', 'matl':'', 'to':'', 'from':''}   
    return
    
# Routines shared among Materials, Layers, and Vias
  
  def checkProperties(self, section, tableCols):
    for elt in self.stackup[section]:
      for key in elt.keys():
        if key not in tableCols:
          print "Unrecognized property: " + str(key) + " in config file: " + str(self.stackup_js_fn)
            
  def convertUnits(self, section, tableCols, tableUnits):
    for elt in self.stackup[section]:
      for prop in tableCols:
        if prop in elt:
          if prop not in tableUnits:
            propValue= elt[prop]
            propUnits= ''
          elif tableUnits[prop] == '':
            propValue= elt[prop]
            propUnits= ''
          else:
            propValue, propUnits= Units.Units.convertUnits(elt[prop], tableUnits[prop])
          elt[prop]= propValue
        else:
          elt[prop]= '-'           

  def createTableDictionary(self, section, tableCols):
    seq= 0
    dict= {}
    for elt in self.stackup[section]:
      # print "Setting database name " + elt['name']
      if elt['name'] in dict:
        print "ERROR: Repeated name " + str(elt['name']) + " in section " + str(section)
      dict[elt['name']]= {}
      dict[elt['name']]['seq']= seq
      for prop in tableCols:
        dict[elt['name']][prop]= elt[prop]
      seq = seq + 1  
    return dict
  
# HTML Generation

  def createWebPage(self, webPageFileName):
    # np.set_printoptions(threshold='nan', linewidth=10000)
    f= open(webPageFileName, 'w')
    self.webpage()
    f.write(self.html)
    f.close()  

  def webpage(self):
    h = Html.Html()
    head  = h.title("Stackup")
    body  = h.h1("Materials")
    body += self.genHTMLMatlTable(h)
    body += h.h1("Layers")
    body += self.genHTMLLayersTable(h)
    body += h.h1("Vias")
    body += self.genHTMLViaTable(h)
    self.html= h.html(h.head(head) + h.body(body)) 
  
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
    
    for matl in self.stackup['Materials']:
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
  
  def genHTMLLayersTable(self, h):
    layerHtml= ''
  
    row= ''
    for prop in self.layerTableCols:
      row += h.tdh(prop)
    layerHtml += h.tr(row)
    
    row= ''
    for prop in self.layerTableCols:
      row += h.tdh(self.layerTableUnits[prop])
    layerHtml += h.tr(row)    
    
    # How to set a default for a layer property? Would like to have default coverage=1
    thisLayerName=''
    for layer in self.stackup['Stackup']:
      row= ''
      for prop in self.layerTableCols:
        if prop in layer:
          if prop == 'name':
            row += h.tdh(layer[prop])
            thisLayerName= layer[prop]
          elif prop == 'matl':
            thisMaterialName= layer[prop]
            if thisMaterialName in self.matlDict:
              if 'color' in self.matlDict[thisMaterialName]:
                row += h.tdc(layer[prop], self.matlDict[thisMaterialName]['color'])
              else:
                print "No color set for material: " + str(thisMaterialName) + " in layer " + str(thisLayerName)
                row += h.tdc(layer[prop], 'yellow')
            else:
              print "Unrecognized material name: " + str(thisMaterialName) + " in layer " + str(thisLayerName)
              row += h.tdc(thisMaterialName, 'red')
          else:
            row += h.td(layer[prop])
        else:
          # Default layer properties
          if prop == 'coverage':
            row += h.td('1.0')
          row += h.td('&nbsp;')    
      layerHtml += h.tr(row)
      
    return h.h3('Stackup') + h.table(layerHtml)
  
  def genHTMLViaTable(self, h):   
    viaHtml= ''
  
    row= ''
    for prop in self.viaTableCols:
      row += h.tdh(prop)
    viaHtml += h.tr(row)
    
    row= ''
    for prop in self.viaTableCols:
      val= self.viaTableUnits[prop]
      if val == '':
        val= '&nbsp;'
      row += h.tdh(val)
    viaHtml += h.tr(row)

    for via in self.stackup['Vias']:
      row= ''
      vianame= ''
      for prop in self.viaTableCols:
        if prop in via:
          if prop == 'name':
            vianame= via[prop]
            row += h.tdh(vianame)
          elif prop == 'matl':
            thisMaterialName= via[prop]
            if thisMaterialName in self.matlDict:
              row += h.tdc(via[prop], self.matlDict[thisMaterialName]['color'])
            else:
              print "Via material " + str(thisMaterialName) + " not found for via " + str(vianame)
              row += h.tdc(str(thisMaterialName), 'red')
          elif prop == 'to':
            toLayer= via[prop]
            if toLayer in self.layerDict:
              row += h.td(toLayer)
            else:
              print "Via 'to' layer " + str(toLayer) + " not found for via " + str(vianame)
              row += h.tdc(str(toLayer), 'red')
          elif prop == 'from':
            fromLayer= via[prop]
            if fromLayer in self.layerDict:
              row += h.td(fromLayer)
            else:
              print "Via 'from' layer " + str(fromLayer) + " not found for via " + str(vianame)
              row += h.tdc(str(fromLayer), 'red')          
          else:
            row += h.td(via[prop])
        else:
          row += h.td('&nbsp;')
      viaHtml += h.tr(row)
    
    return h.h3('Vias') + h.table(viaHtml)
  
  
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