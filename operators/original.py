# * FILE IMPORT
import os
import bpy
import bpy.utils.previews

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
    PointerProperty,
    CollectionProperty,
)

from bpy.types import (
    Operator,
    Panel,
    Menu,
    AddonPreferences,
    PropertyGroup,
    UIList,
)


# * STORE PROPERTIES (Self Descriptive)
class MyProperties(PropertyGroup):
    my_bpm: IntProperty(
        name="BPM Value", description="A integer property", default=128, min=1, max=200
    )

    my_measure: IntProperty(
        name="Measure Value",
        description="A integer property",
        default=8,
        min=4,
        max=9999,
    )

    tool_modifyEndFrame: BoolProperty(
        name="Modify End Frame",
        description="Changes the end frame of your animation when creating beat markers",
        default=True,
    )

    setting_override_frames: BoolProperty(
        name="Override Frames",
        description="Uses a user-specified range of frames from the User",
        default=False,
    )

    measure_Start: IntProperty(
        name="Start of Beat Marker Placements",
        description="A integer property",
        default=0,
        min=0,
        max=99999,
    )

    my_structure: IntProperty(
        name="Structure Value",
        description="Amount of Structures in the animation",
        default=0,
        min=0,
        max=99,
    )

    my_frame_start: IntProperty(
        name="Start Frame Value",
        description="Start frame to use as a reference",
        default=1,
        min=0,
        max=99999,
    )

    my_frame_end: IntProperty(
        name="End Frame Value",
        description="End frame to use as a reference",
        default=1,
        min=1,
        max=99999,
    )

    my_frame_padding: IntProperty(
        name="Frame Padding Value",
        description="Number frames to pad start and end frames, useful for rendering",
        default=0,
        min=0,
        max=999999,
    )

    my_frame_note: StringProperty(
        name="Frame Notation",
        description="Used to notate a given section of frames",
        default="",  # ? Is there a default setting for StringProperties
    )

    tool_enablePreviewRange: BoolProperty(
        name="Enable in Preview",
        description="Enables selected timeline range to be allocated in Timeline preview",
        default=False,
    )

    tool_enable_auto_bookmarks: BoolProperty(
        name="Enable Auto-Bookmarks",
        description="Automatically create measure/bar bookmarks when creating markers",
        default=False,
    )


# * OPERATORS (Executable Functions)
class OPSTYIX_OT_actions(Operator):
    # """Move items up and down, add and remove"""
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
        userinput = scene.OPSTYIX_user_input

        try:
            item = scene.custom[idx]
        except IndexError:
            pass
        else:
            if self.action == "DOWN" and idx < len(scene.custom) - 1:
                item_next = scene.custom[idx + 1].name
                scene.custom.move(idx, idx + 1)
                scene.selected_index += 1
                # This needs to be fixed, it's output item.name is incorrect
                # info = 'Item "%s" moved to position %d' % (item.name, scene.selected_index + 1)
                # self.report({'INFO'}, info)
            elif self.action == "UP" and idx >= 1:
                item_prev = scene.custom[idx - 1].name
                scene.custom.move(idx, idx - 1)
                scene.selected_index -= 1
                # This needs to be fixed, it's output item.name is incorrect
                # info = 'Item "%s" moved to position %d' % (item.name, scene.selected_index + 1)
                # self.report({'INFO'}, info)
            elif self.action == "REMOVE":
                info = 'Item "%s" removed from list' % (scene.custom[idx].name)
                # scene.selected_index -= None
                scene.custom.remove(idx)
                self.report({"INFO"}, info)
                # print("Active index ",scene.active_index)
                # print("Selected index ", scene.selected_index)
            elif self.action == "DESELECT_ALL":
                # Create a loop and select 'select_bookmark' to False.
                for i in scene.custom:
                    i.bookmark_select = False
            elif self.action == "SELECT_ALL":
                # Create a loop and select 'select_bookmark' to False.
                for i in scene.custom:
                    i.bookmark_select = True

        if self.action == "ADD":
            if scene.OPSTYIX_user_input.setting_override_frames == False:
                # Check if user has 'Preview Range' disabled; if enabled, reference Preview Range Start and End frames
                if scene.use_preview_range == False:
                    frame_start = scene.frame_start
                    frame_end = scene.frame_end
                else:
                    frame_start = scene.frame_preview_start
                    frame_end = scene.frame_preview_end
                obj_id = len(scene.custom)  # Assigns the object and ID
                selected_index = len(scene.custom)  # Assigns an index ID
            else:
                if userinput.my_frame_start <= userinput.my_frame_end:
                    frame_start = userinput.my_frame_start
                    frame_end = userinput.my_frame_end
                    obj_id = len(scene.custom)  # Assign obj id
                    selected_index = len(scene.custom)  # Assign index

                    # Reset my_frame_note
                    # userinput.my_frame_note = "Bookmark Name"
                else:
                    self.report({"INFO"}, "Starting frame cannot be after end frame!")
                    print("hey")
                    return {"FINISHED"}

            # Create item data
            item = scene.custom.add()  # Assigns the add function to "item"
            item.bookmark_select = False
            item.name = userinput.my_frame_note
            item.frame_note = item.name
            item.obj_id = obj_id
            item.frame_start = frame_start
            item.frame_end = frame_end
            scene.selected_index = selected_index

            # Reset Bookmark Label
            userinput.my_frame_note = ""

        return {"FINISHED"}


