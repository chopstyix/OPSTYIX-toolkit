import bpy
          
from bpy.types import (Operator,
                       Panel,
					   Menu,
					   AddonPreferences,
                       PropertyGroup,
                       UIList)

class OPSTYIX_OT_OctaneScatter(Operator):
    bl_idname = "opstyix.octane_scatter"
    bl_label = "Initiate Auto Scatter"
    bl_description="Filler Text, TBD"
    def execute(self, context):
        scatter_array = []
        scatter_nodes = ["Scatter Object 1","Scatter Object 2","Scatter Object 3","Scatter Object 4"]
        obj = context.active_object
        active_object = obj
        active_collection = context.scene.OPSTYIX_active_collection.name
            
        # Take the 4 objects in active_collection, place into an array.
        for scatter_object in bpy.data.collections[active_collection].all_objects:
          scatter_array.append(scatter_object)
          print("Adding to scatter_array: " + scatter_object.name)
              
        if len(scatter_array) > 4:
          print("Item Count Failed")
          print("There are too many items in this collection!")            

        else: 
          print("Item Count Passed")
          scatter_material = bpy.data.objects[active_object.name].active_material.name
          print("Active Material: " + scatter_material)
          bpy.data.meshes[active_object.data.name].octane.octane_geo_node_collections.node_graph_tree = scatter_material

          bpy.data.meshes[active_object.data.name].octane.octane_geo_node_collections.osl_geo_node = "Scatter on surface" # ?

          bpy.data.materials[scatter_material].node_tree.nodes["Emitter Object"].inputs[0].default_value = active_object
          for idx,x in enumerate(scatter_array):
            bpy.data.materials[scatter_material].node_tree.nodes[scatter_nodes[idx]].inputs[0].default_value = scatter_array[idx]               
    
        return {'FINISHED'}  
    
class OPSTYIX_PT_OctanePanel(bpy.types.Panel):
    bl_label = "OPSTYIX - Octane Scatter Helper"
    bl_category = "OPSTYIX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        layout = self.layout

        obj = context.active_object
        active_object = obj
 
        row = layout.row()
        row.label(text="Selected Emitter: " + obj.name)

        layout = self.layout

        row = layout.row()
        self.layout.prop(context.scene, "OPSTYIX_active_collection", text = "Active Collection")
        
        #row = layout.row()
        #self.layout.prop(context.scene, "test_collection")        

        box = layout.box()
        split = box.split()            
        col = split.column(align=True)
        row = col.row(align=True) 
        row.operator("opstyix.octane_scatter")

def register_scatter():
    bpy.utils.register_class(OPSTYIX_OT_OctaneScatter)
    bpy.utils.register_class(OPSTYIX_PT_OctanePanel)
    
def unregister_scatter():
    bpy.utils.unregister_class(OPSTYIX_OT_OctaneScatter)
    bpy.utils.unregister_class(OPSTYIX_PT_OctanePanel)

#*  RUN ON LOAD
print("scatter.py loaded")

# TODO
# Automatically assigns 4 objects to a selected object for Octane Scatter, assign object a special prefix so addon is able to recognize it?
# Addon also needs to duplicate a scatter template material.
# Add input fields for scatter settings. Instances, Seeds, etc.
