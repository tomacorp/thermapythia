class Html:
  
  def __init__(self):
    # Nothing to do
    return
    
  def td(self, x):
    return "<td>" + str(x) + "</td>"
  
  def tr(self, x):
    return "<tr>" + str(x) + "</tr>"
  
  def table(self, x):
    return "<table>" + str(x) + "</table>"
  
  def pre(self, x):
    return "<pre>" + str(x) + "</pre>"
  
  def h1(self, x):
    return "<h1>" + str(x) + "</h1>"
  
  def h2(self, x):
    return "<h2>" + str(x) + "</h2>"  
  
  def h3(self, x):
    return "<h3>" + str(x) + "</h3>"
  
  def html(self, x):
    return "<html>" + str(x) + "</html>"
  
  def head(self, x):
    return "<head>" + str(x) + "</head>"
  
  def body(self, x):
    return "<body>" + str(x) + "</body>"
  
  def title(self, x):
    return "<title>" + str(x) + "</title>"