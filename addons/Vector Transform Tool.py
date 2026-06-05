bl_info = {
    "name": "Space Marine 2 Vector Transform Tool",
    "author": "violet :3",
    "version": (1, 2),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > SM2 Tools",
    "description": "Seamlessly translates parent-relative local coordinates between Blender and the Swarm Engine (Integration Studio)",
    "category": "Import-Export",
}

import bpy
import math
from mathutils import Vector, Euler, Matrix

class SM2VectorProperties(bpy.types.PropertyGroup):
    sm2_loc: bpy.props.FloatVectorProperty(
        name="Engine Position",
        size=3,
        subtype='NONE',
        precision=4,
        default=(0.0, 0.0, 0.0)
    )
    
    sm2_rot: bpy.props.FloatVectorProperty(
        name="Engine Rotation",
        size=3,
        subtype='NONE',
        precision=4,
        default=(0.0, 0.0, 0.0)
    )

class OBJECT_OT_apply_sm2_vectors(bpy.types.Operator):
    bl_idname = "object.apply_sm2_vectors"
    bl_label = "Apply to Target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not hasattr(context.scene, 'sm2_vector_tool'):
            self.report({'ERROR'}, "Add-on properties missing. Restart Blender.")
            return {'CANCELLED'}

        props = context.scene.sm2_vector_tool

        if context.mode == 'POSE':
            target = context.active_pose_bone
            if not target:
                self.report({'WARNING'}, "No active bone selected")
                return {'CANCELLED'}
        else:
            target = context.active_object
            if not target:
                self.report({'WARNING'}, "No active object selected")
                return {'CANCELLED'}

        SWIZZLE = Matrix((
            (1.0,  0.0,  0.0, 0.0),
            (0.0,  0.0, -1.0, 0.0),
            (0.0,  1.0,  0.0, 0.0),
            (0.0,  0.0,  0.0, 1.0)
        ))

        loc_s = Vector(props.sm2_loc)
        rad_x = math.radians(props.sm2_rot[0])
        rad_y = math.radians(props.sm2_rot[1])
        rad_z = math.radians(props.sm2_rot[2])

        mat_trans_s = Matrix.Translation(loc_s)
        mat_rot_s = Euler((rad_x, rad_y, rad_z), 'XYZ').to_matrix().to_4x4()
        mat_s = mat_trans_s @ mat_rot_s

        mat_b = SWIZZLE @ mat_s @ SWIZZLE.inverted()

        if context.mode == 'POSE':
            target.matrix_basis = mat_b
        else:
            if target.parent:
                target.matrix_parent_inverse.identity()
            target.matrix_basis = mat_b

        self.report({'INFO'}, f"Applied Swarm Engine Matrix to {target.name}")
        return {'FINISHED'}

class OBJECT_OT_get_sm2_vectors(bpy.types.Operator):
    bl_idname = "object.get_sm2_vectors"
    bl_label = "Fetch from Target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not hasattr(context.scene, 'sm2_vector_tool'):
            self.report({'ERROR'}, "Add-on properties missing. Restart Blender.")
            return {'CANCELLED'}

        props = context.scene.sm2_vector_tool

        if context.mode == 'POSE':
            target = context.active_pose_bone
            if not target:
                return {'CANCELLED'}
            mat_b = target.matrix_basis
        else:
            target = context.active_object
            if not target:
                return {'CANCELLED'}
            mat_b = target.matrix_local 

        SWIZZLE = Matrix((
            (1.0,  0.0,  0.0, 0.0),
            (0.0,  0.0, -1.0, 0.0),
            (0.0,  1.0,  0.0, 0.0),
            (0.0,  0.0,  0.0, 1.0)
        ))

        mat_s = SWIZZLE.inverted() @ mat_b @ SWIZZLE

        loc_s, rot_s_quat, scale_s = mat_s.decompose()
        rot_s_euler = rot_s_quat.to_euler('XYZ')

        props.sm2_loc = (
            round(loc_s.x, 4),
            round(loc_s.y, 4),
            round(loc_s.z, 4)
        )
        
        props.sm2_rot = (
            round(math.degrees(rot_s_euler.x), 4),
            round(math.degrees(rot_s_euler.y), 4),
            round(math.degrees(rot_s_euler.z), 4)
        )
        
        return {'FINISHED'}

class VIEW3D_PT_sm2_vector_panel(bpy.types.Panel):
    bl_label = "Integration Studio Coordinates"
    bl_idname = "VIEW3D_PT_sm2_vector_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SM2 Tools"

    def draw(self, context):
        layout = self.layout
        
        if not hasattr(context.scene, 'sm2_vector_tool'):
            layout.label(text="Error: Tool properties failed to load.", icon='ERROR')
            layout.label(text="Please restart Blender.")
            return

        props = context.scene.sm2_vector_tool

        layout.label(text="Swarm Engine Local Space:")
        
        box = layout.box()
        
        box.label(text="Position:")
        col = box.column(align=True)
        col.prop(props, "sm2_loc", index=0, text="X")
        col.prop(props, "sm2_loc", index=1, text="Y")
        col.prop(props, "sm2_loc", index=2, text="Z")
        
        box.separator()
        
        box.label(text="Rotation:")
        col = box.column(align=True)
        col.prop(props, "sm2_rot", index=0, text="X")
        col.prop(props, "sm2_rot", index=1, text="Y")
        col.prop(props, "sm2_rot", index=2, text="Z")

        layout.separator()
        
        row = layout.row(align=True)
        row.operator("object.get_sm2_vectors", icon='IMPORT')
        row.operator("object.apply_sm2_vectors", icon='EXPORT')

classes = (
    SM2VectorProperties,
    OBJECT_OT_apply_sm2_vectors,
    OBJECT_OT_get_sm2_vectors,
    VIEW3D_PT_sm2_vector_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.sm2_vector_tool = bpy.props.PointerProperty(type=SM2VectorProperties)

def unregister():
    if hasattr(bpy.types.Scene, 'sm2_vector_tool'):
        del bpy.types.Scene.sm2_vector_tool
        
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()