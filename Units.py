class Units:
  def __init__(self):
    return
  
  """
  FIXME: Figure out how to use a class method for this.  
  """
  
  def convertToMeters(self, length, unit):
    if unit == "m":
      return length
    if unit == "mil":
      inches= length / 1000.0 
      centimeters= inches * 2.54
      meters = centimeters / 100.0 
      return meters   
    if unit == "mm":
      meters= length / 1000.0
      return meters
    if unit == "cm":
      meters= length / 100.0
      return meters
    if unit == "in":
      centimeters= inches * 2.54
      meters = centimeters / 100.0 
      return meters
    if unit == "":
      print "Error: units not set in convertToMeters"
      meters= float('NaN')
      return meters    
    
    print "Error: unrecognized length unit in convertToMeters: " + unit
    meters= float('NaN')
    return meters