{
"Format": "Thermal analysis stackup file",
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
{ "name":"Al", "conductivity":"150W/m-K", "specific_heat":"0.860J/gm-K", "type":"solid", "emissivity":"0.09", "reflection_coeff":"0.93", "density":"2.70gm/cc", "specularity":"", "color":"Silver"},
{ "name":"Cu", "conductivity":"385W/m-K", "specific_heat":"0.385J/gm-K", "type":"solid", "emissivity":"0.15", "reflection_coeff":"0.63", "density":"8.93gm/cc", "specularity":"", "color":"IndianRed"},
{ "name":"StainlessSteel", "conductivity":"", "specific_heat":"", "emissivity":"0.16", "type":"solid", "color":"Gold"},
{ "name":"Solder", "conductivity":"58W/m-K", "specific_heat":"0.23J/gm-K", "emissivity":"0.06", "reflection_coeff":"0.80", "density":"7.38gm/cc", "type":"solder_paste", "color":"DimGray"},
{ "name":"Air", "conductivity":"0", "specific_heat":"0", "type":"gas", "color":"white"},
{ "name":"ThermalPad", "conductivity":"", "type":"deformable_pad", "color":"CornflowerBlue"},
{ "name":"Solder_mask", "conductivity":"0.9W/m-K", "type":"solid", "thickness":"1.0mil", "color":"Green"},
{ "name":"Core", "conductivityXX":".343W/m-K", "conductivityYY":".343W/m-K", "conductivityZZ":"1.059W/m-K", "density":"1.85gm/cc", "type":"solid", "emissivity":"0.9", "specularity":"", "color":"LimeGreen"},
{ "name":"Prepreg", "conductivity":"1.059W/m-K", "type":"deformable", "emissivity":"0.9", "specularity":"", "color":"Lime"},
{ "name":"top_component", "type":"component", "max_height":"5mm", "color":"SandyBrown"},
{ "name":"bottom_component", "type":"component", "max_height":"2mm", "color":"SaddleBrown"}
],

"Stackup": [
{ "name":"shield_top", "matl":"Al", "thickness":"30mil", "type":"Rigid"},
{ "name":"shield_top_wall", "matl":"Al", "thickness":"6mm", "type":"Rigid"},

{ "name":"topside_solder", "matl":"Solder", "thickness":"1mil", "adheres_to":"topside_cu", "type":"Coat"},
{ "name":"topside_cu", "matl":"Cu", "thickness":"1.2mil", "type":"Rigid"},
{ "name":"topside_prepreg", "matl":"Prepreg", "thickness":"12mil", "type":"Fill"},

{ "name":"side2_cu", "matl":"Cu", "thickness":"1.2mil", "displaces":"topside_prepreg", "type":"Rigid", "coverage":"1" },
{ "name":"core1", "matl":"Core", "thickness":"12mil" , "type":"Rigid"},
{ "name":"side3_cu", "matl":"Cu", "thickness":"1.2mil", "displaces":"side4_prepreg", "type":"Rigid", "coverage":"0.5" },

{ "name":"side4_prepreg", "matl":"Prepreg", "thickness":"12mil", "type":"Fill"},

{ "name":"side4_cu", "matl":"Cu", "thickness":"1.2mil", "displaces":"side4_prepreg", "type":"Rigid", "coverage":"0.9"},
{ "name":"core2", "matl":"Core", "thickness":"12mil", "type":"Rigid"},
{ "name":"side5_cu", "matl":"Cu", "thickness":"1.2mil", "displaces":"bottomside_prepreg", "type":"Rigid", "coverage":"1"},

{ "name":"bottomside_prepreg", "matl":"Prepreg", "thickness":"12mil", "type":"Fill"},
{ "name":"bottomside_cu", "matl":"Cu", "thickness":"1.2mil", "type":"Rigid"},
{ "name":"bottomside_solder", "matl":"Solder", "thickness":"1mil", "adheres_to":"bottomside_cu", "type":"Coat"},

{ "name":"shield_bottom_wall", "matl":"Al", "thickness":"3mm", "type":"Rigid"},
{ "name":"shield_bottom", "matl":"Al", "thickness":"30mil", "type":"Rigid"}
],

"Embedded": [
{ "name":"air_under_shield_top", "matl":"Air", "start":"topside_prepreg", "stop":"shield_top", "thickness":"6mm", "type":"Fill"},
{ "name":"topside_solder_mask", "matl":"Solder_mask", "thickness":"1mil", "start":"topside_prepreg", "stop":"topside_cu", "type":"Coat"},
{ "name":"thermal_pad", "matl":"ThermalPad", "start":"topside_components", "stop":"shield_top", "thickness":"3mm", "type":"Fill"},
{ "name":"bottomside_solder_mask", "matl":"Solder_mask", "thickness":"1mil", "start":"bottomside_prepreg", "stop":"bottomside_cu", "type":"Coat"},
{ "name":"bottomside_components", "start":"", "stop":"", "matl":"bottom_component", "type":"Rigid"},
{ "name":"air_under_shield_bottom", "matl":"Air", "start":"shield_bottom", "stop":"bottomside_prepreg", "thickness":"3mm", "type":"Fill"},
{ "name":"topside_components", "start":"topside_solder", "stop":"air_under_shield_top", "matl":"top_component", "type":"Rigid"}
],

"Vias": [
{ "name": "shield_top_wall", "matl": "Al", "from":"shield_top", "to":"topside_Cu"},
{ "name":"shield_bottom_wall", "matl":"Al", "from":"shield_bottom", "to":"bottomside_Cu"},
{ "name": "thru", "matl":"Cu", "from":"topside_cu", "to":"bottomside_cu"},
{ "name": "buried", "matl":"Cu", "from":"side2_cu", "to":"side5_cu"},
{ "name": "screw", "matl":"StainlessSteel", "from":"shield_top", "to":"shield_bottom"}
]
}