{

  "showProfile": 1,
  "debug": 1,
  "layers_config": "layers.js",
  "matls_config": "matls.js",
  "vias_config": "vias.js",
  "mesh_config": "mesh.js",
  
  

  "profileFilename": "profile.txt",
  "webPageFileName": "stackup.html",
  "http": {
    "httpPort": 8880,
    "useHttp": 1,
    "popBrowser": 1
  },
  
  
  
  
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
        "active": 0      
      },
      {
        "solverName": "Amesos",
        "active": 1      
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
  }



}