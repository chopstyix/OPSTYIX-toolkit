import bpy
from bpy.types import Operator


class OPSTYIX_OT_instance_offset_from_cursor(Operator):
    bl_idname      = "opstyix.instance_offset_from_cursor"
    bl_label       = "Set Instance Offset from Cursor"
    bl_description = "Set the instance offset of the object's collection to the 3D cursor"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj    = context.active_object
        cursor = context.scene.cursor.location.copy()

        # Find all collections that directly contain this object
        collections = [c for c in bpy.data.collections if obj.name in c.objects]
        if not collections:
            self.report({'WARNING'}, "Object is not in any collection.")
            return {'CANCELLED'}

        for col in collections:
            col.instance_offset = cursor

        self.report({'INFO'}, f"Instance offset set on {len(collections)} collection(s).")
        return {'FINISHED'}


def _draw_context_menu(self, context):
    if context.active_object is not None:
        self.layout.separator()
        self.layout.operator(
            OPSTYIX_OT_instance_offset_from_cursor.bl_idname,
            icon='PIVOT_CURSOR',
        )


def register():
    bpy.utils.register_class(OPSTYIX_OT_instance_offset_from_cursor)
    bpy.types.VIEW3D_MT_object_context_menu.append(_draw_context_menu)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(_draw_context_menu)
    bpy.utils.unregister_class(OPSTYIX_OT_instance_offset_from_cursor)
