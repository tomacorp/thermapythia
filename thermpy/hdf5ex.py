
"""
Program to test hdf5 functionality.
It works.
"""

import numpy as np
import h5py
import matplotlib.pyplot as plt
import subprocess, os

def writeHdf5(filename):
  f=h5py.File(filename, "w")
  sampleValues= np.array([1.1,17.0,6.2])
  f["sampleValues"]= sampleValues
  f.close()

def dumpHdf5(filename):
  """Method to execute xyce"""
  h5dumpBin = "/usr/local/bin/h5dump"
  h5dumpCmd = [h5dumpBin, filename]
  thisEnv = os.environ.copy()
  proc= subprocess.Popen(h5dumpCmd, env=thisEnv)
  return proc

def readHdf5(filename):
  f=h5py.File(filename, "r")
  data= f['sampleValues']
  print "sampleValues"
  for v in data:
    print v
  print "Done"
  f.close()

def main():
  filename= "hdf5ex_dat.hdf5"
  writeHdf5(filename)
  proc= dumpHdf5(filename)
  proc.wait()
  readHdf5(filename)
  
main()


