import re
from pint import UnitRegistry

class Units:
  def __init__(self):  
    # TODO: Switch to using this class, also see python Decimal.quantize
    # Decimal.to_eng_string, 
    # http://stackoverflow.com/questions/15733772/convert-float-number-to-string-with-engineering-notation-with-si-prefixe-in-py/15734251#15734251
    self.ureg = UnitRegistry()
    self.Q_ = self.ureg.Quantity
    return
  
  """
  FIXME: Figure out how to call class methods without Units.Units.convertUnits.  
  """
  
  @classmethod
  def convertToMeters(cls, length, unit):
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
  
  
  # TODO: Convert convertToMeters to a class method, fix calling code.
  @classmethod
  def unitIsLength(cls, unit):
    if unit == "m" or unit == "mil" or unit == "mm" or unit == "cm" or unit == "in":
      return True
    else:
      return False
  
  @classmethod
  def convertUnits(cls, inputString, desiredUnits):
# TODO Parse inputString and convert the numeric part from the embedded units to the desired units.
#      Return the equivalent value in the desired units as a float.  
    # m=re.compile('([-+0-9e]+)(.*)')
    vals = re.match('([-+.0-9e]+)(.*)', inputString)
    if (vals != None):
      inputValue= float(vals.group(1))
      inputUnits= vals.group(2)
      if (inputUnits == desiredUnits or inputUnits == ''):
        return (inputValue, inputUnits)
      else:
        # TODO: Convert units here
        # print "CONVERT: " + inputUnits + " to " + desiredUnits
        if cls.unitIsLength(inputUnits):
          return (cls.convertToMeters(inputValue, inputUnits), 'm')
        else:
          print "CONVERT: UNREGOGNIZED UNITS: " + inputUnits
      return (inputValue, inputUnits)
    return (0.0, '?')