import os
import bpy
import bpy.utils.previews

from bpy.utils import register_class, unregister_class

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    PointerProperty,
    CollectionProperty,
)

from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
    UIList,
)


# ─── Property Groups ──────────────────────────────────────────────────────────

class MarkerProp(PropertyGroup):
    input_bpm: IntProperty(
        name="BPM Value",
        description="Value used to create beat markers",
        default=128,
        min=1,
        max=999,
    )

    input_measure: IntProperty(
        name="Measure Value",
        description="Value used to determine the length of beat marker calculation",
        default=8,
        min=4,
        max=9999,
    )

    input_frame_offset: IntProperty(
        name="Frame offset value",
        description="Offset frames, useful for matching to audio tracks",
        default=0,
        min=0,
        max=999999,
    )

    enable_update_end_frame: BoolProperty(
        name="Modify End Frame",
        description="When enabled, changes the scene's end frame when creating beat markers",
        default=True,
    )

    enable_auto_bookmark: BoolProperty(
        name="Enable Auto-Bookmarks",
        description="When enabled, creates animation bookmarks when creating beat markers",
        default=False,
    )


class BookmarkProp(PropertyGroup):
    id: IntProperty(
        name="Index Value",
        description="An integer property",
        default=0,
        min=0,
        max=99999,
    )

    bookmark_select: BoolProperty(
        name="Select Bookmark",
        description="A bool property",
        default=True,
    )

    name: StringProperty(
        name="Bookmark Name",
        description="An string property",
        default="New Name",
    )

    frame_start: IntProperty(
        name="Start Frame Value",
        description="An integer property",
        default=1,
        min=0,
        max=99999,
    )

    frame_end: IntProperty(
        name="End Frame Value",
        description="An integer property",
        default=1,
        min=0,
        max=99999,
    )


# ─── Operators ────────────────────────────────────────────────────────────────

class OPSTYIX_OT_Actions(Operator):
    bl_idname = "opstyix.list_action"
    bl_label = "Organize Shot List"
    bl_description = "Creates and deletes shot bookmarks for easy references"
    bl_options = {"REGISTER"}

    action: bpy.props.EnumProperty(
        items=(
            ("UP", "Up", ""),
            ("DOWN", "Down", ""),
            ("REMOVE", "Remove", ""),
            ("ADD", "Add", ""),
            ("DESELECT_ALL", "Deselect All", ""),
            ("SELECT_ALL", "Select All", ""),
        )
    )

    def invoke(self, context, event):
        scene = context.scene
        idx = scene.selected_index

        try:
            item = scene.OPSTYIX_AnimationBookmark[idx]
        except IndexError:
            pass
        else:
            if self.action == "DOWN" and idx < len(scene.OPSTYIX_AnimationBookmark) - 1:
                scene.OPSTYIX_AnimationBookmark.move(idx, idx + 1)
                scene.selected_index += 1
            elif self.action == "UP" and idx >= 1:
                scene.OPSTYIX_AnimationBookmark.move(idx, idx - 1)
                scene.selected_index -= 1
            elif self.action == "REMOVE":
                info = 'Item "%s" removed from list' % (
                    scene.OPSTYIX_AnimationBookmark[idx].name
                )
                scene.OPSTYIX_AnimationBookmark.remove(idx)
                self.report({"INFO"}, info)
            elif self.action == "DESELECT_ALL":
                for i in scene.OPSTYIX_AnimationBookmark:
                    i.bookmark_select = False
            elif self.action == "SELECT_ALL":
                for i in scene.OPSTYIX_AnimationBookmark:
                    i.bookmark_select = True

        if self.action == "ADD":
            if scene.use_preview_range:
                frame_start = scene.frame_preview_start
                frame_end = scene.frame_preview_end
            else:
                frame_start = scene.frame_start
                frame_end = scene.frame_end
            obj_id = len(scene.OPSTYIX_AnimationBookmark)
            selected_index = len(scene.OPSTYIX_AnimationBookmark)

            item = scene.OPSTYIX_AnimationBookmark.add()
            item.bookmark_select = False
            item.name = "New Shot"
            item.id = obj_id
            item.frame_start = frame_start
            item.frame_end = frame_end
            scene.selected_index = selected_index

        return {"FINISHED"}


