import os
import bpy
from bpy.utils import register_class, unregister_class

from bpy.types import Operator, Panel, PropertyGroup, UIList

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    # FloatProperty,
    # FloatVectorProperty,
    # EnumProperty,
    PointerProperty,

)



class OctScatterProp(PropertyGroup):
    seed: IntProperty(
        name="Seed Value",
        description="An Integer Value",
        default=0,
        min=0,
        max=999999,
    )
    picking_scatter: BoolProperty(
        name="Picking Scatter Objects",
        default=False,
    )
    surface_object: PointerProperty(
        name="Surface Object",
        type=bpy.types.Object,
    )
    scatter_collection_name: StringProperty(
        name="Collection Name",
        description="Name for the new collection that will hold the scatter objects",
        default="Scatter",
    )
    use_existing_collection: BoolProperty(
        name="Use Existing Collection",
        description="Reference an existing collection instead of creating a new one",
        default=False,
    )
    existing_collection: PointerProperty(
        name="Existing Collection",
        type=bpy.types.Collection,
    )


class OPSTYIX_OT_BeginScatterPick(Operator):
    bl_idname = "opstyix.begin_scatter_pick"
    bl_label = "Select Scatter Objects"
    bl_description = "Store this object as the surface and select up to 4 scatter objects"

    def execute(self, context):
        props = context.scene.OPSTYIX_OctScatterProperties
        props.surface_object = context.active_object
        props.picking_scatter = True
        return {"FINISHED"}


class OPSTYIX_OT_ConfirmScatterPick(Operator):
    bl_idname = "opstyix.confirm_scatter_pick"
    bl_label = "Confirm Selection"
    bl_description = "Move the selected objects into a new collection"

    def execute(self, context):
        props = context.scene.OPSTYIX_OctScatterProperties
        surface = props.surface_object

        if props.use_existing_collection and props.existing_collection:
            collection = props.existing_collection
            col_name = collection.name
            scatter_objects = list(collection.all_objects)[:4]
            if not scatter_objects:
                self.report({"WARNING"}, "Existing collection has no objects.")
                return {"CANCELLED"}
        else:
            scatter_objects = [o for o in context.selected_objects if o != surface][:4]
            if not scatter_objects:
                self.report({"WARNING"}, "No objects selected.")
                return {"CANCELLED"}
            base_name = props.scatter_collection_name or "Scatter"
            prefixed_name = "#OS_" + base_name
            collection = bpy.data.collections.get(prefixed_name)
            if collection is None:
                collection = bpy.data.collections.new(prefixed_name)
                context.scene.collection.children.link(collection)
            col_name = prefixed_name

            for obj in scatter_objects:
                for col in list(obj.users_collection):
                    col.objects.unlink(obj)
                collection.objects.link(obj)

        for obj in scatter_objects:
            if obj.type == 'MESH' and hasattr(obj.data, 'octane'):
                obj.data.octane.primitive_coordinate_mode = 'Octane'

        context.scene.OPSTYIX_active_collection = collection
        props.picking_scatter = False

        if surface:
            surface.name = col_name
            bpy.ops.object.select_all(action='DESELECT')
            surface.select_set(True)
            context.view_layer.objects.active = surface
            context.view_layer.update()

        bpy.ops.opstyix.octane_create_scatter_mat()

        try:
            bpy.ops.opstyix.octane_scatter()
        except RuntimeError as e:
            self.report({'WARNING'}, f"Scatter setup skipped: {e}")

        self.report({"INFO"}, f"Moved {len(scatter_objects)} object(s) into '{col_name}'.")
        return {"FINISHED"}


class OPSTYIX_OT_SetScatterSurface(Operator):
    bl_idname = "opstyix.set_scatter_surface"
    bl_label = "Set Scatter Surface"
    bl_description = "Set this object as the active scatter surface"

    object_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name)
        if obj is None:
            self.report({'WARNING'}, f"Object '{self.object_name}' not found.")
            return {'CANCELLED'}
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {'FINISHED'}


