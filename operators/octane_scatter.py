import bpy
from bpy.utils import register_class, unregister_class

from bpy.types import (Operator,
                       Panel,
					   Menu,
					   AddonPreferences,
                       PropertyGroup,
                       UIList)

class OPSTYIX_OT_get_nodes(Operator):
  bl_idname = "opstyix.get_shader_nodes"
  bl_label = "Show all shader nodes"
  bl_description = "Gets all shader nodes found within the material"

  def execute(self, context):
    mat = bpy.data.materials.get("Octane Scatter - Placeholder")
    for n in mat.node_tree.nodes:
      print(n, n.name)

    return {'FINISHED'}

class OPSTYIX_OT_oct_create_scatter_mat(Operator):
   bl_idname = "opstyix.octane_create_scatter_mat"
   bl_label = "Create octane scatter material"
   bl_description = "Under contruction"

   def execute(self, context):
      active_obj = context.active_object
      selected_obj = []

      for obj in context.selected_objects:
         selected_obj.append(obj)
      
      print("active obj = ", active_obj)
      print("selected obj = ", selected_obj)

      surface_obj = active_obj
      scatter_obj = selected_obj
      scatter_obj.remove(active_obj)

      print("scatter obj = ", scatter_obj)
      print("surface obj = ", surface_obj)

      # Get material
      mat = bpy.data.materials.get("Octane Scatter - Placeholder")
      if mat is None:
        # create material
        mat = bpy.data.materials.new(name="Octane Scatter - Placeholder")
        mat.use_nodes = True

      if surface_obj.data.materials:
         surface_obj.data.materials[0] = mat
      else:
         surface_obj.data.materials.append(mat)

      active_material = bpy.context.active_object.active_material 
      node_tree = active_material.node_tree
      # selected_node = context.selected_nodes
      print("active_material = ", active_material)
      print("node_tree = ", node_tree)
      # print("selected node = ", selected_node)
      # bpy.ops.node.select_all(action='DESELECT')
      # node_tree.nodes["Universal material"].select = True
      # bpy.ops.node.nw_swtch_node_type(to_type='OctaneGreyscaleImage')  
      #! For some reason this doesn't work, maybe it needs to be called upon in a separate operator?
      #Remove it
      # mat.node_tree.nodes.remove(mat.node_tree.nodes['Principled BDSF'])
      # mat.node_tree.nodes.remove(mat.node_tree.nodes['Uni
      # active_material = bpy.context.active_object.active_material 
      # node_tree = active_material.node_tree      
      # node_tree.nodes.remove(node_tree.nodes['Universal material'])
      bpy.ops.opstyix.octane_scatter_surface_setup()
      print("teeeeeeest")

      return {'FINISHED'}
   
class OPSTYIX_OT_oct_scatter_on_surface_setup(Operator):
   bl_idname = "opstyix.octane_scatter_surface_setup"
   bl_label = "Setup Scatter on Surface"
   bl_description = "TBD"

   def execute(self, context):
      active_material = bpy.context.active_object.active_material 
      node_tree = active_material.node_tree
      #Remove it
      # mat.node_tree.nodes.remove(mat.node_tree.nodes['Principled BDSF'])
      # mat = bpy.data.materials.get("Octane Scatter - Placeholder")      
      node_tree.nodes.remove(node_tree.nodes['Universal material'])
      print("HIIIII")

      return {'FINISHED'}    
   
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

classes = [
   OPSTYIX_OT_get_nodes,
   OPSTYIX_OT_oct_scatter_on_surface_setup,
   OPSTYIX_OT_oct_create_scatter_mat,
   OPSTYIX_OT_OctaneScatter,
   OPSTYIX_PT_OctanePanel,
]

def register():
    for cls in classes:
      register_class(cls)
    # bpy.utils.register_class(OPSTYIX_OT_OctaneScatter)
    # bpy.utils.register_class(OPSTYIX_PT_OctanePanel)
    bpy.types.Scene.OPSTYIX_active_collection = bpy.props.PointerProperty(type=bpy.types.Collection)
    
def unregister():
    for cls in classes:
       unregister_class(cls)

#*  RUN ON LOAD
print("octane_scatter.py loaded")

# TODO
# Automatically assigns 4 objects to a selected object for Octane Scatter, assign object a special prefix so addon is able to recognize it?
# Addon also needs to duplicate a scatter template material.
# Add input fields for scatter settings. Instances, Seeds, etc.
