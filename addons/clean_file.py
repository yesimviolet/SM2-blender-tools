bl_info = {
    "name": "SM2: Full Clean",
    "author": "violet :3",
    "version": (1, 18),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > SM2 Tools",
    "description": "Cleans armatures and materials ONLY for visible meshes.",
    "category": "SM2 Tools",
}

import bpy
import re

# ----------------------------------------------------------
# UTILITIES
# ----------------------------------------------------------

def is_visible(obj):
    """Check if the object is visible in the current view layer."""
    try:
        # Accounts for hidden collections and object-level visibility
        return obj.visible_get()
    except:
        return False

def strip_number_suffix(name):
    return re.sub(r"\.\d{3}$", "", name)

def strip_mat_suffix(name):
    return re.sub(r"_mat\d+$", "", name)

# ----------------------------------------------------------
# MATERIAL HANDLING (VISIBLE ONLY)
# ----------------------------------------------------------

def extract_material_parts(raw_name):
    name = strip_mat_suffix(strip_number_suffix(raw_name))
    
    if name.endswith("white_simple_01"):
        if name == "white_simple_01": return "white_simple_01", None
        idx = name.rfind("white_simple_01")
        return "white_simple_01", name[:idx].rstrip("_") or None

    tag_match = re.search(r"(ch_|wpn_|vhl_|imp_|obj_|sky_|part_|decal_|scorch_)", name)
    if tag_match:
        start = tag_match.start()
        return name[start:], name[:start].rstrip("_") or None

    return name, None

def clean_visible_materials():
    """Only affects materials assigned to visible mesh objects."""
    
    # 1. Collect visible meshes and their materials
    visible_meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH' and is_visible(obj)]
    visible_mats = set()
    for obj in visible_meshes:
        for slot in obj.material_slots:
            if slot.material:
                visible_mats.add(slot.material)

    if not visible_mats:
        return

    # 2. Group only the visible materials
    groups = {} 
    for mat in visible_mats:
        core, submat = extract_material_parts(mat.name)
        groups.setdefault(core, {}).setdefault(submat, []).append(mat)

    # 3. Rename and Merge
    for core, subdict in groups.items():
        # Determine sorting (default/None first)
        default_key = None
        if None in subdict: default_key = None
        elif "default" in subdict: default_key = "default"

        sorted_submats = sorted(subdict.keys(), key=lambda sm: (0, "") if sm == default_key else (1, str(sm)))

        mat_index = 1
        for submat in sorted_submats:
            mats = subdict[submat]
            
            # Assign name to the 'canonical' material
            if submat == "default" or (submat is None and default_key is not None):
                final_name = core
            else:
                final_name = f"{core}_mat{mat_index}"
                mat_index += 1

            canonical = mats[0]
            canonical.name = final_name
            if submat: canonical["submaterial"] = submat

            # Merge others into canonical, but ONLY on visible meshes
            for other in mats[1:]:
                for obj in visible_meshes:
                    for slot in obj.material_slots:
                        if slot.material == other:
                            slot.material = canonical

    # 4. Final Purge (Unused materials)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)

# ----------------------------------------------------------
# OBJECT CLEANUP (VISIBLE ONLY)
# ----------------------------------------------------------

def run_visible_object_cleanup():
    stats = {"arm": 0, "del": 0, "mod": 0, "data": 0, "uv": 0}
    
    for obj in list(bpy.data.objects):
        if not is_visible(obj):
            continue

        # Rename Data to match Object
        if obj.data and obj.data.name != obj.name:
            obj.data.name = obj.name
            stats["data"] += 1

        if obj.type == "MESH":
            # Remove messy armature modifiers
            for mod in list(obj.modifiers):
                if mod.type == "ARMATURE":
                    if mod.object is None or re.search(r"\.\d{3}$", mod.object.name):
                        obj.modifiers.remove(mod)
                        stats["arm"] += 1
            
            # Delete objects with "object" in name (visible meshes only)
            if "object" in obj.name.lower():
                bpy.data.objects.remove(obj)
                stats["del"] += 1
                continue # Object is gone, skip further mesh tasks

            # Remove duplicate modifiers
            seen_mods = set()
            for mod in list(obj.modifiers):
                if mod.type in seen_mods:
                    obj.modifiers.remove(mod)
                    stats["mod"] += 1
                else:
                    seen_mods.add(mod.type)

            # Standardize UV names
            for uv in obj.data.uv_layers:
                if uv.name != "UVMap":
                    uv.name = "UVMap"
                    stats["uv"] += 1
                    
    return stats

# ----------------------------------------------------------
# UI & REGISTRATION
# ----------------------------------------------------------

class SM2_OT_CleanEverything(bpy.types.Operator):
    bl_idname = "sm2_tools.clean_everything"
    bl_label = "SM2 Full Clean (Visible Only)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        stats = run_visible_object_cleanup()
        clean_visible_materials()

        self.report(
            {"INFO"},
            f"Done! Data Renamed: {stats['data']}, UVs: {stats['uv']}, Modifiers Cleaned."
        )
        return {"FINISHED"}

class SM2_PT_ToolsPanel(bpy.types.Panel):
    bl_label = "SM2 Tools"
    bl_idname = "SM2_PT_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SM2 Tools"

    def draw(self, context):
        self.layout.operator("sm2_tools.clean_everything", icon="HIDE_OFF")

def register():
    bpy.utils.register_class(SM2_OT_CleanEverything)
    bpy.utils.register_class(SM2_PT_ToolsPanel)

def unregister():
    bpy.utils.unregister_class(SM2_OT_CleanEverything)
    bpy.utils.unregister_class(SM2_PT_ToolsPanel)

if __name__ == "__main__":
    register()