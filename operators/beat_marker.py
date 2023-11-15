# * FILE IMPORT
import bpy

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    PointerProperty,
)

from bpy.types import (
    Operator,
    PropertyGroup,
)

# * STORE PROPERTIES (Self Descriptive)
class OPSTYIX_PropertiesGroup(PropertyGroup):
    bpm: IntProperty(
        name="BPM Value", description="A integer property", default=128, min=1, max=200
    )

    measure: IntProperty(
        name="Measure Value",
        description="A integer property",
        default=8,
        min=4,
        max=9999,
    )

    update_end_frame: BoolProperty(
        name="Modify End Frame",
        description="Changes the end frame of your animation when creating beat markers",
        default=True,
    )

    frame_padding: IntProperty(
        name="Frame Padding Value",
        description="Number frames to pad start and end frames, useful for rendering",
        default=0,
        min=0,
        max=999999,
    )

    enable_auto_bookmarks: BoolProperty(
        name="Enable Auto-Bookmarks",
        description="Automatically create measure/bar bookmarks when creating markers",
        default=False,
    )


# * OPERATORS (Executable Functions)
class OPSTYIX_OT_DrawMarkers(Operator):
    #! Operator only works on main scene frame ranges, if user has preview range enabled no visible changes are made which can result in confusion.
    # TODO: Check for preview frame range and disable if necessary.

    bl_idname = "opstyix.drawmarkers"
    bl_label = "Create Markers"
    bl_description = "Create markers based off user input"

    def execute(self, context):
        scene = bpy.context.scene
        bpm = scene.OPSTYIX_settings.bpm
        measure = scene.OPSTYIX_settings.measure
        update_end_frame = scene.OPSTYIX_settings.update_end_frame
        current_frame = scene.frame_current

        # print the values to the console
        print("Current Frame is: ", current_frame)
        print("BPM: ", bpm)
        print("Modify End Frame: ", update_end_frame)

        # Calculate Frame per Beat
        scene_fps = bpy.context.scene.render.fps

        fpb = scene_fps / bpm * 60

        print("Frames per beat is: ", fpb)

        # Begin Main Code
        beat_total = measure * 4
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

            # If 'enable auto bookmarks' is enabled, add bar bookmarks to UIList
            if scene.OPSTYIX_settings.enable_auto_bookmarks == True:
                item = scene.custom.add()
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

        if update_end_frame == True:
            new_frame_end = int(fpb * measure * 4 - 1)
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

        frame_padding = bpy.data.scenes["Scene"].OPSTYIX_settings.frame_padding
        set_start_frame = scene.custom[selectedIndex].frame_start
        set_end_frame = scene.custom[selectedIndex].frame_end

        if scene.use_preview_range == True:
            info = "Set Preview Range from frames %d to %d" % (
                set_start_frame,
                set_end_frame,
            )
            scene.frame_preview_start = set_start_frame - frame_padding
            scene.frame_preview_end = set_end_frame + frame_padding
        else:
            info = "Set Range from frames %d to %d" % (set_start_frame, set_end_frame)
            scene.frame_start = set_start_frame - frame_padding
            scene.frame_end = set_end_frame + frame_padding

        self.report({"INFO"}, info)
        return {"FINISHED"}

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

# * REGISTER
# * Add all classes below, it will automatically register and unregister
def register_original():
    bpy.utils.register_class(OPSTYIX_PropertiesGroup)
    bpy.utils.register_class(OPSTYIX_OT_DrawMarkers)
    bpy.utils.register_class(OPSTYIX_OT_DeleteMarkers)
    bpy.utils.register_class(OPSTYIX_OT_setFrameRange)

    # Passes "MyProperties" into something callable a.k.a. "OPSTYIX_settings"
    bpy.types.Scene.OPSTYIX_settings = PointerProperty(type=OPSTYIX_PropertiesGroup)
    bpy.types.Scene.OPSTYIX_active_collection = bpy.props.PointerProperty(
        type=bpy.types.Collection
    )

def unregister_original():
    bpy.utils.unregister_class(OPSTYIX_PropertiesGroup)
    bpy.utils.unregister_class(OPSTYIX_OT_DrawMarkers)
    bpy.utils.unregister_class(OPSTYIX_OT_DeleteMarkers)
    bpy.utils.unregister_class(OPSTYIX_OT_setFrameRange)
    bpy.utils.unregister_class(OPSTYIX_objectCollection)
    del bpy.types.Scene.OPSTYIX_settings
    
# if __name__ == "__main__":
#     register()

# *  RUN ON LOAD
print("beat_marker.py loaded")
