# make sure you install the zip DO NOT EXCTRACT

Includes 7 tools for blender to be used with the sm2 model tool (can also be used for renders)
Tool one is sm2 bake tools It has 3 buttons prepare for bake, restore shader and connect _spec bake out output Which will allow you to bake custom textures using the custom shader

The second tool called remove suffixes Will join all meshes to be like how they are in sm2 kitbash file Making it easier to make kit bashes and to convert the model

The third tool is make lods Which will duplicate the selected mesh and make lods for it That keep The custom properties and modifiers

the fourth tool Is sm2 full clean Which will rename materials that have stuff like default_ In front of them so that it has threatened names It will also make sure all UV maps are correctly named and it will remove any empty Armature modifiers And it will also make sure the object name is the same as the data name

The fifth tool is texture autoimporter Which you select a directory where your textures are stored for the mesh And then depending on if you're using _CC or not for a colorable mesh, you select it and then you want to either do import textures, selecting materials which will only import the textures or the material you have selected currently And the other option is all materials which will import textures for all of the materials in the blend file.

The last tool is transfer custom properties, which will allow you to select anything From one of the provided templates from Saber And select it and then select all of the same type and transfer of a custom properties to them For example, you select a locator node/empty And then you select all the ones that were imported from index. and then you transfer custom properties And they will all share the same ones Same goes with anything else. Just make sure whatever has The custom properties is selected in the bright yellow Not orange. If the object with custom properties from A saber provided template Is orange It will then Remove the custom properties

tool tpl export Now when you go to export a GLTF, you will have a new option allowing you to export it to USF and TPL automatically.
You click that instead of clicking the normal export button And it will Automatically convert from GLTF to USF to TPL
Make sure you set up The directory to where the modelconverter.exe is, and the convert_tpl.py is

And that is a basic description on how to use everything I will be making a video tutorial in the near future

# shader created by evac