class OPSTYIX_OT_CancelScatterPick(Operator):
    bl_idname = "opstyix.cancel_scatter_pick"
    bl_label = "Cancel"
    bl_description = "Cancel scatter object selection"

    def execute(self, context):
        context.scene.OPSTYIX_OctScatterProperties.picking_scatter = False
        return {"FINISHED"}


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
        scatter_mat = bpy.data.materials.new(name=active_obj.name)
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
        node_tree.links.new(scatter_node.outputs[0], output_node.inputs["Displacement"])
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
                scatter_obj = node_tree.nodes.new("OctaneObjectData")
                scatter_obj.label = f"Scatter Object {x}"
                scatter_obj.name = f"Scatter Object {x}"
                scatter_obj.location = [scatter_node.location.x - 400, scatter_node.location.y - (250 * x)]
                scatter_obj.use_custom_color = True
                scatter_obj.color = (0.274738, 0.336141, 0.608)
                node_tree.links.new(scatter_obj.outputs[2], scatter_node.inputs[node])
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
        props = context.scene.OPSTYIX_OctScatterProperties

        # ── Picking mode ──────────────────────────────────────────────────────
        if props.picking_scatter:
            surface = props.surface_object
            scatter_candidates = [o for o in context.selected_objects if o != surface][:4]

            box = layout.box()
            col = box.column(align=True)

            row = col.row()
            row.enabled = False
            row.label(text=f"Surface:  {surface.name if surface else '—'}", icon='OBJECT_DATA')

            col.separator(factor=0.5)
            col.prop(props, "use_existing_collection", text="Use Existing Collection", toggle=True)
            col.separator(factor=0.5)

            if props.use_existing_collection:
                col.prop(props, "existing_collection", text="Collection")
                existing_count = len(props.existing_collection.all_objects) if props.existing_collection else 0
                hint = col.row()
                hint.enabled = False
                hint.label(text=f"{existing_count} object(s) in collection.", icon='INFO')
                can_confirm = bool(props.existing_collection and existing_count > 0)
            else:
                col.prop(props, "scatter_collection_name", text="Scatter Group")
                col.separator(factor=0.5)
                hint = col.row()
                hint.enabled = False
                hint.label(text="Select up to 4 objects to scatter on the surface.", icon='INFO')
                col.separator(factor=0.5)
                col.label(text=f"Selected:  {len(scatter_candidates)} / 4 object(s)", icon='OUTLINER_OB_MESH')
                can_confirm = 1 <= len(scatter_candidates) <= 4

            col.separator(factor=0.5)
            row = col.row(align=True)
            row.enabled = can_confirm
            row.operator("opstyix.confirm_scatter_pick", text="Confirm", icon='CHECKMARK')
            row.operator("opstyix.cancel_scatter_pick", text="Cancel", icon='X')
            return

        # ── No object selected ────────────────────────────────────────────────
        obj = context.active_object
        if obj is None:
            layout.label(text="Select a surface object to begin.", icon='INFO')
            return

        if obj.type != 'MESH':
            layout.label(text="Selected object is not a mesh.", icon='INFO')
            return

        mat = obj.material_slots[0].material if obj.material_slots else None

        # ── No material: offer to pick scatter assets directly ────────────────
        if mat is None:
            layout.label(text="Ready to set up scatter. Select scatter assets to begin.", icon='INFO')
            layout.operator("opstyix.begin_scatter_pick",
                            text="Select Scatter Assets", icon='RESTRICT_SELECT_OFF')
            return

        # ── Has material but not an #OS_ scatter material ─────────────────────
        if not mat.name.startswith("#OS_"):
            layout.label(text="Material is not an Octane Scatter material.", icon='INFO')
            return

        # ── Valid #OS_ scatter material ───────────────────────────────────────
        try:
            sn = mat.node_tree.nodes["Scatter on surface"]
        except KeyError:
            layout.label(text="Scatter node not found in material.", icon='ERROR')
            return

        active_col = context.scene.OPSTYIX_active_collection
        layout.label(text="Surface: " + obj.name, icon='OBJECT_DATA')
        layout.label(text="Material: " + mat.name, icon='MATERIAL')
        layout.label(text="Collection: " + (active_col.name if active_col else "None"), icon='OUTLINER_COLLECTION')
        layout.separator(factor=0.5)

        layout.operator("opstyix.begin_scatter_pick",
                        text="Select Scatter Assets", icon='RESTRICT_SELECT_OFF')
        layout.separator(factor=0.5)

        row = layout.row(align=True)
        row.prop(sn.inputs[22], "default_value", text="Instances")
        row.prop(sn.inputs[20], "default_value", text="Seed")

        row = layout.row(align=False)
        col_min = row.column(align=True)
        col_max = row.column(align=True)

        col_min.label(text="Min")
        col_min.prop(sn.inputs[41], "default_value", text="Rotation")
        col_min.prop(sn.inputs[46], "default_value", text="Scale")

        col_max.label(text="Max")
        col_max.prop(sn.inputs[42], "default_value", text="Rotation")
        col_max.prop(sn.inputs[47], "default_value", text="Scale")



# * Global Variables
custom_icons = None

# * Define all classes
classes = [
    OctScatterProp,
    OPSTYIX_OT_BeginScatterPick,
    OPSTYIX_OT_ConfirmScatterPick,
    OPSTYIX_OT_SetScatterSurface,
    OPSTYIX_OT_CancelScatterPick,
    OPSTYIX_OT_get_nodes,
    OPSTYIX_OT_oct_scatter_on_surface_setup,
    OPSTYIX_OT_oct_create_scatter_mat,
    OPSTYIX_OT_OctaneScatter,
    OPSTYIX_PT_OctanePanel,
]


def _redraw_panel(_scene):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'UI':
                        region.tag_redraw()


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

    bpy.types.Scene.OPSTYIX_OctScatterProperties = PointerProperty(type=OctScatterProp)
    bpy.types.Scene.OPSTYIX_active_collection = bpy.props.PointerProperty(
        type=bpy.types.Collection
    )
    bpy.app.handlers.depsgraph_update_post.append(_redraw_panel)


def unregister():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.OPSTYIX_OctScatterProperties

    if _redraw_panel in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_redraw_panel)


print("octane_scatter.py loaded")