class OPSTYIX_OT_DrawMarkers(Operator):
    #! Operator only works on main scene frame ranges, if user has preview range enabled no visible changes are made which can result in confusion.
    # TODO: Check for preview frame range and disable if necessary.

    bl_idname = "opstyix.drawmarkers"
    bl_label = "Create Markers"
    bl_description = "Create markers based off user input"

    def execute(self, context):
        scene = bpy.context.scene
        input_bpm = scene.OPSTYIX_user_input.my_bpm
        input_measure = scene.OPSTYIX_user_input.my_measure
        input_modifyEndFrame = scene.OPSTYIX_user_input.tool_modifyEndFrame
        current_frame = scene.frame_current

        # print the values to the console
        print("Current Frame is: ", current_frame)
        print("BPM: ", input_bpm)
        print("Modify End Frame: ", input_modifyEndFrame)

        # Calculate Frame per Beat
        scene_fps = bpy.context.scene.render.fps

        fpb = scene_fps / input_bpm * 60

        print("Frames per beat is: ", fpb)

        # Begin Main Code
        beat_total = input_measure * 4
        bar_iter = 0
        frame_input = 1
        beat_input = 1
        scene.timeline_markers.new("[1]", frame=1)
        print("Placing beat marker on frame 1")

        while beat_input <= beat_total:
            # print("New Measure")
            bar_iter += 1
            bar_start = frame_input
            frame_input = int(beat_input * fpb)
            scene.timeline_markers.new("[2]", frame=frame_input)
            beat_input += 1
            frame_input = int(beat_input * fpb)
            scene.timeline_markers.new("[3]", frame=frame_input)
            beat_input += 1
            frame_input = int(beat_input * fpb)
            scene.timeline_markers.new("[4]", frame=frame_input)
            beat_input += 1
            frame_input = int(beat_input * fpb)
            bar_end = frame_input - 1
            scene.timeline_markers.new("[1]", frame=frame_input)
            beat_input += 1

            if scene.OPSTYIX_user_input.tool_enable_auto_bookmarks == True:
                item = scene.custom.add()
                item.bookmark_select = False
                item.frame_note = "Bar " + str(bar_iter)
                item.name = "Bar " + str(bar_iter)
                item.obj_id = len(scene.custom)
                # Do this for the very first frame only
                item.frame_start = bar_start
                # if beat_input > 1:
                #     item.frame_start = bar_start
                # else:
                #     item.frame_start = 1
                item.frame_end = bar_end
                # scene.selected_index = len(scene.custom) - 1

        area = bpy.context.area
        old_type = area.type
        area.type = "GRAPH_EDITOR"
        bpy.context.scene.tool_settings.lock_markers = False
        bpy.ops.marker.select_all(action="DESELECT")
        bpy.context.scene.tool_settings.lock_markers = True
        area.type = old_type

        if input_modifyEndFrame == True:
            new_frame_end = int(fpb * input_measure * 4 - 1)
            print("End frame will be: ", new_frame_end)
            bpy.context.scene.frame_start = 1
            bpy.context.scene.frame_end = new_frame_end

        return {"FINISHED"}


