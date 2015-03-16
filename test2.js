{


  "showProfile": 1,
  "profileFilename": "profile.txt",


  "simulation_layers": [
    { "index": 0, "type":"double", "name": "iso"          },
    { "index": 1, "type":"double", "name": "heat"         },# Routines shared among Materials, Layers, and Vias
    { "index": 2, "type":"double", "name": "resis"        },
    { "index": 3, "type":"double", "name": "deg"          },
    { "index": 4, "type":"double", "name": "isodeg"       },
    { "index": 5, "type":"double", "name": "spicedeg"     },
    { "index": 6, "type":"double", "name": "npdeg"        },
    { "index": 0, "type":"int",    "name": "isonode"      },
    { "index": 1, "type":"int",    "name": "isoflag"      },
    { "index": 2, "type":"int",    "name": "spicenodenum" },
    { "index": 3, "type":"int",    "name": "holeflag"     }
  ],
  
  "stackup": {
    "webPageFileName": "stackup.html",
    "debug": 1,
    "stackup_config": "matls.js",
  },
  
  
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
      "thickness_unit": "mil"# Routines shared among Materials, Layers, and Vias
    },
    { "name": "bound",
      "type": "solid",
      "xcond": 600.0,
      "xcond_unit": "W/mK",
      "ycond": 600.0,# Routines shared among Materials, Layers, and Vias
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
      "xsize":5,
      "ysize":5,
      "active":0
    },
    {
      "title":"Bitmap 2D thermal problem",
      "inputFile":"Layout4.png",
      "type":"png",
      "active":0
    },
    {
      "title":"Bitmap 2D thermal problem",
      "inputFile":"simple11.png",
      "type":"png",
      "active":0
    },
    {
      "title":"Bitmap 2D thermal problem",
      "inputFile":"yellow.png",
      "type":"png",
      "active":1
    },
    {
      "title":"Bitmap 2D thermal problem",
      "inputFile":"gimp_test1.png",
      "type":"png",
      "active":0
    }
  ],
  
  "solver": {  
    "solverFlags": [
      {
        "flag": "debug",
        "setting": 0
      },
      {
        "flag": "webPage",
        "setting": 0
      },
      {
        "flag": "matrixMarket",
        "setting": 0
      },
    ],
    "solvers": [
      {
        "solverName": "Spice",
        "active": 0,
        "simbasename": "norton"
      },
      {
        "solverName": "Eigen",
        "active": 0      
      },
      {
        "solverName": "Aztec",
        "active": 1      
      },
      {
        "solverName": "Amesos",
        "active": 0      
      },
      {
        "solverName": "Numpy",
        "active": 0      
      },
    ],
    "solverDebug":
    {
      "debugWebPage": "result.html",
      "mmPrefix": "diri_"
    }
  },


  "outputs": {
    "active": 1,
    "mesh": { 
       "png": ["holeflag","heat","resis","isodeg","isoflag","spicenodenum"],
       "interactive": ["deg"]
    },
    "deltamesh": {
       "interactive": [], 
       "png": []
    },
    "maskedmesh": {
       "interactive": ["deg"],
       "png": []
    },
    "outputDirectory": "thermpypng",
    'maskLayer': 'holeflag'
  },

  
  "http": {
    "httpPort": 8880,
    "useHttp": 1,
    "popBrowser": 1
  }
  

}