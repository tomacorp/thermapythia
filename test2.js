{


  "showProfile": 1,
  "profileFilename": "profile.txt",
  "webPageFileName": "stackup.html",
  "debug": 1,
  "layers_config": "layers.js",
  "matls_config": "matls.js",
  "vias_config": "vias.js",

  
  "http": {
    "httpPort": 8880,
    "useHttp": 1,
    "popBrowser": 1
  },

  "simulation_layers": [
    { "index": 0, "type":"double", "name": "iso"          },
    { "index": 1, "type":"double", "name": "heat"         },
    { "index": 2, "type":"double", "name": "resis"        },
    { "index": 3, "type":"double", "name": "deg"          },
    { "index": 4, "type":"double", "name": "isodeg"       },
    { "index": 5, "type":"double", "name": "spicedeg"     },
    { "index": 6, "type":"double", "name": "npdeg"        },
    { "index": 7, "type":"double", "name": "boundCond"    },
    { "index": 0, "type":"int",    "name": "isonode"      },
    { "index": 1, "type":"int",    "name": "isoflag"      },
    { "index": 2, "type":"int",    "name": "spicenodenum" },
    { "index": 3, "type":"int",    "name": "holeflag"     }
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
       "png": ["deg", "holeflag","heat","resis","isodeg","isoflag","spicenodenum"],
       "interactive": []
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
  }

}