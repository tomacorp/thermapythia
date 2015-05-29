{
"Format": "Thermal analysis materials file",
"Author": "Tom Anderson",
"Creation_Date": "Thu Feb 19 23:46:29 PST 2015",
"Description": "6 layer board",

"Comment1": "
 # Layer stackup has different descriptions.
 # Similar to IPC-2581B, where the BOM View differs from the CAD View.
 # In this case there is a third view, which is the Thermal View.
 # There is no lowest level view where there is a common bottom level of the hierarchy from which all things can be constructed.
 ",
 
"matlsDebug": { "debugWebPage": "stackup.html" },


"Materials": [
{ "name":"Al", "conductivity":"150W/m-K", "specific_heat":"0.860J/gm-K", "type":"solid", "emissivity":"0.09", "reflection_coeff":"0.93", "density":"2.70gm/cc", "color":"Silver"},
{ "name":"Cu", "conductivity":"385W/m-K", "specific_heat":"0.385J/gm-K", "type":"solid", "emissivity":"0.15", "reflection_coeff":"0.63", "density":"8.93gm/cc", "color":"IndianRed"},
{ "name":"StainlessSteel", "conductivity":"", "specific_heat":"", "emissivity":"0.16", "type":"solid", "color":"Gold"},
{ "name":"Solder", "conductivity":"58W/m-K", "specific_heat":"0.23J/gm-K", "emissivity":"0.06", "reflection_coeff":"0.80", "density":"7.38gm/cc", "type":"solder_paste", "color":"DimGray"},
{ "name":"Air", "conductivity":"0", "specific_heat":"0", "type":"gas", "color":"white"},
{ "name":"ThermalPad", "conductivity":"", "type":"deformable_pad", "color":"CornflowerBlue"},
{ "name":"Solder_mask", "conductivity":"0.9W/m-K", "type":"solid", "thickness":"1.0mil", "color":"Green"},
{ "name":"Core", "conductivityXX":".343W/m-K", "conductivityYY":".343W/m-K", "conductivityZZ":"1.059W/m-K", "density":"1.85gm/cc", "type":"solid", "emissivity":"0.9", "color":"LimeGreen"},
{ "name":"Prepreg", "conductivity":"1.059W/m-K", "type":"deformable", "emissivity":"0.9", "color":"Lime"},
{ "name":"top_component", "type":"component", "max_height":"5mm", "color":"SandyBrown"},
{ "name":"bottom_component", "type":"component", "max_height":"2mm", "color":"SaddleBrown"}
],


}