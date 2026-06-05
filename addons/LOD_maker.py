bl_info = {
    "name": "SM2 LOD maker",
    "author": "violet :3",
    "version": (1, 9),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > SM2 Tools",
    "description": "LOD generator that processes meshes in waves to avoid freezing",
    "category": "SM2 Tools",
}

import bpy
import re
from math import pow
from collections import deque

_suffix_re = re.compile(r'\.\d+$')

def clean_name(name):
    return _suffix_re.sub('', name)

# ---------------------------------------------------------
# GLOBAL STATE (needed for timer-based execution)
# ---------------------------------------------------------

LOD_QUEUE = deque()
TOTAL_JOBS = 0
DONE_JOBS = 0
WAVE_SIZE = 5   # 👈 increase to go faster, decrease if Blender stutters


# ---------------------------------------------------------
# TIMER CALLBACK
# ---------------------------------------------------------

def process_lod_wave():
    global DONE_JOBS

    context = bpy.context
    view_layer = context.view_layer
    collection = context.collection
    wm = context.window_manager

    for _ in range(min(WAVE_SIZE, len(LOD_QUEUE))):
        src, lod = LOD_QUEUE.popleft()

        base = clean_name(src.name)

        dup = src.copy()
        dup.data = src.data.copy()
        dup.name = f"{base}_lod{lod}"
        dup.parent = src
        collection.objects.link(dup)

        # Make active ONLY when needed
        view_layer.objects.active = dup
        dup.select_set(True)

        dec = dup.modifiers.new("Decimate", 'DECIMATE')
        dec.ratio = pow(0.5, lod)

        bpy.ops.object.modifier_apply(modifier=dec.name)

        dup.select_set(False)

        DONE_JOBS += 1
        wm.progress_update(DONE_JOBS)

    # Finished
    if not LOD_QUEUE:
        wm.progress_end()
        bpy.context.window.cursor_set('DEFAULT')
        print("SM2 LOD generation complete.")
        return None  # stop timer

    return 0.01  # 👈 delay between waves (seconds)


# ---------------------------------------------------------
# OPERATOR
# ---------------------------------------------------------

class SM2_OT_DuplicateLODs(bpy.types.Operator):
    bl_idname = "object.sm2_duplicate_lods"
    bl_label = "Make LODs (Wave Based)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global TOTAL_JOBS, DONE_JOBS, LOD_QUEUE

        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        if not meshes:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Build job queue
        LOD_QUEUE.clear()
        for obj in meshes:
            for lod in range(1, 6):
                LOD_QUEUE.append((obj, lod))

        TOTAL_JOBS = len(LOD_QUEUE)
        DONE_JOBS = 0

        wm = context.window_manager
        wm.progress_begin(0, TOTAL_JOBS)

        bpy.context.window.cursor_set('WAIT')

        # Start timer
        bpy.app.timers.register(process_lod_wave)

        return {'FINISHED'}


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

class SM2_PT_LODPanel(bpy.types.Panel):
    bl_label = "SM2 Tools"
    bl_idname = "SM2_PT_lod_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SM2 Tools'

    def draw(self, context):
        self.layout.operator(
            "object.sm2_duplicate_lods",
            icon='MOD_DECIM'
        )


classes = (
    SM2_OT_DuplicateLODs,
    SM2_PT_LODPanel,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
