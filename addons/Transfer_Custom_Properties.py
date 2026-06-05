bl_info = {
    "name": "Transfer Custom Properties",
    "blender": (4, 1, 0),
    "category": "SM2 Tools",
    "author": "violet :3",
    "version": (1, 1, 0),
    "description": "Transfers custom properties from active object/bone to others.",
}

import bpy

def copy_custom_properties(source, target):
    for key in list(target.keys()):
        if key not in '_RNA_UI':
            del target[key]
    for key, value in source.items():
        if key not in '_RNA_UI':
            target[key] = value

def copy_bone_display_settings(source_bone, target_bone):
    props = [
        "custom_shape", "custom_shape_scale", "custom_shape_translation",
        "custom_shape_rotation_euler", "custom_shape_scale_xyz",
        "bbone_x", "bbone_z", "bbone_handle_type_start", "bbone_handle_type_end"
    ]
    for prop in props:
        if hasattr(source_bone, prop) and hasattr(target_bone, prop):
            setattr(target_bone, prop, getattr(source_bone, prop))

class OBJECT_OT_transfer_custom_properties(bpy.types.Operator):
    """Transfer custom properties from active to selected"""
    bl_idname = "object.transfer_custom_properties"
    bl_label = "Transfer Custom Properties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "No active object.")
            return {'CANCELLED'}

        if obj.type == 'ARMATURE' and obj.mode == 'POSE':
            source = context.active_pose_bone
            if not source:
                self.report({'ERROR'}, "No active pose bone.")
                return {'CANCELLED'}

            targets = [b for b in context.selected_pose_bones if b != source]
            for target in targets:
                copy_custom_properties(source, target)
                copy_bone_display_settings(source, target)

        elif obj.type == 'ARMATURE' and obj.mode == 'EDIT':
            source = context.active_bone  # edit bone
            if not source:
                self.report({'ERROR'}, "No active edit bone.")
                return {'CANCELLED'}

            targets = [b for b in context.selected_editable_bones if b.name != source.name]
            for target in targets:
                copy_custom_properties(source, target)

        else:  # Object Mode for Meshes, etc.
            source = obj
            targets = [o for o in context.selected_objects if o != source]
            for target in targets:
                if source.type == target.type:
                    copy_custom_properties(source, target)
                    if source.data and target.data:
                        copy_custom_properties(source.data, target.data)

        self.report({'INFO'}, "Custom properties transferred.")
        return {'FINISHED'}

class OBJECT_PT_transfer_custom_properties_panel(bpy.types.Panel):
    """Panel in SM2 Tools Sidebar"""
    bl_label = "Transfer Custom Properties"
    bl_idname = "OBJECT_PT_transfer_custom_properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SM2 Tools'

    def draw(self, context):
        self.layout.operator(OBJECT_OT_transfer_custom_properties.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_OT_transfer_custom_properties)
    bpy.utils.register_class(OBJECT_PT_transfer_custom_properties_panel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_transfer_custom_properties)
    bpy.utils.unregister_class(OBJECT_PT_transfer_custom_properties_panel)

if __name__ == "__main__":
    register()
