bl_info = {
    "name": "Bake Shader Toggle",
    "blender": (4, 1, 0),
    "category": "SM2 Tools",
<<<<<<< Updated upstream:4.1/sm2_bake_setup.py
    "version": (1, 3),
    "author": "violet :3",
    "description": "Toggles baking setup by changing shader output to use SM2 group bake outputs and sets bake settings. Connects _a/Base Color bake or _spec bake for baking."
=======
    "version": (2, 1),
    "author": "violet :3",
    "description": "Toggle SM2 shader bake outputs. Updated for combined _a/Base Color socket."
>>>>>>> Stashed changes:addons/sm2_bake_setup.py
}

import bpy

<<<<<<< Updated upstream:4.1/sm2_bake_setup.py
class BAKE_OT_prepare(bpy.types.Operator):
=======
GROUP_PREFIX = "SM2 Universal Shader"  
SURFACE_NAME = "Surface"
SM2_IMG_PROP = "SM2_orig_colorspace"   

# ----------------------------- utilities -----------------------------

def find_group_and_output(nodes):
    out = next((n for n in nodes if isinstance(n, bpy.types.ShaderNodeOutputMaterial)), None)
    grp = next((n for n in nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name.startswith(GROUP_PREFIX)), None)
    return grp, out

def relink_surface(links, out_node, from_node, from_socket_name):
    for l in list(links):
        if l.to_node == out_node and l.to_socket.name == SURFACE_NAME:
            links.remove(l)
    if from_node and from_socket_name in from_node.outputs:
        links.new(from_node.outputs[from_socket_name], out_node.inputs[SURFACE_NAME])

def set_cycles_emit_bake_defaults(scene: bpy.types.Scene):
    scene.render.engine = 'CYCLES'
    scene.cycles.bake_type = 'EMIT'
    scene.render.bake.use_clear = False

def any_name_matches(node: bpy.types.Node, patterns):
    nm = (getattr(node, "name", "") or "").lower()
    lb = (getattr(node, "label", "") or "").lower()
    for p in patterns:
        if p in nm or p in lb:
            return True
    return False

def select_active_texture_for_patterns(mat: bpy.types.Material, patterns):
    nt = mat.node_tree
    img_node = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and any_name_matches(n, patterns)), None)
    if img_node:
        for n in nt.nodes:
            n.select = False
        img_node.select = True
        nt.nodes.active = img_node
        return img_node.image if img_node.image else None
    return None

def force_image_srgb_and_remember(img: bpy.types.Image):
    if not img:
        return
    try:
        cs = img.colorspace_settings
        if cs:
            if SM2_IMG_PROP not in img:
                img[SM2_IMG_PROP] = cs.name
            cs.name = 'sRGB'
    except Exception:
        pass

def restore_all_images_original_cs():
    for img in bpy.data.images:
        if SM2_IMG_PROP in img:
            try:
                orig = img[SM2_IMG_PROP]
                img.colorspace_settings.name = orig
            except Exception:
                pass
            try:
                del img[SM2_IMG_PROP]
            except Exception:
                pass

# ----------------------------- core ops -----------------------------

def connect_bake_output(context, output_socket_name, tex_patterns_for_active):
    scene = context.scene
    set_cycles_emit_bake_defaults(scene)

    found_any = False
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue

        nt = mat.node_tree
        grp, out = find_group_and_output(nt.nodes)
        if not (grp and out):
            continue

        if output_socket_name not in grp.outputs:
            continue

        relink_surface(nt.links, out, grp, output_socket_name)
        img = select_active_texture_for_patterns(mat, tex_patterns_for_active)
        force_image_srgb_and_remember(img)
        found_any = True

    return {'FINISHED'} if found_any else {'CANCELLED'}

# ---- Operators ----

class BAKE_OT_prepare(bpy.types.Operator):
    """Connects the primary Color/Alpha bake socket"""
>>>>>>> Stashed changes:addons/sm2_bake_setup.py
    bl_idname = "bake.prepare_shader"
    bl_label = "Prepare SM2 Shader for Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
<<<<<<< Updated upstream:4.1/sm2_bake_setup.py
        group_name_prefix = "SM2 Universal Shader"
        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue

            tree = mat.node_tree
            nodes = tree.nodes
            links = tree.links

            output_node = next((n for n in nodes if isinstance(n, bpy.types.ShaderNodeOutputMaterial)), None)
            group_node = next((n for n in nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name.startswith(group_name_prefix)), None)

            if output_node and group_node:
                for link in links:
                    if link.to_node == output_node and link.to_socket.name == 'Surface':
                        links.remove(link)
                if '_a/Base Color bake' in group_node.outputs:
                    links.new(group_node.outputs['_a/Base Color bake'], output_node.inputs['Surface'])

        scene = context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.bake_type = 'EMIT'
        scene.render.bake.use_clear = False

        for mat in bpy.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.label.lower() in ['base color', 'basecolor']:
                        node.select = True
                        mat.node_tree.nodes.active = node

=======
        target_names = ["_a/Base Color bake", "Base Color bake"]
        for name in target_names:
            result = connect_bake_output(context, name, ["base color", "basecolor"])
            if result == {'FINISHED'}:
                return result
        
        set_cycles_emit_bake_defaults(context.scene)
