import Units
import Html
import yaml
from PCModel import PCModel

# TODO: Look at using SQLite for storing all this

class Vias(PCModel):

  def __init__(self, fn):

    self.stackup_js_fn= fn
    with open (self.stackup_js_fn, "r") as jsonHandle:
      jsonContents= jsonHandle.read()

    self.viaConfig= yaml.load(jsonContents)
    # print yaml.dump(self.viaConfig)

    self.vias= self.viaConfig['Vias']

    self.setViaTableCols()
    self.checkProperties(self.vias, self.viaTableCols)
    self.setViaTableUnits()
    self.convertUnits(self.vias, self.viaTableCols, self.viaTableUnits)
    self.viaDict= self.createTableDictionary(self.vias, self.viaTableCols)

# Vias

  def setViaTableCols(self):
    self.viaTableCols= ['name', 'matl', 'to', 'from']
    return

  def setViaTableUnits(self):
    self.viaTableUnits= {'name':'', 'matl':'', 'to':'', 'from':''}   
    return

# HTML Generation

  def genHTMLViaTable(self, matl, lyr, h):   
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

    for via in self.vias:
      row= ''
      vianame= ''
      for prop in self.viaTableCols:
        if prop in via:
          if prop == 'name':
            vianame= via[prop]
            row += h.tdh(vianame)
          elif prop == 'matl':
            thisMaterialName= via[prop]
            if thisMaterialName in matl.propDict:
              row += h.tdc(via[prop], matl.propDict[thisMaterialName]['color'])
            else:
              print "Via material " + str(thisMaterialName) + " not found for via " + str(vianame)
              row += h.tdc(str(thisMaterialName), 'red')
          elif prop == 'to':
            toLayer= via[prop]
            if toLayer in lyr.propDict:
              row += h.td(toLayer)
            else:
              print "Via 'to' layer " + str(toLayer) + " not found for via " + str(vianame)
              row += h.tdc(str(toLayer), 'red')
          elif prop == 'from':
            fromLayer= via[prop]
            if fromLayer in lyr.propDict:
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
    Vias are specified in a JSON file with this format:
      {    
        "Vias": 
        [
          { "name":"shield_top_wall", "matl": "Al", "from":"shield_top", "to":"topside_cu"},
          { "name":"thru", "matl":"Cu", "from":"topside_cu", "to":"bottomside_cu"},
          { "name":"screw", "matl":"StainlessSteel", "from":"shield_top", "to":"shield_bottom"},
          { "name":"hole", "matl":"Air", "from":"topside_cu", "to":"bottomside_cu"}
        ],
      }
   The filename of the JSON file is passed into the __init__ and a Vias object is returned.

    """