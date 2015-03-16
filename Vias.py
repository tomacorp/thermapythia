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

class Vias(PCModel):

    def __init__(self, stackup_config):

        self.stackup_js_fn= stackup_config['stackup_config']
        with open (self.stackup_js_fn, "r") as jsonHandle:
            jsonContents= jsonHandle.read()

        self.stackup= yaml.load(jsonContents)
        # print yaml.dump(self.stackup)

        self.vias= self.stackup['Vias']

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
                        if thisMaterialName in matl.matlDict:
                            row += h.tdc(via[prop], matl.matlDict[thisMaterialName]['color'])
                        else:
                            print "Via material " + str(thisMaterialName) + " not found for via " + str(vianame)
                            row += h.tdc(str(thisMaterialName), 'red')
                    elif prop == 'to':
                        toLayer= via[prop]
                        if toLayer in lyr.layerDict:
                            row += h.td(toLayer)
                        else:
                            print "Via 'to' layer " + str(toLayer) + " not found for via " + str(vianame)
                            row += h.tdc(str(toLayer), 'red')
                    elif prop == 'from':
                        fromLayer= via[prop]
                        if fromLayer in lyr.layerDict:
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