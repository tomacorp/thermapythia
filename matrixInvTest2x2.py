import numpy as np
from numpy.linalg import inv

def setupLHS():
    G1= 3.
    G2= 5.
    a = np.array([[G1+G2, -G2], [-G2, G2]])  
    return a

def setupRHS():
    I1= 2.
    I2= 7.    
    RHS= np.array([I1, I2])
    return RHS

def checkInverse(a, ainv):
    inverseOK= True
    if not np.allclose(np.dot(a, ainv), np.eye(2)):
        inverseOK= False
    if not np.allclose(np.dot(ainv, a), np.eye(2)):
        inverseOK= False
    if inverseOK:
        print "OK 1 - matrix inverse self-check"
    else:
        print "Not OK 1"

if __name__ == "__main__":
    a= setupLHS()
    RHS= setupRHS()
    
    ainv = inv(a) 
    checkInverse(a, ainv)
    
    therm= ainv * RHS
    V= np.dot(ainv, RHS)
    
    HeatSinkPerf= np.array([therm[0][0], therm[1][1]])
    
    V1RiseDueToI2= therm[0][1]
    V2RiseDueToI1= therm[1][0]
    
    print HeatSinkPerf[0], V1RiseDueToI2, V[0]
    print HeatSinkPerf[1], V2RiseDueToI1, V[1]  
    
    exactInverse= np.array([[1./3., 1./3.],[1./3., 8./15.]])
    
    if np.allclose(exactInverse, ainv):
        print "OK 2 - matrix inverse expected value"
    else:
        print "Not OK 2 - matrix inverse expected value"
    