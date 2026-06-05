bl_info = {
    "name": "Texture Auto Importer",
    "blender": (4, 4, 0),
    "category": "SM2 Tools",
    "version": (3, 4),
    "author": "violet :3",
    "description": "Import textures into SM2 Universal Shader for selected or all materials. Handles _cc logic and 'base color / _a' node."
}

import bpy
import os

EXTENSIONS = ['.png', '.tga']
GROUP_PREFIX = "SM2 Universal Shader"
NODEGROUP_BLEND = "SM2 MP Shader.blend"

def collect_files(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in EXTENSIONS:
                files.append(os.path.join(root, fn))
    return files

def find_texture(files, base_name, suffix):
    target = (base_name + suffix).lower()
    for f in files:
        nm = os.path.splitext(os.path.basename(f))[0].lower()
        if nm == target:
            return f
    for f in files:
        nm = os.path.splitext(os.path.basename(f))[0].lower()
        if nm.startswith(target):
            return f
    return None

def append_node_groups():
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    blend_path = os.path.join(addon_dir, NODEGROUP_BLEND)
    if not os.path.isfile(blend_path):
        print(f"Error: Cannot find node group blend file at {blend_path}")
        return

    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        node_groups = [ng for ng in data_from.node_groups]
        data_to.node_groups = node_groups
        print(f"[SM2] Appended node groups: {node_groups}")

def import_textures_to_material(mat, files, use_cc):
    group_data = next((ng for ng in bpy.data.node_groups if ng.name.startswith(GROUP_PREFIX)), None)
    if not group_data:
        append_node_groups()
        group_data = next((ng for ng in bpy.data.node_groups if ng.name.startswith(GROUP_PREFIX)), None)
        if not group_data:
            print(f"Error: Node group starting with '{GROUP_PREFIX}' not found.")
            return False

    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)

    grp = nodes.new('ShaderNodeGroup')
    grp.node_tree = group_data
    grp.location = (200, 0)

    bsdf = grp.outputs.get('BSDF')
    if bsdf:
        links.new(bsdf, out.inputs['Surface'])

    name = mat.name
    paths = {
        'basecolor': find_texture(files, name, ''),
        '_a': find_texture(files, name, '_a') if use_cc else None,
        '_cc': find_texture(files, name, '_cc') if use_cc else None,
        '_spec': find_texture(files, name, '_spec'),
        '_n': find_texture(files, name, '_nm'),
    }

    inp_base_a = grp.inputs.get('base color / _a')
    en_base_socket = grp.inputs.get('Enable if using Base Color')

    for idx, (key, p) in enumerate(paths.items()):
        if not p:
            continue
        try:
            img = bpy.data.images.load(p, check_existing=True)
        except:
            continue
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = img
        tex.label = key
        tex.name = key
        tex.location = (-400, -200 * idx)
        if key in ['_spec','_cc','_n']:
            tex.image.colorspace_settings.name = 'Non-Color'

        if key == '_a' and use_cc and inp_base_a:
            links.new(tex.outputs['Color'], inp_base_a)
            if en_base_socket:
                en_base_socket.default_value = False

        elif key == 'basecolor' and (not use_cc or not paths['_cc']) and inp_base_a:
            links.new(tex.outputs['Color'], inp_base_a)
            if en_base_socket:
                en_base_socket.default_value = True

        elif key not in ['basecolor', '_a']:
            inp = grp.inputs.get(key)
            if inp:
                links.new(tex.outputs['Color'], inp)

    return True

class TEXTURE_OT_import_all(bpy.types.Operator):
    bl_idname = "texture.import_all"
    bl_label = "Import Textures (All Materials)"

    def execute(self, context):
        directory = bpy.path.abspath(context.scene.texture_directory)
        use_cc = context.scene.use_cc
        if not os.path.isdir(directory):
            self.report({'ERROR'}, f"Invalid directory: {directory}")
            return {'CANCELLED'}
        files = collect_files(directory)
        for mat in bpy.data.materials:
            if mat.use_nodes:
                if not import_textures_to_material(mat, files, use_cc):
                    self.report({'ERROR'}, f"'{GROUP_PREFIX}' node group not found.")
                    return {'CANCELLED'}
        return {'FINISHED'}

class TEXTURE_OT_import_selected(bpy.types.Operator):
    bl_idname = "texture.import_selected"
    bl_label = "Import Textures (Selected Material)"

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH' or not obj.active_material:
            self.report({'ERROR'}, "Select a mesh with an active material")
            return {'CANCELLED'}
        directory = bpy.path.abspath(context.scene.texture_directory)
        use_cc = context.scene.use_cc
        if not os.path.isdir(directory):
            self.report({'ERROR'}, f"Invalid directory: {directory}")
            return {'CANCELLED'}
        files = collect_files(directory)
        if not import_textures_to_material(obj.active_material, files, use_cc):
            self.report({'ERROR'}, f"'{GROUP_PREFIX}' node group not found.")
            return {'CANCELLED'}
        return {'FINISHED'}

class TEXTURE_PT_import_panel(bpy.types.Panel):
    bl_label = "Texture Auto Importer"
    bl_idname = "TEXTURE_PT_import_panel"
    bl_category = 'SM2 Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "texture_directory")
        layout.prop(context.scene, "use_cc")
        layout.separator()
        layout.operator("texture.import_selected")
        layout.operator("texture.import_all")

classes = [
    TEXTURE_OT_import_all,
    TEXTURE_OT_import_selected,
    TEXTURE_PT_import_panel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texture_directory = bpy.props.StringProperty(
        name="Texture Directory", subtype='DIR_PATH')
    bpy.types.Scene.use_cc = bpy.props.BoolProperty(name="Use _cc", default=False)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.texture_directory
    del bpy.types.Scene.use_cc

if __name__ == "__main__":
    register()
