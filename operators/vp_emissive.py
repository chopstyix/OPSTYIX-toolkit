#* FILE IMPORT
import bpy
                       
from bpy.types import (Operator)

#* This operator assists by providing a way to visualize the lighting changes in realtime
#* through the use of Blender's object color display setting.
# TODO: Figure out how to set min/max for custom property
class OPSTYIX_OT_EMISSIVEVP_ObjectSetup(Operator):
    bl_idname = "opstyix.emissivevp_objectsetup"
    bl_label = "Octane Emissive Viewport Setup"
    bl_description = "Creates a custom object property named 'emission' which drives the objects viewport color."
    def execute(self, context):

        # Get all selected objects
        for x in bpy.context.selected_objects:

            # Debug, get selected object's name
            print("Object: " + x.name)

            # Create a custom property, labeled as 'emission'
            bpy.data.objects[x.name]['emission'] = 0.0

            # Copy new custom property as a new driver
            # Red Channel
            d = bpy.data.objects[x.name].driver_add("color",0).driver
            d.expression = "self[\'emission\']"
            d.use_self = True

            # Green Channel
            d = bpy.data.objects[x.name].driver_add("color",1).driver
            d.expression = "self[\'emission\']"
            d.use_self = True

            # Blue Channel
            d = bpy.data.objects[x.name].driver_add("color",2).driver
            d.expression = "self[\'emission\']"
            d.use_self = True

        return {'FINISHED'}

#* This operator assists by creating a driver under Octane's 'Float component picker' material node
#* and is based off an object's custom property (in this case 'emission').
#* This allows an object's custom property to drive the emission strength of a material assigned to said object.
#TODO: There are some instances where the operator will return an error when used with multiple objects.
class OPSTYIX_OT_EMISSIVEVP_MaterialSetup(Operator):
    bl_idname = "opstyix.emissivevp_materialsetup"
    bl_label  = "Creates a driver under the first index of 'Float component picker'"
    def execute(self, context):

        # Loop through all of the selected objects
        for x in bpy.context.selected_objects:

            # Debug Stuff
            print("Object: " + x.name)
            print("Active Mat: " + x.active_material.name)
    
            #TODO: Create a new "Float component picker" if none are available.

            # Create driver in the first instance and index of the node 'Float componenet picker'
            d = x.active_material.node_tree.nodes["Float component picker"].inputs[0].driver_add("default_value",0).driver # Unsure why '.driver' is necessary but I'm sure it's there for a reason.
            d.expression = "emission" # Driver Expression

            v = d.variables.new() # Create a new driver variable
            v.name = "emission" # Name variable 'emission'
            v.targets[0].id = x # Set variable target to current object 'x'
            v.targets[0].data_path = "[\"emission\"]" # Set data path to current object 'x' custom property 'emission'
        return {'FINISHED'}

def register_vp_emissive():
    bpy.utils.register_class(OPSTYIX_OT_EMISSIVEVP_ObjectSetup)
    bpy.utils.register_class(OPSTYIX_OT_EMISSIVEVP_MaterialSetup)

def unregister_vp_emissive():
    bpy.utils.unregister_class(OPSTYIX_OT_EMISSIVEVP_ObjectSetup)
    bpy.utils.unregister_class(OPSTYIX_OT_EMISSIVEVP_MaterialSetup)

#* RUN ON LOAD
print("vp_emissive.py loaded")