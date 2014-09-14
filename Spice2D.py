import subprocess, os
class Spice:
  def __init__(self, solver):
    self.solver= solver
    self.simbasename= 'therm'
    self.ckiname= self.simbasename + '.cki'
    self.ascname= self.simbasename + '.asc'
    self.txtname= self.simbasename + '.txt'
    self.sampleTime = 0.1
    
  def createSpiceNetlist(self):
    """Method to write a spice deck based on what was loaded by the solver"""
    f= open(self.simbasename + '.cki', 'w')
    f.write("* Thermal network\n")
    f.write(self.solver.deck)
    f.write(".tran .1 " + str(self.sampleTime) + "\n")
    f.write(".print tran\n")
    f.write(".end\n")
    f.close()
      
  def runSpiceNetlist(self):
    """Method to execute xyce"""
    xycePath = "/usr/local/Xyce-Release-6.1.0-OPENSOURCE/bin"
    xyceCmd = [xycePath + "/runxyce", self.ckiname, "-a", "-r", self.ascname, "-l", self.txtname]
    thisEnv = os.environ.copy()
    thisEnv["PATH"] = xycePath + ":" + thisEnv["PATH"]
    proc= subprocess.Popen(xyceCmd, env=thisEnv)
    return proc
    
  def readSpiceResults(self, lyr, mesh):
    """Method to read results from spice simulation"""
    f= open(self.simbasename + '.asc', 'r')
    # Header
    for line in f:
      if (line == 'Variables:\n'):
        break      
      (name, val)= line.strip().split(': ')
      print "Name: " + name + ", val: " + val

    # Variable names and their indexes
    for line in f:
      if (line == 'Values:\n'):
        break
      (idx, nodename, nodetype)= line.strip().split('\t')
      spiceRawIdx= int(idx)
      if (nodetype == 'time'):
        continue
      nodeIdx= spiceRawIdx - 1
      if (nodename in mesh.spiceNodeXName):
        print nodename + ": " + str(nodeIdx) + " " + str(mesh.spiceNodeXName[nodename]) + " " + str(mesh.spiceNodeYName[nodename])
        mesh.spiceNodeX.append(mesh.spiceNodeXName[nodename])
        mesh.spiceNodeY.append(mesh.spiceNodeYName[nodename])

    # ASCII data
    atSampleTime= False
    inTimePoint = True
    idx= 0
    for line in f:
      if (atSampleTime == True):
        voltage= line.strip()
        if (line == '\n'):
          break
        if (idx < len(mesh.spiceNodeX)):
          # TODO: Add to mesh layer here for visualization.
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

    f.close()
