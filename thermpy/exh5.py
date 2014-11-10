#

import numpy as np
import h5py
import matplotlib.pyplot as plt

f = h5py.File("out.hdf5", 'r')
ds = f['/spiceplot/therm.asc']
samp= ds[14]
print samp[0]
time= ds['time']
last= time.item(time.size-1)
lastitem= time.size - 1

deg= ds['N2U2']
print deg.max(), deg.min(), deg.mean(), deg.item(lastitem)

plt.figure(1)
plt.subplot(1,1,1)
quad4= plt.plot(time, deg)
plt.title('Temperature versus time')
plt.draw()
plt.show()

