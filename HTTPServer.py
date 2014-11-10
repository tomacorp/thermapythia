import CGIHTTPServer
import SocketServer

def main():
  PORT = 8080
  Handler = CGIHTTPServer.CGIHTTPRequestHandler
  httpd = SocketServer.TCPServer(("", PORT), Handler)
  
  print "serving at port", PORT
  httpd.serve_forever()

if __name__ == '__main__':
  main()