# TODO: Add the ability to lock certain bookmarks, which are protected from being deleted by this operator.
class OPSTYIX_OT_DeleteMarkers(Operator):
    bl_idname = "opstyix.deletemarkers"
    bl_label = "Delete Markers"
    bl_description = "Delete Markers from current scene."

    def execute(self, context):
        scene = context.scene
        print("Clearing all markers from scene...")
        scene.timeline_markers.clear()

        return {"FINISHED"}


class OPSTYIX_OT_setFrameRange(Operator):
    bl_idname = "opstyix.setframerange"
    bl_label = "Set Frame Range"
    bl_description = "Set Frame Range"

    # ? 2023-11-05
    # ? Revisting this block of code, seems like 'custom' can be renamed to something else
    # ? perhaps it should be renamed to animationBookmarks?
    # TODO: Renamed 'custom' to 'animation bookmarks'. Name not final.

    # If nothing is found in the UIList, the button is disabled
    @classmethod
    def poll(cls, context):
        return bool(context.scene.custom)

    def execute(self, context):
        scene = context.scene
        selectedIndex = scene.selected_index
        print("Selected index from UIList:", selectedIndex)

        framepadding = bpy.data.scenes["Scene"].OPSTYIX_user_input.my_frame_padding
        set_start_frame = scene.custom[selectedIndex].frame_start
        set_end_frame = scene.custom[selectedIndex].frame_end

        if scene.use_preview_range == True:
            info = "Set Preview Range from frames %d to %d" % (
                set_start_frame,
                set_end_frame,
            )
            scene.frame_preview_start = set_start_frame - framepadding
            scene.frame_preview_end = set_end_frame + framepadding
        else:
            info = "Set Range from frames %d to %d" % (set_start_frame, set_end_frame)
            scene.frame_start = set_start_frame - framepadding
            scene.frame_end = set_end_frame + framepadding

        self.report({"INFO"}, info)
        return {"FINISHED"}

class OPSTYIX_OT_set_range_select(Operator):
    bl_idname = "opstyix.set_range_select"
    bl_label = "Set Selected Frame Range"
    bl_description = "Sets Selected Bookmark Frame Range"

    # ? 2023-11-05
    # ? Revisting this block of code, seems like 'custom' can be renamed to something else
    # ? perhaps it should be renamed to animationBookmarks?
    # TODO: Renamed 'custom' to 'animation bookmarks'. Name not final.

    # If nothing is found in the UIList, the button is disabled
    @classmethod
    def poll(cls, context):
        return bool(context.scene.custom)

    def execute(self, context):
        scene = context.scene
        selectedIndex = scene.selected_index
        print("Selected index from UIList:", selectedIndex)
        select_check = False
        lowest_frame = 9999999999
        highest_frame = 1

        # Go through UIList 'custom' and find if 'bookmark_select' is True.
        for i in scene.custom:
            if i.bookmark_select == True:
                select_check = True
                # Find lowest 'frame_start' value
                if i.frame_start < lowest_frame:
                    lowest_frame = i.frame_start
                # Find highest 'frame_end' value
                elif i.frame_end > highest_frame:
                    highest_frame = i.frame_end



        # Set frame range
        if select_check == False:
            self.report({"INFO"}, "No bookmarks were selected.")
            return {"FINISHED"}
        
        framepadding = bpy.data.scenes["Scene"].OPSTYIX_user_input.my_frame_padding
        set_start_frame = lowest_frame
        set_end_frame = highest_frame

        if scene.use_preview_range == True:
            info = "Set Preview Range from frames %d to %d" % (
                set_start_frame,
                set_end_frame,
            )
            scene.frame_preview_start = set_start_frame - framepadding
            scene.frame_preview_end = set_end_frame + framepadding
        else:
            info = "Set Range from frames %d to %d" % (set_start_frame, set_end_frame)
            scene.frame_start = set_start_frame - framepadding
            scene.frame_end = set_end_frame + framepadding

        self.report({"INFO"}, info)
        return {"FINISHED"}


