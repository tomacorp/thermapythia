#!/Users/toma/python278i/bin/python
# Tom Anderson
# Thermal simulation prototype
# Sun Jul 13 22:30:26 PDT 2014
 
import matplotlib.pyplot as plt
import numpy as np

# Construction


from PyTrilinos import Epetra, AztecOO

# Layers
class Layers:
  def __init__(self):
    self.iso = 0
    self.heat = 1
    self.resis = 2
    self.deg = 3
    self.flux = 4

# Convergence monitor
class Monitors:
  def __init__(self):
    self.maxtemp = -273
    self.powerin = 0
    self.powerout = 0

# Mesh the field
class Mesh:
  def __init__(self, w, h):
    self.width = 25
    self.height = 20
    self.width = w
    self.height = h
    self.field = np.zeros((self.width+1,self.height+1,5), dtype = 'double')
    self.xr, self.yr= np.mgrid[:self.width+1, :self.height+1]

    
def aztecsolve(lyr, mesh, monitor):
  # define the communicator (Serial or parallel, depending on your configure
  # line), then initialize a distributed matrix of size 4. The matrix is empty,
  # `0' means to allocate for 0 elements on each row (better estimates make the
  # code faster). `NumMyElements' is the number of rows that are locally hosted 
  # by the calling processor; `MyGlobalElements' is the global ID of locally 
  # hosted rows.
  Comm              = Epetra.PyComm()
  NumGlobalElements = 5
  Map               = Epetra.Map(NumGlobalElements, 0, Comm)
  A                 = Epetra.CrsMatrix(Epetra.Copy, Map, 0)
  NumMyElements     = Map.NumMyElements()
  MyGlobalElements  = Map.MyGlobalElements()
  print "MyGlobalElements =", MyGlobalElements

  # Solution for voltage source: 10, 4.1803, 1.7213,  1.475
  # Solution for current source:  0, 1.475,  5.901,   9.344
  # Total solution:              10, 5.656,  7.6133, 10.819

  R1 = 10.0
  R2 = 10.0
  R3 = 15.0
  R4 = 15.0
  R5 = 5.0
  R6 = 30.0

  # A is the problem matrix
  # Modified nodal analysis
  # http://www.swarthmore.edu/NatSci/echeeve1/Ref/mna/MNA2.html
  # node 0
  A[0, 0] = 1/R1
  # node 1
  A[1, 1] = 1/R1 + 1/R2 + 1/R3
  # node 2
  A[2, 2] = 1/R3 + 1/R4 + 1/R5
  # node 3
  A[3, 3] = 1/R5 + 1/R6
  # Common node impedances
  A[0, 1] = -1/R1
  A[1, 0] = -1/R1
  A[1, 2] = -1/R3
  A[2, 1] = -1/R3
  A[2, 3] = -1/R5
  A[3, 2] = -1/R5
  # Independent voltage source into node 0
  A[0, 4] = 1
  A[4, 0] = 1

  # b is the RHS
  b = Epetra.Vector(Map)
  b[0] = 0
  b[1] = 0
  b[2] = 0
  # This is the only term for a 1A current source injected into node 3
  b[3] = 1
  # This is the 10V voltage source going into node 0.
  # Current going in to the arrow of this source is in the solution as x[4]
  # In this example, the current flows in the direction of the arrow on the current source,
  # so the solution to the current is negative.
  b[4] = 10

  # x are the unknowns to be solved.
  x = Epetra.Vector(Map)
  
  A.FillComplete()

  solver = AztecOO.AztecOO(A, x, b)

  # This loads x with the solution to the problem
  solver.Iterate(1550, 1e-5)

  Comm.Barrier()

  for i in MyGlobalElements:
    print "PE%d: %d %e" % (Comm.MyPID(), i, x[i])
  
  # synchronize processors
  Comm.Barrier()

  if Comm.MyPID() == 0: print "End Result: TEST PASSED"

# This can scale by using a PNG input
def defineproblem(lyr, mesh):

  mesh.field[:, :, lyr.heat]  = 0.0
  mesh.field[:, :, lyr.resis] = 0.1
  mesh.field[:, :, lyr.iso]   = 0.0
  mesh.field[:, :, lyr.deg]   = 23
  mesh.field[:, :, lyr.flux]  = 0.0
  
  # Heat source
  hsx= 0.5
  hsy= 0.5
  hswidth= 0.25
  hsheight= 0.25
  srcl= round(mesh.width*(hsx-hswidth*0.5))
  srcr= round(mesh.width*(hsx+hswidth*0.5))
  srct= round(mesh.height*(hsy-hsheight*0.5))
  srcb= round(mesh.height*(hsy+hsheight*0.5))
  mesh.field[srcl:srcr, srct:srcb, lyr.heat] = 5.0
  mesh.field[srcl:srcr, srct:srcb, lyr.resis] = 10.0
  
  # Boundary conditions
  mesh.field[0, 0:mesh.height-1, lyr.iso] = 1.0
  mesh.field[mesh.width-1:mesh.width, 0:mesh.height-1, lyr.iso] = 1.0
  mesh.field[0:mesh.width-1, 0, lyr.iso] = 1.0
  mesh.field[0:mesh.width-1, mesh.height-1, lyr.iso] = 1.0
  
  # Thermal conductors
  condwidth= 0.05
  cond1l= round(mesh.width*hsx - mesh.width*condwidth*0.5)
  cond1r= round(mesh.width*hsx + mesh.width*condwidth*0.5)
  cond1t= round(mesh.height*hsy - mesh.height*condwidth*0.5)
  cond1b= round(mesh.height*hsy + mesh.height*condwidth*0.5)
  mesh.field[0:mesh.width, cond1t:cond1b, lyr.resis] = 10.0
  mesh.field[cond1l:cond1r, 0:mesh.height, lyr.resis] = 10.0

