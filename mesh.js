{
  "Format": "Thermal analysis layers file",
  "Author": "Tom Anderson",
  "Creation_Date": "Thu Feb 19 23:46:29 PST 2015",
  "Description": "6 layer board",

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
  ]

}