import numpy as np
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
    matrix= ''
    rhsStr= ''
    xhtml= ''
    col= 0
    cols= '* '
  
    temperatureStartNode= 0
    temperatureEndNode= self.mesh.solveTemperatureNodeCount()
    dirichletStartNode= temperatureEndNode
    dirichletEndNode= dirichletStartNode + self.mesh.boundaryDirichletNodeCount(self.lyr)
  
    rowType = ''
    for n in range(0, self.solver.NumGlobalElements):
      nodeType= '?'
      if ((n >= temperatureStartNode) and (n < temperatureEndNode)):
        nodeType= 'matl'
      else:
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
  
    # Create web page
    head  = "<title>Matrix output</title>"
    body  = "<h1>Ax = b</h1>"
    body += "<h3>A Matrix</h3>"
    body += "<pre>" + matrix + "</pre>"
    body += "<h3>Vectors</h3>"
    body += "<pre>" + vectors + "</pre>"
    body += "<h3>Counts</h3>"
    body += "<pre>" + counts + "</pre>"
    self.html= "<html><head>" + head + "</head><body>" + body + "</body></html>"  