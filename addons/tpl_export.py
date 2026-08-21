bl_info = {
    "name": "Auto Export to USF and TPL",
    "author": "violet :3",
    "version": (1, 6),
    "blender": (4, 1, 0),
    "location": "File > Export > glTF 2.0 > Sidebar Panel",
    "description": "Adds buttons to glTF export panel to export and auto run ModelConverter.exe and convert_tpl.py. Enforces TPL resource markup during auto export.",
    "category": "Import-Export",
}

import bpy
import os
import subprocess
import time
import glob
import re

# ---------- Preferences ----------

class GLTFExportAutoConvertPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    model_converter_path: bpy.props.StringProperty(
        name="ModelConverter.exe Path",
        subtype='FILE_PATH',
        description="Path to ModelConverter.exe (choose .exe file)"
    )

    convert_tpl_script: bpy.props.StringProperty(
        name="convert_tpl.py Path",
        subtype='FILE_PATH',
        description="Path to convert_tpl.py (choose .py file)"
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.prop(self, "model_converter_path")
        row.operator("gltf_autoconvert.pick_modelconverter", text="Browse .exe")

        row = layout.row(align=True)
        row.prop(self, "convert_tpl_script")
        row.operator("gltf_autoconvert.pick_convertpy", text="Browse .py")


# ---------- File picker operators ----------

class GLTF_OT_pick_modelconverter(bpy.types.Operator):
    bl_idname = "gltf_autoconvert.pick_modelconverter"
    bl_label = "Select ModelConverter.exe"
    bl_description = "Pick the ModelConverter.exe file"
    filename_ext = ".exe"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.exe", options={'HIDDEN'})

    def invoke(self, context, event):
        prefs = context.preferences.addons[__name__].preferences
        self.filepath = prefs.model_converter_path or ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        prefs.model_converter_path = self.filepath
        self.report({'INFO'}, f"Selected ModelConverter.exe: {self.filepath}")
        return {'FINISHED'}


class GLTF_OT_pick_convertpy(bpy.types.Operator):
    bl_idname = "gltf_autoconvert.pick_convertpy"
    bl_label = "Select convert_tpl.py"
    bl_description = "Pick the convert_tpl.py file"
    filename_ext = ".py"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.py", options={'HIDDEN'})

    def invoke(self, context, event):
        prefs = context.preferences.addons[__name__].preferences
        self.filepath = prefs.convert_tpl_script or ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        prefs.convert_tpl_script = self.filepath
        self.report({'INFO'}, f"Selected convert_tpl.py: {self.filepath}")
        return {'FINISHED'}


# ---------- Utility: quoting for logs ----------

def _q(path: str) -> str:
    return f'"{path}"'


# ---------- Modal monitor: checks frequently, stops when done ----------

class GLTF_AUTOCONVERT_OT_monitor_tpl_resource(bpy.types.Operator):
    """Monitors <name>.tpl.resource during auto export and enforces markup"""
    bl_idname = "gltf_autoconvert.monitor_tpl_resource"
    bl_label = "Monitor TPL Resource"
    bl_options = {'INTERNAL'}

    usf_path: bpy.props.StringProperty()   
    search_folder: bpy.props.StringProperty()
    interval_seconds: bpy.props.FloatProperty(default=1.0, min=0.1, max=30.0)
    max_duration_seconds: bpy.props.FloatProperty(default=120.0, min=30.0, max=600.0)

    _timer = None
    _start_time = 0.0
    _resource_path = None
    _basename = ""
    _folder = ""

    def _find_resource_path(self):
        search_pattern = os.path.join(self._folder, "**", f"{self._basename}.tpl.resource")
        matches = glob.glob(search_pattern, recursive=True)
        return matches[0] if matches else None

    def _fix_if_needed(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = f.read()
        except (FileNotFoundError, PermissionError):
            return False, "locked or not found"

        if not data.strip():
            return False, "empty file"

        fixed = data
        
        # Overwrite everything after the colon, removing any dangling quotes
        fixed_new = re.sub(r"linkTplMarkup:[^\r\n]*", f"linkTplMarkup: '{self._basename}.tpl_markup.resource'", fixed)
        fixed_new = re.sub(r"tplMarkup:[^\r\n]*", f"tplMarkup: '{self._basename}.tpl_markup'", fixed_new)

        if fixed_new != fixed:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(fixed_new)
                print(f'[TPL Resource Fix] Re-applied markup to {_q(path)}')
                return True, "fixed"
            except Exception as e:
                print(f'[TPL Resource Fix] Error writing {_q(path)}: {e}')
                return False, "write error"
        else:
            if f"linkTplMarkup: '{self._basename}.tpl_markup.resource'" in fixed:
                print(f'[TPL Resource Fix] Markup already correct in {_q(path)}')
                return True, "already correct"
            
            return False, "waiting for markup fields"

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        now = time.time()
        elapsed = now - self._start_time
        if elapsed > self.max_duration_seconds:
            print('[TPL Resource Fix] Monitoring ended (time limit reached).')
            self._cleanup(context)
            return {'FINISHED'}

        if not self._resource_path or not os.path.exists(self._resource_path):
            self._resource_path = self._find_resource_path()
            if self._resource_path:
                print(f'[TPL Resource Fix] Found resource at {_q(self._resource_path)}')

        if self._resource_path:
            is_done, status = self._fix_if_needed(self._resource_path)
            
            if is_done:
                print(f'[TPL Resource Fix] Operation finished successfully: {status}.')
                self._cleanup(context)
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def _cleanup(self, context):
        if self._timer:
            try:
                context.window_manager.event_timer_remove(self._timer)
            except Exception:
                pass
            self._timer = None

    def invoke(self, context, event):
        if not self.usf_path:
            self.report({'ERROR'}, "No usf_path set for monitor.")
            return {'CANCELLED'}

        self._folder = self.search_folder if self.search_folder else os.path.dirname(self.usf_path)
        self._basename = os.path.splitext(os.path.basename(self.usf_path))[0]
        self._start_time = time.time()
        self._resource_path = None

        wm = context.window_manager
        self._timer = wm.event_timer_add(self.interval_seconds, window=context.window)
        wm.modal_handler_add(self)
        print(f'[TPL Resource Fix] Monitoring started for "{self._basename}" in {self._folder}')
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        print('[TPL Resource Fix] Monitoring cancelled.')
        self._cleanup(context)


# ---------- Main export UI panel ----------

class GLTF_PT_auto_convert_button(bpy.types.Panel):
    bl_label = "Auto Export to USF and TPL"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        operator = context.space_data.active_operator
        return operator is not None and operator.bl_idname == "EXPORT_SCENE_OT_gltf"

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences.addons.get(__name__)
        if prefs:
            prefs = prefs.preferences
            layout.prop(prefs, "model_converter_path")
            layout.prop(prefs, "convert_tpl_script")

        row = layout.row(align=True)
        row.operator("export_scene.gltf_auto_convert_button", icon='EXPORT')
        row.operator("export_scene.gltf_auto_convert_tangent_button", icon='SHADERFX')


# ---------- Export + convert, then start monitor ----------

def run_export_and_convert(context, keep_tangent: bool = False):
    prefs = context.preferences.addons[__name__].preferences
    model_converter = bpy.path.abspath(prefs.model_converter_path)
    convert_tpl = bpy.path.abspath(prefs.convert_tpl_script)

    if not os.path.isfile(model_converter):
        return {'ERROR'}, "ModelConverter.exe path invalid or not set."
    if not os.path.isfile(convert_tpl):
        return {'ERROR'}, "convert_tpl.py path invalid or not set."

    export_op = context.space_data.active_operator
    if export_op is None or export_op.bl_idname != "EXPORT_SCENE_OT_gltf":
        return {'ERROR'}, "GLTF export operator not found."

    export_path = export_op.filepath
    if not export_path:
        return {'ERROR'}, "No export filepath specified."

    # Copy all export operator properties except internal ones
    args = {}
    exclude_props = {'bl_idname', 'bl_label', 'bl_options', 'bl_rna', 'rna_type', 'filepath'}
    for prop_name in export_op.properties.bl_rna.properties.keys():
        if prop_name not in exclude_props:
            args[prop_name] = getattr(export_op, prop_name)
    args['filepath'] = export_path

    # Export GLTF with current settings
    bpy.ops.export_scene.gltf(**args)

    folder = os.path.dirname(export_path)
    basename = os.path.splitext(os.path.basename(export_path))[0]
    usf_path = os.path.join(folder, basename + ".usf")

    working_dir = os.path.dirname(model_converter)

    def quote_path(path):
        return f'"{path}"' if ' ' in path or '(' in path or ')' in path else path

    tpl_folder = os.path.normpath(os.path.join(os.path.dirname(convert_tpl), "project", "resources", "tpl"))

    model_converter_cmd = quote_path(model_converter) + " " + quote_path(export_path)
    if keep_tangent:
        model_converter_cmd += " --keep-tanget-orientation"

    if os.name == 'nt':
        cmd = (
            f'{model_converter_cmd} && '
            f'python {quote_path(convert_tpl)} {quote_path(usf_path)} && exit'
        )
        subprocess.Popen(
            ['cmd.exe', '/c', 'start', '', 'cmd.exe', '/k', cmd],
            cwd=working_dir,
        )

        bpy.ops.gltf_autoconvert.monitor_tpl_resource('INVOKE_DEFAULT',
                                                     usf_path=usf_path,
                                                     search_folder=tpl_folder,
                                                     interval_seconds=1.0,
                                                     max_duration_seconds=120.0)

        subprocess.Popen(['explorer', tpl_folder])

    else:
        cmd = (
            f'{model_converter_cmd} && '
            f'python3 {quote_path(convert_tpl)} {quote_path(usf_path)} && exit'
        )
        subprocess.Popen(cmd, shell=True, cwd=working_dir)

        bpy.ops.gltf_autoconvert.monitor_tpl_resource('INVOKE_DEFAULT',
                                                     usf_path=usf_path,
                                                     search_folder=tpl_folder,
                                                     interval_seconds=1.0,
                                                     max_duration_seconds=120.0)

        subprocess.Popen(['xdg-open', tpl_folder])

    return {'FINISHED'}


class EXPORT_OT_gltf_auto_convert_button(bpy.types.Operator):
    """Export using current GLTF settings and then auto run ModelConverter and convert_tpl.py"""
    bl_idname = "export_scene.gltf_auto_convert_button"
    bl_label = "Export and Auto Convert to USF/TPL"
    bl_options = {'REGISTER'}

    def execute(self, context):
        result = run_export_and_convert(context, keep_tangent=False)
        if isinstance(result, tuple) and result[0] == 'ERROR':
            self.report({'ERROR'}, result[1])
            return {'CANCELLED'}
        self.report({'INFO'}, "Exporting GLTF. Monitoring TPL markup (polling every 1s).")
        return {'FINISHED'}


class EXPORT_OT_gltf_auto_convert_tangent_button(bpy.types.Operator):
    """Export using current GLTF settings and then auto run ModelConverter with --keep-tanget-orientation and convert_tpl.py"""
    bl_idname = "export_scene.gltf_auto_convert_tangent_button"
    bl_label = "Export and Auto Convert (--keep-tanget-orientation)"
    bl_options = {'REGISTER'}

    def execute(self, context):
        result = run_export_and_convert(context, keep_tangent=True)
        if isinstance(result, tuple) and result[0] == 'ERROR':
            self.report({'ERROR'}, result[1])
            return {'CANCELLED'}
        self.report({'INFO'}, "Exporting GLTF (--keep-tanget-orientation). Monitoring TPL markup.")
        return {'FINISHED'}


# ---------- Register ----------

classes = (
    GLTFExportAutoConvertPreferences,
    GLTF_OT_pick_modelconverter,
    GLTF_OT_pick_convertpy,
    GLTF_AUTOCONVERT_OT_monitor_tpl_resource,
    GLTF_PT_auto_convert_button,
    EXPORT_OT_gltf_auto_convert_button,
    EXPORT_OT_gltf_auto_convert_tangent_button,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()