# This can scale by using a PNG output
def plotsolution(lyr, mesh):
  z1= mesh.field[:, :, lyr.flux];
  z2= mesh.field[:, :, lyr.deg];

  plt.figure(1)
  plt.subplot(1,1,1)
  plt.axes(aspect=1)
  quad= plt.pcolormesh(mesh.xr, mesh.yr, z1)
  plt.colorbar()
  plt.draw()
  
  plt.figure(2)
  plt.subplot(1,1,1)
  plt.axes(aspect=1)
  quad2= plt.pcolormesh(mesh.xr, mesh.yr, z2)
  plt.colorbar()
  plt.draw()
  plt.show()

def gsitersolve(lyr, mesh, monitor):
  finished = 0
  iter = 0
  while ((iter < 1200) and (finished == 0)):
    monitor.powerout = 0
    monitor.powerin = 0
    delta= simstep(iter, lyr, mesh, monitor)
    print iter, delta, monitor.maxtemp, monitor.powerin, monitor.powerout
    powerbalance= (monitor.powerout - monitor.powerin)/(monitor.powerout+monitor.powerin)
    if ((iter > 10) and (abs(powerbalance) < .005)):
      finished = 1
    iter = iter + 1

# This will become a pytrilinos solver
def simstep(iter, lyr, mesh, monitor):
  maxdelta= 0;
  mesh.field[:, :, lyr.flux] = 0.0
  for x in range(1, mesh.width-1):
    for y in range(1, mesh.height-1):
      if (mesh.field[x , y, lyr.iso] != 1.0):
        resisl= mesh.field[x - 1, y, lyr.resis]
        resisr= mesh.field[x + 1, y, lyr.resis]
        resisu= mesh.field[x, y - 1, lyr.resis]
        resisd= mesh.field[x, y + 1, lyr.resis]
        tresis= resisl+resisr+resisu+resisd
        degl= mesh.field[x - 1, y, lyr.deg]
        degr= mesh.field[x + 1, y, lyr.deg]
        degu= mesh.field[x, y - 1, lyr.deg]
        degd= mesh.field[x, y + 1, lyr.deg]
        
        if (tresis > 0):
          prevdeg = mesh.field[x, y, lyr.deg]
          powerincell = mesh.field[x, y, lyr.heat]
          monitor.powerin = monitor.powerin + powerincell
          newdeg = (powerincell + ( degl*resisl + degr*resisr + degu*resisu + degd*resisd ))/tresis

          poweroutcell = 0.0
          fluxl= (prevdeg - degl) * resisl
          fluxr= (prevdeg - degr) * resisr
          fluxu= (prevdeg - degu) * resisu
          fluxd= (prevdeg - degd) * resisd

          if (mesh.field[x - 1 , y, lyr.iso] == 1.0):
            poweroutcell = poweroutcell + fluxl
          if (mesh.field[x + 1 , y, lyr.iso] == 1.0):
            poweroutcell = poweroutcell + fluxr
          if (mesh.field[x , y - 1, lyr.iso] == 1.0):
            poweroutcell = poweroutcell + fluxu
          if (mesh.field[x , y + 1, lyr.iso] == 1.0):
            poweroutcell = poweroutcell + fluxd

          mesh.field[x - 1 , y, lyr.flux] += abs(fluxl)
          mesh.field[x + 1 , y, lyr.flux] += abs(fluxr)
          mesh.field[x, y - 1, lyr.flux] += abs(fluxu)
          mesh.field[x, y + 1, lyr.flux] += abs(fluxd)
          
          mesh.field[x, y, lyr.deg]= newdeg;

          if (maxdelta < abs(prevdeg - newdeg)):
            maxdelta = abs(prevdeg - newdeg)
          if (monitor.maxtemp < newdeg):
            monitor.maxtemp = newdeg

          monitor.powerout = monitor.powerout + poweroutcell
  return maxdelta

lyr = Layers()
monitor = Monitors()
mesh = Mesh(25, 20)

defineproblem(lyr, mesh)
gsitersolve(lyr, mesh, monitor)
plotsolution(lyr, mesh)

aztecsolve(lyr, mesh, monitor)

