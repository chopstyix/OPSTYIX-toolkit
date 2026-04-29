import bpy
import os


class OPSTYIX_OT_rename_node_to_image(bpy.types.Operator):
    bl_idname = "opstyix.rename_node_to_image"
    bl_label = "Rename to Image File"
    bl_description = "Rename this node to match its texture filename"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        node = getattr(context, 'active_node', None)
        return (
            node is not None
            and hasattr(node, 'image')
            and node.image is not None
        )

    def execute(self, context):
        node = context.active_node
        raw = node.image.filepath or node.image.name
        name = os.path.splitext(os.path.basename(raw))[0] or node.image.name
        node.label = name
        return {'FINISHED'}


def _draw_context_menu(self, context):
    node = getattr(context, 'active_node', None)
    if node is not None and hasattr(node, 'image') and node.image is not None:
        self.layout.separator()
        self.layout.operator(OPSTYIX_OT_rename_node_to_image.bl_idname)


def register():
    bpy.utils.register_class(OPSTYIX_OT_rename_node_to_image)
    bpy.types.NODE_MT_context_menu.append(_draw_context_menu)


def unregister():
    bpy.types.NODE_MT_context_menu.remove(_draw_context_menu)
    bpy.utils.unregister_class(OPSTYIX_OT_rename_node_to_image)
