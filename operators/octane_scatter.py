import os
import bpy
from bpy.utils import register_class, unregister_class

from bpy.types import Operator, Panel, Menu, AddonPreferences, PropertyGroup, UIList

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    # FloatProperty,
    # FloatVectorProperty,
    # EnumProperty,
    PointerProperty,
    CollectionProperty,
)


class OctScatterProp(PropertyGroup):
    seed: IntProperty(
        name="Seed Value",
        description="An Integer Value",
        default=0,
        min=0,
        max=999999,
    )


class OPSTYIX_OT_get_nodes(Operator):
    bl_idname = "opstyix.get_shader_nodes"
    bl_label = "Show all shader nodes"
    bl_description = "Gets all shader nodes found within the material"

    def execute(self, context):
        mat = bpy.data.materials.get("Octane Scatter - Placeholder")
        for n in mat.node_tree.nodes:
            print(n, n.name)

        return {"FINISHED"}


class OPSTYIX_OT_oct_create_scatter_mat(Operator):
    bl_idname = "opstyix.octane_create_scatter_mat"
    bl_label = "Create octane scatter material"
    bl_description = "Under contruction"

    def execute(self, context):
        active_obj = context.active_object
        selected_obj = []
        #* Get selected object.
        print("active obj = ", active_obj)
        #* Check if object contains a material.
        # if active_obj.active_material != None:
        #     active_obj.active_material = None
        scatter_mat = bpy.data.materials.new(name="TESTING")
        scatter_mat.use_nodes = True
        if active_obj.data.materials:
            active_obj.data.materials[0] = scatter_mat
        else:
            active_obj.data.materials.append(scatter_mat)

        #* Convert universal node to scatter on object node.
        #* Create 5 object nodes.
        #* Connect to to the appropriate sockets.
        # for obj in context.selected_objects:
        #     selected_obj.append(obj)

        # print("active obj = ", active_obj)
        # print("selected obj = ", selected_obj)

        # surface_obj = active_obj
        # scatter_obj = selected_obj
        # scatter_obj.remove(active_obj)

        # print("scatter obj = ", scatter_obj)
        # print("surface obj = ", surface_obj)

        # Get material
        # mat = bpy.data.materials.get("Octane Scatter - Placeholder")
        # if mat is None:
        #     # create material
        #     mat = bpy.data.materials.new(name="Octane Scatter - Placeholder")
        #     mat.use_nodes = True

        # # if surface_obj.data.materials:
        # #     surface_obj.data.materials[0] = mat
        # # else:
        # #     surface_obj.data.materials.append(mat)

        # active_material = bpy.context.active_object.active_material
        # node_tree = active_material.node_tree
        # selected_node = context.selected_nodes
        # print("active_material = ", active_material)
        # print("node_tree = ", node_tree)
        # print("selected node = ", selected_node)
        # bpy.ops.node.select_all(action='DESELECT')
        # node_tree.nodes["Universal material"].select = True
        # bpy.ops.node.nw_swtch_node_type(to_type='OctaneGreyscaleImage')
        #! For some reason this doesn't work, maybe it needs to be called upon in a separate operator?
        # Remove it
        # mat.node_tree.nodes.remove(mat.node_tree.nodes['Principled BDSF'])
        # mat.node_tree.nodes.remove(mat.node_tree.nodes['Uni
        # active_material = bpy.context.active_object.active_material
        # node_tree = active_material.node_tree
        # node_tree.nodes.remove(node_tree.nodes['Universal material'])
        
        print("helloooooooooo?")
        area = bpy.context.area
        old_type = area.type
        area.type = "NODE_EDITOR"
        area.spaces.active.tree_type = 'ShaderNodeTree'
        print(scatter_mat)
        bpy.ops.opstyix.octane_scatter_surface_setup()
        # bpy.ops.node.nw_swtch_node_type(to_type="OctaneScatterOnSurface")

        area.type = old_type

        print("teeeeeeest")

        return {"FINISHED"}


