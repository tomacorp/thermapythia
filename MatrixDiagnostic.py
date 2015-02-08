import numpy as np
import Html
class MatrixDiagnosticWebpage:

  def __init__(self, solv, lyr, mesh):
    self.html    = ''
    self.solver = solv
    self.lyr = lyr
    self.mesh = mesh
    self.maxWebPageSize = 122
    
  def createWebPage(self):
    matrixSize= self.mesh.solveTemperatureNodeCount()
    if matrixSize > self.maxWebPageSize:
      print "Web page skipped because problem size is " + matrixSize + " which is larger than limit " + self.maxWebPageSize
      return
    print "Creating web page"
    np.set_printoptions(threshold='nan', linewidth=10000)
    f= open(self.solver.debugWebPage, 'w')
    self.webpage()
    f.write(self.html)
    f.close()  
    
  def webpage(self):
    h = Html.Html()
    matrix= ''
    rhsStr= ''
    xhtml= ''
    col= 0
    cols= '* '
  
    rowType = ''
    for n in range(0, self.solver.NumGlobalElements):
      nodeType= 'matl'
      rowType = rowType + "<td>" + nodeType + "</td>"
  
    #rowX = ''
    #for n in range(0, self.solver.NumGlobalElements):
      #x = self.mesh.getXAtNode(n)
      #rowX = rowX + "<td>" + str(x) + "</td>"
    #rowY = ''
    #for n in range(0, self.solver.NumGlobalElements):
      #y = self.mesh.getYAtNode(n)
      #rowY = rowY + "<td>" + str(y) + "</td>"
  
    # Create matrix table
    for x in range(0, self.solver.NumGlobalElements):
      rhsStr = rhsStr + "<td>" + str("%.3f" % self.solver.bs[x]) + "</td>"
      matrix_row = ''
      for y in range(0, self.solver.NumGlobalElements):
        if self.solver.As[x,y] != 0.0:
          elt= str("%.3f" % self.solver.As[x,y])
        else:
          elt= '.'
        matrix_row = matrix_row + "<td>" + elt + "</td>"
      matrix= matrix + "<tr>" + matrix_row + "</tr>"
      cols = cols + "<td>" + str(col) + "</td>"
      col = col + 1
    matrix = "<table>" + matrix + "</table>"
    
    mostCommon= self.solver.nonzeroMostCommonCount()
  
    # Create vector table
    vectors =           "<tr><td><b>col</b></td>" + cols + "</tr>"
    #vectors = vectors + "<tr><td><b>X</b></td>" + rowX + "</tr>"
    #vectors = vectors + "<tr><td><b>Y</b></td>" + rowY + "</tr>"
    vectors = vectors + "<tr><td><b>Type</b></td>" + rowType + "</tr>"
    vectors = vectors + "<tr><td><b>rhs</b></td>" + rhsStr + "</tr>"
    vectors = vectors + "<tr><td><b>lhs</b></td>" + xhtml + "</tr>"
    vectors = "<table>" + vectors + "</table>"
  
    # Counts
    counts = "<tr><td>BodyNodeCount</td><td>" + str(self.solver.BodyNodeCount) + "</td></tr>"
    counts += "<tr><td>BoundaryNodeCount</td><td>" + str(self.solver.BoundaryNodeCount) + "</td></tr>"
    counts += "<tr><td>Matrix Size</td><td>" + str(self.solver.NumGlobalElements) + "</td></tr>"
    counts += "Total number of independent nodes= " + str(self.mesh.nodeCount) + "<br/>"
    counts += "Most Common number of nonzero matrix entries per row= " + str(mostCommon) + "<br/>"
    counts = "<table>" + counts + "</table>"
    
    descr = """ 
    <pre>
    The total number of rows in A is self.nodeCount
    The solution to the matrix is the vector x. These are voltages (temperature)
    For energy balance in steady state, the current into the constant-temperature boundary condition 
    must equal the current from the constant-power thermal sources.
    </pre>
    """
  
    # Create web page
    head  = h.title("Matrix output")
    body  = h.h1("Ax = b")
    body += h.h3("A Matrix")
    body += h.pre(matrix)
    body += h.h3("Vectors")
    body += h.pre(vectors)
    body += h.h3("Counts")
    body += h.pre(counts) + descr
    self.html= h.html(h.head(head) + h.body(body))  
 