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
{ "name":"Al", "conductivity":"150W/m-K", "specific_heat":"0.860J/gm-K", "type":"solid", "emissivity":"0.09", "reflection_coeff":"0.93", "density":"2.70gm/cc", "specularity":"", "color":"gray"},
{ "name":"Cu", "conductivity":"385W/m-K", "specific_heat":"0.385J/gm-K", "type":"solid", "emissivity":"0.15", "reflection_coeff":"0.63", "density":"8.93gm/cc", "specularity":"", "color":"orange"},
{ "name":"StainlessSteel", "conductivity":"", "specific_heat":"", "emissivity":"0.16", "type":"solid", "color":"yellow"},
{ "name":"Solder", "conductivity":"58W/m-K", "specific_heat":"0.23J/gm-K", "emissivity":"0.06", "reflection_coeff":"0.80", "density":"7.38gm/cc", "type":"solder_paste", "color":"light_gray"},
{ "name":"Air", "conductivity":"0", "specific_heat":"0", "type":"gas", "color":"white"},
{ "name":"ThermalPad", "conductivity":"", "type":"deformable_pad", "color":"dark_gray"},
{ "name":"Solder_mask", "conductivity":"0.9W/m-K", "type":"solid", "thickness":"1.0mil", "color":"dark_green"},
{ "name":"Core", "conductivityXX":".343W/m-K", "conductivityYY":".343W/m-K", "conductivityZZ":"1.059W/m-K", "density":"1.85gm/cc", "type":"solid", "emissivity":"0.9", "specularity":"", "color":"light_green"},
{ "name":"Prepreg", "conductivity":"1.059W/m-K", "type":"deformable", "emissivity":"0.9", "specularity":"", "color":"green"},
{ "name":"top_component", "type":"component", "max_height":"5mm", "color":"brown"},
{ "name":"bottom_component", "type":"component", "max_height":"2mm", "color":"brown"}
],

"Stackup": [
"shield_top": {"matl":"Al", "thickness":"30mil", "type":"Rigid"},

"air_under_shield_top": { "matl":"Air", "start":"shield_top", "stop":"topside_cu", "thickness":"6mm", "type":"Fill"},

"thermal_pad": { "displaces":["air_under_shield_top"], "undeformed_thickness":"3mm", "type":"Fill"},


"topside_components": { "displaces":["air_under_shield_top","thermal_pad"], "matl":"top_component", "height":"varies", "soldered_to_layer":"topside_cu", "type":"Fill"},
"topside_solder": { "binds_bottom":"topside_cu", "binds_top":"topside_components", "displaces":["air_under_shield_top","thermal_pad"], "type":"Coat"},
"topside_solder_mask": { "matl":"Solder_mask", "thickness":"1mil", "displaces":["air_under_shield_top","thermal_pad","topside_solder"], "laysatop":["topside_cu","topside_prepreg"], "type":"Coat"},

"topside_cu": { "matl":"Cu", "thickness":"1.2mil", "displaces":["air_under_shield_top","thermal_pad"], "type":"Rigid"},
"topside_prepreg": { "matl":"Prepreg", "thickness":"12mil", "type":"Fill"},


"side2_cu": { "matl":"Cu", "thickness":"1.2mil", "displaces":["side2_prepreg"], "type":"Rigid"},
"core1": { "matl":"Core", "thickness":"12mil" , "type":"Rigid"},
"side3_cu": { "matl":"Cu", "thickness":"1.2mil", "displaces":["side2_prepreg"], "type":"Rigid"},

"side4_prepreg": { "matl":"prepreg", "thickness":"12mil", "type":"Fill"},


"side4_cu": { "matl":"Cu", "thickness":"1.2mil", "displaces":["side4_prepreg"], "type":"Rigid"},
"core2": { "matl":"Core", "thickness":"12mil", "type":"Rigid"},
"side5_cu": { "matl":"Cu", "thickness":"1.2mil", "displaces":["side4_prepreg"], "type":"Rigid"},

"bottomside_prepreg": { "matl":"Prepreg", "thickness":"12mil", "type":"Fill"},
"bottomside_cu": { "matl":"Cu", "thickness":"1.2mil", "displaces":["air_under_shield_bottom"], "type":"Rigid"},

"bottomside_solder_mask": { "matl":"Solder_mask", "thickness":"1mil", "displaces":["air_under_shield_bottom","bottomside_solder"], "laysatop":["topside_cu","topside_prepreg"], "type":"Coat"},
"bottomside_solder": { "binds_bottom":"bottomside_cu", "binds_bottom":"bottomside_components", "displaces":["air_under_shield_bottom","thermal_pad"], "type":"Coat"},
"bottomside_components": { "displaces":["air_under_shield_bottom"], "matl":"bottom_component", "height":"varies", "soldered_to_layer":"bottomside_cu", "type":"Fill"},


"air_under_shield_bottom": { "matl":"Air", "start":"shield_bottom", "stop":"bottomside_cu", "thickness":"3mm", "type":"Fill"},
"shield_bottom": { "matl":"Al", "thickness":"30mil", "type":"Rigid"}
],

"Vias": [
 "shield_top_wall": {"matl": "Al", "from":"shield_top", "to":"topside_Cu"},
 "shield_bottom_wall": { "matl":"Al", "from":"shield_bottom", "to":"bottomside_Cu"},
 "thru": {"matl":"Cu", "from":"topside_cu", "to":"bottomside_cu"},
 "buried": {"matl":"Cu", "from":"side2_cu", "to":"side5_cu"},
 "screw": {"matl":"StainlessSteel", "from":"shield_top", "to":"shield_bottom"}
]
}