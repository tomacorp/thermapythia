from PCModel import PCModel
import Html
import yaml

# OLD CODE: These are layer properties only. 
#           

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
# TODO: Display graphical visualization of the stackup that is in the layers.js file.

# TODO: Attached parts, especially resistors, might be handled with
# vias for electrodes, alumina layer, metal resistance material layer.
# The idea would be to get a picture of the oval hotspot on the top of the part.
# In this case the layer thickness would vary with different part sizes.

class Layers(PCModel):
  def __init__(self, config, fn):
    # The old code
    self.loadConfig(config)
    
    # The new code
    self.stackup_js_fn= fn
    with open (self.stackup_js_fn, "r") as jsonHandle:
      jsonContents= jsonHandle.read()
      
    self.layerConfig= yaml.load(jsonContents)
    # print yaml.dump(self.layerConfig)
    
    self.layers= self.layerConfig['Stackup']
    self.setLayerTableCols()
    self.checkProperties(self.layers, self.layerTableCols)
    self.setLayerTableUnits()
    self.convertUnits(self.layers, self.layerTableCols, self.layerTableUnits)
    self.layerDict= self.createTableDictionary(self.layers, self.layerTableCols)    
    
    self.calculateBoardThickness()
    self.calculateLayerZCoords()     
    
    return
  
  def getProp(self, layerName, prop):
    if layerName not in self.layerDict:
      print "Layer name " + str(layerName) + " not found"
      return ''
    if prop not in self.layerDict[layerName]:
      print "Property " + str(prop) + " not found in layer " + str(layerName)
      return ''
    return self.layerDict[layerName][prop]  
  
  def getUnits(self, layerName):
    return self.layerTableUnits[layerName]
  
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
    for layer in self.layers:
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
    for layer in self.layers:
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
      layer= self.layers[layerIdx]
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
    for layer in self.layers:
      self.boardThickness= self.boardThickness + layer['thickness']      
      
    return
          
  def calculateLayerZCoords(self):
    height= self.boardThickness
    for layer in self.layers:
      layer['z_top']= height
      height= height - layer['thickness']  
      layer['z_bottom']= height
    return

  # HTML Generation
  def genHTMLLayersTable(self, matl, h):
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
    for layer in self.layers:
      row= ''
      for prop in self.layerTableCols:
        if prop in layer:
          if prop == 'name':
            row += h.tdh(layer[prop])
            thisLayerName= layer[prop]
          elif prop == 'matl':
            thisMaterialName= layer[prop]
            if thisMaterialName in matl.matlDict:
              if 'color' in matl.matlDict[thisMaterialName]:
                row += h.tdc(layer[prop], matl.matlDict[thisMaterialName]['color'])
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
  
  # The old code
  
  def loadConfig(self, config):
    self.numdoublelayers= 0
    self.numintlayers= 0
    for lyr in config:
      self.__dict__[lyr['name']]= lyr['index']
      if (lyr['type'] == 'double'):
        self.numdoublelayers = self.numdoublelayers + 1
      if (lyr['type'] == 'int'):
        self.numintlayers = self.numintlayers + 1
        
  def helpString(self):        
    return """ 
    Layers are specified in a JSON file with this format:
      {    
        "Stackup": 
        [
          { "name":"topside_cu", "matl":"Cu", "thickness":"1.2mil", "type":"Rigid"},
          { "name":"core", "matl":"Core", "thickness":"12mil" , "type":"Rigid"}
        ],
      }
   The filename of the JSON file is passed into the __init__ and a Layers object is returned.

    """
  