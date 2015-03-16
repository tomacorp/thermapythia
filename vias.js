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
 
"Vias": [
{ "name":"shield_top_wall", "matl": "Al", "from":"shield_top", "to":"topside_cu"},
{ "name":"shield_bottom_wall", "matl":"Al", "from":"shield_bottom", "to":"bottomside_cu"},
{ "name":"thru", "matl":"Cu", "from":"topside_cu", "to":"bottomside_cu"},
{ "name":"buried", "matl":"Cu", "from":"side2_cu", "to":"side5_cu"},
{ "name":"screw", "matl":"StainlessSteel", "from":"shield_top", "to":"shield_bottom"},
{ "name":"hole", "matl":"Air", "from":"topside_cu", "to":"bottomside_cu"}

]
}