class OPSTYIX_OT_oct_scatter_on_surface_setup(Operator):
    bl_idname = "opstyix.octane_scatter_surface_setup"
    bl_label = "Setup Scatter on Surface"
    bl_description = "TBD"

    def execute(self, context):
        # scatter_obj_1, scatter_obj_2, scatter_obj_3, scatter_obj_4 = None
        # scatter_mat = bpy.context.active_object.data.materials[0]
        print("1")
        # scatter_mat.node_tree.nodes["Material Output"].select = False
        # scatter_mat.node_tree.nodes["Universal material"].select
        # scatter_mat.node_tree.nodes["Principled BSDF"].select
        # scatter_mat.node_tree.nodes["Universal material"].select
        active_material = bpy.context.active_object.active_material
        print(active_material)
        node_tree = active_material.node_tree
        # Remove it
        # mat.node_tree.nodes.remove(mat.node_tree.nodes['Principled BDSF'])
        # mat = bpy.data.materials.get("Octane Scatter - Placeholder")
        # node_tree.nodes["Universal material"].select
        node_tree.nodes.remove(node_tree.nodes["Universal material"])
        print("HIIIII")
        # define node get "universal material"
        # node = node_tree.nodes["Universal material"]
        # node.select = True
        # select "universal material"
        # node_tree.nodes.active = node
        output_node = node_tree.nodes["Material Output"]
        scatter_node = node_tree.nodes.new('OctaneScatterOnSurface')
        scatter_node.location = [(output_node.location.x - 250), output_node.location.y]
        node_tree.links.new(scatter_node.outputs[0], output_node.inputs["Surface"]) 
        node = 3
        for x in range(5):
            # node = 3
            # Create a variable with the name "var_i", where i is the loop index 
            if x == 0:
                emitter_obj = node_tree.nodes.new("OctaneObjectData")
                emitter_obj.label = "Emitter Object"
                emitter_obj.name = "Emitter Object"             
                emitter_obj.location = [(scatter_node.location.x - 400), scatter_node.location.y]
                emitter_obj.use_custom_color = True
                emitter_obj.color = (0.608, 0.270136, 0.440512)
                node_tree.links.new(emitter_obj.outputs[2], scatter_node.inputs["Surface"])     

            else:
                # node = 3
                exec(f"scatter_obj_{x} = node_tree.nodes.new(\"OctaneObjectData\")")
                exec(f"scatter_obj_{x}.label = \"Scatter Object {x}\"")
                exec(f"scatter_obj_{x}.name = \"Scatter Object {x}\"")    
                exec(f"scatter_obj_{x}.location = [scatter_node.location.x - 400, scatter_node.location.y - (250 * {x})]")    
                exec(f"scatter_obj_{x}.use_custom_color = True")    
                exec(f"scatter_obj_{x}.color = (0.274738, 0.336141, 0.608)")    
                exec(f"node_tree.links.new(scatter_obj_{x}.outputs[2], scatter_node.inputs[{node}])")
                node += 1
        
        # bpy.ops.node.nw_swtch_node_type(to_type="OctaneScatterOnSurface") 
        # Default Settings
        scatter_node.inputs[7].default_value = 'Random'
        scatter_node.inputs[11].default_value = 'Random instances by relative area'
        scatter_node.inputs[40].default_value = 'Randomized with independent axes'
        scatter_node.inputs[45].default_value = 'Randomized with independent axes'        
        scatter_node.inputs[41].default_value[1] = -360
        scatter_node.inputs[42].default_value[1] = 360
        scatter_node.inputs[46].default_value = (.9, .9, .9)
        scatter_node.inputs[47].default_value = (1.1, 1.1, 1.1)


        

        return {"FINISHED"}


class OPSTYIX_OT_OctaneScatter(Operator):
    bl_idname = "opstyix.octane_scatter"
    bl_label = "Octane Scatter Setup"
    bl_description = "Filler Text, TBD"
    
    @classmethod
    def poll(cls, context):
        return bool(context.active_object and bpy.data.objects[context.active_object.name].active_material.name)
    
    def execute(self, context):
        scatter_array = []
        scatter_nodes = [
            "Scatter Object 1",
            "Scatter Object 2",
            "Scatter Object 3",
            "Scatter Object 4",
        ]
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
            bpy.data.meshes[
                active_object.data.name
            ].octane.octane_geo_node_collections.node_graph_tree = scatter_material

            bpy.data.meshes[
                active_object.data.name
            ].octane.octane_geo_node_collections.osl_geo_node = (
                "Scatter on surface"  # ?
            )

            # bpy.data.materials[scatter_material].node_tree.nodes["Emitter Object"].inputs[0].default_value = active_object
            bpy.data.materials[scatter_material].node_tree.nodes[
                "Emitter Object"
            ].object_ptr = active_object
            for idx, x in enumerate(scatter_nodes):
                bpy.data.materials[scatter_material].node_tree.nodes[
                    scatter_nodes[idx]
                ].object_ptr = None

            for idx, x in enumerate(scatter_array):
                bpy.data.materials[scatter_material].node_tree.nodes[
                    scatter_nodes[idx]
                ].object_ptr = scatter_array[idx]
                # bpy.data.materials[scatter_material].node_tree.nodes[scatter_nodes[idx]].inputs[0].default_value = scatter_array[idx]

        return {"FINISHED"}


