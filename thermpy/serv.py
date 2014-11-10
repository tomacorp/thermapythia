import cherrypy
from html import HTML

class HelloWorld(object):
  @cherrypy.expose
  def index(self):
    h = HTML()
    h.h1("Hello world")
    h.h2("And")
    h.h3("Bye")
    indexString= str(h)
    return indexString

if __name__ == '__main__':
   cherrypy.quickstart(HelloWorld())
