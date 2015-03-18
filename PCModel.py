import Units

# Routines shared among Materials, Layers, and Vias

class PCModel:

  def checkProperties(self, section, tableCols):
    for elt in section:
      for key in elt.keys():
        if key not in tableCols:
          print "Unrecognized property: " + str(key) + " in " + str(self.rowName) + " config file: " + str(self.config_js_fn)

  def convertUnits(self, section, tableCols, tableUnits):
    for elt in section:
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
    for elt in section:
      # print "Setting database name " + elt['name']
      if elt['name'] in dict:
        print "ERROR: Repeated name " + str(elt['name']) + " in section " + str(section) + " config file: " + str(self.config_js_fn)
      dict[elt['name']]= {}
      dict[elt['name']]['seq']= seq
      for prop in tableCols:
        dict[elt['name']][prop]= elt[prop]
      seq = seq + 1  
    return dict
  
  def getProp(self, propName, propVal):
    if propName not in self.propDict:
      print self.rowName + " with name " + str(propName) + " not found"
      return ''
    if propVal not in self.propDict[propName]:
      print self.colName + " with name " + str(propVal) + " not found for " + self.rowName + " " + str(propName)
      return ''
    return self.propDict[propName][propVal]   
  
  def __str__(self):
    out= ''
    for row in self.propDict:
      for prop in self.tableCols:
        if prop in row:
          if prop == 'name':
            out += str(row[prop]) + ': '
          else:
            out += str(prop) + " = " + str(row[prop]) + ", "
      out += "\n"
    return out  
  
  def getUnits(self, propName):
    return self.tableUnits[propName]  