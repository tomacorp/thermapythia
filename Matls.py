import Units
import Html
import yaml
from sets import Set
from pint import UnitRegistry

# TODO: REFACTOR: This isn't really materials, since it also has geometry and layer
# information. It is actually the boxel model class, and should be renamed.
# There might be another class for materials.

class Matls:

  def __init__(self, config, stackup_config):
    
    self.loadConfig(config)
    stackup_js_fn= stackup_config['stackup_config']
    with open (stackup_js_fn, "r") as jsonHandle:
      jsonContents= jsonHandle.read()    
    self.stackup= yaml.load(jsonContents)
    print yaml.dump(self.stackup)
    if (stackup_config['debug'] == 1):
      self.createWebPage(stackup_config['webPageFileName'])
    self.units= Units.Units()
    return

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
    
  def reportConfig(self, config):
    lines= []
    for matl in config:
      lines.append('Material: ' + matl['name'])
      for key in matl.keys():
        lines.append('  ' + key + ' ' + str(matl[key]))
      lines.append('---------')
    out= "\n".join(lines)
    return out  
  
  
  def createWebPage(self, webPageFileName):
    print "Creating stackup web page"
    # np.set_printoptions(threshold='nan', linewidth=10000)
    f= open(webPageFileName, 'w')
    self.webpage()
    f.write(self.html)
    f.close()  

  def webpage(self):
    h = Html.Html()
    head  = h.title("Stackup")
    body  = h.h1("Materials")
    body += self.matlsStr(h)
    body += h.h1("Layers")
    body += self.layersStr()
    body += h.h1("Vias")
    body += self.viasStr()
    self.html= h.html(h.head(head) + h.body(body)) 
  
  def layersStr(self):
    return "Layer properties"
    
  def matlsStr(self, h):
    #{"Materials":
    #[{ name:"Al" conductivity:"150W/m-K" specific_heat:"0.860J/gdegC" type:"solid" emissivity:"0.09" reflection_coeff:"0.93" density:"2.70gm/cc" specularity:"" grain_size:"" color:"gray"},`
    #{ name:"Cu" conductivity:"385W/m-K" specific_heat:"0.385J/gdegC" type:"solid" emissivity:"0.15" reflection_coeff:"0.63" density:"8.93g/cc" specularity:"" grain_size:"" color:"orange"},
    #{ name:"StainlessSteel" conductivity:"" specific_heat:"" emissivity:"0.16" type:"solid" color:"yellow"},
    #{ name:"Solder" conductivity:"58W/m-K" specific_heat:"0.23K/gdegC" emissivity:"0.06" reflection_coeff:"0.80" density:"7.38gm/cc" type:"solder_paste" color:"light_gray"},
    #{ name:"Air" conductivity:"0" specific_heat:"0" type:"gas" color:"white"},
    #{ name:"ThermalPad" conductivity:"" type:"deformable_pad" color:"dark_gray"},
    #{ name:"Solder_mask" conductivity:"0.9W/m-K" type:"solid" thickness:"1.0mil" color:"dark_green"},
    #{ name:"Core" conductivityXX:".343W/m-K" conductivityYY:".343W/m-K" conductivityZZ:"1.059W/m-K" density:"1.85gm/cc" type:"solid" emissivity:"0.9" specularity:"" color:"light_green"},
    #{ name:"Prepreg" conductivity:"1.059W/m-K" type:"deformable" emissivity:"0.9" specularity:"" color:"green"},
    #{ name:"top_component" type:"component" max_height:"5mm" color:"brown"},
    #{ name:"bottom_component" type:"component" max_height:"2mm" color:"brown"}
    #]}, 
    
    self.matlPropSet= Set([])
    for matl in self.stackup['Materials']:
      for key in matl.keys():
        self.matlPropSet.add(key)   
        
    # TODO: Convert density and Specific heat to kg/m^3 and J/kg-K
    # Set property order for report tables
    cols= ['name', 'type', 'density', 'color', 'specific_heat', 'conductivity', 'conductivityXX', 'conductivityYY', 'conductivityZZ', 'reflection_coeff', 'emissivity', 'max_height', 'thickness']    
    
    # Set desired units for properties
    units= {'name':'', 'type':'', 'density':'gm/cc', 'color':'', 'specific_heat':'J/gm-K', 'conductivity':'W/m-K', 
            'conductivityXX':'W/m-K', 'conductivityYY':'W/m-K', 'conductivityZZ':'W/m-K', 'reflection_coeff':'', 
            'emissivity':'', 'max_height':'m', 'thickness':'m'}
    
    # Distribute isotropic properties to directional properties
    for matl in self.stackup['Materials']:
      if 'conductivity' in matl:
        matl['conductivityXX'] = matl['conductivity']
        matl['conductivityYY'] = matl['conductivity']
        matl['conductivityZZ'] = matl['conductivity']
    
    # Report input units
    for matl in self.stackup['Materials']:
      for prop in cols:
        if units[prop] != '' and prop in matl:
          print "Material " + matl['name'] + " entry " + prop + " is: " + matl[prop] + " desired units are: " + units[prop]   
        
    # Convert units   
    # u= Units.Units()
    for matl in self.stackup['Materials']:
      for prop in cols:
        if prop in matl:
          if prop not in units:
            propValue= matl[prop]
            propUnits= ''
          elif units[prop] == '':
            propValue= matl[prop]
            propUnits= ''
          else:
            print "matl[prop]: " + str(matl[prop])
            print " prop: " + str(prop)
            print " desired units: " + str(units[prop])
            propValue, propUnits=  Units.Units.convertUnits(matl[prop], units[prop])
            print "Material " + matl['name'] + " entry " + prop + " is: " + str(propValue) + ' ' + units[prop]  
          matl[prop]= propValue
        else:
          matl[prop]= '-'

    out= h.h3('Properties')
    matlHtml= ''

    row= ''
    for prop in cols:
      row += h.tdh(prop)
    matlHtml += h.tr(row)
    
    row= ''
    for prop in cols:
      row += h.tdh(units[prop])
    matlHtml += h.tr(row)    
    
    for matl in self.stackup['Materials']:
      row= ''
      for prop in cols:
        if prop in matl:
          if prop == 'name':
            row += h.tdh(matl[prop])
          else:
            row += h.td(matl[prop])
        else:
          row += h.td('&nbsp;')
      matlHtml += h.tr(row)
      
    return out + h.table(matlHtml)
    
  def viasStr(self):
    return "Via properties"
    
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