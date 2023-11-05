#* FILE IMPORT
import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty)
                       
from bpy.types import (Operator,
                       Panel,
					   Menu,
					   AddonPreferences,
                       PropertyGroup,
                       UIList)

#* STORE PROPERTIES (Self Descriptive)
class MyProperties (PropertyGroup):
    my_bpm : IntProperty(
        name = "BPM Value",
        description="A integer property",
        default = 128,
        min = 1,
        max = 200
        )
    
    my_measure : IntProperty(
        name = "Measure Value",
        description="A integer property",
        default = 8,
        min = 4,
        max = 9999
        )
        
    tool_modifyEndFrame : BoolProperty(
        name = "Modify End Frame",
        description="Changes the end frame of your animation when creating beat markers",
        default = True
        )
    
    setting_override_frames : BoolProperty(
        name = "Override Frames",
        description= "Uses a user-specified range of frames from the User",
        default = True
        )
        
    measure_Start : IntProperty(
        name = "Start of Beat Marker Placements",
        description="A integer property",
        default = 0,
        min = 0,
        max = 99999
        )
        
    my_structure : IntProperty(
        name = "Structure Value",
        description="Amount of Structures in the animation",
        default = 0,
        min = 0,
        max = 99,
        )
    
    my_frame_start : IntProperty(
        name = "Start Frame Value",
        description="Start frame to use as a reference",
        default = 1,
        min = 0,
        max = 99999,
        )

    my_frame_end : IntProperty(
        name = "End Frame Value",
        description="End frame to use as a reference",
        default = 1,
        min = 1,
        max = 99999,
        )

    my_frame_padding : IntProperty(
        name = "Frame Padding Value",
        description = "Number frames to pad start and end frames, useful for rendering",
        default = 0,
        min = 0,
        max = 999999,
        )
    
    my_frame_note : StringProperty(
        name = "Frame Notation",
        description="Used to notate a given section of frames",
        default = "", #? Is there a default setting for StringProperties
        )    

    tool_enablePreviewRange : BoolProperty(
        name = "Enable in Preview",
        description="Enables selected timeline range to be allocated in Timeline preview",
        default = False
        )

		
