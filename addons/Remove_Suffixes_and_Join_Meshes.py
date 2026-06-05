bl_info = {
    "name": "Remove Suffixes and Join Meshes",
    "blender": (4, 1, 0),
    "category": "SM2 Tools",
    "author": "violet :3",
    "version": (1, 5),
    "location": "View3D > Sidebar > SM2 Tools",
    "description": "Removes suffixes like .001, _node, _node_0 and joins matching meshes individually by name. Also cleans material names.",
    "warning": "",
    "support": "COMMUNITY",
}

import bpy
import re
from collections import defaultdict

# Combine all suffix patterns into one regex
SUFFIX_PATTERN = re.compile(r"^(.*?)(?:\.(\d{3})|_node(?:_\d*)?)?$")

def is_in_view_layer(obj):
    return obj.name in bpy.context.view_layer.objects

def clean_and_merge_meshes():
    name_map = defaultdict(list)

    # Collect meshes grouped by base name
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            match = SUFFIX_PATTERN.match(obj.name)
            if match:
                base_name = match.group(1)
                name_map[base_name].append(obj)

    # Join meshes with the same base name into the base one
    for base_name, objects in name_map.items():
        visible_objects = [obj for obj in objects if is_in_view_layer(obj)]
        if len(visible_objects) > 1:
            base_obj = next((obj for obj in visible_objects if obj.name == base_name), None)

            if not base_obj:
                # If no object has the exact base name, pick first and rename it
                base_obj = visible_objects[0]
                base_obj.name = base_name

            # Deselect all, then select objects to join
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = base_obj
            base_obj.select_set(True)

            to_join = [obj for obj in visible_objects if obj != base_obj]
            for obj in to_join:
                obj.select_set(True)

            bpy.ops.object.join()

    # Clean up any remaining suffixes from meshes and empties
    for obj in bpy.data.objects:
        if obj.type in {'MESH', 'EMPTY'}:
            obj.name = re.sub(r"(\.\d{3}|_node(?:_\d*)?)$", "", obj.name)

    # Clean up material names
    for mat in bpy.data.materials:
        mat.name = re.sub(r"(\.\d{3}|_node(?:_\d*)?)$", "", mat.name)

class OBJECT_OT_RemoveSuffixes(bpy.types.Operator):
    """Remove suffixes like .001 and _node, and join meshes by base name"""
    bl_idname = "object.remove_suffixes"
    bl_label = "Remove Suffixes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        clean_and_merge_meshes()
        self.report({'INFO'}, "Suffixes removed, meshes joined, and materials cleaned")
        return {'FINISHED'}

class OBJECT_PT_RemoveSuffixesPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Remove Suffixes"
    bl_idname = "OBJECT_PT_remove_suffixes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SM2 Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.remove_suffixes")

def register():
    bpy.utils.register_class(OBJECT_OT_RemoveSuffixes)
    bpy.utils.register_class(OBJECT_PT_RemoveSuffixesPanel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_RemoveSuffixes)
    bpy.utils.unregister_class(OBJECT_PT_RemoveSuffixesPanel)

if __name__ == "__main__":
    register()
