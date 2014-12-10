import numpy as np

# 
# Example header for matrix of 16 x 16 reals
# %%MatrixMarket matrix coordinate real general
# 16 16 32

# Example header for array of 16 reals
# %%MatrixMarket matrix array real general
# 16 1

class MatrixMarket:
    def __init__(self):
        self.verbose= False
        return
    
    def read(self, fn):
        self.fn= open(fn, mode='r')
        self.lines = self.fn.readlines()
        self.readHeader()
        if self.shape == 'coordinate':
            return self.readMatrix()
        elif self.shape == 'array':
            return self.readArray()
        return None
    
    def readHeader(self):
        headerMetaLine= self.lines[0]
        headerVals = headerMetaLine.split(' ');
        self.filetype= headerVals[0]
        if self.filetype != '%%MatrixMarket':
            print "File " + self.fn + ' is not a MatrixMarket file'
            self= None
            return
        self.shape= headerVals[2]
        
        headerSizeLine= self.lines[1]
        headerSizeVals= headerSizeLine.split(' ')
        
        if self.shape == 'coordinate':
            self.dim= 2
            self.xsize= int(headerSizeVals[0])
            self.ysize= int(headerSizeVals[1])
            self.entries= int(headerSizeVals[2])
        elif self.shape == 'array':
            self.dim=1
            self.entries = int(headerSizeVals[0])
        else:
            print "Unrecognized datashape " + self.shape
            
        self.datatype= headerVals[3]
        return
    
    def readMatrix(self):
        if self.verbose:
            print "Matrix has " + str(self.entries) + " entries"
        self.fullMatrix = np.empty((self.xsize, self.ysize))
        self.fullMatrix.fill(0.0)        
        for lineIndex in range(2, self.entries + 2):
            # print "Matrix Line: " + str(lineIndex) + ' ' + self.lines[lineIndex]
            lineDataString= self.lines[lineIndex]
            lineData= lineDataString.split(' ')
            xIndex= int(lineData[0])-1
            yIndex= int(lineData[1])-1
            floatingData= float(lineData[2])
            self.fullMatrix[xIndex][yIndex]= floatingData
        return self
    
    def readArray(self):
        if self.verbose:
            print "Array has " + str(self.entries) + " entries"
        self.fullArray = np.empty(self.entries)
        self.fullArray.fill(0.0)        
        idx= 0
        for lineIndex in range(2, self.entries + 2):        
            # print "Array Line: " + str(lineIndex) + ' ' + self.lines[lineIndex]
            self.fullArray[idx]= float(self.lines[lineIndex])
            idx = idx + 1
        return self
    
if __name__ == "__main__":
    MM= MatrixMarket()
    mmDataArray= MM.read('mmRHS.mm')
    mmDataMatrix= MM.read('mmA.mm')