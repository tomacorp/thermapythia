import subprocess, os
class Spice:
  def __init__(self, basename):
    self.simbasename= basename
    self.ckiname= self.simbasename + '.cki'
    self.ascname= self.simbasename + '.asc'
    self.txtname= self.simbasename + '.txt'
    self.sampleTime = 0.1
    self.debug = False
    self.startSpiceNetlist()
    
  def appendSpiceNetlist(self, str):
    self.f.write(str)
    
  def startSpiceNetlist(self):
    self.f= open(self.simbasename + '.cki', 'w')
    self.f.write("* Thermal network\n")
    self.fileIsFinished = False

  def finishSpiceNetlist(self):
    # self.f.write(".tran .1 " + str(self.sampleTime) + "\n")
    self.f.write(".op\n")
    # self.f.write(".print tran\n")
    self.f.write(".end\n")
    self.f.close()
    self.fileIsFinished= True
      
  def runSpiceNetlist(self):
    """Method to execute xyce"""
    if (not self.fileIsFinished):
      self.finishSpiceNetlist()
    xycePath = "/usr/local/Xyce-Release-6.1.0-OPENSOURCE/bin"
    xyceCmd = [xycePath + "/runxyce", self.ckiname, "-a", "-r", self.ascname, "-l", self.txtname]
    thisEnv = os.environ.copy()
    thisEnv["PATH"] = xycePath + ":" + thisEnv["PATH"]
    proc= subprocess.Popen(xyceCmd, env=thisEnv)
    return proc
  
#  def readOperatingPointSpiceResults(self, lyr, mesh):
#    """Method to read the DC operating point from an ASCII raw file"""
#    fraw = self.readAsciiRawHeader(mesh)
#    self.readDCOperatingPoint(fraw, mesh, lyr)
#    fraw.close()    
    
  def readSpiceRawFile(self, lyr, mesh):
    """
    Method to read results from spice transient analysis ASCII raw file.
    simulation. Captures a single point in time, at or near self.sampleTime.
    """
    fraw = self.readAsciiRawHeader(mesh)

    # self.readTransientTimePoint(fraw, mesh, lyr)
    self.readDCOperatingPoint(fraw, mesh, lyr)

    fraw.close()

  def readAsciiRawHeader(self, mesh):
    fraw= open(self.simbasename + '.asc', 'r')
    # Header
    for line in fraw:
      if (line == 'Variables:\n'):
        break      
      (name, val)= line.strip().split(': ')
      if (self.debug == True):
        print "Name: " + name + ", val: " + val

    # Variable names and their indexes

    for line in fraw:
      if (line == 'Values:\n'):
        break
      (idx, nodename, nodetype)= line.strip().split('\t')
      spiceRawIdx= int(idx)
      if (nodetype == 'time'):
        continue
      nodeIdx= spiceRawIdx - 1
      if (nodename in mesh.spiceNodeXName):
        if self.debug == True:
          print nodename + ": " + str(nodeIdx) + " " + str(mesh.spiceNodeXName[nodename]) + " " + str(mesh.spiceNodeYName[nodename])
        mesh.spiceNodeX.append(mesh.spiceNodeXName[nodename])
        mesh.spiceNodeY.append(mesh.spiceNodeYName[nodename])
    return fraw
  
  def readDCOperatingPoint(self, fraw, mesh, lyr):
    idx= 0
    # First point is just zeroes as a placeholder for time
    next(fraw)    
    for line in fraw:
      voltage= line.strip()
      if (line == '\n'):
        break
      if (idx < len(mesh.spiceNodeX)):
        # TODO: Add to mesh layer here for visualization.
        if self.debug == True:
          print str(idx) + ' ' + voltage + ' ' + str(mesh.spiceNodeX[idx]) + ' ' + str(mesh.spiceNodeY[idx])
        mesh.field[mesh.spiceNodeX[idx], mesh.spiceNodeY[idx], lyr.spicedeg] = voltage
        idx += 1
      continue

  def readTransientTimePoint(self, fraw, mesh, lyr):
    # ASCII data
    atSampleTime= False
    inTimePoint = True
    idx= 0
    for line in fraw:
      if (atSampleTime == True):
        voltage= line.strip()
        if (line == '\n'):
          break
        if (idx < len(mesh.spiceNodeX)):
          # TODO: Add to mesh layer here for visualization.
          if self.debug == True:
            print str(idx) + ' ' + voltage + ' ' + str(mesh.spiceNodeX[idx]) + ' ' + str(mesh.spiceNodeY[idx])
          mesh.field[mesh.spiceNodeX[idx], mesh.spiceNodeY[idx], lyr.spicedeg] = voltage
          idx += 1
        continue
      if (inTimePoint == True):
        (timeIteration, time)= line.strip().split('\t')
        # Capture data near the final timepoint only
        if (abs(float(time) - self.sampleTime) < self.sampleTime/1e4):
          atSampleTime= True
          continue
      if (line == '\n'):
        inTimePoint = True
        continue
      else:
        inTimePoint = False