class OPSTYIX_OT_infoTest(Operator):
    """Tooltip"""

    bl_idname = "opstyix.custom_test"
    bl_label = "Test"

    def execute(self, context):
        self.report({"INFO"}, "Printing report to Info window.")
        return {"FINISHED"}


# * DRAW PANELS
# This controls the output text inside the UIList
class OPSTYIX_UL_items(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        # row = layout.row(align=False, heading='', heading_ctxt='', translate=True)
        # label = layout.split(factor=.5, align=True)
        # split_row = split.row(align=False, heading='', heading_ctxt='', translate=True)
        
        checkbox = "CHECKBOX_HLT" if item.bookmark_select else "CHECKBOX_DEHLT"
        # row.prop(item, "active", text="", emboss=False, icon=checkbox)
        row = layout.row(align=False, heading='', heading_ctxt='', translate=True)
        row.prop(item, "bookmark_select", text="", emboss=False, translate=False, icon=checkbox)
        label = layout.split(factor=.6, align=True)
        label.prop(item, "name", text="", emboss=False, translate=False)
        frame = label.split(factor=0, align=True)
        frame.prop(item, "frame_start", text="", emboss=False, translate=False)
        frame.prop(item, "frame_end", text="", emboss=False, translate=False)

    def invoke(self, context, event):
        pass


# Buttons for UIList
class OPSTYIX_PT_toolkit(Panel):
    # bl_idname = "VIEW3D_Opstyix_BPM_Marker"
    # bl_space_type = "VIEW_3D"
    # bl_context = "objectmode"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "OPSTYIX Toolkit"
    bl_category = "OPSTYIX"

    def draw_header(self, context):
        self.layout.label(icon_value=custom_icons["opstyix_icon"].icon_id)

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        global custom_icons
        # layout.label(text="test", icon_value=custom_icons["opstyix_icon"].icon_id)
        layout.use_property_split = True
        layout.use_property_decorate = False
        my_tool = scene.OPSTYIX_user_input

        row = layout.row(align=True)
        col = row.column(align=True)
        col.prop(my_tool, "my_bpm", text="BPM")
        col.prop(my_tool, "my_measure", text="Measures / Bars")
        col.prop(my_tool, "my_frame_padding", text="Frame Offset")

        row = layout.row(align=True)
        col = row.column(align=True)
        col.prop(my_tool, "tool_modifyEndFrame", text="Update End Frame")
        col.prop(my_tool, "tool_enable_auto_bookmarks", text="Auto Bookmark")

        row = layout.row(align=True)
        row.operator("opstyix.drawmarkers", text="Create Markers")
        row.operator("opstyix.deletemarkers", text="Delete Markers")


class OPSTYIX_PT_animationBookmarks(Panel):
    # bl_idname = 'TEXT_PT_my_panel'
    # bl_space_type = "VIEW_3D"
    # bl_region_type = "UI"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "Animation Bookmarks"
    bl_category = "OPSTYIX"
    bl_parent_id = "OPSTYIX_PT_toolkit"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = bpy.context.scene
        mytool = scene.OPSTYIX_user_input

        row = layout.row(align=True)
        row.prop(mytool, "my_frame_note", text="Bookmark Label")

        row = layout.row(align=True)
        col = row.column(align=True)

        if scene.OPSTYIX_user_input.setting_override_frames == True:
            col.enabled = True
        else:
            col.enabled = False

        # row = layout.row()
        col.prop(mytool, "my_frame_start", text="Start")
        col.prop(mytool, "my_frame_end", text="End")

        row = layout.row()
        row.prop(mytool, "setting_override_frames", text="Override Frames")

        # row = layout.row()
        # col = row.column(align=True)
        # split.label(text = '', translate = False)

        # rows = 2
        row = layout.row()
        row.template_list(
            "OPSTYIX_UL_items", "", scene, "custom", scene, "selected_index", rows=6
        )

        # Align settingsto the right of the UIList
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
        col.operator("opstyix.setframerange", text="", icon="DRIVER_DISTANCE")
        col.operator("opstyix.set_range_select", text="", icon="RESTRICT_SELECT_OFF")
        col.prop(scene, "use_preview_range", text="", toggle=True)


# * COLLECTIONS
# This contains the shot list bookmark data properties
class OPSTYIX_objectCollection(PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    # obj_type: StringProperty()
    id: IntProperty(
        name="Index Value",
        description="An integer property",
        default=0,
        min=0,
        max=99999,
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

    # TODO: Rename to bookmark_label
    frame_note: StringProperty(
        name="Bookmark Label",
        description="An string property",
        default="Label",
    )

    bookmark_select: BoolProperty(
        name="Select Bookmark",
        description="A bool property",
        default=True,
    )

# * Global Variable
custom_icons = None


# * REGISTER
# * Add all classes below, it will automatically register and unregister
def register_original():
    # from bpy.utils import register_class
    # for cls in classes:
    #     register_class(cls)
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    addon_path = os.path.dirname(__file__)
    icons_dir = os.path.join(addon_path, "..", "icons")

    custom_icons.load(
        "opstyix_icon", os.path.join(icons_dir, "opstyix_icon.png"), "IMAGE"
    )

    bpy.utils.register_class(MyProperties)
    bpy.utils.register_class(OPSTYIX_PT_toolkit)
    bpy.utils.register_class(OPSTYIX_PT_animationBookmarks)
    # bpy.utils.register_class(OPSTYIX_PT_settings)
    bpy.utils.register_class(OPSTYIX_UL_items)
    bpy.utils.register_class(OPSTYIX_OT_DrawMarkers)
    bpy.utils.register_class(OPSTYIX_OT_DeleteMarkers)
    bpy.utils.register_class(OPSTYIX_OT_setFrameRange)
    bpy.utils.register_class(OPSTYIX_OT_set_range_select)
    bpy.utils.register_class(OPSTYIX_objectCollection)
    bpy.utils.register_class(OPSTYIX_OT_infoTest)
    bpy.utils.register_class(OPSTYIX_OT_actions)

    # Passes "MyProperties" into something callable a.k.a. "OPSTYIX_user_input"
    bpy.types.Scene.OPSTYIX_user_input = PointerProperty(type=MyProperties)
    # bpy.types.Scene.OPSTYIX_active_collection = bpy.props.PointerProperty(
    #     type=bpy.types.Collection
    # )

    # Custom Properties
    # TODO: Cleanup, move all custom properties to OPSTYIX.
    bpy.types.Scene.custom = CollectionProperty(type=OPSTYIX_objectCollection)
    bpy.types.Scene.selected_index = IntProperty()


def unregister_original():
    # from bpy.utils import unregister_class
    # for cls in classes:
    #     unregister_class(cls)
    global custom_icons
    bpy.utils.previews.remove(custom_icons)
    bpy.utils.unregister_class(MyProperties)
    bpy.utils.unregister_class(OPSTYIX_PT_toolkit)
    bpy.utils.unregister_class(OPSTYIX_PT_animationBookmarks)
    # bpy.utils.unregister_class(OPSTYIX_PT_settings)
    bpy.utils.unregister_class(OPSTYIX_UL_items)
    bpy.utils.unregister_class(OPSTYIX_OT_DrawMarkers)
    bpy.utils.unregister_class(OPSTYIX_OT_DeleteMarkers)
    bpy.utils.unregister_class(OPSTYIX_OT_setFrameRange)
    bpy.utils.unregister_class(OPSTYIX_OT_set_range_select)
    bpy.utils.unregister_class(OPSTYIX_objectCollection)
    bpy.utils.unregister_class(OPSTYIX_OT_infoTest)
    bpy.utils.unregister_class(OPSTYIX_OT_actions)
    # bpy.utils.unregister_class(CUSTOM_OT_printItems)
    # bpy.utils.unregister_class(CUSTOM_OT_clearList)
    # bpy.utils.unregister_class(CUSTOM_OT_removeDuplicates)
    # bpy.utils.unregister_class(CUSTOM_OT_selectItems)

    del bpy.types.Scene.OPSTYIX_user_input


# if __name__ == "__main__":
#     register()

# *  RUN ON LOAD
print("original.py loaded")
