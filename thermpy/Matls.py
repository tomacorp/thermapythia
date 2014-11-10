class Matls:
  def __init__(self):
    self.fr4Cond    = 1.0
    self.copperCond = 401.0
    
    self.boundCond = 1000.0
    
    self.fr4Thickmil = 59.0
    self.copperThickmil = 1.2
    self.fr4Thick= self.convertMilToMeters(self.fr4Thickmil)
    self.copperThick= self.convertMilToMeters(self.copperThickmil)
    print "Copper Thickness, meters: " + str(self.copperThick)
    print "FR4 Thickness, meters:" + str(self.fr4Thick)

    self.fr4ResistancePerSquare=  1.0 / (self.fr4Cond * self.fr4Thick)
    self.copperResistancePerSquare=  1.0 / (self.copperCond * self.copperThick)
    print "Copper layer thermal resistance per square: " + str(self.copperResistancePerSquare)
    print "FR4 layer thermal resistance per square: " + str(self.fr4ResistancePerSquare)
    
  def convertMilToMeters(self, mil):
    inches= mil / 1000.0 
    centimeters= inches * 2.54
    meters = centimeters / 100.0 
    return meters
    
    """ 
    
        Cu thermal conductivity: 401 W/(m degK)
        Cu thickness 1.2mil
        FR-4 thermal conductivity: 1W/(m degK)
        FR-4 thickness 59mil
        
        Thermal resistance
        
    Need units conversion, and to account for thicknesses of layers.
    
    """