>>>>>>> Stashed changes:addons/sm2_bake_setup.py
        return {'FINISHED'}


class BAKE_OT_restore(bpy.types.Operator):
    bl_idname = "bake.restore_shader"
    bl_label = "Restore SM2 Shader Output"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        group_name_prefix = "SM2 Universal Shader"
        for mat in bpy.data.materials:
<<<<<<< Updated upstream:4.1/sm2_bake_setup.py
            if not mat.use_nodes:
                continue

            tree = mat.node_tree
            nodes = tree.nodes
            links = tree.links

            output_node = next((n for n in nodes if isinstance(n, bpy.types.ShaderNodeOutputMaterial)), None)
            group_node = next((n for n in nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name.startswith(group_name_prefix)), None)

            if output_node and group_node:
                for link in links:
                    if link.to_node == output_node and link.to_socket.name == 'Surface':
                        links.remove(link)
                if 'BSDF' in group_node.outputs:
                    links.new(group_node.outputs['BSDF'], output_node.inputs['Surface'])

        return {'FINISHED'}


class BAKE_OT_connect_spec(bpy.types.Operator):
    bl_idname = "bake.connect_spec_output"
    bl_label = "Connect _spec Bake to Surface"
    bl_options = {'REGISTER', 'UNDO'}

=======
            if not mat.use_nodes: continue
            grp, out = find_group_and_output(mat.node_tree.nodes)
            if grp and out and 'BSDF' in grp.outputs:
                relink_surface(mat.node_tree.links, out, grp, 'BSDF')

        restore_all_images_original_cs()
        return {'FINISHED'}

class BAKE_OT_connect_base(bpy.types.Operator):
    bl_idname = "bake.connect_base_output"
    bl_label = "Connect Base Color Bake"
    
    def execute(self, context):
        if connect_bake_output(context, "_a/Base Color bake", ["base color", "basecolor"]) == {'FINISHED'}:
            return {'FINISHED'}
        return connect_bake_output(context, "Base Color bake", ["base color", "basecolor"])

class BAKE_OT_connect_spec(bpy.types.Operator):
    bl_idname = "bake.connect_spec_output"
    bl_label = "Connect _spec Bake"
    
>>>>>>> Stashed changes:addons/sm2_bake_setup.py
    def execute(self, context):
        group_name_prefix = "SM2 Universal Shader"
        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue

<<<<<<< Updated upstream:4.1/sm2_bake_setup.py
            tree = mat.node_tree
            nodes = tree.nodes
            links = tree.links

            output_node = next((n for n in nodes if isinstance(n, bpy.types.ShaderNodeOutputMaterial)), None)
            group_node = next((n for n in nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name.startswith(group_name_prefix)), None)

            if output_node and group_node:
                for link in links:
                    if link.to_node == output_node and link.to_socket.name == 'Surface':
                        links.remove(link)
                if '_spec bake' in group_node.outputs:
                    links.new(group_node.outputs['_spec bake'], output_node.inputs['Surface'])

            # Select the _spec texture node if found
            for node in nodes:
                if node.type == 'TEX_IMAGE' and '_spec' in node.name.lower():
                    node.select = True
                    nodes.active = node

        return {'FINISHED'}
=======
class BAKE_OT_connect_em(bpy.types.Operator):
    bl_idname = "bake.connect_em_output"
    bl_label = "Connect _em (emissive) Bake"
    
    def execute(self, context):
        return connect_bake_output(context, "_em (emissive) bake", ["_em", "emissive"])

class BAKE_OT_connect_cc(bpy.types.Operator):
    bl_idname = "bake.connect_cc_output"
    bl_label = "Connect _cc Bake"
    
    def execute(self, context):
        return connect_bake_output(context, "_cc bake", ["_cc"])
>>>>>>> Stashed changes:addons/sm2_bake_setup.py


class BAKE_PT_shader_bake_tools(bpy.types.Panel):
    bl_label = "SM2 Bake Tools"
    bl_idname = "BAKE_PT_shader_bake_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SM2 Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator("bake.prepare_shader", text="Prepare for Bake")
        layout.operator("bake.restore_shader", text="Restore Shader")
        layout.operator("bake.connect_spec_output", text="Connect _spec Bake Output")

<<<<<<< Updated upstream:4.1/sm2_bake_setup.py
=======
        box = layout.box()
        box.label(text="Connect Bake Output")
        row = box.column(align=True)
        row.operator("bake.connect_base_output", text="Base Color / Alpha bake")
        row.operator("bake.connect_spec_output", text="_spec bake")
        row.operator("bake.connect_em_output", text="_em (emissive) bake")
        row.operator("bake.connect_cc_output", text="_cc bake")

# ----------------------------- registration -----------------------------
>>>>>>> Stashed changes:addons/sm2_bake_setup.py

classes = [
    BAKE_OT_prepare,
    BAKE_OT_restore,
<<<<<<< Updated upstream:4.1/sm2_bake_setup.py
=======
    BAKE_OT_connect_base,
>>>>>>> Stashed changes:addons/sm2_bake_setup.py
    BAKE_OT_connect_spec,
    BAKE_PT_shader_bake_tools,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()