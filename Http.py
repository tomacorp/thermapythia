from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.internet import reactor
from twisted.web.resource import NoResource
from twisted.web import server, resource, static
import subprocess, os

import cgi
from calendar import calendar
from itertools import izip

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
    
    
# TODO: The Index should be in a file, and also styled with CSS
    
    
class Index(Resource):
  
  def pairwise(self, iterable):
      "s -> (s0,s1), (s2,s3), (s4, s5), ..."
      a = iter(iterable)
      return izip(a, a)    
  
  def __init__(self, config):
    self.config= config
    
  def render_GET(self, request):
    outputMeshList= ''

    if 'mesh' in self.config['outputs']:
      if 'png' in self.config['outputs']['mesh']:
        for png in self.config['outputs']['mesh']['png']:
          outputMeshList = outputMeshList + "<li><img src='thermpypng/" + png + "_heat_map.png' /></li>"

    if 'deltamesh' in self.config['outputs']:
      if 'png' in self.config['outputs']['deltamesh']:
      
        for out1, out2 in self.pairwise(self.config['outputs']['deltamesh']['png']):
          plotName= 'png' + '_' + out1 + '_' + out2
          outputMeshList = outputMeshList + "<li><img src='thermpypng/" + plotName + "_heat_map.png' /></li>"            
    
    return """
    <html>
    <head><title>Thermonous</title></head>
    <body>
    <ul>
    <li><a href="cal/2015">2015</a></li>
    <li><a href="stop">Stop</a></li>
    <li><a href="htmlfile/result.html">Matrix with diagnostics</a></li>
    <li><a href="htmlfile/diri_AxRHS.html">Matrix solution</a></li>
    %s
    </ul>
    <!-- <img src="thermpypng/aztecOO_heat_map.png"><br />
    <img src="thermpypng/difference_heat_map.png"><br /> -->
    </body>
    </html>
    """ % (outputMeshList)

class Http:
  
  def __init__(self, config):
    if config['http']['useHttp'] == 1:
      self.config= config
    print "Initializing web server"
    self.popBrowser= config['http']['popBrowser']
        
    self.port = self.config['http']['httpPort']
    self.uri = "http://localhost:" + str(self.port)
    self.root = Resource()
    self.root.putChild("cal", Calendar())
    self.root.putChild("formesc", FormPageEscaped())
    self.root.putChild("form", FormPage())
    self.root.putChild("stop", Stop())
    self.root.putChild("htmlfile", HTMLPreformattedTextFile())
    # Can use an absolute path or a relative path here
    # pngdir= '/Users/toma/tools/trilinos/pytrilinos/matrixmnodal/thermpypng'
    pngdir= 'thermpypng'
    self.root.putChild("thermpypng", File(pngdir, defaultType="image/png"))
    
    self.root.putChild("", Index(self.config))
      
    self.factory = Site(self.root)
    reactor.listenTCP(self.port, self.factory)
    
    
    # TODO: Add configuration variables for both starting
    # the web browser and the server. It should be possible
    # to run in a non-interactive batch mode without
    # needing to kill the server. In this mode, getting
    # an accurate set of profiling statistics and good
    # logging is useful.
    #   Option for starting a server
    #   Option for popping web browser
    #   Options for file logging
    #   Command line option for choosing JSON config files
    # Having more than one config file allows distinction
    # between simulator setup and problem to be solved.
    # This way one sim setups can be used across a suite
    # of problems.
    
  def startServer(self):
    print "Serving web pages on on " + self.uri
    reactor.run()
    print "http server has shut down"    

  def openWebBrowser(self, delay):
    if self.popBrowser == True:
      cmd= "sleep " + str(delay) + ' ; open "'+ self.uri + '"'
      subprocess.Popen(cmd,shell=True)