class OPSTYIX_PT_OctanePanel(bpy.types.Panel):
    bl_label = "OPSTYIX Toolkit"
    bl_category = "OPSTYIX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'octane'

    def draw_header(self, context):
        self.layout.label(icon_value=custom_icons["opstyix_icon"].icon_id)

    def draw(self, context):
        layout = self.layout
        
        try:
            obj = context.active_object
            # scatter_material = bpy.data.objects[obj.name].active_material.name
            scatter_material = obj.material_slots[0].name
            print(scatter_material)
            scatter_node = bpy.data.materials[scatter_material].node_tree.nodes["Scatter on surface"]
        except:
            print("Error!")
            pass
        else:
          obj = context.active_object
          scatter_material = bpy.data.objects[obj.name].active_material.name
          
          row = layout.row()
          col = row.column()
          col.label(text="Selected Emitter: " + obj.name)
          col.label(text="Scatter Material: " + scatter_material)

          row = layout.row()
          col = row.column()
          col.prop(context.scene, "OPSTYIX_active_collection", text="Active Collection")          
          col.operator("opstyix.octane_scatter")

          layout = self.layout

          row = layout.row()
          col = row.column()
          col.prop(
              bpy.data.materials[scatter_material]
              .node_tree.nodes["Scatter on surface"]
              .inputs[22],
              "default_value",
              text="Instances",
          )

          col = layout.column(align=True)
          col.prop(
              bpy.data.materials[scatter_material]
              .node_tree.nodes["Scatter on surface"]
              .inputs[20],
              "default_value",
              text="Seed Location",
          )          
          col.prop(
              bpy.data.materials[scatter_material]
              .node_tree.nodes["Scatter on surface"]
              .inputs[8],
              "default_value",
              text="Seed Selection",
          )

          col = layout.column(align=True)

          col.prop(
              bpy.data.materials[scatter_material]
              .node_tree.nodes["Scatter on surface"]
              .inputs[41],
              "default_value",
            #   index=1,
              text="Rotation Min.",
          )
          col.prop(
              bpy.data.materials[scatter_material]
              .node_tree.nodes["Scatter on surface"]
              .inputs[42],
              "default_value",
            #   index=1,
              text="Rotation Max.",
          )   
          col = layout.column(align=True)                             
          col.prop(
              bpy.data.materials[scatter_material]
              .node_tree.nodes["Scatter on surface"]
              .inputs[46],
              "default_value",
            #   index=0,
              text="Scale Min.",
          )
          col.prop(
              bpy.data.materials[scatter_material]
              .node_tree.nodes["Scatter on surface"]
              .inputs[47],
              "default_value",
            #   index=0,
              text="Scale Max.",
          )          
        #   col.prop(
        #       bpy.data.materials[scatter_material]
        #       .node_tree.nodes["Scatter on surface"]
        #       .inputs[46],
        #       "default_value",
        #     #   index=1,
        #       text="Rotation Max.",
        #   )
        #   col.prop(
        #       bpy.data.materials[scatter_material]
        #       .node_tree.nodes["Scatter on surface"]
        #       .inputs[46],
        #       "default_value",
        #       index=2,
        #       text="Rotation Max.",
        #   )                                  
# bpy.data.materials["OS_WhiteWindflower"].node_tree.nodes["Scatter on surface"].inputs[41].default_value[1]
        # row = layout.row()
        # self.layout.prop(context.scene, "test_collection")

        # box = layout.box()
        # split = box.split()
        # col = split.column(align=True)
        # col.operator("bpy.ops.view3d.localview", text="Toggle Local View")


# * Global Variables
custom_icons = None

# * Define all classes
classes = [
    OctScatterProp,
    OPSTYIX_OT_get_nodes,
    OPSTYIX_OT_oct_scatter_on_surface_setup,
    OPSTYIX_OT_oct_create_scatter_mat,
    OPSTYIX_OT_OctaneScatter,
    OPSTYIX_PT_OctanePanel,
]


def register():
    # Custom Icon
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    addon_path = os.path.dirname(__file__)
    icons_dir = os.path.join(addon_path, "..", "icons")

    custom_icons.load(
        "opstyix_icon", os.path.join(icons_dir, "opstyix_icon.png"), "IMAGE"
    )

    for cls in classes:
        register_class(cls)
    # bpy.utils.register_class(OPSTYIX_OT_OctaneScatter)
    # bpy.utils.register_class(OPSTYIX_PT_OctanePanel)
    bpy.types.Scene.OPSTYIX_OctScatterProperties = PointerProperty(type=OctScatterProp)
    bpy.types.Scene.OPSTYIX_active_collection = bpy.props.PointerProperty(
        type=bpy.types.Collection
    )


def unregister():
    # Custom Icon
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.OPSTYIX_OctScatterProperties


# *  RUN ON LOAD
print("octane_scatter.py loaded")

# TODO
# Automatically assigns 4 objects to a selected object for Octane Scatter, assign object a special prefix so addon is able to recognize it?
# Addon also needs to duplicate a scatter template material.
# Add input fields for scatter settings. Instances, Seeds, etc.
