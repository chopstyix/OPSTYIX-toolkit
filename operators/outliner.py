# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
from bpy.types import Header, Menu, Panel

class OPSTYIX_OT_collection_template(bpy.types.Operator):
    bl_idname = "opstyix.collection_test"
    bl_label = "test label"
    bl_description = "test description"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # bpy.ops.outliner.collection_new()

        # New Collection
        my_coll = bpy.data.collections.new("MyCollection")

        # Add collection to scene collection
        # bpy.context.scene.collection.children.link(my_coll)
        bpy.context.scene.collection.children.link(my_coll)

        return {"FINISHED"}
    
def draw(self, context):
    self.layout.operator(OPSTYIX_OT_collection_template.bl_idname, text="", icon="OUTLINER_COLLECTION")

# class OUTLINER_HT_header(Header):
#     bl_space_type = 'OUTLINER'

#     def draw(self, context):
#         layout = self.layout

#         space = context.space_data
#         display_mode = space.display_mode
#         scene = context.scene
#         # ks = context.scene.keying_sets.active

#         # layout.template_header()

#         # layout.prop(space, "display_mode", icon_only=True)

#         # if display_mode == 'DATA_API':
#         #     OUTLINER_MT_editor_menus.draw_collapsible(context, layout)
#         # if display_mode == 'LIBRARY_OVERRIDES':
#         #     layout.prop(space, "lib_override_view_mode", text="")

#         # layout.separator_spacer()

#         # # filter_text_supported = True
#         # # # No text filtering for library override hierarchies. The tree is lazy built to avoid
#         # # # performance issues in complex files.
#         # # if display_mode == 'LIBRARY_OVERRIDES' and space.lib_override_view_mode == 'HIERARCHIES':
#         # #     filter_text_supported = False

#         # # if filter_text_supported:
#         # #     row = layout.row(align=True)
#         # #     row.prop(space, "filter_text", icon='VIEWZOOM', text="")

#         # # layout.separator_spacer()

#         # if display_mode == 'SEQUENCE':
#         #     row = layout.row(align=True)
#         #     row.prop(space, "use_sync_select", icon='UV_SYNC_SELECT', text="")

#         # row = layout.row(align=True)
#         # if display_mode in {'SCENES', 'VIEW_LAYER', 'LIBRARY_OVERRIDES'}:
#         #     row.popover(
#         #         panel="OUTLINER_PT_filter",
#         #         text="",
#         #         icon='FILTER',
#         #     )

#         # if display_mode in {'LIBRARIES', 'ORPHAN_DATA'}:
#         #     row.prop(space, "use_filter_id_type", text="", icon='FILTER')
#         #     sub = row.row(align=True)
#         #     sub.active = space.use_filter_id_type
#         #     sub.prop(space, "filter_id_type", text="", icon_only=True)

#         if display_mode == 'VIEW_LAYER':
#             layout.operator("outliner.collection_new", text="", icon='COLLECTION_NEW').nested = True

def register_outliner():
    bpy.utils.register_class(OPSTYIX_OT_collection_template)
    bpy.types.OUTLINER_HT_header.append(draw)

def unregister_outliner():
    bpy.types.OUTLINER_HT_header.remove(draw)
    bpy.utils.unregister_class(OPSTYIX_OT_collection_template)


print("outliner.py loaded")
