import numpy as np
import Html
class MatrixDiagnosticWebpage:

  def __init__(self, solv, lyr, mesh):
    self.html    = ''
    self.solver = solv
    self.lyr = lyr
    self.mesh = mesh
    self.maxWebPageSize = 100
    
  def createWebPage(self):
    matrixSize= self.mesh.solveTemperatureNodeCount()
    if matrixSize > self.maxWebPageSize:
      print "Web page skipped because problem size is " + matrixSize + " which is larger than limit " + self.maxWebPageSize
      return
    print "Creating web page"
    np.set_printoptions(threshold='nan', linewidth=10000)
    f= open('result.html', 'w')
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
  
    temperatureStartNode= 0
    temperatureEndNode= self.mesh.solveTemperatureNodeCount()
    # For the NORTON formulation these will not be needed.
    dirichletStartNode= temperatureEndNode
    dirichletEndNode= dirichletStartNode + self.mesh.boundaryDirichletNodeCount(self.lyr)
  
    rowType = ''
    for n in range(0, self.solver.NumGlobalElements):
      nodeType= '?'
      if ((n >= temperatureStartNode) and (n < temperatureEndNode)):
        nodeType= 'matl'
      else:
        # For the NORTON formulation these diri nodes will not be needed. 
        if ((n >= dirichletStartNode) and (n < dirichletEndNode)):
          nodeType = 'diri'
      rowType = rowType + "<td>" + nodeType + "</td>"
  
    rowX = ''
    for n in range(0, self.solver.NumGlobalElements):
      x = self.mesh.getXAtNode(n)
      rowX = rowX + "<td>" + str(x) + "</td>"
    rowY = ''
    for n in range(0, self.solver.NumGlobalElements):
      y = self.mesh.getYAtNode(n)
      rowY = rowY + "<td>" + str(y) + "</td>"
  
    # Create matrix table
    for x in range(0, self.solver.NumGlobalElements):
      rhsStr = rhsStr + "<td>" + str("%.3f" % self.solver.bs[x]) + "</td>"
   #   xhtml = xhtml + "<td>" + str("%.3f" % self.solver.x[x]) + "</td>"
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
    vectors = vectors + "<tr><td><b>X</b></td>" + rowX + "</tr>"
    vectors = vectors + "<tr><td><b>Y</b></td>" + rowY + "</tr>"
    vectors = vectors + "<tr><td><b>Type</b></td>" + rowType + "</tr>"
    vectors = vectors + "<tr><td><b>rhs</b></td>" + rhsStr + "</tr>"
    vectors = vectors + "<tr><td><b>lhs</b></td>" + xhtml + "</tr>"
    vectors = "<table>" + vectors + "</table>"
  
    # Counts
    counts = "<tr><td>BodyNodeCount</td><td>" + str(self.solver.BodyNodeCount) + "</td></tr>"
    counts += "<tr><td>TopEdgeNodeCount</td><td>" + str(self.solver.TopEdgeNodeCount) + "</td></tr>"
    counts += "<tr><td>RightEdgeNodeCount</td><td>" + str(self.solver.RightEdgeNodeCount) + "</td></tr>"
    counts += "<tr><td>BottomEdgeNodeCount</td><td>" + str(self.solver.BottomEdgeNodeCount) + "</td></tr>"
    counts += "<tr><td>LeftEdgeNodeCount</td><td>" + str(self.solver.LeftEdgeNodeCount) + "</td></tr>"
    counts += "<tr><td>TopLeftCornerNodeCount</td><td>" + str(self.solver.TopLeftCornerNodeCount) + "</td></tr>"
    counts += "<tr><td>TopRightCornerNodeCount</td><td>" + str(self.solver.TopRightCornerNodeCount) + "</td></tr>"
    counts += "<tr><td>BottomRightCornerNodeCount</td><td>" + str(self.solver.BottomRightCornerNodeCount) + "</td></tr>"
    counts += "<tr><td>BoundaryNodeCount</td><td>" + str(self.solver.BoundaryNodeCount) + "</td></tr>"
    counts += "<tr><td>Total NodeCount</td><td>" + str(self.solver.totalNodeCount()) + "</td></tr>"
    counts += "<tr><td>Matrix Size</td><td>" + str(self.solver.NumGlobalElements) + "</td></tr>"
  
    counts += "Number of independent nodes in G matrix= " + str(self.mesh.nodeGcount) + "<br/>"
    counts += "Number of independent nodes in GF matrix= " + str(self.mesh.nodeGFcount) + "<br/>"
    counts += "Number of independent nodes in GB matrix= " + str(self.mesh.nodeGBcount) + "<br/>"
    counts += "Number of independent nodes in D matrix= " + str(self.mesh.nodeDcount) + "<br/>"
    counts += "Total number of independent nodes= " + str(self.mesh.nodeCount) + "<br/>"
    counts += "Most Common number of nonzero matrix entries per row= " + str(mostCommon) + "<br/>"
    counts = "<table>" + counts + "</table>"
    
    # Description
    descr = """ 
    A matrix is in sections:
    
    <table border='2'>
      <tr>
        <td>GF</td><tr><td>GB</td><td>0</td>
      </tr>
        </td>
      <td>D</td>
    </tr>
    
    <tr><td>D^T</td><td>0</td></tr>
    </table>
    
    <table>
    <tr><td>G</td><td>Transconductance matrix</td>
        <td>The number of rows in G is self.nodeGcount .
        The first set of rows GF is for the square mesh elements.
        The second set of rows GB is for the boundary condition voltage source nodes.
        </td>
    </tr>
    <tr><td>B</td><td>Voltage sources</td>
        <td>The number of rows is the number of boundary condition mesh cells.
        </td>
    </tr>
    <tr><td>D^T</td><td>D Transpose</td><td></td></tr>
    <tr><td>C</td><td>Zeros</td><td></td></tr>
    </table>

    <pre>
    G is in two sections, which are the upper left GF (for field) and GB (for boundary)
    The analysis is of the form  Ax = b
    For rows in b corresponding to G,  
       b is the known value of the current (constant power in thermal circuits) sources
    For rows in b corresponding to D, (constant temperature boundary conditions) 
       b is the known value of temperature at the boundary.
    The number of rows in D is self.nodeDcount
    The number of rows in G is self.nodeGcount
    The number of rows in GF is self.nodeGFcount
    The number of rows in GB is self.nodeGBcount
    The total number of rows in A is self.nodeCount
  
    The solution to the matrix is the vector x
    For rows in x corresponding to G, these are voltages (temperature)
    For rows in x corresponding to D, these are currents (power flow) in the boundary condition.
  
    For energy balance in steady state, the current into the constant-temperature boundary condition 
    must equal the current from the constant-power thermal sources.
  
    The index of the last nodes in the G submatrix for the field plus one is the number
    of nodes in the field GF. Add the boundary nodes GB to G.
  
    Also count the number of boundary sources, which is the size of the D matrix.
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
 
