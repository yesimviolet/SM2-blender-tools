bl_info = {
    "name": "Mark Loose Edges as Sharp",
    "author": "violet :3",
    "version": (1, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Object Context Menu > Mark Loose Edges Sharp",
    "description": "Marks loose/border edges as sharp on all selected mesh objects",
    "category": "Mesh",
}

import bpy
import bmesh


class MESH_OT_mark_loose_edges_sharp(bpy.types.Operator):
    """Mark all loose/border edges as sharp on all selected meshes"""
    bl_idname = "mesh.mark_loose_edges_sharp_multi"
    bl_label = "Mark Loose Edges Sharp (Multi)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_meshes = [
            obj for obj in context.selected_objects
            if obj.type == 'MESH'
        ]

        if not selected_meshes:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        total_marked = 0

        for obj in selected_meshes:
            mesh = obj.data

            bm = bmesh.new()
            bm.from_mesh(mesh)
            bm.edges.ensure_lookup_table()

            marked = 0
            for e in bm.edges:
                if len(e.link_faces) < 2:  # loose or border
                    e.smooth = False  # sharp edge
                    marked += 1

            if marked:
                bm.to_mesh(mesh)
                mesh.update()
                total_marked += marked

            bm.free()

        self.report(
            {'INFO'},
            f"Marked {total_marked} loose edges as sharp on {len(selected_meshes)} objects"
        )
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(
        MESH_OT_mark_loose_edges_sharp.bl_idname,
        icon='EDGESEL'
    )


def register():
    bpy.utils.register_class(MESH_OT_mark_loose_edges_sharp)
    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)
    bpy.utils.unregister_class(MESH_OT_mark_loose_edges_sharp)


if __name__ == "__main__":
    register()