class OPSTYIX_OT_DrawMarkers(Operator):
    #! Operator only works on main scene frame ranges, if user has preview range enabled no visible changes are made which can result in confusion.
    # TODO: Check for preview frame range and disable if necessary.

    bl_idname = "opstyix.draw_markers"
    bl_label = "Create Markers"
    bl_description = "Initialize beat marker creation"

    def execute(self, context):
        scene = context.scene
        props = scene.OPSTYIX_MarkerProperties
        input_bpm = props.input_bpm
        input_measure = props.input_measure
        input_frame_offset = props.input_frame_offset

        render = scene.render
        scene_fps = render.fps / render.fps_base
        fpb = scene_fps * 60 / input_bpm

        beat_total = input_measure * 4
        bar_iter = 0
        scene.timeline_markers.new("[1]", frame=input_frame_offset)

        beat_input = 1
        while beat_input <= beat_total:
            bar_iter += 1
            bar_start = round((beat_input - 1) * fpb) + input_frame_offset
            for _ in range(4):
                frame_input = round(beat_input * fpb) + input_frame_offset
                label = f"[{(beat_input % 4) + 1}]"
                scene.timeline_markers.new(label, frame=frame_input)
                beat_input += 1
            bar_end = frame_input - 1

            if props.enable_auto_bookmark:
                item = scene.OPSTYIX_AnimationBookmark.add()
                item.bookmark_select = False
                item.name = "Bar " + str(bar_iter)
                item.obj_id = len(scene.OPSTYIX_AnimationBookmark)
                item.frame_start = bar_start
                item.frame_end = bar_end

        area = bpy.context.area
        old_type = area.type
        area.type = "GRAPH_EDITOR"
        scene.tool_settings.lock_markers = False
        bpy.ops.marker.select_all(action="DESELECT")
        scene.tool_settings.lock_markers = True
        area.type = old_type

        if props.enable_update_end_frame:
            new_frame_end = round(fpb * input_measure * 4) - 1
            scene.frame_start = 1
            scene.frame_end = new_frame_end

        return {"FINISHED"}


# TODO: Add the ability to lock certain bookmarks, which are protected from being deleted by this operator.
class OPSTYIX_OT_DeleteMarkers(Operator):
    bl_idname = "opstyix.delete_markers"
    bl_label = "Delete Markers"
    bl_description = "Initialize the deletion of all markers within the scene"

    def execute(self, context):
        context.scene.timeline_markers.clear()
        return {"FINISHED"}


class OPSTYIX_OT_ClearBookmarks(Operator):
    bl_idname = "opstyix.clear_bookmarks"
    bl_label = "Clear Animation Bookmarks"
    bl_description = "Clears animation bookmarks"

    @classmethod
    def poll(cls, context):
        return bool(context.scene.OPSTYIX_AnimationBookmark)

    def execute(self, context):
        context.scene.OPSTYIX_AnimationBookmark.clear()
        self.report({"INFO"}, "Cleared bookmark list")
        return {"FINISHED"}


class OPSTYIX_OT_SetFrameRangeActive(Operator):
    bl_idname = "opstyix.set_frame_range_active"
    bl_label = "Set Frame Range"
    bl_description = "Set the scenes frame range based on highlighted bookmark"

    @classmethod
    def poll(cls, context):
        return context.scene.OPSTYIX_AnimationBookmark

    def execute(self, context):
        scene = context.scene
        selected_index = scene.selected_index
        set_start_frame = scene.OPSTYIX_AnimationBookmark[selected_index].frame_start
        set_end_frame = scene.OPSTYIX_AnimationBookmark[selected_index].frame_end

        if scene.use_preview_range:
            info = "Set Preview Range from frames %d to %d" % (set_start_frame, set_end_frame)
            scene.frame_preview_start = set_start_frame
            scene.frame_preview_end = set_end_frame
        else:
            info = "Set Range from frames %d to %d" % (set_start_frame, set_end_frame)
            scene.frame_start = set_start_frame
            scene.frame_end = set_end_frame

        self.report({"INFO"}, info)
        return {"FINISHED"}


class OPSTYIX_OT_SetFrameRangeSelected(Operator):
    bl_idname = "opstyix.set_frame_range_selected"
    bl_label = "Set Frame Range from Selected Bookmarks"
    bl_description = "Sets the scenes frame range based off selected bookmark(s)"

    @classmethod
    def poll(cls, context):
        return bool(context.scene.OPSTYIX_AnimationBookmark)

    def execute(self, context):
        scene = context.scene
        lowest_frame = 9999999999
        highest_frame = 1
        select_check = False

        for i in scene.OPSTYIX_AnimationBookmark:
            if i.bookmark_select:
                select_check = True
                if i.frame_start < lowest_frame:
                    lowest_frame = i.frame_start
                if i.frame_end > highest_frame:
                    highest_frame = i.frame_end

        if not select_check:
            self.report({"INFO"}, "Action cancelled, no selected bookmarks")
            return {"CANCELLED"}

        frame_padding = scene.OPSTYIX_MarkerProperties.input_frame_offset

        if scene.use_preview_range:
            info = "Set Preview Range from frames %d to %d" % (lowest_frame, highest_frame)
            scene.frame_preview_start = lowest_frame - frame_padding
            scene.frame_preview_end = highest_frame + frame_padding
        else:
            info = "Set Range from frames %d to %d" % (lowest_frame, highest_frame)
            scene.frame_start = lowest_frame - frame_padding
            scene.frame_end = highest_frame + frame_padding

        self.report({"INFO"}, info)
        return {"FINISHED"}


