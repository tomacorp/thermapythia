
import yaml

class ParseSimFile:

# NORTON isonode layer will be eliminated.
# But NORTON with holes will need another layer.
  def exampleJSON(self):
    js= """
{
  "simulation_layers": [
    { "index": 0, "type":"double", "name": "iso"          },
    { "index": 1, "type":"double", "name": "heat"         },
    { "index": 2, "type":"double", "name": "resis"        },
    { "index": 3, "type":"double", "name": "deg"          },
    { "index": 4, "type":"double", "name": "flux"         },
    { "index": 5, "type":"double", "name": "isodeg"       },
    { "index": 6, "type":"double", "name": "spicedeg"     },
    { "index": 0, "type":"int",    "name": "isonode"      },
    { "index": 1, "type":"int",    "name": "isoflag"      },
    { "index": 2, "type":"int",    "name": "spicenodenum" }
  ],
  
  "layer_matl": [
    { "name": "fr4",
      "type": "solid",
      "xcond": 1.0,
      "xcond_unit": "W/mK",
      "ycond": 1.0,
      "ycond_unit": "W/mK",
      "thickness": 59.0,
      "thickness_unit": "mil"
    },
    { "name": "copper",
      "type": "solid",
      "xcond": 401.0,
      "xcond_unit": "W/mK",
      "ycond": 401.0,
      "ycond_unit": "W/mK",
      "thickness": 1.2,
      "thickness_unit": "mil"
    },
    { "name": "bound",
      "type": "solid",
      "xcond": 1000.0,
      "xcond_unit": "W/mK",
      "ycond": 1000.0,
      "ycond_unit": "W/mK",
      "thickness": 10,
      "thickness_unit": "mil"
    }
  ],
  
  "mesh": [
    {
      "title":"Tiny 2D thermal problem",
      "type":"tiny",
      "active":0
    },
    {
      "title":"Scalable 2D thermal problem",
      "type":"scalable",
      "xsize":6,
      "ysize":5,
      "active":1
    },
    {
      "title":"Bitmap 2D thermal problem",
      "file":"Layout4.png",
      "type":"png",
      "active":0
    }
  ],
  
  "solverFlags": [
    {
      "flag": "debug",
      "setting": 1
    },
    {
      "flag": "useNorton",
      "setting": 1
    }
  ],
  
  "solvers": [
    {
      "solverName": "Spice",
      "active": 1,
      "simbasename": "norton"
    },
    {
      "solverName": "Eigen",
      "active": 0      
    },
    {
      "solverName": "Aztec",
      "active": 0      
    },
    {
      "solverName": "Amesos",
      "active": 1      
    }
  ],

  "outputs": [
    {
      "name": "showPlots",
      "active": 1
    },
  ],
  

  "showProfile": 1,
  "profileFilename": "profile.txt",
  
  "solverDebug":
  {
    "debugWebPage": "result.html"
  },
  
  "http": {
    "httpPort": 8880,
    "useHttp": 1
  }
  

}

"""  
    return js
  
def Main():
  exampleJson= '["foo", {"bar":["baz", null, 1.0, 2]}]'
  print exampleJson
  x= yaml.load(exampleJson)
  print str(x)
  
  simConfig= ParseSimFile()
  jsonStr= simConfig.exampleJSON()

  js= yaml.load(jsonStr)
  print str(js)
  print str(js['outputs'][0]['name'])
  
if __name__ == '__main__':
  Main()
  