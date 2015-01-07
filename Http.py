from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.internet import reactor
from twisted.web.resource import NoResource
from twisted.web import server, resource, static

import cgi
from calendar import calendar


# TODO: Hook up the other images in interactivePlot, and display
# them in an HTML page here.

class HTMLPreformattedTextFile(Resource):
  def getChild(self, filename, request):
    # Should check that the file exists here
    # Also make the filename into a fully configured path
    # Handle exceptions with error codes.
    self.filename= filename
    return FileContents(filename)
    
class FileContents(Resource):
  def __init__(self, filename):
    Resource.__init__(self)
    self.filename= filename
    
  def render_GET(self, request):
    with open (self.filename, "r") as htmlFileHandle:
      fileContents= htmlFileHandle.read()
    return "<html><body><pre>%s</pre></body></html>" % (fileContents)



class Calendar(Resource):
  def getChild(self, name, request):
    try:
      year = int(name)
    except ValueError:
      return NoResource()
    else:
      return YearPage(year)
    
class YearPage(Resource):
  def __init__(self, year):
    Resource.__init__(self)
    self.year = year

  def render_GET(self, request):
    return "<html><body><pre>%s</pre></body></html>" % (calendar(self.year),)



class FormPage(Resource):
  def render_GET(self, request):
    return '<html><body><form method="POST"><input name="the-field" type="text" /></form></body></html>'

  def render_POST(self, request):
    return '<html><body>You submitted: %s</body></html>' % (request.args["the-field"][0])

class FormPageEscaped(Resource):
  def render_GET(self, request):
    return '<html><body><form method="POST"><input name="the-field" type="text" /></form></body></html>'

  def render_POST(self, request):
    return '<html><body>You submitted: %s</body></html>' % (cgi.escape(request.args["the-field"][0]),)

class Stop(Resource):
  def render_GET(self, request):
    reactor.callFromThread(reactor.stop)
    
    
# TODO: At some point this should be in a file, and also styled with CSS
    
    
class Index(Resource):
  def render_GET(self, request):
    return """<html><head><title>Main</title></head><body>
    <ul>
    <li><a href="cal/2015">2015</a></li>
    <li><a href="stop">Stop</a></li>
    <li><a href="htmlfile/result.html">Matrix with diagnostics</a></li>
    <li><a href="htmlfile/diri_AxRHS.html">Matrix solution</a></li>
    <li><a href="thermpypng/aztecOO_heat_map.png">Saved bitmaps</a>
    </ul>
    
    <img src="thermpypng/aztecOO_heat_map.png"><br />
    <img src="thermpypng/difference_heat_map.png"><br />
    
    </body></html>
    """

class Http:
  
  def __init__(self, config):
    if config['http']['useHttp'] == 1:
      self.config= config
      self.startServer()

  def startServer(self):
    print "Calling web server start"
        
    self.port = self.config['http']['httpPort']
    self.root = Resource()
    self.root.putChild("cal", Calendar())
    self.root.putChild("formesc", FormPageEscaped())
    self.root.putChild("form", FormPage())
    self.root.putChild("stop", Stop())
    self.root.putChild("htmlfile", HTMLPreformattedTextFile())
    # pngdir= '/Users/toma/tools/trilinos/pytrilinos/matrixmnodal/thermpypng'
    pngdir= 'thermpypng'
    self.root.putChild("thermpypng", File(pngdir, defaultType="image/png"))
    
    self.root.putChild("", Index())
      
    self.factory = Site(self.root)
    reactor.listenTCP(self.port, self.factory)
    print "Starting reactor on localhost:" + str(self.port)
    reactor.run()
    print "Reactor is finished"
    print "Done with http server"