#* OPERATORS (Executable Functions)
class OPSTYIX_OT_actions(Operator):
    #"""Move items up and down, add and remove"""
    bl_idname = "opstyix.list_action"
    bl_label = "Organize Shot List"
    bl_description = "Creates and deletes shot bookmarks for easy references"
    bl_options = {'REGISTER'}

    action: bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", "")))

    def invoke(self, context, event):
        scene = context.scene
        idx = scene.selected_index
        userinput = scene.OPSTYIX_user_input

        try:
            item = scene.custom[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(scene.custom) - 1:
                item_next = scene.custom[idx+1].name
                scene.custom.move(idx, idx+1)
                scene.selected_index += 1
                #This needs to be fixed, it's output item.name is incorrect
                #info = 'Item "%s" moved to position %d' % (item.name, scene.selected_index + 1)
                #self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = scene.custom[idx-1].name
                scene.custom.move(idx, idx-1)
                scene.selected_index -= 1
                #This needs to be fixed, it's output item.name is incorrect
                #info = 'Item "%s" moved to position %d' % (item.name, scene.selected_index + 1)
                #self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                info = 'Item "%s" removed from list' % (scene.custom[idx].name)
                #scene.selected_index -= None
                scene.custom.remove(idx)
                self.report({'INFO'}, info)
                #print("Active index ",scene.active_index)
                print("Selected index ",scene.selected_index)

        if self.action == 'ADD':
            item = scene.custom.add() # Assigns the add function to "item"
            item.name = userinput.my_frame_note
            item.frame_note = item.name  

            if scene.OPSTYIX_user_input.setting_override_frames == False:
                # Check if user has 'Preview Range' disabled; if enabled, reference Preview Range Start and End frames
                if scene.use_preview_range == False:
                    item.frame_start = scene.frame_start
                    item.frame_end = scene.frame_end
                else:
                    item.frame_start = scene.frame_preview_start
                    item.frame_end = scene.frame_preview_end
                
                item.active = False
                item.obj_id = len(scene.custom) # Assigns the object and ID 
                scene.selected_index = len(scene.custom)-1 # Assigns an index ID                
                
                # Reset my_frame_note
                userinput.my_frame_note = "Bookmark Name"

            else:
                if userinput.my_frame_start < userinput.my_frame_end:
                    item.frame_start = userinput.my_frame_start
                    item.frame_end = userinput.my_frame_end

                    item.active = False
                    item.obj_id = len(scene.custom) # Assigns the object and ID 
                    scene.selected_index = len(scene.custom)-1 # Assigns an index ID                
                    
                    # Reset my_frame_note                
                    userinput.my_frame_note = "Bookmark Name"
                
                else:
                    self.report({'INFO'}, "Starting frame cannot be after end frame!")

                # info = 'Bookmark successful' # % (item.name,item.frame_start,item.frame_end)
                # self.report({'INFO'}, info)
   
        return {"FINISHED"}

# class CUSTOM_OT_printItems(Operator):
#     """Print all items and their properties to the console"""
#     bl_idname = "custom.print_items"
#     bl_label = "Print Items to Console"
#     bl_description = "Print all items and their properties to the console"
#     bl_options = {'REGISTER', 'UNDO'}

#     reverse_order: BoolProperty(
#         default=False,
#         name="Reverse Order")

#     @classmethod
#     def poll(cls, context):
#         return bool(context.scene.custom)

#     def execute(self, context):
#         scene = context.scene
#         if self.reverse_order:
#             for i in range(scene.selected_index, -1, -1):        
#                 item = scene.custom[i]
#                 print ("Name:", item.name,"-",item.frame_start,"to",item.frame_end)
#         else:
#             for item in scene.custom:
#                 print ("Name:", item.name,"-",item.frame_start,"to",item.frame_end)
#                 print("test",item.id)
#         return{'FINISHED'}

# class CUSTOM_OT_clearList(Operator):
#     """Clear all items of the list"""
#     bl_idname = "custom.clear_list"
#     bl_label = "Clear List"
#     bl_description = "Clear all items of the list"
#     bl_options = {'INTERNAL'}

#     @classmethod
#     def poll(cls, context):
#         return bool(context.scene.custom)

#     def invoke(self, context, event):
#         return context.window_manager.invoke_confirm(self, event)

#     def execute(self, context):
#         if bool(context.scene.custom):
#             context.scene.custom.clear()
#             self.report({'INFO'}, "All items removed")
#         else:
#             self.report({'INFO'}, "Nothing to remove")
#         return{'FINISHED'}

# class CUSTOM_OT_removeDuplicates(Operator):
#     """Remove all duplicates"""
#     bl_idname = "custom.remove_duplicates"
#     bl_label = "Remove Duplicates"
#     bl_description = "Remove all duplicates"
#     bl_options = {'INTERNAL'}

#     def find_duplicates(self, context):
#         """find all duplicates by name"""
#         name_lookup = {}
#         for c, i in enumerate(context.scene.custom):
#             name_lookup.setdefault(i.name, []).append(c)
#         duplicates = set()
#         for name, indices in name_lookup.items():
#             for i in indices[1:]:
#                 duplicates.add(i)
#         return sorted(list(duplicates))

#     @classmethod
#     def poll(cls, context):
#         return bool(context.scene.custom)

#     def execute(self, context):
#         scene = context.scene
#         removed_items = []
#         # Reverse the list before removing the items
#         for i in self.find_duplicates(context)[::-1]:
#             scene.custom.remove(i)
#             removed_items.append(i)
#         if removed_items:
#             scene.selected_index = len(scene.custom)-1
#             info = ', '.join(map(str, removed_items))
#             self.report({'INFO'}, "Removed indices: %s" % (info))
#         else:
#             self.report({'INFO'}, "No duplicates")
#         return{'FINISHED'}

#     def invoke(self, context, event):
#         return context.window_manager.invoke_confirm(self, event)

# class CUSTOM_OT_selectItems(Operator):
#     """Select Items in the Viewport"""
#     bl_idname = "custom.select_items"
#     bl_label = "Select Item(s) in Viewport"
#     bl_description = "Select Items in the Viewport"
#     bl_options = {'REGISTER', 'UNDO'}

#     select_all: BoolProperty(
#         default=False,
#         name="Select all Items of List",
#         options={'SKIP_SAVE'})

#     @classmethod
#     def poll(cls, context):
#         return bool(context.scene.custom)

#     def execute(self, context):
#         scene = context.scene
#         idx = scene.selected_index

#         try:
#             item = scene.custom[idx]
#         except IndexError:
#             self.report({'INFO'}, "Nothing selected in the list")
#             return{'CANCELLED'}

#         obj_error = False
#         bpy.ops.object.select_all(action='DESELECT')
#         if not self.select_all:
#             obj = scene.objects.get(scene.custom[idx].name, None)
#             if not obj: 
#                 obj_error = True
#             else:
#                 obj.select_set(True)
#                 info = '"%s" selected in Viewport' % (obj.name)
#         else:
#             selected_items = []
#             unique_objs = set([i.name for i in scene.custom])
#             for i in unique_objs:
#                 obj = scene.objects.get(i, None)
#                 if obj:
#                     obj.select_set(True)
#                     selected_items.append(obj.name)

#             if not selected_items: 
#                 obj_error = True
#             else:
#                 missing_items = unique_objs.difference(selected_items)
#                 if not missing_items:
#                     info = '"%s" selected in Viewport' \
#                         % (', '.join(map(str, selected_items)))
#                 else:
#                     info = 'Missing items: "%s"' \
#                         % (', '.join(map(str, missing_items)))
#         if obj_error: 
#             info = "Nothing to select, object removed from scene"
#         self.report({'INFO'}, info)    
#         return{'FINISHED'}
    
class OPSTYIX_OT_DrawMarkers (Operator):
    #! Operator only works on main scene frame ranges, if user has preview range enabled no visible changes are made which can result in confusion.
    #TODO: Check for preview frame range and disable if necessary.

    bl_idname = "opstyix.drawmarkers"
    bl_label = "Create Markers"
    bl_description = "Create markers based off user input"

    def execute(self,context):
        scene = bpy.context.scene
        input_bpm = scene.OPSTYIX_user_input.my_bpm
        input_measure = scene.OPSTYIX_user_input.my_measure
        input_modifyEndFrame = scene.OPSTYIX_user_input.tool_modifyEndFrame
        current_frame = scene.frame_current
        
        # print the values to the console
        print("Current Frame is: ",current_frame)
        print("BPM: ",input_bpm)
        print("Modify End Frame: ",input_modifyEndFrame)

        # Calculate Frame per Beat
        scene_fps = bpy.context.scene.render.fps

        fpb = scene_fps/input_bpm * 60
        
        print("Frames per beat is: ",fpb)

        # Begin Main Code
        beat_total = input_measure * 4
        beat_input = 1
        scene.timeline_markers.new('[1]', frame=1)
        print("Placing beat marker on frame 1")
          
        while(beat_input <= beat_total):
            print("New Measure")
            frame_input = int(beat_input * fpb)
            scene.timeline_markers.new('[2]', frame=frame_input)
            beat_input += 1 
            frame_input = int(beat_input * fpb)
            scene.timeline_markers.new('[3]', frame=frame_input)
            beat_input += 1
            frame_input = int(beat_input * fpb)
            scene.timeline_markers.new('[4]', frame=frame_input)
            beat_input += 1
            frame_input = int(beat_input * fpb)
            scene.timeline_markers.new('[1]', frame=frame_input)
            beat_input += 1
            
        area = bpy.context.area
        old_type = area.type
        area.type = 'GRAPH_EDITOR'
        bpy.context.scene.tool_settings.lock_markers = False
        bpy.ops.marker.select_all(action='DESELECT')
        bpy.context.scene.tool_settings.lock_markers = True
        area.type = old_type
        
        if input_modifyEndFrame == True:
            new_frame_end = int(fpb * input_measure * 4 - 1)
            print("End frame will be: ",new_frame_end)
            bpy.context.scene.frame_start = 1
            bpy.context.scene.frame_end = new_frame_end
        
        return {'FINISHED'}
    
class OPSTYIX_OT_DeleteMarkers(Operator):
    bl_idname = "opstyix.deletemarkers"
    bl_label = "Delete Markers"
    bl_description = "Delete Markers from current scene."
    
    def execute(self,context):
        scene = context.scene
        print("Clearing all markers from scene...")
        scene.timeline_markers.clear()
        
        return {'FINISHED'}

class OPSTYIX_OT_setFrameRange(Operator):
    bl_idname = "opstyix.setframerange"
    bl_label = "Set Frame Range"
    bl_description = "Set Frame Range"

    # ? 2023-11-05
    # ? Revisting this block of code, seems like 'custom' can be renamed to something else
    # ? perhaps it should be renamed to animationBookmarks?
    # TODO: Renamed 'custom' to 'animationBookmarks'. Name not final.

    # If nothing is found in the UIList, the button is disabled
    @classmethod
    def poll(cls, context):
        return bool(context.scene.custom)

    def execute(self,context):
        scene = context.scene
        selectedIndex = scene.selected_index
        print("Selected index from UIList:",selectedIndex)

        framepadding = bpy.data.scenes["Scene"].OPSTYIX_user_input.my_frame_padding
        set_start_frame = scene.custom[selectedIndex].frame_start
        set_end_frame = scene.custom[selectedIndex].frame_end
        
        if scene.use_preview_range == True:
            info = 'Set Preview Range from frames %d to %d' % (set_start_frame, set_end_frame)
            scene.frame_preview_start = set_start_frame - framepadding
            scene.frame_preview_end = set_end_frame + framepadding
        else:
            info = 'Set Range from frames %d to %d' % (set_start_frame, set_end_frame)            
            scene.frame_start = set_start_frame - framepadding
            scene.frame_end = set_end_frame + framepadding
        
        self.report({'INFO'}, info)
        return {'FINISHED'}
    
class OPSTYIX_OT_infoTest(Operator):
    """Tooltip"""
    bl_idname = "opstyix.custom_test"
    bl_label = "Test"
    
    def execute(self,context):
        self.report({'INFO'}, 'Printing report to Info window.')
        return {'FINISHED'}

#* DRAW PANELS
# This controls the output text inside the UIList
class OPSTYIX_UL_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        #scene = bpy.context.scene
        #mytool = scene.OPSTYIX_user_input
        split = layout.split(factor=.5,align=True)
        #checkbox = "CHECKBOX_HLT" if item.active else "CHECKBOX_DEHLT"
        #split.label(text="Index: %d" % (index))
        #custom_icon = "OUTLINER_OB_%s" % item.obj_type
        #split.prop(item, "name", text="", emboss=False, translate=False, icon=custom_icon)
        #split.label(text=item.name, icon=custom_icon) # avoids renaming the item by accident
        #split.label(text=item.name)
        split.prop(item, "name", text = '', emboss= False, translate = False)
        #split = layout.split(factor=.2,align=False)
        split.prop(item, "frame_start", text = '', emboss = False, translate = False)      
        split.prop(item, "frame_end", text = '', emboss = False, translate = False)
        #split.label(text=str(item.frame_start)+" -> "+str(item.frame_end))
        #split = layout.split(factor=.2,align=True)   
        #split.prop(item, "active", text='', emboss=False, icon=checkbox)
        #split.prop(mytool, 'tool_enablePreviewRange', text = '', emboss=False)
        #split.prop(modifier, 'show_viewport', text='', emboss=False) 
        #split.label(text="-")
        #split.label(text=str(item.frame_end))

    def invoke(self, context, event):
        pass   

# Buttons for UIList
class OPSTYIX_PT_toolkit(Panel):
    #bl_idname = "VIEW3D_Opstyix_BPM_Marker"
    #bl_space_type = "VIEW_3D"
    #bl_context = "objectmode"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "OPSTYIX Toolkit"
    bl_category = "OPSTYIX"
    
    def draw(self,context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        my_tool = scene.OPSTYIX_user_input

        row = layout.row(align = True)
        col = row.column(align = True)
        col.prop(my_tool,"my_bpm", text ="BPM")
        col.prop(my_tool,"my_measure", text ="Measures / Bars")
        col.prop(my_tool, "my_frame_padding", text = "Frame Offset")
        col.prop(my_tool, "tool_modifyEndFrame", text= "Update End Frame") 

        row = layout.row(align=True)
        row.operator("opstyix.drawmarkers", text="Create Markers")
        row.operator("opstyix.deletemarkers", text="Delete Markers")



class OPSTYIX_PT_animationBookmarks(Panel):
    #bl_idname = 'TEXT_PT_my_panel'
    #bl_space_type = "VIEW_3D"
    #bl_region_type = "UI"
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
        
        row = layout.row(align = True)
        row.prop(mytool,"my_frame_note", text="Label")

        row = layout.row(align = True)
        col = row.column(align = True)             

        if scene.OPSTYIX_user_input.setting_override_frames == True:
            col.enabled = True
        else:
            col.enabled = False

        #row = layout.row()
        col.prop(mytool,"my_frame_start", text = "Start")
        col.prop(mytool,"my_frame_end", text ="End")

        row = layout.row()
        row.prop(mytool, "setting_override_frames", text = "Override Frames")

        split = layout.split(factor=0.5,align= True)
        #split.alignment = 'CENTER'
        split.label(text = 'Name', translate = False)
        split.label(text = 'Start', translate = False)
        split.label(text = 'End', translate = False)
        
        # row = layout.row()        
        # col = row.column(align=True)
        # split.label(text = '', translate = False)
        # split.prop(item, "frame_start", text = 'Start:', emboss = False, translate = False)      
        # split.prop(item, "frame_end", text = 'End', emboss = False, translate = False)

        # rows = 2
        row = layout.row()
        row.template_list("OPSTYIX_UL_items", "", scene, "custom", scene, "selected_index", rows=6)

        # Align settingsto the right of the UIList
        col = row.column(align=True)
        col.operator("opstyix.list_action", icon='ADD', text="").action = 'ADD'
        col.operator("opstyix.list_action", icon='REMOVE', text="").action = 'REMOVE'
        col.separator()
        col.operator("opstyix.list_action", icon='TRIA_UP', text="").action = 'UP'
        col.operator("opstyix.list_action", icon='TRIA_DOWN', text="").action = 'DOWN'
        col.separator()
        col.operator("opstyix.setframerange", text="", icon="DRIVER_DISTANCE")
        col.prop(scene, "use_preview_range", text="", toggle=True)

# class OPSTYIX_PT_settings(Panel):
#     bl_label = "Settings"
#     bl_space_type = "PROPERTIES"
#     bl_region_type = "WINDOW"
#     bl_context = "scene"
#     bl_category = "OPSTYIX"
#     bl_parent_id = "OPSTYIX_PT_toolkit"

#     def draw(self, context):
#         layout = self.layout
#         scene = context.scene
#         mytool = scene.OPSTYIX_user_input

#         row = layout.row()
#         column = layout.column()
#         # Should probably defunct this, and leave this enabled by default.
#         # row.prop(mytool, "tool_modifyEndFrame", text= "Modify End Frame") 

#         # row = column.row()
#         # row.prop(mytool, "setting_useStartEndFrame", text = "Use Start/End Frames")

#         # row = column.row()
#         # row.prop(mytool, "my_frame_padding", text = "Frame Padding")
        
#* COLLECTIONS
# This contains the shot list bookmark data
class OPSTYIX_objectCollection(PropertyGroup):
    #name: StringProperty() -> Instantiated by default
    #obj_type: StringProperty()
    id: IntProperty()
    frame_start: IntProperty()
    frame_end: IntProperty()
    frame_note: StringProperty()
    active: BoolProperty()

#* REGISTER
#* Add all classes below, it will automatically register and unregister
def register_original():
    # from bpy.utils import register_class
    # for cls in classes:
    #     register_class(cls)
    bpy.utils.register_class(MyProperties)
    bpy.utils.register_class(OPSTYIX_PT_toolkit)
    bpy.utils.register_class(OPSTYIX_PT_animationBookmarks)
    # bpy.utils.register_class(OPSTYIX_PT_settings)
    bpy.utils.register_class(OPSTYIX_UL_items)
    bpy.utils.register_class(OPSTYIX_OT_DrawMarkers)
    bpy.utils.register_class(OPSTYIX_OT_DeleteMarkers)
    bpy.utils.register_class(OPSTYIX_OT_setFrameRange)
    bpy.utils.register_class(OPSTYIX_objectCollection)
    bpy.utils.register_class(OPSTYIX_OT_infoTest)
    bpy.utils.register_class(OPSTYIX_OT_actions)
    # bpy.utils.register_class(CUSTOM_OT_printItems)
    # bpy.utils.register_class(CUSTOM_OT_clearList)
    # bpy.utils.register_class(CUSTOM_OT_removeDuplicates)
    # bpy.utils.register_class(CUSTOM_OT_selectItems)

    # Passes "MyProperties" into something callable a.k.a. "OPSTYIX_user_input"
    bpy.types.Scene.OPSTYIX_user_input = PointerProperty(type=MyProperties)
    bpy.types.Scene.OPSTYIX_active_collection = bpy.props.PointerProperty(type=bpy.types.Collection)

    # Passes 
    bpy.types.Scene.custom = CollectionProperty(type=OPSTYIX_objectCollection)
    bpy.types.Scene.selected_index = IntProperty()
    
def unregister_original():
    # from bpy.utils import unregister_class
    # for cls in classes:
    #     unregister_class(cls)
    bpy.utils.unregister_class(MyProperties)
    bpy.utils.unregister_class(OPSTYIX_PT_toolkit)
    bpy.utils.unregister_class(OPSTYIX_PT_animationBookmarks)
    # bpy.utils.unregister_class(OPSTYIX_PT_settings)
    bpy.utils.unregister_class(OPSTYIX_UL_items)
    bpy.utils.unregister_class(OPSTYIX_OT_DrawMarkers)
    bpy.utils.unregister_class(OPSTYIX_OT_DeleteMarkers)
    bpy.utils.unregister_class(OPSTYIX_OT_setFrameRange)
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

#*  RUN ON LOAD
# print("OPSTYIX_toolkit loaded!")
print("original.py loaded")