# ─── UI List ──────────────────────────────────────────────────────────────────

class OPSTYIX_UL_Items(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        checkbox = "CHECKBOX_HLT" if item.bookmark_select else "CHECKBOX_DEHLT"
        row = layout.row(align=False, heading="", heading_ctxt="", translate=True)
        row.prop(
            item,
            "bookmark_select",
            text="",
            emboss=False,
            translate=False,
            icon=checkbox,
        )
        label = layout.split(factor=0.435, align=True)
        label.prop(item, "name", text="", emboss=False, translate=False)
        frame = label.split(factor=0, align=True)
        frame.prop(item, "frame_start", text="", emboss=False, translate=False)
        frame.prop(item, "frame_end", text="", emboss=False, translate=False)

    def invoke(self, context, event):
        pass


# ─── Panels ───────────────────────────────────────────────────────────────────

class OPSTYIX_PT_MainPanel(Panel):
    bl_label = "OPSTYIX Beat Marker"
    bl_category = "OPSTYIX"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw_header(self, context):
        self.layout.label(icon_value=custom_icons["opstyix_icon"].icon_id)

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        my_tool = scene.OPSTYIX_MarkerProperties

        row = layout.row(align=True)
        col = row.column(align=True)
        col.prop(my_tool, "input_bpm", text="BPM")
        col.prop(my_tool, "input_measure", text="Measures / Bars")
        col.prop(my_tool, "input_frame_offset", text="Frame Offset")

        row = layout.row(align=True)
        col = row.column(align=True)
        col.prop(my_tool, "enable_update_end_frame", text="Update End Frame")
        col.prop(my_tool, "enable_auto_bookmark", text="Auto Bookmark")

        row = layout.row(align=True)
        row.operator("opstyix.draw_markers", text="Create Markers")
        row.operator("opstyix.delete_markers", text="Delete Markers")


class OPSTYIX_PT_AnimationBookmark(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "Animation Bookmarks"
    bl_category = "OPSTYIX"
    bl_parent_id = "OPSTYIX_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene

        row = layout.row()
        row.template_list(
            "OPSTYIX_UL_Items",
            "",
            scene,
            "OPSTYIX_AnimationBookmark",
            scene,
            "selected_index",
            rows=9,
        )

        col = row.column(align=True)
        col.operator("opstyix.list_action", icon="ADD", text="").action = "ADD"
        col.operator("opstyix.list_action", icon="REMOVE", text="").action = "REMOVE"
        col.separator()
        col.operator("opstyix.list_action", icon="TRIA_UP", text="").action = "UP"
        col.operator("opstyix.list_action", icon="TRIA_DOWN", text="").action = "DOWN"
        col.separator()
        col.operator("opstyix.list_action", icon="CHECKBOX_DEHLT", text="").action = "DESELECT_ALL"
        col.operator("opstyix.list_action", icon="CHECKBOX_HLT", text="").action = "SELECT_ALL"
        col.separator()
        col.operator("opstyix.set_frame_range_active", text="", icon="RESTRICT_SELECT_OFF")
        col.operator("opstyix.set_frame_range_selected", text="", icon="DRIVER_DISTANCE")
        col.separator()
        col.operator("opstyix.clear_bookmarks", text="", icon="TRASH")


# ─── Global Variable ──────────────────────────────────────────────────────────
custom_icons = None

# ─── Registration ─────────────────────────────────────────────────────────────
classes = [
    MarkerProp,
    BookmarkProp,
    OPSTYIX_PT_MainPanel,
    OPSTYIX_PT_AnimationBookmark,
    OPSTYIX_UL_Items,
    OPSTYIX_OT_DrawMarkers,
    OPSTYIX_OT_DeleteMarkers,
    OPSTYIX_OT_ClearBookmarks,
    OPSTYIX_OT_SetFrameRangeActive,
    OPSTYIX_OT_SetFrameRangeSelected,
    OPSTYIX_OT_Actions,
]


def register():
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    addon_path = os.path.dirname(__file__)
    icons_dir = os.path.join(addon_path, "..", "icons")

    custom_icons.load(
        "opstyix_icon", os.path.join(icons_dir, "opstyix_icon.png"), "IMAGE"
    )
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.OPSTYIX_MarkerProperties = PointerProperty(type=MarkerProp)
    bpy.types.Scene.OPSTYIX_AnimationBookmark = CollectionProperty(type=BookmarkProp)
    bpy.types.Scene.selected_index = IntProperty()


def unregister():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.OPSTYIX_MarkerProperties


print("beat_marker.py loaded")
